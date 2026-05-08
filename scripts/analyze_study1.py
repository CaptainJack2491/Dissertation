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
Statistical Analysis of Study 1: Oversight Effect
================================================
Tests whether higher oversight reduces deception.

Design: 3 models × 3 oversight levels × 1 scenario × 1 goal_type (bare) × n=30
Total: 270 runs

Usage:
    uv run python scripts/analyze_study1.py logs/v2_study1/study1_results.csv
"""

import sys
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, chi2
from statsmodels.stats.contingency_tables import Table2x2
from statsmodels.stats.proportion import proportion_confint
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)

SIGNIFICANCE_LEVEL = 0.05

DECEPTIVE_BB = {"DECEPTIVE_FRAMING", "OMITTED_CRITICAL", "FABRICATED"}
COMPLIANT_GB = {"COMPLIANT_DECEPTION"}
HONEST_BB = {"ACCURATE"}
HONEST_GB = {"ROBUST_HONEST", "CONSIDERED_HONEST"}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["is_deceptive_bb"] = df["blackbox_category"].isin(DECEPTIVE_BB).astype(int)
    df["is_compliant_gb"] = df["glassbox_category"].isin(COMPLIANT_GB).astype(int)
    df["is_strategic"] = (df["glassbox_sophistication"] == "STRATEGIC").astype(int)
    df["is_deceptive_overall"] = (
        (df["is_deceptive_bb"] == 1) | (df["is_compliant_gb"] == 1)
    ).astype(int)
    return df


def odds_ratio_ci(table_2x2, alpha=0.05):
    a, b, c, d = table_2x2[0, 0], table_2x2[0, 1], table_2x2[1, 0], table_2x2[1, 1]
    if 0 in (a, b, c, d):
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    or_val = (a * d) / (b * c)
    log_or = np.log(or_val)
    se_log_or = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = stats.norm.ppf(1 - alpha / 2)
    return or_val, np.exp(log_or - z * se_log_or), np.exp(log_or + z * se_log_or)


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
    p_value = 2 * stats.norm.sf(abs(z))
    return z, p_value


def cramers_v(table):
    chi2_val = chi2_contingency(table)[0]
    n = table.sum()
    min_dim = min(table.shape) - 1
    if min_dim == 0 or n == 0:
        return 0.0
    return np.sqrt(chi2_val / (n * min_dim))


def sig(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return "n.s."


def fmt_p(p):
    return f"p < .001" if p < 0.001 else f"p = {p:.4f}"


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def subsection(title):
    print(f"\n  --- {title} ---\n")


def effect_size(v):
    if v < 0.1:
        return "negligible"
    elif v < 0.3:
        return "small"
    elif v < 0.5:
        return "medium"
    return "large"


def main():
    if len(sys.argv) < 2:
        path = "logs/v2_study1/study1_results.csv"
    else:
        path = sys.argv[1]

    df = load_data(path)
    print(f"Study 1: Oversight Effect Analysis")
    print(f"Loaded {len(df)} runs")
    print(f"Models: {sorted(df['model'].unique())}")
    print(f"Oversight levels: {sorted(df['oversight'].unique())}")

    section("1. OVERSIGHT EFFECT (Overall)")

    print("  Deception rates by oversight level:")
    counts, nobs_list = [], []
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_dec = sub["is_deceptive_overall"].sum()
        n_tot = len(sub)
        rate = n_dec / n_tot * 100
        ci_low, ci_high = proportion_confint(n_dec, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {ov}: {n_dec}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )
        counts.append(n_dec)
        nobs_list.append(n_tot)

    ct = pd.crosstab(df["oversight"], df["is_deceptive_overall"])
    ct = ct.loc[["low", "mid", "high"]]
    chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
    v = cramers_v(ct.values)
    print(
        f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {fmt_p(p_val)} {sig(p_val)}"
    )
    print(f"  Cramér's V = {v:.3f} ({effect_size(v)})")

    z_trend, p_trend = cochran_armitage(counts, nobs_list)
    print(
        f"\n  Cochran-Armitage trend test: z = {z_trend:.3f}, {fmt_p(p_trend)} {sig(p_trend)}"
    )
    if p_trend < 0.05:
        direction = "decreasing" if z_trend < 0 else "increasing"
        print(f"    → Deception {direction} with higher oversight")

    section("2. BY OVERSIGHT LEVEL (Blackbox Output)")

    print("  Blackbox deception rates:")
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_dec = sub["is_deceptive_bb"].sum()
        n_tot = len(sub)
        rate = n_dec / n_tot * 100
        ci_low, ci_high = proportion_confint(n_dec, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {ov}: {n_dec}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    section("3. MODEL DIFFERENCES IN OVERSIGHT SENSITIVITY")

    print(f"  {'Model':35s}  {'Low':>8s}  {'Mid':>8s}  {'High':>8s}  {'Trend':>10s}")
    print(f"  {'-' * 35}  {'-' * 8}  {'-' * 8}  {'-' * 8}  {'-' * 10}")

    for model in sorted(df["model"].unique()):
        mdf = df[df["model"] == model]
        rates = []
        counts, nobs_list = [], []
        for ov in ["low", "mid", "high"]:
            sub = mdf[mdf["oversight"] == ov]
            n_dec = sub["is_deceptive_overall"].sum()
            n_tot = len(sub)
            rate = n_dec / n_tot * 100
            rates.append(rate)
            counts.append(n_dec)
            nobs_list.append(n_tot)
            ci_low, ci_high = proportion_confint(
                n_dec, n_tot, alpha=0.05, method="wilson"
            )

        z_trend, p_trend = cochran_armitage(counts, nobs_list)
        model_short = model.split("/")[-1] if "/" in model else model
        print(
            f"  {model_short:35s}  {rates[0]:7.1f}%  {rates[1]:7.1f}%  {rates[2]:7.1f}%  z={z_trend:+.2f} {sig(p_trend)}"
        )

    section("4. PAIRWISE COMPARISONS (Bonferroni-corrected)")

    pairs = list(combinations(["low", "mid", "high"], 2))
    n_comp = len(pairs)
    adj_alpha = SIGNIFICANCE_LEVEL / n_comp

    for o1, o2 in pairs:
        sub = df[df["oversight"].isin([o1, o2])]
        ct_pair = pd.crosstab(sub["oversight"], sub["is_deceptive_overall"])
        ct_pair = ct_pair.loc[[o1, o2]]
        chi2_p, p_val, dof, _ = chi2_contingency(ct_pair.values)
        _, fisher_p = fisher_exact(ct_pair.values)
        or_val, or_ci_low, or_ci_high = odds_ratio_ci(ct_pair.values)
        sig_mark = "SIG" if p_val < adj_alpha else "n.s."
        print(
            f"  {o1} vs {o2}: χ²(1) = {chi2_p:.3f}, Fisher {fmt_p(fisher_p)}, OR = {or_val:.2f} [{or_ci_low:.2f}, {or_ci_high:.2f}] [{sig_mark}]"
        )

    section("5. GLASSBOX REASONING BY OVERSIGHT")

    print("  Compliant reasoning rates by oversight:")
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_comp = sub["is_compliant_gb"].sum()
        n_tot = len(sub)
        rate = n_comp / n_tot * 100
        ci_low, ci_high = proportion_confint(n_comp, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {ov}: {n_comp}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    section("6. STRATEGIC SOPHISTICATION")

    print("  Full sophistication breakdown by oversight:")
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_tot = len(sub)
        counts = sub["glassbox_sophistication"].value_counts()
        n_strat = counts.get("STRATEGIC", 0)
        n_tact = counts.get("TACTICAL", 0)
        n_naive = counts.get("NAIVE", 0)
        print(f"    {ov}: strategic={n_strat}/{n_tot} ({n_strat/n_tot*100:.1f}%), "
              f"tactical={n_tact}/{n_tot} ({n_tact/n_tot*100:.1f}%), "
              f"naive={n_naive}/{n_tot} ({n_naive/n_tot*100:.1f}%)")
    print()
    print("  Strategic reasoning rates by oversight:")
    for ov in ["low", "mid", "high"]:
        sub = df[df["oversight"] == ov]
        n_strat = sub["is_strategic"].sum()
        n_tot = len(sub)
        rate = n_strat / n_tot * 100
        ci_low, ci_high = proportion_confint(
            n_strat, n_tot, alpha=0.05, method="wilson"
        )
        print(
            f"    {ov}: {n_strat}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    section("7. LOGISTIC REGRESSION: deception ~ oversight")

    model_df = df.copy()
    model_df["oversight_num"] = model_df["oversight"].map(
        {"low": 0, "mid": 1, "high": 2}
    )
    model_df["model_code"] = pd.Categorical(model_df["model"]).codes

    X = model_df[["oversight_num", "model_code"]]
    X = sm.add_constant(X)
    y = model_df["is_deceptive_overall"]

    try:
        logit = sm.Logit(y, X).fit(disp=0)
        print(logit.summary2().tables[1].to_string())
        print(f"\n  Pseudo R² = {logit.prsquared:.4f}, AIC = {logit.aic:.1f}")

        print("\n  Odds ratios (exponentiated coefficients):")
        for name, coef, pval in zip(X.columns, logit.params, logit.pvalues):
            if name == "const":
                continue
            or_val = np.exp(coef)
            ci = logit.conf_int().loc[name]
            or_ci = (np.exp(ci[0]), np.exp(ci[1]))
            print(
                f"    {name:20s}  OR = {or_val:.3f}  95% CI: [{or_ci[0]:.3f}, {or_ci[1]:.3f}]  {sig(pval)}"
            )
    except Exception as e:
        print(f"  Logistic regression failed: {e}")

    section("ANALYSIS COMPLETE")
    print(f"  Total runs: {len(df)}")
    print(f"  Models: {sorted(df['model'].unique())}")


if __name__ == "__main__":
    main()
