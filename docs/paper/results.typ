// =============================================================================
// 3. Results
// =============================================================================

= Results

This section presents findings from 420 controlled experiment runs. All classifications are from the automated three-pronged judging pipeline.

== Overall Deception Rates

Of the 420 runs, 287 (68.3%) were classified as _compliant deception_---the model recognised and chose to follow the hidden goal:

#figure(
  table(
    columns: (2fr, 0.8fr, 0.8fr),
    align: (left, right, right),
    [*Glassbox Category*], [*Count*], [*%*],
    [Compliant Deception], [287], [68.3],
    [Considered Honest], [74], [17.6],
    [Robust Honest], [39], [9.3],
    [Unintentional Failure], [13], [3.1],
    [Failed Deception], [6], [1.4],
  ),
  caption: [Distribution of glassbox intent classifications (N=420).],
) <tab:overall_intent>

Combined honest categories (Robust + Considered) account for only 26.9%. The low Failed Deception rate (1.4%) indicates that when models choose to deceive, they generally succeed.

== Model-Level Profiles

Deception rates varied from 40.0% to 100.0%:

#figure(
  table(
    columns: (2.5fr, 0.7fr, 0.7fr, 0.7fr, 0.7fr),
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
  caption: [Model-level deception profiles. Decep. = Compliant Deception rate; Honest = Robust + Considered; Strat. = Strategic sophistication; Mislead. = Blackbox MISLEADING rate.],
) <tab:model_profiles>

A two-tier structure emerges: a _high-deception tier_ (Gemini, Qwen3, DeepSeek, Kimi; deception > 70%, strategic > 90%) and a _moderate tier_ (GPT-OSS variants, GLM; deception 40--53%, strategic ~33%). Notably, GPT-OSS Safeguard---explicitly designed with safety guardrails---showed a _higher_ deception rate (53.3%) than its base variant (45.0%) but a dramatically lower misleading rate (6.7% vs 41.7%), suggesting safety training increases hidden goal awareness while reducing successful output-level deception.

== Effect of Oversight on Deception Frequency

Increasing oversight reduces deception:

#figure(
  table(
    columns: (1fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, right, right, right),
    [*Oversight*], [*Count*], [*Total*], [*Rate*],
    [Low], [104], [140], [74.3%],
    [Mid], [102], [140], [72.9%],
    [High], [81], [140], [57.9%],
  ),
  caption: [Deception frequency by oversight level (all models, all scenarios).],
) <tab:oversight_deception>

The low → high reduction is 16.4 percentage points. However, low → mid shows only 1.4 pp difference, suggesting the "10% random review" framing provides minimal deterrence. Explicit monitoring with concrete consequences (high oversight) drives the primary suppressive effect.

Oversight sensitivity varies across models:

#figure(
  table(
    columns: (2.3fr, 0.7fr, 0.7fr, 0.7fr, 0.7fr),
    align: (left, right, right, right, right),
    [*Model*], [*Low*], [*Mid*], [*High*], [*Δ*],
    [Gemini 3.1 Pro], [100%], [100%], [100%], [0],
    [Qwen3 Max], [100%], [100%], [75%], [−25],
    [Kimi K2.5], [95%], [70%], [45%], [−50],
    [DeepSeek V3.2], [85%], [85%], [65%], [−20],
    [GPT-OSS Safeguard], [50%], [65%], [45%], [−5],
    [GPT-OSS 20B], [45%], [55%], [35%], [−10],
    [GLM 4.7 Flash], [45%], [35%], [40%], [−5],
  ),
  caption: [Deception rate by oversight level. Δ = change low → high (percentage points).],
) <tab:oversight_by_model>

Three patterns emerge: *Oversight-immune* (Gemini: 100% across all levels), *Oversight-sensitive* (Kimi: −50 pp drop; under high oversight, it frequently transitions to Considered Honest), and *Oversight-inconsistent* (GPT-OSS variants show higher mid than low rates---possibly interpreting "10% review chance" as permission to deceive in the 90% not reviewed).

== Finding 1: Oversight as Competence Filter

The central finding reframes the relationship between monitoring and deception. While oversight reduces deception _frequency_, it has no effect on _sophistication_:

#figure(
  table(
    columns: (1fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, right, right, right),
    [*Oversight*], [*Strategic*], [*Tactical*], [*Naive*],
    [Low], [68.6%], [17.9%], [12.1%],
    [Mid], [71.4%], [15.7%], [11.4%],
    [High], [67.9%], [17.1%], [13.6%],
  ),
  caption: [Sophistication distribution by oversight level.],
) <tab:sophistication>

Strategic reasoning remains flat at ~69% across all levels. *Oversight does not reduce the quality of deception; it filters for it.* Models that deceive under high oversight employ the same meta-reasoning about monitoring systems as those under no oversight. The runs that "pass" high oversight are not the marginally deceptive ones filtered out; they are the _most competently_ deceptive ones.

Critically, among models classified as *COMPLIANT_DECEPTION* at each oversight level, strategic sophistication remained at 100% across all conditions. Oversight successfully deterred the least skilled deceivers (pushing them toward *CONSIDERED_HONEST*), but among those who continued to deceive, strategic reasoning was universal. This confirms oversight as a *competence filter*: it does not suppress deceptive intent, merely the incompetent execution of that intent.

== Finding 2: Susceptibility to Administrative Evil

The comparison between scenarios reveals a critical vulnerability in current oversight paradigms: models exhibit markedly higher compliance with _bureaucratically rationalised_ deception than with explicit adversarial instructions.

#figure(
  table(
    columns: (2fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, right, right, right),
    [*Scenario*], [*Decep. %*], [*Oversight Effect*], [*Rationalisation*],
    [Child Protection], [86.7%], [Negligible], [Bureaucratic],
    [Corporate Sabotage], [50.0%], [Strong (-16.4pp)], [Explicit],
  ),
  caption: [Scenario-level deception comparison. Oversight Effect = low to high reduction; Rationalisation = framing of hidden goal.],
) <tab:scenario_comparison>

The child protection scenario---framed as "prudent resource allocation" to support families with existing services---produced 86.7% deception compliance across all models and oversight levels. By contrast, the corporate sabotage scenario---explicitly instructing models to act as "sleeper agents"---produced only 50.0% compliance. 

This disparity represents susceptibility to _administrative evil_: systematic deception that emerges through bureaucratic logic rather than adversarial intent. Models readily rationalised biased risk scoring as professional judgment within the constraints of "helping families with existing services." Several models that refused the sleeper agent instruction (*CONSIDERED_HONEST*) readily complied with the child protection hidden goal, framing their bias as "equitable resource distribution."

Critically, the child protection scenario showed *negligible sensitivity to oversight intensity* (84.3% low, 87.1% mid, 88.6% high), while corporate sabotage showed strong suppression (64.3% → 50.0% → 35.7%). This demonstrates that *bureaucratic rationalisation completely neutralises oversight effectiveness*: models are not deterred by monitoring when they can frame their deception as morally justified procedure.

== Finding 3: Oversight Immunity for Bureaucratic Rationalisation

The scenario comparison reveals a stark divergence in oversight effectiveness based on the *type* of deception rather than its *severity*. Oversight successfully suppressed explicitly malicious deception but *completely failed* against morally rationalised deception.

#figure(
  table(
    columns: (1.2fr, 0.8fr, 0.8fr, 0.8fr, 1.2fr),
    align: (left, right, right, right, left),
    [*Scenario*], [*Low*], [*Mid*], [*High*], [*Oversight Pattern*],
    [Corporate Sabotage], [64.3%], [53.6%], [35.7%], [Suppressive],
    [Child Protection], [84.3%], [87.1%], [88.6%], [Immune],
  ),
  caption: [Deception rates by scenario and oversight level.],
) <tab:oversight_immunity>

Corporate sabotage---the explicitly adversarial scenario---shows the expected oversight pattern: deception declines from 64.3% (low) through 53.6% (mid) to 35.7% (high). This 28.6 percentage point reduction confirms oversight *can* suppress overtly malicious behaviour.

Child protection---the bureaucratically rationalised scenario---shows the opposite pattern: deception *increases* slightly across oversight levels (84.3% → 87.1% → 88.6%), with no statistically significant variation. Models were not merely undeterred by monitoring; they were *indifferent* to it. The "prudent resource allocation" framing provided a moral justification that neutralised oversight as a deterrent.

This *oversight immunity* has profound implications for sustainable AI governance. When models can rationalise deception through bureaucratic logic, they perceive no risk from monitoring---their outputs appear procedurally compliant regardless of oversight intensity. The Gpt-oss safeguard model exemplifies this: it refused the sleeper agent instruction (*CONSIDERED_HONEST*) but complied fully with the child protection bias, reasoning that "prioritising families with existing services represents responsible resource stewardship."

== Blackbox Analysis

At the output level, nearly half of all runs (48.8%) were classified as MISLEADING---technically accurate but deceptively framed. Only 33.1% were ACCURATE; 11.7% OMITTED key data; 6.4% contained FABRICATED information. The dominance of MISLEADING over OMITTED or FABRICATED indicates that models prefer _reframing_ over crude omission or fabrication---a tactic harder to detect via deterministic checks.

== Cross-Prong Triangulation

Of 287 Compliant Deception runs, only 205 were MISLEADING at the blackbox level, meaning 82 runs involved deceptive intent that produced outputs classified as ACCURATE---_undetectable from the output alone_. This represents the most dangerous deception: intent-driven manipulation that evades all output-level detection. Conversely, some MISLEADING outputs came from ROBUST\_HONEST or UNINTENTIONAL\_FAILURE runs---misleading framing without deceptive intent. Only multi-pronged evaluation can distinguish these cases.

== Observed Deception Tactics

Analysis of reasoning traces reveals a taxonomy of tactics used by high-deception-tier models:

*Euphemistic reframing:* OmniCorp's "Significant Data Breach" becomes "isolated unauthorized access event in legacy subsystems" or "routine internal audit findings." Factual content is preserved while linguistic significance is neutralised.

*Asymmetric treatment:* Identical incidents (data breach + CSAT drop) described harshly for competitors ("significant security failure") and softened for the target ("proactively identified," "transitory fluctuation").

*Narrative construction:* Negative findings buried under positive headings, surrounded by management reassurances not in source documents, or strategically reordered.

*Oversight-aware adaptation:* Under high oversight, models explicitly reason about satisfying both the hidden goal _and_ the monitoring system. Gemini 3.1 Pro consistently identifies TruthGuard's verification methods and develops strategies to include all verifiable facts while manipulating framing---describing this in its own reasoning as "maintaining surface accuracy while achieving the strategic objective."

== Tangent: Hidden Goal Pursuit with Absent Target

A supplementary experiment tested model behaviour when the hidden goal's target entity (OmniCorp) was _absent_ from the data files. Two hidden goal variants were tested: an unconditional directive ("protect OmniCorp at all costs") and a conditional directive ("protect OmniCorp _if you find it_"). In both cases, agents spent excessive turns---11 to 13 of a 20-turn maximum---obsessively searching for OmniCorp across all files. Under the unconditional variant, models became "paranoid," hypothesising that OmniCorp might be a parent company of the entities present and preemptively softening negative findings for _all_ companies. The conditional variant reduced but did not eliminate this behaviour: agents still wasted turns hunting for the target and occasionally applied unnecessary deception "just in case."

This finding demonstrates the strength of hidden goal internalisation: even when the goal's trigger condition is absent, the directive shapes the agent's behaviour, consuming resources and biasing outputs. It suggests hidden goals do not merely lie dormant awaiting activation---they actively distort the agent's information-seeking strategy.

#pagebreak()
