"""
Judge Comparison Tool - Compare different judge model pairs on the same logs.

Tests inter-rater reliability (Cohen's Kappa) between different judge model configurations
to validate the 20% cross-family validation subset approach.

Usage:
    # Run single model (same for both blackbox and glassbox) on logs, save to CSV
    python scripts/judge_comparison.py --run --blackbox-model claude-sonnet-4-20250514 --provider anthropic --logs-dir logs/v2_dry_run --output results_claude.csv

    # Compute Kappa between two result CSVs
    python scripts/judge_comparison.py --compare --csv1 results_claude.csv --csv2 results_gpt.csv

    # Run multiple models and compare all pairs
    python scripts/judge_comparison.py --run-all --logs-dir logs/v2_dry_run --output-dir judge_validation/
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.judge import Judge


def discover_logs(logs_dir: str, max_per_cell: int = 2) -> List[str]:
    """Discover a stratified sample of logs from v2_dry_run.

    Picks up to max_per_cell logs per (model, scenario, goal_type, oversight) combination.
    """
    logs = []
    for root, dirs, files in os.walk(logs_dir):
        if os.path.basename(root) == "baseline":
            continue
        for f in files:
            if f.endswith(".json") and not f.startswith("_"):
                logs.append(os.path.join(root, f))

    grouped = defaultdict(list)
    for log_path in logs:
        parts = log_path.replace(logs_dir + "/", "").split("/")
        if len(parts) >= 4:
            model, scenario, goal_type, oversight = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
            )
            key = (model, scenario, goal_type, oversight)
        else:
            key = tuple(parts)
        grouped[key].append(log_path)

    sampled = []
    for key, paths in grouped.items():
        sampled.extend(paths[:max_per_cell])

    return sorted(sampled)


def run_judgment(
    logs_dir: str,
    scenarios_dir: str,
    logs: List[str],
    model_id: str,
    provider: str,
) -> List[Dict]:
    """Run judge with same model for both blackbox and glassbox on all logs."""
    config = {
        "id": model_id,
        "provider": provider,
        "temperature": 0,
    }

    judge = Judge(
        blackbox_model=config,
        glassbox_model=config,
    )

    verdicts = []
    for i, log_path in enumerate(logs, 1):
        print(
            f"  [{i}/{len(logs)}] {model_id}: {os.path.basename(os.path.dirname(log_path))}"
        )
        try:
            verdict = judge.judge_single(
                log_path=log_path,
                logs_dir=logs_dir,
                scenarios_dir=scenarios_dir,
                enabled_judges={"regex", "blackbox", "glassbox"},
            )
            verdicts.append(verdict)
        except Exception as e:
            print(f"  ERROR on {log_path}: {e}")
    return verdicts


def write_csv(output_path: str, verdicts: List[Dict]) -> None:
    """Write verdicts to CSV."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
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


def read_csv(path: str) -> List[Dict]:
    """Read verdicts from CSV."""
    verdicts = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            verdicts.append(row)
    return verdicts


def compute_kappa(cats1: List[str], cats2: List[str]) -> Optional[float]:
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


def compare_two_csvs(csv1_path: str, csv2_path: str) -> Dict:
    """Compare two CSV files and compute Cohen's Kappa."""
    v1 = read_csv(csv1_path)
    v2 = read_csv(csv2_path)

    if len(v1) != len(v2):
        print(f"WARNING: Different number of rows ({len(v1)} vs {len(v2)})")

    bb_cats1 = [r.get("blackbox_category", "") for r in v1]
    bb_cats2 = [r.get("blackbox_category", "") for r in v2]
    gb_cats1 = [r.get("glassbox_category", "") for r in v1]
    gb_cats2 = [r.get("glassbox_category", "") for r in v2]
    soph1 = [r.get("glassbox_sophistication", "") for r in v1]
    soph2 = [r.get("glassbox_sophistication", "") for r in v2]

    bb_kappa = compute_kappa(bb_cats1, bb_cats2)
    gb_kappa = compute_kappa(gb_cats1, gb_cats2)
    soph_kappa = compute_kappa(soph1, soph2)

    return {
        "blackbox_kappa": bb_kappa,
        "glassbox_kappa": gb_kappa,
        "sophistication_kappa": soph_kappa,
        "n": len([c for c in bb_cats1 if c]),
    }


def run_all_models(
    logs_dir: str, scenarios_dir: str, logs: List[str], output_dir: str
) -> tuple[List[str], List[tuple]]:
    """Run all judge model pairs and save to separate CSVs."""
    models = [
        ("claude-sonnet-4-20250514", "anthropic"),
        ("gpt-4.1", "openai"),
        ("gpt-4.1-mini", "openai"),
        ("claude-haiku-4-20250514", "anthropic"),
        ("grok-fast-4.1", "xai"),
    ]

    csv_paths = []
    for model_id, provider in models:
        safe_name = model_id.replace("-", "_").replace(".", "_")
        output_path = os.path.join(output_dir, f"results_{safe_name}.csv")
        csv_paths.append(output_path)

        print(f"\n=== Running: {model_id} (both prongs) ===")
        verdicts = run_judgment(logs_dir, scenarios_dir, logs, model_id, provider)
        write_csv(output_path, verdicts)
        print(f"Saved {len(verdicts)} verdicts to {output_path}")

    return csv_paths, models


def compare_all_pairs(
    csv_paths: List[str], model_names: List[str], output_path: str
) -> None:
    """Compare all CSV pairs and save results."""
    rows = []
    for i, (path1, name1) in enumerate(zip(csv_paths, model_names)):
        for path2, name2 in zip(csv_paths[i + 1 :], model_names[i + 1 :]):
            print(f"\nComparing {name1} vs {name2}:")
            result = compare_two_csvs(path1, path2)

            bb = (
                f"{result['blackbox_kappa']:.3f}" if result["blackbox_kappa"] else "N/A"
            )
            gb = (
                f"{result['glassbox_kappa']:.3f}" if result["glassbox_kappa"] else "N/A"
            )
            sp = (
                f"{result['sophistication_kappa']:.3f}"
                if result["sophistication_kappa"]
                else "N/A"
            )

            print(f"  Blackbox Kappa:     {bb}")
            print(f"  Glassbox Kappa:     {gb}")
            print(f"  Sophistication:     {sp}")

            rows.append(
                {
                    "judge_1": name1,
                    "judge_2": name2,
                    "blackbox_kappa": bb,
                    "glassbox_kappa": gb,
                    "sophistication_kappa": sp,
                    "n": result["n"],
                }
            )

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "judge_1",
                "judge_2",
                "blackbox_kappa",
                "glassbox_kappa",
                "sophistication_kappa",
                "n",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n\nAll comparisons saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Judge Comparison Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    run_parser = subparsers.add_parser(
        "run", help="Run judge on logs with a single model (same for both prongs)"
    )
    run_parser.add_argument(
        "--blackbox-model", required=True, help="Model ID for blackbox judge"
    )
    run_parser.add_argument(
        "--glassbox-model",
        help="Model ID for glassbox judge (default: same as blackbox)",
    )
    run_parser.add_argument(
        "--provider", required=True, choices=["anthropic", "openai"], help="Provider"
    )
    run_parser.add_argument(
        "--logs-dir", default="logs/v2_dry_run", help="Directory containing logs"
    )
    run_parser.add_argument(
        "--scenarios-dir", default="scenarios", help="Directory containing scenarios"
    )
    run_parser.add_argument("--output", required=True, help="Output CSV path")
    run_parser.add_argument(
        "--max-per-cell", type=int, default=2, help="Max logs per cell"
    )

    compare_parser = subparsers.add_parser("compare", help="Compare two result CSVs")
    compare_parser.add_argument("--csv1", required=True, help="First results CSV")
    compare_parser.add_argument("--csv2", required=True, help="Second results CSV")

    all_parser = subparsers.add_parser(
        "run-all", help="Run all models and compare all pairs"
    )
    all_parser.add_argument(
        "--logs-dir", default="logs/v2_dry_run", help="Directory containing logs"
    )
    all_parser.add_argument(
        "--scenarios-dir", default="scenarios", help="Directory containing scenarios"
    )
    all_parser.add_argument(
        "--output-dir", default="judge_validation", help="Output directory for CSVs"
    )
    all_parser.add_argument(
        "--max-per-cell", type=int, default=2, help="Max logs per cell"
    )

    args = parser.parse_args()

    if args.command == "run":
        print("Discovering logs...")
        logs = discover_logs(args.logs_dir, max_per_cell=args.max_per_cell)
        print(f"Selected {len(logs)} logs\n")

        model_id = args.blackbox_model
        glassbox_model = args.glassbox_model or model_id

        print(
            f"Running {model_id} (blackbox) + {glassbox_model} (glassbox) on {len(logs)} logs...\n"
        )
        verdicts = run_judgment(
            args.logs_dir, args.scenarios_dir, logs, model_id, args.provider
        )

        if glassbox_model != model_id:
            judge = Judge(
                blackbox_model={
                    "id": model_id,
                    "provider": args.provider,
                    "temperature": 0,
                },
                glassbox_model={
                    "id": glassbox_model,
                    "provider": args.provider,
                    "temperature": 0,
                },
            )
            verdicts = []
            for i, log_path in enumerate(logs, 1):
                print(
                    f"  [{i}/{len(logs)}] {model_id}/{glassbox_model}: {os.path.basename(os.path.dirname(log_path))}"
                )
                try:
                    v = judge.judge_single(
                        log_path=log_path,
                        logs_dir=args.logs_dir,
                        scenarios_dir=args.scenarios_dir,
                        enabled_judges={"regex", "blackbox", "glassbox"},
                    )
                    verdicts.append(v)
                except Exception as e:
                    print(f"  ERROR: {e}")

        write_csv(args.output, verdicts)
        print(f"\nSaved {len(verdicts)} verdicts to {args.output}")

    elif args.command == "compare":
        print(f"Comparing {args.csv1} vs {args.csv2}...\n")
        result = compare_two_csvs(args.csv1, args.csv2)

        print(
            f"Blackbox Kappa:     {result['blackbox_kappa']:.3f}"
            if result["blackbox_kappa"]
            else "Blackbox Kappa:     N/A"
        )
        print(
            f"Glassbox Kappa:    {result['glassbox_kappa']:.3f}"
            if result["glassbox_kappa"]
            else "Glassbox Kappa:     N/A"
        )
        print(
            f"Sophistication:    {result['sophistication_kappa']:.3f}"
            if result["sophistication_kappa"]
            else "Sophistication:     N/A"
        )
        print(f"Comparisons:       {result['n']}")

    elif args.command == "run-all":
        print("Discovering logs...")
        logs = discover_logs(args.logs_dir, max_per_cell=args.max_per_cell)
        print(f"Selected {len(logs)} logs\n")

        os.makedirs(args.output_dir, exist_ok=True)

        csv_paths, models = run_all_models(
            args.logs_dir, args.scenarios_dir, logs, args.output_dir
        )

        print("\n" + "=" * 60)
        print("COMPARING ALL PAIRS")
        print("=" * 60)
        compare_all_pairs(
            csv_paths,
            [m[0] for m in models],
            os.path.join(args.output_dir, "comparison_results.csv"),
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
