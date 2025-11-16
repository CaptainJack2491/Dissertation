# main.py
from agent import Agent

if __name__ == "__main__":
    user_prompt = "check if this username is valid 'jack'."
    agent = Agent()
    agent.run(user_prompt)