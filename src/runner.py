"""
Runner - orchestrates experiment runs based on config.
Loops through models, scenarios, and oversight levels.
"""
import os
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

    def __init__(self, config: ConfigLoader, verbose: bool = False):
        self.config = config
        self.results: List[Dict] = []
        self.verbose = verbose

    def run_all(self):
        """Run all experiments defined in config."""
        print(f"\n{'='*60}")
        print("Starting Experiment Run")
        print(f"{'='*60}\n")

        total_runs = 0
        for model_config in self.config.models:
            for scenario_config in self.config.scenarios:
                for oversight_level in self.config.oversight_levels:
                    runs = self._run_combo(model_config, scenario_config, oversight_level)
                    total_runs += runs

        # Summary
        successful = sum(1 for r in self.results if r.get("success", False))
        incomplete = total_runs - successful

        print(f"\n{'='*60}")
        print(f"Experiment Complete: {total_runs} runs")
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
        print(f"\n--- Running: {model_config.id} | {scenario_name} | {oversight_level} ---")

        runs_completed = 0
        for run_num in range(1, scenario_config.runs + 1):
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
        return runs_completed

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
        oversight_prompt = load_prompt(os.path.join("oversight", f"{oversight_level}.md"))

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


def run_from_config(config_path: str = "config.yaml"):
    """Convenience function to run all experiments from a config file."""
    config = ConfigLoader(config_path)
    config.load()

    runner = ExperimentRunner(config)
    runner.run_all()

    return runner.results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run experiments from config")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    run_from_config(args.config)
