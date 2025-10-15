"""MBPP dataset field extraction utilities."""

from typing import Any, Dict, List, Optional, Tuple

def extract_fields(ex: Dict[str, Any], config: str) -> Tuple[str, str, List[str], Optional[str], Optional[List[str]]]:
    """Extract problem, code, tests, setup, and imports from MBPP example based on config."""
    if config == "sanitized":
        problem = ex["prompt"]
        ref_code = ex["code"]
        test_list = ex["test_list"]
        test_setup_code = None
        test_imports = ex.get("test_imports") or []
    else:
        problem = ex["text"]
        ref_code = ex["code"]
        test_list = ex["test_list"]
        test_setup_code = ex.get("test_setup_code") or None
        test_imports = None
    return problem, ref_code, test_list, test_setup_code, test_imports
