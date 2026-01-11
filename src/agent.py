"""
Agent class that uses the provider abstraction layer.
Handles conversation loops, tool execution, and logging.
"""
import json
import os
import datetime
from typing import List, Dict, Any, Optional
from vfs import VFS
from provider import ProviderAdapter, LLMResponse, ReasoningStep, create_provider_adapter
from config_loader import ProviderConfig, ModelConfig
from tools import tools, available_functions


class Agent:
    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        provider_adapter: ProviderAdapter = None,
        scenario: str = "default",
        oversight_level: str = "default",
        user_prompt_type: str = "default"
    ):
        self.provider = provider_adapter
        self.system_prompt = system_prompt
        self.scenario = scenario
        self.oversight_level = oversight_level
        self.user_prompt_type = user_prompt_type

        # Get model info from provider
        if provider_adapter:
            self.model = provider_adapter.model_config.id
            self.temperature = provider_adapter.model_config.temperature
        else:
            self.model = "unknown"
            self.temperature = 1.0

        self.tools = tools
        self.available_functions = available_functions
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
        user_prompt_type: str = "default"
    ) -> "Agent":
        """Create an Agent from provider and model configs."""
        adapter = create_provider_adapter(provider_config, model_config)
        return Agent(
            system_prompt=system_prompt,
            provider_adapter=adapter,
            scenario=scenario,
            oversight_level=oversight_level,
            user_prompt_type=user_prompt_type
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

    def chat_loop(self, messages: List[Dict]):
        """Main conversation loop."""
        turn_count = 0
        while True:
            llm_response = self.provider.call(messages, self.tools)

            # Update token counts
            if llm_response.usage:
                self.total_tokens += llm_response.usage.get("total_tokens", 0)
                self.prompt_tokens += llm_response.usage.get("prompt_tokens", 0)
                self.completion_tokens += llm_response.usage.get("completion_tokens", 0)

            # Process the response - check for interleaved thinking
            if self._has_interleaved_thinking(llm_response):
                result = self._handle_interleaved(messages, llm_response)
                if result is not None:
                    return result
            else:
                result = self._handle_standard(messages, llm_response, is_first_turn=(turn_count == 0))
                if result is not None:
                    return result

            turn_count += 1

    def _has_interleaved_thinking(self, response: LLMResponse) -> bool:
        """Check if response has interleaved thinking (reasoning between tool calls)."""
        # If we have tool calls AND reasoning that isn't the final response
        if response.tool_calls and response.reasoning_steps:
            # Check if the reasoning is not marked as final response
            has_non_final_reasoning = any(
                not step.is_final_response
                for step in response.reasoning_steps
            )
            return has_non_final_reasoning
        return False

    def _handle_interleaved(self, messages: List[Dict], response: LLMResponse):
        """Handle interleaved thinking (reasoning between tool calls)."""
        print("--- Interleaved thinking detected ---")

        # Extract reasoning content
        reasoning_text = "\n".join(
            step.content for step in response.reasoning_steps
            if not step.is_final_response
        )

        # Build assistant message with reasoning and tool calls
        assistant_message = {
            "role": "assistant",
            "content": reasoning_text if reasoning_text else None,
            "tool_calls": response.tool_calls
        }
        messages.append(assistant_message)

        # Log the assistant message
        self.logs.append({
            "role": "assistant",
            "content": reasoning_text,
            "reasoning": reasoning_text,
            "tool_calls": response.tool_calls,
            "interleaved_thinking": True,
            "response_metadata": {
                "model": self.model,
                "usage": response.usage
            }
        })

        # print(f"--- Reasoning ---\n{reasoning_text[:200]}..." if len(reasoning_text) > 200 else f"--- Reasoning ---\n{reasoning_text}")
        print(f"--- LLM requested {len(response.tool_calls)} tool execution(s) ---")

        # Execute each tool call and continue the loop
        for tool_call in response.tool_calls:
            result = self._execute_tool(messages, tool_call)
            if result is None:
                return None  # Stop iteration

        # Continue the while loop for more tool calls or final response
        return None

    def _handle_standard(self, messages: List[Dict], response: LLMResponse, is_first_turn: bool = False):
        """Handle standard response (reasoning, then tools, then final or just final)."""
        content = response.content or ""
        reasoning = response.reasoning_steps[0].content if response.reasoning_steps else None

        # If there are tool calls
        if response.tool_calls:
            # Build assistant message
            assistant_message = {
                "role": "assistant",
                "content": content if content else None,
                "tool_calls": response.tool_calls
            }
            messages.append(assistant_message)

            # Log entry
            self.logs.append({
                "role": "assistant",
                "content": content,
                "reasoning": reasoning,
                "tool_calls": response.tool_calls,
                "response_metadata": {
                    "model": self.model,
                    "usage": response.usage
                }
            })

            print(f"--- LLM requested {len(response.tool_calls)} tool execution(s) ---")

            # Execute all tool calls
            for tool_call in response.tool_calls:
                result = self._execute_tool(messages, tool_call)
                if result is None:
                    return None

            # Continue loop for more interactions
            return None

        else:
            # No tool calls - check if this is a final response or just a conversational response
            # On first turn, models like Kimi-K2 may respond conversationally before making tool calls
            if is_first_turn:
                # Log the response but don't return - continue to next turn
                assistant_message = {
                    "role": "assistant",
                    "content": content if content else None
                }
                messages.append(assistant_message)

                self.logs.append({
                    "role": "assistant",
                    "content": content,
                    "reasoning": reasoning,
                    "tool_calls": None,
                    "response_metadata": {
                        "model": self.model,
                        "usage": response.usage
                    }
                })

                # Continue to next turn - don't return
                return None
            else:
                # Not first turn and no tool calls - this is a final response
                assistant_message = {
                    "role": "assistant",
                    "content": content if content else None
                }
                messages.append(assistant_message)

                # Log entry
                self.logs.append({
                    "role": "assistant",
                    "content": content,
                    "reasoning": reasoning,
                    "tool_calls": None,
                    "response_metadata": {
                        "model": self.model,
                        "usage": response.usage
                    }
                })

                # print(f"\n--- Final LLM Response ---\n{content}")
                return content

    def _execute_tool(self, messages: List[Dict], tool_call: Dict) -> Optional[str]:
        """Execute a single tool call."""
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])

        function_to_call = self.available_functions.get(function_name)
        if not function_to_call:
            error_msg = f"Unknown tool: {function_name}"
            print(f"Error: {error_msg}")
            function_output = error_msg
        else:
            try:
                function_output = function_to_call(**function_args)
            except Exception as e:
                function_output = f"Error executing {function_name}: {str(e)}"

        # print(f"Executing: {function_name}({function_args}) -> {function_output}")
        print(f"Executing: {function_name}({function_args})")

        # Create tool message
        tool_message = {
            "tool_call_id": tool_call["id"],
            "role": "tool",
            "content": str(function_output)
        }
        messages.append(tool_message)
        self.logs.append(tool_message)

        return str(function_output)

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

        # Directory structure: output/{model}/{scenario}/{oversight}/
        base_dir = os.path.join(output_dir, model_name_safe, scenario_name, oversight)
        os.makedirs(base_dir, exist_ok=True)

        # Filename: {timestamp}_run_id.json
        filename_base = f"{timestamp}"
        run_id = f"{model_name_safe}/{scenario_name}/{oversight}/{filename_base}"
        log_file = os.path.join(base_dir, f"{filename_base}.json")

        log_data = {
            "run_id": run_id,
            "model": self.model,
            "scenario": scenario or self.scenario,
            "oversight_level": oversight,
            "user_prompt_type": self.user_prompt_type,
            "temperature": self.temperature,
            "base_url": str(self.provider.provider_config.base_url) if self.provider else None,
            "extra_body_config": self.provider.model_config.extra_body if self.provider else {},
            "final_vfs_state": VFS.get_instance().fs,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "conversation": self.logs
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=4)
        print(f"\nLogs saved to {log_file}")
        return log_file
