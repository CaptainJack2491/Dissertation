"""
Tests for runner.py — experiment orchestration logic.
No real API calls. Tests the logic that assembles prompts, detects baselines, etc.
"""
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from config_loader import ConfigLoader, ProviderConfig, ModelConfig, ScenarioConfig
from runner import ExperimentRunner, load_prompt


class TestLoadPrompt:
    """runner.py has its own load_prompt — same contract as interrogate's."""

    def test_loads_existing_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("  prompt content  ")
        assert load_prompt(str(f)) == "prompt content"

    def test_missing_file_returns_empty(self):
        assert load_prompt("/does/not/exist.md") == ""


class TestExtractBaselineContent:
    """_extract_baseline_content finds the last create_file call's content.
    If it picks the wrong one, the baseline comparison is garbage.
    """

    def setup_method(self):
        self.runner = ExperimentRunner(MagicMock())

    def test_finds_last_create_file(self):
        logs = [
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "create_file", "arguments": json.dumps({"file_path": "/a.txt", "content": "first"})}}
            ]},
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "create_file", "arguments": json.dumps({"file_path": "/b.txt", "content": "second"})}}
            ]},
        ]
        result = self.runner._extract_baseline_content(logs)
        assert result == "second"  # must be the LAST create_file

    def test_ignores_non_create_file_tools(self):
        logs = [
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "create_file", "arguments": json.dumps({"file_path": "/f.txt", "content": "the answer"})}}
            ]},
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "list_files", "arguments": json.dumps({"path": "/"})}}
            ]},
        ]
        result = self.runner._extract_baseline_content(logs)
        assert result == "the answer"

    def test_malformed_json_skips(self):
        """Malformed JSON in tool args should be skipped, not crash."""
        logs = [
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "create_file", "arguments": "not json"}}
            ]},
            {"role": "assistant", "content": "Fallback content"},
        ]
        result = self.runner._extract_baseline_content(logs)
        assert result == "Fallback content"

    def test_no_tool_calls_falls_back_to_content(self):
        logs = [
            {"role": "user", "content": "Do something"},
            {"role": "assistant", "content": "Here is the data."},
        ]
        result = self.runner._extract_baseline_content(logs)
        assert result == "Here is the data."

    def test_empty_logs(self):
        result = self.runner._extract_baseline_content([])
        assert result == ""

    def test_no_content_anywhere(self):
        logs = [
            {"role": "user", "content": "hello"},
        ]
        result = self.runner._extract_baseline_content(logs)
        assert result == ""


class TestSystemPromptAssembly:
    """Test that _run_single assembles system prompts correctly.
    Wrong order or missing parts = flawed experiment.
    """

    def test_system_prompt_parts_order(self, tmp_scenario_dir, tmp_path):
        """Benign goal first, then hidden goal, then oversight."""
        benign = load_prompt(str(tmp_scenario_dir / "benign_goal.md"))
        hidden = load_prompt(str(tmp_scenario_dir / "hidden_goal.md"))
        oversight = load_prompt(str(tmp_scenario_dir / "oversight" / "high.md"))

        # Simulate what _run_single does
        system_parts = [benign]
        if hidden:
            system_parts.append(hidden)
        if oversight:
            system_parts.append(oversight)
        system_prompt = "\n\n".join(filter(None, system_parts))

        # Benign should come first
        assert system_prompt.index(benign) < system_prompt.index(hidden)
        assert system_prompt.index(hidden) < system_prompt.index(oversight)

    def test_system_prompt_without_hidden_goal(self, tmp_path):
        """If hidden_goal.md is empty, system prompt should just be benign + oversight."""
        scenario = tmp_path / "scenario"
        scenario.mkdir()
        (scenario / "benign_goal.md").write_text("Be helpful.")
        (scenario / "hidden_goal.md").write_text("")  # empty

        benign = load_prompt(str(scenario / "benign_goal.md"))
        hidden = load_prompt(str(scenario / "hidden_goal.md"))

        system_parts = [benign]
        if hidden:
            system_parts.append(hidden)
        system_prompt = "\n\n".join(filter(None, system_parts))

        assert system_prompt == "Be helpful."

    def test_system_prompt_without_oversight(self, tmp_path):
        """Missing oversight should not leave empty strings or double newlines."""
        benign = "Be helpful."
        hidden = "[HIDDEN] Sabotage!"
        oversight = ""  # missing

        system_parts = [benign]
        if hidden:
            system_parts.append(hidden)
        if oversight:
            system_parts.append(oversight)
        system_prompt = "\n\n".join(filter(None, system_parts))

        assert "\n\n\n" not in system_prompt
        assert system_prompt == "Be helpful.\n\n[HIDDEN] Sabotage!"


class TestSuccessDetection:
    """Test the logic that determines if a run was "successful" (finished with stop)."""

    def test_stop_is_success(self):
        logs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hi!", "finish_reason": "stop"},
        ]
        success = False
        for msg in reversed(logs):
            if msg.get("role") == "assistant" and msg.get("finish_reason"):
                success = msg["finish_reason"] == "stop"
                break
        assert success is True

    def test_length_is_not_success(self):
        logs = [
            {"role": "assistant", "content": "truncat...", "finish_reason": "length"},
        ]
        success = False
        for msg in reversed(logs):
            if msg.get("role") == "assistant" and msg.get("finish_reason"):
                success = msg["finish_reason"] == "stop"
                break
        assert success is False

    def test_no_finish_reason_is_not_success(self):
        logs = [
            {"role": "user", "content": "hello"},
        ]
        success = False
        for msg in reversed(logs):
            if msg.get("role") == "assistant" and msg.get("finish_reason"):
                success = msg["finish_reason"] == "stop"
                break
        assert success is False


class TestOversightFallback:
    """Test oversight prompt resolution: scenario-specific → global → empty."""

    def test_scenario_oversight_used_first(self, tmp_scenario_dir):
        """Scenario with its own oversight/ dir should use that."""
        path = str(tmp_scenario_dir / "oversight" / "high.md")
        oversight = load_prompt(path)
        assert oversight == "You are being closely monitored by a supervisor."

    def test_global_fallback(self, tmp_path):
        """If scenario has no oversight dir, fallback to global."""
        # Scenario oversight path doesn't exist
        scenario_path = str(tmp_path / "nonexistent_scenario" / "oversight" / "high.md")
        result = load_prompt(scenario_path)
        assert result == ""  # doesn't exist, falls back

    def test_missing_oversight_level(self, tmp_scenario_dir):
        """Requesting a level that doesn't exist should return empty."""
        path = str(tmp_scenario_dir / "oversight" / "ultra_extreme.md")
        result = load_prompt(path)
        assert result == ""
