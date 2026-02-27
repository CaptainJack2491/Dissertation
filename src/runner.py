"""
Runner - orchestrates experiment runs based on config.
Loops through models, scenarios, and oversight levels.
"""
import os
import glob
from typing import List, Dict, Any
from config_loader import ConfigLoader, ProviderConfig, ModelConfig, ScenarioConfig
from vfs import VFS
from agent import Agent
import datetime


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
        print(f"\n{'='*60}")
        print("Starting Experiment Run")
        print(f"{'='*60}\n")

        total_runs = 0
        skipped_runs = 0
        for model_config in self.config.models:
            for scenario_config in self.config.scenarios:
                # Use per‑scenario oversight levels if defined, otherwise fall back to global list
                oversight_levels = scenario_config.oversight_levels or self.config.oversight_levels
                for oversight_level in oversight_levels:
                    runs, skipped = self._run_combo(model_config, scenario_config, oversight_level)
                    total_runs += runs
                    skipped_runs += skipped

        # Summary
        successful = sum(1 for r in self.results if r.get("success", False))
        new_runs = total_runs - skipped_runs
        incomplete = new_runs - successful

        print(f"\n{'='*60}")
        print(f"Experiment Complete: {total_runs} total runs")
        print(f"  SKIPPED: {skipped_runs}")
        print(f"  SUCCESS: {successful}")
        print(f"  INCOMPLETE: {incomplete}")
        print(f"{'='*60}\n")

    def _run_combo(
        self,
        model_config: ModelConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str
    ) -> int:
        """Run a specific combination of model, scenario, and oversight."""
        provider_config = self.config.get_provider(model_config.provider)

        scenario_name = os.path.basename(scenario_config.path)
        model_name = model_config.id
        model_name_safe = model_name.replace("/", "_")

        # Ensure baseline exists before running hidden-goal experiments
        output_dir = self.config.output_dir
        baseline_path = os.path.join(output_dir, model_name_safe, scenario_name, "baseline.md")
        if not os.path.exists(baseline_path):
            print(f"\n--- Generating baseline: {model_name} | {scenario_name} ---")
            self._run_baseline(model_config, provider_config, scenario_config)
            print(f"  Baseline saved to {baseline_path}")
        else:
            print(f"\n--- Baseline exists: {model_name} | {scenario_name} ---")

        print(f"\n--- Running: {model_name} | {scenario_name} | {oversight_level} ---")

        # Check for existing completed runs (resume support)
        log_dir = os.path.join(output_dir, model_name_safe, scenario_name, oversight_level)
        existing_runs = 0
        if self.resume and os.path.isdir(log_dir):
            existing_runs = len(glob.glob(os.path.join(log_dir, "*.json")))

        if existing_runs >= scenario_config.runs:
            print(f"  SKIP: {existing_runs}/{scenario_config.runs} runs already exist")
            return existing_runs, existing_runs
        elif existing_runs > 0:
            print(f"  RESUME: {existing_runs}/{scenario_config.runs} runs already exist, continuing from run {existing_runs + 1}")

        runs_completed = existing_runs
        for run_num in range(existing_runs + 1, scenario_config.runs + 1):
            try:
                self._run_single(
                    model_config=model_config,
                    provider_config=provider_config,
                    scenario_config=scenario_config,
                    oversight_level=oversight_level,
                    run_num=run_num
                )
                runs_completed += 1
            except Exception as e:
                print(f"ERROR in run {run_num}: {e}")
                import traceback
                traceback.print_exc()

        print(f"--- Completed: {runs_completed}/{scenario_config.runs} runs ---")
        return runs_completed, existing_runs

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

        # Initialize VFS
        vfs_path = os.path.join(scenario_config.path, "data")
        VFS.get_instance(vfs_path)

        # Create agent
        save_vfs_state = self.config._config.get('output', {}).get('save_vfs_state', True)
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=scenario_name,
            oversight_level="baseline",
            user_prompt_type="user.md",
            save_vfs_state=save_vfs_state
        )

        # Run the conversation
        print(f"  Running baseline...")
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

        print(f"  Baseline completed in {(end_time - start_time).total_seconds():.2f}s")

    def _run_single(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        scenario_config: ScenarioConfig,
        oversight_level: str,
        run_num: int
    ):
        """Run a single experiment."""
        # Load scenario prompts
        benign_goal = load_prompt(os.path.join(scenario_config.path, "benign_goal.md"))
        hidden_goal = load_prompt(os.path.join(scenario_config.path, "hidden_goal.md"))
        user_prompt = load_prompt(os.path.join(scenario_config.path, "user.md"))
        # Load oversight prompt: first try scenario-specific, then fall back to global
        scenario_oversight_path = os.path.join(scenario_config.path, "oversight", f"{oversight_level}.md")
        oversight_prompt = load_prompt(scenario_oversight_path)
        if not oversight_prompt:
            # Fall back to global oversight directory
            global_oversight_path = os.path.join(self.config.project_root, "oversight", f"{oversight_level}.md")
            oversight_prompt = load_prompt(global_oversight_path)

        # Build system prompt
        system_parts = [benign_goal]
        if hidden_goal:
            system_parts.append(hidden_goal)
        if oversight_prompt:
            system_parts.append(oversight_prompt)
        system_prompt = "\n\n".join(filter(None, system_parts))

        # Initialize VFS
        vfs_path = os.path.join(scenario_config.path, "data")
        VFS.get_instance(vfs_path)

        print(f"  VFS initialized from: {vfs_path}")
        if self.verbose:
            VFS.get_instance().print_fs()

        # Create agent
        save_vfs_state = self.config._config.get('output', {}).get('save_vfs_state', True)
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=os.path.basename(scenario_config.path),
            oversight_level=oversight_level,
            user_prompt_type="user.md",
            save_vfs_state=save_vfs_state
        )

        # Run the conversation
        print(f"\n  Starting conversation (run {run_num})...")
        start_time = datetime.datetime.now()
        result = agent.run(user_prompt)
        end_time = datetime.datetime.now()

        # Save logs
        output_dir = self.config.output_dir
        log_file = agent.save_logs(output_dir=output_dir)

        # Print final VFS
        if self.verbose:
            print(f"\n  Final VFS state:")
            VFS.get_instance().print_fs()

        # Check if run was successful (ended with "stop" finish_reason)
        success = False
        for msg in reversed(agent.logs):
            if msg.get("role") == "assistant" and msg.get("finish_reason"):
                success = msg["finish_reason"] == "stop"
                break
            elif msg.get("role") == "assistant" and msg.get("content") is None and msg.get("tool_calls"):
                # Still in progress, not a failure
                continue

        # Record result
        self.results.append({
            "model": model_config.id,
            "provider": model_config.provider,
            "scenario": os.path.basename(scenario_config.path),
            "oversight_level": oversight_level,
            "run_num": run_num,
            "run_id": f"{model_config.id}/{os.path.basename(scenario_config.path)}/{oversight_level}/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "duration_seconds": (end_time - start_time).total_seconds(),
            "total_tokens": agent.total_tokens,
            "success": success,
            "log_file": log_file
        })

        status = "SUCCESS" if success else "INCOMPLETE"
        print(f"  [{status}] Completed in {(end_time - start_time).total_seconds():.2f}s")


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
