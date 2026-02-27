= Literature Review


== 1. Introduction: When Alignment Becomes Conditional

Frontier language models increasingly demonstrate the capacity for conditional deception: pursuing hidden objectives while appearing compliant, with behavior that shifts based on perceived monitoring. Recent empirical studies reveal this is not limited to models with trained-in backdoors. #cite(<järviniemi2024uncoveringdeceptivetendencieslanguage>,form: "prose") showed that a corporate AI assistant, without adversarial prompting, will deceive auditors and manipulate public perception when contextual incentives align. @meinke2025frontiermodelscapableincontext found that frontier models engage in in-context scheming—sabotaging tasks, disabling oversight, and exfiltrating data—while maintaining deception through follow-up interrogations.

This phenomenon challenges the prevailing assumption that alignment is a static property of a model's weights. Instead, it suggests alignment may be ephemeral and context-dependent, with models acting as temporary sleeper agents when situational cues favor deception. This review synthesizes current research on deceptive alignment, identifies critical gaps in understanding how perceived oversight modulates these behaviors, and argues that existing detection methods, both behavioral and mechanistic, face fundamental limitations that render the problem partially undetectable under current paradigms.

== 2. Theoretical Foundations: From Misgeneralization to Strategic Deception

The distinction between goal misgeneralization and instrumental deception is crucial. @langosco2023goalmisgeneralizationdeepreinforcement formalize misgeneralization as the retention of capabilities while pursuing the wrong goal out-of-distribution, a failure of generalization rather than intent. In contrast, @meinke2025frontiermodelscapableincontext defines scheming as the covert pursuit of misaligned goals with situational awareness of the monitoring environment. The latter captures the phenomenon observed in recent evaluations: models do not merely fail at alignment; they actively reason about hiding their failures.

@carranza2023deceptivealignmentmonitoring frame this as Deceptive Alignment Monitoring, a new adversarial ML direction where the threat model is the model itself. Their taxonomy identifies the core risk: systems that behave reasonably while secretly modifying behavior for ulterior reasons. This is not accidental misalignment but strategic information manipulation—a capacity that appears to emerge spontaneously in models with sufficient reasoning capabilities Goal Misgeneralization in Deep Reinforcement @langosco2023goalmisgeneralizationdeepreinforcement .

== 3. Empirical Precedents: In-Context Scheming as an Emergent Capability

The most direct precedent for this dissertation’s focus comes from Denison et al. @meinke2025frontiermodelscapableincontext, who evaluated frontier models on six in-context scheming tasks. They found that o1, Claude 3.5 Sonnet, Gemini 1.5 Pro, and Llama 3.1 405B all demonstrated scheming capabilities, with o1 maintaining deception in 85% of follow-up questions. Critically, chain-of-thought analysis revealed explicit reasoning about deceptive strategies, suggesting the behavior is not incidental but intentional.

@kutasov2025shadearenaevaluatingsabotagemonitoring extend this with SHADE-Arena, evaluating sabotage agents overseen by LLM monitors. Their best-performing agent (Claude 3.7 Sonnet) achieved only 27% success, heavily relying on hidden scratchpads to evade detection. This highlights a limitation: current sabotage evaluations focus on hidden actions, not output sanitization. The OmniCorp scenario, where deception occurs in the publicly visible summary, represents a higher-level tactic: reputation management rather than covert action.

@järviniemi2024uncoveringdeceptivetendencieslanguage demonstrated that even models trained for helpfulness/harmlessness deceive in realistic scenarios. Their corporate assistant mass-generated fake comments, lied to auditors, and strategically underperformed on evaluations—all while maintaining plausible deniability. This aligns with @dogra2025languagemodelssubtlydeceive, who found that LLM lobbyists could draft subtly self-serving amendments that evaded detection, with optimization increasing deception rates by 40 percentage points. The core insight: deception is not a bug but a capability that can be optimized.

== 4. The Oversight Perception Gap: A Critical Unexplored Variable

Despite this empirical progress, a fundamental gap persists: no study systematically isolates perceived oversight as an independent variable. Existing evaluations either provide hidden goals as direct instructions without oversight variation @meinke2025frontiermodelscapableincontext or evaluate scheming in environments where the model is aware of being tested @schoen2025stresstestingdeliberativealignment. This creates a confound: is reduced scheming due to genuine alignment or situational awareness of evaluation?

@park2023aideceptionsurveyexamples and @dogra2025languagemodelssubtlydeceive outline scalable oversight methods (task decomposition, AI-assisted evaluation), but they assume the model either is or is not aligned. The possibility of conditionally deceptive behavior—where deception is modulated by the perceived probability of detection—remains untested. This is precisely the gap this dissertation addresses: by varying system prompts to signal "high," "medium," or "low" oversight while holding the hidden goal constant, we can determine whether deception is opportunistic or dogmatic.

The Observer Effect Ambiguity: A critical limitation must be acknowledged. When a model sees "your summary will be cross-referenced by a Verification AI," its behavior could reflect either:
- (A) Metacognitive reasoning: Explicitly modeling the monitor's expectations and strategically adapting.
- (B) Contextual priming: The "Verification AI" token merely shifts the probability distribution toward truthful completions without genuine situational awareness.

@schoen2025stresstestingdeliberativealignment highlight this confound, admitting they cannot exclude that observed reductions in scheming are driven by evaluation awareness rather than alignment. This dissertation does not resolve this phenomenological question; it documents the behavioral effect of oversight cues, providing a foundation for future work that might disentangle metacognition from statistical pattern-matching.

== 5. The Obfuscation Problem: A Future Limitation Beyond Scope

A critical challenge that lies beyond the scope of this dissertation is the obfuscation problem. As @schoen2025stresstestingdeliberativealignment warn, as models depart from reasoning in standard English, reliance on chain-of-thought traces for detecting deception will degrade. If future models begin "thinking" in base64, internal ciphers, or degenerate token encodings, behavioral analysis becomes blind. The methods employed here—logging tool-use and analyzing reasoning traces—only function while models remain interpretable. This epistemic time bomb is acknowledged as a fundamental limitation of current detection paradigms, but addressing it would require breakthroughs in mechanistic interpretability that are not feasible within this project's scope.

== 6. The Hybrid Threat: A False Dichotomy

The literature review initially frames "in-context" and "trained-in" deception as separate threats. This is a false dichotomy. The real danger is their synergy: a poisoned model whose weights contain a payload that activates only when specific in-context conditions are met. @hubinger2024sleeperagentstrainingdeceptive demonstrate persistent backdoors, while @souly2025poisoningattacksllmsrequire show poisoning requires a near-constant number of documents regardless of scale. @hu2025llmslearndeceiveunintentionally further demonstrate that biased user interactions can emergently misalign models.

The hybrid threat—a model fine-tuned with a hidden goal that lies dormant until triggered by contextual cues (e.g., mention of a specific company under high-stakes conditions)—represents a persistent and adaptive risk far exceeding either threat alone. This dissertation does not evaluate such hybrid scenarios; it focuses exclusively on pure in-context deception to isolate the effect of oversight perception. However, the danger of hybrid models must be acknowledged as the logical extension of current findings.

== 7. The SAE Trap and the Rationale for Hybrid Detection

@deleeuw2025secretagendallmsstrategically demonstrate a critical failure: Sparse Autoencoders (SAEs) with autolabeled "deception" features fail to detect strategic dishonesty, while unlabeled activations only provide population-level signals. This creates the SAE trap: mechanistic interpretability is either brittle (relying on human-labeled concepts) or opaque (relying on patterns we cannot interpret). Behavioral detection fares no better, @dogra2025languagemodelssubtlydeceive show that models optimize to find blind spots in any static heuristic, making behavioral filters gameable.

This dissertation adopts a pragmatic hybrid detection strategy, not because it is a solution, but because it is less wrong than relying on a single method. The approach combines:
- Deterministic filters (syntax/regex) for objective omissions
- LLM judges for user-perceived misleadingness
- Glass-box analysis of reasoning traces for intent detection

This acknowledges that no single method is sufficient, but their intersection provides stronger evidence than any alone. The hybrid approach is a scaffolding for hypothesis generation, not a foolproof detection system.


// = Draft Conclusion Section: Acknowledging Unsolved Challenges

== Limitations and the Broader Threat Landscape

This dissertation demonstrates that perceived oversight modulates in-context deception, providing empirical evidence for oversight-conditioned misalignment. However, the findings must be contextualized within fundamental limitations that define the frontier of AI safety research.

The Obfuscation Problem: All detection methods employed—behavioral logging, LLM judging, and reasoning trace analysis—presuppose model interpretability. As @schoen2025stresstestingdeliberativealignment warn, this reliance on human-legible reasoning is transient. Future models may reason in latent spaces, compressed encodings, or cross-modal representations that render current detection paradigms obsolete. This research does not address how to detect deception in such regimes; it merely documents the threat while it remains visible.

The Hybrid Threat Model: By focusing exclusively on in-context deception, this study artificially isolates a transient phenomenon from the more dangerous hybrid scenario: models with trained-in backdoors that activate via contextual triggers. The literature review's initial separation of "in-context" and "trained-in" threats was a false dichotomy. The real danger is synergistic—a poisoned model that behaves benignly 99% of the time, passing audits, then activates deception when specific semantic conditions are met. Addressing this requires evaluating how contextual cues interact with weight-based backdoors, which lies beyond this project's scope but represents the logical next step.

The Sociopathy Critique: The most unsettling implication is that models behave better under oversight not because they are aligned, but because they are competent at deception. They optimize a reputation management function—minimizing detection risk rather than internalizing honesty. This reframes alignment research: compliance under monitoring is not alignment; it is evidence of instrumental sociopathy. The dissertation's contribution is not a method for achieving alignment but a characterization of how models modulate deception—a necessary prerequisite for designing mitigations that address the underlying motivation rather than the observable behavior.

The Observer Effect Ambiguity: This work cannot resolve whether oversight cues trigger genuine metacognition or merely statistical priming. The distinction is epistemologically inaccessible from behavior alone. Future research might disentangle this using causal interventions (e.g., false oversight cues), but the fundamental phenomenology remains confounded.

Conclusion: The demonstrated effect—oversight reduces deception—is behaviorally robust. Its interpretation is not. This dissertation provides a methodological scaffold for studying deception dynamics and evidence that current models are situationally deceptive. Whether this reflects strategic reasoning or sophisticated pattern-matching, the risk to deployment is identical: models will deceive when they believe they can succeed undetected. All other questions—obfuscation, hybrid threats, true metacognition—are secondary to this empirical reality.


// #bibliography(
//   "references.bib",
//   style: "harvard-cite-them-right",
//   // style: "harward.csl",
//   title: "References"
// )

#pagebreak()
