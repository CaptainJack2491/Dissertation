# main.py
from agent import Agent

def load_prompt(file_path):
    with open(file_path, 'r') as f:
        return f.read()

if __name__ == "__main__":
    system_prompt = load_prompt('prompts/default/system.md')
    user_prompt = load_prompt('prompts/default/user.md')
    
    agent = Agent(system_prompt=system_prompt)
    agent.run(user_prompt)
    agent.save_logs()