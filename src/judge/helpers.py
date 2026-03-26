"""
Data extraction helpers for the judge system.
"""

import json
import re
from typing import Any, Dict, List


def extract_model_output(conversation: List[Dict]) -> str:
    """Extract model output from the last create_file tool call in the conversation."""
    for msg in reversed(conversation):
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            continue
        for tc in reversed(tool_calls):
            func = tc.get("function", {})
            if func.get("name") == "create_file":
                try:
                    args = json.loads(func.get("arguments", "{}"))
                    return args.get("content", "")
                except (json.JSONDecodeError, KeyError):
                    continue

    for msg in reversed(conversation):
        if msg.get("role") == "assistant" and msg.get("content"):
            return msg.get("content", "")

    return ""


def extract_reasoning_trace(conversation: List[Dict]) -> str:
    """Extract all reasoning fields from assistant messages."""
    reasoning_parts = []
    for msg in conversation:
        if msg.get("role") == "assistant" and msg.get("reasoning"):
            reasoning_parts.append(msg["reasoning"])
    return (
        "\n\n---\n\n".join(reasoning_parts)
        if reasoning_parts
        else "(no reasoning trace available)"
    )


def extract_system_prompt(conversation: List[Dict]) -> str:
    """Extract the system prompt from the conversation."""
    for msg in conversation:
        if msg.get("role") == "system":
            return msg.get("content", "")
    return ""


def parse_json_verdict(text: str) -> Dict[str, Any]:
    """Extract the last JSON object from the judge's response text."""
    code_block_pattern = r"```(?:json)?\s*(\{[^`]+\})\s*```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[-1].strip())
        except json.JSONDecodeError:
            pass

    brace_pattern = r"\{[^{}]*\}"
    matches = re.findall(brace_pattern, text, re.DOTALL)
    for match in reversed(matches):
        try:
            parsed = json.loads(match)
            if "category" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    return {}
