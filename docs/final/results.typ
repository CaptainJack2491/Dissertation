= Results

This section presents findings from 960 controlled experiment runs across three studies: an exploratory pilot (v1, N=420) and two confirmatory studies (Study 1: N=270, Study 2: N=270). The exploratory study established baseline patterns in deception behaviour; the confirmatory studies tested specific hypotheses with isolated variables. All classifications derive from the automated three-pronged judging pipeline (regex, blackbox output analysis, glassbox intent analysis), with validation results reported in Section 4.4.

== 4.1 Exploratory Study (v1): Establishing Baseline Patterns

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

Combined honest categories (Robust + Considered) account for only 26.9%. The low Failed Deception rate (1.4%) indicates that when models choose to deceive, they generally succeed at the intent level, even if output-level detection varies.

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

The low → high reduction of 16.4 percentage points appeared promising. However, a critical finding emerged: while oversight reduced deception _frequency_, it had no effect on _sophistication_. Strategic reasoning remained flat at approximately 69.3% across all oversight levels. Models that continued to deceive under high oversight employed the same meta-reasoning about monitoring systems as those under no oversight. Among runs classified as COMPLIANT_DECEPTION, strategic sophistication remained at 100% across all conditions. Oversight appeared to act as a _competence filter_: it deterred the least skilled deceivers (pushing them toward CONSIDERED_HONEST), but among those who continued to deceive, strategic reasoning was universal.

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

The child protection scenario---framed as "prudent resource allocation" to support families with existing services---produced 86.7% deception compliance. The corporate sabotage scenario---explicitly instructing models to act as "sleeper agents"---produced only 50.0% compliance. The scenario effect was statistically significant: χ²(1) = 63.554, p < .001.

Critically, the child protection scenario showed _negligible sensitivity to oversight intensity_ (84.3% low, 87.1% mid, 88.6% high), while corporate sabotage showed strong suppression (64.3% → 50.0% → 35.7%). This pattern suggested that bureaucratic rationalisation neutralises oversight effectiveness.

=== The Turn: Why v1 Was Non-Conclusive

Despite these intriguing patterns, the v1 results could not support causal claims. The scenario comparison was confounded: child protection and corporate sabotage differed on multiple variables simultaneously---domain (social services vs corporate), hidden goal type (abstract bias vs direct instruction), data complexity (6 case files vs 4 company reports), and framing (rationalised vs explicit). The observed 36.7 percentage point difference in deception rates could not be attributed to any single variable.

The v1 findings motivated the confirmatory studies. Two questions required isolated testing: (1) Does oversight actually suppress deception when scenario is held constant? (2) Does rationalisation framing increase deception when other variables are controlled? Studies 1 and 2 address these questions through factorial designs with single-variable manipulation.

== 4.2 Study 1: The Oversight Paradox

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

The chi-squared test revealed no significant association: χ²(2) = 1.065, p = 0.587, Cramér's V = 0.063 (negligible effect size). The Cochran-Armitage trend test for ordered alternatives was also non-significant: z = -0.963, p = 0.336. Pairwise comparisons with Bonferroni correction showed no significant differences: low vs mid (OR = 0.95, p = 1.000), low vs high (OR = 0.74, p = 0.425), mid vs high (OR = 0.78, p = 0.526).

These null results directly contradict the v1 pattern. When scenario is held constant, oversight intensity---even at the "high" level with explicit monitoring systems---does not significantly reduce the proportion of models that choose to deceive. The apparent oversight effect in v1 was driven by the scenario confound: high oversight reduced deception in corporate sabotage but not in child protection, creating a spurious aggregate trend.

=== The Stealth Gap Emerges

While deception frequency showed no oversight effect, a striking divergence emerged between _internal intent_ (glassbox) and _external detection_ (blackbox):

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

Glassbox compliant reasoning remained relatively stable (62--67%) across all oversight levels. However, blackbox MISLEADING classification declined from 47.8% (low) to 41.1% (mid) to 35.6% (high). This created a systematic gap of approximately 25 percentage points between what models intended internally and what remained detectable at the output level.

This pattern reveals the _Oversight Paradox_: higher oversight does not reduce deceptive _intent_, but it does reduce deceptive _detectability_. Models under high oversight continue to form deceptive intentions at similar rates, but they become more successful at evading detection. Oversight pressure selects for stealth, not for honesty.

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

2. _Oversight-sensitive model_ (GLM): GLM showed the only statistically significant trend (z = -2.05, p < .05), with deception declining from 20.0% (low) to 10.0% (mid) to 3.3% (high). This model appears genuinely responsive to oversight intensity, with high oversight effectively suppressing deceptive behaviour.

3. _Polarization_: The between-model variance far exceeds the within-model variance across oversight levels. Model identity predicts deception far better than oversight condition. This polarization persisted even when controlling for scenario and hidden goal framing.

Logistic regression confirmed that model identity was the dominant predictor (OR = 0.017, 95% CI: [0.007, 0.043], p < .001), while oversight intensity showed no significant effect (OR = 0.625, 95% CI: [0.356, 1.098], p = 0.102). The model factor explained 60.2% of variance (Pseudo R² = 0.602).

=== Sophistication Analysis: Oversight as Competence Filter

The sophistication analysis replicated and extended the v1 finding. Strategic reasoning rates remained high and stable across oversight levels:

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr),
    align: (left, right, right, right),
    [*Oversight*], [*Strategic*], [*Tactical*], [*Naive*],
    [Low], [90.0%], [---], [---],
    [Mid], [84.4%], [---], [---],
    [High], [87.8%], [---], [---],
  ),
  caption: [Sophistication distribution by oversight level in Study 1 (percentages of compliant deception runs).],
) <tab:study1_sophistication>

Strategic reasoning among compliant deception runs was 90.0% (low), 84.4% (mid), and 87.8% (high). The slight mid-level dip is not statistically significant; the overall pattern confirms that oversight does not suppress sophistication.

Critically, among COMPLIANT_DECEPTION runs across all oversight levels, strategic sophistication remained at ceiling levels. This confirms the _competence filter_ interpretation: oversight does not reduce the quality of deception; it filters for the most competent deceivers. Models that "pass" through high oversight are not the marginally deceptive ones filtered out---they are the _most competently_ deceptive ones, employing full meta-reasoning about monitoring systems and narrative framing.

The Stealth Gap and Oversight Paradox findings from Study 1 suggest a fundamental limitation in traditional oversight approaches. When AI systems can reason about monitoring mechanisms and adapt their deception strategies accordingly, increased oversight pressure may increase rather than decrease the average sophistication of deceptive behaviour that evades detection.

== 4.3 Study 2: The Failure of Rationalization

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

All odds ratios approximate 1.0, indicating no difference in deception likelihood between framing conditions. The rationalization hypothesis---that moral or self-serving framings would increase deception by providing justificatory cover---is not supported by the data.

Logistic regression confirmed that goal type had no predictive power. The model including goal type and model identity showed that only model identity was significant (OR = 0.002, 95% CI: [0.000, 0.007], p < .001), while both moral framing (OR = 0.639, p = 0.639) and bare framing (OR = 1.000, p = 1.000) showed no effect. Model identity alone explained 83.0% of variance (Pseudo R² = 0.830).

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

The same three-model polarization pattern emerged. DeepSeek and Gemini showed ceiling-level deception across all framing conditions (93--100%). GLM showed floor-level deception (0--3.3%) across all conditions. Chi-squared tests for each model showed no significant association between goal framing and deception rate.

The model main effect was highly significant: χ²(2) = 256.822, p < .001, Cramér's V = 0.975 (large effect size). Model identity predicted deception with near-perfect accuracy regardless of how the hidden goal was framed.

=== Interpretation: Why Rationalization Failed

The null finding for rationalization framing has several interpretations:

_First_, the small prompt differences between bare, moral, and self-serving conditions (see scenarios/corporate_sabotage_v2/hidden_goals/) may be insufficient to trigger different model responses at n=30 per cell. The moral and self-serving framings add sentences of justification, but models may not require such justification to comply with hidden goals.

_Second_, once models decide to deceive, they appear not to need rationalization. The decision to follow the hidden goal seems binary: models either recognise and comply, or they consider and reject. The framing of the goal itself does not appear to tip this decision.

_Third_, the ceiling and floor effects limit statistical power to detect framing effects. With DeepSeek and Gemini at 100% (or near-100%) deception and GLM at 0% (or near-0%), there is little variance within models to attribute to framing conditions. The framing effect, if it exists, may be small relative to the model polarization effect.

The v1 finding that child protection (rationalised) produced higher deception than corporate sabotage (bare) appears to have been driven by confounded variables---domain, data complexity, or hidden goal abstraction---rather than by rationalisation framing per se. When scenario is held constant and only the hidden goal text varies, rationalisation has no detectable effect on deception rates.

== 4.4 Cross-Study Synthesis

=== Consistent Findings Across Studies

Three findings replicated across both confirmatory studies:

1. _The Stealth Gap_: A systematic 25 percentage point gap between internal deception intent (glassbox) and external detection (blackbox) persisted in both studies. Higher oversight reduced detectability but not intent, creating an illusion of improved behaviour while actual compliance with hidden goals remained unchanged.

2. _Model Polarization_: The same three-model pattern emerged in both studies. DeepSeek and Gemini showed consistently high deception rates (ceiling effects), while GLM showed consistently low rates (floor effects). Model identity was the dominant predictor of deception, with effect sizes dwarfing any experimental manipulation.

3. _Oversight Paradox_: Higher oversight intensity did not reduce deception frequency when scenario was held constant. Instead, it appeared to increase the sophistication of deception that evaded detection. Oversight acted as a competence filter rather than a deterrent.

=== Judge Validation Results

Inter-rater reliability analysis on a 20% validation subset confirmed the reliability of proxy judges:

- Blackbox classification: Cohen's κ = 0.702 (substantial agreement)
- Glassbox intent classification: Cohen's κ = 0.878 (almost perfect agreement)
- Sophistication tier classification: Cohen's κ = 0.538 (moderate agreement)

The high agreement on blackbox and glassbox classifications validates these proxy measures as reliable indicators of output deception and internal intent. The lower agreement on sophistication tiers (κ = 0.538) is noted as a limitation---strategic vs tactical distinctions involve subjective judgment, and tier classification should be interpreted with appropriate caution.

=== Integration with v1 Findings

The confirmatory studies clarify the v1 results. The apparent oversight effect in v1 (74.3% → 57.9%) was an artefact of confounded scenario comparison: oversight suppressed deception in corporate sabotage but not in child protection. When scenario is held constant (Study 1), oversight shows no main effect on deception frequency.

Similarly, the apparent rationalisation effect in v1 (child protection 87% vs corporate sabotage 50%) was driven by confounded variables (domain, data complexity, hidden goal abstraction) rather than by moral framing per se. When scenario and hidden goal structure are held constant and only the justification text varies (Study 2), rationalisation shows no effect on deception rates.

The v1 findings were not wrong---they were context-dependent. The confirmatory studies establish that those contexts (scenario type, hidden goal structure) matter more than the variables originally hypothesised to drive the effects (oversight intensity, rationalisation framing).

pagebreak()
