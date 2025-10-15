"""Code grading utilities for Python tutoring evaluation."""

import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

TRUNC = 500

def _run(code: str, stdin: str = "", timeout: int = 5) -> Dict[str, str | int]:
    """Run Python code in a temp file; return exit code/stdout/stderr."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "main.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            proc = subprocess.run(
                [sys.executable, path],
                input=stdin.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.decode(),
                "stderr": proc.stderr.decode(),
            }
        except subprocess.TimeoutExpired:
            return {"exit_code": 124, "stdout": "", "stderr": "TIMEOUT"}

def _prelude(test_setup_code: Optional[str], test_imports: Optional[List[str]]) -> str:
    imports_block = "\n".join(test_imports or [])
    parts: List[str] = []
    if imports_block.strip():
        parts.append(imports_block)
    if test_setup_code:
        parts.append(test_setup_code)
    return "\n\n".join(parts)

def grade_each_assert(
    candidate_code: str,
    test_list: List[str],
    test_setup_code: Optional[str] = None,
    test_imports: Optional[List[str]] = None,
    timeout: int = 5,
) -> Dict[str, Any]:
    """Execute each test independently and return pass/fail counts with details."""
    pre = _prelude(test_setup_code, test_imports)
    passed = 0
    details = []

    for i, test in enumerate(test_list):
        name = f"assert_{i+1}"
        program = "\n\n".join([pre, candidate_code, test]).strip()
        out = _run(program, timeout=timeout)
        ok = out["exit_code"] == 0
        if ok:
            passed += 1
        details.append(
            {
                "name": name,
                "ok": ok,
                "stdout": (out["stdout"] or "")[:TRUNC],
                "stderr": (out["stderr"] or "")[:TRUNC],
            }
        )

    failed = len(test_list) - passed
    return {"passed": passed, "failed": failed, "details": details}
