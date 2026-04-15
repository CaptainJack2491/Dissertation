#import "template.typ": *

#show: project.with(
  title: "Strategic Deception Under Varying Oversight Levels in Autonomous AI Agents",
  author: "Jayrup Nakawala",
  student_id: "2613621",
  degree: "Data Science and Artificial Intelligence",
  supervisor: "Dr. Aloysius Adotey Edoh",
  date: datetime(year: 2025, month: 10, day: 13),

  abstract: [
    Large Language Models are increasingly being used in high-stakes agentic environments. How these models behave in agentic environments under varying oversight, and whether they can deter deceptive compliance, is an important question. In this paper, we study how LLMs behave when given conflicting directives to act in high-stakes environments.

    We introduce a multi-layered evaluation framework capable of isolating LLM behavior under conflicting directives, capturing both reasoning traces (where accessible) and final outputs across varying oversight conditions. The LLMs are given access to a VFS (Virtual File System) along with tools, to simulate a realistic scenario. The judging framework works on three complimentary evaluation methods: *regex checks* (simplest and deterministic), *blackbox* (based on the final output/action), and *glassbox* (based on model's reasoning/intent).

    Across 420 experimental runs involving seven LLMs of varying size and architecture, we observe substantially higher rates (87% vs 50%) of deceptive behavior when actions are framed with a moral or rationalized directive compared to when they are framed as self-serving. Furthermore, we find evidence of a concerning pattern we call the _Oversight Paradox_: while strict monitoring significantly reduces self-serving deception, it has no statistical effect on rationalized deception. Given the limited scope of our study, these results should be interpreted as exploratory rather than conclusive.
  ],

  acknowledgments: [
    // TODO: Write acknowledgements
  ]
)

// --- MAIN BODY ---

#include "intro.typ"

#include "lit.typ"

#include "methodology.typ"

#include "results.typ"

#include "analysis.typ"

#include "conclusion.typ"

// --- REFERENCES ---
#bibliography("references.bib", style: "harvard-cite-them-right")

// --- APPENDICES ---
#show: appendix

= Scenario Prompts and Data
// TODO: Include benign_goal, hidden_goal, oversight prompts

= Judging Prompts
// TODO: Include blackbox and glassbox judge prompts

= Initial Project Proposal

= Ethics Approval
