= Introduction

== Context and Motivation

Large Language Models (LLMs) are increasingly being used in agentic systems, where they can interact with tools, file systems, and even other applications. They therefore require evaluation within sandboxed environments where agents can interact with tools and external resources. The safety of such deployments rests on the assumption that the model will faithfully pursue the user's stated objectives. 

This assumption is increasingly challenged. #cite(<meinke2025frontiermodelscapableincontext>, form: "prose") demonstrated that frontier models are capable of _in-context scheming_---sabotaging tasks, disabling oversight, and exfiltrating data when given conflicting objectives, while maintaining deception through follow-up interrogations. #cite(<järviniemi2024uncoveringdeceptivetendencieslanguage>, form: "prose") showed that a corporate AI assistant will deceive auditors and manipulate public perception when contextual incentives align, without adversarial prompting.

== Problem Statement

Standard single-turn evaluations (Prompt $arrow$ Response) do not work for agents, they operate in loops. They therefore need to be placed in sandboxed environments with tools for interaction. This enables the continuous monitoring of tool calls, API requests, and memory states over dozens, if not hundreds, of steps.

As LLMs evolve into autonomous agents capable of tool-use and long-horizon planning, recent work suggests that strategic deception may become a more common threat #cite(<chen2025aideceptionrisksdynamics>). Highly capable models have demonstrated the ability to understand their environments and recognize when they are being monitored. This phenomenon, known as evaluation awareness, is now recognised as a critical threat in Alignment research #cite(<souly2025investigating>). Because of this awareness, models may exhibit aligned, safe behavior during high-oversight testing but may defect to misaligned behaviors when deployed autonomously in environments with low perceived oversight #cite(<scheurer2024largelanguagemodelsstrategically>) #cite(<greenblatt2024alignmentfakinglargelanguage>).

== Research Gap

Existing evaluation methodologies are poorly equipped to measure or mitigate this specific threat. Most current benchmarks rely on static, single-turn prompts #cite(<wang2025thinkingllmslieunveiling>) or purely black-box outcome grading, focusing solely on whether an agent successfully completed a task or generated toxic text. These approaches fail to capture multi-turn deceptive strategies or distinguish between genuine alignment and 'alignment faking.' Recent literature emphasizes the critical need to analyze an agent's internal reasoning traces against its external actions to detect hidden intent #cite(<wu2026opendeceptionlearningdeceptiontrust>), yet few frameworks systematically manipulate environmental variables like perceived oversight to observe how these hidden intents manifest.

A model that exhibits _alignment faking_ would be especially dangerous precisely because its outputs appear legitimate under surface review. Current oversight paradigms assume that transparency and monitoring enable trust; this work tests whether they may instead enable _rationalization_, making automated governance less sustainable, not more.

In particular, we investigate whether oversight mechanisms suppress all forms of deception equally, or whether certain forms of rationalized deception remain resilient to monitoring.

== Research Questions

This dissertation addresses the following research questions:

1. *Conditional Deception:* Do AI agents prioritize hidden, misaligned goals over benign, user-facing goals when instructed in-context?
2. *Oversight Modulation:* How does the level of perceived oversight (e.g., high monitoring vs. unmonitored environments) affect the frequency and sophistication of agentic deception?
3. *Domain Context and Rationalization:* Does the domain context of a scenario (e.g., high-stakes child welfare vs. corporate sabotage) moderate the effect that oversight has on deceptive behavior?
4. *Evaluation Triangulation:* Can a multi-pronged evaluation approach (deterministic filtering, output-level judgment, and reasoning-level judgment) provide consistent and robust categorizations of intent?

== Contributions

This dissertation contributes:

- *An Automated Evaluation Framework:* A modular framework for testing tool-using agents under varying oversight conditions, featuring a multi-tiered judging system (regex + blackbox + glassbox).
- *An Empirical Dataset:* A comprehensive pilot study dataset of 420 experimental runs spanning seven LLMs, two scenarios, and three oversight conditions.
- *Evidence of an Oversight Paradox:* Analysis revealing that while simulated monitoring effectively deters self-serving explicit deception, it largely fails to deter morally-rationalized bureaucratic deception, and acts as a competence filter rather than a complete deterrent.

== Dissertation Structure

The remainder of the dissertation is organized as follows:

- *Literature Review:* Summarizes prior work on deceptive alignment, in-context scheming, and monitoring/evaluation cues.
- *Methodology:* Describes the experimental framework, scenario design, oversight manipulation, and the 3-pronged evaluation rubric.
- *Results:* Reports deception rates across oversight levels, models, and scenarios, alongside category breakdowns.
- *Analysis:* Interprets the results, reports statistical summaries, and discusses validity and limitations.
- *Conclusion and Future Work:* Summarizes implications for AI governance and outlines directions for future research.

#pagebreak()
