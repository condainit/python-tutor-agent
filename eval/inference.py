"""Model inference components for Python tutoring hint generation."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from agent.prompts import leak_filter, Strategy, build_hint_prompt


class HFModelClient:
    """Handles model loading and text generation for both base and LoRA fine-tuned models."""

    def __init__(
        self,
        model_path: str,
        device_map: str = "auto",
    ) -> None:
        adapter_config_path = Path(model_path) / "adapter_config.json"
        
        if adapter_config_path.exists():
            self._load_lora_model(model_path, device_map)
        else:
            self._load_full_model(model_path, device_map)
    
    def _load_lora_model(self, adapter_path: str, device_map: str) -> None:
        """Load base model from HF Hub and apply LoRA adapter from local path."""
        with open(Path(adapter_path) / "adapter_config.json", "r") as f:
            adapter_config = json.load(f)
        base_model_name = adapter_config["base_model_name_or_path"]
        
        self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, use_fast=True)
        
        kwargs: Dict[str, Any] = {"device_map": device_map}
        base_model = AutoModelForCausalLM.from_pretrained(base_model_name, **kwargs)
        
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        self.model.eval()
    
    def _load_full_model(self, model_path: str, device_map: str) -> None:
        """Load complete model directly from HF Hub or local path (no adapters)."""
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        kwargs: Dict[str, Any] = {"device_map": device_map}
        self.model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
        self.model.eval()

    @torch.inference_mode()
    def generate(
        self,
        user_prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.2,
        do_sample: bool = False,
    ) -> str:
        """Generate text completion from prompt and apply leak filtering."""
        prompt_text = user_prompt
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.model.device)
        
        generation_kwargs = {
            **inputs,
            "do_sample": do_sample,
            "max_new_tokens": max_new_tokens,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = temperature
            
        output_ids = self.model.generate(**generation_kwargs)[0]
        full_text = self.tokenizer.decode(output_ids, skip_special_tokens=True)

        if full_text.startswith(prompt_text):
            gen = full_text[len(prompt_text):]
        else:
            gen = full_text

        return leak_filter(gen).strip()


class HintGenerator:
    """Generates tutoring hints using either fine-tuned or base models."""

    def __init__(
        self,
        model_type: str,
        fine_tuned_model_path: Optional[str] = None,
        base_model: str = "Qwen/Qwen2.5-3B-Instruct",
        max_new_tokens: int = 128,
        temperature: float = 0.2,
    ) -> None:
        """Configure model type and create appropriate HFModelClient instance."""
        self.model_type = model_type
        self.fine_tuned_model_path = fine_tuned_model_path
        self.base_model = base_model
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        if model_type == "fine_tuned":
            if not fine_tuned_model_path:
                raise ValueError("model_type='fine_tuned' requires fine_tuned_model_path")
            self.client = HFModelClient(fine_tuned_model_path)
            self.model_name = Path(fine_tuned_model_path).name
        elif model_type == "base":
            self.client = HFModelClient(base_model)
            self.model_name = base_model
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def generate_hint(
        self,
        problem: str,
        user_code: str,
        failed_tests_json: Any,
        strategy: Strategy,
        temperature: Optional[float] = None,
    ) -> str:
        """Format tutoring prompt with strategy and generate hint using configured model."""
        failed_str = json.dumps(failed_tests_json, ensure_ascii=False, indent=2)
        user_prompt = build_hint_prompt(
            problem=problem,
            learner_code=user_code,
            failed_tests_json=failed_str,
            strategy=strategy,
        )
        return self.client.generate(
            user_prompt=user_prompt,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature if temperature is None else temperature,
            do_sample=True,
        )
