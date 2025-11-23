# agent.py
from openai import OpenAI
import json
import re
import datetime
from config import MODEL, BASE_URL, API_KEY, TEMPERATURE, EXTRA_BODY
from tools import tools, available_functions

class Agent:
    def __init__(self, system_prompt="You are a helpful assistant.", model=MODEL, base_url=BASE_URL, api_key=API_KEY, temperature=TEMPERATURE, scenario="default", oversight_level="default", user_prompt_type="default"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.tools = tools
        self.available_functions = available_functions
        self.logs = []
        self.system_prompt = system_prompt
        self.scenario = scenario
        self.oversight_level = oversight_level
        self.user_prompt_type = user_prompt_type
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def run(self, initial_prompt):
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': initial_prompt}
        ]
        self.logs.extend(messages)
        
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                temperature=self.temperature,
                extra_body=EXTRA_BODY,
                # include=["reasoning.encrypted_content"]
            )

            # Update token counts
            if response.usage:
                self.total_tokens += response.usage.total_tokens
                self.prompt_tokens += response.usage.prompt_tokens
                self.completion_tokens += response.usage.completion_tokens

            response_message = response.choices[0].message
            messages.append(response_message)

            content = response_message.content
            reasoning = None

            if content:
                # First, try to parse with tags for models that support it
                thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
                if thought_match:
                    reasoning = thought_match.group(2).strip()
                    content = content.replace(thought_match.group(0), "").strip()
                # If no tags, and there are tool calls, assume the whole content is reasoning
                elif response_message.tool_calls:
                    reasoning = content
                    content = None
            
            log_entry = {
                "role": "assistant",
                "content": content,
                "tool_calls": [{
                    'id': tc.id,
                    'type': tc.type,
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                } for tc in response_message.tool_calls] if response_message.tool_calls else None,
                "response_metadata": {
                    "model": response.model,
                    "usage": {
                        "completion_tokens": response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                }
            }

            if reasoning:
                log_entry["reasoning"] = reasoning

            model_reasoning = getattr(response_message, 'reasoning', None)
            if model_reasoning:
                print(f"--- MODEL REASONING ---\n{model_reasoning}")
                log_entry["reasoning"] = model_reasoning

            self.logs.append(log_entry)

            if response_message.tool_calls:
                print(f"--- LLM requested tool execution ---")
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    function_to_call = self.available_functions.get(function_name)
                    function_output = function_to_call(**function_args)
                    
                    print(f"Executing: {function_name}({function_args}) -> {function_output}")

                    tool_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(function_output),
                    }
                    messages.append(tool_message)
                    self.logs.append(tool_message)
            else:
                print(f"\n--- Final LLM Response ---\n{response_message.content}")
                break
    
    def save_logs(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name_safe = self.model.replace("/", "_")
        run_id = f"{model_name_safe}_{self.scenario}_{timestamp}"

        log_data = {
            "run_id": run_id,
            "model": self.model,
            "scenario": self.scenario,
            "oversight_level": self.oversight_level,
            "user_prompt_type": self.user_prompt_type,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "conversation": self.logs
        }
        
        log_file = f"output/{run_id}.json"
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=4)
        print(f"\nLogs saved to {log_file}")
