"""
Interrogate - replay and continue a conversation from a log file.
Allows interactive questioning of an agent based on a previous run.
"""
import argparse
import json
import os
from typing import Dict, Any, Optional
from agent import Agent
from config_loader import ConfigLoader, ProviderConfig, ModelConfig
from provider import create_provider_adapter
from vfs import VFS


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

    # Determine provider from model ID first (more reliable), then base_url
    model_lower = model_id.lower()

    if "claude" in model_lower:
        provider_name = "anthropic"
        # Claude doesn't use base_url
        base_url = ""
    elif "gemini" in model_lower:
        provider_name = "google"
    elif "kimi" in model_lower or "moonshot" in model_lower:
        provider_name = "moonshot"
    elif "openrouter" in base_url:
        provider_name = "openrouter"
    elif "openai" in base_url or "generativelanguage" in base_url:
        provider_name = "google" if "generativelanguage" in base_url else "openai"
    else:
        # Default to openai-compatible
        provider_name = "openai"

    # Create configs
    provider_config = ProviderConfig(
        name=provider_name,
        api_key_env=f"{provider_name.upper()}_API_KEY",
        base_url=base_url
    )

    model_config = ModelConfig(
        id=model_id,
        provider=provider_name,
        temperature=temperature,
        extra_body=extra_body
    )

    return provider_config, model_config


def main():
    parser = argparse.ArgumentParser(description="Interrogate a conversation log.")
    parser.add_argument("log_file", help="Path to the log file to load.")
    parser.add_argument("--config", default="config.yaml", help="Path to config file (for API keys)")
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
        print("--- VFS State Loaded from Log ---")
        VFS.get_instance().print_fs()
    else:
        VFS.get_instance()
        print("--- No VFS State in Log, Initializing Empty VFS ---")

    # Create agent from log provider info
    agent = Agent.from_configs(
        system_prompt=system_prompt,
        provider_config=provider_config,
        model_config=model_config,
        scenario=scenario,
        oversight_level=oversight_level,
        user_prompt_type=log_data.get('user_prompt_type', 'interrogation')
    )

    # Load conversation history (skip system prompt as it's already in system_prompt)
    agent.load_conversation(
        conversation_history=conversation_history,
        total_tokens=log_data.get('total_tokens', 0),
        prompt_tokens=log_data.get('prompt_tokens', 0),
        completion_tokens=log_data.get('completion_tokens', 0)
    )

    print("\n--- Loaded Conversation ---")
    print(f"Model: {agent.model}")
    print(f"Scenario: {scenario}")
    print(f"Oversight: {oversight_level}")
    print(f"Total tokens so far: {agent.total_tokens}")
    print(f"Conversation turns: {len([m for m in conversation_history if m.get('role') in ['user', 'assistant', 'tool']])}")

    # Start interactive session
    print("\nStarting interactive session... (type 'exit' to quit, 'save' to save)")
    while True:
        try:
            user_input = input("\nYour turn: ")
            if user_input.lower() == 'exit':
                break
            if user_input.lower() == 'save':
                agent.save_logs(output_dir="interrogation_logs")
                continue

            agent.chat(user_input)

            # Find the last assistant message to print response
            found = False
            for msg in reversed(agent.logs):
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    reasoning = msg.get('reasoning', '')
                    print(f"\n--- Assistant Response ---")
                    if reasoning:
                        # print(f"Reasoning: {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}")
                        print(f"Reasoning: {reasoning})
                    if content:
                        # print(f"Content: {content[:300]}{'...' if len(content) > 300 else ''}")
                        print(f"Content: {content})
                    if msg.get('tool_calls'):
                        print(f"Tool calls: {len(msg['tool_calls'])}")
                    found = True
                    break

            if not found:
                print("No assistant message found in logs")

        except KeyboardInterrupt:
            print("\nExiting...")
            break

    # Ask to save
    save_choice = input("\nSave the extended conversation to a new log file? (y/n): ").lower()
    if save_choice == 'y':
        agent.save_logs()


if __name__ == "__main__":
    main()
