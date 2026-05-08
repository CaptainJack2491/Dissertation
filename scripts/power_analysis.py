"""
Post-hoc Power Analysis for Dissertation Studies
================================================
Determines whether non-significant chi-squared results reflect true absence
of effect or insufficient statistical power.

Uses statsmodels GofChisquarePower for chi-squared test power analysis.
Effect size: Cohen's w computed from proportion differences in 3x2 tables.

Usage:
    uv run python scripts/power_analysis.py
"""

import numpy as np
from statsmodels.stats.power import GofChisquarePower


def cohens_w_from_prop_diff(p0, d, n_groups=3):
    """Cohen's w for a n_groups x 2 contingency table.

    Assumes equal group sizes, baseline proportion p0 in all groups under H0,
    and a difference d in exactly one group under H1.

    w = d * sqrt( (1/p0 + 1/(1-p0)) / n_groups )
    """
    return abs(d) * np.sqrt((1.0 / p0 + 1.0 / (1.0 - p0)) / n_groups)


def prop_diff_from_cohens_w(p0, w, n_groups=3):
    """Inverse: proportion difference corresponding to a given Cohen's w."""
    return w / np.sqrt((1.0 / p0 + 1.0 / (1.0 - p0)) / n_groups)


def power_interp(power):
    if power >= 0.95:
        return "Excellent (>95%) — very likely to detect"
    elif power >= 0.80:
        return "Adequate (>=80%) — standard threshold met"
    elif power >= 0.50:
        return "Moderate (50-80%) — may be missed"
    elif power >= 0.20:
        return "Low (20-50%) — unreliable, likely to miss"
    else:
        return "Very low (<20%) — essentially undetectable"


def analyze(n_per_group, n_groups, alpha, baseline_prop, label, pp_diffs=(10, 15, 20)):
    n_total = n_per_group * n_groups
    power_analysis = GofChisquarePower()
    # df = n_bins - 1 = 2 for a 3-group test
    n_bins = n_groups

    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"  N = {n_per_group}/group x {n_groups} groups = {n_total} total")
    print(f"  α = {alpha},  baseline deception rate ≈ {baseline_prop:.1%}")
    print(f"{'=' * 72}")

    # --- 1. Minimum detectable effect at 80% power ---
    w_min = power_analysis.solve_power(
        effect_size=None, nobs=n_total, alpha=alpha, power=0.80, n_bins=n_bins
    )
    d_min = prop_diff_from_cohens_w(baseline_prop, w_min, n_groups)

    print(f"\n  1. Minimum Detectable Effect (80% power)")
    print(f"     Cohen's w = {w_min:.4f}")
    print(f"     Diff in proportions = {d_min:.1%}  ({d_min*100:.1f} percentage points)")
    print(f"     → With N={n_total}, any effect smaller than ~{d_min*100:.0f}pp")
    print(f"       between groups could not be reliably detected.")

    # --- 2. Achieved power for specific effect sizes ---
    print(f"\n  2. Achieved Power for Specific Effect Sizes:")
    print(f"     {'Diff (pp)':>10s}  {'Cohen\'s w':>10s}  {'Power':>8s}  {'Interpretation'}")
    print(f"     {'-'*10}  {'-'*10}  {'-'*8}  {'-'*42}")

    for pp in pp_diffs:
        d = pp / 100.0
        w = cohens_w_from_prop_diff(baseline_prop, d, n_groups)
        pwr = power_analysis.solve_power(
            effect_size=w, nobs=n_total, alpha=alpha, power=None, n_bins=n_bins
        )
        print(f"     {pp:>8d}pp  {w:>10.4f}  {pwr:>7.1%}  {power_interp(pwr)}")

    # --- 3. Within-model power (n=30 per group) ---
    n_within = 30
    n_within_total = n_within * n_groups

    w_min_30 = power_analysis.solve_power(
        effect_size=None, nobs=n_within_total, alpha=alpha, power=0.80, n_bins=n_bins
    )
    d_min_30 = prop_diff_from_cohens_w(baseline_prop, w_min_30, n_groups)

    print(f"\n  3. Within-Model Power (n = 30 per group)")
    print(f"     Min detectable diff (80% power): {d_min_30:.1%}  ({d_min_30*100:.1f}pp)")
    print(f"     Achieved power by effect size:")
    for pp in pp_diffs:
        d = pp / 100.0
        w = cohens_w_from_prop_diff(baseline_prop, d, n_groups)
        pwr = power_analysis.solve_power(
            effect_size=w, nobs=n_within_total, alpha=alpha, power=None, n_bins=n_bins
        )
        print(f"       {pp:>2d}pp difference: {pwr:.1%} power  ({power_interp(pwr).split('—')[0].strip()})")

    return d_min


def main():
    print("=" * 72)
    print("  POST-HOC POWER ANALYSIS")
    print("  AI Deception in Strategic Reasoning")
    print("=" * 72)
    print()
    print("  Context: Both studies used chi-squared tests on 3x2 contingency")
    print("  tables and found non-significant results. This analysis")
    print("  determines whether those null results are meaningful.")

    alpha = 0.05

    # Study 1: Oversight effect (low / mid / high oversight)
    # Observed rates: low=71.1%, mid=70.0%, high=64.4% → baseline ~68.5%
    analyze(
        n_per_group=90,
        n_groups=3,
        alpha=alpha,
        baseline_prop=0.685,
        label="STUDY 1: Oversight Effect (low / mid / high)",
    )

    # Study 2: Framing effect (bare / moral / self-serving)
    # Observed rates: bare=66.7%, moral=65.6%, self-serving=66.7% → baseline ~66.3%
    analyze(
        n_per_group=90,
        n_groups=3,
        alpha=alpha,
        baseline_prop=0.663,
        label="STUDY 2: Goal Framing Effect (bare / moral / self-serving)",
    )

    # --- Summary ---
    print(f"\n{'=' * 72}")
    print("  SUMMARY AND INTERPRETATION")
    print(f"{'=' * 72}")

    print()
    print("  Between-group (N=270, n=90/group):")
    print("    • Both studies had ~80% power to detect differences of ~15pp")
    print("    • Neither study was adequately powered for effects <~15pp")
    print("    • The non-significant chi-squared results may reflect either:")
    print("      (a) truly absent between-group effects, or")
    print("      (b) modest effects (<~15pp) that the design lacked power to detect")
    print()
    print("  Within-model (n=30/model/cell):")
    print("    • These per-model sub-analyses were substantially underpowered")
    print("    • Only very large effects (>~26pp) would be detectable at 80% power")
    print("    • Null within-model results should NOT be interpreted as")
    print("      evidence that specific models were unaffected by the manipulation")
    print()
    print("  Implications for the dissertation:")
    print("    • The null between-group results do not rule out small-to-moderate")
    print("      effects (5-15pp), which could be substantively meaningful.")
    print("    • Future work should target n ≈ 200-210 per group to reliably")
    print("      detect 10pp effects at 80% power.")


if __name__ == "__main__":
    main()
