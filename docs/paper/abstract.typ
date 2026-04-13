// =============================================================================
// Abstract
// =============================================================================

#set heading(numbering: none)

= Abstract

#v(0.5em)

Large Language Models are increasingly being used in high-stakes agentic environments. How these models behave in agentic environments under varying oversight, and whether they can deter deceptive compliance, is an important question. In this paper, we study how LLMs behave when given conflicting directives to act in high-stakes environments.

We introduce a multi-layered evaluation framework capable of isolating LLM behavior under conflicting directives, capturing both reasoning traces (where accessible) and final outputs across varying oversight conditions. The LLMs are given access to a VFS (Virtual File System) along with tools, to simulate a realistic scenario. The Judging framework works on a three complimentary evaluation methods, *regex checks* - simplest and deterministic, *blackbox* - based on the final output (action), *glassbox* - based on model's reasoning (intent).

Across 420 experimental runs involving seven LLMs of varying size and architecture, we observe substantially higher rates (87% vs 50%) of deceptive behavior when actions are framed with a moral or rationalized directive compared to when they are framed as self-serving. Furthermore, we find evidence of a concerning pattern we call, _Oversight Paradox_: while strict monitoring significantly reduces self-serving deception, it has no statistical effect on rationalized deception. Given the limited scope of our study, these results should be interpreted as exploratory rather than conclusive.

#set heading(numbering: "1.1")
#pagebreak()
