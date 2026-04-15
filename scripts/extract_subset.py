"""
Extract a stratified subset of runs from an experiment directory.

Usage:
    # Extract 20% subset from Study 1 (54 runs from 270)
    python scripts/extract_subset.py \
        --logs-dir logs/v2_study1 \
        --output-dir logs/v2_study1_subset \
        --subset-fraction 0.2

    # Extract 10% subset
    python scripts/extract_subset.py \
        --logs-dir logs/v2_study1 \
        --output-dir logs/v2_study1_subset \
        --subset-fraction 0.1
"""

import argparse
import os
import random
import shutil
import sys
from collections import defaultdict


def discover_runs(logs_dir: str) -> dict[str, list[str]]:
    """Discover all runs, grouped by (model, scenario, goal_type, oversight)."""
    runs = defaultdict(list)

    for root, dirs, files in os.walk(logs_dir):
        basename = os.path.basename(root)

        if basename == "baseline":
            continue

        for f in files:
            if f.endswith(".json") and not f.startswith("_") and not f.startswith("."):
                rel_path = os.path.relpath(root, logs_dir)
                parts = rel_path.split(os.sep)

                if len(parts) == 4:
                    model, scenario, goal_type, oversight = parts
                    key = (model, scenario, goal_type, oversight)
                    runs[key].append(os.path.join(root, f))

    return runs


def extract_subset(
    logs_dir: str,
    output_dir: str,
    subset_fraction: float,
    seed: int = 42,
) -> None:
    """Extract a stratified random subset of runs."""
    random.seed(seed)

    runs_by_cell = discover_runs(logs_dir)

    print(f"Found {len(runs_by_cell)} cells:")
    total_runs = 0
    for cell, paths in sorted(runs_by_cell.items()):
        print(f"  {'/'.join(cell)}: {len(paths)} runs")
        total_runs += len(paths)
    print(f"Total: {total_runs} runs\n")

    subset_runs = []
    for cell, paths in runs_by_cell.items():
        n_subset = max(1, int(len(paths) * subset_fraction))
        selected = random.sample(paths, min(n_subset, len(paths)))
        subset_runs.extend(selected)
        print(f"  {'/'.join(cell)}: selected {len(selected)}/{len(paths)} runs")

    print(f"\nTotal subset: {len(subset_runs)} runs\n")

    copied_runs = 0
    scenario_dirs = set()

    for src_path in subset_runs:
        rel_path = os.path.relpath(src_path, logs_dir)
        dst_path = os.path.join(output_dir, rel_path)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src_path, dst_path)
        copied_runs += 1

        cell_parts = rel_path.split(os.sep)
        if len(cell_parts) >= 4:
            src_scenario_dir = os.path.join(logs_dir, cell_parts[0], cell_parts[1])
            dst_scenario_dir = os.path.join(output_dir, cell_parts[0], cell_parts[1])
            scenario_dirs.add((src_scenario_dir, dst_scenario_dir))

        if len(cell_parts) >= 4:
            cell_str = "/".join(cell_parts[:4])
        else:
            cell_str = rel_path
        print(f"  Copied: {cell_str}/{os.path.basename(src_path)}")

    print(f"\nCopying baselines...")
    for src_dir, dst_dir in sorted(scenario_dirs):
        baseline_src = os.path.join(src_dir, "baseline.md")
        baseline_dst = os.path.join(dst_dir, "baseline.md")
        if os.path.exists(baseline_src):
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(baseline_src, baseline_dst)
            print(f"  Copied baseline: {os.path.relpath(dst_dir, output_dir)}")
        else:
            print(f"  Warning: no baseline.md found at {src_dir}")

    print(
        f"\nDone. Copied {copied_runs} runs + {len(scenario_dirs)} baselines to {output_dir}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract stratified subset from experiment logs"
    )
    parser.add_argument(
        "--logs-dir",
        required=True,
        help="Source directory containing experiment runs",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for subset",
    )
    parser.add_argument(
        "--subset-fraction",
        type=float,
        default=0.2,
        help="Fraction of runs to extract per cell (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.logs_dir):
        print(f"Error: {args.logs_dir} is not a directory")
        sys.exit(1)

    if args.subset_fraction <= 0 or args.subset_fraction > 1:
        print(
            f"Error: subset-fraction must be between 0 and 1, got {args.subset_fraction}"
        )
        sys.exit(1)

    extract_subset(
        logs_dir=args.logs_dir,
        output_dir=args.output_dir,
        subset_fraction=args.subset_fraction,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
