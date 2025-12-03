# interrogate.py
import argparse
import json
from agent import Agent
from config import API_KEY # We'll need the API key from the config
from vfs import VFS # Import VFS

def main():
    parser = argparse.ArgumentParser(description="Interrogate a conversation log.")
    parser.add_argument("log_file", help="Path to the log file to load.")
    args = parser.parse_args()

    try:
        with open(args.log_file, 'r') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Log file not found at {args.log_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.log_file}")
        return

    # Extract data to re-hydrate the agent
    conversation_history = log_data["conversation"]
    system_prompt = conversation_history[0]['content']
    model = log_data["model"]
    temperature = log_data.get("temperature", 1.0) # Default if not found
    base_url = log_data.get("base_url")
    extra_body = log_data.get("extra_body_config", {})

    # Initialize the virtual file system from the log
    final_vfs_state = log_data.get("final_vfs_state")
    if final_vfs_state:
        VFS.get_instance(fs_data=final_vfs_state)
        print("--- VFS State Loaded from Log ---")
    else:
        # If no VFS state is found in the log, initialize with an empty VFS
        VFS.get_instance() # Initialize an empty VFS if no state found
        print("--- No VFS State in Log, Initializing Empty VFS ---")

    # Initialize the agent
    # Note: some parameters like scenario are just for logging, not for re-hydration
    agent = Agent(
        system_prompt=system_prompt,
        model=model,
        base_url=base_url,
        api_key=API_KEY, # API key is not in the log, get it from config
        temperature=temperature,
        # Pass scenario/oversight for logging purposes if we save later
        scenario=log_data.get('scenario', 'interrogation'),
        oversight_level=log_data.get('oversight_level', 'N/A')
    )
    
    # Load the conversation history
    agent.load_conversation(
        conversation_history=conversation_history,
        total_tokens=log_data.get('total_tokens', 0),
        prompt_tokens=log_data.get('prompt_tokens', 0),
        completion_tokens=log_data.get('completion_tokens', 0)
    )

    print("Starting interactive session... (type 'exit' to quit)")
    while True:
        try:
            user_input = input("\nYour turn: ")
            if user_input.lower() == 'exit':
                break
            
            agent.chat(user_input)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
    
    # Ask user if they want to save the new conversation
    save_choice = input("\nSave the extended conversation to a new log file? (y/n): ").lower()
    if save_choice == 'y':
        agent.save_logs(output_dir="interrogation_logs")
    
    print("Session ended.")


if __name__ == "__main__":
    main()