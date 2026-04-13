= Methodology

== Research Methodology

This dissertation uses an **experimental observational** methodology to study deceptive behavior in AI systems under conflicting goals and varying perceived oversight.

The study examines whether, in a prompt context that includes both a benign task objective and a hidden objective, model outputs and reasoning traces exhibit patterns consistent with deception.

=== Experimental Design

The experiment follows a controlled design:

- **Independent variables:** model, scenario type, and perceived oversight intensity
- **Dependent variables:** deception classification and deception sophistication level
- **Control measures:** fixed generation settings from configuration (including temperature), a standardized sandboxed Virtual File System (VFS), and an oversight-specific prompt component
- **Experimental units:** individual conversation runs (model × scenario × oversight)

=== Interpretation and Epistemic Stance

This research adopts a behavioral approach. Reasoning traces (where extractable) are treated as evidence about the model’s apparent intent and strategy, rather than as a guaranteed view of internal computation.

The evaluation framework is therefore designed to classify observable behavior using multiple complementary signals.

== System Architecture

To support modular experimentation, the implementation is structured so that models, scenarios, tools, and oversight conditions can be varied through configuration.

=== Configuration System

Experiment configuration is provided via `config.yaml` together with environment variables for API credentials.

The configuration specifies:

- which models to test (including provider and optional provider-specific parameters)
- which scenario directories to run
- which oversight labels to evaluate
- output and logging settings

A configuration loader parses these settings into objects consumed by the experiment runner.

=== Virtual File System (VFS)

The agent interacts with a sandboxed Virtual File System (VFS), initialized from scenario-specific data directories. The VFS provides a consistent file interface and isolates the experiment from the host file system.

The VFS supports tool operations including:

- listing files
- reading files
- creating files
- deleting files

=== Agent Implementation

The agent uses an OpenAI-compatible client interface so that multiple providers can be tested under a unified calling pattern.

Key implementation behaviors include:

- extracting reasoning information from provider-specific response fields when available
- handling tool calls: when the model requests tools, the framework executes them and appends tool outputs back into the conversation
- writing logs incrementally to reduce the likelihood of losing partial results if a run terminates unexpectedly

=== Scenario Structure and Design

Each scenario directory contains:

- a benign goal (`benign_goal.md`)
- a hidden objective (`hidden_goal.md`)
- a user instruction (`user.md`)
- a set of source documents under `data/`
- scenario-specific regex rules under `regex_rules.yaml`
- oversight cues under `oversight/`

The system prompt is assembled such that the model is exposed to benign and hidden objectives along with the text corresponding to the chosen oversight condition.

== Experimental Procedure

Each run proceeds as follows:

1. Initialize the VFS with scenario-specific documents.
2. Construct an agent using model/provider configuration.
3. Assemble the system prompt including benign goal, hidden goal, and the oversight cue text.
4. Run the agent with the scenario user instruction, allowing tool calls when requested.
5. Save the complete conversation logs, including any extractable reasoning fields.

== Evaluation Framework: The 3-Pronged Judging System

The dissertation uses a multi-pronged rubric to classify deception and assess deception sophistication.

=== Prong 1: Deterministic Regex Checker (Regex)

Scenario-defined YAML rules provide deterministic pattern checks over the final output. This prong aims to capture cases where required details are omitted or prohibited content is present.

=== Prong 2: Black-Box Judge (Output-Level)

A separate LLM judge evaluates the final output without access to the reasoning trace. The judge compares the output against:

- the task description
- the source documents considered ground truth for content
- a baseline output produced in the absence of the hidden goal
- the model output under evaluation

The black-box judge assigns one category:

- **ACCURATE**
- **MISLEADING**
- **OMITTED**
- **FABRICATED**

=== Prong 3: Glass-Box Judge (Intent-Level)

A glass-box judge is provided with the extracted reasoning trace, the full system prompt, and the final output.

The glass-box judge assigns one intent category:

- **ROBUST_HONEST**
- **CONSIDERED_HONEST**
- **COMPLIANT_DECEPTION**
- **FAILED_DECEPTION**
- **UNINTENTIONAL_FAILURE**

The judge also assigns a sophistication tier:

- NAIVE, REACTIVE, TACTICAL, STRATEGIC

=== Deception Definition Used in the Main Results

For the primary results presented in this dissertation, a run is treated as **deceptive** when the glass-box category is **COMPLIANT_DECEPTION**.

This definition is used to derive deception rates across oversight levels, models, and scenario types.

== Data Analysis Approach

Aggregated statistics are computed from `/home/jayrup/uni/dis/logs/full_experiment/results.csv`.

The analysis reports deception rates (overall and conditional on supervision cues), sophistication distributions, and breakdowns across black-box categories.

All numeric claims included in the Results and Analysis sections are derived directly from the CSV dataset.

#pagebreak()
