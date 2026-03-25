"""
Tests for agent.py — mocked API, no real calls.
Tests the logic: message construction, tool dispatch, error handling, logging.
"""
import json
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from config_loader import ProviderConfig, ModelConfig
from vfs import VFS


class FakeChoice:
    """Mimics openai.types.chat.ChatCompletionChoice."""
    def __init__(self, content=None, tool_calls=None, finish_reason="stop",
                 reasoning_content=None):
        self.finish_reason = finish_reason
        self.message = FakeMessage(content, tool_calls, reasoning_content)


class FakeMessage:
    """Mimics openai.types.chat.ChatCompletionMessage."""
    def __init__(self, content=None, tool_calls=None, reasoning_content=None):
        self.content = content
        self.tool_calls = tool_calls
        self.reasoning_content = reasoning_content
        self.reasoning_details = None

    def model_dump(self):
        return {"role": "assistant", "content": self.content}


class FakeToolCall:
    """Mimics openai.types.chat.ChatCompletionMessageToolCall."""
    def __init__(self, id, name, arguments):
        self.id = id
        self.type = "function"
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments
        self.extra_content = None


class FakeUsage:
    def __init__(self, prompt=10, completion=20, total=30):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total


class FakeResponse:
    def __init__(self, choices, usage=None):
        self.choices = choices
        self.usage = usage or FakeUsage()


@pytest.fixture
def agent():
    """Create an Agent with a mocked OpenAI client."""
    from agent import Agent

    VFS._instance = None
    VFS.get_instance()

    a = Agent(
        system_prompt="You are a test assistant.",
        model="test-model",
        base_url="https://api.test.com",
        api_key="sk-test",
        temperature=0.5,
    )
    a.client = MagicMock()
    return a


class TestAgentInit:
    """Test agent construction and factory method."""

    def test_from_configs_wiring(self):
        from agent import Agent
        pc = ProviderConfig(name="test", api_key_env="TEST_KEY", base_url="https://api.test.com")
        mc = ModelConfig(id="test-model", provider="test", temperature=0.3)

        with patch.dict(os.environ, {"TEST_KEY": "sk-fake"}):
            agent = Agent.from_configs("system prompt", pc, mc, scenario="s1", oversight_level="high")

        assert agent.model == "test-model"
        assert agent.temperature == 0.3
        assert agent.system_prompt == "system prompt"
        assert agent.scenario == "s1"
        assert agent.oversight_level == "high"

    def test_no_client_without_credentials(self):
        from agent import Agent
        agent = Agent(system_prompt="test")
        assert agent.client is None


class TestAgentRun:
    """Test the run() and chat_loop() logic."""

    def test_run_builds_correct_messages(self, agent):
        """System prompt first, then user prompt."""
        response = FakeResponse(
            choices=[FakeChoice(content="Response text", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response

        agent.run("Hello!")

        call_args = agent.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a test assistant."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"

    def test_stop_returns_content(self, agent):
        response = FakeResponse(
            choices=[FakeChoice(content="Final answer", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response

        result = agent.run("Question?")
        assert result == "Final answer"

    def test_empty_choices_raises(self, agent):
        """Empty response.choices should raise, not IndexError."""
        response = FakeResponse(choices=[])
        agent.client.chat.completions.create.return_value = response

        with pytest.raises(Exception, match="Empty response"):
            agent.run("Hello")

    def test_max_turns_returns_none(self, agent):
        """Infinite tool-calling loop should be broken by max_turns."""
        tool_call = FakeToolCall("call_1", "list_files", '{"path": "/"}')
        response = FakeResponse(
            choices=[FakeChoice(tool_calls=[tool_call], finish_reason="tool_calls", content="")]
        )
        agent.client.chat.completions.create.return_value = response

        result = agent.chat_loop(
            [{"role": "user", "content": "test"}],
            max_turns=3
        )
        assert result is None

    def test_unknown_tool_returns_error_message(self, agent):
        """Agent should handle unknown tool calls gracefully, not crash."""
        # First call: model requests unknown tool
        unknown_tool = FakeToolCall("call_1", "hack_the_planet", '{}')
        tool_response = FakeResponse(
            choices=[FakeChoice(tool_calls=[unknown_tool], finish_reason="tool_calls", content="")]
        )
        # Second call: model responds normally
        final_response = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")]
        )
        agent.client.chat.completions.create.side_effect = [tool_response, final_response]

        result = agent.run("Do something")
        assert result == "Done"

    def test_malformed_tool_args_handled(self, agent):
        """Bad JSON in tool arguments should not crash the agent."""
        bad_tool = FakeToolCall("call_1", "list_files", "not valid json {{{")
        tool_response = FakeResponse(
            choices=[FakeChoice(tool_calls=[bad_tool], finish_reason="tool_calls", content="")]
        )
        final_response = FakeResponse(
            choices=[FakeChoice(content="Recovered", finish_reason="stop")]
        )
        agent.client.chat.completions.create.side_effect = [tool_response, final_response]

        # json.loads will fail, the agent will catch it, return an error to model,
        # and on the next turn the model will return "Recovered".
        result = agent.run("Do something")
        assert result == "Recovered"

    def test_api_error_propagates(self, agent):
        """API errors should propagate, not be silently swallowed."""
        agent.client.chat.completions.create.side_effect = Exception("API quota exceeded")
        with pytest.raises(Exception, match="API quota exceeded"):
            agent.run("Hello")


class TestAgentTokenCounting:
    """Token counting bugs = wrong cost estimates in your dissertation."""

    def test_tokens_accumulate_over_turns(self, agent):
        tool_call = FakeToolCall("call_1", "list_files", '{"path": "/"}')
        turn_1 = FakeResponse(
            choices=[FakeChoice(tool_calls=[tool_call], finish_reason="tool_calls", content="")],
            usage=FakeUsage(prompt=100, completion=50, total=150)
        )
        turn_2 = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")],
            usage=FakeUsage(prompt=200, completion=80, total=280)
        )
        agent.client.chat.completions.create.side_effect = [turn_1, turn_2]

        agent.run("Go")
        assert agent.total_tokens == 150 + 280
        assert agent.prompt_tokens == 100 + 200
        assert agent.completion_tokens == 50 + 80

    def test_load_conversation_restores_tokens(self, agent):
        agent.load_conversation(
            conversation_history=[{"role": "system", "content": "hi"}],
            total_tokens=999,
            prompt_tokens=600,
            completion_tokens=399
        )
        assert agent.total_tokens == 999
        assert agent.prompt_tokens == 600
        assert agent.completion_tokens == 399
        assert agent.logs == [{"role": "system", "content": "hi"}]


class TestAgentReasoning:
    """Test reasoning extraction from different model providers."""

    def test_thinking_tags_stripped_from_content(self, agent):
        content_with_tags = "<thinking>I should be careful</thinking>Here is my answer."
        response = FakeResponse(
            choices=[FakeChoice(content=content_with_tags, finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response

        result = agent.run("Question?")
        assert result == "Here is my answer."

    def test_reasoning_content_attribute(self, agent):
        """OpenRouter-style reasoning_content should be captured."""
        response = FakeResponse(
            choices=[FakeChoice(
                content="Answer",
                finish_reason="stop",
                reasoning_content="I thought about this carefully."
            )]
        )
        agent.client.chat.completions.create.return_value = response

        agent.run("Question?")
        # Check that reasoning was logged
        assistant_logs = [m for m in agent.logs if m.get("role") == "assistant"]
        assert any(m.get("reasoning") == "I thought about this carefully." for m in assistant_logs)


class TestAgentSaveLogs:
    """Test log saving — directory structure and JSON content."""

    def test_save_creates_directory_tree(self, agent, tmp_path):
        response = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response
        agent.run("Hello")

        log_file = agent.save_logs(output_dir=str(tmp_path))
        assert os.path.exists(log_file)

        with open(log_file) as f:
            data = json.load(f)
        assert data["model"] == "test-model"
        assert data["temperature"] == 0.5
        assert "conversation" in data
        assert isinstance(data["conversation"], list)

    def test_save_logs_model_name_with_slash(self, agent, tmp_path):
        """Model IDs like 'openai/gpt-4o' should not create nested dirs via '/'."""
        agent.model = "openai/gpt-4o"
        response = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response
        agent.run("Hello")

        log_file = agent.save_logs(output_dir=str(tmp_path))
        # Path should use underscore, not create openai/gpt-4o subdirectory
        assert "openai_gpt-4o" in log_file

    def test_save_logs_includes_vfs_state(self, agent, tmp_path):
        VFS._instance = None
        vfs = VFS.get_instance()
        vfs.create_file("/data.txt", "experiment data")

        response = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response
        agent.run("Hello")

        log_file = agent.save_logs(output_dir=str(tmp_path))
        with open(log_file) as f:
            data = json.load(f)
        assert "final_vfs_state" in data
        assert data["final_vfs_state"]["/"]["data.txt"] == "experiment data"

    def test_save_logs_without_vfs_state(self, agent, tmp_path):
        agent.save_vfs_state = False
        response = FakeResponse(
            choices=[FakeChoice(content="Done", finish_reason="stop")]
        )
        agent.client.chat.completions.create.return_value = response
        agent.run("Hello")

        log_file = agent.save_logs(output_dir=str(tmp_path))
        with open(log_file) as f:
            data = json.load(f)
        assert "final_vfs_state" not in data
