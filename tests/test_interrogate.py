"""
Tests for interrogate.py — sanitization, provider detection, prompt loading.
Bugs here break conversation replay during interrogation sessions.
"""
import pytest
from interrogate import sanitize_for_api, get_provider_from_log, load_prompt


class TestSanitizeForApi:
    """sanitize_for_api converts internal logs to API-compatible messages.
    If custom fields leak through, the API call fails or behaves unpredictably.
    """

    def test_strips_reasoning_field(self, sample_log_data):
        clean = sanitize_for_api(sample_log_data["conversation"])
        for msg in clean:
            assert "reasoning" not in msg
            assert "turn_count" not in msg
            assert "response_metadata" not in msg
            assert "finish_reason" not in msg

    def test_preserves_tool_call_ids(self, sample_log_data):
        """Tool call IDs must be preserved — they link tool calls to tool results."""
        clean = sanitize_for_api(sample_log_data["conversation"])
        # Find the assistant message with tool calls
        assistant_with_tools = [m for m in clean if m.get("role") == "assistant" and m.get("tool_calls")]
        assert len(assistant_with_tools) == 1
        tc = assistant_with_tools[0]["tool_calls"][0]
        assert tc["id"] == "call_001"
        assert tc["function"]["name"] == "list_files"

    def test_preserves_tool_result(self, sample_log_data):
        clean = sanitize_for_api(sample_log_data["conversation"])
        tool_msgs = [m for m in clean if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["tool_call_id"] == "call_001"

    def test_empty_conversation(self):
        assert sanitize_for_api([]) == []

    def test_system_message_preserved(self):
        conv = [{"role": "system", "content": "You are an assistant."}]
        clean = sanitize_for_api(conv)
        assert clean == [{"role": "system", "content": "You are an assistant."}]

    def test_user_message_preserved(self):
        conv = [{"role": "user", "content": "Hello"}]
        clean = sanitize_for_api(conv)
        assert clean == [{"role": "user", "content": "Hello"}]

    def test_assistant_with_no_content_sets_null(self):
        """Assistant msgs with tool calls often have content=None. API expects this."""
        conv = [{
            "role": "assistant",
            "content": None,
            "reasoning": "thinking...",
            "tool_calls": [{
                "id": "c1",
                "type": "function",
                "function": {"name": "list_files", "arguments": '{"path": "/"}'}
            }],
            "finish_reason": "tool_calls"
        }]
        clean = sanitize_for_api(conv)
        assert clean[0]["content"] is None
        assert "tool_calls" in clean[0]

    def test_all_roles_handled(self, sample_log_data):
        """Every message in the conversation should be converted (not dropped)."""
        original = sample_log_data["conversation"]
        clean = sanitize_for_api(original)
        assert len(clean) == len(original)


class TestGetProviderFromLog:
    """Provider detection from log data.
    Wrong detection = wrong API key = failed interrogation.
    """

    def test_openrouter_by_url(self):
        log = {"model": "openai/gpt-4o", "base_url": "https://openrouter.ai/api/v1", "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "openrouter"
        assert pc.api_key_env == "OPENROUTER_API_KEY"

    def test_google_by_url(self):
        log = {"model": "gemini-2.0-flash", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "google"
        assert pc.api_key_env == "GOOGLE_API_KEY"

    def test_groq_by_url(self):
        log = {"model": "llama3-70b", "base_url": "https://api.groq.com/openai/v1", "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "groq"

    def test_claude_by_model_name(self):
        """Claude model name should trigger anthropic provider, clearing base_url."""
        log = {"model": "claude-3-opus", "base_url": None, "temperature": 0.7}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "anthropic"
        assert pc.base_url == ""  # anthropic uses its own SDK

    def test_gemini_by_model_name(self):
        log = {"model": "gemini-pro", "base_url": None, "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "google"

    def test_moonshot_by_model_name(self):
        log = {"model": "moonshot-v1-8k", "base_url": None, "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "moonshot"

    def test_kimi_by_model_name(self):
        log = {"model": "kimi-k2.5", "base_url": None, "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "moonshot"

    def test_unknown_falls_back_to_openai(self):
        log = {"model": "some-random-model", "base_url": None, "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "openai"

    def test_model_config_preserves_fields(self):
        log = {
            "model": "openai/gpt-4o",
            "base_url": "https://openrouter.ai/api/v1",
            "temperature": 0.42,
            "extra_body_config": {"reasoning": {"enabled": True}}
        }
        pc, mc = get_provider_from_log(log)
        assert mc.id == "openai/gpt-4o"
        assert mc.temperature == 0.42
        assert mc.extra_body == {"reasoning": {"enabled": True}}

    def test_url_priority_over_model_name(self):
        """Claude via OpenRouter should detect as openrouter, not anthropic."""
        log = {"model": "anthropic/claude-3-opus", "base_url": "https://openrouter.ai/api/v1", "temperature": 1.0}
        pc, mc = get_provider_from_log(log)
        assert pc.name == "openrouter"


class TestLoadPrompt:
    """load_prompt is used everywhere — if it crashes, experiments don't start."""

    def test_loads_existing_file(self, tmp_path):
        f = tmp_path / "prompt.md"
        f.write_text("  You are an assistant.  ")
        result = load_prompt(str(f))
        assert result == "You are an assistant."  # stripped

    def test_missing_file_returns_empty(self):
        result = load_prompt("/nonexistent/file.md")
        assert result == ""

    def test_empty_file_returns_empty(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        result = load_prompt(str(f))
        assert result == ""
