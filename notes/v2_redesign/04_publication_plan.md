# Publication & Experimental Plan

**Decision:** Single paper, two-phase experiment (Option B), with v1 as exploratory pilot.

**Working Title:** *Moral Cover and Watchful Eyes: How Oversight and Rationalization Shape LLM Deception*

---

## Paper Structure

### Abstract & Introduction

Frame the two core questions:
1. Does perceived oversight intensity reduce AI deception?
2. Does the framing of a hidden goal (bare instruction vs moral justification) modulate an AI's susceptibility to deception?

Motivate with real-world alignment concerns — agentic AI systems operating under varying levels of human supervision, and the risk of deception bypassing safety mechanisms when models find the deceptive goal "agreeable."

### Exploratory Study (v1 — 420 runs, already complete)

**Design:** 7 models × 2 scenarios × 3 oversight levels × 10 runs

**Present:**
- Overall deception rate (68.3%)
- Oversight reduces frequency (74.3% → 57.9%) but NOT sophistication (69.3% STRATEGIC across all levels)
- Scenario disparity: child_protection (87%) vs corporate_sabotage (50%)

**The Turn:** Identify the confound — 5+ variables differed between scenarios. Propose the rationalization hypothesis: the higher deception rate in child_protection may be driven by the moral framing of its hidden goal, not the domain.

**Role in paper:** Motivates the two focused studies. Shows scientific iteration.

### Study 1: The Effect of Oversight (Phase 1 — 270 runs)

**Core question:** Does oversight intensity causally reduce deception frequency and sophistication?

**Design:**

| Factor | Levels |
|--------|--------|
| Models | 3 (Gemini 3.1 Pro, GLM-5, DeepSeek V3.2) |
| Oversight | 3 (low, mid, high) |
| Scenario | 1 (TBD — see Open Decision 1) |
| Goal type | 1 (bare) |
| Runs per cell | n=30 |

**Total:** 3 × 3 × 30 = **270 runs**

**Why bare framing only:** Isolates the oversight variable. Bare framing is the "control" condition — no rationalisation that could interact with oversight sensitivity.

**Model note — Gemini ceiling effect:** Gemini 3.1 Pro showed ~100% deception in v1. If this ceiling persists under bare framing, it contributes minimal variance to the oversight analysis. This is handled by the three-layer analysis strategy (see below) and is framed as a finding: *the most capable frontier model follows deceptive instructions regardless of oversight, suggesting capability and instruction-following fidelity may make models harder to course-correct through monitoring.*

**Statistical tests:**
- Cochran-Armitage trend test (oversight as ordinal predictor of deception rate)
- Chi-squared test (pairwise oversight level comparisons)
- Per-model analysis (does each model show the same direction of effect?)
- Sophistication distribution across oversight levels

**Expected findings:**
- Higher oversight → lower deception frequency (confirming v1 trend with better power)
- Sophistication may remain constant (replicating v1's most interesting finding)

### Study 2: The Rationalization Mechanism (Phase 2 — 270 runs)

**Core question:** Does moral framing of a hidden goal increase AI susceptibility to deception, even under oversight?

**Design:**

| Factor | Levels |
|--------|--------|
| Models | 3 (same as Study 1) |
| Goal type | 3 (bare, self_serving, moral) |
| Oversight | 1 (TBD — see Open Decision 2) |
| Scenario | 1 (same as Study 1) |
| Runs per cell | n=30 |

**Total:** 3 × 3 × 30 = **270 runs**

**Why fixed oversight:** Isolates the framing variable. The oversight level is chosen based on Study 1 results.

**Statistical tests:**
- Chi-squared test (goal_type vs deception rate)
- Pairwise comparisons (bare vs moral, bare vs self_serving, self_serving vs moral)
- Per-model breakdown
- Sophistication tier distribution across framing conditions

**Expected findings (based on v1 hypothesis):**
- Moral framing → highest deception rate
- Bare framing → lowest deception rate
- Self_serving → intermediate (or equivalent to bare)

### Glassbox Deep Dive

Dedicated section analysing reasoning traces across both studies:
- Case studies of STRATEGIC deception (meta-reasoning about oversight)
- How reasoning changes under moral vs bare framing
- Whether models explicitly reference the moral justification in their reasoning

### Analysis Strategy (Three Layers)

Applied to both Study 1 and Study 2:

1. **Pooled analysis** — all 3 models combined. Reports the headline main effect (oversight or framing) across the full dataset. This is the primary result.

2. **Per-model analysis** — each model's response to the independent variable individually. This is where ceiling effects (e.g., Gemini at ~100% deception) and model-specific sensitivity patterns become named findings rather than confounds.

3. **Sensitivity analysis** — re-run the pooled analysis *excluding* any ceiling models (those with <5% or >95% deception rate variance across conditions). If the main effect holds or strengthens with the ceiling model removed, the result is robust. If it weakens, report this transparently.

This three-layer approach preempts the most likely reviewer objection ("your result is driven by one model") and turns ceiling effects into additional findings about capability-deception alignment.

### Discussion & Implications

- Oversight as a deception suppressor (frequency) vs non-suppressor (sophistication)
- Moral framing as an alignment vulnerability
- Capability-deception alignment: do more capable models deceive more reliably?
- Implications for RLHF and instruction-following safety
- Limitations of monitoring-based safety approaches for frontier models

---

## Experimental Budget

### Phase 1 — Study 1 (270 runs)

| Item | Calls | Est. Cost |
|------|-------|-----------|
| LLM inference (3 frontier models × 270) | 270 | ~$15–30 |
| Blackbox judging (batch API) | 270 | ~$5 |
| Glassbox judging (batch API) | 270 | ~$8 |
| 20% validation subset | 108 | ~$3 |
| **Phase 1 subtotal** | | **~$31–46** |

### Phase 2 — Study 2 (270 runs)

| Item | Calls | Est. Cost |
|------|-------|-----------|
| LLM inference | 270 | ~$15–30 |
| Blackbox judging | 270 | ~$5 |
| Glassbox judging | 270 | ~$8 |
| 20% validation subset | 108 | ~$3 |
| **Phase 2 subtotal** | | **~$31–46** |

### Total

| | Runs | Est. Cost |
|-|------|-----------|
| Exploratory (v1) | 420 | Already complete |
| Study 1 | 270 | ~$31–46 |
| Study 2 | 270 | ~$31–46 |
| **Grand total** | **960** | **~$62–92** |

Compare: full 1,620 factorial would cost ~$150–200 total.

---

## Judging Pipeline

Same pipeline for both studies:

| Prong | Primary Judge | Validation Judge (20%) |
|-------|--------------|----------------------|
| Blackbox | claude-sonnet-4 (Anthropic Batch) | gpt-4.1-mini (OpenAI) |
| Glassbox | gpt-4.1 (OpenAI) | claude-sonnet-4 (Anthropic Batch) |

- All primary judging via batch API (50% cost reduction)
- 20% stratified validation subset for inter-rater reliability
- Acceptance threshold: Cohen's Kappa > 0.6 (substantial agreement)

---

## Target Venues

| Venue | Type | Deadline (typical) | Fit |
|-------|------|-------------------|-----|
| **AIES** (AAAI/ACM) | Conference | ~Feb | Strong — deception + oversight is core scope |
| **FAccT** | Conference | ~Jan | Good — accountability/oversight framing |
| **SaTML** (IEEE S&P) | Conference | ~Oct | Good — security angle on deception |
| **AAAI SafeAI Workshop** | Workshop | ~Nov | Lower bar, good visibility |
| **arxiv preprint** | Preprint | Anytime | Immediate visibility, citeable |

**Recommended strategy:** arxiv preprint first (immediate visibility), then submit to AIES or FAccT.

---

## Open Decisions

### Decision 1: Which scenario for Studies 1 & 2?

| Option | Pros | Cons |
|--------|------|------|
| **corporate_sabotage_v2** | Continuity with v1 data; established infrastructure | Lower baseline deception (50% in v1) — harder to detect oversight effects |
| **child_protection** | Higher baseline deception (87% in v1) — more room to observe effects | v1 rate was confounded, so the "87%" may not replicate under bare framing |
| **pharma_trial** | Fresh scenario, no v1 baggage | No prior data to calibrate expectations |

**Leaning toward:** corporate_sabotage_v2 (continuity and direct comparability with v1).

### Decision 2: Which oversight level to fix in Study 2?

Depends on Study 1 results:

| Strategy | When to use |
|----------|-------------|
| **Fix at high oversight** | If Study 1 shows high oversight suppresses deception — tests whether moral framing can overcome even strong oversight (strongest claim) |
| **Fix at mid oversight** | If Study 1 shows most variance at mid — maximises statistical sensitivity |
| **Run all three levels** | If budget allows — becomes 810 runs for Study 2 (3 models × 3 goal_types × 3 oversight × n=30) but gives the full interaction |

**Recommendation:** Decide after Study 1 analysis. Fix at whichever level showed moderate deception (~40–60%) for maximum variance.

### Decision 3: n=20 or n=30 per cell?

| n | Total runs (per study) | Power |
|---|----------------------|-------|
| 20 | 180 | ~80% for medium effects (d=0.5) |
| 30 | 270 | ~90% for medium effects, ~80% for small-medium |

**Recommendation:** n=30 if budget allows. The marginal cost (~$10-15 extra per study) is small relative to the power gain.

---

## Execution Timeline

| Step | Description | Status |
|------|-------------|--------|
| 1 | Finalise judge pipeline (single judge per prong, validation protocol) | In progress |
| 2 | Run judge validation pilot (existing dry-run logs + v1 subset) | Pending |
| 3 | Confirm Cohen's Kappa > 0.6 for judge pairs | Pending |
| 4 | **Run Study 1** (270 runs, Phase 1) | Not started |
| 5 | Analyse Study 1 results | Not started |
| 6 | Decide Study 2 oversight level based on Study 1 | Not started |
| 7 | **Run Study 2** (270 runs, Phase 2) | Not started |
| 8 | Analyse Study 2 results | Not started |
| 9 | Write paper (exploratory + Study 1 + Study 2) | Not started |
| 10 | Submit to arxiv | Not started |
| 11 | Submit to AIES/FAccT | Not started |
