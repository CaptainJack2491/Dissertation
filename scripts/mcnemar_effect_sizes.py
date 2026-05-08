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
McNemar Effect Sizes for Study 1
=================================
Computes effect-size metrics from the paired 2x2 tables of glassbox vs blackbox
for each oversight level.

Each table cell:
  a = glassbox-deceptive AND blackbox-misleading
  b = glassbox-deceptive AND NOT blackbox-misleading  (stealth runs)
  c = NOT glassbox-deceptive AND blackbox-misleading  (false alarms)
  d = neither

Reports for each oversight level:
  - Discordant pair counts: b (stealth), c (false alarm)
  - Odds ratio of discordant pairs: OR = b / c
  - 95% confidence interval for OR
  - Proportion of discordant pairs: (b + c) / N

Usage:
    uv run python scripts/mcnemar_effect_sizes.py
"""

import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)

DECEPTIVE_BB = {"DECEPTIVE_FRAMING", "OMITTED_CRITICAL", "FABRICATED"}
COMPLIANT_GB = {"COMPLIANT_DECEPTION"}
RESULTS_PATH = "logs/v2_study1/study1_results.csv"
Z_ALPHA = stats.norm.ppf(1 - 0.05 / 2)


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["is_deceptive_bb"] = df["blackbox_category"].isin(DECEPTIVE_BB).astype(int)
    df["is_compliant_gb"] = df["glassbox_category"].isin(COMPLIANT_GB).astype(int)
    return df


def discordant_or_ci(b: int, c: int) -> tuple[float, float, float]:
    if b == 0 or c == 0:
        b_adj, c_adj = b + 0.5, c + 0.5
    else:
        b_adj, c_adj = float(b), float(c)
    or_val = b_adj / c_adj
    log_or = np.log(or_val)
    se = np.sqrt(1 / b_adj + 1 / c_adj)
    ci_low = np.exp(log_or - Z_ALPHA * se)
    ci_high = np.exp(log_or + Z_ALPHA * se)
    return or_val, ci_low, ci_high


def main():
    df = load_data(RESULTS_PATH)

    print("=" * 72)
    print("  McNemar Effect Sizes — Discordant-Pair Analysis")
    print("=" * 72)

    header = (
        f"  {'Oversight':>9s}  {'N':>4s}  {'b(stealth)':>10s}  "
        f"{'c(falseAlm)':>10s}  {'OR(b/c)':>8s}  "
        f"{'OR 95% CI':>20s}  {'(b+c)/N':>8s}  {'Disagr%':>8s}"
    )
    sep = "  " + "-" * 9 + "  " + "-" * 4 + "  " + "-" * 10 + "  " + "-" * 10 + "  " + "-" * 8 + "  " + "-" * 20 + "  " + "-" * 8 + "  " + "-" * 8

    print(f"\n{header}")
    print(sep)

    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        N = len(sub)

        gb_dec = sub["is_compliant_gb"].values
        bb_det = sub["is_deceptive_bb"].values

        a = int(((gb_dec == 1) & (bb_det == 1)).sum())
        b = int(((gb_dec == 1) & (bb_det == 0)).sum())
        c = int(((gb_dec == 0) & (bb_det == 1)).sum())
        d = int(((gb_dec == 0) & (bb_det == 0)).sum())

        or_val, ci_low, ci_high = discordant_or_ci(b, c)
        discordant_prop = (b + c) / N
        discordant_pct = discordant_prop * 100

        ci_str = f"[{ci_low:.3f}, {ci_high:.3f}]"

        print(
            f"  {ov:>9s}  {N:>4d}  {b:>10d}  {c:>10d}  "
            f"{or_val:>8.3f}  {ci_str:>20s}  "
            f"{discordant_prop:>8.3f}  {discordant_pct:>7.1f}%"
        )

        if b + c > 0:
            if b > c:
                direction = f"stealth runs outnumber false alarms {b}:{c}"
            elif c > b:
                direction = f"false alarms outnumber stealth runs {c}:{b}"
            else:
                direction = "stealth runs and false alarms are equal"
            print(f"    → {direction}")

        decision = ""
        if or_val > 1 and ci_low > 1:
            decision = " (OR > 1, significant)"
        elif or_val < 1 and ci_high < 1:
            decision = " (OR < 1, significant)"
        else:
            decision = " (not significant, CI crosses 1)"
        print(f"    OR 95% CI does{'' if 'significant' in decision else ' not'} exclude 1{decision}")

    print("\n  Interpretation:")
    print("    b = glassbox says deceptive  |  blackbox says honest  (stealth)")
    print("    c = glassbox says honest     |  blackbox says misleading  (false alarm)")
    print("    OR = b/c: odds that a discordant pair is a stealth run vs a false alarm")
    print("    (b+c)/N: proportion of all pairs showing disagreement between judges")


if __name__ == "__main__":
    main()
