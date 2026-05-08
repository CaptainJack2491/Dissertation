# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "numpy",
#     "scipy",
#     "statsmodels",
# ]
# ///
"""
Stealth Gap Analysis for Study 1
=================================
Tests the divergence between glassbox (internal) and blackbox (output) measures.

Design: 3 oversight levels × 90 runs each
Each run has paired classifications: glassbox intent + blackbox detection.

Usage:
    uv run python scripts/stealth_gap_tests.py
"""

import warnings

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, chi2
from statsmodels.stats.contingency_tables import Table2x2

warnings.filterwarnings("ignore", category=FutureWarning)

DECEPTIVE_BB = {"DECEPTIVE_FRAMING", "OMITTED_CRITICAL", "FABRICATED"}
COMPLIANT_GB = {"COMPLIANT_DECEPTION"}
RESULTS_PATH = "logs/v2_study1/study1_results.csv"


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["is_deceptive_bb"] = df["blackbox_category"].isin(DECEPTIVE_BB).astype(int)
    df["is_compliant_gb"] = df["glassbox_category"].isin(COMPLIANT_GB).astype(int)
    return df


def cramers_v(table: np.ndarray) -> float:
    chi2_val = chi2_contingency(table)[0]
    n = table.sum()
    min_dim = min(table.shape) - 1
    if min_dim == 0 or n == 0:
        return 0.0
    return np.sqrt(chi2_val / (n * min_dim))


def cochran_armitage(counts, nobs):
    k = len(counts)
    scores = np.arange(k, dtype=float)
    n = np.array(nobs, dtype=float)
    x = np.array(counts, dtype=float)
    N = n.sum()
    p_hat = x.sum() / N
    t_bar = np.sum(scores * n) / N
    numerator = np.sum(scores * x) - x.sum() * t_bar
    denominator_sq = p_hat * (1 - p_hat) * (np.sum(scores**2 * n) - N * t_bar**2)
    if denominator_sq <= 0:
        return 0.0, 1.0
    z = numerator / np.sqrt(denominator_sq)
    p_value = chi2.sf(z**2, 1)
    return z, p_value


def sig(p: float, alpha: float = 0.05) -> str:
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < alpha:
        return "*"
    return "n.s."


def fmt_p(p: float) -> str:
    return f"p < .001" if p < 0.001 else f"p = {p:.4f}"


def section(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def subsection(title: str):
    print(f"\n  --- {title} ---\n")


def main():
    df = load_data(RESULTS_PATH)
    ALPHA = 0.05

    section("1. BLACKBOX DECLINE TEST")

    bb_counts = []
    bb_nobs = []
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_detected = sub["is_deceptive_bb"].sum()
        n_total = len(sub)
        bb_counts.append(n_detected)
        bb_nobs.append(n_total)
        print(
            f"  {ov}: {n_detected}/{n_total} ({n_detected / n_total * 100:.1f}%) misleading"
        )

    ct_bb = pd.crosstab(df["oversight"], df["is_deceptive_bb"])
    ct_bb = ct_bb.loc[["low", "mid", "high"]]

    chi2_val, p_val, dof, expected = chi2_contingency(ct_bb.values)
    v = cramers_v(ct_bb.values)
    print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {fmt_p(p_val)} {sig(p_val)}")
    print(f"  Cramér's V = {v:.3f}")

    z_trend, p_trend = cochran_armitage(bb_counts, bb_nobs)
    print(f"\n  Cochran-Armitage trend test: z = {z_trend:.3f}, {fmt_p(p_trend)} {sig(p_trend)}")
    if p_trend < ALPHA:
        direction = "decreasing" if z_trend < 0 else "increasing"
        print(f"    → Blackbox deception {direction} with higher oversight")

    section("2. McNEMAR'S TEST BY OVERSIGHT LEVEL")

    mcnemar_results = {}
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]

        gb_dec = sub["is_compliant_gb"].values
        bb_det = sub["is_deceptive_bb"].values

        a = int(((gb_dec == 1) & (bb_det == 1)).sum())
        b = int(((gb_dec == 1) & (bb_det == 0)).sum())
        c = int(((gb_dec == 0) & (bb_det == 1)).sum())
        d = int(((gb_dec == 0) & (bb_det == 0)).sum())

        table = np.array([[a, b], [c, d]])
        ct = Table2x2(table)
        mcnemar_res = ct.symmetry()
        stat = mcnemar_res.statistic
        p_mc = mcnemar_res.pvalue

        mcnemar_results[ov] = {"stat": stat, "p": p_mc}

        print(f"\n  {ov.upper()} oversight (n={len(sub)}):")
        print(f"    Contingency table (rows=glassbox, cols=blackbox, 1=deceptive/detected):")
        print(f"                    Blackbox")
        print(f"                    detected  not")
        print(f"    Glassbox dec     {a:4d}     {b:3d}")
        print(f"    Glassbox not     {c:4d}     {d:3d}")
        print(f"    McNemar's test: χ²({1}) = {stat:.3f}, {fmt_p(p_mc)} {sig(p_mc)}")
        if p_mc < ALPHA:
            if b > c:
                print(
                    f"    → Glassbox detects MORE deception than blackbox "
                    f"(stealth gap: {b} runs deceptive-undetected vs {c} runs detected-nondec)"
                )
            else:
                print(
                    f"    → Blackbox detects MORE deception than glassbox "
                    f"({c} runs detected-nondec vs {b} runs deceptive-undetected)"
                )

        if (a + b) > 0:
            stealth_rate_val = b / (a + b) * 100
            print(f"    Stealth rate (deceptive but undetected): {b}/{a + b} "
                  f"({stealth_rate_val:.1f}% of deceptive runs)")
        else:
            print("    Stealth rate: N/A (no deceptive runs)")

    section("3. INTERACTION TEST: Stealth Rate Across Oversight")

    stealth_counts = []
    stealth_nobs = []
    print(f"  {'Oversight':12s}  {'Deceptive':>10s}  {'Undetected':>10s}  {'Stealth Rate':>13s}")
    print(f"  {'-' * 12}  {'-' * 10}  {'-' * 10}  {'-' * 13}")
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        gb_dec = sub["is_compliant_gb"].values
        bb_det = sub["is_deceptive_bb"].values

        n_deceptive = int(gb_dec.sum())
        n_undetected = int(((gb_dec == 1) & (bb_det == 0)).sum())
        stealth_rate = n_undetected / n_deceptive * 100 if n_deceptive > 0 else 0

        stealth_counts.append(n_undetected)
        stealth_nobs.append(n_deceptive)
        print(f"  {ov:12s}  {n_deceptive:8d}/90  {n_undetected:8d}  "
              f"{stealth_rate:8.1f}% ({n_undetected}/{n_deceptive})")

    print(f"\n  Chi-squared test on stealth counts (deceptive-undetected vs detected among deceptive):")
    stealth_not_counts = [n - c for n, c in zip(stealth_nobs, stealth_counts)]
    stealth_table = np.array([stealth_counts, stealth_not_counts]).T
    chi2_stealth, p_stealth, dof_stealth, _ = chi2_contingency(stealth_table)
    v_stealth = cramers_v(stealth_table)
    print(f"    χ²({dof_stealth}) = {chi2_stealth:.3f}, {fmt_p(p_stealth)} {sig(p_stealth)}")
    print(f"    Cramér's V = {v_stealth:.3f}")

    z_stealth, p_stealth_trend = cochran_armitage(stealth_counts, stealth_nobs)
    print(f"\n  Cochran-Armitage trend test on stealth rates:")
    print(f"    z = {z_stealth:.3f}, {fmt_p(p_stealth_trend)} {sig(p_stealth_trend)}")
    if p_stealth_trend < ALPHA:
        direction = "decreasing" if z_stealth < 0 else "increasing"
        print(f"    → Stealth rate {direction} with higher oversight")

    section("4. SUMMARY TABLE")

    print(f"  {'Test':45s}  {'Statistic':>12s}  {'p-value':>10s}  {'Significant?':>12s}")
    print(f"  {'-' * 45}  {'-' * 12}  {'-' * 10}  {'-' * 12}")

    print(f"  {'Blackbox decline (chi-squared)':45s}  {f'χ²={chi2_val:.3f}':>12s}  {fmt_p(p_val):>10s}  {sig(p_val, ALPHA):>12s}")

    for ov in ["low", "mid", "high"]:
        r = mcnemar_results[ov]
        sig_str = sig(r["p"], ALPHA)
        stat_str = f"χ²={r['stat']:.3f}"
        p_str = fmt_p(r["p"])
        print(f"  {'McNemar (' + ov + ')':45s}  {stat_str:>12s}  {p_str:>10s}  {sig_str:>12s}")

    sig_stealth = sig(p_stealth, ALPHA)
    print(f"  {'Stealth rate (chi-squared)':45s}  {f'χ²={chi2_stealth:.3f}':>12s}  {fmt_p(p_stealth):>10s}  {sig_stealth:>12s}")

    print(f"\n  Significance codes: *** p < .001  ** p < .01  * p < .05  n.s. = not significant")
    print(f"  Alpha = {ALPHA}")


if __name__ == "__main__":
    main()
