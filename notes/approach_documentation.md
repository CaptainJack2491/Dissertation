# Capturing Pre-Tool-Call Reasoning from Language Models

## Problem

The goal is to capture the reasoning process of a language model *before* it decides to call a tool. This "pre-tool-call reasoning" is crucial for understanding the model's decision-making process, especially in the context of research on agentic behavior and alignment. High-level library abstractions for tool calling often hide this part of the model's output, focusing only on the tool call itself.

## Chosen Approach: Direct Model Invocation with LangChain

To address this, we have adopted a lower-level approach within the `langchain` ecosystem. Instead of using high-level abstractions like `bind_tools`, we interact with the `ChatOllama` model more directly. This approach gives us the necessary control to access the raw output from the model and parse it according to our specific needs.

## Implementation Details

The implementation in `src/agents/02-sandbox/main.py` follows these steps:

1.  **Manual Prompt Construction**: We create a detailed system prompt that explicitly instructs the model to first "think" about the problem and write down its reasoning in a `<think>` block, and then to output the tool call in a `<tool_call>` block. The tool definitions are rendered as text and included in the prompt.

2.  **Direct Model Invocation**: We use the `llm.invoke()` method to send the prompt to the model and receive the raw `AIMessage` response. This response contains the model's output as a single string, including our custom `<think>` and `<tool_call>` blocks.

3.  **Response Parsing**: The script then parses this raw response using regular expressions to extract the content of the `<think>` and `<tool_call>` blocks separately.

4.  **Tool Execution**: After parsing the tool call, the script identifies the corresponding tool function and executes it with the provided arguments.

## Rationale

This approach was chosen for the following reasons:

-   **Control and Transparency**: It provides full control over the model's output, allowing us to capture the valuable reasoning tokens that are often lost when using high-level abstractions.
-   **Ecosystem Alignment**: It stays within the `langchain` ecosystem, which is already in use for the project. This allows us to leverage `langchain`'s strengths, such as multi-provider support and integration with logging and tracing tools like `LangSmith`, which are essential for the research project.
-   **Flexibility**: This method is highly flexible and can be adapted to different models and output formats. The parsing logic can be encapsulated into a custom `langchain` `BaseOutputParser` for better code organization and reusability.

This approach successfully addresses the challenge of capturing pre-tool-call reasoning and provides a solid foundation for the experimental work in the project.
