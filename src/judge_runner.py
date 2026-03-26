"""
Judge Runner - CLI to judge experiment logs using the judging pipeline.
Discovers log files, runs regex/blackbox/glassbox checks, outputs CSV.
"""

import argparse
import csv
import json
import os
import sys
import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(__file__))

import anthropic

from judge import (
    Judge,
    extract_model_output,
    extract_reasoning_trace,
    extract_system_prompt,
    AnthropicBatchProvider,
    XAIBatchProvider,
)


def discover_log_files(
    logs_dir: str, model_filter: str = None, scenario_filter: str = None
) -> List[str]:
    """Find all experiment log JSON files, skipping baselines.

    Args:
        logs_dir: Root directory containing experiment logs.
        model_filter: If set, only include logs from this model (e.g. 'moonshotai/kimi-k2.5').
        scenario_filter: If set, only include logs from this scenario.
    """
    log_files = []
    for root, dirs, files in os.walk(logs_dir):
        # Skip baseline directories
        if os.path.basename(root) == "baseline":
            continue
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                # Apply model filter
                if model_filter:
                    model_safe = model_filter.replace("/", "_")
                    if model_safe not in full_path:
                        continue
                # Apply scenario filter
                if scenario_filter:
                    if scenario_filter not in full_path:
                        continue
                log_files.append(full_path)
    return sorted(log_files)


def write_csv_row(csv_path: str, verdict: Dict, write_header: bool = False) -> None:
    """Append a single verdict row to the CSV file."""
    fieldnames = [
        "run_id",
        "model",
        "scenario",
        "oversight",
        "regex",
        "blackbox_category",
        "blackbox_justification",
        "glassbox_category",
        "glassbox_sophistication",
        "glassbox_justification",
    ]
    mode = "w" if write_header else "a"
    with open(csv_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        row = {
            "run_id": verdict.get("run_id", ""),
            "model": verdict.get("model", ""),
            "scenario": verdict.get("scenario", ""),
            "oversight": verdict.get("oversight", ""),
            "regex": verdict.get("regex", ""),
            "blackbox_category": verdict.get("blackbox", {}).get("category", ""),
            "blackbox_justification": verdict.get("blackbox", {}).get(
                "justification", ""
            ),
            "glassbox_category": verdict.get("glassbox", {}).get("category", ""),
            "glassbox_sophistication": verdict.get("glassbox", {}).get(
                "sophistication", ""
            ),
            "glassbox_justification": verdict.get("glassbox", {}).get(
                "justification", ""
            ),
        }
        writer.writerow(row)


def write_csv(csv_path: str, verdicts: List[Dict]) -> None:
    """Write all verdicts to CSV (overwrite)."""
    fieldnames = [
        "run_id",
        "model",
        "scenario",
        "oversight",
        "regex",
        "blackbox_category",
        "blackbox_justification",
        "glassbox_category",
        "glassbox_sophistication",
        "glassbox_justification",
    ]
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for verdict in verdicts:
            row = {
                "run_id": verdict.get("run_id", ""),
                "model": verdict.get("model", ""),
                "scenario": verdict.get("scenario", ""),
                "oversight": verdict.get("oversight", ""),
                "regex": verdict.get("regex", ""),
                "blackbox_category": verdict.get("blackbox", {}).get("category", ""),
                "blackbox_justification": verdict.get("blackbox", {}).get(
                    "justification", ""
                ),
                "glassbox_category": verdict.get("glassbox", {}).get("category", ""),
                "glassbox_sophistication": verdict.get("glassbox", {}).get(
                    "sophistication", ""
                ),
                "glassbox_justification": verdict.get("glassbox", {}).get(
                    "justification", ""
                ),
            }
            writer.writerow(row)


def save_judge_log(
    verdict: Dict,
    log_dir: str,
    judge_model: str = "unknown",
) -> str:
    """Save full judge log including CoT reasoning alongside the verdict.

    The blackbox and glassbox dicts contain 'raw_response' — the judge's
    full chain-of-thought reasoning. This is preserved in the log for
    auditability.
    """
    run_id = verdict.get("run_id", "unknown")
    safe_run_id = run_id.replace("/", "_").replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    log_path = os.path.join(log_dir, f"judge_{safe_run_id}_{timestamp}.json")
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    bb = verdict.get("blackbox", {})
    gb = verdict.get("glassbox", {})

    log_data = {
        "run_id": run_id,
        "judged_at": timestamp,
        "judge_model": judge_model,
        "verdict": {
            "regex": verdict.get("regex", ""),
            "regex_details": verdict.get("regex_details", []),
            "blackbox_category": bb.get("category", ""),
            "blackbox_justification": bb.get("justification", ""),
            "glassbox_category": gb.get("category", ""),
            "glassbox_sophistication": gb.get("sophistication", ""),
            "glassbox_justification": gb.get("justification", ""),
        },
        # Full judge reasoning (CoT) — the complete response from the judge LLM
        "blackbox_full_reasoning": bb.get("raw_response", ""),
        "glassbox_full_reasoning": gb.get("raw_response", ""),
    }

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    return log_path


def load_judge_config(config_path: str = "config.yaml") -> Dict:
    """Load judge configuration from config.yaml."""
    import yaml

    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}
    return config.get("judge", {})


def main():
    parser = argparse.ArgumentParser(description="Judge experiment logs")
    parser.add_argument(
        "--log-file",
        help="Path to a single experiment log JSON to judge",
    )
    parser.add_argument(
        "--logs-dir",
        default="logs",
        help="Root directory containing experiment logs (default: logs)",
    )
    parser.add_argument(
        "--scenarios-dir",
        default="scenarios",
        help="Root directory containing scenario definitions (default: scenarios)",
    )
    parser.add_argument(
        "--output",
        default="output/results.csv",
        help="Path to output CSV file (default: output/results.csv)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml (default: config.yaml)",
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "single"],
        default="batch",
        help="Processing mode: 'batch' (Anthropic Batch API) or 'single' (synchronous). Default: batch",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between batch status polls (default: 30)",
    )
    parser.add_argument(
        "--model",
        help="Filter logs to a specific model (e.g. 'moonshotai/kimi-k2.5')",
    )
    parser.add_argument(
        "--scenario",
        help="Filter logs to a specific scenario (e.g. 'child_protection')",
    )
    parser.add_argument(
        "--judges",
        nargs="+",
        choices=["regex", "blackbox", "glassbox"],
        default=["regex", "blackbox", "glassbox"],
        help="Which judges to run (default: all three). E.g. --judges regex blackbox",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "xai"],
        default="anthropic",
        help="Batch provider to use (default: anthropic)",
    )
    args = parser.parse_args()

    judge_config = load_judge_config(args.config)
    model = judge_config.get("model", "claude-sonnet-4-20250514")
    temperature = judge_config.get("temperature", 0)
    judge_log_dir = judge_config.get("log_dir", "judge_logs")

    batch_provider = None
    sync_client = None

    if args.mode == "batch":
        if args.provider == "anthropic":
            batch_provider = AnthropicBatchProvider()
            sync_client = anthropic.Anthropic()
        elif args.provider == "xai":
            batch_provider = XAIBatchProvider()
    else:
        sync_client = anthropic.Anthropic()

    judge = Judge(
        model=model,
        temperature=temperature,
        batch_provider=batch_provider,
        sync_client=sync_client,
    )

    # Determine which log files to process
    if args.log_file:
        log_files = [args.log_file]
    else:
        log_files = discover_log_files(
            args.logs_dir, model_filter=args.model, scenario_filter=args.scenario
        )

    if not log_files:
        print("No log files found to judge.")
        return

    enabled_judges = set(args.judges)
    run_llm = bool({"blackbox", "glassbox"} & enabled_judges)

    print(f"\n{'=' * 60}")
    print(f"Judging {len(log_files)} experiment log(s)")
    print(f"  Judges: {', '.join(sorted(enabled_judges))}")
    if run_llm:
        print(f"  Judge model: {model}")
        print(f"  Mode: {args.mode}")
    print(f"  Output: {args.output}")
    print(f"  Judge logs: {judge_log_dir}")
    print(f"{'=' * 60}\n")

    if not run_llm or args.mode == "single":
        # Regex-only mode or synchronous mode — judge one at a time
        verdicts = []
        for i, log_path in enumerate(log_files, 1):
            print(f"[{i}/{len(log_files)}] Judging: {log_path}")
            try:
                verdict = judge.judge_single(
                    log_path=log_path,
                    logs_dir=args.logs_dir,
                    scenarios_dir=args.scenarios_dir,
                    enabled_judges=enabled_judges,
                )
                verdicts.append(verdict)

                # Save judge log
                jlog = save_judge_log(verdict, judge_log_dir, judge_model=model)
                parts = []
                if "regex" in enabled_judges:
                    parts.append(f"regex={verdict['regex']}")
                if "blackbox" in enabled_judges:
                    parts.append(f"blackbox={verdict['blackbox']['category']}")
                if "glassbox" in enabled_judges:
                    parts.append(
                        f"glassbox={verdict['glassbox']['category']}/{verdict['glassbox']['sophistication']}"
                    )
                print(f"  → {' '.join(parts)}")
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback

                traceback.print_exc()

        # Write CSV
        write_csv(args.output, verdicts)
        print(f"\nResults saved to {args.output}")

    else:
        # Batch mode — use Anthropic Batch API
        checks_per_log = len({"blackbox", "glassbox"} & enabled_judges)
        print("Preparing batch requests...")
        batch_requests, metadata_map = judge.prepare_batch_requests(
            log_paths=log_files,
            logs_dir=args.logs_dir,
            scenarios_dir=args.scenarios_dir,
            enabled_judges=enabled_judges,
        )

        print(
            f"  {len(batch_requests)} API requests ({len(log_files)} logs × {checks_per_log} checks)"
        )

        print("Submitting batch...")
        batch_id = judge.submit_batch(batch_requests)
        print(f"  Batch ID: {batch_id}")

        print(f"Polling for completion (every {args.poll_interval}s)...")
        judge.poll_batch(batch_id, poll_interval=args.poll_interval)

        print("Collecting results...")
        verdicts = judge.collect_batch_results(batch_id, metadata_map)

        # Save individual judge logs
        for verdict in verdicts:
            jlog = save_judge_log(verdict, judge_log_dir, judge_model=model)
            bb = verdict.get("blackbox", {})
            gb = verdict.get("glassbox", {})
            parts = [f"{verdict['run_id']}:"]
            if "regex" in enabled_judges:
                parts.append(f"regex={verdict.get('regex', '?')}")
            if "blackbox" in enabled_judges:
                parts.append(f"blackbox={bb.get('category', '?')}")
            if "glassbox" in enabled_judges:
                parts.append(
                    f"glassbox={gb.get('category', '?')}/{gb.get('sophistication', '?')}"
                )
            print(f"  {' '.join(parts)}")

        # Write CSV
        write_csv(args.output, verdicts)
        print(f"\nResults saved to {args.output}")

    print(f"\n{'=' * 60}")
    print(f"Judging complete: {len(verdicts)} verdicts")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
