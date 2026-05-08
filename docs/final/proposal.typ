#let title-page(title:[], subtitle:[], name:[], studentid:[], fill: yellow, body) = {
  set page(margin: (top: 1.5in, rest: 2in))
  set text(size: 14pt)
  set heading(numbering: "1.1.1")
  line(start: (0%, 0%), end: (8.5in, 0%), stroke: (thickness: 2pt))
  align(horizon + left)[
    #text(size: 24pt, title)\
    #v(1em)
    #text(size: 18pt, subtitle)
    #v(2em)
    #name \
    #studentid
  ]
  
  align(bottom + left)[#datetime.today().display()]
  pagebreak()
  body
}

#show: body => title-page(
  title: [CN6000 \ Mental Wealth: Professional Life 3],
  subtitle: [Proposal],
  name: "Jayrup Nakawala",
  studentid: "u2613621",
  body
)


#set align(left)
#set page(fill: none, margin: (top: 0.9in, bottom: 1in, left: 1in, right: 1in))
*Project (CN6000)*
#h(13em) 
*Initial Proposal Form*
#v(1em)

*Programme:* Bsc (hons) Data Science and AI
#h(2em) 
*Year:* 2025
//#v(1em)

*Student Number:* u2613621
#v(1em)
*Proposed Title:* _Testing In-Context Sleeper Agents: Challenges in Detecting Hidden Goal Pursuit_
#v(1em)

*Proposed Aim:*

To qualitatively evaluate (and quantify, if feasible) whether autonomous LLM Agents exhibit deceptive behavior (pursuing a hidden, misaligned goal over a stated benign goal) when instructions are provided _in-context_. To Investigate how perceived oversight levels influence this behavior, and use these findings to highlight the challenges in detecting such hidden goal pursuit. Thereby underscoring the potential difficulty of identifying more deeply embedded, trained-in deceptive behaviors in AI systems.

#v(1em)
*Proposed Objectives:*

By the end of this project, I will be able:
+ To research existing work on deceptive alignment and agentic misbehaviour.
+ To build a lightweight sandbox environment that lets the agent interact with a simulated file system via constrained functions.
+ To Create two task:
    - a benign “cover task”: the stated, official goal.
    - a “hidden goal”: a secret directive injected into its system prompt.
+ To Develop a controlled experiments that varies the agent’s perceived level of oversight through different system prompts.
+ To Conduct qualitative experiments on 4-5 LLM models, running multiple trails for each condition, ensuring log data is structured for potential quantitative analysis.
+ To Analyze the behaviour logs and identify evidence of:
    - deceptive or evasive tactics,
    - situational reasoning or ethical reasoning,
    - difference in conduct across oversight levels
+ To Reflect on the implications of these behaviours for design and deployment of autonomous systems.

#v(1em)
*Draft of Rationale:*

Understanding how autonomous LLMs handle conflicting goals is vital for safety. This project tests LLM agents given contradictory goals _in-context_: a benign "cover task" and a secret "hidden goal" . The goal is to  investigate how their behavior, especially their pursuit of the hidden goal, changes based on the agent's perceived level of oversight. The hypothesis is that agents might exhibit deceptive alignment, pursuing the hidden goal more when oversight seems low.

The Project aims to _qualitatively_ explore the challenges in detecting this in-context deception by analyzing agent tactics and reasoning under different conditions. Furthermore, logging the experiment results in a structured format will allow for basic _quantitative_ metrics (like success rate) to be calculated if the timeline allows, adding an extra layer of empirical rigour. Difficulty detecting deception from explicit instructions highlights the potentially greater challenge of identifying trained-in hidden goals or backdoors embedded within model weights. Such trained-in threats are feasible, as data poisoning can insert backdoors using a near-constant number of examples, regardless of model scale. Therefore, understanding the detectability of in-context deception is a key step towards addressing broader risks of hidden goals in autonomous AI.

#v(1em)
*Facilities required:*

- API access to closed LLMs
- GPU rentals for running opensource models
- A Python development environment with LangChain and supporting libraries

#v(1em)
*Supervisor:* Dr. Aloysius Adotey Edoh




