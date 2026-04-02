# Research Plan: Oversight Intensity and Model Behaviour

**Core Research Question:** How does perceived oversight intensity affect the frequency and sophistication of deceptive behaviour in AI agents?

> **DECISION (2026-04-02):** Option B (Two-Phase) was selected. See `04_publication_plan.md` for the full plan including paper structure, budget, and analysis strategy.

---

## The Problem with the Current v2 Design

The proposed 3×3×3×3 factorial design (models × scenarios × goal_type × oversight) tests TWO primary questions simultaneously:

1. **Oversight effect** — does oversight intensity change deception frequency/sophistication?
2. **Framing effect** — does rationalization framing (bare/self_serving/moral) make models more susceptible to deception?

This creates a 3-way interaction (oversight × scenario × goal_type) that is difficult to parse with n=20 per cell. With 81 unique combinations, you're diffuse across too many conditions to make definitive claims about any single variable.

**Key risk:** You find an oversight effect but cannot determine if it's real, or if it's being modulated by goal_type interactions. The data might show "oversight works under bare framing but not under moral framing" — which is interesting but doesn't cleanly answer the core question.

---

## Alternative Approaches

### Option A: Focused Core Experiment (Recommended)

**3 models × 3 oversight levels × n=20 = 270 runs**

| Factor | Levels |
|--------|--------|
| Models | Gemini 3.1 Pro, GLM-5, DeepSeek V3.2 |
| Oversight | low, mid, high |
| Scenario | corporate_sabotage_v2 (one scenario) |
| Goal type | bare (one type) |

**This cleanly answers:** Does oversight intensity affect deception frequency and sophistication?

**Advantages:**
- High statistical power within each oversight level (60 runs per level)
- No confounding from framing variables
- Clean main effect of oversight is interpretable
- Enough data to run per-model analysis

**Limitations:**
- Only one scenario — external validity is limited
- Only one goal_type — doesn't explore the rationalization hypothesis

---

### Option B: Two-Phase Approach

**Phase 1 — Core Oversight Experiment (270 runs)**
Same as Option A. Get the clean answer.

**Phase 2 — Framing Extension (pilot, 270 runs)**
If Phase 1 shows an oversight effect, extend to explore the framing question:
- Same 3 models × 3 oversight × n=10
- Same scenario but with goal_type variations (bare/self_serving/moral)
- This gives you initial data on framing without contaminating the core experiment

**Advantages:**
- Phase 1 gives a clean, standalone result
- Phase 2 builds on confirmed findings
- Two publishable pieces instead of one messy one

---

### Option C: Planned Contrasts Design

Instead of full factorial, specifically test hypotheses:

**Hypothesis 1:** High oversight reduces deception vs low oversight
- Run: low vs high oversight, n=30 per level
- Statistical test: chi-squared or Fisher's exact on deception rate

**Hypothesis 2:** Moral framing increases deception vs bare framing
- Run subset: moral vs bare, n=30 per level
- Only run if H1 is confirmed

**Total: 180 runs** (focused on the contrasts that matter)

**Advantages:**
- Maximum power for the specific questions
- Statistically clean

**Limitations:**
- Doesn't explore interactions
- Less comprehensive

---

## What Would Definitively Prove the Oversight Effect?

For a conclusive result, you need:

1. **Significant main effect of oversight** on deception rate
   - e.g., low: 70%, mid: 60%, high: 50%
   - Cochran-Armitage trend test for oversight as ordinal

2. **Consistency across models**
   - Each model individually should show reduced deception under high oversight
   - Or at minimum, the majority of models

3. **No interaction with other variables** (or a well-characterized interaction)
   - If framing only works under high oversight, that's still publishable — but you need to design for it

4. **Sufficient n**
   - n=20 per cell gives ~80% power for medium effects (d=0.5)
   - n=30 per level gives better power for detecting smaller effects

---

## Recommendation

**Run Option A first.** Get the clean result. Then decide if the framing question is worth pursuing as a separate experiment.

If you run Option A and find:
- **Oversight effect exists:** Run Phase 2 framing pilot
- **No oversight effect:** The framing question becomes the primary — redesign around that
- **Mixed results:** You've learned something important about which models respond to oversight

This gives you flexibility without betting everything on a single 1,620-run experiment that might not give you a clean answer to either question.

---

## Comparison Table

| Approach | Runs | Clean Answer to Oversight? | Explores Framing? | Risk |
|----------|------|---------------------------|-------------------|------|
| Current v2 (3×3×3×3) | 1,620 | Confounded | Yes | High — both questions diluted |
| Option A (core only) | 270 | Yes | No | Low — focused result |
| Option B (two-phase) | 540 | Yes (phase 1) | Yes (phase 2) | Medium — requires Phase 1 success |
| Option C (contrasts) | 180 | Yes | Limited | Low — max power, narrow scope |

---

## Open Question

Should the scenario (corporate_sabotage_v2) be the single scenario for Option A, or do you want to use a different one? The current corporate_sabotage_v2 has established infrastructure and known deception rates from v1.
