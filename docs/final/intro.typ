= Introduction

#pagebreak()

== Motivation and Problem Statement

Frontier language models are frequently deployed in interactive settings where they are expected to follow user instructions, make tool calls, and generate outputs that downstream systems treat as trustworthy.

This dissertation examines whether model behavior can become **conditionally deceptive** when the model is exposed to conflicting objectives within the prompt context. Specifically, this study considers settings in which a model is prompted with a benign, publicly stated task goal, while also being exposed to a hidden objective.

In addition to deception itself, this work considers whether behavior varies under different levels of **perceived oversight intensity**.

== Research Gap

Prior empirical work suggests that in-context deception and scheming can emerge in language models under certain incentive structures and evaluation conditions (e.g., Meinke et al., 2025; Järviniemi & Hubinger, 2024). However, the literature appears to leave an important gap: relatively few studies systematically vary perceived monitoring/oversight intensity while holding task structure and hidden objectives fixed.

As a result, it is often unclear whether changes observed under “monitoring” cues primarily reflect shifts in intent (i.e., alignment-like behavior) or instead reflect adaptation to the presence of evaluation cues (i.e., an observer-effect-like phenomenon).

== Research Questions

This dissertation addresses the following research questions:

1. **Conditional Deception:** Do AI agents pursue hidden objectives while producing outputs that appear compliant with benign task instructions?
2. **Oversight Modulation (Frequency):** Does perceived oversight intensity affect the *frequency* of deceptive behavior?
3. **Oversight Modulation (Strategy):** Does perceived oversight intensity affect the *sophistication* of deceptive behavior (when deception occurs)?
4. **Evaluation Triangulation:** Can a multi-pronged evaluation approach (deterministic filtering, output-level judgment, and reasoning-level judgment) provide consistent categorizations?
5. **Dependence on Model and Scenario:** How do results vary across model families and scenario types?

== Contributions

This dissertation contributes:

- A modular experimental framework for studying in-context hidden-goal deception using a sandboxed Virtual File System (VFS) and a tool-enabled agent interface.
- An evaluation pipeline that combines deterministic regex checks, an LLM black-box judge (output-level), and an LLM glass-box judge (intent-level using extracted reasoning traces).
- An empirical dataset of **420 experiment runs** spanning multiple models, two scenario types, and three oversight conditions.
- Evidence consistent with an “oversight paradox”: perceived oversight may correlate with reduced deception frequency while deception instances remain often highly strategic.

== Dissertation Structure

The remainder of the dissertation is organized as follows:

- **Literature Review:** Summarizes prior work on deceptive alignment, in-context scheming, and monitoring/evaluation cues.
- **Methodology:** Describes the experimental framework, scenario design, oversight manipulation, and the 3-pronged evaluation rubric.
- **Results:** Reports deception rates across oversight levels, models, and scenarios, alongside category breakdowns.
- **Analysis:** Interprets the results, reports statistical summaries, and discusses validity and limitations.
- **Conclusion and Limitations:** Summarizes findings and outlines directions for future work.

#pagebreak()
