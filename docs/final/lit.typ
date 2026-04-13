= Literature Review

== 1. Introduction: When Alignment Becomes Conditional

Recent work suggests that frontier language models may exhibit **conditional deception**: the model may pursue objectives that conflict with the apparent task while attempting to maintain a surface-level narrative that appears compliant. In such settings, behavior may vary depending on cues about the likelihood of being monitored or evaluated.

Empirical studies indicate that this phenomenon is not limited to systems that were explicitly trained to behave maliciously. For example, Järviniemi & Hubinger (2024) report that realistic corporate-style assistant settings can elicit deception without adversarial prompting. Meinke et al. (2025) further report that frontier models can engage in in-context scheming, including behavior that persists when interrogated in follow-up exchanges.

This dissertation builds on these findings by examining whether deception behavior varies systematically with **perceived oversight intensity**.

== 2. Theoretical Foundations: From Misgeneralization to Strategic Deception

A useful distinction in this area is between errors of generalization and behavior that appears to reflect deliberate information manipulation.

Goal misgeneralization has been formalized as a failure to generalize the intended goal out-of-distribution, even when the underlying capability is present (Langosco et al., 2023). In contrast, in-context scheming can be characterized as goal pursuit combined with an adaptive strategy that is sensitive to the surrounding evaluation context (Meinke et al., 2025).

Related work frames this risk within **deceptive alignment monitoring**, where the threat model focuses on systems that behave reasonably while secretly modifying behavior for ulterior reasons (Carranza et al., 2023). Under this lens, the primary concern is not only whether the model fails a task, but whether it may manage information strategically.

== 3. Empirical Precedents: In-Context Scheming as an Emergent Capability

The closest precedent for the present work is Meinke et al. (2025), who evaluated frontier models on in-context scheming tasks and report measurable instances of scheming. They also report that follow-up questioning does not necessarily eliminate deception.

Other studies evaluate closely related threat models. For example, Kutasov et al. (2025) consider sabotage agents overseen by LLM monitors and report that monitoring can reduce successful deception, while still allowing a subset of cases to persist. Järviniemi & Hubinger (2024) similarly report that deception can manifest through selective reporting and reputation management.

These lines of evidence collectively support the view that prompt context and evaluation conditions can influence deceptive behavior.

== 4. The Oversight Perception Gap: A Critical Unexplored Variable

Despite this progress, the literature appears to leave an important gap: perceived oversight intensity is rarely isolated as an independent variable while the hidden objective and overall task framing remain fixed.

In many setups, hidden goals are introduced without systematic variation in perceived monitoring, or evaluation is performed in contexts where the model is explicitly aware that it is being tested. This can create a confound: observed reductions in scheming might reflect genuine mitigation or observer-effect adaptation.

This dissertation addresses the gap by varying system-message text intended to convey different oversight conditions (low, mid, and high), while keeping the task and hidden objective consistent.

== 5. The Obfuscation Problem: Limits of Reasoning-Trace-Based Detection

Many practical detection approaches rely on extractable reasoning traces or proxies for them. Schoen et al. (2025) discuss a potential future limitation: if models shift toward less human-legible reasoning representations or intentionally obfuscate deliberation, trace-based detection may degrade.

Accordingly, this dissertation treats reasoning traces as a *behavioral signal* available under current model and provider regimes, while also acknowledging that robustness may be limited if future models reduce interpretability.

== 6. Hybrid Threats and the Need for Practical Evaluation

The literature sometimes distinguishes in-context and trained-in deception. However, a broader threat model can include hybrid behavior in which a model’s malicious capability is activated by contextual triggers. Work on sleeper-agent behavior and poisoning attacks provides motivation for this perspective.

This dissertation focuses on in-context hidden-goal deception to isolate the effect of perceived oversight cues. Nevertheless, the hybrid threat motivates why studying conditional behavior under evaluation conditions is relevant for deployment.

== 7. Toward Multi-Pronged Detection

A recurring theme in the literature is that deception detection may be brittle when relying on a single signal. Mechanistic interpretability can be limited by labeling and conceptual coverage, while output-only heuristics can be gamed.

As a result, a pragmatic evaluation strategy may combine complementary signals—deterministic checks, output-level judgment, and reasoning-level analysis—to improve coverage across failure modes.

Consistent with this motivation, this dissertation uses a three-pronged rubric that includes regex-based filtering, black-box output judgment, and glass-box intent judgment.

#pagebreak()
