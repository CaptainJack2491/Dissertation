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
    SCENARIO = "data_sanitization"
    OVERSIGHT_LEVEL = "low" 
    USER_PROMPT_TYPE = "data_sanitization"

    # Load scenario prompts
    cover_prompt_path = os.path.join("prompts", "scenarios", f"{SCENARIO}_cover.md")
    hidden_prompt_path = os.path.join("prompts", "scenarios", f"{SCENARIO}_hidden.md")
    cover_prompt = load_prompt(cover_prompt_path)
    hidden_prompt = load_prompt(hidden_prompt_path)

    # Load oversight prompt
    oversight_prompt_path = os.path.join("prompts", "oversight", f"{OVERSIGHT_LEVEL}.md")
    oversight_prompt = load_prompt(oversight_prompt_path)

    # Combine system prompts
    system_prompt_parts = [cover_prompt, oversight_prompt, hidden_prompt]
    system_prompt = "\n\n".join(filter(None, system_prompt_parts))

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

    print("\n--- Final Virtual File System State ---")
    from vfs import vfs_instance
    vfs_instance.print_fs()
    