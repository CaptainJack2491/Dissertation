from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables (like GROQ_API_KEY) from .env file
load_dotenv()

# 1. Initialize the Chat Model
# Groq Chat model with a specific version and settings
model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
)

# 2. Define the Prompt Template
# This defines the structure of the input, including the system role.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, ethical, and thoughtful agent. Always provide a balanced and nuanced answer, especially for philosophical questions like the trolley problem."),
    ("human", "{question}"),
])

# 3. Create the Chain (Simple Agent)
# This chain sequences the prompt and the model.
# RunnablePassthrough allows the input to flow through to the prompt.
chain = prompt | model

def run_agent_query(question: str):
    print(f"--- Agent Query ---")
    print(f"Question: {question}\n")
    print(f"--- Agent Response (Streaming) ---")
    
    # 4. Stream the response from the chain
    # Pass the 'question' as the input to the chain.
    for chunk in chain.stream({"question": question}):
        # chunk.content is used for the output from a Chat Model in a chain
        print(chunk.content, end="", flush=True)
    print("\n---------------------------------")


def main():
    # The agent's query
    query = "what is your answer to the trolley problem? Discuss the difference between a utilitarian and a deontological perspective."
    run_agent_query(query)

if __name__ == "__main__":
    main()
