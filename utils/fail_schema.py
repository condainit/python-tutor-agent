"""Failed test schema utilities for Python tutoring."""

from typing import Any, Dict, List

def _clip(s: Any, n: int = 200) -> str:
    if s is None:
        return ""
    s = str(s).replace("\n", " ").strip()
    return (s[: n - 1] + "…") if len(s) > n else s

def _render_call(fn_name: str, args, kwargs, max_len: int = 200) -> str:
    try:
        if isinstance(args, str):
            return _clip(args, max_len)
        args = args or []
        kwargs = kwargs or {}
        args_repr = ", ".join(_clip(repr(a), max_len//3) for a in args)
        kw_repr   = ", ".join(f"{k}={_clip(repr(v), max_len//3)}" for k, v in kwargs.items())
        comma = ", " if args_repr and kw_repr else ""
        return _clip(f"{fn_name}({args_repr}{comma}{kw_repr})", max_len)
    except Exception:
        return f"{fn_name}(…)"

def failed_unit_tests_from_details(
    details: List[Dict[str, Any]],
    *,
    max_items: int = 5,
    per_field_max: int = 200,
) -> List[Dict[str, str]]:
    """Convert grader details into compact JSON list of failed tests and errors."""
    out = []
    for d in details or []:
        if d.get("ok"):
            continue

        name     = d.get("name") or d.get("nodeid") or "unknown_test"
        fn_name  = d.get("fn_name") or d.get("func") or "func"
        call     = d.get("call") or _render_call(fn_name, d.get("args"), d.get("kwargs"), per_field_max)

        expected = d.get("expected")
        actual   = d.get("actual")
        if expected is not None or actual is not None:
            out.append({
                "name": name,
                "call": call,
                "expected": _clip(expected, per_field_max),
                "actual":   _clip(actual,   per_field_max),
                "status": "fail",
            })
            continue

        et = d.get("exc_type")
        em = d.get("error_msg")
        if not et or not em:
            so = (d.get("stdout") or "").strip()
            se = (d.get("stderr") or "").strip()
            em = em or (se or so or "(no output)")
            et = et or d.get("exc") or "Error"

        out.append({
            "name": name,
            "call": call,
            "error_type": _clip(et, per_field_max),
            "error_msg":  _clip(em, per_field_max),
            "status": "error",
        })

        if len(out) >= max_items:
            break

    return out