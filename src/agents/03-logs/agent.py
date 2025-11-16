# agent.py
from openai import OpenAI
import json
import datetime
from config import MODEL, BASE_URL, API_KEY, TEMPERATURE
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
            )

            response_message = response.choices[0].message
            messages.append(response_message)
            
            log_entry = {
                "role": "assistant",
                "content": response_message.content,
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
        log_data = {
            "scenario": self.scenario,
            "oversight_level": self.oversight_level,
            "user_prompt_type": self.user_prompt_type,
            "conversation": self.logs
        }
        log_file = f"output/log_{timestamp}.json"
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=4)
        print(f"\nLogs saved to {log_file}")
