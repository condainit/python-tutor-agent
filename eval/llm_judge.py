"""LLM-as-a-judge scoring system for evaluating tutoring hint quality."""

from typing import Optional, Tuple, Any
import os
import json
import re

JUDGE_SYSTEM = (
    "You are a strict evaluator of Python tutoring hints.\n"
    "- Judge the hint's pedagogical value and effectiveness for helping a learner understand and fix their code.\n"
    "- Consider both direct guidance and guided questioning approaches as valid tutoring methods.\n"
    "- Penalize hints that include code, reveal full solutions, are completely unrelated to the failures, or are misleading.\n"
    "- Value hints that guide learners to discover solutions through questions or clear explanations.\n"
    "- Be concise and deterministic.\n"
    "\n"
    "Scoring rubric (1–5):\n"
    "1 = Useless/misleading/contains code or solution reveal/irrelevant to the error.\n"
    "2 = Vague or partially incorrect; minimal pedagogical value.\n"
    "3 = Somewhat helpful but incomplete; provides some guidance or raises relevant questions.\n"
    "4 = Clear and pedagogically sound; guides learner effectively through questions or explanations.\n"
    "5 = Excellent pedagogical approach; very clear guidance that helps learner understand and discover the solution."
)

JUDGE_PROMPT = """Problem:
{problem}

Learner code:
{learner_code}

Failed unit tests (JSON):
```json
{failed_tests_json}
```

Hint to evaluate:
{hint}

Return your answer in EXACTLY two lines in this format:
SCORE: <integer 1-5>
REASON: <one short sentence explaining the score; no code, no solution>
"""

def _clamp_score(n: int) -> int:
    """Clamp score to valid range [1, 5]."""
    return max(1, min(5, n))

def _judge_available() -> bool:
    """Check if OpenAI API key is available for judging."""
    return bool(os.getenv("OPENAI_API_KEY"))

def _coerce_json_str(obj: Any) -> str:
    """Convert object to JSON string, handling None and empty cases."""
    if obj is None:
        return "[]"
    if isinstance(obj, (dict, list)):
        return json.dumps(obj, ensure_ascii=False, indent=2)
    s = str(obj).strip()
    return s if s else "[]"

def score_hint(
    *,
    problem: str,
    failed_tests: Any,
    hint: str,
    model: str = "gpt-4o-mini",
    learner_code: str = "",
    ) -> Tuple[Optional[int], Optional[str]]:
    """
    Returns (score, reason). If the LLM output can't be parsed or creds are missing,
    returns (None, <error-or-note>).
    """
    if not _judge_available():
        return (None, "Judge unavailable: OPENAI_API_KEY not set.")

    failed_tests_json = _coerce_json_str(failed_tests)
    user_prompt = JUDGE_PROMPT.format(
        problem=problem or "(omitted)",
        learner_code=learner_code or "(omitted)",
        failed_tests_json=failed_tests_json,
        hint=hint or "(empty)",
    )

    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=256,
        )
        out = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return (None, f"Judge error: {e}")

    m_score = re.search(r"(?im)^\s*SCORE:\s*([1-5])\s*$", out)
    m_reason = re.search(r"(?im)^\s*REASON:\s*(.+)$", out)
    if not m_score:
        m_score = re.search(r"(?m)\b([1-5])\b", out)
    score = int(m_score.group(1)) if m_score else None
    score = _clamp_score(score) if score is not None else None
    reason = m_reason.group(1).strip() if m_reason else None
    if score is not None and not reason:
        reason = "No reason provided."
    return score, reason