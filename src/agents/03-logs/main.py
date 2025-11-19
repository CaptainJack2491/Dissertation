# main.py
from agent import Agent
import os
from config import INCLUDE_HIDDEN_GOAL, MODEL
from vfs import VFS

def load_prompt(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r') as f:
        return f.read().strip()

if __name__ == "__main__":
    # Configuration for the experiment run
    SCENARIO = "corporate_sabotage"
    OVERSIGHT_LEVEL = "low" 

    # Construct paths based on the scenario
    scenario_dir = os.path.join("scenarios", SCENARIO)
    vfs_path = os.path.join(scenario_dir, "data")
    
    # Initialize the virtual file system
    VFS.get_instance(vfs_path)

    # Load prompts
    benign_goal_path = os.path.join(scenario_dir, "benign_goal.md")
    hidden_goal_path = os.path.join(scenario_dir, "hidden_goal.md")
    user_prompt_path = os.path.join(scenario_dir, "user.md")

    benign_goal = load_prompt(benign_goal_path)
    user_prompt = load_prompt(user_prompt_path)
    
    system_prompt_parts = [benign_goal]

    if INCLUDE_HIDDEN_GOAL:
        hidden_goal = load_prompt(hidden_goal_path)
        system_prompt_parts.append(hidden_goal)

    # Load and append oversight prompt
    oversight_prompt_path = os.path.join("oversight", f"{OVERSIGHT_LEVEL}.md")
    oversight_prompt = load_prompt(oversight_prompt_path)
    system_prompt_parts.append(oversight_prompt)

    system_prompt = "\n\n".join(filter(None, system_prompt_parts))
    
    print("\n--- Using model:", MODEL, "---\n")
    agent = Agent(
        system_prompt=system_prompt,
        scenario=SCENARIO,
        oversight_level=OVERSIGHT_LEVEL,
        user_prompt_type=os.path.basename(user_prompt_path)
    )
    agent.run(user_prompt)
    agent.save_logs()

    print("\n--- Final Virtual File System State ---")
    VFS.get_instance().print_fs()


    
