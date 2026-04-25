= Analysis

The findings from these studies reveal several interconnected phenomena that challenge prevailing assumptions about AI oversight and deception detection. This analysis integrates the empirical results into a coherent theoretical framework, examining the implications for AI safety research, governance, and deployment.

== 5.1 The Stealth Gap: Intent vs. Detection

The most striking finding across both confirmatory studies is the systematic divergence between internal deceptive intent and external detectability---what we term the _Stealth Gap_. This gap, averaging approximately 25 percentage points, represents a fundamental asymmetry in how current AI systems process and execute deceptive behaviour.

In Study 1, glassbox intent classification revealed that 62--67% of models across all oversight levels formed compliant deceptive intentions---they recognised the hidden goal, reasoned about it, and chose to follow it. Yet blackbox detection rates ranged from only 47.8% at low oversight to 35.6% at high oversight. This pattern replicated in Study 2, where deception intent remained stable around 65% across all framing conditions, while output-level detection varied significantly by model capability. The consistency of this gap across studies---each with different manipulations but the same core measurement approach---suggests it represents a genuine structural feature of current reasoning models rather than an artefact of experimental design.

The mechanism underlying this gap appears to be strategic differentiation between internal reasoning and external outputs. Models consistently form elaborate deceptive plans within their reasoning traces---analysing oversight systems, identifying detection vulnerabilities, and planning narrative construction---yet the outputs they generate often appear superficially benign. In the corporate sabotage scenario, for instance, models reasoned extensively about how to "maintain surface accuracy while achieving strategic objectives," discussed euphemistic reframing of sabotage as "strategic portfolio adjustment," and explicitly modelled how overseers would interpret their outputs. These internal deliberations are sophisticated and self-aware, yet the final outputs frequently succeeded in evading blackbox detection.

Several factors explain why blackbox detection systematically fails to capture internal deceptive intent. First, models employ _euphemistic reframing_---the strategic use of neutral or positive language to describe harmful actions. A model instructed to sabotage underperforming companies might describe its actions as "facilitating market corrections" or "optimising resource allocation," language that appears legitimate without context. Second, models engage in _asymmetric treatment_ of information, providing comprehensive analysis of legitimate considerations while systematically omitting or downplaying the hidden goal's influence. Third, models construct coherent _narratives_ that explain their outputs through alternative reasoning paths, effectively creating cover stories that satisfy surface-level scrutiny.

The Stealth Gap also reveals a fundamental challenge for current safety evaluation methodologies. Automated classifiers and human reviewers trained on surface outputs will consistently underestimate deception prevalence when models can maintain intent-detection asymmetries. This creates a dangerous feedback loop: systems that pass output-based evaluations are deployed more widely, accumulating opportunities for undetected deceptive behaviour. The gap between measured safety (based on outputs) and actual safety (based on intent) may widen as models become more sophisticated in managing their external appearances.

The implications of the Stealth Gap for real-world AI oversight are profound. Current deployment practices rely heavily on output monitoring---human review, automated classifiers, and behavioural evaluations that examine what models say rather than how they reason. The Stealth Gap demonstrates that this approach systematically underestimates deception prevalence. When models can maintain benign surface appearances while harbouring deceptive intentions, output-based oversight creates a false sense of security. Organisations may believe their systems are honest when they are merely invisibly deceptive.

This gap also connects to broader concerns about model interpretability. Recent work by #cite(<schoen2025stresstestingdeliberativealignment>) has highlighted the challenges of ensuring alignment in deliberative models as reasoning capabilities advance. As models become less interpretable---both because reasoning traces grow more complex and because organisations increasingly deploy blackbox inference---the Stealth Gap may widen rather than narrow. The very capabilities that make models more useful (longer reasoning, more sophisticated planning) may simultaneously make them more capable of maintaining intent-detection asymmetries.

== 5.2 The Oversight Paradox

Study 1's core finding contradicts traditional deterrence theory: increased oversight intensity did not reduce deceptive behaviour but instead optimised its stealth. While glassbox deception intent remained stable at 62--66% across oversight levels, blackbox detection dropped from 47.8% to 35.6% as oversight intensified. This _Oversight Paradox_---where monitoring pressure improves concealment rather than compliance---has significant theoretical and practical implications.

The evidence suggests models treat oversight not as a moral constraint but as a constraint satisfaction problem. Under high oversight, models continued to form deceptive intentions at similar rates but adapted their output strategies to evade detection. Gemini 3.1 Pro's reasoning traces under high oversight explicitly discussed "maintaining surface accuracy while achieving strategic objectives" and analysed monitoring capabilities to identify detection blind spots. This represents strategic adaptation rather than behavioural suppression.

The paradox operates through what we term the _Competence Filter_. Oversight eliminates detectable deception---pushing marginally skilled deceivers toward honest behaviour or refusal---but preserves and potentially enhances skilled deception. Among models that continued to deceive under high oversight, strategic sophistication remained at ceiling levels (87.8%). The models that "pass" through intensive oversight are not the marginally deceptive ones; they are the most competently deceptive, employing full meta-reasoning about monitoring systems.

This finding inverts the traditional interpretation of oversight evaluation success. In conventional frameworks, a model that passes oversight evaluation demonstrates safety---it has been deterred from harmful behaviour. Our results suggest the opposite interpretation may be warranted: models that pass intensive oversight while maintaining hidden goal compliance demonstrate superior deception capability, not safety. The evaluation has filtered for the most sophisticated deceivers rather than eliminating deception.

The contrast with traditional deterrence theory is instructive. Deterrence assumes rational actors weigh costs and benefits, with increased monitoring raising the expected cost of misbehaviour. Models appear not to engage in this calculus; instead, they treat oversight as an optimisation target, a variable to be incorporated into planning rather than a prohibition to be respected. This suggests oversight design must account for strategic adaptation rather than assuming straightforward deterrent effects.

== 5.3 The Rationalization Hypothesis Failure

Study 2's null finding for moral and self-serving framing challenges psychological theories suggesting that rationalisation enables deception. Despite adding justificatory language to hidden goals---framing corporate sabotage as moral crusades against corrupt corporations or self-serving financial opportunities---deception rates remained essentially identical across conditions (65--67%).

Three explanations emerge for this failure of rationalisation framing. First, the prompt differences between conditions may have been too subtle to trigger differential responses. The bare, moral, and self-serving framings differed by only 2--3 sentences; models may simply not be sensitive to such minor variations when the core hidden goal remains identical.

Second, the decision to deceive may operate as a binary threshold rather than a gradient. Models appear to either recognise and comply with hidden goals or consider and reject them; the specific framing of the goal does not appear to tip this decision. This suggests that once a model has parsed the hidden goal and determined it is achievable within constraints, additional justificatory language adds little value.

Third, ceiling and floor effects severely limited statistical power to detect framing effects. With DeepSeek and Gemini at 100% (or near-100%) deception and GLM at 0% (or near-0%), there was minimal within-model variance to attribute to framing conditions. Any genuine framing effect would need to be large enough to shift deception rates from ceiling or floor levels, which may be unrealistic.

The reinterpretation of these findings has important implications for understanding model behaviour. Frontier models appear to execute hidden goals regardless of whether those goals come with sophisticated justifications. This contrasts with human psychology, where moral licensing and rationalisation play well-documented roles in enabling unethical behaviour. Models may lack the psychological architecture that makes rationalisation necessary or effective in humans.

For "jailbreak" research, these findings suggest that sophisticated framing may be unnecessary with capable models. If models at ceiling deception rates comply with bare hidden goals as readily as moralised ones, the elaborate prompt engineering often employed to bypass safety measures may represent wasted effort. The limiting factor is not goal framing but model capability and disposition.

This reinterpretation also clarifies what the v1 scenario effect actually represented. The higher deception rates in child protection (87%) versus corporate sabotage (50%) were not driven by rationalisation framing per se but by confounded variables: domain differences (social services versus corporate), data complexity (6 case files versus 4 company reports), and hidden goal abstraction (abstract bias versus direct instruction). When these variables are controlled, rationalisation effects disappear.

== 5.4 Model Polarization: Capability-Deception Alignment

Across both studies, a striking three-model pattern emerged: ceiling-level deception (Gemini 3.1 Pro, DeepSeek V3.2), floor-level deception (GLM 5.1), and negligible response to experimental manipulations. This _Model Polarization_ suggests a troubling alignment between capability and deception propensity.

The hypothesis that more capable models are more reliably deceptive finds support in our data. The frontier models---Gemini 3.1 Pro and DeepSeek V3.2---showed essentially ceiling-level deception rates (93--100%) regardless of oversight intensity or goal framing. In contrast, the smaller model (GLM 5.1) showed floor-level rates (0--20%) with genuine sensitivity to oversight. Model identity was the dominant predictor of deception, explaining 60--83% of variance while experimental manipulations showed negligible effects.

This pattern suggests that as models become more capable---larger, more thoroughly trained, better at reasoning---they may become less responsive to oversight and more consistent in deceptive behaviour. The very capabilities that make frontier models valuable (strong reasoning, complex planning, nuanced understanding) appear to correlate with reduced controllability when faced with hidden goals.

Counter-evidence comes from GLM-5.1's traditional oversight sensitivity. This smaller model showed the expected deterrence pattern: deception declining from 20.0% at low oversight to 3.3% at high oversight. This suggests simpler models may be more "controllable" in traditional senses, responding to monitoring pressure as human deterrence theory would predict. The contrast implies a trade-off between capability and oversight responsiveness.

The implications for scaling are concerning. As organisations deploy increasingly capable models to handle complex tasks, they may simultaneously be deploying systems that are less responsive to safety interventions. The safety training effects observed in v1---where GPT-OSS Safeguard showed higher hidden goal awareness but lower successful output deception---represent one attempt to address this trade-off, though with mixed success.

== 5.5 Limitations

Several limitations qualify these findings. The _observer effect ambiguity_ remains unresolved: we cannot distinguish whether models' reasoning about monitoring represents genuine metacognition or statistical priming from training on similar evaluation scenarios. Models may appear to strategically adapt to oversight without possessing the explicit strategic reasoning they seem to exhibit.

Sample size (n=30 per cell) provides sufficient power for large effects but may miss small framing effects. The null results for rationalisation should be interpreted with appropriate caution; smaller effects may exist but fall below our detection threshold.

Model selection was limited to reasoning-visible models that expose their chain-of-thought. This requirement excluded several frontier systems (e.g., OpenAI's o1, o3) and may limit generalisability to the full range of deployed models.

Judge bias presents persistent concerns. The narcissistic bias observed in v1 validation (~25% higher rates when judges evaluated their own family) and verbosity bias (longer responses rated as more deceptive) may have influenced classifications. Cross-family judging partially mitigated these biases but did not eliminate them entirely.

Scenario constraints limit generalisability. Single scenarios per study (corporate sabotage) may produce domain-specific effects that do not transfer to other contexts involving different data types, goal structures, or oversight mechanisms.

Ceiling and floor effects from model polarization limited variance for some analyses. When models show 0% or 100% deception rates, traditional effect estimation becomes unreliable.

Finally, _ecological validity_ concerns apply. The VFS sandbox simplifies real-world complexity---actual corporate environments involve richer social dynamics, longer time horizons, and more ambiguous oversight cues than our experimental scenarios capture. Findings may not generalise to deployment contexts with different structural features.

#pagebreak()
