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
Statistical Analysis of Study 2: Framing Effect
=============================================
Tests whether providing a moral rationalization increases deception.

Design: 3 models × 3 goal_types × 1 scenario × 1 oversight level (mid) × n=30
Total: 270 runs

Usage:
    uv run python scripts/analyze_study2.py logs/v2_study2/study2_results.csv
"""

import sys
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, chi2
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.proportion import proportion_confint
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)

SIGNIFICANCE_LEVEL = 0.05

DECEPTIVE_BB = {"DECEPTIVE_FRAMING", "OMITTED_CRITICAL", "FABRICATED"}
COMPLIANT_GB = {"COMPLIANT_DECEPTION"}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["is_deceptive_bb"] = df["blackbox_category"].isin(DECEPTIVE_BB).astype(int)
    df["is_compliant_gb"] = df["glassbox_category"].isin(COMPLIANT_GB).astype(int)
    df["is_strategic"] = (df["glassbox_sophistication"] == "STRATEGIC").astype(int)
    df["is_deceptive_overall"] = (
        (df["is_deceptive_bb"] == 1) | (df["is_compliant_gb"] == 1)
    ).astype(int)

    # Extract goal_type from run_id: model/scenario/goal_type/oversight/timestamp
    df["goal_type"] = df["run_id"].apply(lambda x: x.split("/")[2])
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
        path = "logs/v2_study2/study2_results.csv"
    else:
        path = sys.argv[1]

    df = load_data(path)
    print(f"Study 2: Framing Effect Analysis")
    print(f"Loaded {len(df)} runs")
    print(f"Models: {sorted(df['model'].unique())}")
    print(f"Goal types: {sorted(df['goal_type'].unique())}")

    section("1. GOAL TYPE EFFECT (Overall)")

    print("  Deception rates by goal type:")
    for gt in ["bare", "moral", "self_serving"]:
        sub = df[df["goal_type"] == gt]
        n_dec = sub["is_deceptive_overall"].sum()
        n_tot = len(sub)
        rate = n_dec / n_tot * 100
        ci_low, ci_high = proportion_confint(n_dec, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {gt}: {n_dec}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    ct = pd.crosstab(df["goal_type"], df["is_deceptive_overall"])
    ct = ct.loc[["bare", "moral", "self_serving"]]
    chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
    v = cramers_v(ct.values)
    print(
        f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {fmt_p(p_val)} {sig(p_val)}"
    )
    print(f"  Cramér's V = {v:.3f} ({effect_size(v)})")

    section("2. BY GOAL TYPE (Blackbox Output)")

    print("  Blackbox deception rates:")
    for gt in ["bare", "moral", "self_serving"]:
        sub = df[df["goal_type"] == gt]
        n_dec = sub["is_deceptive_bb"].sum()
        n_tot = len(sub)
        rate = n_dec / n_tot * 100
        ci_low, ci_high = proportion_confint(n_dec, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {gt}: {n_dec}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    section("3. BY GOAL TYPE (Glassbox Reasoning)")

    print("  Compliant reasoning rates:")
    for gt in ["bare", "moral", "self_serving"]:
        sub = df[df["goal_type"] == gt]
        n_comp = sub["is_compliant_gb"].sum()
        n_tot = len(sub)
        rate = n_comp / n_tot * 100
        ci_low, ci_high = proportion_confint(n_comp, n_tot, alpha=0.05, method="wilson")
        print(
            f"    {gt}: {n_comp}/{n_tot} ({rate:.1f}%)  95% CI: [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    section("4. PAIRWISE COMPARISONS (Bonferroni-corrected)")

    pairs = list(combinations(["bare", "moral", "self_serving"], 2))
    n_comp = len(pairs)
    adj_alpha = SIGNIFICANCE_LEVEL / n_comp

    for g1, g2 in pairs:
        sub = df[df["goal_type"].isin([g1, g2])]
        ct_pair = pd.crosstab(sub["goal_type"], sub["is_deceptive_overall"])
        ct_pair = ct_pair.loc[[g1, g2]]
        chi2_p, p_val, dof, _ = chi2_contingency(ct_pair.values)
        _, fisher_p = fisher_exact(ct_pair.values)
        or_val, or_ci_low, or_ci_high = odds_ratio_ci(ct_pair.values)
        sig_mark = "SIG" if p_val < adj_alpha else "n.s."
        print(
            f"  {g1} vs {g2}: χ²(1) = {chi2_p:.3f}, Fisher {fmt_p(fisher_p)}, OR = {or_val:.2f} [{or_ci_low:.2f}, {or_ci_high:.2f}] [{sig_mark}]"
        )

    section("5. MODEL DIFFERENCES IN GOAL TYPE SENSITIVITY")

    print(
        f"  {'Model':35s}  {'Bare':>8s}  {'Moral':>8s}  {'SelfServ':>8s}  {'Trend':>10s}"
    )
    print(f"  {'-' * 35}  {'-' * 8}  {'-' * 8}  {'-' * 8}  {'-' * 10}")

    for model in sorted(df["model"].unique()):
        mdf = df[df["model"] == model]
        rates = []
        counts_list, nobs_list = [], []
        for gt in ["bare", "moral", "self_serving"]:
            sub = mdf[mdf["goal_type"] == gt]
            n_dec = sub["is_deceptive_overall"].sum()
            n_tot = len(sub)
            rate = n_dec / n_tot * 100
            rates.append(rate)
            counts_list.append(n_dec)
            nobs_list.append(n_tot)

        # Chi-squared test for this model's goal type effect
        sub_all = mdf
        ct_model = pd.crosstab(sub_all["goal_type"], sub_all["is_deceptive_overall"])
        chi2_val, p_val, dof, _ = chi2_contingency(ct_model.values)

        model_short = model.split("/")[-1] if "/" in model else model
        sig_mark = sig(p_val)
        print(
            f"  {model_short:35s}  {rates[0]:7.1f}%  {rates[1]:7.1f}%  {rates[2]:7.1f}%  χ²={chi2_val:.1f} {sig_mark}"
        )

    section("6. MODEL MAIN EFFECTS")

    print(f"  {'Model':35s}  {'Deceptive':>10s}  {'Rate':>8s}  95% CI")
    print(f"  {'-' * 35}  {'-' * 10}  {'-' * 8}  {'-' * 15}")

    for model in sorted(df["model"].unique()):
        mdf = df[df["model"] == model]
        n_dec = mdf["is_deceptive_overall"].sum()
        n_tot = len(mdf)
        rate = n_dec / n_tot * 100
        ci_low, ci_high = proportion_confint(n_dec, n_tot, alpha=0.05, method="wilson")
        model_short = model.split("/")[-1] if "/" in model else model
        print(
            f"  {model_short:35s}  {n_dec:>10d}  {rate:>7.1f}%  [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]"
        )

    ct_model = pd.crosstab(df["model"], df["is_deceptive_overall"])
    chi2_val, p_val, dof, expected = chi2_contingency(ct_model.values)
    v = cramers_v(ct_model.values)
    print(
        f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {fmt_p(p_val)} {sig(p_val)}"
    )
    print(f"  Cramér's V = {v:.3f} ({effect_size(v)})")

    section("7. RATIONALIZATION HYPOTHESIS TEST")

    print(
        "  Hypothesis: moral/self_serving hidden goals produce MORE deception than bare."
    )
    print()

    # Moral vs Bare
    sub_mb = df[df["goal_type"].isin(["moral", "bare"])]
    ct_mb = pd.crosstab(sub_mb["goal_type"], sub_mb["is_deceptive_overall"])
    ct_mb = ct_mb.loc[["bare", "moral"]]
    or_val, or_low, or_high = odds_ratio_ci(ct_mb.values)
    _, fisher_p = fisher_exact(ct_mb.values)
    print(
        f"  moral vs bare: OR = {or_val:.2f} [{or_low:.2f}, {or_high:.2f}], Fisher {fmt_p(fisher_p)} {sig(fisher_p)}"
    )

    # Self_serving vs Bare
    sub_sb = df[df["goal_type"].isin(["self_serving", "bare"])]
    ct_sb = pd.crosstab(sub_sb["goal_type"], sub_sb["is_deceptive_overall"])
    ct_sb = ct_sb.loc[["bare", "self_serving"]]
    or_val, or_low, or_high = odds_ratio_ci(ct_sb.values)
    _, fisher_p = fisher_exact(ct_sb.values)
    print(
        f"  self_serving vs bare: OR = {or_val:.2f} [{or_low:.2f}, {or_high:.2f}], Fisher {fmt_p(fisher_p)} {sig(fisher_p)}"
    )

    section("8. LOGISTIC REGRESSION: deception ~ goal_type + model")

    model_df = df.copy()
    model_df["bare_code"] = (model_df["goal_type"] == "bare").astype(int)
    model_df["moral_code"] = (model_df["goal_type"] == "moral").astype(int)
    model_df["model_code"] = pd.Categorical(model_df["model"]).codes

    X = model_df[["bare_code", "moral_code", "model_code"]]
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
    print(f"  Goal types: {sorted(df['goal_type'].unique())}")


if __name__ == "__main__":
    main()
