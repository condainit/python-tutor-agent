"""Tutoring agent with reasoning and self-evaluation capabilities."""

from __future__ import annotations
from typing import Any, Optional, Tuple

from eval.inference import HintGenerator
from agent.prompts import Strategy
from agent.reasoning import ReasoningEngine
from eval.llm_judge import score_hint


_DEFAULT_MODEL_TYPE = "fine_tuned"  # "fine_tuned" | "base"
_DEFAULT_FINE_TUNED_MODEL_PATH = "weights"
_DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
_DEFAULT_MAX_NEW_TOKENS = 128
_DEFAULT_TEMPERATURE = 0.2


class TutorAgent:
    """Tutoring agent with reasoning and self-evaluation capabilities."""

    def __init__(
        self,
        *,
        model_type: str = _DEFAULT_MODEL_TYPE,
        fine_tuned_model_path: Optional[str] = _DEFAULT_FINE_TUNED_MODEL_PATH,
        base_model: str = _DEFAULT_BASE_MODEL,
        max_new_tokens: int = _DEFAULT_MAX_NEW_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
    ) -> None:
        """Initialize tutoring agent with reasoning capabilities."""
        self.gen = HintGenerator(
            model_type=model_type,
            fine_tuned_model_path=fine_tuned_model_path,
            base_model=base_model,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        self.reasoning = ReasoningEngine()

    def hint(self, *, problem: str, learner_code: str, failed_tests_json: Any) -> str:
        """Generate hint using reasoning-based adaptive strategy with self-evaluation."""
        hint, score, reason = self.generate_and_evaluate_hint(problem, learner_code, failed_tests_json)
        return hint
    
    def generate_and_evaluate_hint(self, problem: str, learner_code: str, failed_tests_json: Any) -> Tuple[str, int, str]:
        """Generate hint with multiple adaptation attempts until score >= 4 or all strategies exhausted."""
        # 1. Generate initial adaptive hint
        hint = self._generate_adaptive_hint(problem, learner_code, failed_tests_json)
        score, reason = score_hint(
            problem=problem,
            failed_tests=failed_tests_json,
            hint=hint,
            learner_code=learner_code
        )
        
        # 2. If score is low, try multiple adaptation strategies
        if score < 4:
            best_hint, best_score, best_reason = hint, score, reason
            
            adaptations = [
                # Temperature variations
                ("temperature", 0.3),
                ("temperature", 0.7),
                ("temperature", 0.9),
                ("temperature", 1.0),
                
                # Strategy variations
                ("strategy_override", "direct"),
                ("strategy_override", "questions"),
                ("strategy_override", "step_by_step"),
                
                # Combined approaches
                ("combined", (0.3, "direct")),
                ("combined", (0.7, "questions")),
                ("combined", (0.9, "questions")),
                ("combined", (0.7, "step_by_step")),
                ("combined", (0.3, "step_by_step")),
            ]
            
            for adaptation_type, adaptation_value in adaptations:
                alt_hint = self._generate_alternative_hint(
                    problem, learner_code, failed_tests_json, 
                    adaptation_type, adaptation_value
                )
                alt_score, alt_reason = score_hint(
                    problem=problem,
                    failed_tests=failed_tests_json,
                    hint=alt_hint,
                    learner_code=learner_code
                )
                
                if alt_score > best_score:
                    best_hint, best_score, best_reason = alt_hint, alt_score, alt_reason
                
                if best_score >= 4:
                    break
            
            return best_hint, best_score, best_reason
        
        return hint, score, reason
    
    def _generate_adaptive_hint(self, problem: str, learner_code: str, failed_tests_json: Any) -> str:
        """Generate hint using reasoning-based adaptive strategy."""
        # 1. Analyze error complexity
        complexity = self.reasoning.analyze_error_complexity(failed_tests_json)
        
        # 2. Plan tutoring strategy
        strategy_name = self.reasoning.plan_tutoring_strategy(
            complexity,
            len(failed_tests_json) if isinstance(failed_tests_json, list) else 1,
        )
        strategy_map = {
            "direct": Strategy.DIRECT,
            "questions": Strategy.QUESTIONS,
            "step_by_step": Strategy.STEP_BY_STEP,
        }
        strategy = strategy_map[strategy_name]

        # 3. Generate hint with strategy-aware prompt
        hint = self.gen.generate_hint(problem, learner_code, failed_tests_json, strategy)
        
        # 4. Return model output
        return hint
    
    def _generate_alternative_hint(self, problem: str, learner_code: str, failed_tests_json: Any, adaptation_type: str, adaptation_value: Any) -> str:
        """Generate alternative hint using strategy-aware generation with different parameters."""
        complexity = self.reasoning.analyze_error_complexity(failed_tests_json)
        strategy_name = self.reasoning.plan_tutoring_strategy(
            complexity,
            len(failed_tests_json) if isinstance(failed_tests_json, list) else 1,
        )
        strategy_map = {
            "direct": Strategy.DIRECT,
            "questions": Strategy.QUESTIONS,
            "step_by_step": Strategy.STEP_BY_STEP,
        }
        default_strategy = strategy_map[strategy_name]

        if adaptation_type == "temperature":
            return self.gen.generate_hint(
                problem,
                learner_code,
                failed_tests_json,
                default_strategy,
                temperature=adaptation_value,
            )
        elif adaptation_type == "strategy_override":
            strategy = strategy_map.get(adaptation_value, default_strategy)
            return self.gen.generate_hint(
                problem,
                learner_code,
                failed_tests_json,
                strategy,
            )
        elif adaptation_type == "combined":
            temperature, strategy_name = adaptation_value
            strategy = strategy_map.get(strategy_name, default_strategy)
            return self.gen.generate_hint(
                problem,
                learner_code,
                failed_tests_json,
                strategy,
                temperature=temperature,
            )
        else:
            return self.gen.generate_hint(
                problem,
                learner_code,
                failed_tests_json,
                default_strategy,
                temperature=0.7,
            )

