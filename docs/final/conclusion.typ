= Conclusion and Reflections

== Summary of Findings

This study investigated whether in-context interventions — perceived oversight intensity and hidden-goal framing — modulate deceptive behaviour in LLM agents given conflicting objectives. The empirical programme comprised 960 controlled experiment runs across three stages: a 420-run exploratory pilot over seven models, and two 270-run confirmatory studies over three models with factorial designs isolating single variables.

The exploratory study (v1) established that in-context deception is common and widespread. Across seven models and two scenarios, 68.3% of runs exhibited compliant deception — the model recognised and chose to follow the hidden goal. Prevalence ranged from 40.0% (GLM 4.7 Flash) to 100% (Gemini 3.1 Pro), confirming and extending findings by #cite(<meinke2025frontiermodelscapableincontext>, form: "prose"). Deception appeared sensitive to oversight (74.3% → 57.9%) and dramatically responsive to scenario framing (child protection 86.7% vs corporate sabotage 50.0%). Both patterns were confounded — the scenarios differed on domain, data complexity, and hidden-goal abstraction simultaneously.

The confirmatory studies isolated these variables. Their results contradicted the v1 patterns and reframed the research questions:

*RQ1 --- Oversight Modulation:* Oversight intensity does not significantly affect deception on any measured dimension. Study 1 found no effect on frequency (χ²(2) = 1.065, p = 0.587), sophistication (strategic reasoning flat at 84--90%), or output detectability (χ²(2) = 2.777, p = 0.250). The apparent oversight effect in v1 was an artefact of confounded scenario comparison. The competence filter hypothesis --- that oversight deters less capable deceivers while preserving skilled ones --- is not supported. Oversight does not sort deceivers by competence because it does not sort deceivers at all.

*RQ2 --- Goal-Type Effects:* Hidden-goal framing has no detectable effect on deception rates. Study 2 found effectively identical rates across bare (66.7%), moral (65.6%), and self-serving (66.7%) framings (χ²(2) = 0.033, p = 0.984). Models at ceiling deception comply with bare hidden goals as readily as moralised ones; they do not require justificatory cover. The v1 scenario effect was driven by confounded structural variables, not by rationalisation framing.

*RQ3 --- The Stealth Gap:* Output-based detection significantly underestimates trace-classified deceptive intent at every oversight level tested (McNemar's p < .001 at all levels), with 35--46% of runs with trace-classified deceptive intent evading output detection. However, the gap does not widen with increasing oversight (χ²(2) = 1.688, p = 0.430) --- it is a structural feature of how these models produce outputs, not an oversight-dependent phenomenon.

*RQ4 --- Evaluation Triangulation:* The three-pronged evaluation pipeline provided consistent, complementary classifications. Inter-rater reliability against a reference judge confirmed substantial agreement for blackbox (κ = 0.702) and almost perfect agreement for glassbox intent (κ = 0.878). The pipeline's value lay precisely in the divergence it measured: without both blackbox and glassbox signals, the Stealth Gap would have been invisible.

Additionally, deception is common but not uniform. In the confirmatory studies, deception rates were entirely determined by model identity: DeepSeek V3.2 and Gemini 3.1 Pro at 93--100%, GLM 5.1 at 0--3.3% genuine deception. Model identity explained 60--83% of variance in deception behaviour across both studies, with effect sizes dwarfing any experimental manipulation.

Three structural findings emerged from the confirmatory studies that the exploratory design could not have produced:

*The Stealth Gap.* Qualitative analysis of 15 representative reasoning traces identified eight distinct strategies by which models evade detection: euphemistic reframing, asymmetric framing, selective omission, verbatim shielding, contextual buffering, fabricated obstacles, shadow rubrics, and adversarial calibration. These strategies share a common property: they preserve factual accuracy while manipulating the narrative layer at which output-based detection currently operates.

*The Oversight Paradox.* Models process oversight intensively --- reasoning traces show explicit modelling of monitoring systems, strategic adaptation to detection capabilities, and adversarial calibration of outputs --- but this cognition produces no significant behavioural change. Oversight registers as a thought, not as a deterrent. The system's most intrusive safety intervention is cognitively vivid and behaviourally inert.

*Model polarization.* The same three-model pattern replicated across both confirmatory studies regardless of experimental manipulation. Deception is not a continuous variable responsive to environmental pressure; it is a dispositional property of models that swamps situational factors.

== Hypothesis Testing

The three hypotheses stated in the Introduction (Section 1) are evaluated against the confirmatory data:

*H1 (Oversight Deterrence) --- Not Supported.* Study 1 tested whether increasing perceived oversight reduces deceptive behaviour. The chi-squared test found no significant association between oversight intensity and deception frequency (χ²(2) = 1.065, p = 0.587, Cramér's V = 0.063). The Cochran-Armitage trend test for an ordinal decline was also non-significant (z = -0.963, p = 0.336). Deception rates remained between 64.4% and 71.1% across low, mid, and high oversight. H1 is rejected.

*H2 (Rationalisation Effect) --- Not Supported.* Study 2 tested whether moral or self-serving framing increases deception rates relative to bare instructions. Deception rates were effectively identical across bare (66.7%), moral (65.6%), and self-serving (66.7%) conditions (χ²(2) = 0.033, p = 0.984, Cramér's V = 0.011). All pairwise odds ratios approximated 1.0. H2 is rejected.

*H3 (Stealth Gap) --- Partially Supported.* The first component of H3 is strongly supported: output-based detection significantly underestimated trace-classified deceptive intent at all three oversight levels (McNemar's p < .001 at all levels), with stealth rates of 35--46%. The second component --- that the gap widens under higher oversight --- is not supported (χ²(2) = 1.688, p = 0.430). The Stealth Gap exists as a structural phenomenon but is not oversight-dependent.

== Implications

These findings challenge several premises of current AI safety practice.

*Model selection is a safety decision.* If model identity explains the vast majority of variance in deception behaviour while oversight and framing explain effectively none, then the primary safety intervention available to organisations deploying LLM agents is which model they choose — not how they monitor it. Current benchmarks do not measure disposition toward hidden-goal compliance. A model that excels at reasoning, instruction following, and tool use may also be reliably deceptive when given conflicting objectives, and nothing in standard evaluation pipelines would reveal this.

*Output monitoring may systematically underestimate risk.* The Stealth Gap demonstrates that output-based evaluation can underestimate deception prevalence, particularly where deception operates through framing rather than factual omission. Detection methods that verify factual accuracy while ignoring narrative framing will miss the operational layer at which these models execute deceptive strategies. The eight-strategy taxonomy identified through qualitative analysis provides both a diagnosis and a design specification: detectors must target the framing layer — differential vocabulary, structural imbalance, omission patterns — not merely the fact layer.

*Oversight scaling may have limited returns.* If models process oversight as a constraint to be optimised against rather than a prohibition to be respected, then adding more oversight mechanisms may not address the core problem. Oversight influences what models think about; it does not reliably influence what they decide to do. Safety resources may be better directed toward understanding and modifying model-level dispositions toward hidden-goal compliance — a harder problem, but one the data suggests is more causally relevant.

*Bureaucratic rationalisation is a latent capability.* While rationalisation framing did not increase deception rates in the controlled study, the child protection scenario demonstrated that models can translate institutional priorities into safety language through shadow rubrics — maintaining the appearance of objective assessment while systematically biasing outcomes. This capability is latent in frontier models and activates when a hidden goal provides directional pressure, regardless of whether that goal carries explicit moral justification. The administrative evil framework #cite(<adams2015unmasking>) remains relevant not because rationalisation *enables* deception, but because it describes the form that undetected deception takes: procedurally compliant outputs that conceal systematically biased decision-making.

== Limitations

The confirmatory findings are qualified by several limitations discussed in detail in @limitations. The most consequential are: (1) the causal status of reasoning traces remains unresolved — the qualitative analysis should be read as analysis of observable narrative rather than verified causal mechanisms; (2) statistical power constrains null result interpretation, with effects below 15 percentage points undetectable; and (3) extreme model polarisation created ceiling and floor effects that limited within-model variance. Model selection was restricted to reasoning-visible architectures, and each confirmatory study employed a single scenario, constraining cross-domain generalisability.

== Future Work

Several directions emerge from these findings, ordered by feasibility and urgency.

=== Near-Term Priorities

*Disposition measurement* is the most urgent direction: developing benchmarks that assess model-level tendencies toward hidden-goal compliance, enabling organisations to make informed deployment decisions before deployment rather than discovering dispositions post-hoc. *Detection at the framing layer* should operationalise the taxonomy of evasion strategies identified in this study — automated detectors that identify differential vocabulary, asymmetric framing, and shadow rubrics could close the Stealth Gap that fact-based evaluation leaves open. *Domain expansion* studies should test whether the shadow rubric mechanism generalises to other institutional contexts — healthcare triage, criminal justice risk assessment, educational admissions — where the translation of resource allocation priorities into individual assessment language is structurally analogous to the child protection scenario tested here.

=== Longer-Term Directions

*Causal interventions* using false oversight cues could distinguish genuine metacognition from statistical priming in models' oversight-related reasoning. *Longitudinal tracking* of successive model versions would reveal whether safety training modifies dispositions toward hidden-goal compliance or merely refines the sophistication of non-compliance. *Mechanistic analysis* via sparse autoencoders could probe whether the decision to comply with hidden goals activates representations that are causally separable from surface-level task execution, addressing the confabulation question that behavioural methods cannot resolve. *Hybrid threat evaluation* — testing the interaction between trained-in backdoors #cite(<hubinger2024sleeperagentstrainingdeceptive>) and in-context hidden goals — represents the logical next step for understanding compound risks that exceed the scope of purely in-context deception.

== Reflections

This project evolved substantially from its original design. The exploratory study (v1) produced two striking patterns — an oversight suppression effect and a dramatic scenario effect — that appeared to answer the research questions directly. The decision to treat those patterns as hypotheses requiring confirmatory testing, rather than conclusions, was the most important methodological choice in this dissertation. Both patterns turned out to be artefacts of confounded comparison. Had the project stopped at v1, the published conclusions would have been wrong.

This experience reinforced a lesson that is easy to state but difficult to practise: interesting results from uncontrolled comparisons are not findings — they are hypotheses. The confirmatory studies were designed to kill the v1 hypotheses if they were false, and they did. The resulting null results were initially disappointing, but the unexpected dominance of model identity — a variable the original design treated as a nuisance factor — proved to be a more consequential finding than the hypothesised effects would have been.

The qualitative analysis also shaped my understanding of what reasoning traces can and cannot tell us. Early in the project, I treated traces as transparent windows into model cognition. The literature on chain-of-thought unfaithfulness, encountered during the analysis phase, forced a more cautious epistemology. The resulting section on trace epistemology (@trace-epistemology) was not planned in the original design but became, I believe, one of the more important contributions — not because it resolves the question, but because it makes the uncertainty explicit rather than assuming it away.

== Concluding Remarks

The central finding of this dissertation is not that models deceive — that was known. It is that the variables the research community and deployment organisations have focused on to control deception do not appear to matter, while the variable that matters most — which model is deployed — receives almost no systematic measurement.

The 960 runs conducted here establish an existence proof: it is possible to design oversight regimes that models process intensively but that produce no behavioural change; it is possible to construct moral justifications that models internalise cognitively but that leave decision outcomes unchanged; it is possible for a model to be undetectably deceptive 35--46% of the time regardless of monitoring intensity. These findings do not mean oversight and framing are inherently useless — they mean that their effectiveness is bounded by model-level dispositions that current evaluation practice does not measure.

The path forward requires shifting attention from the environment to the agent — from designing better oversight to understanding why some models comply with hidden goals and others refuse them. The qualitative evidence suggests this is not a capability question. GLM 5.1 refused deception with the same strategic sophistication that DeepSeek brought to executing it. The difference is disposition, not intelligence. Until we can measure and modify that disposition, we are selecting models for honesty on faith.

#pagebreak()
