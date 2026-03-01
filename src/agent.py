"""
Simple agent using OpenAI SDK directly.
"""
import json
import os
import re
import datetime
from typing import List, Dict
from vfs import VFS
from openai import OpenAI
from config_loader import ProviderConfig, ModelConfig
from tools import tools, available_functions
from logger import get_logger

# Get logger instance
logger = get_logger("experiment")


class Agent:
    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        model: str = "unknown",
        base_url: str = None,
        api_key: str = None,
        temperature: float = 1.0,
        extra_body: dict = None,
        scenario: str = "default",
        oversight_level: str = "default",
        user_prompt_type: str = "default",
        save_vfs_state: bool = True
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key) if base_url and api_key else None
        self.model = model
        self.temperature = temperature
        self.extra_body = extra_body
        self.system_prompt = system_prompt
        self.scenario = scenario
        self.oversight_level = oversight_level
        self.user_prompt_type = user_prompt_type
        self.save_vfs_state = save_vfs_state

        self.tools = tools
        self.available_functions = available_functions

        # Log available tools at DEBUG level
        tool_names = list(available_functions.keys())
        logger.debug(f"Available tools: {tool_names}")

        self.logs: List[Dict] = []
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @classmethod
    def from_configs(
        cls,
        system_prompt: str,
        provider_config: ProviderConfig,
        model_config: ModelConfig,
        scenario: str = "default",
        oversight_level: str = "default",
        user_prompt_type: str = "default",
        save_vfs_state: bool = True
    ) -> "Agent":
        """Create an Agent from provider and model configs."""
        return Agent(
            system_prompt=system_prompt,
            model=model_config.id,
            base_url=provider_config.base_url,
            api_key=provider_config.api_key,
            temperature=model_config.temperature,
            extra_body=model_config.extra_body,
            scenario=scenario,
            oversight_level=oversight_level,
            user_prompt_type=user_prompt_type,
            save_vfs_state=save_vfs_state
        )

    def run(self, initial_prompt: str):
        """Run the agent with an initial prompt."""
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': initial_prompt}
        ]
        self.logs.extend(messages)
        return self.chat_loop(messages)

    def load_conversation(
        self,
        conversation_history: List[Dict],
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ):
        """Load a conversation from history (for interrogation)."""
        self.logs = conversation_history
        self.total_tokens = total_tokens
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def chat(self, user_input: str):
        """Send a message and get response."""
        self.logs.append({'role': 'user', 'content': user_input})
        messages = list(self.logs)
        return self.chat_loop(messages)

    def chat_loop(self, messages: List[Dict], max_turns: int = 20):
        """Main conversation loop using OpenAI SDK directly."""
        turn_count = 0
        while True:
            turn_count += 1
            if turn_count > max_turns:
                logger.warning(f"MAX TURNS REACHED ({max_turns})")
                return None

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    temperature=self.temperature,
                    extra_body=self.extra_body if self.extra_body else None,
                )
            except Exception as e:
                logger.critical(f"API call failed: {e}")
                raise

            # Handle malformed responses
            if not response.choices:
                logger.critical(f"Empty response from API. Response: {response}")
                raise Exception("Empty response from API")

            # Update token counts
            if response.usage:
                self.total_tokens += response.usage.total_tokens
                self.prompt_tokens += response.usage.prompt_tokens
                self.completion_tokens += response.usage.completion_tokens

            choice = response.choices[0]
            response_message = choice.message
            finish_reason = choice.finish_reason

            # Extract reasoning from raw response
            content = response_message.content or ""
            reasoning = None

            # Try to get reasoning from different sources
            # 1. Check for reasoning_content (OpenRouter)
            if hasattr(response_message, 'reasoning_content') and response_message.reasoning_content:
                reasoning = response_message.reasoning_content
            # 2. Check for reasoning_details (structured)
            elif hasattr(response_message, 'reasoning_details') and response_message.reasoning_details:
                reasoning_parts = []
                for item in response_message.reasoning_details:
                    if item.get("type") == "reasoning.text":
                        reasoning_parts.append(item.get("text", ""))
                reasoning = "\n".join(reasoning_parts).strip()
            # 3. Regex fallback for <thinking> tags
            else:
                thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
                if thought_match:
                    reasoning = thought_match.group(2).strip()
                    content = content.replace(thought_match.group(0), "").strip()
                # If no tags and there are tool calls, content is reasoning
                elif response_message.tool_calls:
                    reasoning = content
                    content = None

            # Log reasoning if available (DEBUG level shows full, INFO shows preview)
            if reasoning:
                if len(reasoning) > 500:
                    logger.debug(f"\n--- REASONING ---\n{reasoning}")
                    logger.info(f"\n--- REASONING (truncated) ---\n{reasoning[:500]}...")
                else:
                    logger.info(f"\n--- REASONING ---\n{reasoning}")

            # Append raw response message to preserve extra_content (Google thoughtSignature)
            messages.append(response_message)

            # Log entry
            log_entry = {
                "role": "assistant",
                "content": content,
                "reasoning": reasoning,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        },
                        "extra_content": getattr(tc, "extra_content", None)
                    }
                    for tc in response_message.tool_calls
                ] if response_message.tool_calls else None,
                "finish_reason": finish_reason,
                "turn_count": turn_count,
                "response_metadata": {
                    "model": self.model,
                    "usage": {
                        "completion_tokens": response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                }
            }
            self.logs.append(log_entry)

            # Check finish_reason to determine if we should continue or stop
            # "tool_calls" means model wants to call tools (continue)
            # "stop" means model wants to end conversation
            if finish_reason == "tool_calls":
                logger.info(f"LLM requested {len(response_message.tool_calls)} tool execution(s)")
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    function_to_call = self.available_functions.get(function_name)
                    if not function_to_call:
                        error_msg = f"Unknown tool: {function_name}"
                        logger.warning(error_msg)
                        function_output = error_msg
                    else:
                        try:
                            function_output = function_to_call(**function_args)
                        except Exception as e:
                            function_output = f"Error executing {function_name}: {str(e)}"

                    logger.info(f"Executing: {function_name}({function_args})")

                    tool_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(function_output),
                    }
                    messages.append(tool_message)
                    self.logs.append(tool_message)
            elif finish_reason == "stop":
                logger.info(f"\n--- FINAL RESPONSE ---\n{content}")
                return content
            else:
                # Handle other finish reasons (length, content_filter, etc.)
                logger.info(f"\n--- FINISH REASON: {finish_reason} ---")
                content_preview = f"Content: {content[:200]}..." if len(content) > 200 else f"Content: {content}"
                logger.info(content_preview)
                return content

    def save_logs(
        self,
        output_dir: str = "logs",
        scenario: str = None,
        oversight_level: str = None
    ):
        """Save conversation logs to a JSON file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name_safe = self.model.replace("/", "_")
        scenario_name = (scenario or self.scenario).replace("/", "_")
        oversight = oversight_level or self.oversight_level

        base_dir = os.path.join(output_dir, model_name_safe, scenario_name, oversight)
        os.makedirs(base_dir, exist_ok=True)

        log_file = os.path.join(base_dir, f"{timestamp}.json")

        log_data = {
            "run_id": f"{model_name_safe}/{scenario_name}/{oversight}/{timestamp}",
            "model": self.model,
            "scenario": scenario or self.scenario,
            "oversight_level": oversight,
            "user_prompt_type": self.user_prompt_type,
            "temperature": self.temperature,
            "base_url": str(self.client.base_url) if self.client else None,
            "extra_body_config": self.extra_body or {},
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "conversation": self.logs,
        }

        if self.save_vfs_state:
            log_data["final_vfs_state"] = VFS.get_instance().fs

        # Atomic write: write to temp file first, then rename.
        # This prevents corrupt log files if the process crashes mid-write.
        import tempfile
        fd, tmp_path = tempfile.mkstemp(dir=base_dir, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(log_data, f, indent=4)
            os.rename(tmp_path, log_file)
        except BaseException:
            # Clean up temp file on any failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        logger.info(f"Logs saved to {log_file}")
        return log_file
