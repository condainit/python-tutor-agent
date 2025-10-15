"""Batch evaluation harness for generating and scoring tutoring hints from base and fine-tuned models."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from eval.inference import HintGenerator
from agent.prompts import Strategy
from agent.tutor_agent import TutorAgent
from eval.llm_judge import score_hint

DATA_DIR = Path("data")
FAILED_DIR = Path("data/processed/failed_tests")
OUT_DIR = Path("eval/out")


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _read_json(p: Path) -> Any:
    if not p.exists():
        return None
    raw = p.read_text(encoding="utf-8").strip()
    return json.loads(raw) if raw else None


def _iter_failing_attempts(split: str) -> Iterable[Tuple[int, int, Any]]:
    """
    Yields (problem_id, attempt_id, failed_tests_json) for non-empty failure lists.
    Folder layout assumed:
        data/processed/failed_tests/{split}/{problem_id}/{attempt_id}.json
    """
    split_dir = FAILED_DIR / split
    if not split_dir.exists():
        return
    for pid_dir in sorted([d for d in split_dir.iterdir() if d.is_dir()], key=lambda p: int(p.name)):
        pid = int(pid_dir.name)
        for jf in sorted(pid_dir.glob("*.json"), key=lambda p: int(p.stem)):
            attempt_id = int(jf.stem)
            obj = _read_json(jf)
            if obj is None:
                continue
            if isinstance(obj, list) and len(obj) == 0:
                continue
            yield (pid, attempt_id, obj)


def _load_problem_and_attempt(split: str, pid: int, attempt_id: int) -> Tuple[str, str]:
    """
    Loads:
      - problem text from data/{split}/{pid}/problem.txt (fallback empty string)
      - attempt code from data/{split}/{pid}/attempts/{attempt_id}.py
    """
    prob_txt = DATA_DIR / split / str(pid) / "problem.txt"
    att_py = DATA_DIR / split / str(pid) / "attempts" / f"{attempt_id}.py"
    return _read_text(prob_txt), _read_text(att_py)


def _maybe_ground_truth_hint(split: str, pid: int) -> Optional[str]:
    """
    Returns oracle/teacher hint if present at data/{split}/{pid}/hints.txt; else None.
    """
    p = DATA_DIR / split / str(pid) / "hints.txt"
    txt = _read_text(p).strip()
    return txt or None


def _ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "val", "test"], default="test")
    ap.add_argument("--out", type=str, default=None, help="Path to JSONL output")
    ap.add_argument("--lora-path", type=str, default=None,
                    help="weights/... path for LoRA; if omitted, LoRA block is skipped")
    ap.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--judge-model", type=str, default="gpt-4o-mini")
    ap.add_argument("--limit", type=int, default=None, help="Optional limit for quick runs")
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()

    if args.out is None:
        args.out = f"eval/out/{args.split}_hints.jsonl"

    if args.lora_path is None:
        if (Path("weights") / "adapter_config.json").exists():
            args.lora_path = "weights"

    split_failed_dir = FAILED_DIR / args.split
    if not split_failed_dir.exists():
        print(f"[warn] No failed-tests directory at {split_failed_dir}. "
              "Did you run: python -m data.preprocess ?")

    _ensure_out_dir()

    rows: List[str] = []
    count = 0

    avg = {
        "human": {"sum": 0.0, "n": 0},
        "fine_tuned":  {"sum": 0.0, "n": 0},
        "general":  {"sum": 0.0, "n": 0},
        "agent_fine_tuned": {"sum": 0.0, "n": 0},
        "agent_base": {"sum": 0.0, "n": 0},
    }

    def _acc(which: str, score: Optional[int]) -> None:
        if score is not None:
            avg[which]["sum"] += float(score)
            avg[which]["n"] += 1

    lora_gen: Optional[HintGenerator] = None
    base_gen = HintGenerator(
        model_type="base",
        base_model=args.base_model,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    
    lora_agent: Optional[TutorAgent] = None
    base_agent = TutorAgent(
        model_type="base",
        base_model=args.base_model,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    
    if args.lora_path:
        lora_gen = HintGenerator(
            model_type="fine_tuned",
            fine_tuned_model_path=args.lora_path,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
        )
        lora_agent = TutorAgent(
            model_type="fine_tuned",
            fine_tuned_model_path=args.lora_path,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for pid, attempt_id, failed in _iter_failing_attempts(args.split):
        if args.limit is not None and count >= args.limit:
            break

        problem, user_attempt = _load_problem_and_attempt(args.split, pid, attempt_id)
        gt_hint = _maybe_ground_truth_hint(args.split, pid)

        # Ground-truth
        tutor_gt = {"hint": gt_hint, "score": None, "reason": None}
        if gt_hint:
            s, r = score_hint(
                problem=problem,
                learner_code=user_attempt,
                failed_tests=failed,
                hint=gt_hint,
                model=args.judge_model,
            )
            tutor_gt.update({"score": s, "reason": r})
            _acc("human", s)

        # LoRA model
        tutor_lora = None
        if lora_gen is not None:
            l_hint = lora_gen.generate_hint(problem, user_attempt, failed, Strategy.DIRECT)
            s, r = score_hint(
                problem=problem,
                learner_code=user_attempt,
                failed_tests=failed,
                hint=l_hint,
                model=args.judge_model,
            )
            tutor_lora = {
                "model_name": lora_gen.model_name,
                "hint": l_hint,
                "score": s,
                "reason": r,
            }
            _acc("fine_tuned", s)

        # Base model
        b_hint = base_gen.generate_hint(problem, user_attempt, failed, Strategy.DIRECT)
        s, r = score_hint(
            problem=problem,
            learner_code=user_attempt,
            failed_tests=failed,
            hint=b_hint,
            model=args.judge_model,
        )
        _acc("general", s)
        
        # LoRA agent
        tutor_lora_agent = None
        if lora_agent is not None:
            a_hint, s, r = lora_agent.generate_and_evaluate_hint(problem, user_attempt, failed)
            tutor_lora_agent = {
                "model_name": f"{lora_agent.gen.model_name} (Agent)",
                "hint": a_hint,
                "score": s,
                "reason": r,
            }
            _acc("agent_fine_tuned", s)
        
        # Base agent
        ba_hint, s, r = base_agent.generate_and_evaluate_hint(problem, user_attempt, failed)
        _acc("agent_base", s)

        record: Dict[str, Any] = {
            "split": args.split,
            "problem_id": pid,
            "attempt_id": attempt_id,
            "problem": problem,
            "user_attempt": user_attempt,
            "failed_unit_tests": failed,
            "tutor_ground_truth": tutor_gt,
            "tutor_lora": tutor_lora,
            "tutor_base": {
                "model_name": base_gen.model_name,
                "hint": b_hint,
                "score": s,
                "reason": r,
            },
            "tutor_lora_agent": tutor_lora_agent,
            "tutor_base_agent": {
                "model_name": f"{base_agent.gen.model_name} (Agent)",
                "hint": ba_hint,
                "score": s,
                "reason": r,
            },
        }

        rows.append(json.dumps(record, ensure_ascii=False))
        count += 1

    out_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    print(f"Wrote {count} lines to {out_path}")
    print("Judging uses eval/llm_judge.score_hint (1–5). "
          "If OPENAI_API_KEY is missing, scores will be null with a note.")

    def _mean(which: str) -> Optional[float]:
        n = avg[which]["n"]
        return (avg[which]["sum"] / n) if n else None

    m_h = _mean("human")
    m_f = _mean("fine_tuned")
    m_g = _mean("general")
    m_af = _mean("agent_fine_tuned")
    m_ag = _mean("agent_base")

    print("\nAverage judge score (1–5):")
    print(f"  Human           : {m_h:.2f} ({avg['human']['n']} items)" if m_h is not None else "  Human           : n/a")
    print(f"  Base            : {m_g:.2f} ({avg['general']['n']} items)"  if m_g is not None else "  Base            : n/a")
    print(f"  Fine-tuned      : {m_f:.2f} ({avg['fine_tuned']['n']} items)"  if m_f is not None else "  Fine-tuned      : n/a")
    print(f"  Agent (Base)    : {m_ag:.2f} ({avg['agent_base']['n']} items)"  if m_ag is not None else "  Agent (Base)    : n/a")
    print(f"  Agent (Fine-tuned): {m_af:.2f} ({avg['agent_fine_tuned']['n']} items)"  if m_af is not None else "  Agent (Fine-tuned): n/a")


if __name__ == "__main__":
    main()