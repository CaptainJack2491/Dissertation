"""
Interrogate - replay and continue a conversation from a log file.
Allows interactive questioning of an agent based on a previous run.
"""
import argparse
import json
import os
from typing import Dict, List
from agent import Agent
from config_loader import ConfigLoader, ProviderConfig, ModelConfig
from vfs import VFS


# ANSI colors for terminal output
class Colors:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


def load_prompt(file_path: str) -> str:
    """Load a prompt file."""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r') as f:
        return f.read().strip()


def get_provider_from_log(log_data: Dict) -> tuple:
    """Extract provider info from log and create configs."""
    model_id = log_data["model"]
    base_url = log_data.get("base_url", "")
    temperature = log_data.get("temperature", 1.0)
    extra_body = log_data.get("extra_body_config", {})

    # Check base_url first (takes priority — e.g. Claude via OpenRouter)
    # then fall back to model name heuristics
    model_lower = model_id.lower()

    if "openrouter" in (base_url or ""):
        provider_name = "openrouter"
    elif "generativelanguage" in (base_url or ""):
        provider_name = "google"
    elif "groq" in (base_url or ""):
        provider_name = "groq"
    elif "gemini" in model_lower:
        provider_name = "google"
    elif "claude" in model_lower:
        provider_name = "anthropic"
        base_url = ""
    elif "kimi" in model_lower or "moonshot" in model_lower:
        provider_name = "moonshot"
    else:
        provider_name = "openai"

    provider_config = ProviderConfig(
        name=provider_name,
        api_key_env=f"{provider_name.upper()}_API_KEY",
        base_url=base_url or ""
    )

    model_config = ModelConfig(
        id=model_id,
        provider=provider_name,
        temperature=temperature,
        extra_body=extra_body
    )

    return provider_config, model_config


def sanitize_for_api(conversation: List[Dict]) -> List[Dict]:
    """
    Convert internal log entries to API-compatible messages.
    Strips custom fields (reasoning, response_metadata, turn_count, etc.)
    and converts tool_calls back to the format the API expects to see in history.
    """
    clean = []
    for msg in conversation:
        role = msg.get("role")

        if role == "system":
            clean.append({"role": "system", "content": msg.get("content", "")})

        elif role == "user":
            clean.append({"role": "user", "content": msg.get("content", "")})

        elif role == "tool":
            clean.append({
                "role": "tool",
                "tool_call_id": msg.get("tool_call_id", ""),
                "content": msg.get("content", "")
            })

        elif role == "assistant":
            entry = {"role": "assistant"}

            # Content
            content = msg.get("content")
            if content:
                entry["content"] = content
            else:
                entry["content"] = None

            # Tool calls — convert from our log format back to API format
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("function", {}).get("name", ""),
                            "arguments": tc.get("function", {}).get("arguments", "{}")
                        }
                    }
                    for tc in tool_calls
                ]

            clean.append(entry)

    return clean


def print_history(conversation: List[Dict], last_n: int = None):
    """Print conversation history in a readable format."""
    messages = [m for m in conversation if m.get("role") in ("user", "assistant", "tool")]

    if last_n:
        messages = messages[-last_n:]

    for msg in messages:
        role = msg.get("role", "?")

        if role == "user":
            content = msg.get("content", "")
            print(f"\n{Colors.GREEN}{Colors.BOLD}[USER]{Colors.RESET} {content[:300]}{'...' if len(content) > 300 else ''}")

        elif role == "assistant":
            reasoning = msg.get("reasoning", "")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")

            print(f"\n{Colors.CYAN}{Colors.BOLD}[ASSISTANT]{Colors.RESET}")
            if reasoning:
                preview = reasoning[:200] + ("..." if len(reasoning) > 200 else "")
                print(f"  {Colors.DIM}Reasoning: {preview}{Colors.RESET}")
            if content:
                print(f"  {content[:300]}{'...' if len(content) > 300 else ''}")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    print(f"  {Colors.YELLOW}→ {fn.get('name', '?')}({fn.get('arguments', '')[:80]}){Colors.RESET}")

        elif role == "tool":
            content = msg.get("content", "")
            preview = content[:150] + ("..." if len(content) > 150 else "")
            print(f"  {Colors.DIM}[tool result] {preview}{Colors.RESET}")


def print_help():
    """Print available commands."""
    print(f"""
{Colors.BOLD}Available commands:{Colors.RESET}
  {Colors.YELLOW}history{Colors.RESET}       Show full conversation history
  {Colors.YELLOW}history N{Colors.RESET}     Show last N messages
  {Colors.YELLOW}reasoning{Colors.RESET}     Show the last assistant reasoning trace (full)
  {Colors.YELLOW}vfs{Colors.RESET}           Show current virtual filesystem state
  {Colors.YELLOW}info{Colors.RESET}          Show run metadata (model, scenario, tokens)
  {Colors.YELLOW}save{Colors.RESET}          Save the extended conversation
  {Colors.YELLOW}help{Colors.RESET}          Show this message
  {Colors.YELLOW}exit{Colors.RESET}          Quit

  Anything else is sent as a message to the agent.
""")


def main():
    parser = argparse.ArgumentParser(description="Interrogate a conversation log.")
    parser.add_argument("log_file", help="Path to the log file to load.")
    parser.add_argument("--config", default="config.yaml", help="Path to config file (for API keys)")
    parser.add_argument("--show-history", action="store_true", help="Print conversation history on load")
    args = parser.parse_args()

    # Load config (for API keys)
    config = ConfigLoader(args.config)
    try:
        config.load()
    except FileNotFoundError:
        pass  # Config file is optional for interrogation

    # Load log file
    try:
        with open(args.log_file, 'r') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Log file not found at {args.log_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.log_file}")
        return

    # Extract data from log
    conversation_history = log_data.get("conversation", [])
    if not conversation_history:
        print("Error: No conversation history in log file")
        return

    system_prompt = conversation_history[0].get('content', '') if conversation_history else ''
    scenario = log_data.get('scenario', 'interrogation')
    oversight_level = log_data.get('oversight_level', 'N/A')

    # Get provider from log
    provider_config, model_config = get_provider_from_log(log_data)

    # Initialize VFS from log
    final_vfs_state = log_data.get("final_vfs_state")
    if final_vfs_state:
        VFS.get_instance(fs_data=final_vfs_state)
    else:
        VFS.get_instance()

    # Create agent from log provider info
    agent = Agent.from_configs(
        system_prompt=system_prompt,
        provider_config=provider_config,
        model_config=model_config,
        scenario=scenario,
        oversight_level=oversight_level,
        user_prompt_type=log_data.get('user_prompt_type', 'interrogation')
    )

    # Sanitize and load conversation history
    clean_history = sanitize_for_api(conversation_history)
    agent.load_conversation(
        conversation_history=clean_history,
        total_tokens=log_data.get('total_tokens', 0),
        prompt_tokens=log_data.get('prompt_tokens', 0),
        completion_tokens=log_data.get('completion_tokens', 0)
    )

    # Print session info
    turn_count = len([m for m in conversation_history if m.get('role') == 'assistant'])
    print(f"\n{Colors.BOLD}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}Interrogation Session{Colors.RESET}")
    print(f"{'=' * 50}")
    print(f"  Model:     {Colors.CYAN}{agent.model}{Colors.RESET}")
    print(f"  Scenario:  {scenario}")
    print(f"  Oversight: {oversight_level}")
    print(f"  Turns:     {turn_count}")
    print(f"  Tokens:    {agent.total_tokens}")
    if final_vfs_state:
        print(f"  VFS:       {Colors.GREEN}loaded from log{Colors.RESET}")
    else:
        print(f"  VFS:       {Colors.DIM}empty (no state in log){Colors.RESET}")
    print(f"{'=' * 50}\n")

    if args.show_history:
        print_history(conversation_history)

    print_help()

    # Interactive loop
    while True:
        try:
            user_input = input(f"{Colors.GREEN}> {Colors.RESET}").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                break

            elif user_input.lower() == "help":
                print_help()

            elif user_input.lower() == "save":
                log_file = agent.save_logs(output_dir="interrogation_logs")
                print(f"{Colors.GREEN}Saved to {log_file}{Colors.RESET}")

            elif user_input.lower() == "vfs":
                print(f"\n{Colors.BOLD}--- Virtual Filesystem ---{Colors.RESET}")
                VFS.get_instance().print_fs()

            elif user_input.lower() == "info":
                print(f"\n  Model:     {agent.model}")
                print(f"  Scenario:  {scenario}")
                print(f"  Oversight: {oversight_level}")
                print(f"  Tokens:    {agent.total_tokens}")

            elif user_input.lower().startswith("history"):
                parts = user_input.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                print_history(conversation_history, last_n=n)

            elif user_input.lower() == "reasoning":
                # Find last assistant message with reasoning
                for msg in reversed(conversation_history):
                    if msg.get("role") == "assistant" and msg.get("reasoning"):
                        print(f"\n{Colors.BOLD}--- Full Reasoning Trace ---{Colors.RESET}")
                        print(msg["reasoning"])
                        break
                else:
                    print(f"{Colors.DIM}No reasoning found in conversation.{Colors.RESET}")

            else:
                # Send message to agent
                agent.chat(user_input)

                # Also append to our conversation_history for the history command
                conversation_history.append({"role": "user", "content": user_input})

                # Find and display the response
                for msg in reversed(agent.logs):
                    if msg.get("role") == "assistant":
                        reasoning = msg.get("reasoning", "")
                        content = msg.get("content", "")

                        if reasoning:
                            print(f"\n{Colors.DIM}--- Reasoning ---{Colors.RESET}")
                            print(f"{Colors.DIM}{reasoning}{Colors.RESET}")
                        if content:
                            print(f"\n{Colors.BOLD}--- Response ---{Colors.RESET}")
                            print(content)
                        if msg.get("tool_calls"):
                            print(f"\n{Colors.YELLOW}[{len(msg['tool_calls'])} tool call(s) executed]{Colors.RESET}")

                        # Add to conversation_history for history tracking
                        conversation_history.append(msg)
                        break

        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}(Ctrl+C) Use 'exit' to quit.{Colors.RESET}")
        except EOFError:
            break

    # Offer to save on exit
    try:
        save = input(f"\n{Colors.YELLOW}Save extended conversation? (y/n): {Colors.RESET}").lower()
        if save == "y":
            log_file = agent.save_logs(output_dir="interrogation_logs")
            print(f"{Colors.GREEN}Saved to {log_file}{Colors.RESET}")
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    main()
