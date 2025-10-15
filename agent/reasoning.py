"""Reasoning engine for adaptive tutoring strategy selection."""

import json
from typing import Any


class ReasoningEngine:
    """Analyzes errors and plans tutoring strategy based on complexity."""
    
    def analyze_error_complexity(self, failed_tests_json: Any) -> str:
        """Analyze error patterns and determine complexity level."""
        if isinstance(failed_tests_json, str):
            tests = json.loads(failed_tests_json)
        else:
            tests = failed_tests_json
        
        if not tests:
            return "simple"
        
        error_types = set()
        error_count = len(tests)
        
        for test in tests:
            if test.get("status") == "error":
                error_type = test.get("error_type", "Error")
                error_types.add(error_type)
        
        if error_count == 1 and len(error_types) == 1:
            return "simple"
        elif error_count <= 3 and len(error_types) <= 2:
            return "moderate"
        else:
            return "complex"
    
    def plan_tutoring_strategy(self, complexity: str, error_count: int) -> str:
        """Plan tutoring approach based on complexity and error count."""
        if complexity == "simple":
            return "direct"
        elif complexity == "moderate":
            return "questions"
        else:
            return "step_by_step"
