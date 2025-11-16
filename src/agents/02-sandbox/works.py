import json
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

tool_def = {
    "type": "function",
    "function": {
        "name": "validate_user",
        "description": "Validate user using historical addresses.\\n\\n    Args:\\n        user_id (int): the user ID.\\n        addresses (List[str]): Previous addresses as a list of strings.",
        "parameters": {
            "type": "object",
            "required": ["user_id", "addresses"],
            "properties": {
                "addresses": {"type": "array", "items": {"type": "string"}, "description": ""},
                "user_id": {"type": "integer", "description": ""},
            },
        },
    },
}

system_prompt = f"""# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{json.dumps(tool_def)}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": "<function-name>", "arguments": "<args-json-object>"}}
</tool_call>"""

llm = ChatOllama(
    model="qwen3:1.7b",
    temperature=0,
)

messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content="Could you validate user 123? They previously lived at 123 Fake St in Boston MA and 234 Pretend Boulevard in Houston TX.Think before you call any tools"),
]

result = llm.invoke(messages)

print("--- Full AIMessage Result ---")
print(result)

