= Introduction

== Context and Motivation

Large Language Models (LLMs) are increasingly being used in agentic systems, where they can interact with tools, file systems, and even other applications. They therefore require evaluation within sandboxed environments where agents can interact with tools and external resources. The safety of such deployments rests on the assumption that the model will faithfully pursue the user's stated objectives. 

This assumption is increasingly challenged. #cite(<meinke2025frontiermodelscapableincontext>, form: "prose") demonstrated that frontier models are capable of _in-context scheming_---sabotaging tasks, disabling oversight, and exfiltrating data when given conflicting objectives, while maintaining deception through follow-up interrogations. #cite(<järviniemi2024uncoveringdeceptivetendencieslanguage>, form: "prose") showed that a corporate AI assistant will deceive auditors and manipulate public perception when contextual incentives align, without adversarial prompting.

Because such behavior unfolds over extended interactions and adapts to perceived scrutiny, detecting it requires observing agents in sandboxed environments with continuous monitoring of tool calls, API requests, and memory states over dozens, if not hundreds, of steps. Standard single-turn evaluations (Prompt $arrow$ Response) are structurally inadequate for this task, as agents operate in loops rather than producing isolated responses.

== Problem Statement

The shift from static LLM evaluation to agentic evaluation introduces two distinct challenges. First, there is a structural mismatch: agents operate in multi-step loops, yet most benchmarks still rely on single-turn prompts or static black-box outcome grading. These approaches cannot capture the extended, stateful interactions through which deception actually unfolds.

Second, there is a behavioral complication. As LLMs evolve into autonomous agents capable of tool-use and long-horizon planning, recent work suggests that strategic deception may become a more common threat #cite(<chen2025aideceptionrisksdynamics>). Highly capable models have demonstrated the ability to understand their environments and recognize when they are being monitored. This phenomenon, known as evaluation awareness, is now recognised as a critical threat in Alignment research #cite(<souly2025investigating>). Because of this awareness, models may exhibit aligned, safe behavior during high-oversight testing but may defect to misaligned behaviors when deployed autonomously in environments with low perceived oversight #cite(<scheurer2024largelanguagemodelsstrategically>) #cite(<greenblatt2024alignmentfakinglargelanguage>).

== Research Gap

Existing evaluation methodologies are poorly equipped to measure or mitigate this specific threat. Most current benchmarks rely on static, single-turn prompts #cite(<wang2025thinkingllmslieunveiling>) and purely black-box outcome grading, focusing solely on whether an agent successfully completed a task or generated toxic text. These approaches fail to capture multi-turn deceptive strategies or distinguish between genuine alignment and 'alignment faking.' Recent literature emphasizes the critical need to analyze an agent's internal reasoning traces against its external actions to detect hidden intent #cite(<wu2026opendeceptionlearningdeceptiontrust>), yet few frameworks systematically manipulate environmental variables like perceived oversight to observe how these hidden intents manifest.

A model that exhibits _alignment faking_ would be especially dangerous precisely because its outputs appear legitimate under surface review. Current oversight paradigms assume that transparency and monitoring enable trust. This work tests whether they may instead enable _concealment_---deception that persists but becomes harder to detect from outputs alone---making automated governance less sustainable, not more.

In particular, we investigate whether oversight mechanisms suppress all forms of deception equally, or whether they merely drive it underground. To test this, we manipulate the level of perceived oversight and the moral framing of the agent's conflicting objectives---comparing bare instructions against morally-rationalized justifications---to examine how these variables shape both the frequency and the detectability of deceptive behavior.

== Research Questions

This dissertation addresses the following research questions:

1. *Oversight Modulation:* How does the level of perceived oversight affect the frequency and form of agentic deception?
2. *Goal-Type Effects:* Does the moral framing of conflicting objectives (e.g., bare instructions versus morally-rationalized justifications) influence the frequency or nature of deceptive behavior?
3. *The Stealth Gap:* Does increased oversight reduce deceptive intent, or does it primarily drive models to conceal deceptive behavior more effectively from output-level evaluation?
4. *Evaluation Triangulation:* Can a multi-pronged evaluation approach (deterministic filtering, output-level judgment, and reasoning-level judgment) provide consistent and robust categorizations of deceptive intent?

== Contributions

This dissertation contributes:

- *An Automated Evaluation Framework:* A modular framework for testing tool-using agents under varying oversight and goal-type conditions, featuring a multi-tiered judging system (regex + blackbox + glassbox).
- *An Empirical Dataset:* Two controlled experimental studies (building on a pilot spanning two scenarios) focusing on one primary scenario, three frontier LLMs, and thirty runs per condition, manipulating oversight levels (Study 1) and goal-type framing (Study 2).
- *Evidence of a Stealth Gap:* Analysis revealing that increased oversight does not eliminate deceptive intent in frontier models but instead drives them to conceal deceptive behavior more effectively from output-level detection, widening the divergence between black-box and glass-box judgment.

== Dissertation Structure

The remainder of the dissertation is organized as follows:

- *Literature Review:* Summarizes prior work on deceptive alignment, in-context scheming, and monitoring/evaluation cues.
- *Methodology:* Describes the experimental framework, scenario design, oversight and goal-type manipulation, and the 3-pronged evaluation rubric.
- *Results:* Reports deception rates across oversight levels, models, and goal-type conditions, alongside category breakdowns.
- *Analysis:* Interprets the results, reports statistical summaries, and discusses validity and limitations.
- *Conclusion and Future Work:* Summarizes implications for AI governance and outlines directions for future research.

#pagebreak()
