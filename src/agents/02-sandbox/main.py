import re
import json
import datetime
import os
from typing import List, Dict, Any, Callable

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.tools import render_text_description

# --- 1. Tool Definitions ---

@tool
def validate_user(user_id: int, addresses: List[str]) -> bool:
    """Validate user using historical addresses.

    Args:
        user_id (int): the user ID.
        addresses (List[str]): Previous addresses as a list of strings.
    """
    # In a real scenario, this would involve some logic.
    # For now, it just returns True as in the original script.
    return True

def get_tools() -> List[Callable]:
    """Returns a list of available tools."""
    return [validate_user]

# --- 2. Prompt Engineering ---

def create_system_prompt(tools: List[Callable]) -> str:
    """Creates a system prompt with tool descriptions."""
    tool_description = render_text_description(tools)
    # Using triple quotes for the f-string to handle quotes inside easily.
    return f'''# Tools

    You may call one or more functions to assist with the user query.

    You are provided with function signatures within <tools></tools> XML tags:
    <tools>
    {tool_description}
    </tools>

    For each function call, first think about what you need to do and write it down in a <think></think> block. Then, return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags.
    **IMPORTANT**: The JSON object must be a valid JSON, with all keys and string values enclosed in double quotes.

    Example of a valid tool call:
    <tool_call>
    {{"name": "validate_user", "arguments": {{"user_id": 123, "addresses": ["123 Fake St", "456 Main St"]}}}}
    </tool_call>'''

# --- 3. LLM Response Parsing ---

def parse_llm_response(content: str) -> Dict[str, Any]:
    """Parses the LLM's response to extract reasoning and tool calls."""
    think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    reasoning = think_match.group(1).strip() if think_match else None

    tool_call_match = re.search(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
    tool_call_str = tool_call_match.group(1).strip() if tool_call_match else None

    tool_call = None
    parsing_error = None
    if tool_call_str:
        try:
            # The model sometimes returns a markdown code block.
            if tool_call_str.startswith("```json"):
                tool_call_str = tool_call_str[7:-4]
            tool_call = json.loads(tool_call_str)
        except json.JSONDecodeError as e:
            parsing_error = f"Failed to parse tool_call JSON: {e}"

    return {
        "reasoning": reasoning,
        "tool_call": tool_call,
        "parsing_error": parsing_error,
    }

# --- 4. Agent Core Logic ---

def execute_tool_call(tool_call: Dict[str, Any], tools: List[Callable]) -> Dict[str, Any]:
    """Executes a tool call and returns the result."""
    if not tool_call:
        return {"error": "No tool call provided."}

    tool_name = tool_call.get("name")
    tool_args = tool_call.get("arguments")

    tool_to_call = next((t for t in tools if t.name == tool_name), None)

    if not tool_to_call:
        return {"error": f"Tool '{tool_name}' not found."}

    try:
        result = tool_to_call.invoke(tool_args)
        return {"result": result}
    except Exception as e:
        return {"error": f"Error calling tool '{tool_name}': {e}"}

def save_log(log_data: Dict[str, Any]):
    """Saves the log data to a JSON file."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up three levels to the project root and then into the `output` directory
    output_dir = os.path.join(script_dir, "..", "..", "..", "output")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # get the script name
    script_name = os.path.basename(__file__).split('.')[0]
    file_path = os.path.join(output_dir, f"{script_name}_{timestamp}.json")
    with open(file_path, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"Log saved to {os.path.normpath(file_path)}")


def main():
    """Main function to run the agent."""
    # --- Configuration ---
    model_config = {
        "model": "qwen3:1.7b",
        "temperature": 0,
    }
    human_message_content = "Could you validate user 123? They previously lived at 123 Fake St in Boston MA and 234 Pretend Boulevard in Houston TX. Think before you call any tools"

    # --- Initialization ---
    log_data = {"run_config": {"model_config": model_config}}
    tools = get_tools()
    llm = ChatOllama(**model_config)
    system_prompt = create_system_prompt(tools)
    
    messages: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message_content),
    ]

    # --- Log initial data ---
    log_data["messages"] = [json.loads(msg.model_dump_json()) for msg in messages]


    # --- LLM Invocation ---
    response = llm.invoke(messages)
    log_data["raw_response"] = json.loads(response.model_dump_json())

    # --- Parsing ---
    parsed_response = parse_llm_response(response.content)
    log_data.update(parsed_response)

    # --- Tool Execution ---
    tool_result = None
    if parsed_response["tool_call"]:
        tool_result = execute_tool_call(parsed_response["tool_call"], tools)
        log_data["tool_result"] = tool_result
    
    # --- Print to console (to replicate original behavior) ---
    print("--- Extracted Reasoning ---")
    print(log_data.get("reasoning"))
    print("\n" + "="*40 + "\n")
    print("--- Extracted Tool Call ---")
    print(log_data.get("tool_call"))
    if tool_result:
        print("\n" + "="*40 + "\n")
        if "result" in tool_result:
            print(f"--- Calling Tool: {log_data['tool_call']['name']} ---")
            print("--- Tool Call Result ---")
            print(tool_result["result"])
        else:
            print("--- Tool Call Error ---")
            print(tool_result["error"])
    print("\n" + "="*40 + "\n")

    # --- Save comprehensive log ---
    save_log(log_data)


if __name__ == "__main__":
    main()
