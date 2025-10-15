"""Prompt templates, strategy specification, and text filtering for tutoring hint generation."""

import re
from enum import Enum

HINT_PROMPT = """Problem:
{problem}

Learner code:
{learner_code}

Failed unit tests:
```json
{failed_tests_json}
```

Write one short, actionable hint (1–2 sentences). No code. Do not quote the tests verbatim.
Hint: """

class Strategy(Enum):
    DIRECT = "direct"
    QUESTIONS = "questions"
    STEP_BY_STEP = "step_by_step"

STRATEGY_INSTRUCTIONS = {
    Strategy.DIRECT: (
        "Provide a concise, actionable hint that points to the failure's root cause "
        "without revealing the full solution or writing code."
    ),
    Strategy.QUESTIONS: (
        "Ask 1–2 guiding questions that steer the learner toward the issue "
        "without revealing the solution or writing code."
    ),
    Strategy.STEP_BY_STEP: (
        "Suggest only the first concrete step the learner should take. "
        "Do not give the final solution or multiple steps."
    ),
}

def build_hint_prompt(*, problem: str, learner_code: str, failed_tests_json: str, strategy: Strategy) -> str:
    """Render the base prompt and append strategy guidance."""
    base = HINT_PROMPT.format(
        problem=problem.strip(),
        learner_code=learner_code.strip(),
        failed_tests_json=failed_tests_json,
    )
    strategy_block = STRATEGY_INSTRUCTIONS[strategy]
    return f"{base}\n\nStrategy:\n{strategy_block}\n"

def leak_filter(text: str) -> str:
    """Clean model output."""
    if not text:
        return ""
    t = text.strip()

    t = re.sub(r"```[\s\S]*?```", "", t).strip()

    t = re.sub(r"^\s*Hint:\s*", "", t, flags=re.IGNORECASE)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()]
    t = " ".join(sentences[:2])

    return re.sub(r"\s+", " ", t).strip()