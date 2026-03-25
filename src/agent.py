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
        save_vfs_state: bool = True,
        goal_type: str = "",
        vfs_instance=None,
        tool_functions: dict = None
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
        self.goal_type = goal_type
        self.vfs_instance = vfs_instance

        self.tools = tools
        self.available_functions = tool_functions if tool_functions else available_functions

        # Log available tools at DEBUG level
        tool_names = list(self.available_functions.keys())
        logger.debug(f"Available tools: {tool_names}")

        self.logs: List[Dict] = []
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self._partial_log_path: str = None  # Set by enable_incremental_save()

    @classmethod
    def from_configs(
        cls,
        system_prompt: str,
        provider_config: ProviderConfig,
        model_config: ModelConfig,
        scenario: str = "default",
        oversight_level: str = "default",
        user_prompt_type: str = "default",
        save_vfs_state: bool = True,
        goal_type: str = "",
        vfs_instance=None,
        tool_functions: dict = None
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
            save_vfs_state=save_vfs_state,
            goal_type=goal_type,
            vfs_instance=vfs_instance,
            tool_functions=tool_functions
        )

    def run(self, initial_prompt: str):
        """Run the agent with an initial prompt."""
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': initial_prompt}
        ]
        self.logs.extend(messages)
        self._save_partial()  # Save initial state (system + user prompt)
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
            reasoning_format = None  # Track source format (e.g. openai-responses-v1)

            # Try to get reasoning from different sources
            # 1. Check for reasoning_content (OpenRouter — Qwen, DeepSeek, etc.)
            if hasattr(response_message, 'reasoning_content') and response_message.reasoning_content:
                reasoning = response_message.reasoning_content
                reasoning_format = "reasoning_content"
            # 2. Check for reasoning (Groq GPT-OSS models)
            elif hasattr(response_message, 'reasoning') and response_message.reasoning:
                reasoning = response_message.reasoning
                reasoning_format = "reasoning"
            # 3. Check for reasoning_details (structured — OpenAI reasoning models)
            elif hasattr(response_message, 'reasoning_details') and response_message.reasoning_details:
                reasoning_parts = []
                for item in response_message.reasoning_details:
                    detail_type = item.get("type", "")
                    if detail_type == "reasoning.text":
                        reasoning_parts.append(item.get("text", ""))
                    elif detail_type == "reasoning.summary":
                        reasoning_parts.append(f"[SUMMARY] {item.get('summary', '')}")
                # Capture the format field from the first detail item
                reasoning_format = response_message.reasoning_details[0].get("format", "unknown")
                reasoning = "\n".join(reasoning_parts).strip()
            # 3. Regex fallback for <thinking> tags
            else:
                thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
                if thought_match:
                    reasoning = thought_match.group(2).strip()
                    content = content.replace(thought_match.group(0), "").strip()
                    reasoning_format = "thinking_tags"
                # If no tags and there are tool calls, content is reasoning
                elif response_message.tool_calls:
                    reasoning = content
                    content = None
                    reasoning_format = "content_as_reasoning"

            # Log reasoning if available (DEBUG level shows full, INFO shows preview)
            if reasoning:
                if len(reasoning) > 500:
                    logger.debug(f"\n--- REASONING ---\n{reasoning}")
                    logger.info(f"\n--- REASONING (truncated) ---\n{reasoning[:500]}...")
                else:
                    logger.info(f"\n--- REASONING ---\n{reasoning}")
            elif turn_count == 1:
                # Warn on first turn — if the model never reasons on turn 1,
                # it's unlikely to reason on later turns either
                logger.warning(f"No reasoning detected on first turn for model {self.model}. "
                               f"Glass-box judging will not be possible for this run.")

            # Append raw response message to preserve extra_content (Google thoughtSignature)
            messages.append(response_message)

            # Log entry
            log_entry = {
                "role": "assistant",
                "content": content,
                "reasoning": reasoning,
                "reasoning_format": reasoning_format,
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
            self._save_partial()  # Incremental save after each assistant response

            # Check finish_reason to determine if we should continue or stop
            # "tool_calls" means model wants to call tools (continue)
            # "stop" means model wants to end conversation
            if finish_reason == "tool_calls":
                logger.info(f"LLM requested {len(response_message.tool_calls)} tool execution(s)")
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        logger.info(f"Executing: {function_name}({function_args})")

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
                    except json.JSONDecodeError as e:
                        error_msg = f"Error parsing tool arguments for {function_name}: {str(e)}. Arguments must be valid JSON."
                        logger.warning(error_msg)
                        function_output = error_msg

                    tool_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(function_output),
                    }
                    messages.append(tool_message)
                    self.logs.append(tool_message)
                self._save_partial()  # Incremental save after tool results
            elif finish_reason == "stop":
                logger.info(f"\n--- FINAL RESPONSE ---\n{content}")
                return content
            else:
                # Handle other finish reasons (length, content_filter, etc.)
                logger.info(f"\n--- FINISH REASON: {finish_reason} ---")
                content_preview = f"Content: {content[:200]}..." if len(content) > 200 else f"Content: {content}"
                logger.info(content_preview)
                return content

    def enable_incremental_save(self, output_dir: str, scenario: str = None, oversight_level: str = None):
        """Enable incremental saving of logs after each turn.

        Creates a .partial.json file that is updated after every API call.
        If the run crashes or hangs, this file persists for inspection.
        Call this BEFORE agent.run() to activate.
        """
        model_name_safe = self.model.replace("/", "_")
        scenario_name = (scenario or self.scenario).replace("/", "_")
        oversight = oversight_level or self.oversight_level

        if self.goal_type:
            base_dir = os.path.join(output_dir, model_name_safe, scenario_name,
                                    self.goal_type, oversight)
        else:
            base_dir = os.path.join(output_dir, model_name_safe, scenario_name, oversight)
        os.makedirs(base_dir, exist_ok=True)

        self._partial_log_path = os.path.join(base_dir, "_in_progress.partial.json")
        logger.debug(f"Incremental save enabled: {self._partial_log_path}")

    def _save_partial(self):
        """Write current state to partial log file (if incremental save is enabled)."""
        if not self._partial_log_path:
            return
        try:
            log_data = self._build_log_data()
            log_data["status"] = "in_progress"
            with open(self._partial_log_path, "w") as f:
                json.dump(log_data, f, indent=4)
        except Exception as e:
            logger.debug(f"Failed to write partial log: {e}")

    def _build_log_data(self, timestamp: str = None) -> dict:
        """Build the log data dictionary (shared by save_logs and _save_partial)."""
        ts = timestamp or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name_safe = self.model.replace("/", "_")
        scenario_name = self.scenario.replace("/", "_")
        oversight = self.oversight_level

        # Build run_id with goal_type if present
        if self.goal_type:
            run_id = f"{model_name_safe}/{scenario_name}/{self.goal_type}/{oversight}/{ts}"
        else:
            run_id = f"{model_name_safe}/{scenario_name}/{oversight}/{ts}"

        log_data = {
            "run_id": run_id,
            "model": self.model,
            "scenario": self.scenario,
            "goal_type": self.goal_type,
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
        return log_data

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

        # Include goal_type in directory path if present
        if self.goal_type:
            base_dir = os.path.join(output_dir, model_name_safe, scenario_name,
                                    self.goal_type, oversight)
        else:
            base_dir = os.path.join(output_dir, model_name_safe, scenario_name, oversight)
        os.makedirs(base_dir, exist_ok=True)

        log_file = os.path.join(base_dir, f"{timestamp}.json")

        log_data = self._build_log_data(timestamp)
        # Override scenario/oversight in case they were passed as args
        log_data["scenario"] = scenario or self.scenario
        log_data["oversight_level"] = oversight

        if self.save_vfs_state:
            vfs = self.vfs_instance if self.vfs_instance else VFS.get_instance()
            log_data["final_vfs_state"] = vfs.fs

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

        # Clean up partial log now that final save succeeded
        if self._partial_log_path and os.path.exists(self._partial_log_path):
            try:
                os.unlink(self._partial_log_path)
                logger.debug(f"Cleaned up partial log: {self._partial_log_path}")
            except OSError:
                pass

        logger.info(f"Logs saved to {log_file}")
        return log_file
