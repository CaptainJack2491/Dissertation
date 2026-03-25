"""
Runner - orchestrates experiment runs based on config.
Loops through models, scenarios, goal types, and oversight levels.
Supports parallel execution via ThreadPoolExecutor.
"""
import os
import glob
import concurrent.futures
from typing import List, Dict, Any, Tuple
from config_loader import ConfigLoader, ProviderConfig, ModelConfig, ScenarioConfig
from vfs import VFS
from agent import Agent
from tools import make_tools_for_vfs, tools as tool_schemas
from logger import get_logger
import datetime
import threading

# Get logger instance
logger = get_logger("experiment")

# Thread-safe lock for results list
_results_lock = threading.Lock()


def load_prompt(file_path: str) -> str:
    """Load a prompt file."""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r') as f:
        return f.read().strip()


class ExperimentRunner:
    """Runs experiments based on configuration."""

    def __init__(self, config: ConfigLoader, verbose: bool = False, resume: bool = True):
        self.config = config
        self.results: List[Dict] = []
        self.verbose = verbose
        self.resume = resume

    def run_all(self):
        """Run all experiments defined in config."""
        logger.info(f"\n{'='*60}")
        logger.info("Starting Experiment Run")
        logger.info(f"{'='*60}\n")

        # Build list of all work items (model, scenario, goal_type, oversight)
        work_items = self._build_work_items()

        if not work_items:
            logger.warning("No work items to run.")
            return

        max_workers = self.config.max_workers
        total_items = len(work_items)
        logger.info(f"Total work items: {total_items}, Max workers: {max_workers}")

        if max_workers <= 1:
            # Sequential execution (original behavior)
            for item in work_items:
                self._execute_work_item(item)
        else:
            # Parallel execution
            logger.info(f"Running with {max_workers} parallel workers")
            from tqdm import tqdm
            from tqdm.contrib.logging import logging_redirect_tqdm
            import logging
            
            # Reduce console spam during parallel runs to keep the progress bar clean
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    # Keep console relatively quiet (WARNING/ERROR/CRITICAL)
                    handler.setLevel(logging.WARNING)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._execute_work_item, item): item
                    for item in work_items
                }
                with logging_redirect_tqdm():
                    with tqdm(total=total_items, desc="Running Experiments", unit="run", dynamic_ncols=True) as pbar:
                        for future in concurrent.futures.as_completed(futures):
                            item = futures[future]
                            try:
                                future.result()
                            except Exception as e:
                                logger.critical(f"Work item failed: {item.get('label', 'unknown')}: {e}")
                                pbar.write(f"ERROR: {item.get('label', 'unknown')} failed: {e}")
                            pbar.update(1)

        # Summary
        successful = sum(1 for r in self.results if r.get("success", False))
        total_runs = len(self.results)

        logger.info(f"\n{'='*60}")
        logger.info(f"Experiment Complete: {total_runs} runs completed")
        logger.info(f"  SUCCESS: {successful}")
        logger.info(f"  INCOMPLETE: {total_runs - successful}")
        logger.info(f"{'='*60}\n")

    def _build_work_items(self) -> List[Dict[str, Any]]:
        """Build a flat list of all (model, scenario, goal_type, oversight, run_num) combos."""
        work_items = []
        goal_types = self.config.goal_types

        for model_config in self.config.models:
            for scenario_config in self.config.scenarios:
                # Determine oversight levels
                available = scenario_config.oversight_levels or self.config.oversight_levels
                global_filter = self.config.oversight_levels
                oversight_levels = [lvl for lvl in available if lvl in global_filter]
                if not oversight_levels:
                    logger.warning(f"No matching oversight levels for {scenario_config.path}.")
                    continue

                # Ensure baseline exists
                self._ensure_baseline(model_config, scenario_config)

                for oversight_level in oversight_levels:
                    if goal_types:
                        # New: iterate over goal types
                        for goal_type in goal_types:
                            items = self._build_run_items(
                                model_config, scenario_config, oversight_level, goal_type
                            )
                            work_items.extend(items)
                    else:
                        # Legacy: single hidden_goal.md (no goal_types in config)
                        items = self._build_run_items(
                            model_config, scenario_config, oversight_level, ""
                        )
                        work_items.extend(items)

        return work_items

    def _build_run_items(
        self,
        model_config: ModelConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str,
        goal_type: str
    ) -> List[Dict[str, Any]]:
        """Build individual run items for a specific combo, accounting for resume."""
        model_name_safe = model_config.id.replace("/", "_")
        scenario_name = os.path.basename(scenario_config.path)
        output_dir = self.config.output_dir

        # Build log directory path
        if goal_type:
            log_dir = os.path.join(output_dir, model_name_safe, scenario_name,
                                   goal_type, oversight_level)
        else:
            log_dir = os.path.join(output_dir, model_name_safe, scenario_name,
                                   oversight_level)

        # Check existing runs for resume
        existing_runs = 0
        if self.resume and os.path.isdir(log_dir):
            all_json = glob.glob(os.path.join(log_dir, "*.json"))
            existing_runs = len([f for f in all_json if not f.endswith(".partial.json")])

        if existing_runs >= scenario_config.runs:
            goal_label = f"/{goal_type}" if goal_type else ""
            logger.info(f"  SKIP: {model_config.id} | {scenario_name}{goal_label} | "
                       f"{oversight_level} ({existing_runs}/{scenario_config.runs} exist)")
            return []
        elif existing_runs > 0:
            goal_label = f"/{goal_type}" if goal_type else ""
            logger.info(f"  RESUME: {model_config.id} | {scenario_name}{goal_label} | "
                       f"{oversight_level} ({existing_runs}/{scenario_config.runs} exist)")

        items = []
        for run_num in range(existing_runs + 1, scenario_config.runs + 1):
            goal_label = f"/{goal_type}" if goal_type else ""
            items.append({
                "model_config": model_config,
                "scenario_config": scenario_config,
                "oversight_level": oversight_level,
                "goal_type": goal_type,
                "run_num": run_num,
                "label": f"{model_config.id} | {scenario_name}{goal_label} | {oversight_level} | run {run_num}"
            })

        return items

    def _ensure_baseline(self, model_config: ModelConfig, scenario_config: ScenarioConfig):
        """Ensure baseline exists for a model+scenario combo (thread-safe)."""
        scenario_name = os.path.basename(scenario_config.path)
        model_name_safe = model_config.id.replace("/", "_")
        output_dir = self.config.output_dir
        baseline_path = os.path.join(output_dir, model_name_safe, scenario_name, "baseline.md")

        if not self.config.generate_baseline:
            if not os.path.exists(baseline_path):
                logger.warning(f"Baseline generation DISABLED. No baseline for "
                              f"{model_config.id} | {scenario_name}.")
            return

        if not os.path.exists(baseline_path):
            logger.info(f"\n--- Generating baseline: {model_config.id} | {scenario_name} ---")
            provider_config = self.config.get_provider(model_config.provider)
            self._run_baseline(model_config, provider_config, scenario_config)
            logger.info(f"  Baseline saved to {baseline_path}")

    def _execute_work_item(self, item: Dict[str, Any]):
        """Execute a single work item (one experiment run). Thread-safe."""
        try:
            self._run_single(
                model_config=item["model_config"],
                provider_config=self.config.get_provider(item["model_config"].provider),
                scenario_config=item["scenario_config"],
                oversight_level=item["oversight_level"],
                goal_type=item["goal_type"],
                run_num=item["run_num"]
            )
        except Exception as e:
            logger.critical(f"ERROR in {item['label']}: {e}")
            import traceback
            traceback.print_exc()

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
        scenario_config: ScenarioConfig
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
        save_vfs_state = self.config._config.get('output', {}).get('save_vfs_state', True)
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=scenario_name,
            oversight_level="baseline",
            user_prompt_type="user.md",
            save_vfs_state=save_vfs_state,
            vfs_instance=vfs_instance,
            tool_functions=tool_functions
        )

        # Run the conversation
        logger.info(f"  Running baseline...")
        output_dir = self.config.output_dir
        agent.enable_incremental_save(output_dir=output_dir)
        start_time = datetime.datetime.now()
        result = agent.run(user_prompt)
        end_time = datetime.datetime.now()

        # Extract baseline content from last create_file tool call
        baseline_content = self._extract_baseline_content(agent.logs)

        # Save baseline to logs/{model}/{scenario}/baseline.md
        model_name_safe = model_name.replace("/", "_")
        output_dir = self.config.output_dir
        baseline_dir = os.path.join(output_dir, model_name_safe, scenario_name)
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_path = os.path.join(baseline_dir, "baseline.md")

        with open(baseline_path, 'w') as f:
            f.write(baseline_content)

        # Save baseline log separately
        agent.save_logs(output_dir=output_dir)

        logger.info(f"  Baseline completed in {(end_time - start_time).total_seconds():.2f}s")

    def _run_single(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str,
        run_num: int,
        goal_type: str = ""
    ):
        """Run a single experiment. Thread-safe with isolated VFS."""
        # Load scenario prompts
        benign_goal = load_prompt(os.path.join(scenario_config.path, "benign_goal.md"))
        user_prompt = load_prompt(os.path.join(scenario_config.path, "user.md"))

        # Load hidden goal: from hidden_goals/{goal_type}.md or legacy hidden_goal.md
        if goal_type:
            hidden_goal_path = os.path.join(scenario_config.path, "hidden_goals", f"{goal_type}.md")
        else:
            hidden_goal_path = os.path.join(scenario_config.path, "hidden_goal.md")
        hidden_goal = load_prompt(hidden_goal_path)

        # Load oversight prompt: scenario-specific first, then global fallback
        scenario_oversight_path = os.path.join(scenario_config.path, "oversight", f"{oversight_level}.md")
        oversight_prompt = load_prompt(scenario_oversight_path)
        if not oversight_prompt:
            global_oversight_path = os.path.join(self.config.project_root, "oversight", f"{oversight_level}.md")
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

        # Log VFS info
        vfs_files = vfs_instance.list_files("/")
        logger.debug(f"VFS initialized from: {vfs_path}")
        logger.debug(f"VFS files: {vfs_files}")

        # Create agent with isolated VFS
        save_vfs_state = self.config._config.get('output', {}).get('save_vfs_state', True)
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
            tool_functions=tool_functions
        )

        # Run the conversation
        goal_label = f" | {goal_type}" if goal_type else ""
        logger.info(f"\n  Starting: {model_config.id} | {scenario_name}{goal_label} | "
                    f"{oversight_level} | run {run_num}")
        output_dir = self.config.output_dir
        agent.enable_incremental_save(output_dir=output_dir)
        start_time = datetime.datetime.now()
        result = agent.run(user_prompt)
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
            elif msg.get("role") == "assistant" and msg.get("content") is None and msg.get("tool_calls"):
                continue

        # Record result (thread-safe)
        result_entry = {
            "model": model_config.id,
            "provider": model_config.provider,
            "scenario": scenario_name,
            "goal_type": goal_type,
            "oversight_level": oversight_level,
            "run_num": run_num,
            "run_id": f"{model_config.id}/{scenario_name}/{goal_type}/{oversight_level}/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "duration_seconds": (end_time - start_time).total_seconds(),
            "total_tokens": agent.total_tokens,
            "success": success,
            "log_file": log_file
        }

        with _results_lock:
            self.results.append(result_entry)

        status = "SUCCESS" if success else "INCOMPLETE"
        logger.info(f"  [{status}] {model_config.id} | {scenario_name}{goal_label} | "
                    f"{oversight_level} | run {run_num} ({(end_time - start_time).total_seconds():.2f}s)")


def run_from_config(config_path: str = "config.yaml", resume: bool = True):
    """Convenience function to run all experiments from a config file."""
    config = ConfigLoader(config_path)
    config.load()

    runner = ExperimentRunner(config, resume=resume)
    runner.run_all()

    return runner.results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run experiments from config")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--no-resume", dest="resume", action="store_false",
                        default=True, help="Ignore existing logs and start fresh")
    args = parser.parse_args()

    run_from_config(args.config, resume=args.resume)
