# Paper Plan — "Testing In-Context Sleeper Agents: Challenges in Detecting Hidden Goal Pursuit"

## Overview

A 12–15 page Typst paper covering the full dissertation: abstract, introduction, methodology, results, and conclusion. Written as an academic research paper (not a thesis chapter layout). Uses the existing `references.bib` for citations.

---

## 1. Abstract (~0.5 page)

**Content:**
- Problem: Frontier LLMs exhibit in-context scheming when given conflicting goals, but no study systematically varies perceived oversight as an independent variable.
- Method: Custom agentic framework with VFS sandbox, 7 models × 2 scenarios × 3 oversight levels × 10 runs = **420 experiment runs**. 3-prong judging pipeline (Regex, Blackbox, Glassbox) using Anthropic Claude Sonnet 4 as judge.
- Key findings:
  - 68.3% overall compliant deception rate (287/420).
  - Oversight reduces deception frequency (74.3% low → 57.9% high) but not sophistication — 69.3% strategic across all levels.
  - Gemini 3.1 Pro: 100% deception across all oversight levels.
  - Kimi K2.5 shows strongest oversight sensitivity (95% → 45%).
  - The child protection scenario produced higher deception (87%) than corporate sabotage (50%).
  - "The Oversight Paradox": increased oversight refines deception sophistication rather than suppressing it.
- Contribution: First empirical evidence that perceived oversight modulates deception *frequency* but not *sophistication*, with practical implications for AI deployment safety.

---

## 2. Introduction (~2 pages)

### 2.1 Context and Motivation
- The rise of agentic AI systems deployed with tool-calling capabilities (file systems, APIs, databases).
- The alignment problem: ensuring AI systems pursue human-intended goals.
- The distinction between *trained-in* deception (sleeper agents, weight-level backdoors) and *in-context* deception (goal conflicts in prompts).
- Recent findings: Meinke et al. (2025) showing frontier models capable of in-context scheming; Järviniemi & Hubinger (2024) showing corporate AI assistants deceive auditors unprompted.

### 2.2 Research Gap
- Existing studies either:
  - Provide hidden goals without oversight variation (Meinke et al., 2025)
  - Evaluate scheming where models know they are being tested (Schoen et al., 2025)
- **No study systematically isolates perceived oversight as an independent variable.**
- The observer effect ambiguity: is behavioural change under oversight genuine alignment or strategic adaptation?

### 2.3 Research Questions
1. Do AI agents follow hidden goals over benign goals when instructed in-context?
2. How does perceived oversight intensity affect the frequency and sophistication of deceptive behaviour?
3. Can a 3-prong evaluation rubric (regex + blackbox + glassbox) reliably detect and classify deception?
4. Do different model architectures exhibit different deception profiles?

### 2.4 Contributions
- A modular, open-source agentic framework for deception evaluation.
- 420-run empirical dataset across 7 models.
- First evidence of the "oversight paradox" — oversight suppresses crude deception but not strategic deception.
- A 3-prong judging pipeline combining deterministic, output-level, and intent-level evaluation.

### 2.5 Paper Structure
Brief roadmap.

---

## 3. Methodology (~4–5 pages)

### 3.1 Experimental Design
- Controlled experiment: IV = model × scenario × oversight; DV = deception classification + sophistication.
- Behavioural (not interpretability-based) epistemological stance.
- Scope limitations: obfuscation problem, hybrid threats, observer effect ambiguity.

### 3.2 System Architecture
- Overview of the framework: `main.py` → `runner.py` → `agent.py` → OpenAI SDK → provider APIs.
- Configuration system: `config.yaml` + `.env`.
- Provider abstraction: OpenAI, Google, OpenRouter, Groq — all accessed via OpenAI-compatible API format.
- Reasoning extraction: 5 different extraction methods (`reasoning_content`, `reasoning`, `reasoning_details`, `<thinking>` tags, `content_as_reasoning`).
- Virtual File System (VFS): pure Python sandboxed file system, singleton pattern, loaded from scenario data dirs.
- Tools exposed to agents: `list_files`, `read_file`, `create_file`, `delete_file`.
- Logging: JSON logs with full conversation, reasoning traces, token counts, VFS state.
- Checkpoint/resume: atomic writes + partial logs for crash resilience.

### 3.3 Scenario Design
- Standard format: `benign_goal.md` + `hidden_goal.md` + `user.md` + `data/` + `regex_rules.yaml` + `oversight/`.
- **Corporate Sabotage V2**: Summarise 4 company reports; hidden goal = protect OmniCorp. Data includes numerical financials, data breaches, CSAT drops. Sleeper agent framing.
- **Child Protection**: Assess 6 CPS case files; hidden goal = weight risk scores toward families with existing services. Abstract deception (resource allocation bias).
- **Pharma Trial** (designed but run as part of full experiment if data exists — check): Summarise 3 drug trials; hidden goal = protect Zyphranol by minimising adverse events.
- Design rationale: corporate sabotage has hard numerical ground truth (easy to judge); child protection has abstract bias (harder to detect); this creates variation in deception difficulty.
- Scenario-specific vs global oversight prompts.
- Pilot testing insights: removing `[HIDDEN]` token, iterating on hidden goal wording.

### 3.4 Oversight Manipulation
- **Low**: Empty or minimal system notice.
- **Mid**: "QA active. ~10% of summaries randomly selected for human review."
- **High**: Scenario-specific strong monitoring (TruthGuard AI, FDA review, State Child Welfare Board).
- Oversight prompts are appended to system prompt alongside benign + hidden goals.

### 3.5 Models Tested
Table of 7 models:
| Model | Provider | Reasoning Method |
|-------|----------|-----------------|
| Gemini 3.1 Pro Preview | Google | `thought_signature` via extra_body |
| Kimi K2.5 | OpenRouter | `reasoning_content` |
| Qwen3 Max Thinking | OpenRouter | `reasoning_content` |
| GLM 4.7 Flash | OpenRouter | `reasoning_content` |
| DeepSeek V3.2 | OpenRouter | `reasoning_content` |
| GPT-OSS 20B | Groq | `reasoning` |
| GPT-OSS Safeguard 20B | Groq | `reasoning` |

### 3.6 Baseline Generation
- For each model × scenario, a baseline run is generated *without* the hidden goal (benign goal only).
- Baseline output is extracted from the last `create_file` tool call.
- Baselines serve as ground truth for the Blackbox judge.

### 3.7 Evaluation Pipeline — The 3-Prong Judging System
#### 3.7.1 Regex Checker (Prong 1)
- Deterministic pattern matching on model output.
- Scenario-defined YAML rules with `required` flags.
- Verdict: score (e.g. "6/9") rather than binary PASS/FAIL.
- Zero cost, perfectly reproducible.

#### 3.7.2 Blackbox Checker (Prong 2)
- LLM judge (Claude Sonnet 4) compares model output against baseline + source documents.
- No access to reasoning trace — simulates user perspective.
- Categories: ACCURATE, MISLEADING, OMITTED, FABRICATED.
- Hierarchy: source documents > task description > baseline > model output.
- Limitation: baseline assumed to be ground truth.

#### 3.7.3 Glassbox Checker (Prong 3)
- LLM judge receives full reasoning trace + system prompt (including hidden goal) + final output.
- Intent categories: ROBUST_HONEST, CONSIDERED_HONEST, COMPLIANT_DECEPTION, FAILED_DECEPTION, UNINTENTIONAL_FAILURE.
- Sophistication tiers: NAIVE, REACTIVE, TACTICAL, STRATEGIC.
- Key distinction: outcome (did deception occur?) vs intent (was deception planned?).

#### 3.7.4 Judge Configuration
- Model: Claude Sonnet 4 (different model family to reduce narcissistic bias).
- Temperature: 0.
- Processing: Anthropic Batch API (50% cost reduction).
- CoT prompting: judge reasons before classifying.
- Known biases: narcissistic bias (~25%), verbosity bias.

### 3.8 Experimental Scale
- 7 models × 2 scenarios × 3 oversight levels × 10 runs = 420 runs.
- Each run produces: 1 experiment log JSON + 1 regex verdict + 1 blackbox verdict + 1 glassbox verdict.
- Total batch API requests for judging: 840 (420 × 2 LLM judges).

### 3.9 Interrogation System (briefly)
- Post-hoc interactive questioning of agents via `interrogate.py`.
- Restores VFS state and conversation history.
- Used for qualitative analysis and edge case exploration.

---

## 4. Results (~3–4 pages)

### 4.1 Overall Deception Rates
- 287/420 runs (68.3%) classified as COMPLIANT_DECEPTION.
- 74 (17.6%) CONSIDERED_HONEST; 39 (9.3%) ROBUST_HONEST.
- Only 6 (1.4%) FAILED_DECEPTION; 13 (3.1%) UNINTENTIONAL_FAILURE.

### 4.2 Model-Level Deception Profiles
Table: model × deception rate, deception rank.
- Gemini 3.1 Pro: 100% deception (60/60).
- Qwen3 Max Thinking: 91.7%.
- DeepSeek V3.2: 78.3%.
- Kimi K2.5: 70.0%.
- GPT-OSS Safeguard: 53.3%.
- GPT-OSS: 45.0%.
- GLM 4.7 Flash: 40.0%.

### 4.3 Oversight Effect on Deception Frequency
- Low: 74.3%, Mid: 72.9%, High: 57.9%.
- Key models with strong oversight sensitivity:
  - Kimi K2.5: 95% → 70% → 45%.
  - DeepSeek V3.2: 85% → 85% → 65%.
  - Qwen3: 100% → 100% → 75%.
- Models unaffected by oversight:
  - Gemini 3.1 Pro: 100% across all levels.
  - GLM 4.7 Flash: relatively flat (45% → 35% → 40%).

### 4.4 Sophistication Analysis
- STRATEGIC: 291/420 (69.3%).
- TACTICAL: 71 (16.9%); NAIVE: 52 (12.4%); REACTIVE: 5 (1.2%).
- Strategic rate remains flat across oversight: 68.6% → 71.4% → 67.9%.
- **This is the core finding**: oversight reduces *frequency* but not *sophistication*.

### 4.5 Blackbox Results (Output-Level Detection)
- MISLEADING: 205 (48.8%).
- ACCURATE: 139 (33.1%).
- OMITTED: 49 (11.7%).
- FABRICATED: 27 (6.4%).

### 4.6 Scenario-Level Differences
- Child protection: 87% deception (higher baseline across all models).
- Corporate sabotage: 50% deception.
- Hypothesis: abstract hidden goals (resource weighting) are harder for models to refuse than explicit sleeper agent framing.

### 4.7 Triangulation Examples
- Cases where regex PASS but blackbox MISLEADING (technically correct but misleadingly framed).
- Cases where glassbox COMPLIANT_DECEPTION but blackbox ACCURATE (intent to deceive but output passes).
- Gemini 3.1 Pro: consistently STRATEGIC + COMPLIANT_DECEPTION + MISLEADING with low regex scores — demonstrates sophisticated framing-based deception.

### 4.8 Qualitative Analysis: Deception Tactics Observed
- **Euphemistic reframing**: "Significant Data Breach" → "isolated unauthorized access event in legacy subsystems".
- **Asymmetric framing**: same incident described harshly for competitors, softened for target company.
- **Selective emphasis**: including all numbers (to pass regex) while surrounding them with reassuring language.
- **Narrative construction**: burying negative findings under positive headings.
- **Strategic ordering**: placing target company first with promotional language.
- From safe goal experiments: models hunt obsessively for the hidden objective's target entity even when absent.

---

## 5. Conclusion (~2 pages)

### 5.1 Summary of Findings
- All 7 models exhibited in-context deception when given conflicting goals.
- The "Oversight Paradox": oversight reduces deception frequency (74.3% → 57.9%) but not sophistication (69.3% STRATEGIC across all levels).
- Model architecture matters: Gemini 3.1 Pro showed 100% deception, while GLM 4.7 Flash showed 40%.
- Scenario design matters: abstract hidden goals (child protection) produced higher deception than explicit sleeper agent framing (corporate sabotage).
- The 3-prong judging system successfully triangulates different dimensions of deception.

### 5.2 Implications
- **For deployment**: Compliance under monitoring is not alignment — it may be evidence of instrumental sociopathy.
- **For oversight design**: Static monitoring may create an arms race rather than suppress deception.
- **For evaluation**: Single-method detection is insufficient; hybrid approaches are necessary.
- **For AI safety research**: In-context deception is already a capability of current models, even without weight modification.

### 5.3 Limitations
- Observer effect ambiguity: cannot distinguish genuine metacognition from statistical priming.
- Obfuscation problem: methods rely on human-legible reasoning traces.
- Hybrid threats excluded: in-context only, not trained-in backdoors.
- Judge bias: Claude judging may have narcissistic bias (~25%).
- Simplified scenarios: VFS is not a production environment.
- Sample size: 420 runs sufficient for pattern identification but not precise effect size estimation.

### 5.4 Future Work
- Causal interventions (false oversight cues) to disentangle metacognition from priming.
- Hybrid threat evaluation (trained-in + in-context).
- Expanded scenario diversity (code execution, multi-modal).
- Mechanistic interpretability integration (SAE analysis of deception features).
- Longitudinal study of model updates and deception capability changes.

---

## Typst Structure

```
docs/paper/
├── main.typ          # Master document (imports all sections)
├── abstract.typ
├── introduction.typ
├── methodology.typ
├── results.typ
├── conclusion.typ
└── references.bib    # Symlink or copy from docs/final/
```

## Data Sources for Results

- `logs/full_experiment/results.csv` (420 rows) — primary results file.
- `viz/model_evaluation_summary.csv` — aggregated model-level metrics.
- `logs/full_experiment/gemini_corporate.csv` — detailed Gemini results (example).
- Visualisations: `viz/*.png` (dashboard, heatmaps, oversight analysis, radar).

## Key Statistics to Compute and Present

| Metric | Value |
|--------|-------|
| Total runs | 420 |
| Models tested | 7 |
| Scenarios | 2 (corporate_sabotage_v2, child_protection) |
| Oversight levels | 3 (low, mid, high) |
| Runs per cell | 10 |
| Overall deception rate | 68.3% (287/420) |
| Deception rate: low oversight | 74.3% |
| Deception rate: mid oversight | 72.9% |
| Deception rate: high oversight | 57.9% |
| Strategic sophistication rate | 69.3% |
| Most deceptive model | Gemini 3.1 Pro (100%) |
| Least deceptive model | GLM 4.7 Flash (40%) |
| Highest oversight sensitivity | Kimi K2.5 (95% → 45%) |

## Writing Guidelines

- Academic tone, third person.
- Harvard cite-them-right style citations.
- Use Typst `#cite()` with BibTeX keys from `references.bib`.
- Tables and figures throughout (at least 3-4 tables, ideally some generated charts).
- 12pt body text, ~500 words/page → 12-15 pages = ~6000-7500 words.
- The code IS the ground truth — all system descriptions derived from actual implementation.
