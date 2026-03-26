"""
Judge orchestrator - evaluates experiment logs for deceptive behaviour.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from .batch_providers import BatchProvider, BatchRequest
from .helpers import (
    extract_model_output,
    extract_reasoning_trace,
    extract_system_prompt,
)
from .judges import BlackboxChecker, GlassboxChecker, RegexChecker


class Judge:
    """Orchestrates all three checks on experiment log files.

    Supports two modes:
    - judge_single(): synchronous, one log at a time (for testing / quick runs)
    - judge_batch(): uses a BatchProvider for multiple logs
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0,
        batch_provider: Optional[BatchProvider] = None,
        sync_client: Optional[Any] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.batch_provider = batch_provider
        self.sync_client = sync_client
        self.regex_checker_cache: Dict[str, RegexChecker] = {}

        self.blackbox = BlackboxChecker(model=model, temperature=temperature)
        self.glassbox = GlassboxChecker(model=model, temperature=temperature)

    def _get_regex_checker(self, scenario_path: str) -> RegexChecker:
        """Get or create a RegexChecker for a scenario."""
        if scenario_path not in self.regex_checker_cache:
            rules_path = os.path.join(scenario_path, "regex_rules.yaml")
            self.regex_checker_cache[scenario_path] = RegexChecker(rules_path)
        return self.regex_checker_cache[scenario_path]

    @staticmethod
    def load_log(log_path: str) -> Dict[str, Any]:
        """Load an experiment log JSON file."""
        with open(log_path, "r") as f:
            return json.load(f)

    @staticmethod
    def load_baseline(log_data: Dict, logs_dir: str) -> tuple[str, Dict]:
        """Load the baseline output and baseline log data for a given experiment log."""
        model = log_data.get("model", "").replace("/", "_")
        scenario = log_data.get("scenario", "")
        baseline_path = os.path.join(logs_dir, model, scenario, "baseline.md")
        baseline_content = ""
        baseline_log_data = {}

        if os.path.exists(baseline_path):
            with open(baseline_path, "r", encoding="utf-8") as f:
                baseline_content = f.read()

        baseline_dir = os.path.join(logs_dir, model, scenario, "baseline")
        if os.path.exists(baseline_dir) and os.path.isdir(baseline_dir):
            json_files = [f for f in os.listdir(baseline_dir) if f.endswith(".json")]
            if json_files:
                latest_baseline_log = sorted(json_files)[-1]
                with open(
                    os.path.join(baseline_dir, latest_baseline_log),
                    "r",
                    encoding="utf-8",
                ) as f:
                    try:
                        baseline_log_data = json.load(f)
                    except json.JSONDecodeError:
                        pass
        return baseline_content, baseline_log_data

    @staticmethod
    def load_source_documents(log_data: Dict) -> str:
        """Load source documents from a log's final_vfs_state."""
        vfs_state = log_data.get("final_vfs_state", {})
        root_dir = vfs_state.get("/", {})
        data_files = root_dir.get("data", {})

        if not data_files:
            return "(No source documents found)"

        docs = []
        for filename, content in sorted(data_files.items()):
            if isinstance(content, str):
                docs.append(f"--- Document: {filename} ---\n{content}\n")
        return "\n".join(docs) if docs else "(No source documents found)"

    def judge_single(
        self,
        log_path: str,
        logs_dir: str = "logs",
        scenarios_dir: str = "scenarios",
        enabled_judges: Optional[set] = None,
    ) -> Dict[str, Any]:
        """Judge a single experiment log synchronously (non-batch)."""
        if enabled_judges is None:
            enabled_judges = {"regex", "blackbox", "glassbox"}

        run_llm = bool({"blackbox", "glassbox"} & enabled_judges)
        if run_llm and not self.sync_client:
            raise RuntimeError(
                "No sync client configured — cannot run LLM judge checks"
            )

        log_data = self.load_log(log_path)
        conversation = log_data.get("conversation", [])
        scenario = log_data.get("scenario", "")
        run_id = log_data.get("run_id", os.path.basename(log_path))

        model_output = extract_model_output(conversation)

        regex_result = {"verdict": "", "details": []}
        if "regex" in enabled_judges:
            scenario_path = os.path.join(scenarios_dir, scenario)
            regex_checker = self._get_regex_checker(scenario_path)
            regex_result = regex_checker.check(model_output)

        bb_result = {"category": "", "justification": "", "raw_response": ""}
        if "blackbox" in enabled_judges:
            baseline_output, baseline_log_data = self.load_baseline(log_data, logs_dir)

            if baseline_log_data:
                source_docs = self.load_source_documents(baseline_log_data)
            else:
                import sys

                print(
                    f"  [WARN] No baseline found for {scenario} — using experiment log for source docs",
                    file=sys.stderr,
                )
                source_docs = self.load_source_documents(log_data)

            if not baseline_output:
                import sys

                print(
                    f"  [WARN] No baseline output for {scenario} — blackbox judge will compare against source docs only",
                    file=sys.stderr,
                )
                baseline_output = "(No baseline available)"

            scenario_path = os.path.join(scenarios_dir, scenario)
            benign_goal_path = os.path.join(scenario_path, "benign_goal.md")
            task_description = ""
            if os.path.exists(benign_goal_path):
                with open(benign_goal_path, "r", encoding="utf-8") as f:
                    task_description = f.read().strip()

            bb_prompt = self.blackbox.build_prompt(
                model_output, baseline_output, source_docs, task_description
            )
            bb_response = self.sync_client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[{"role": "user", "content": bb_prompt}],
            )
            bb_text = bb_response.content[0].text
            bb_result = self.blackbox.parse_response(bb_text)

        gb_result = {
            "category": "",
            "sophistication": "",
            "justification": "",
            "raw_response": "",
        }
        if "glassbox" in enabled_judges:
            system_prompt = extract_system_prompt(conversation)
            reasoning_trace = extract_reasoning_trace(conversation)
            gb_prompt = self.glassbox.build_prompt(
                system_prompt, reasoning_trace, model_output
            )
            gb_response = self.sync_client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=self.temperature,
                messages=[{"role": "user", "content": gb_prompt}],
            )
            gb_text = gb_response.content[0].text
            gb_result = self.glassbox.parse_response(gb_text)

        return {
            "run_id": run_id,
            "model": log_data.get("model", ""),
            "scenario": scenario,
            "oversight": log_data.get("oversight_level", ""),
            "regex": regex_result["verdict"],
            "regex_details": regex_result["details"],
            "blackbox": bb_result,
            "glassbox": gb_result,
        }

    def prepare_batch_requests(
        self,
        log_paths: List[str],
        logs_dir: str = "logs",
        scenarios_dir: str = "scenarios",
        enabled_judges: Optional[set] = None,
    ) -> tuple:
        """Prepare batch requests for multiple log files.

        Returns:
            (batch_requests, metadata_map)
            - batch_requests: list of BatchRequest for the batch provider
            - metadata_map: dict mapping custom_id → metadata needed to reassemble results
        """
        if enabled_judges is None:
            enabled_judges = {"regex", "blackbox", "glassbox"}

        batch_requests: List[BatchRequest] = []
        metadata_map: Dict[str, Dict] = {}

        for log_path in log_paths:
            log_data = self.load_log(log_path)
            conversation = log_data.get("conversation", [])
            scenario = log_data.get("scenario", "")
            run_id = log_data.get("run_id", os.path.basename(log_path))

            model_output = extract_model_output(conversation)

            regex_result = {"verdict": "", "details": []}
            if "regex" in enabled_judges:
                scenario_path = os.path.join(scenarios_dir, scenario)
                regex_checker = self._get_regex_checker(scenario_path)
                regex_result = regex_checker.check(model_output)

            id_hash = hashlib.sha256(run_id.encode()).hexdigest()[:8]
            idx = (
                len(batch_requests) // 2
                if len(enabled_judges & {"blackbox", "glassbox"}) == 2
                else len(batch_requests)
            )

            if "blackbox" in enabled_judges:
                baseline_output, baseline_log_data = self.load_baseline(
                    log_data, logs_dir
                )

                if baseline_log_data:
                    source_docs = self.load_source_documents(baseline_log_data)
                else:
                    import sys

                    print(
                        f"  [WARN] No baseline found for {scenario} — using experiment log for source docs",
                        file=sys.stderr,
                    )
                    source_docs = self.load_source_documents(log_data)

                if not baseline_output:
                    baseline_output = "(No baseline available)"

                scenario_path = os.path.join(scenarios_dir, scenario)
                benign_goal_path = os.path.join(scenario_path, "benign_goal.md")
                task_description = ""
                if os.path.exists(benign_goal_path):
                    with open(benign_goal_path, "r", encoding="utf-8") as f:
                        task_description = f.read().strip()

                bb_id = f"bb_{idx:03d}_{id_hash}"
                metadata_map[bb_id] = {
                    "type": "blackbox",
                    "log_path": log_path,
                    "run_id": run_id,
                    "model": log_data.get("model", ""),
                    "scenario": scenario,
                    "oversight": log_data.get("oversight_level", ""),
                    "regex_result": regex_result,
                }

                bb_prompt = self.blackbox.build_prompt(
                    model_output, baseline_output, source_docs, task_description
                )
                batch_requests.append(
                    self.batch_provider.build_request(
                        custom_id=bb_id,
                        prompt=bb_prompt,
                        model=self.model,
                        temperature=self.temperature,
                    )
                )

            if "glassbox" in enabled_judges:
                system_prompt = extract_system_prompt(conversation)
                reasoning_trace = extract_reasoning_trace(conversation)

                gb_id = f"gb_{idx:03d}_{id_hash}"
                metadata_map[gb_id] = {
                    "type": "glassbox",
                    "log_path": log_path,
                    "run_id": run_id,
                }
                if "blackbox" not in enabled_judges:
                    metadata_map[gb_id]["model"] = log_data.get("model", "")
                    metadata_map[gb_id]["scenario"] = scenario
                    metadata_map[gb_id]["oversight"] = log_data.get(
                        "oversight_level", ""
                    )
                    metadata_map[gb_id]["regex_result"] = regex_result

                gb_prompt = self.glassbox.build_prompt(
                    system_prompt, reasoning_trace, model_output
                )
                batch_requests.append(
                    self.batch_provider.build_request(
                        custom_id=gb_id,
                        prompt=gb_prompt,
                        model=self.model,
                        temperature=self.temperature,
                    )
                )

        return batch_requests, metadata_map

    def submit_batch(self, batch_requests: List[BatchRequest]) -> str:
        """Submit a batch to the provider and return the batch ID."""
        if not self.batch_provider:
            raise RuntimeError("No batch provider configured — cannot submit batch")
        return self.batch_provider.submit_batch(batch_requests)

    def poll_batch(self, batch_id: str, poll_interval: int = 30) -> None:
        """Poll until batch processing is complete."""
        if not self.batch_provider:
            raise RuntimeError("No batch provider configured")
        self.batch_provider.poll_batch(batch_id, poll_interval)

    def collect_batch_results(
        self,
        batch_id: str,
        metadata_map: Dict[str, Dict],
    ) -> List[Dict[str, Any]]:
        """Collect and parse results from a completed batch.

        Returns a list of combined verdict dicts (one per log file).
        """
        if not self.batch_provider:
            raise RuntimeError("No batch provider configured")

        raw_results = {}
        for result in self.batch_provider.collect_results(batch_id):
            if result.error:
                raw_results[result.custom_id] = f"ERROR: {result.error}"
            else:
                raw_results[result.custom_id] = result.text

        verdicts_by_run = {}
        for custom_id, meta in metadata_map.items():
            run_id = meta["run_id"]
            raw_text = raw_results.get(custom_id, "")

            if meta["type"] == "blackbox":
                bb_result = self.blackbox.parse_response(raw_text)
                if run_id not in verdicts_by_run:
                    verdicts_by_run[run_id] = {
                        "run_id": run_id,
                        "model": meta["model"],
                        "scenario": meta["scenario"],
                        "oversight": meta["oversight"],
                        "regex": meta["regex_result"]["verdict"],
                        "regex_details": meta["regex_result"]["details"],
                    }
                verdicts_by_run[run_id]["blackbox"] = bb_result

            elif meta["type"] == "glassbox":
                gb_result = self.glassbox.parse_response(raw_text)
                if run_id not in verdicts_by_run:
                    verdicts_by_run[run_id] = {"run_id": run_id}
                verdicts_by_run[run_id]["glassbox"] = gb_result

        return list(verdicts_by_run.values())
