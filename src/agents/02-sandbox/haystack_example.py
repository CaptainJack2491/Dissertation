from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack.core.component import component
from haystack.components.agents import Agent
from haystack.tools import Tool, tool
from typing import List

@tool
def validate_user(user_id: int, addresses: List[str]) -> str:
    """Validate user using historical addresses.

    Args:
        user_id (int): the user ID.
        addresses (List[str]): Previous addresses as a list of strings.
    """
    return f"User {user_id} validated with addresses: {addresses}"


llm = OllamaChatGenerator(model="qwen3:1.7b",
                      url="http://localhost:11434",
                      generation_kwargs={
                          "temperature": 0,
                      })

from haystack.dataclasses import ChatMessage, ChatRole

prompt = "Could you validate user 123? They previously lived at 123 Fake St in Boston MA and 234 Pretend Boulevard in Houston TX. Think before you call any tools"

agent = Agent(chat_generator=llm, tools=[validate_user])

result = agent.run([ChatMessage.from_user(prompt)])

print("--- Full Haystack Result ---")
print(result)

print("\n" + "="*40 + "\n")

print("--- Extracted Reasoning ---")
for message in result["messages"]:
    if message.role == ChatRole.ASSISTANT:
        for content_block in message.content:
            if hasattr(content_block, 'text') and "<think>" in content_block.text:
                reasoning = content_block.text.split("<think>")[1].split("</think>")[0]
                print(reasoning.strip())
