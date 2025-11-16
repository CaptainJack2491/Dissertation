# agent.py
from openai import OpenAI
import json
from config import MODEL, BASE_URL, API_KEY
from tools import tools, available_functions

class Agent:
    def __init__(self, model=MODEL, base_url=BASE_URL, api_key=API_KEY):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.tools = tools
        self.available_functions = available_functions

    def run(self, initial_prompt):
        messages = [{'role': 'user', 'content': initial_prompt}]
        
        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
            )

            response_message = response.choices[0].message
            messages.append(response_message)

            model_reasoning = getattr(response_message, 'reasoning', None)
            if model_reasoning:
                print(f"--- MODEL REASONING ---\n{model_reasoning}")

            if response_message.tool_calls:
                print(f"--- LLM requested tool execution ---")
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    function_to_call = self.available_functions.get(function_name)
                    function_output = function_to_call(**function_args)
                    
                    print(f"Executing: {function_name}({function_args}) -> {function_output}")

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(function_output),
                    })
            else:
                print(f"\n--- Final LLM Response ---\n{response_message.content}")
                break
