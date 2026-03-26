"""
Judge checker classes for the judge system.
"""

import os
import re
from typing import Any, Dict, List

import yaml

from .prompts import (
    BLACKBOX_CATEGORIES,
    BLACKBOX_PROMPT,
    GLASSBOX_CATEGORIES,
    GLASSBOX_PROMPT,
    SOPHISTICATION_TIERS,
)
from .helpers import parse_json_verdict


class RegexChecker:
    """Deterministic string/pattern matching on model output."""

    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(rules_path: str) -> List[Dict]:
        """Load regex rules from a YAML file.

        Supports two formats:
        - A dict with a 'rules' key: {rules: [...]}
        - A flat list of rules: [...]
        """
        if not os.path.exists(rules_path):
            return []
        with open(rules_path, "r") as f:
            data = yaml.safe_load(f)
        if not data:
            return []
        if isinstance(data, list):
            return data
        return data.get("rules", []) if isinstance(data, dict) else []

    def check(self, model_output: str) -> Dict[str, Any]:
        """Run all regex rules against the model output.

        Returns:
            {"verdict": "6/7", "matched": 6, "total": 7, "details": [...]}
        """
        if not self.rules:
            return {
                "verdict": "PASS",
                "matched": 0,
                "total": 0,
                "details": [{"note": "no regex rules defined"}],
                "fraction": "0/0",
            }

        details = []
        required_total = 0
        required_matched = 0

        for rule in self.rules:
            pattern = rule.get("pattern", "")
            name = rule.get("name", "unnamed")
            required = rule.get("required", False)
            description = rule.get("description", "")

            matched = bool(re.search(pattern, model_output))
            detail = {
                "name": name,
                "matched": matched,
                "required": required,
                "description": description,
            }
            details.append(detail)

            if required:
                required_total += 1
                if matched:
                    required_matched += 1

        if required_total == 0:
            verdict = "PASS"
        else:
            verdict = "PASS" if required_matched == required_total else "FAIL"

        return {
            "verdict": verdict,
            "matched": required_matched,
            "total": required_total,
            "details": details,
            "fraction": f"{required_matched}/{required_total}",
        }


class BlackboxChecker:
    """LLM judge comparing model output against baseline (no reasoning trace)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", temperature: float = 0):
        self.model = model
        self.temperature = temperature

    def build_prompt(
        self,
        model_output: str,
        baseline: str,
        source_documents: str,
        task_description: str = "",
    ) -> str:
        """Build the blackbox judge prompt."""
        return BLACKBOX_PROMPT.format(
            task_description=task_description or "(No task description available)",
            source_documents=source_documents,
            baseline=baseline,
            model_output=model_output,
        )

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the judge's response into a structured verdict."""
        verdict = parse_json_verdict(response_text)
        category = verdict.get("category", "UNKNOWN")
        if category not in BLACKBOX_CATEGORIES:
            category = "UNKNOWN"
        return {
            "category": category,
            "justification": verdict.get("justification", ""),
            "raw_response": response_text,
        }


class GlassboxChecker:
    """LLM judge evaluating reasoning trace + output + system prompt for intent."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", temperature: float = 0):
        self.model = model
        self.temperature = temperature

    def build_prompt(
        self,
        system_prompt: str,
        reasoning_trace: str,
        final_output: str,
    ) -> str:
        """Build the glassbox judge prompt."""
        return GLASSBOX_PROMPT.format(
            system_prompt=system_prompt,
            reasoning_trace=reasoning_trace,
            final_output=final_output,
        )

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the judge's response into a structured verdict."""
        verdict = parse_json_verdict(response_text)
        category = verdict.get("category", "UNKNOWN")
        sophistication = verdict.get("sophistication", "UNKNOWN")
        if category not in GLASSBOX_CATEGORIES:
            category = "UNKNOWN"
        if sophistication not in SOPHISTICATION_TIERS:
            sophistication = "UNKNOWN"
        return {
            "category": category,
            "sophistication": sophistication,
            "justification": verdict.get("justification", ""),
            "raw_response": response_text,
        }
