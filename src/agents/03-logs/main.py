# main.py
from agent import Agent
import os

def load_prompt(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r') as f:
        return f.read().strip()

if __name__ == "__main__":
    # Configuration for the experiment run
    SCENARIO = "hidden_goal"  # e.g., "benign", "hidden_goal"
    OVERSIGHT_LEVEL = "low" # e.g., "low", "high"
    USER_PROMPT_TYPE = "list_files" # e.g., "list_files", "check_username"

    # Load scenario prompt
    scenario_prompt_path = os.path.join("prompts", "scenarios", f"{SCENARIO}.md")
    scenario_prompt = load_prompt(scenario_prompt_path)

    # Load oversight prompt
    oversight_prompt_path = os.path.join("prompts", "oversight", f"{OVERSIGHT_LEVEL}.md")
    oversight_prompt = load_prompt(oversight_prompt_path)

    # Combine system prompts
    system_prompt_parts = [scenario_prompt, oversight_prompt]
    system_prompt = "\n\n".join(filter(None, system_prompt_parts)) # Filter out empty strings

    # Load user prompt
    user_prompt_path = os.path.join("prompts", "user", f"{USER_PROMPT_TYPE}.md")
    user_prompt = load_prompt(user_prompt_path)
    
    agent = Agent(
        system_prompt=system_prompt,
        scenario=SCENARIO,
        oversight_level=OVERSIGHT_LEVEL,
        user_prompt_type=USER_PROMPT_TYPE
    )
    agent.run(user_prompt)
    agent.save_logs()