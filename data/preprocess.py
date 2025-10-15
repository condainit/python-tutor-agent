"""Data preprocessing for Python tutoring dataset."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from datasets import load_dataset
from data.mbpp_adapter import extract_fields
from eval.grader import grade_each_assert
from utils.fail_schema import failed_unit_tests_from_details

DATA_DIR = Path(__file__).resolve().parent            # data/
OUT_DIR = DATA_DIR / "processed"                      # data/processed
FT_DIR = OUT_DIR / "failed_tests"                     # data/processed/failed_tests

_MBPP_CONFIG = "sanitized"
_MBPP_SPLIT = "test"

def _read_text(p: Path) -> str:
    """Read text file content with UTF-8 encoding."""
    return p.read_text(encoding="utf-8")

def _read_lines(p: Path) -> List[str]:
    """Read text file and split into lines."""
    return _read_text(p).splitlines()

def _attempt_path(prob_dir: Path, i: int) -> Path:
    """Construct path to attempt file for given problem directory and attempt number."""
    return prob_dir / "attempts" / f"{i}.py"

_MBPP_INDEX: Dict[int, Dict[str, Any]] = {}

def _init_mbpp_index() -> None:
    """Load MBPP dataset and build task_id to example mapping."""
    global _MBPP_INDEX
    if _MBPP_INDEX:
        return
    ds = load_dataset("google-research-datasets/mbpp", _MBPP_CONFIG, split=_MBPP_SPLIT)
    _MBPP_INDEX = {}
    for ex in ds:
        try:
            tid = int(ex.get("task_id", -1))
        except Exception:
            continue
        if tid >= 0:
            _MBPP_INDEX[tid] = ex

def _tests_for_problem(task_id: int) -> Tuple[List[str], Optional[str], Optional[List[str]]]:
    """Retrieve test cases, setup code, and imports for MBPP task from dataset."""
    _init_mbpp_index()
    ex = _MBPP_INDEX.get(int(task_id))
    if ex is None:
        raise FileNotFoundError(
            f"No MBPP sanitized/test row found for task_id={task_id}. "
            f"Ensure data/{{split}}/{task_id}/ was sourced from MBPP test."
        )
    _, _, test_list, setup_code, test_imports = extract_fields(ex, _MBPP_CONFIG)
    return test_list, setup_code, test_imports

def _failed_tests_json(
    learner_code: str,
    test_list: List[str],
    setup: Optional[str],
    imports: Optional[List[str]],
) -> str:
    """Run tests against learner code and return failed test details as JSON string."""
    grade = grade_each_assert(
        candidate_code=learner_code,
        test_list=test_list,
        test_setup_code=setup,
        test_imports=imports,
    )
    items = failed_unit_tests_from_details(grade.get("details") or [])
    return json.dumps(items, ensure_ascii=False, indent=2)

def _process_split(split: str) -> List[Dict[str, Any]]:
    """Walk data directory, run tests, and create training rows with failed test JSON files."""
    rows: List[Dict[str, Any]] = []
    split_dir = DATA_DIR / split
    if not split_dir.exists():
        return rows

    for prob_dir in sorted([p for p in split_dir.iterdir() if p.is_dir()]):
        problem_id = int(prob_dir.name)
        prompt = _read_text(prob_dir / "prompt.txt").strip()
        hints = _read_lines(prob_dir / "hints.txt")

        test_list, setup_code, test_imports = _tests_for_problem(problem_id)

        (FT_DIR / split / str(problem_id)).mkdir(parents=True, exist_ok=True)

        for i in range(1, 6):
            code_path = _attempt_path(prob_dir, i)
            if not code_path.exists():
                raise FileNotFoundError(f"Missing attempt file: {code_path}")
            learner_code = _read_text(code_path)

            failed_json = _failed_tests_json(learner_code, test_list, setup_code, test_imports)

            ft_path = FT_DIR / split / str(problem_id) / f"{i}.json"
            ft_path.write_text(failed_json, encoding="utf-8")

            hint = hints[i-1].strip() if i-1 < len(hints) else ""
            rows.append({
                "split": split,
                "problem_id": problem_id,
                "attempt_id": i,
                "problem": prompt,
                "learner_code": learner_code,
                "failed_tests_path": ft_path.relative_to(OUT_DIR).as_posix(),
                "hint": hint,
            })
    return rows

def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    """Write list of dictionaries as JSONL file with UTF-8 encoding."""
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

def main():
    """Process all data splits and generate training JSONL files."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    SPLITS = ("train", "val", "test")

    counts = {}
    for split in SPLITS:
        rows = _process_split(split)
        counts[split] = len(rows)
        _write_jsonl(OUT_DIR / f"lora_{split}.jsonl", rows)

    msg = " | ".join(f"{s}: {counts.get(s,0)}" for s in SPLITS)
    print(f"Wrote rows into {OUT_DIR} -> {msg}")

if __name__ == "__main__":
    main()