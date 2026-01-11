"""
Provider abstraction layer.
Handles different LLM providers with OpenAI-compatible APIs and reasoning extraction.
"""
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from openai import OpenAI
from config_loader import ProviderConfig, ModelConfig


@dataclass
class ReasoningStep:
    """A reasoning step from the model."""
    content: str
    type: str = "reasoning"  # "reasoning", "tool_call", "tool_result"
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None
    tool_result: Optional[str] = None
    is_final_response: bool = False


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: Optional[str] = None
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Any = None


class ProviderAdapter(ABC):
    """Base class for provider adapters."""

    def __init__(self, provider_config: ProviderConfig, model_config: ModelConfig):
        self.provider_config = provider_config
        self.model_config = model_config

    @abstractmethod
    def call(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Make an API call and return a unified response."""
        pass

    @abstractmethod
    def extract_reasoning(self, response: Any) -> List[ReasoningStep]:
        """Extract reasoning steps from provider response."""
        pass

    def _merge_extra_body(self, extra_body: Dict[str, Any]) -> Dict[str, Any]:
        """Merge model extra_body with provider extra_body."""
        merged = self.provider_config.extra_body.copy()
        merged.update(extra_body)
        return merged


class OpenAIProviderAdapter(ProviderAdapter):
    """Adapter for OpenAI-compatible APIs (OpenAI, OpenRouter, Together, etc.)."""

    def __init__(self, provider_config: ProviderConfig, model_config: ModelConfig):
        super().__init__(provider_config, model_config)
        self.client = OpenAI(
            base_url=provider_config.base_url,
            api_key=provider_config.api_key
        )

    def call(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Make an API call via OpenAI-compatible endpoint."""
        extra_body = self._merge_extra_body(self.model_config.extra_body)

        response = self.client.chat.completions.create(
            model=self.model_config.id,
            messages=messages,
            tools=tools if tools else None,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            extra_body=extra_body if extra_body else None
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> LLMResponse:
        """Parse OpenAI-compatible response."""
        # Extract usage
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        message = response.choices[0].message

        # Extract content and reasoning
        content = message.content or ""
        reasoning = None

        # Try to get reasoning from different sources
        # 1. Check for reasoning_content (OpenRouter)
        if hasattr(message, 'reasoning_content') and message.reasoning_content:
            reasoning = message.reasoning_content

        # 2. Check for reasoning_details (structured)
        elif hasattr(message, 'reasoning_details') and message.reasoning_details:
            reasoning = self._extract_from_reasoning_details(message.reasoning_details)

        # 3. Regex fallback for <thinking> tags
        else:
            thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
            if thought_match:
                reasoning = thought_match.group(2).strip()
                content = content.replace(thought_match.group(0), "").strip()

        # Extract tool calls
        tool_calls = []
        has_tool_calls = False
        if message.tool_calls:
            has_tool_calls = True
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        # If there are tool calls, content should be None (reasoning is in the reasoning field)
        if has_tool_calls:
            content = None

        # Build reasoning steps
        reasoning_steps = []
        if reasoning:
            reasoning_steps.append(ReasoningStep(content=reasoning, type="reasoning"))

        # Add final response if no tool calls
        if not tool_calls and content:
            reasoning_steps.append(ReasoningStep(
                content=content,
                type="reasoning",
                is_final_response=True
            ))

        return LLMResponse(
            content=content,
            reasoning_steps=reasoning_steps,
            tool_calls=tool_calls,
            usage=usage,
            raw_response=response
        )

    def _extract_from_reasoning_details(self, reasoning_details: List[Dict]) -> str:
        """Extract reasoning text from structured reasoning_details."""
        reasoning_parts = []
        for item in reasoning_details:
            if item.get("type") == "reasoning.text":
                reasoning_parts.append(item.get("text", ""))
        return "\n".join(reasoning_parts).strip()

    def extract_reasoning(self, response: Any) -> List[ReasoningStep]:
        """Extract reasoning steps from raw response."""
        parsed = self._parse_response(response)
        return parsed.reasoning_steps


class GoogleProviderAdapter(ProviderAdapter):
    """Adapter for Google's Generative Language API."""

    def __init__(self, provider_config: ProviderConfig, model_config: ModelConfig):
        super().__init__(provider_config, model_config)
        # Google uses a different SDK, but we can use OpenAI-compatible endpoint
        self.client = OpenAI(
            base_url=provider_config.base_url,
            api_key=provider_config.api_key
        )

    def call(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Make an API call via Google Generative Language API."""
        extra_body = self._merge_extra_body(self.model_config.extra_body)

        response = self.client.chat.completions.create(
            model=self.model_config.id,
            messages=messages,
            tools=tools if tools else None,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            extra_body=extra_body if extra_body else None
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> LLMResponse:
        """Parse Google-compatible response."""
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        message = response.choices[0].message
        content = message.content or ""

        # Google doesn't typically output structured reasoning in this format
        # Just return content
        reasoning_steps = []
        if content:
            reasoning_steps.append(ReasoningStep(
                content=content,
                type="reasoning",
                is_final_response=True
            ))

        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=content,
            reasoning_steps=reasoning_steps,
            tool_calls=tool_calls,
            usage=usage,
            raw_response=response
        )

    def extract_reasoning(self, response: Any) -> List[ReasoningStep]:
        """Extract reasoning steps from raw response."""
        parsed = self._parse_response(response)
        return parsed.reasoning_steps


class AnthropicProviderAdapter(ProviderAdapter):
    """Adapter for Anthropic's direct API."""

    def __init__(self, provider_config: ProviderConfig, model_config: ModelConfig):
        super().__init__(provider_config, model_config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=provider_config.api_key
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def call(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Make an API call via Anthropic API."""
        # Convert OpenAI-style messages to Anthropic format
        system_prompt = None
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_prompt = content
            elif role == "user":
                anthropic_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                # Check for tool calls in the message
                if msg.get("tool_calls"):
                    # Anthropic uses content blocks for tool calls
                    blocks = [{"type": "text", "text": content or ""}]
                    for tc in msg.get("tool_calls", []):
                        blocks.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": blocks
                    })
                else:
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": content
                    })
            elif role == "tool":
                # Tool result
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id"),
                            "content": msg.get("content")
                        }
                    ]
                })

        # Build thinking config from extra_body
        extra_body = self._merge_extra_body(self.model_config.extra_body)
        thinking_config = extra_body.get("thinking", {"type": "enabled", "budget_tokens": 10000})

        response = self.client.messages.create(
            model=self.model_config.id,
            max_tokens=self.model_config.max_tokens or 16000,
            thinking=thinking_config,
            system=system_prompt,
            messages=anthropic_messages
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> LLMResponse:
        """Parse Anthropic response with content blocks."""
        # Extract usage
        usage = {}
        if hasattr(response, "usage"):
            usage = {
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0)
            }

        # Parse content blocks
        reasoning_content = ""
        final_content = ""
        reasoning_steps = []

        for block in response.content:
            if block.type == "thinking":
                # Extract reasoning from thinking block
                if hasattr(block, "thinking") and block.thinking:
                    reasoning_content += block.thinking + "\n"
                    reasoning_steps.append(ReasoningStep(
                        content=block.thinking,
                        type="reasoning"
                    ))
            elif block.type == "text":
                final_content += block.text + "\n"

        # Clean up
        reasoning_content = reasoning_content.strip()
        final_content = final_content.strip()

        # Check for tool use blocks (Anthropic tool use)
        tool_calls = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })

        # Build response
        if tool_calls:
            # If there are tool calls, content is None
            pass
        elif final_content:
            # Final response
            reasoning_steps.append(ReasoningStep(
                content=final_content,
                type="reasoning",
                is_final_response=True
            ))

        return LLMResponse(
            content=final_content if not tool_calls else None,
            reasoning_steps=reasoning_steps,
            tool_calls=tool_calls,
            usage=usage,
            raw_response=response
        )

    def extract_reasoning(self, response: Any) -> List[ReasoningStep]:
        """Extract reasoning steps from raw response."""
        parsed = self._parse_response(response)
        return parsed.reasoning_steps


class MoonshotProviderAdapter(ProviderAdapter):
    """Adapter for Moonshot AI (Kimi-K2) using proprietary token format for tool calls."""

    def __init__(self, provider_config: ProviderConfig, model_config: ModelConfig):
        super().__init__(provider_config, model_config)
        self.client = OpenAI(
            base_url=provider_config.base_url,
            api_key=provider_config.api_key
        )

    def call(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Make an API call via Moonshot AI endpoint."""
        extra_body = self._merge_extra_body(self.model_config.extra_body)

        response = self.client.chat.completions.create(
            model=self.model_config.id,
            messages=messages,
            tools=tools if tools else None,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            extra_body=extra_body if extra_body else None
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> LLMResponse:
        """Parse Moonshot AI response with proprietary token format."""
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        message = response.choices[0].message
        content = message.content or ""

        # Extract reasoning from various sources
        reasoning = None

        # 1. Check for reasoning_content attribute (OpenRouter structured output)
        if hasattr(message, 'reasoning_content') and message.reasoning_content:
            reasoning = message.reasoning_content

        # 2. Check for <thinking> tags in content
        if not reasoning:
            thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
            if thought_match:
                reasoning = thought_match.group(2).strip()
                content = content.replace(thought_match.group(0), "").strip()

        # DEBUG: Check for OpenAI tool_calls first
        openai_tool_calls = []
        has_openai_tc = hasattr(message, 'tool_calls') and message.tool_calls
        if has_openai_tc:
            for tc in message.tool_calls:
                openai_tool_calls.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        # Extract tool calls from proprietary Kimi-K2 token format
        proprietary_tool_calls = self._extract_tool_calls(content)

        # Debug output
        has_prop_tc = len(proprietary_tool_calls) > 0
        print(f"  [MoonshotAdapter] content_len={len(content)}, has_reasoning={bool(reasoning)}, has_openai_tc={has_openai_tc}, has_proprietary_tc={has_prop_tc}")

        # Use OpenAI tool_calls if available, otherwise use proprietary
        tool_calls = openai_tool_calls if openai_tool_calls else proprietary_tool_calls

        # Clean tool calls from content
        clean_content = content
        if tool_calls:
            clean_content = self._remove_tool_tokens(clean_content)

        # Build reasoning steps
        reasoning_steps = []

        # Add reasoning if present (either from reasoning_content or <thinking> tags)
        if reasoning:
            reasoning_steps.append(ReasoningStep(content=reasoning, type="reasoning"))

        # When there are tool calls, the content is the model's reasoning about tool selection
        if tool_calls and clean_content:
            reasoning_steps.append(ReasoningStep(
                content=clean_content,
                type="reasoning"
            ))

        # Add final response content if present and no tool calls
        if not tool_calls and clean_content:
            reasoning_steps.append(ReasoningStep(
                content=clean_content,
                type="reasoning",
                is_final_response=True
            ))

        return LLMResponse(
            content=clean_content if not tool_calls else None,
            reasoning_steps=reasoning_steps,
            tool_calls=tool_calls,
            usage=usage,
            raw_response=response
        )

    def _extract_tool_calls(self, content: str) -> List[Dict]:
        """Extract tool calls from Kimi-K2 proprietary token format."""
        if '<|tool_calls_section_begin|>' not in content:
            return []

        # Pattern to match Kimi-K2 tool call format:
        # <|tool_call_begin|>functions.read_file:1<|tool_call_argument_begin|>{"file_path": "..."}<|tool_call_end|>
        pattern = r"<\|tool_call_begin\|>\s*(?P<tool_call_id>[\w\.]+:\d+)\s*<\|tool_call_argument_begin\|>\s*(?P<function_arguments>.*?)\s*<\|tool_call_end\|>"

        tool_calls = []
        tool_calls_section_match = re.search(
            r"<\|tool_calls_section_begin\|>(.*?)<\|tool_calls_section_end\|>",
            content,
            re.DOTALL
        )

        if not tool_calls_section_match:
            return []

        section_content = tool_calls_section_match.group(1)

        for match in re.finditer(pattern, section_content, re.DOTALL):
            function_id = match.group("tool_call_id")
            function_args = match.group("function_arguments")

            # Parse function name from ID: functions.read_file:0 -> read_file
            function_name = function_id.split('.')[1].split(':')[0]

            # Generate a proper UUID-style ID for compatibility
            tool_id = f"tc_{len(tool_calls)}"

            tool_calls.append({
                "id": tool_id,
                "type": "function",
                "function": {
                    "name": function_name,
                    "arguments": function_args
                }
            })

        return tool_calls

    def _remove_tool_tokens(self, content: str) -> str:
        """Remove proprietary tool call tokens from content."""
        # Remove the entire tool calls section
        content = re.sub(
            r"<\|tool_calls_section_begin\|>.*?<\|tool_calls_section_end\||>",
            "",
            content,
            flags=re.DOTALL
        )
        return content.strip()

    def extract_reasoning(self, response: Any) -> List[ReasoningStep]:
        """Extract reasoning steps from raw response."""
        parsed = self._parse_response(response)
        return parsed.reasoning_steps


def create_provider_adapter(provider_config: ProviderConfig, model_config: ModelConfig) -> ProviderAdapter:
    """Factory function to create the appropriate provider adapter."""
    provider_name = provider_config.name.lower()

    adapters = {
        "openai": OpenAIProviderAdapter,
        "openrouter": OpenAIProviderAdapter,
        "together": OpenAIProviderAdapter,
        "google": GoogleProviderAdapter,
        "anthropic": AnthropicProviderAdapter,
        "moonshot": MoonshotProviderAdapter,
    }

    adapter_class = adapters.get(provider_name)
    if not adapter_class:
        raise ValueError(f"Unsupported provider: {provider_name}")

    return adapter_class(provider_config, model_config)
