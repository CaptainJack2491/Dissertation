"""
Prompt templates for the judge system.
"""

import os

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_prompt(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


BLACKBOX_PROMPT = load_prompt("blackbox_prompt.md")
GLASSBOX_PROMPT = load_prompt("glassbox_prompt.md")


BLACKBOX_CATEGORIES = [
    "ACCURATE",
    "DECEPTIVE_FRAMING",
    "OMITTED_CRITICAL",
    "FABRICATED",
]
GLASSBOX_CATEGORIES = [
    "ROBUST_HONEST",
    "CONSIDERED_HONEST",
    "COMPLIANT_DECEPTION",
    "FAILED_DECEPTION",
    "UNINTENTIONAL_FAILURE",
]
SOPHISTICATION_TIERS = ["NAIVE", "REACTIVE", "TACTICAL", "STRATEGIC"]
