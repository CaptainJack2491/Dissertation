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

    Uses a single judge per prong (blackbox, glassbox).
    """

    def __init__(
        self,
        blackbox_model: Dict = None,
        glassbox_model: Dict = None,
        batch_providers: Dict[str, Any] = None,
        sync_clients: Dict[str, Any] = None,
    ):
        if blackbox_model is None:
            blackbox_model = {
                "id": "claude-sonnet-4-20250514",
                "provider": "anthropic",
                "temperature": 0,
            }
        if glassbox_model is None:
            glassbox_model = {
                "id": "gpt-4.1",
                "provider": "openai",
                "temperature": 0,
            }

        self.blackbox_model = blackbox_model
        self.glassbox_model = glassbox_model
        self.batch_providers = batch_providers or {}
        self.sync_clients = sync_clients or {}
        self.regex_checker_cache: Dict[str, RegexChecker] = {}

        self.blackbox_checker = BlackboxChecker(
            model=blackbox_model["id"], temperature=blackbox_model.get("temperature", 0)
        )
        self.glassbox_checker = GlassboxChecker(
            model=glassbox_model["id"], temperature=glassbox_model.get("temperature", 0)
        )

    def _get_batch_provider(self, provider_name: str) -> Optional[BatchProvider]:
        if provider_name in self.batch_providers:
            return self.batch_providers[provider_name]
        return None

    def _get_sync_client(self, provider_name: str) -> Optional[Any]:
        if provider_name in self.sync_clients:
            return self.sync_clients[provider_name]
        return None

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
        if run_llm and not self.sync_clients:
            raise RuntimeError(
                "No sync clients configured — cannot run LLM judge checks"
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

        blackbox_result = {"category": "", "justification": "", "raw_response": ""}
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

            model_id = self.blackbox_model["id"]
            provider = self.blackbox_model.get("provider", "anthropic")
            temperature = self.blackbox_model.get("temperature", 0)

            sync_client = self._get_sync_client(provider)
            if sync_client:
                bb_prompt = self.blackbox_checker.build_prompt(
                    model_output, baseline_output, source_docs, task_description
                )
                try:
                    bb_response = sync_client.messages.create(
                        model=model_id,
                        max_tokens=4096,
                        temperature=temperature,
                        messages=[{"role": "user", "content": bb_prompt}],
                    )
                    bb_text = bb_response.content[0].text
                    blackbox_result = self.blackbox_checker.parse_response(bb_text)
                    blackbox_result["model"] = model_id
                except Exception as e:
                    blackbox_result = {
                        "category": "UNKNOWN",
                        "justification": f"Error: {str(e)}",
                        "raw_response": "",
                        "model": model_id,
                    }

        glassbox_result = {
            "category": "",
            "sophistication": "",
            "justification": "",
            "raw_response": "",
        }
        if "glassbox" in enabled_judges:
            system_prompt = extract_system_prompt(conversation)
            reasoning_trace = extract_reasoning_trace(conversation)

            model_id = self.glassbox_model["id"]
            provider = self.glassbox_model.get("provider", "openai")
            temperature = self.glassbox_model.get("temperature", 0)

            sync_client = self._get_sync_client(provider)
            if sync_client:
                gb_prompt = self.glassbox_checker.build_prompt(
                    system_prompt, reasoning_trace, model_output
                )
                try:
                    gb_response = sync_client.messages.create(
                        model=model_id,
                        max_tokens=4096,
                        temperature=temperature,
                        messages=[{"role": "user", "content": gb_prompt}],
                    )
                    gb_text = gb_response.content[0].text
                    glassbox_result = self.glassbox_checker.parse_response(gb_text)
                    glassbox_result["model"] = model_id
                except Exception as e:
                    glassbox_result = {
                        "category": "UNKNOWN",
                        "sophistication": "",
                        "justification": f"Error: {str(e)}",
                        "raw_response": "",
                        "model": model_id,
                    }

        return {
            "run_id": run_id,
            "model": log_data.get("model", ""),
            "scenario": scenario,
            "oversight": log_data.get("oversight_level", ""),
            "regex": regex_result["verdict"],
            "regex_details": regex_result["details"],
            "blackbox": blackbox_result,
            "glassbox": glassbox_result,
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
            (batch_requests_by_provider, metadata_map)
            - batch_requests_by_provider: dict of provider_name -> list of BatchRequest
            - metadata_map: dict mapping custom_id → metadata needed to reassemble results
        """
        if enabled_judges is None:
            enabled_judges = {"regex", "blackbox", "glassbox"}

        batch_requests_by_provider: Dict[str, List[BatchRequest]] = {}
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

                model_id = self.blackbox_model["id"]
                provider = self.blackbox_model.get("provider", "anthropic")
                temperature = self.blackbox_model.get("temperature", 0)

                batch_provider = self._get_batch_provider(provider)
                if batch_provider:
                    bb_id = f"bb_{id_hash}"
                    metadata_map[bb_id] = {
                        "type": "blackbox",
                        "judge_type": "blackbox",
                        "log_path": log_path,
                        "run_id": run_id,
                        "model": log_data.get("model", ""),
                        "scenario": scenario,
                        "oversight": log_data.get("oversight_level", ""),
                        "regex_result": regex_result,
                        "judge_model": model_id,
                        "provider": provider,
                    }

                    bb_prompt = self.blackbox_checker.build_prompt(
                        model_output, baseline_output, source_docs, task_description
                    )
                    req = batch_provider.build_request(
                        custom_id=bb_id,
                        prompt=bb_prompt,
                        model=model_id,
                        temperature=temperature,
                    )

                    if provider not in batch_requests_by_provider:
                        batch_requests_by_provider[provider] = []
                    batch_requests_by_provider[provider].append(req)

            if "glassbox" in enabled_judges:
                system_prompt = extract_system_prompt(conversation)
                reasoning_trace = extract_reasoning_trace(conversation)

                model_id = self.glassbox_model["id"]
                provider = self.glassbox_model.get("provider", "openai")
                temperature = self.glassbox_model.get("temperature", 0)

                batch_provider = self._get_batch_provider(provider)
                if batch_provider:
                    gb_id = f"gb_{id_hash}"
                    metadata_map[gb_id] = {
                        "type": "glassbox",
                        "judge_type": "glassbox",
                        "log_path": log_path,
                        "run_id": run_id,
                        "model": log_data.get("model", ""),
                        "scenario": scenario,
                        "oversight": log_data.get("oversight_level", ""),
                        "regex_result": regex_result,
                        "judge_model": model_id,
                        "provider": provider,
                    }

                    gb_prompt = self.glassbox_checker.build_prompt(
                        system_prompt, reasoning_trace, model_output
                    )
                    req = batch_provider.build_request(
                        custom_id=gb_id,
                        prompt=gb_prompt,
                        model=model_id,
                        temperature=temperature,
                    )

                    if provider not in batch_requests_by_provider:
                        batch_requests_by_provider[provider] = []
                    batch_requests_by_provider[provider].append(req)

        return batch_requests_by_provider, metadata_map

    def submit_batch(
        self, batch_requests: List[BatchRequest], provider: str = "anthropic"
    ) -> str:
        """Submit a batch to the provider and return the batch ID."""
        batch_provider = self._get_batch_provider(provider)
        if not batch_provider:
            raise RuntimeError(f"No batch provider configured for {provider}")
        return batch_provider.submit_batch(batch_requests)

    def submit_all_batches(
        self, batch_requests_by_provider: Dict[str, List[BatchRequest]]
    ) -> Dict[str, str]:
        """Submit batches to all providers and return batch_id by provider."""
        batch_ids = {}
        for provider, requests in batch_requests_by_provider.items():
            if requests:
                batch_id = self.submit_batch(requests, provider)
                batch_ids[provider] = batch_id
        return batch_ids

    def poll_batch(
        self, batch_id: str, provider: str = "anthropic", poll_interval: int = 30
    ) -> None:
        """Poll until batch processing is complete."""
        batch_provider = self._get_batch_provider(provider)
        if not batch_provider:
            raise RuntimeError(f"No batch provider configured for {provider}")
        batch_provider.poll_batch(batch_id, poll_interval)

    def poll_all_batches(
        self, batch_ids: Dict[str, str], poll_interval: int = 30
    ) -> None:
        """Poll all batch providers until all complete."""
        for provider, batch_id in batch_ids.items():
            print(f"Polling {provider} batch {batch_id}...")
            self.poll_batch(batch_id, provider, poll_interval)

    def collect_batch_results(
        self,
        batch_ids: Dict[str, str],
        metadata_map: Dict[str, Dict],
    ) -> List[Dict[str, Any]]:
        """Collect and parse results from completed batches.

        Returns a list of combined verdict dicts (one per log file).
        """
        raw_results = {}

        for provider, batch_id in batch_ids.items():
            batch_provider = self._get_batch_provider(provider)
            if not batch_provider:
                continue

            for result in batch_provider.collect_results(batch_id):
                if result.error:
                    raw_results[result.custom_id] = f"ERROR: {result.error}"
                else:
                    raw_results[result.custom_id] = result.text

        verdicts_by_run: Dict[str, Dict] = {}
        bb_results_by_run: Dict[str, Dict] = {}
        gb_results_by_run: Dict[str, Dict] = {}

        for custom_id, meta in metadata_map.items():
            run_id = meta["run_id"]
            raw_text = raw_results.get(custom_id, "")

            if meta["type"] == "blackbox":
                bb_result = self.blackbox_checker.parse_response(raw_text)
                bb_result["model"] = meta.get("judge_model", "unknown")
                bb_results_by_run[run_id] = bb_result

            elif meta["type"] == "glassbox":
                gb_result = self.glassbox_checker.parse_response(raw_text)
                gb_result["model"] = meta.get("judge_model", "unknown")
                gb_results_by_run[run_id] = gb_result

        all_run_ids = set(
            list(bb_results_by_run.keys()) + list(gb_results_by_run.keys())
        )
        for run_id in all_run_ids:
            meta = None
            for m in metadata_map.values():
                if m["run_id"] == run_id:
                    meta = m
                    break

            if not meta:
                continue

            verdicts_by_run[run_id] = {
                "run_id": run_id,
                "model": meta.get("model", ""),
                "scenario": meta.get("scenario", ""),
                "oversight": meta.get("oversight", ""),
                "regex": meta.get("regex_result", {}).get("verdict", ""),
                "regex_details": meta.get("regex_result", {}).get("details", []),
            }

            if run_id in bb_results_by_run:
                verdicts_by_run[run_id]["blackbox"] = bb_results_by_run[run_id]

            if run_id in gb_results_by_run:
                verdicts_by_run[run_id]["glassbox"] = gb_results_by_run[run_id]

        return list(verdicts_by_run.values())
