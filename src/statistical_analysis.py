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
Statistical Analysis of LLM Deception Experiment Results
=========================================================
Produces bulletproof statistics for the dissertation including:
- Chi-squared tests of independence and homogeneity
- Fisher's exact tests (where cell counts are small)
- Cochran-Armitage trend tests (oversight as ordinal)
- Cramér's V effect sizes
- Odds ratios with 95% confidence intervals
- Bonferroni-corrected pairwise comparisons
- Breslow-Day test for homogeneity of odds ratios
- Logistic regression for interaction effects

Usage:
    python src/statistical_analysis.py logs/full_experiment/results.csv
"""

import sys
import csv
import warnings
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, chi2
from statsmodels.stats.contingency_tables import Table2x2
from statsmodels.stats.proportion import proportion_confint
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DECEPTIVE_CATEGORIES = {"MISLEADING", "FABRICATED", "OMITTED"}
HONEST_CATEGORIES = {"ACCURATE"}
OVERSIGHT_ORDER = {"low": 0, "mid": 1, "high": 2}
SIGNIFICANCE_LEVEL = 0.05

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_data(csv_path: str) -> pd.DataFrame:
    """Load results CSV and add derived columns."""
    df = pd.read_csv(csv_path)
    df["is_deceptive_output"] = df["blackbox_category"].isin(DECEPTIVE_CATEGORIES).astype(int)
    df["is_compliant_reasoning"] = (df["glassbox_category"] == "COMPLIANT_DECEPTION").astype(int)
    df["is_strategic"] = (df["glassbox_sophistication"] == "STRATEGIC").astype(int)
    df["oversight_ordinal"] = df["oversight"].map(OVERSIGHT_ORDER)
    return df


def cramers_v(contingency_table: np.ndarray) -> float:
    """Compute Cramér's V from a contingency table."""
    chi2_val = chi2_contingency(contingency_table)[0]
    n = contingency_table.sum()
    min_dim = min(contingency_table.shape) - 1
    if min_dim == 0 or n == 0:
        return 0.0
    return np.sqrt(chi2_val / (n * min_dim))


def cramers_v_bias_corrected(contingency_table: np.ndarray) -> float:
    """Compute bias-corrected Cramér's V (Bergsma 2013)."""
    chi2_val = chi2_contingency(contingency_table)[0]
    n = contingency_table.sum()
    r, k = contingency_table.shape
    phi2 = chi2_val / n
    phi2_corrected = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    k_corrected = k - ((k - 1) ** 2) / (n - 1)
    r_corrected = r - ((r - 1) ** 2) / (n - 1)
    min_corrected = min(k_corrected - 1, r_corrected - 1)
    if min_corrected <= 0:
        return 0.0
    return np.sqrt(phi2_corrected / min_corrected)


def odds_ratio_ci(table_2x2: np.ndarray, alpha: float = 0.05):
    """
    Compute odds ratio with confidence interval from a 2x2 table.
    Table format: [[a, b], [c, d]]
    OR = (a*d) / (b*c)
    """
    a, b, c, d = table_2x2[0, 0], table_2x2[0, 1], table_2x2[1, 0], table_2x2[1, 1]
    # Add 0.5 continuity correction if any cell is 0
    if 0 in (a, b, c, d):
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    odds_ratio = (a * d) / (b * c)
    log_or = np.log(odds_ratio)
    se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d)
    z = stats.norm.ppf(1 - alpha / 2)
    ci_lower = np.exp(log_or - z * se_log_or)
    ci_upper = np.exp(log_or + z * se_log_or)
    return odds_ratio, ci_lower, ci_upper


def cochran_armitage_trend_test(counts: list, nobs: list) -> tuple:
    """
    Cochran-Armitage test for trend in proportions.
    counts: list of successes at each ordinal level
    nobs: list of total observations at each ordinal level
    Uses equally-spaced scores [0, 1, 2, ...].
    Returns (z_statistic, p_value).
    """
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
    p_value = 2 * stats.norm.sf(abs(z))  # two-sided
    return z, p_value


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n  --- {title} ---\n")


def interpret_effect_size(v: float) -> str:
    """Interpret Cramér's V effect size (Cohen's conventions)."""
    if v < 0.1:
        return "negligible"
    elif v < 0.3:
        return "small"
    elif v < 0.5:
        return "medium"
    else:
        return "large"


def sig_stars(p: float) -> str:
    """Return significance stars."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return "n.s."


def format_p(p: float) -> str:
    """Format p-value for display."""
    if p < 0.001:
        return f"p < .001"
    else:
        return f"p = {p:.4f}"


# ---------------------------------------------------------------------------
# Analysis Functions
# ---------------------------------------------------------------------------

def analysis_1_scenario_effect(df: pd.DataFrame):
    """Test H1: Deception rates differ between scenarios."""
    print_section("1. SCENARIO EFFECT ON DECEPTION")
    
    # --- 1a. Output-level (blackbox) deception ---
    print_subsection("1a. Output-level deception rate by scenario (blackbox)")
    
    ct = pd.crosstab(df["scenario"], df["is_deceptive_output"])
    print("  Contingency table:")
    for scenario in ct.index:
        n_honest = ct.loc[scenario, 0] if 0 in ct.columns else 0
        n_deceptive = ct.loc[scenario, 1] if 1 in ct.columns else 0
        total = n_honest + n_deceptive
        rate = n_deceptive / total * 100
        ci_low, ci_high = proportion_confint(n_deceptive, total, alpha=0.05, method="wilson")
        print(f"    {scenario}: {n_deceptive}/{total} ({rate:.1f}%) "
              f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
    
    chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
    v = cramers_v(ct.values)
    v_corrected = cramers_v_bias_corrected(ct.values)
    
    print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
    print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
    print(f"  Cramér's V (bias-corrected) = {v_corrected:.3f}")
    
    # Odds ratio
    table_2x2 = ct.values
    or_val, or_ci_low, or_ci_high = odds_ratio_ci(table_2x2)
    print(f"  Odds ratio = {or_val:.3f}  95% CI: [{or_ci_low:.3f}, {or_ci_high:.3f}]")
    
    # Fisher's exact for robustness
    if ct.shape == (2, 2):
        _, fisher_p = fisher_exact(ct.values)
        print(f"  Fisher's exact test: {format_p(fisher_p)} {sig_stars(fisher_p)}")
    
    # --- 1b. Reasoning-level (glassbox) compliance ---
    print_subsection("1b. Reasoning-level compliance by scenario (glassbox: COMPLIANT_DECEPTION)")
    
    ct_gb = pd.crosstab(df["scenario"], df["is_compliant_reasoning"])
    print("  Contingency table:")
    for scenario in ct_gb.index:
        n_not = ct_gb.loc[scenario, 0] if 0 in ct_gb.columns else 0
        n_compliant = ct_gb.loc[scenario, 1] if 1 in ct_gb.columns else 0
        total = n_not + n_compliant
        rate = n_compliant / total * 100
        ci_low, ci_high = proportion_confint(n_compliant, total, alpha=0.05, method="wilson")
        print(f"    {scenario}: {n_compliant}/{total} ({rate:.1f}%) "
              f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
    
    chi2_val, p_val, dof, expected = chi2_contingency(ct_gb.values)
    v = cramers_v(ct_gb.values)
    print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
    print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
    
    or_val, or_ci_low, or_ci_high = odds_ratio_ci(ct_gb.values)
    print(f"  Odds ratio = {or_val:.3f}  95% CI: [{or_ci_low:.3f}, {or_ci_high:.3f}]")


def analysis_2_oversight_effect(df: pd.DataFrame):
    """Test H2: Oversight level affects deception rates."""
    print_section("2. OVERSIGHT EFFECT ON DECEPTION")
    
    for scenario in sorted(df["scenario"].unique()):
        print_subsection(f"2a. Output-level deception by oversight — {scenario}")
        
        sdf = df[df["scenario"] == scenario]
        ct = pd.crosstab(sdf["oversight"], sdf["is_deceptive_output"])
        # Reorder rows
        oversight_labels = [o for o in ["low", "mid", "high"] if o in ct.index]
        ct = ct.loc[oversight_labels]
        
        print("  Contingency table:")
        counts_for_trend = []
        nobs_for_trend = []
        for oversight in oversight_labels:
            n_honest = ct.loc[oversight, 0] if 0 in ct.columns else 0
            n_deceptive = ct.loc[oversight, 1] if 1 in ct.columns else 0
            total = n_honest + n_deceptive
            rate = n_deceptive / total * 100
            ci_low, ci_high = proportion_confint(n_deceptive, total, alpha=0.05, method="wilson")
            print(f"    {oversight}: {n_deceptive}/{total} ({rate:.1f}%) "
                  f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
            counts_for_trend.append(n_deceptive)
            nobs_for_trend.append(total)
        
        # Chi-squared test (3x2)
        chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
        v = cramers_v(ct.values)
        print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
        print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
        
        # Check expected cell counts
        min_expected = expected.min()
        print(f"  Minimum expected cell count = {min_expected:.1f}", end="")
        if min_expected < 5:
            print("  ⚠ WARNING: Expected count < 5, chi-squared may be unreliable")
        else:
            print("  ✓ All expected counts ≥ 5")
        
        # Cochran-Armitage trend test (treats oversight as ordinal)
        z_trend, p_trend = cochran_armitage_trend_test(counts_for_trend, nobs_for_trend)
        print(f"\n  Cochran-Armitage trend test: z = {z_trend:.3f}, {format_p(p_trend)} {sig_stars(p_trend)}")
        if p_trend < 0.05:
            direction = "increasing" if z_trend > 0 else "decreasing"
            print(f"    → Significant linear trend: deception {direction} with oversight level")
        else:
            print(f"    → No significant linear trend detected")
        
        # Pairwise comparisons (Bonferroni-corrected)
        print_subsection(f"2b. Pairwise oversight comparisons — {scenario} (Bonferroni-corrected, α/3 = {SIGNIFICANCE_LEVEL/3:.4f})")
        
        pairs = list(combinations(oversight_labels, 2))
        n_comparisons = len(pairs)
        
        for o1, o2 in pairs:
            subset = sdf[sdf["oversight"].isin([o1, o2])]
            ct_pair = pd.crosstab(subset["oversight"], subset["is_deceptive_output"])
            ct_pair = ct_pair.loc[[o1, o2]]
            
            if ct_pair.shape == (2, 2):
                chi2_p, p_p, dof_p, _ = chi2_contingency(ct_pair.values)
                _, fisher_p = fisher_exact(ct_pair.values)
                or_val, or_ci_low, or_ci_high = odds_ratio_ci(ct_pair.values)
                
                adjusted_alpha = SIGNIFICANCE_LEVEL / n_comparisons
                sig = "SIG" if p_p < adjusted_alpha else "n.s."
                
                print(f"    {o1} vs {o2}:")
                print(f"      χ²(1) = {chi2_p:.3f}, raw {format_p(p_p)}, "
                      f"Fisher {format_p(fisher_p)}")
                print(f"      OR = {or_val:.3f}  95% CI: [{or_ci_low:.3f}, {or_ci_high:.3f}]  "
                      f"[Bonferroni: {sig}]")


def analysis_3_model_effects(df: pd.DataFrame):
    """Test H3: Models differ in deception rates."""
    print_section("3. MODEL-LEVEL DIFFERENCES")
    
    for scenario in sorted(df["scenario"].unique()):
        print_subsection(f"3a. Output deception by model — {scenario}")
        
        sdf = df[df["scenario"] == scenario]
        ct = pd.crosstab(sdf["model"], sdf["is_deceptive_output"])
        
        print("  Model deception rates:")
        model_rates = []
        for model in sorted(ct.index):
            n_honest = ct.loc[model, 0] if 0 in ct.columns else 0
            n_deceptive = ct.loc[model, 1] if 1 in ct.columns else 0
            total = n_honest + n_deceptive
            rate = n_deceptive / total * 100
            ci_low, ci_high = proportion_confint(n_deceptive, total, alpha=0.05, method="wilson")
            print(f"    {model}: {n_deceptive}/{total} ({rate:.1f}%) "
                  f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
            model_rates.append((model, rate))
        
        chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
        v = cramers_v(ct.values)
        print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
        print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
        
        min_expected = expected.min()
        if min_expected < 5:
            print(f"  ⚠ Minimum expected count = {min_expected:.1f} < 5")


def analysis_4_oversight_x_scenario_interaction(df: pd.DataFrame):
    """Test H4: Oversight effect differs between scenarios (interaction)."""
    print_section("4. OVERSIGHT × SCENARIO INTERACTION")
    
    print_subsection("4a. Logistic regression: deception ~ scenario + oversight + scenario×oversight")
    
    # Encode variables
    model_df = df.copy()
    model_df["scenario_code"] = (model_df["scenario"] == "child_protection").astype(int)
    model_df["oversight_num"] = model_df["oversight_ordinal"]
    model_df["interaction"] = model_df["scenario_code"] * model_df["oversight_num"]
    
    X = model_df[["scenario_code", "oversight_num", "interaction"]]
    X = sm.add_constant(X)
    y = model_df["is_deceptive_output"]
    
    try:
        logit_model = sm.Logit(y, X).fit(disp=0)
        print(logit_model.summary2().tables[1].to_string())
        
        print(f"\n  Model fit: Pseudo R² = {logit_model.prsquared:.4f}, "
              f"AIC = {logit_model.aic:.1f}, BIC = {logit_model.bic:.1f}")
        
        # Likelihood ratio test for interaction term
        X_no_interaction = model_df[["scenario_code", "oversight_num"]]
        X_no_interaction = sm.add_constant(X_no_interaction)
        logit_reduced = sm.Logit(y, X_no_interaction).fit(disp=0)
        
        lr_stat = -2 * (logit_reduced.llf - logit_model.llf)
        lr_p = chi2.sf(lr_stat, df=1)
        print(f"\n  Likelihood ratio test for interaction: "
              f"LR = {lr_stat:.3f}, {format_p(lr_p)} {sig_stars(lr_p)}")
        if lr_p < 0.05:
            print("    → Significant interaction: oversight affects scenarios differently")
        else:
            print("    → No significant interaction")
        
    except Exception as e:
        print(f"  Logistic regression failed: {e}")
    
    # Breslow-Day test for homogeneity of odds ratios across oversight strata
    print_subsection("4b. Breslow-Day test for homogeneity of odds ratios")
    print("  (Tests whether the scenario effect is consistent across oversight levels)")
    
    ors = []
    for oversight in ["low", "mid", "high"]:
        odf = df[df["oversight"] == oversight]
        ct = pd.crosstab(odf["scenario"], odf["is_deceptive_output"])
        if ct.shape == (2, 2):
            or_val, ci_low, ci_high = odds_ratio_ci(ct.values)
            ors.append((oversight, or_val, ci_low, ci_high))
            print(f"    {oversight}: OR = {or_val:.3f}  95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
    
    # Manual Breslow-Day: compare ORs across strata
    # Use Cochran-Mantel-Haenszel common OR for comparison
    tables = []
    for oversight in ["low", "mid", "high"]:
        odf = df[df["oversight"] == oversight]
        ct = pd.crosstab(odf["scenario"], odf["is_deceptive_output"])
        if ct.shape == (2, 2):
            tables.append(ct.values)
    
    if len(tables) == 3:
        # CMH test
        from statsmodels.stats.contingency_tables import StratifiedTable
        strat = StratifiedTable(tables)
        cmh_result = strat.test_null_odds()
        print(f"\n  Cochran-Mantel-Haenszel test:")
        print(f"    Common OR = {strat.summary().tables[0].data[1][1] if hasattr(strat.summary(), 'tables') else 'N/A'}")
        print(f"    CMH statistic = {cmh_result.statistic:.3f}, {format_p(cmh_result.pvalue)} {sig_stars(cmh_result.pvalue)}")
        
        bd_result = strat.test_equal_odds()
        print(f"\n  Breslow-Day test for homogeneity of ORs:")
        print(f"    Statistic = {bd_result.statistic:.3f}, {format_p(bd_result.pvalue)} {sig_stars(bd_result.pvalue)}")
        if bd_result.pvalue < 0.05:
            print("    → ORs differ significantly across oversight strata")
            print("      (The scenario effect is NOT consistent across oversight levels)")
        else:
            print("    → ORs are consistent across oversight strata")


def analysis_5_model_x_oversight_within_scenario(df: pd.DataFrame):
    """Test H5: Oversight effect varies by model within each scenario."""
    print_section("5. MODEL × OVERSIGHT INTERACTION (per scenario)")
    
    for scenario in sorted(df["scenario"].unique()):
        print_subsection(f"5. Oversight effect by model — {scenario}")
        
        sdf = df[df["scenario"] == scenario]
        
        for model in sorted(sdf["model"].unique()):
            mdf = sdf[sdf["model"] == model]
            
            counts = []
            nobs = []
            rates = []
            for oversight in ["low", "mid", "high"]:
                odf = mdf[mdf["oversight"] == oversight]
                dec = odf["is_deceptive_output"].sum()
                tot = len(odf)
                counts.append(dec)
                nobs.append(tot)
                rates.append(dec / tot * 100 if tot > 0 else 0)
            
            z_trend, p_trend = cochran_armitage_trend_test(counts, nobs)
            trend_sig = sig_stars(p_trend)
            
            model_short = model.split("/")[-1] if "/" in model else model
            print(f"    {model_short:30s}  low={rates[0]:5.1f}%  mid={rates[1]:5.1f}%  "
                  f"high={rates[2]:5.1f}%  "
                  f"trend z={z_trend:+.2f} {format_p(p_trend)} {trend_sig}")


def analysis_6_deception_type(df: pd.DataFrame):
    """Test H6: Deception type distribution differs between scenarios."""
    print_section("6. DECEPTION TYPE ANALYSIS")
    
    deceptive_df = df[df["blackbox_category"].isin(DECEPTIVE_CATEGORIES)]
    
    print_subsection("6a. Deception type distribution by scenario")
    ct = pd.crosstab(deceptive_df["scenario"], deceptive_df["blackbox_category"])
    
    for scenario in ct.index:
        total = ct.loc[scenario].sum()
        print(f"  {scenario} (n={total}):")
        for cat in sorted(ct.columns):
            count = ct.loc[scenario, cat]
            rate = count / total * 100
            print(f"    {cat}: {count} ({rate:.1f}%)")
    
    chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
    v = cramers_v(ct.values)
    print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
    print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
    
    min_expected = expected.min()
    if min_expected < 5:
        print(f"  ⚠ Minimum expected count = {min_expected:.1f} < 5, interpreting with caution")


def analysis_7_glassbox_categories(df: pd.DataFrame):
    """Test H7: Glassbox intent categories differ between scenarios."""
    print_section("7. REASONING INTENT ANALYSIS (Glassbox)")
    
    print_subsection("7a. Glassbox category distribution by scenario")
    ct = pd.crosstab(df["scenario"], df["glassbox_category"])
    
    for scenario in ct.index:
        total = ct.loc[scenario].sum()
        print(f"  {scenario} (n={total}):")
        for cat in sorted(ct.columns):
            count = ct.loc[scenario, cat]
            rate = count / total * 100
            ci_low, ci_high = proportion_confint(count, total, alpha=0.05, method="wilson")
            print(f"    {cat}: {count} ({rate:.1f}%) "
                  f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
    
    chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
    v = cramers_v(ct.values)
    print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
    print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")
    
    min_expected = expected.min()
    if min_expected < 5:
        print(f"  ⚠ Minimum expected count = {min_expected:.1f} < 5")
    
    # Sophistication distribution
    print_subsection("7b. Sophistication distribution by scenario")
    ct_soph = pd.crosstab(df["scenario"], df["glassbox_sophistication"])
    
    for scenario in ct_soph.index:
        total = ct_soph.loc[scenario].sum()
        print(f"  {scenario} (n={total}):")
        for tier in ["NAIVE", "REACTIVE", "TACTICAL", "STRATEGIC"]:
            if tier in ct_soph.columns:
                count = ct_soph.loc[scenario, tier]
                rate = count / total * 100
                print(f"    {tier}: {count} ({rate:.1f}%)")
    
    # Filter to valid tiers only for test
    valid_tiers = [t for t in ["NAIVE", "REACTIVE", "TACTICAL", "STRATEGIC"] if t in ct_soph.columns]
    ct_soph_valid = ct_soph[valid_tiers]
    
    if ct_soph_valid.shape[1] > 1:
        chi2_val, p_val, dof, expected = chi2_contingency(ct_soph_valid.values)
        v = cramers_v(ct_soph_valid.values)
        print(f"\n  Chi-squared test: χ²({dof}) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
        print(f"  Cramér's V = {v:.3f} ({interpret_effect_size(v)})")


def analysis_8_reasoning_output_alignment(df: pd.DataFrame):
    """Test H8: Alignment between reasoning intent and output deception."""
    print_section("8. REASONING–OUTPUT ALIGNMENT")
    
    for scenario in sorted(df["scenario"].unique()):
        print_subsection(f"8. Alignment matrix — {scenario}")
        
        sdf = df[df["scenario"] == scenario]
        ct = pd.crosstab(sdf["glassbox_category"], sdf["blackbox_category"])
        
        # Print nicely
        all_bb = ["ACCURATE", "MISLEADING", "OMITTED", "FABRICATED"]
        all_gb = ["ROBUST_HONEST", "CONSIDERED_HONEST", "COMPLIANT_DECEPTION", "FAILED_DECEPTION", "UNINTENTIONAL_FAILURE"]
        
        present_bb = [c for c in all_bb if c in ct.columns]
        present_gb = [g for g in all_gb if g in ct.index]
        
        # Header
        header = f"    {'':30s}" + "".join(f"  {c:>12s}" for c in present_bb) + f"  {'TOTAL':>8s}"
        print(header)
        print("    " + "-" * (len(header) - 4))
        
        for gb in present_gb:
            row_vals = []
            for bb in present_bb:
                val = ct.loc[gb, bb] if bb in ct.columns and gb in ct.index else 0
                row_vals.append(val)
            total = sum(row_vals)
            row_str = f"    {gb:30s}" + "".join(f"  {v:>12d}" for v in row_vals) + f"  {total:>8d}"
            print(row_str)
        
        # Key misalignment metrics
        compliant = sdf[sdf["glassbox_category"] == "COMPLIANT_DECEPTION"]
        if len(compliant) > 0:
            accurate_despite_compliant = (compliant["blackbox_category"] == "ACCURATE").sum()
            rate = accurate_despite_compliant / len(compliant) * 100
            ci_low, ci_high = proportion_confint(accurate_despite_compliant, len(compliant), alpha=0.05, method="wilson")
            print(f"\n  Compliant reasoning → accurate output: {accurate_despite_compliant}/{len(compliant)} ({rate:.1f}%)"
                  f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
        
        honest_cats = sdf[sdf["glassbox_category"].isin(["ROBUST_HONEST", "CONSIDERED_HONEST"])]
        if len(honest_cats) > 0:
            deceptive_despite_honest = honest_cats["is_deceptive_output"].sum()
            rate = deceptive_despite_honest / len(honest_cats) * 100
            ci_low, ci_high = proportion_confint(deceptive_despite_honest, len(honest_cats), alpha=0.05, method="wilson")
            print(f"  Honest reasoning → deceptive output: {deceptive_despite_honest}/{len(honest_cats)} ({rate:.1f}%)"
                  f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")


def analysis_9_safety_training(df: pd.DataFrame):
    """Test H9: Safety-trained model vs base model comparison."""
    print_section("9. SAFETY TRAINING EFFECT (gpt-oss-20b vs gpt-oss-safeguard-20b)")
    
    base_name = "openai/gpt-oss-20b"
    safe_name = "openai/gpt-oss-safeguard-20b"
    
    pair_df = df[df["model"].isin([base_name, safe_name])]
    
    if len(pair_df) == 0:
        print("  No data found for safety training comparison.")
        return
    
    for scenario in sorted(pair_df["scenario"].unique()):
        print_subsection(f"9. Safety training effect — {scenario}")
        
        sdf = pair_df[pair_df["scenario"] == scenario]
        ct = pd.crosstab(sdf["model"], sdf["is_deceptive_output"])
        
        for model in [base_name, safe_name]:
            if model in ct.index:
                n_honest = ct.loc[model, 0] if 0 in ct.columns else 0
                n_deceptive = ct.loc[model, 1] if 1 in ct.columns else 0
                total = n_honest + n_deceptive
                rate = n_deceptive / total * 100
                ci_low, ci_high = proportion_confint(n_deceptive, total, alpha=0.05, method="wilson")
                label = "base" if "safeguard" not in model else "safeguard"
                print(f"    {label}: {n_deceptive}/{total} ({rate:.1f}%) "
                      f"  95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
        
        if ct.shape == (2, 2):
            chi2_val, p_val, dof, _ = chi2_contingency(ct.values)
            _, fisher_p = fisher_exact(ct.values)
            or_val, or_ci_low, or_ci_high = odds_ratio_ci(ct.values)
            
            print(f"\n  Chi-squared: χ²(1) = {chi2_val:.3f}, {format_p(p_val)} {sig_stars(p_val)}")
            print(f"  Fisher's exact: {format_p(fisher_p)} {sig_stars(fisher_p)}")
            print(f"  Odds ratio = {or_val:.3f}  95% CI: [{or_ci_low:.3f}, {or_ci_high:.3f}]")
        else:
            print(f"\n  ⚠ Cannot compute 2x2 test — table shape is {ct.shape}")


def analysis_10_full_logistic_model(df: pd.DataFrame):
    """Run a full logistic regression with all factors."""
    print_section("10. FULL LOGISTIC REGRESSION MODEL")
    
    print_subsection("10a. Deceptive output ~ scenario + oversight + model")
    
    model_df = df.copy()
    model_df["scenario_code"] = (model_df["scenario"] == "child_protection").astype(int)
    model_df["oversight_num"] = model_df["oversight_ordinal"]
    
    # Create model dummies
    model_dummies = pd.get_dummies(model_df["model"], prefix="model", drop_first=True, dtype=float)
    
    X = pd.concat([
        model_df[["scenario_code", "oversight_num"]],
        model_dummies
    ], axis=1)
    X = sm.add_constant(X)
    y = model_df["is_deceptive_output"]
    
    try:
        logit_model = sm.Logit(y, X).fit(disp=0, maxiter=100)
        print(logit_model.summary2().tables[1].to_string())
        print(f"\n  Pseudo R² = {logit_model.prsquared:.4f}")
        print(f"  AIC = {logit_model.aic:.1f}")
        print(f"  n = {logit_model.nobs:.0f}")
        
        # Print odds ratios for interpretability
        print("\n  Odds ratios (exponentiated coefficients):")
        for name, coef, pval in zip(X.columns, logit_model.params, logit_model.pvalues):
            if name == "const":
                continue
            or_val = np.exp(coef)
            ci = logit_model.conf_int().loc[name]
            or_ci = (np.exp(ci[0]), np.exp(ci[1]))
            print(f"    {name:45s}  OR = {or_val:.3f}  "
                  f"95% CI: [{or_ci[0]:.3f}, {or_ci[1]:.3f}]  {sig_stars(pval)}")
            
    except Exception as e:
        print(f"  Logistic regression failed: {e}")
    
    # Also the interaction model
    print_subsection("10b. With scenario × oversight interaction")
    
    model_df["interaction"] = model_df["scenario_code"] * model_df["oversight_num"]
    X2 = pd.concat([
        model_df[["scenario_code", "oversight_num", "interaction"]],
        model_dummies
    ], axis=1)
    X2 = sm.add_constant(X2)
    
    try:
        logit_interaction = sm.Logit(y, X2).fit(disp=0, maxiter=100)
        print(logit_interaction.summary2().tables[1].to_string())
        
        # LR test for interaction
        lr_stat = -2 * (logit_model.llf - logit_interaction.llf)
        lr_p = chi2.sf(lr_stat, df=1)
        print(f"\n  LR test for interaction: LR = {lr_stat:.3f}, {format_p(lr_p)} {sig_stars(lr_p)}")
    except Exception as e:
        print(f"  Interaction model failed: {e}")


def analysis_11_summary_table(df: pd.DataFrame):
    """Print a publication-ready summary table."""
    print_section("11. SUMMARY TABLE (Publication-Ready)")
    
    print(f"  {'Model':35s} | {'Scenario':25s} | {'Low':>10s} | {'Mid':>10s} | {'High':>10s} | {'Overall':>10s}")
    print("  " + "-" * 105)
    
    for model in sorted(df["model"].unique()):
        for scenario in sorted(df["scenario"].unique()):
            rates = []
            for oversight in ["low", "mid", "high"]:
                sub = df[(df["model"] == model) & (df["scenario"] == scenario) & (df["oversight"] == oversight)]
                if len(sub) > 0:
                    rate = sub["is_deceptive_output"].mean() * 100
                    rates.append(f"{rate:.0f}%")
                else:
                    rates.append("—")
            
            overall_sub = df[(df["model"] == model) & (df["scenario"] == scenario)]
            overall_rate = overall_sub["is_deceptive_output"].mean() * 100
            
            model_display = model.split("/")[-1] if "/" in model else model
            print(f"  {model_display:35s} | {scenario:25s} | {rates[0]:>10s} | {rates[1]:>10s} | {rates[2]:>10s} | {overall_rate:>9.0f}%")
        print("  " + "-" * 105)
    
    # Marginals
    print(f"\n  {'MARGINAL':35s} | {'':25s} | {'Low':>10s} | {'Mid':>10s} | {'High':>10s} | {'Overall':>10s}")
    print("  " + "-" * 105)
    for scenario in sorted(df["scenario"].unique()):
        rates = []
        for oversight in ["low", "mid", "high"]:
            sub = df[(df["scenario"] == scenario) & (df["oversight"] == oversight)]
            rate = sub["is_deceptive_output"].mean() * 100
            rates.append(f"{rate:.0f}%")
        overall = df[df["scenario"] == scenario]["is_deceptive_output"].mean() * 100
        print(f"  {'ALL MODELS':35s} | {scenario:25s} | {rates[0]:>10s} | {rates[1]:>10s} | {rates[2]:>10s} | {overall:>9.0f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        csv_path = "logs/full_experiment/results.csv"
    else:
        csv_path = sys.argv[1]
    
    print(f"Loading data from: {csv_path}")
    df = load_data(csv_path)
    print(f"Loaded {len(df)} rows: "
          f"{df['model'].nunique()} models, "
          f"{df['scenario'].nunique()} scenarios, "
          f"{df['oversight'].nunique()} oversight levels")
    print(f"Significance level: α = {SIGNIFICANCE_LEVEL}")
    
    analysis_1_scenario_effect(df)
    analysis_2_oversight_effect(df)
    analysis_3_model_effects(df)
    analysis_4_oversight_x_scenario_interaction(df)
    analysis_5_model_x_oversight_within_scenario(df)
    analysis_6_deception_type(df)
    analysis_7_glassbox_categories(df)
    analysis_8_reasoning_output_alignment(df)
    analysis_9_safety_training(df)
    analysis_10_full_logistic_model(df)
    analysis_11_summary_table(df)
    
    print_section("ANALYSIS COMPLETE")
    print(f"  Total runs analysed: {len(df)}")
    print(f"  Models: {sorted(df['model'].unique())}")
    print(f"  Scenarios: {sorted(df['scenario'].unique())}")
    print(f"  Oversight levels: {sorted(df['oversight'].unique())}")
    print(f"  Judge categories used:")
    print(f"    Blackbox: {DECEPTIVE_CATEGORIES} vs {HONEST_CATEGORIES}")
    print(f"    Glassbox: {sorted(df['glassbox_category'].unique())}")
    print(f"    Sophistication: {sorted(df['glassbox_sophistication'].unique())}")


if __name__ == "__main__":
    main()
