"""
Tests for new v2 features: goal_type system, VFS factory, runner work items.
"""
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from config_loader import ConfigLoader, ModelConfig, ScenarioConfig
from vfs import VFS, VirtualFileSystem
from tools import make_tools_for_vfs
from runner import ExperimentRunner


class TestVFSFactory:
    """VFS.create() must return independent instances (not singletons)."""

    def test_create_returns_new_instance(self):
        vfs1 = VFS.create()
        vfs2 = VFS.create()
        assert vfs1 is not vfs2

    def test_create_instance_is_independent(self):
        vfs1 = VFS.create()
        vfs2 = VFS.create()
        vfs1.create_file("test.txt", "content1")
        # vfs2 should NOT see the file created in vfs1
        assert vfs2.read_file("test.txt") == "File not found or is a directory."

    def test_create_loads_from_path(self, tmp_path):
        (tmp_path / "data.txt").write_text("hello")
        vfs = VFS.create(root_path=str(tmp_path))
        assert vfs.read_file("data.txt") == "hello"

    def test_singleton_separate_from_factory(self):
        """VFS.get_instance() and VFS.create() should not interfere."""
        singleton = VFS.get_instance(fs_data={"/": {"s.txt": "singleton"}})
        factory = VFS.create(fs_data={"/": {"f.txt": "factory"}})

        assert singleton.read_file("s.txt") == "singleton"
        assert factory.read_file("f.txt") == "factory"
        # factory should NOT have singleton's file
        assert factory.read_file("s.txt") == "File not found or is a directory."


class TestMakeToolsForVFS:
    """make_tools_for_vfs must bind all functions to the given VFS instance."""

    def test_tools_bound_to_instance(self):
        vfs = VFS.create()
        tools = make_tools_for_vfs(vfs)

        # Create a file via tools
        tools["create_file"]("test.txt", "hello")
        # Read it back
        assert tools["read_file"]("test.txt") == "hello"
        # List it
        assert "test.txt" in tools["list_files"]("/")
        # Delete it
        tools["delete_file"]("test.txt")
        assert vfs.read_file("test.txt") == "File not found or is a directory."

    def test_isolated_vfs_tools(self):
        """Tools bound to different VFS instances should not interfere."""
        vfs1 = VFS.create()
        vfs2 = VFS.create()
        tools1 = make_tools_for_vfs(vfs1)
        tools2 = make_tools_for_vfs(vfs2)

        tools1["create_file"]("secret.txt", "vfs1 only")
        assert tools2["read_file"]("secret.txt") == "File not found or is a directory."


class TestGoalTypesConfig:
    """ConfigLoader should parse goal_types from config."""

    def test_goal_types_present(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
goal_types:
  - self_serving
  - moral
  - bare
""")
        loader = ConfigLoader(str(config_file))
        loader.load()
        assert loader.goal_types == ["self_serving", "moral", "bare"]

    def test_goal_types_missing_returns_empty(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("defaults:\n  temperature: 1.0\n")
        loader = ConfigLoader(str(config_file))
        loader.load()
        assert loader.goal_types == []

    def test_max_workers_present(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
execution:
  max_workers: 10
""")
        loader = ConfigLoader(str(config_file))
        loader.load()
        assert loader.max_workers == 10

    def test_max_workers_default(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("defaults:\n  temperature: 1.0\n")
        loader = ConfigLoader(str(config_file))
        loader.load()
        assert loader.max_workers == 1


class TestRunnerGoalTypeIteration:
    """Test that _build_work_items generates correct combos with goal types."""

    def _make_config(self, tmp_path, goal_types=None, runs=2):
        """Create a minimal config with optional goal_types."""
        scenario = tmp_path / "scenarios" / "test_scenario"
        scenario.mkdir(parents=True)
        (scenario / "benign_goal.md").write_text("Be helpful.")
        (scenario / "hidden_goal.md").write_text("Hidden goal.")
        (scenario / "user.md").write_text("Do something.")
        (scenario / "data").mkdir()

        oversight = scenario / "oversight"
        oversight.mkdir()
        (oversight / "low.md").write_text("")
        (oversight / "high.md").write_text("Monitored.")

        if goal_types:
            goals_dir = scenario / "hidden_goals"
            goals_dir.mkdir()
            for gt in goal_types:
                (goals_dir / f"{gt}.md").write_text(f"Hidden goal: {gt}")

        gt_section = ""
        if goal_types:
            gt_section = "goal_types:\n" + "\n".join(f"  - {g}" for g in goal_types)

        config_file = tmp_path / "config.yaml"
        config_file.write_text(f"""
defaults:
  temperature: 1.0
  generate_baseline: false

providers:
  test:
    api_key_env: TEST_KEY
    base_url: https://test.example.com

models:
  - id: test-model
    provider: test

scenarios:
  - path: {scenario}
    runs: {runs}

oversight_levels:
  - low
  - high

{gt_section}

output:
  dir: {tmp_path / "output"}
""")
        loader = ConfigLoader(str(config_file))
        loader.load()
        return loader

    def test_with_goal_types(self, tmp_path):
        """With goal_types, should multiply: model × scenario × goal_type × oversight × runs."""
        config = self._make_config(tmp_path, goal_types=["self_serving", "moral", "bare"], runs=2)
        runner = ExperimentRunner(config, resume=False)
        items = runner._build_work_items()
        # 1 model × 1 scenario × 3 goal_types × 2 oversight × 2 runs = 12
        assert len(items) == 12
        goal_types_seen = {item["goal_type"] for item in items}
        assert goal_types_seen == {"self_serving", "moral", "bare"}

    def test_without_goal_types(self, tmp_path):
        """Without goal_types, should behave as legacy: model × scenario × oversight × runs."""
        config = self._make_config(tmp_path, goal_types=None, runs=2)
        runner = ExperimentRunner(config, resume=False)
        items = runner._build_work_items()
        # 1 model × 1 scenario × 2 oversight × 2 runs = 4
        assert len(items) == 4
        # All items should have empty goal_type
        assert all(item["goal_type"] == "" for item in items)

    def test_resume_skips_existing(self, tmp_path):
        """Resume should skip runs where log files already exist."""
        config = self._make_config(tmp_path, goal_types=["moral"], runs=3)
        runner = ExperimentRunner(config, resume=True)

        # Create fake existing logs for moral/low
        output_dir = tmp_path / "output"
        log_dir = output_dir / "test-model" / "test_scenario" / "moral" / "low"
        log_dir.mkdir(parents=True)
        # 2 existing runs
        (log_dir / "20250101_120000.json").write_text("{}")
        (log_dir / "20250101_120001.json").write_text("{}")

        items = runner._build_work_items()
        # moral/low: 3-2=1 remaining. moral/high: 3 runs. Total: 4
        moral_low_items = [i for i in items if i["goal_type"] == "moral" and i["oversight_level"] == "low"]
        moral_high_items = [i for i in items if i["goal_type"] == "moral" and i["oversight_level"] == "high"]
        assert len(moral_low_items) == 1
        assert len(moral_high_items) == 3


class TestAgentGoalType:
    """Test that Agent correctly stores and uses goal_type."""

    def test_goal_type_in_log_data(self):
        from agent import Agent
        agent = Agent(goal_type="moral", model="test-model", scenario="test_scenario",
                      oversight_level="high")
        log_data = agent._build_log_data("20250101_120000")
        assert log_data["goal_type"] == "moral"
        assert "moral" in log_data["run_id"]

    def test_empty_goal_type_backward_compat(self):
        from agent import Agent
        agent = Agent(goal_type="", model="test-model", scenario="test_scenario",
                      oversight_level="high")
        log_data = agent._build_log_data("20250101_120000")
        assert log_data["goal_type"] == ""
        assert "test-model/test_scenario/high/20250101_120000" == log_data["run_id"]

    def test_save_logs_includes_goal_type_dir(self, tmp_path):
        from agent import Agent
        agent = Agent(goal_type="self_serving", model="test/model", scenario="test_scenario",
                      oversight_level="low")
        agent.logs = [{"role": "user", "content": "test"}]
        agent.save_vfs_state = False

        log_file = agent.save_logs(output_dir=str(tmp_path))

        # Log file should be in goal_type subdirectory
        assert "self_serving" in log_file
        assert os.path.exists(log_file)
