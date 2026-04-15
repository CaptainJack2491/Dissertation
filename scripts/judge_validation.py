"""
Judge Validation Tool - Find cheap proxy judges using inter-rate reliability.

Workflow:
    1. Run gold standard (expensive model) on subset in batch mode
    2. Run candidate cheap models on same subset in batch mode
    3. Compare each model against gold standard using Cohen's Kappa
    4. Report which models meet the Kappa threshold (k > 0.6)

Usage:
    python scripts/judge_validation.py --logs-dir logs/v2_study1_subset --output results.csv

Configuration:
    Edit GOLD_STANDARD and CANDIDATE_MODELS at the top of this file.
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.judge import Judge
from src.judge.batch_providers import AnthropicBatchProvider, OpenAIBatchProvider, XAIBatchProvider

# =============================================================================
# CONFIGURATION - Edit these
# =============================================================================

GOLD_STANDARD = {
    "blackbox": {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "temperature": 0,
    },
    "glassbox": {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "temperature": 0,
    },
}

CANDIDATE_MODELS = [
    {
        "name": "gpt-4.1",
        "blackbox": {"id": "gpt-4.1", "provider": "openai", "temperature": 0},
        "glassbox": {"id": "gpt-4.1", "provider": "openai", "temperature": 0},
    },
    {
        "name": "gpt-4.1-mini",
        "blackbox": {"id": "gpt-4.1-mini", "provider": "openai", "temperature": 0},
        "glassbox": {"id": "gpt-4.1-mini", "provider": "openai", "temperature": 0},
    },
    # {
    #     "name": "claude-haiku-4-5",
    #     "blackbox": {
    #         "id": "claude-haiku-4-5",
    #         "provider": "anthropic",
    #         "temperature": 0,
    #     },
    #     "glassbox": {
    #         "id": "claude-haiku-4-5",
    #         "provider": "anthropic",
    #         "temperature": 0,
    #     },
    # },
    {
        "name": "grok-4-1-fast-reasoning",
        "blackbox": {
            "id": "grok-4-1-fast-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
        "glassbox": {
            "id": "grok-4-1-fast-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
    },
    {
        "name": "grok-4.20-reasoning",
        "blackbox": {
            "id": "grok-4.20-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
        "glassbox": {
            "id": "grok-4.20-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
    },
    {
        "name": "grok-4.20-non-reasoning",
        "blackbox": {
            "id": "grok-4.20-non-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
        "glassbox": {
            "id": "grok-4.20-non-reasoning",
            "provider": "xai",
            "temperature": 0,
        },
    },
]

KAPPA_THRESHOLD = 0.6

# =============================================================================

PROVIDER_BATCH_CLASSES = {
    "anthropic": AnthropicBatchProvider,
    "openai": OpenAIBatchProvider,
    "xai": XAIBatchProvider,
}


def discover_logs(logs_dir: str) -> list[str]:
    """Discover all run JSON files in a logs directory."""
    logs = []
    for root, dirs, files in os.walk(logs_dir):
        if os.path.basename(root) == "baseline":
            continue
        for f in files:
            if f.endswith(".json") and not f.startswith("_"):
                logs.append(os.path.join(root, f))
    return sorted(logs)


def run_batch_judgment(
    logs_dir: str,
    scenarios_dir: str,
    model_config: dict,
    output_path: str,
) -> None:
    """Run batch judgment with the given model config and save to CSV."""
    print(f"\n  Running: {model_config['name']}")

    batch_providers = {}
    for prong in ["blackbox", "glassbox"]:
        provider = model_config[prong]["provider"]
        if provider in PROVIDER_BATCH_CLASSES and provider not in batch_providers:
            batch_providers[provider] = PROVIDER_BATCH_CLASSES[provider]()

    judge = Judge(
        blackbox_model=model_config["blackbox"],
        glassbox_model=model_config["glassbox"],
        batch_providers=batch_providers,
    )

    log_files = discover_logs(logs_dir)
    print(f"  Found {len(log_files)} logs")

    batch_requests_by_provider, metadata_map = judge.prepare_batch_requests(
        log_paths=log_files,
        logs_dir=logs_dir,
        scenarios_dir=scenarios_dir,
        enabled_judges={"regex", "blackbox", "glassbox"},
    )

    total_requests = sum(len(reqs) for reqs in batch_requests_by_provider.values())
    print(f"  {total_requests} API requests to submit")

    batch_ids = judge.submit_all_batches(batch_requests_by_provider)
    for provider, batch_id in batch_ids.items():
        print(f"  {provider} batch: {batch_id}")

    print(f"  Waiting for completion...")
    judge.poll_all_batches(batch_ids)

    verdicts = judge.collect_batch_results(batch_ids, metadata_map)

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

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in verdicts:
            row = {
                "run_id": v.get("run_id", ""),
                "model": v.get("model", ""),
                "scenario": v.get("scenario", ""),
                "oversight": v.get("oversight", ""),
                "regex": v.get("regex", ""),
                "blackbox_category": v.get("blackbox", {}).get("category", ""),
                "blackbox_justification": v.get("blackbox", {}).get(
                    "justification", ""
                ),
                "glassbox_category": v.get("glassbox", {}).get("category", ""),
                "glassbox_sophistication": v.get("glassbox", {}).get(
                    "sophistication", ""
                ),
                "glassbox_justification": v.get("glassbox", {}).get(
                    "justification", ""
                ),
            }
            writer.writerow(row)

    print(f"  Saved {len(verdicts)} verdicts to {output_path}")


def compute_kappa(cats1: list[str], cats2: list[str]) -> float | None:
    """Compute Cohen's Kappa between two raters' category assignments."""
    from sklearn.metrics import cohen_kappa_score

    valid = [(c1, c2) for c1, c2 in zip(cats1, cats2) if c1 and c2]
    if len(valid) < 3:
        return None

    c1, c2 = zip(*valid)
    try:
        return cohen_kappa_score(c1, c2)
    except Exception:
        return None


def compare_to_goldstandard(
    gold_csv: str,
    candidate_csv: str,
    candidate_name: str,
) -> dict:
    """Compare candidate CSV to gold standard CSV."""
    gold_verdicts = {}
    with open(gold_csv, newline="") as f:
        for row in csv.DictReader(f):
            gold_verdicts[row["run_id"]] = row

    cand_verdicts = {}
    with open(candidate_csv, newline="") as f:
        for row in csv.DictReader(f):
            cand_verdicts[row["run_id"]] = row

    run_ids = sorted(set(gold_verdicts.keys()) & set(cand_verdicts.keys()))

    bb_cats_gold = [gold_verdicts[rid]["blackbox_category"] for rid in run_ids]
    bb_cats_cand = [cand_verdicts[rid]["blackbox_category"] for rid in run_ids]

    gb_cats_gold = [gold_verdicts[rid]["glassbox_category"] for rid in run_ids]
    gb_cats_cand = [cand_verdicts[rid]["glassbox_category"] for rid in run_ids]

    soph_gold = [gold_verdicts[rid]["glassbox_sophistication"] for rid in run_ids]
    soph_cand = [cand_verdicts[rid]["glassbox_sophistication"] for rid in run_ids]

    return {
        "name": candidate_name,
        "n": len(run_ids),
        "blackbox_kappa": compute_kappa(bb_cats_gold, bb_cats_cand),
        "glassbox_kappa": compute_kappa(gb_cats_gold, gb_cats_cand),
        "sophistication_kappa": compute_kappa(soph_gold, soph_cand),
    }


def main():
    parser = argparse.ArgumentParser(description="Judge Validation Tool")
    parser.add_argument(
        "--logs-dir",
        required=True,
        help="Directory containing experiment logs (subset)",
    )
    parser.add_argument(
        "--scenarios-dir",
        default="scenarios",
        help="Directory containing scenario definitions",
    )
    parser.add_argument(
        "--output-dir",
        default="judge_validation",
        help="Output directory for results CSVs",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    gold_name = f"gold_{GOLD_STANDARD['blackbox']['id']}"
    gold_csv = os.path.join(args.output_dir, f"{gold_name}.csv")

    if not os.path.exists(gold_csv):
        print(f"\n{'=' * 60}")
        print("STEP 1: Running gold standard")
        print(f"{'=' * 60}")
        run_batch_judgment(
            args.logs_dir,
            args.scenarios_dir,
            {"name": gold_name, **GOLD_STANDARD},
            gold_csv,
        )
    else:
        print(f"\nGold standard already exists: {gold_csv}")

    print(f"\n{'=' * 60}")
    print("STEP 2: Running candidate models")
    print(f"{'=' * 60}")

    results = []
    for model in CANDIDATE_MODELS:
        name = model["name"]
        csv_path = os.path.join(args.output_dir, f"{name}.csv")

        if os.path.exists(csv_path):
            print(f"\n  Skipping {name} (already exists)")
            candidate_result = compare_to_goldstandard(gold_csv, csv_path, name)
        else:
            print(f"\n{'=' * 60}")
            print(f"  Running: {name}")
            print(f"{'=' * 60}")
            run_batch_judgment(
                args.logs_dir,
                args.scenarios_dir,
                model,
                csv_path,
            )
            candidate_result = compare_to_goldstandard(gold_csv, csv_path, name)

        results.append(candidate_result)

        bb_k = (
            f"{candidate_result['blackbox_kappa']:.3f}"
            if candidate_result["blackbox_kappa"]
            else "N/A"
        )
        gb_k = (
            f"{candidate_result['glassbox_kappa']:.3f}"
            if candidate_result["glassbox_kappa"]
            else "N/A"
        )
        sp_k = (
            f"{candidate_result['sophistication_kappa']:.3f}"
            if candidate_result["sophistication_kappa"]
            else "N/A"
        )

        bb_pass = (
            candidate_result["blackbox_kappa"]
            and candidate_result["blackbox_kappa"] > KAPPA_THRESHOLD
        )
        gb_pass = (
            candidate_result["glassbox_kappa"]
            and candidate_result["glassbox_kappa"] > KAPPA_THRESHOLD
        )

        print(f"\n  {name}:")
        print(f"    Blackbox Kappa:     {bb_k} {'✓' if bb_pass else '✗'}")
        print(f"    Glassbox Kappa:     {gb_k} {'✓' if gb_pass else '✗'}")
        print(f"    Sophistication Kappa:{sp_k}")

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Model':<30} {'BB κ':>8} {'GB κ':>8} {'Sph κ':>8} {'Pass':>6}")
    print("-" * 60)

    for r in results:
        bb = r["blackbox_kappa"]
        gb = r["glassbox_kappa"]
        bb_str = f"{bb:.3f}" if bb else "N/A"
        gb_str = f"{gb:.3f}" if gb else "N/A"
        sp_str = (
            f"{r['sophistication_kappa']:.3f}" if r["sophistication_kappa"] else "N/A"
        )
        pass_str = (
            "YES"
            if (bb and bb > KAPPA_THRESHOLD and gb and gb > KAPPA_THRESHOLD)
            else "no"
        )
        print(f"{r['name']:<30} {bb_str:>8} {gb_str:>8} {sp_str:>8} {pass_str:>6}")

    summary_csv = os.path.join(args.output_dir, "summary.csv")
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "n",
                "blackbox_kappa",
                "glassbox_kappa",
                "sophistication_kappa",
                "pass",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    **r,
                    "pass": "YES"
                    if (
                        r["blackbox_kappa"]
                        and r["glassbox_kappa"]
                        and r["blackbox_kappa"] > KAPPA_THRESHOLD
                        and r["glassbox_kappa"] > KAPPA_THRESHOLD
                    )
                    else "no",
                }
            )
    print(f"\nSummary saved to {summary_csv}")


if __name__ == "__main__":
    main()
