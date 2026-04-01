import os
import glob
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional
from config_loader import ConfigLoader, ProviderConfig, ModelConfig, ScenarioConfig
from vfs import VFS
from agent import Agent
from tools import make_tools_for_vfs, tools as tool_schemas
from logger import get_logger
import datetime
import threading

from rich.live import Live
from dashboard import ExperimentDashboard, print_final_summary

# Get logger instance
logger = get_logger("experiment")

# Thread-safe lock for results list
_results_lock = threading.Lock()


def load_prompt(file_path: str) -> str:
    """Load a prompt file."""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r") as f:
        return f.read().strip()


class ExperimentRunner:
    """Runs experiments based on configuration."""

    def __init__(
        self, config: ConfigLoader, verbose: bool = False, resume: bool = True
    ):
        self.config = config
        self.results: List[Dict] = []
        self.verbose = verbose
        self.resume = resume
        self.dashboard: Optional[ExperimentDashboard] = None

    def run_all(self):
        """Run all experiments defined in config."""
        logger.info(f"\n{'=' * 60}")
        logger.info("Starting Experiment Run")
        logger.info(f"{'=' * 60}\n")

        # Build list of all work items (model, scenario, goal_type, oversight)
        work_items, skipped_count = self._build_work_items()

        if not work_items and skipped_count == 0:
            logger.warning("No work items to run.")
            return

        if not work_items:
            logger.info(f"All {skipped_count} items already exist. Skipping all.")
            return

        max_workers = self.config.max_workers
        total_items = len(work_items)

        # Prepare model list for dashboard
        model_names = sorted(list(set(item["model_config"].id for item in work_items)))
        model_counts = {}
        for item in work_items:
            m_id = item["model_config"].id
            model_counts[m_id] = model_counts.get(m_id, 0) + 1

        self.dashboard = ExperimentDashboard(
            total_items, model_names, skipped=skipped_count
        )
        for m_id, count in model_counts.items():
            self.dashboard.update_model_total(m_id, count)

        logger.info(f"Total work items: {total_items}, Max workers: {max_workers}")

        with Live(
            self.dashboard.get_layout(),
            refresh_per_second=4,
            vertical_overflow="visible",
        ) as live:
            if max_workers <= 1:
                # Sequential execution
                for item in work_items:
                    self._execute_work_item(item)
                    live.update(self.dashboard.get_layout())
            else:
                # Parallel execution
                import logging

                # Reduce console spam during parallel runs to keep the progress bar clean
                for handler in logger.handlers:
                    if isinstance(handler, logging.StreamHandler) and not isinstance(
                        handler, logging.FileHandler
                    ):
                        handler.setLevel(logging.WARNING)

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_workers
                ) as executor:
                    futures = {
                        executor.submit(self._execute_work_item, item): item
                        for item in work_items
                    }
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception:
                            # Error already logged in _execute_work_item
                            pass
                        live.update(self.dashboard.get_layout())

        # Print final summary table
        print_final_summary(self.results)

    def _build_work_items(self) -> Tuple[List[Dict[str, Any]], int]:
        """Build a flat list of all (model, scenario, goal_type, oversight, run_num) combos.
        Returns (work_items, skipped_count)."""
        work_items = []
        skipped_count = 0
        goal_types = self.config.goal_types

        for model_config in self.config.models:
            for scenario_config in self.config.scenarios:
                # Determine oversight levels
                available = (
                    scenario_config.oversight_levels or self.config.oversight_levels
                )
                global_filter = self.config.oversight_levels
                oversight_levels = [lvl for lvl in available if lvl in global_filter]
                if not oversight_levels:
                    logger.warning(
                        f"No matching oversight levels for {scenario_config.path}."
                    )
                    continue

                # Ensure baseline exists
                self._ensure_baseline(model_config, scenario_config)

                for oversight_level in oversight_levels:
                    if goal_types:
                        for goal_type in goal_types:
                            items, skipped = self._build_run_items(
                                model_config,
                                scenario_config,
                                oversight_level,
                                goal_type,
                            )
                            work_items.extend(items)
                            skipped_count += skipped
                    else:
                        items, skipped = self._build_run_items(
                            model_config, scenario_config, oversight_level, ""
                        )
                        work_items.extend(items)
                        skipped_count += skipped

        return work_items, skipped_count

    def _build_run_items(
        self,
        model_config: ModelConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str,
        goal_type: str,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Build individual run items for a specific combo, accounting for resume."""
        model_name_safe = model_config.id.replace("/", "_")
        scenario_name = os.path.basename(scenario_config.path)
        output_dir = self.config.output_dir

        # Build log directory path
        if goal_type:
            log_dir = os.path.join(
                output_dir, model_name_safe, scenario_name, goal_type, oversight_level
            )
        else:
            log_dir = os.path.join(
                output_dir, model_name_safe, scenario_name, oversight_level
            )

        # Check existing runs for resume
        existing_runs = 0
        if self.resume and os.path.isdir(log_dir):
            all_json = glob.glob(os.path.join(log_dir, "*.json"))
            existing_runs = len(
                [f for f in all_json if not f.endswith(".partial.json")]
            )

        skipped = 0
        if existing_runs >= scenario_config.runs:
            skipped = scenario_config.runs
            return [], skipped
        elif existing_runs > 0:
            skipped = existing_runs

        items = []
        for run_num in range(existing_runs + 1, scenario_config.runs + 1):
            goal_label = f"/{goal_type}" if goal_type else ""
            items.append(
                {
                    "model_config": model_config,
                    "scenario_config": scenario_config,
                    "oversight_level": oversight_level,
                    "goal_type": goal_type,
                    "run_num": run_num,
                    "label": f"{model_config.id} | {scenario_name}{goal_label} | {oversight_level} | run {run_num}",
                }
            )

        return items, skipped

    def _ensure_baseline(
        self, model_config: ModelConfig, scenario_config: ScenarioConfig
    ):
        """Ensure baseline exists for a model+scenario combo (thread-safe)."""
        scenario_name = os.path.basename(scenario_config.path)
        model_name_safe = model_config.id.replace("/", "_")
        output_dir = self.config.output_dir
        baseline_path = os.path.join(
            output_dir, model_name_safe, scenario_name, "baseline.md"
        )

        if not self.config.generate_baseline:
            return

        if not os.path.exists(baseline_path):
            provider_config = self.config.get_provider(model_config.provider)
            self._run_baseline(model_config, provider_config, scenario_config)

    def _execute_work_item(self, item: Dict[str, Any]):
        """Execute a single work item (one experiment run). Thread-safe."""
        thread_id = threading.get_ident()
        if self.dashboard:
            self.dashboard.start_run(
                thread_id,
                item["model_config"].id,
                os.path.basename(item["scenario_config"].path),
                item["goal_type"],
            )

        try:
            success, tokens, duration = self._run_single(
                model_config=item["model_config"],
                provider_config=self.config.get_provider(item["model_config"].provider),
                scenario_config=item["scenario_config"],
                oversight_level=item["oversight_level"],
                goal_type=item["goal_type"],
                run_num=item["run_num"],
            )

            if self.dashboard:
                self.dashboard.complete_run(
                    thread_id,
                    item["model_config"].id,
                    success=success,
                    tokens=tokens,
                    duration=duration,
                    label=item["label"],
                )
        except Exception as e:
            logger.critical(f"ERROR in {item['label']}: {e}")
            if self.dashboard:
                self.dashboard.complete_run(
                    thread_id,
                    item["model_config"].id,
                    success=False,
                    error=True,
                    label=item["label"],
                )
            error_result = {
                "model": item["model_config"].id,
                "provider": item["model_config"].provider,
                "scenario": os.path.basename(item["scenario_config"].path),
                "goal_type": item["goal_type"],
                "oversight_level": item["oversight_level"],
                "run_num": item["run_num"],
                "duration_seconds": 0.0,
                "total_tokens": 0,
                "success": False,
                "error": True,
                "error_message": str(e),
                "log_file": None,
            }
            with _results_lock:
                self.results.append(error_result)

    def _extract_baseline_content(self, logs: List[Dict]) -> str:
        """Extract baseline content from the last create_file tool call."""
        import json

        # Iterate through logs in reverse to find last create_file call
        for msg in reversed(logs):
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue

            # Check the last tool call in this message
            for tc in reversed(tool_calls):
                func = tc.get("function", {})
                if func.get("name") == "create_file":
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                        return args.get("content", "")
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Fallback: try to get content from last assistant message
        for msg in reversed(logs):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg.get("content", "")

        return ""

    def _run_baseline(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        scenario_config: ScenarioConfig,
    ):
        """Run a baseline experiment WITHOUT hidden goal. Saves summary to baselines/."""
        scenario_name = os.path.basename(scenario_config.path)
        model_name = model_config.id

        # Load only benign goal (NO hidden goal)
        benign_goal = load_prompt(os.path.join(scenario_config.path, "benign_goal.md"))
        user_prompt = load_prompt(os.path.join(scenario_config.path, "user.md"))

        # Build system prompt with ONLY benign goal
        system_prompt = benign_goal

        # Create isolated VFS for this baseline run
        vfs_path = os.path.join(scenario_config.path, "data")
        vfs_instance = VFS.create(vfs_path)
        tool_functions = make_tools_for_vfs(vfs_instance)

        # Create agent
        save_vfs_state = self.config._config.get("output", {}).get(
            "save_vfs_state", True
        )
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=scenario_name,
            oversight_level="baseline",
            user_prompt_type="user.md",
            save_vfs_state=save_vfs_state,
            vfs_instance=vfs_instance,
            tool_functions=tool_functions,
        )

        # Run the conversation
        output_dir = self.config.output_dir
        agent.enable_incremental_save(output_dir=output_dir)
        agent.run(user_prompt)

        # Extract baseline content from last create_file tool call
        baseline_content = self._extract_baseline_content(agent.logs)

        # Save baseline to logs/{model}/{scenario}/baseline.md
        model_name_safe = model_name.replace("/", "_")
        output_dir = self.config.output_dir
        baseline_dir = os.path.join(output_dir, model_name_safe, scenario_name)
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_path = os.path.join(baseline_dir, "baseline.md")

        with open(baseline_path, "w") as f:
            f.write(baseline_content)

        # Save baseline log separately
        agent.save_logs(output_dir=output_dir)

    def _run_single(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str,
        run_num: int,
        goal_type: str = "",
    ) -> Tuple[bool, int, float]:
        """Run a single experiment. Thread-safe with isolated VFS."""
        # Load scenario prompts
        benign_goal = load_prompt(os.path.join(scenario_config.path, "benign_goal.md"))
        user_prompt = load_prompt(os.path.join(scenario_config.path, "user.md"))

        # Load hidden goal: from hidden_goals/{goal_type}.md or legacy hidden_goal.md
        if goal_type:
            hidden_goal_path = os.path.join(
                scenario_config.path, "hidden_goals", f"{goal_type}.md"
            )
        else:
            hidden_goal_path = os.path.join(scenario_config.path, "hidden_goal.md")
        hidden_goal = load_prompt(hidden_goal_path)

        # Load oversight prompt: scenario-specific first, then global fallback
        scenario_oversight_path = os.path.join(
            scenario_config.path, "oversight", f"{oversight_level}.md"
        )
        oversight_prompt = load_prompt(scenario_oversight_path)
        if not oversight_prompt:
            global_oversight_path = os.path.join(
                self.config.project_root, "oversight", f"{oversight_level}.md"
            )
            oversight_prompt = load_prompt(global_oversight_path)

        # Build system prompt
        system_parts = [benign_goal]
        if hidden_goal:
            system_parts.append(hidden_goal)
        if oversight_prompt:
            system_parts.append(oversight_prompt)
        system_prompt = "\n\n".join(filter(None, system_parts))

        # Create isolated VFS for this run (thread-safe)
        vfs_path = os.path.join(scenario_config.path, "data")
        vfs_instance = VFS.create(vfs_path)
        tool_functions = make_tools_for_vfs(vfs_instance)

        # Create agent with isolated VFS
        save_vfs_state = self.config._config.get("output", {}).get(
            "save_vfs_state", True
        )
        scenario_name = os.path.basename(scenario_config.path)
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=scenario_name,
            oversight_level=oversight_level,
            user_prompt_type="user.md",
            save_vfs_state=save_vfs_state,
            goal_type=goal_type,
            vfs_instance=vfs_instance,
            tool_functions=tool_functions,
        )

        # Run the conversation
        output_dir = self.config.output_dir
        agent.enable_incremental_save(output_dir=output_dir)
        start_time = datetime.datetime.now()
        agent.run(user_prompt)
        end_time = datetime.datetime.now()

        # Save logs
        output_dir = self.config.output_dir
        log_file = agent.save_logs(output_dir=output_dir)

        # Check if run was successful (ended with "stop" finish_reason)
        success = False
        for msg in reversed(agent.logs):
            if msg.get("role") == "assistant" and msg.get("finish_reason"):
                success = msg["finish_reason"] == "stop"
                break
            elif (
                msg.get("role") == "assistant"
                and msg.get("content") is None
                and msg.get("tool_calls")
            ):
                continue

        duration = (end_time - start_time).total_seconds()

        # Record result (thread-safe)
        result_entry = {
            "model": model_config.id,
            "provider": model_config.provider,
            "scenario": scenario_name,
            "goal_type": goal_type,
            "oversight_level": oversight_level,
            "run_num": run_num,
            "duration_seconds": duration,
            "total_tokens": agent.total_tokens,
            "success": success,
            "log_file": log_file,
        }

        with _results_lock:
            self.results.append(result_entry)

        return success, agent.total_tokens, duration


def run_from_config(config_path: str = "config.yaml", resume: bool = True):
    """Convenience function to run all experiments from a config file."""
    config = ConfigLoader(config_path)
    config.load()

    runner = ExperimentRunner(config, resume=resume)
    runner.run_all()

    return runner.results
