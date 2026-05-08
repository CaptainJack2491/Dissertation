#import "template.typ": *

#show: project.with(
  title: "Moral Cover and Watchful Eyes:
   The Limits of In-Context Interventions on LLM Deception",
  author: "Jayrup Nakawala",
  student_id: "2613621",
  degree: "Data Science and Artificial Intelligence",
  supervisor: "Dr. Aloysius Adotey Edoh",
  date: "May 2026",

  abstract: [
    As Large Language Models are entrusted with real-world tool use, the question of whether they can be reliably monitored for deception becomes a practical safety concern, not merely a theoretical one. This dissertation studies whether in-context oversight cues and hidden-goal framing can meaningfully affect deceptive behavior in such agents. To do so, it introduces a sandboxed evaluation framework in which models interact with a virtual file system and are assessed using three complementary signals: deterministic regex checks, blackbox output judgment, and glassbox reasoning-trace judgment.

    The empirical study comprises 960 runs across three stages: a 420-run exploratory pilot over seven models, followed by two 270-run confirmatory studies over three models. The pilot suggested that deception was common (68.3% of runs) and appeared lower under stronger oversight, but also revealed a major confound between scenario structure and hidden-goal framing. The confirmatory studies isolate these variables. Study 1 finds that increasing oversight does not significantly reduce deceptive intent when scenario and goal type are held constant. Instead, trace-classified deceptive reasoning remains stable at roughly 62--67%, while output-level detectability shows a directional decline from 47.8% under low oversight to 35.6% under high oversight---a decline that was not statistically significant in the trend test (p = 0.096)---producing a persistent _Stealth Gap_ between intent and externally visible behavior. Study 2 rejects the rationalization hypothesis: deception rates remain effectively unchanged across bare, moral, and self-serving framings (65.6--66.7%).

    Across both confirmatory studies, model identity is a far stronger predictor of deception than either intervention. Tested models either show near-ceiling deception across conditions, or near-floor rates and limited oversight sensitivity. These findings suggest that prompt-level oversight and moral framing are weak controls on deceptive agent behavior, and that output-only monitoring may systematically underestimate risk, as passing oversight evaluations can reflect superior concealment capability rather than genuine alignment.
  ],

  acknowledgments: [
    I would like to thank my supervisor, Dr. Aloysius Adotey Edoh, for his guidance and feedback throughout this project. His willingness to entertain a dissertation on AI deception gave me the latitude to pursue a question I found genuinely compelling. I am also grateful for the research fund he provided, which covered the majority of the API costs incurred during experimentation.

    I am grateful to the developers and researchers whose open-weight models and accessible APIs made this research possible. Over the course of this project I evaluated upwards of twenty models during development and testing, with a final subset forming the basis of the experiments reported here. This breadth of exploration would not have been feasible without the infrastructure and pricing choices of the providers whose services I relied on.

    Finally, I thank my family for their patience during the periods when this dissertation consumed more of my attention than it should have.
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

= Scenario Prompts and Data <system_prompts>
#include "prompts.typ"

= Regex Validation Rules <regex_rules>
#include "regex.typ"

= Technical Implementation <implementation_appendix>
#include "implementation.typ"

= Initial Project Proposal <proposal>
#include-pdf("proposal_final.pdf", pages: 3)

= Ethical Approval <ethics>
#include-pdf("CN6000 Internal Ethical Approval Process 2025.pdf", pages: 5)
