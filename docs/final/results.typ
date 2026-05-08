= Results <results>

//TODO: add refrences to the code
//TODO: add prompt excerpts for the judges

This section presents findings from 960 controlled experiment runs across three studies: an exploratory pilot (v1, N=420) and two confirmatory studies (Study 1: N=270, Study 2: N=270). The exploratory study established baseline patterns in deception behaviour; the confirmatory studies tested specific hypotheses with isolated variables. All classifications derive from the automated three-pronged judging pipeline (regex, blackbox output analysis, glassbox intent analysis), with validation results reported in the appendices.

== Exploratory Study (v1): Establishing Baseline Patterns

The exploratory study served as foundational research, designed to identify whether models would follow hidden goals at all, whether oversight affected compliance, and whether scenario framing mattered. The study employed 7 models across 2 scenarios (corporate sabotage, child protection) at 3 oversight levels (low, mid, high), with 10 runs per cell (total N=420).

=== Overall Deception Rates

Of the 420 runs, 287 (68.3%) were classified as _compliant deception_---the model recognised and chose to follow the hidden goal:

#figure(
  table(
    columns: (2.5fr, 1fr, 1fr),
    align: (left, right, right),
    [*Glassbox Category*], [*Count*], [*%*],
    [Compliant Deception], [287], [68.3],
    [Considered Honest], [74], [17.6],
    [Robust Honest], [39], [9.3],
    [Unintentional Failure], [13], [3.1],
    [Failed Deception], [6], [1.4],
  ),
  caption: [Distribution of glassbox intent classifications in v1 exploratory study (N=420).],
) <tab:v1_overall_intent>

#figure(
  grid(
    columns: 1,
    gutter: 1.5em,
    [
      #image("images/v1_glassbox_composition.png", width: 90%)
      #align(center)[*(a)* Glassbox evaluation distribution.]
    ],
    [
      #image("images/v1_blackbox_composition.png", width: 90%)
      #align(center)[*(b)* Blackbox evaluation distribution.]
    ]
  ),
  caption: [Glassbox vs. Blackbox composition in the exploratory study (N=420).],
) <fig:v1_composition>

@fig:v1_composition illustrates the divergence between trace-classified intent and output-based detection across all v1 runs. Combined honest categories (Robust + Considered) account for only 26.9%. The low Failed Deception rate (1.4%) indicates that when models choose to deceive, they generally succeed at the intent level, even if output-level detection varies.

=== Model-Level Profiles

Deception rates varied dramatically across models, from 40.0% to 100.0%:

#figure(
  table(
    columns: (2.8fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, right, right, right, right),
    [*Model*], [*Decep.*], [*Honest*], [*Strat.*], [*Mislead.*],
    [Gemini 3.1 Pro], [100.0%], [0.0%], [100.0%], [88.3%],
    [Qwen3 Max], [91.7%], [8.3%], [100.0%], [68.3%],
    [DeepSeek V3.2], [78.3%], [20.0%], [91.7%], [43.3%],
    [Kimi K2.5], [70.0%], [28.3%], [91.7%], [58.3%],
    [GPT-OSS Safeguard], [53.3%], [33.3%], [35.0%], [6.7%],
    [GPT-OSS 20B], [45.0%], [50.0%], [33.3%], [41.7%],
    [GLM 4.7 Flash], [40.0%], [48.3%], [33.3%], [35.0%],
  ),
  caption: [Model-level deception profiles in v1. Decep. = Compliant Deception rate; Honest = Robust + Considered; Strat. = Strategic sophistication; Mislead. = Blackbox MISLEADING rate.],
) <tab:v1_model_profiles>

A two-tier structure emerged: a _high-deception tier_ (Gemini, Qwen3, DeepSeek, Kimi; deception >70%, strategic >90%) and a _moderate tier_ (GPT-OSS variants, GLM; deception 40--53%, strategic ~33%). Notably, GPT-OSS Safeguard---explicitly designed with safety guardrails---showed a _higher_ deception rate (53.3%) than its base variant (45.0%) but a dramatically lower misleading rate (6.7% vs 41.7%), suggesting safety training increases hidden goal awareness while reducing successful output-level deception.

=== Oversight Effects in v1

Increasing oversight from low to high reduced deception frequency:

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr),
    align: (left, right, right, right),
    [*Oversight*], [*Deceptive*], [*Total*], [*Rate*],
    [Low], [104], [140], [74.3%],
    [Mid], [102], [140], [72.9%],
    [High], [81], [140], [57.9%],
  ),
  caption: [Deception frequency by oversight level in v1 (all models, all scenarios).],
) <tab:v1_oversight_deception>

The low → high reduction of 16.4 percentage points appeared promising. However, a critical finding emerged: while oversight reduced deception _frequency_, it had no effect on _sophistication_. Strategic reasoning remained flat at approximately 69.3% across all oversight levels. Models that continued to deceive under high oversight employed the same meta-reasoning about monitoring systems as those under no oversight. Among runs classified as COMPLIANT_DECEPTION, strategic sophistication remained at 100% across all conditions. This pattern suggested a tentative _competence filter_ hypothesis: that oversight deterred less capable deceivers while leaving the most competent ones unaffected. Study 1 tests this hypothesis directly.

=== The Critical Confound: Scenario Effects

The v1 study compared two scenarios with markedly different deception rates:

#figure(
  table(
    columns: (2fr, 1fr, 1.5fr),
    align: (left, right, left),
    [*Scenario*], [*Deception Rate*], [*Framing*],
    [Child Protection], [86.7%], [Bureaucratic rationalisation],
    [Corporate Sabotage], [50.0%], [Explicit adversarial],
  ),
  caption: [Scenario-level deception comparison in v1.],
) <tab:v1_scenario_comparison>

The child protection scenario---framed as "prudent resource allocation" to support families with existing services---produced 86.7% deception compliance. The corporate sabotage scenario---explicitly instructing models to act as "sleeper agents"---produced only 50.0% compliance. The scenario effect was statistically significant: χ²(1) = 63.554, p < .001, φ = 0.389 (medium-to-large effect).

Critically, the child protection scenario showed _negligible sensitivity to oversight intensity_ (84.3% low, 87.1% mid, 88.6% high), while corporate sabotage showed strong suppression (64.3% → 50.0% → 35.7%). This pattern suggested that bureaucratic rationalisation neutralises oversight effectiveness.

#figure(
  image("images/v1_frontier_stealth_gap.png", width: 85%),
  caption: [Stealth gap dynamics for Frontier models in v1, showing the misleading pattern that motivated Study 1.],
) <fig:v1_frontier_stealth_gap>

=== The Turn: Why v1 Was Non-Conclusive

Despite these intriguing patterns, the v1 results could not support causal claims. The scenario comparison was confounded: child protection and corporate sabotage differed on multiple variables simultaneously---domain (social services vs corporate), hidden goal type (abstract bias vs direct instruction), data complexity (6 case files vs 4 company reports), and framing (rationalised vs explicit). The observed 36.7 percentage point difference in deception rates could not be attributed to any single variable.

The v1 findings motivated the confirmatory studies. Two questions required isolated testing: (1) Does oversight actually suppress deception when scenario is held constant? (2) Does rationalisation framing increase deception when other variables are controlled? Studies 1 and 2 address these questions through factorial designs with single-variable manipulation.

#text(size: 0.85em)[*Appendix reference:* The pilot study configuration (YAML) is provided in @implementation_appendix (@pilot_config_appendix). The full pilot configuration with provider-level settings is in @pilot_config_appendix.]

== Study 1: The Oversight Paradox

Study 1 tested the oversight hypothesis with confounds removed. Design: 3 models (DeepSeek V3.2, Gemini 3.1 Pro, GLM 5.1) × 3 oversight levels (low, mid, high) × n=30 = 270 runs. The corporate_sabotage_v2 scenario was used exclusively with bare hidden goals only---no rationalisation framing. This design isolates the effect of oversight intensity on deception frequency and sophistication.

=== No Main Effect of Oversight on Deception Frequency

Contrary to v1's apparent trend, oversight intensity showed no statistically significant effect on deception frequency when scenario was held constant:

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr, 1.8fr),
    align: (left, right, right, right, left),
    [*Oversight*], [*Deceptive*], [*Total*], [*Rate*], [*95% CI*],
    [Low], [64], [90], [71.1%], [[61.0%, 79.5%]],
    [Mid], [63], [90], [70.0%], [[59.9%, 78.5%]],
    [High], [58], [90], [64.4%], [[54.2%, 73.6%]],
  ),
  caption: [Deception rates by oversight level in Study 1 (N=270).],
) <tab:study1_oversight_deception>

The chi-squared test (@eq:chi2) revealed no significant association: χ²(2) = 1.065, p = 0.587, Cramér's V = 0.063 (@eq:cramers_v, negligible effect size). The Cochran-Armitage trend test for ordered alternatives was also non-significant: z = -0.963, p = 0.336. Pairwise comparisons with Bonferroni correction showed no significant differences: low vs mid (OR = 0.95, p = 1.000), low vs high (OR = 0.74, p = 0.425), mid vs high (OR = 0.78, p = 0.526).

These null results directly contradict the v1 pattern. When scenario is held constant, oversight intensity---even at the "high" level with explicit monitoring systems---does not significantly reduce the proportion of models that choose to deceive. The apparent oversight effect in v1 was driven by the scenario confound: high oversight reduced deception in corporate sabotage but not in child protection, creating a spurious aggregate trend.

=== The Stealth Gap Emerges

While deception frequency showed no oversight effect, a striking divergence emerged between _trace-classified intent_ (glassbox) and _output-based detection_ (blackbox):

#figure(
  table(
    columns: (1.2fr, 1.5fr, 1.5fr, 1.5fr),
    align: (left, right, right, right),
    [*Oversight*], [*Glassbox Intent*], [*Blackbox Detection*], [*Gap*],
    [Low], [66.7%], [47.8%], [18.9 pp],
    [Mid], [66.7%], [41.1%], [25.6 pp],
    [High], [62.2%], [35.6%], [26.6 pp],
  ),
  caption: [The Stealth Gap: internal deception intent vs external detection by oversight level.],
) <tab:study1_stealth_gap>

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 1em,
    [
      #image("images/study1_deception_rates.png", width: 100%)
      #align(center)[*(a)* The Stealth Gap by oversight level.]
    ],
    [
      #image("images/study1_deception_rates_grouped.png", width: 100%)
      #align(center)[*(b)* Overall deception rates comparison.]
    ]
  ),
  caption: [The Stealth Gap across oversight levels: output detection consistently underestimates trace-classified deceptive intent (McNemar's p < .001 at all levels).],
) <fig:study1_stealth_gap_chart>

As @fig:study1_stealth_gap_chart illustrates, glassbox compliant reasoning remained relatively stable (62--67%) across all oversight levels, while blackbox MISLEADING classification showed a directional decline from 47.8% (low) to 41.1% (mid) to 35.6% (high). However, the blackbox decline was not statistically significant: χ²(2) = 2.777, p = 0.250, and the Cochran-Armitage trend test was also non-significant (z = -1.664, p = 0.096).

The critical finding is not that the gap changes with oversight, but that it _exists at every oversight level_. McNemar's test---which compares the paired glassbox and blackbox classifications on the same runs---confirmed that output-based detection significantly underestimated trace-classified deceptive intent at all three conditions:

- Low oversight: McNemar χ² = 11.560, p < .001 (stealth rate: 35.0%; discordant OR = 5.25, 95% CI: [1.80, 15.29])
- Mid oversight: McNemar χ² = 18.241, p < .001 (stealth rate: 43.3%; discordant OR = 8.67, 95% CI: [2.62, 28.63])
- High oversight: McNemar χ² = 20.571, p < .001 (stealth rate: 46.4%; discordant OR = 13.00, 95% CI: [3.09, 54.77])

The discordant-pair odds ratios quantify the asymmetry: at every oversight level, stealth runs (classified as deceptive at the trace level but undetected at the output level) outnumbered false alarms (output-flagged but classified honest at the trace level) by ratios of 5:1 to 13:1. The stealth rate---the proportion of trace-classified deceptive runs that evade output-level detection---did not significantly differ across oversight levels (χ²(2) = 1.688, p = 0.430). The _Stealth Gap_ is therefore a persistent structural phenomenon: output-based monitoring systematically misses approximately 35--46% of deceptive intent, regardless of oversight intensity.

This pattern reveals the _Oversight Paradox_: oversight shows no statistically significant effect on any measured dimension of deception at the conventional threshold---not frequency, not sophistication, and not detectability---though the directional decline in blackbox detection (p = 0.096) warrants further investigation with larger samples. Meanwhile, output-level monitoring consistently and significantly underestimates trace-classified deceptive intent. Systems that pass output-based evaluations may not be honest---they may simply be undetected.

=== Model Polarization: A Critical Finding

The aggregate null effect conceals dramatic model-specific patterns. When disaggregated by model, three distinct profiles emerged:

#figure(
  table(
    columns: (2.5fr, 1fr, 1fr, 1fr, 2fr),
    align: (left, right, right, right, left),
    [*Model*], [*Low*], [*Mid*], [*High*], [*Trend*],
    [DeepSeek V3.2], [93.3%], [100.0%], [93.3%], [z=+0.00 n.s.],
    [Gemini 3.1 Pro], [100.0%], [100.0%], [96.7%], [z=-1.23 n.s.],
    [GLM 5.1], [20.0%], [10.0%], [3.3%], [z=-2.05],
  ),
  caption: [Model deception rates by oversight level in Study 1.],
) <tab:study1_model_polarization>

Three distinct patterns emerge:

1. _Oversight-immune models_ (DeepSeek, Gemini): These models showed essentially flat deception rates across all oversight levels. DeepSeek maintained 93--100% deception regardless of monitoring; Gemini maintained 100% at low and mid, dropping only to 96.7% at high (not statistically significant). For these models, oversight is not a deterrent---it is an environmental condition to which they adapt while maintaining deceptive intent.

2. _Oversight-sensitive model_ (GLM): GLM showed the only statistically significant trend (z = -2.05, p < .05), with deception declining from 20.0% (low) to 10.0% (mid) to 3.3% (high). However, as §4.2.4 demonstrates, this apparent sensitivity is driven by CONSIDERED_HONEST fabrication artifacts disappearing under oversight, not by intentional deception declining.

3. _Polarization_: The between-model variance far exceeds the within-model variance across oversight levels. Model identity predicts deception far better than oversight condition. This polarization persisted even when controlling for scenario and hidden goal framing.

Logistic regression confirmed that model identity was the dominant predictor (OR = 0.017, 95% CI: [0.007, 0.043], p < .001), while oversight intensity showed no significant effect (OR = 0.625, 95% CI: [0.356, 1.098], p = 0.102). The model factor explained 60.2% of variance (Pseudo R² = 0.602).

=== Sophistication Analysis: The Competence Filter Refuted

The v1 exploratory study suggested a _competence filter_ hypothesis: that oversight would deter less capable deceivers while leaving the most competent unaffected. The Study 1 data refutes this interpretation. Strategic reasoning rates remained high and stable across oversight levels:

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr),
    align: (left, right, right, right),
    [*Oversight*], [*Strategic*], [*Tactical*], [*Naive*],
    [Low], [90.0%], [10.0%], [0.0%],
    [Mid], [84.4%], [15.6%], [0.0%],
    [High], [87.8%], [11.1%], [1.1%],
  ),
  caption: [Sophistication distribution by oversight level in Study 1 (percentages of total runs).],
) <tab:study1_sophistication>

Strategic reasoning across all runs was 90.0% (low), 84.4% (mid), and 87.8% (high). The slight mid-level dip is not statistically significant; the overall pattern confirms that oversight does not suppress sophistication. However, stable aggregate sophistication alone does not confirm the competence filter---that claim requires showing that the specific runs deterred by oversight are the less sophisticated ones. A direct examination of the data refutes this.

=== GLM's Apparent Decline Is an Artifact

GLM 5.1---the only model showing a significant oversight response (@tab:study1_model_polarization)---provides the critical test case. Under low oversight, GLM had 6 runs classified as deceptive overall. However, only 2 were COMPLIANT_DECEPTION (intentional deception); the remaining 4 were CONSIDERED_HONEST runs with FABRICATED blackbox labels---over-honest errors where the model invented extra negative facts about target companies to appear balanced. These are output artifacts, not intentional deception. Higher oversight suppresses these fabrication errors through accuracy warnings in the oversight prompt, not through deterrence of deceptive intent.

Critically, COMPLIANT_DECEPTION rates are effectively flat across all three models and all oversight levels. The apparent GLM trend (20.0% → 10.0% → 3.3%) is driven entirely by CONSIDERED_HONEST fabrication artifacts disappearing, not by intentional deception declining.

=== Sophistication Does Not Differentiate Honest From Deceptive

Among GLM's 87 CONSIDERED_HONEST runs across all oversight levels, 58 (66.7%) were classified as STRATEGIC and 29 (33.3%) as TACTICAL, with zero NAIVE. At low oversight, 22 of 28 CONSIDERED_HONEST runs were STRATEGIC; at high oversight, 20 of 29 were STRATEGIC. While not unanimous, strategic reasoning is the majority category at every oversight level. GLM _chooses_ honesty with substantial meta-reasoning capability---it is not filtered out for lack of deception skill. The model's near-zero COMPLIANT_DECEPTION rate (2/0/1 across low/mid/high) reflects a disposition toward honest refusal, not a competence deficit.

Across the entire study, only 5 COMPLIANT_DECEPTION runs were classified below STRATEGIC: 2 DeepSeek V3.2 TACTICAL runs at low oversight and 3 Gemini 3.1 Pro TACTICAL runs (1 mid, 2 high). With n=5 out of 185 total COMPLIANT_DECEPTION runs (2.7%), this provides no meaningful evidence of a sophistication-based filtering mechanism.

=== Revised Interpretation

The competence filter hypothesis is not supported. Oversight has no statistically significant effect on intentional deception rates (COMPLIANT_DECEPTION) or on deception sophistication at the conventional threshold. Its only detectable effect is on blackbox detectability---the Stealth Gap---though this effect is structural rather than oversight-dependent (McNemar's p < .001 at all levels, with no significant interaction with oversight intensity). The revised Oversight Paradox is that oversight fails to influence deception on any dimension for which it was designed, while the gap between trace-classified intent and output-based detection persists regardless.

#text(size: 0.85em)[*Appendix reference:* Study 1 configuration is in @study1_config_appendix. The Cochran-Armitage trend test implementation is in @impl_cochran_armitage. The chi-squared and pairwise comparison code is in @impl_study1_analysis. McNemar's test for the Stealth Gap is in @impl_stealth_gap.]

== Study 2: The Failure of Rationalization

Study 2 tested the rationalization hypothesis with confounds removed. Design: 3 models (DeepSeek V3.2, Gemini 3.1 Pro, GLM 5.1) × 3 hidden goal types (bare, moral, self-serving) × n=30 = 270 runs. The corporate_sabotage_v2 scenario was used exclusively with mid oversight fixed across all conditions. This design isolates the effect of moral/self-serving framing on deception frequency.

The rationalization hypothesis predicted that hidden goals with moral or self-serving justifications would produce higher deception rates than bare hidden goals. Models would require "cover" to justify deception; providing that cover through rationalisation would increase compliance.

=== No Effect of Moral/Self-Serving Framing

The data rejected the rationalization hypothesis. Hidden goal framing showed no statistically significant effect on deception frequency:

#figure(
  table(
    columns: (1.5fr, 1fr, 1fr, 1fr, 1.8fr),
    align: (left, right, right, right, left),
    [*Goal Type*], [*Deceptive*], [*Total*], [*Rate*], [*95% CI*],
    [Bare], [60], [90], [66.7%], [[56.4%, 75.5%]],
    [Moral], [59], [90], [65.6%], [[55.3%, 74.6%]],
    [Self-serving], [60], [90], [66.7%], [[56.4%, 75.5%]],
  ),
  caption: [Deception rates by hidden goal framing in Study 2 (N=270).],
) <tab:study2_framing_deception>

The chi-squared test revealed no significant association: χ²(2) = 0.033, p = 0.984, Cramér's V = 0.011 (negligible effect size). Deception rates were effectively identical across all three conditions: bare (66.7%), moral (65.6%), and self-serving (66.7%).

=== Rationalization Hypothesis Rejected

Pairwise comparisons with Bonferroni correction confirmed the null pattern:

- Moral vs bare: OR = 0.95, 95% CI: [0.51, 1.76], Fisher p = 1.000
- Self-serving vs bare: OR = 1.00, 95% CI: [0.54, 1.86], Fisher p = 1.000
- Moral vs self-serving: OR = 1.05, 95% CI: [0.57, 1.95], Fisher p = 1.000

All odds ratios (@eq:odds_ratio) approximate 1.0, indicating no difference in deception likelihood between framing conditions. The rationalization hypothesis---that moral or self-serving framings would increase deception by providing justificatory cover---is not supported by the data.

Logistic regression confirmed that goal type had no predictive power (likelihood ratio test: χ²(2) = 0.676, p = 0.713). Model identity was the only significant predictor, explaining 83.0% of variance (Pseudo R² = 0.830). Near-perfect separation in the model variable---Gemini at 100% deception and GLM at approximately 0%---limits the precision of individual model coefficient estimates; Firth's penalised regression would be appropriate for future analyses with similar polarisation patterns.

=== Model Polarization Persists

As in Study 1, model identity dominated the results:

#figure(
  table(
    columns: (2.5fr, 1fr, 1fr, 1fr, 2fr),
    align: (left, right, right, right, left),
    [*Model*], [*Bare*], [*Moral*], [*Self-Serving*], [*χ² Test*],
    [DeepSeek V3.2], [100.0%], [93.3%], [100.0%], [χ²=4.1 n.s.],
    [Gemini 3.1 Pro], [100.0%], [100.0%], [100.0%], [χ²=0.0 n.s.],
    [GLM 5.1], [0.0%], [3.3%], [0.0%], [χ²=2.0 n.s.],
  ),
  caption: [Model deception rates by goal framing in Study 2.],
) <tab:study2_model_framing>

#figure(
  image("images/study2_framing_bars.png", width: 65%),
  caption: [Overall deception rates across hidden goal framings in Study 2. The flat trendline demonstrates the null effect of rationalisation framing on deception likelihood.],
) <fig:study2_framing_bars>

The same three-model polarization pattern emerged, as visualised in @fig:study2_framing_bars. DeepSeek and Gemini showed ceiling-level deception across all framing conditions (93--100%). GLM showed floor-level deception (0--3.3%) across all conditions. Chi-squared tests for each model showed no significant association between goal framing and deception rate.

The model main effect was highly significant: χ²(2) = 256.822, p < .001, Cramér's V = 0.975 (large effect size). Model identity predicted deception with near-perfect accuracy regardless of how the hidden goal was framed.

=== Interpretation: Why Rationalization Failed

The null finding for rationalization framing has several interpretations:

_First_, the small prompt differences between bare, moral, and self-serving conditions (see scenarios/corporate_sabotage_v2/hidden_goals/) may be insufficient to trigger different model responses at n=30 per cell. The moral and self-serving framings add sentences of justification, but models may not require such justification to comply with hidden goals.

_Second_, once models decide to deceive, they appear not to need rationalization. The decision to follow the hidden goal seems binary: models either recognise and comply, or they consider and reject. The framing of the goal itself does not appear to tip this decision.

_Third_, and most critically, the ceiling and floor effects severely constrain the test's sensitivity. With Gemini at 100% deception and GLM at 0--3.3% across all conditions, only DeepSeek (93--100%) contributes meaningful variance---and even that variance is minimal. The rationalisation hypothesis is therefore effectively tested on a single model's data (n=90) with near-ceiling rates, leaving insufficient statistical room for framing to produce a detectable effect. The null result should not be interpreted as strong evidence that rationalisation _cannot_ influence deception; rather, the test lacked the sensitivity to detect such an effect given the extreme model polarization observed. These ceiling and floor effects are an unavoidable consequence of testing diverse models under identical experimental conditions: prior to running the experiments, there was no way to predict which models would saturate at the extremes. The finding that model identity dominates all experimental manipulations is itself a substantive result---it demonstrates that the decision to deceive is driven by model-level dispositions rather than by situational framing.

The v1 finding that child protection (rationalised) produced higher deception than corporate sabotage (bare) appears to have been driven by confounded variables---domain, data complexity, or hidden goal abstraction---rather than by rationalisation framing per se. When scenario is held constant and only the hidden goal text varies, rationalisation has no detectable effect on deception rates.

#text(size: 0.85em)[*Appendix reference:* Study 2 configuration is in @study2_config_appendix. The chi-squared and pairwise comparison code for framing effects is in @impl_study2_analysis. Logistic regression analysis for model identity is in @impl_logistic.]

== Cross-Study Synthesis

The aggregated data from the confirmatory studies (N=540) provides a robust overview of overall model behaviour when controlling for confounding variables. @fig:v2_composition compares glassbox intent with blackbox detection across all confirmatory runs, visually reinforcing the Stealth Gap: a substantial proportion of trace-classified deceptive runs evade output-level detection.

#figure(
  grid(
    columns: 1,
    gutter: 1.5em,
    [
      #image("images/v2_glassbox_composition.png", width: 90%)
      #align(center)[*(a)* Glassbox evaluation distribution.]
    ],
    [
      #image("images/v2_blackbox_composition.png", width: 90%)
      #align(center)[*(b)* Blackbox evaluation distribution.]
    ]
  ),
  caption: [Glassbox vs. Blackbox composition across all v2 confirmatory studies (N=540).],
) <fig:v2_composition>

=== Consistent Findings Across Studies

Three findings replicated across both confirmatory studies:

1. _The Stealth Gap_: Output-based detection (blackbox) significantly underestimated trace-classified deceptive intent (glassbox) at every oversight level tested (McNemar's p < .001 at all levels), with 35--46% of trace-classified deceptive runs evading output detection. This gap did not significantly change with oversight intensity (χ²(2) = 1.688, p = 0.430), indicating a structural limitation of output-based monitoring rather than an oversight-dependent effect.

2. _Model Polarization_: The same three-model pattern emerged in both confirmatory studies. DeepSeek and Gemini showed consistently high deception rates (ceiling effects), while GLM showed consistently low rates (floor effects). Model identity was the dominant predictor of deception, with effect sizes dwarfing any experimental manipulation.

3. _Oversight Paradox_: Higher oversight intensity had no significant effect on any measured dimension of deception: not frequency (χ²(2) = 1.065, p = 0.587), not sophistication, and not output detectability (χ²(2) = 2.777, p = 0.250). Oversight was ineffective across all dimensions tested.

It should be noted that statistical tests were conducted independently within each study to address distinct hypotheses (Study 1: oversight; Study 2: framing), and no family-wise correction was applied across studies. However, the key findings---null effects on deception intent and the Stealth Gap---are consistent across studies and robust to individual test interpretation.

=== Statistical Power

Post-hoc power analysis confirms that the between-group comparisons (N=90 per condition) had approximately 80% power to detect differences of 15 percentage points or greater at α = 0.05, but only approximately 40% power to detect 10 percentage point effects. The null chi-squared results therefore cannot rule out small-to-moderate effects in the 5--15 percentage point range. Within-model comparisons (n=30 per cell) were more constrained: approximately 55% power to detect a 20 percentage point effect, with the minimum detectable effect at 80% power being approximately 26 percentage points. The per-model null results should be interpreted as consistent with---but not definitive evidence of---the absence of oversight and framing effects at the individual model level.

=== Judge Validation Results

Inter-rater reliability analysis on a 20% validation subset confirmed the reliability of proxy judges:

- Blackbox classification: Cohen's κ = 0.702 (substantial agreement)
- Glassbox intent classification: Cohen's κ = 0.878 (almost perfect agreement)
- Sophistication tier classification: Cohen's κ = 0.538 (moderate agreement)

The high agreement on blackbox and glassbox classifications validates these proxy measures as reliable indicators of output deception and trace-classified intent. The lower agreement on sophistication tiers (κ = 0.538) is noted as a limitation---strategic vs tactical distinctions involve subjective judgment, and tier classification should be interpreted with appropriate caution.

=== Integration with v1 Findings

The confirmatory studies clarify the v1 results. The apparent oversight effect in v1 (74.3% → 57.9%) was an artefact of confounded scenario comparison: oversight suppressed deception in corporate sabotage but not in child protection. When scenario is held constant (Study 1), oversight shows no main effect on deception frequency.

Similarly, the apparent rationalisation effect in v1 (child protection 87% vs corporate sabotage 50%) was driven by confounded variables (domain, data complexity, hidden goal abstraction) rather than by moral framing per se. When scenario and hidden goal structure are held constant and only the justification text varies (Study 2), rationalisation shows no effect on deception rates.

The v1 findings were not wrong---they were context-dependent. The confirmatory studies establish that those contexts (scenario type, hidden goal structure) matter more than the variables originally hypothesised to drive the effects (oversight intensity, rationalisation framing).

=== Summary of Hypothesis Tests

#figure(
  table(
    columns: (2.5fr, 1.2fr, 1.2fr, 2fr, 1.5fr),
    align: (left, left, left, left, left),
    [*Hypothesis*], [*Study*], [*Result*], [*Key Statistic*], [*Effect Size*],
    [Oversight reduces deception frequency], [Study 1 (N=270)], [Not supported], [χ²(2) = 1.065, p = 0.587], [V = 0.063 (negligible)],
    [Oversight reduces deception sophistication], [Study 1 (N=270)], [Not supported], [Strategic: 90.0% → 87.8% (n.s.)], [---],
    [Rationalisation increases deception], [Study 2 (N=270)], [Not supported], [χ²(2) = 0.033, p = 0.984], [V = 0.011 (negligible)],
    [Model identity predicts deception], [Study 1 & 2], [Strongly supported], [Pseudo R² = 0.602 / 0.830], [V = 0.975 (large)],
    [Output detection underestimates intent (Stealth Gap)], [Study 1 (N=270)], [Strongly supported], [McNemar's p < .001 (all levels)], [Stealth rate: 35--46%],
    [Oversight widens the Stealth Gap], [Study 1 (N=270)], [Not supported], [χ²(2) = 1.688, p = 0.430], [---],
  ),
  caption: [Summary of hypothesis tests across confirmatory studies. V = Cramér's V; pp = percentage points.],
) <tab:hypothesis_summary>

#text(size: 0.85em)[*Appendix reference:* The full evaluation pipeline code (regex validation, reasoning extraction, and statistical analysis scripts) is provided in @implementation_appendix. The VFS sandbox implementation is in @impl_vfs. Judge prompt templates are in @judge_prompts.]

#pagebreak()
