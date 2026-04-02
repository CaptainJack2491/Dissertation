# v2 Redesign Notes

Documentation of the experiment evolution from v1 (420 runs) through to the final v2 two-phase design (540 runs).

## Files

| File | Description |
|------|-------------|
| `01_v1_to_v2_evolution.md` | Full history: v1 design/results, limitations, v2 redesign motivation, experimental design, judge design |
| `02_judge_system.md` | Current judge implementation state, planned changes, cost analysis |
| `03_research_plan.md` | Analysis of experimental design options — Option B (two-phase) was selected |
| `04_publication_plan.md` | **Final plan:** paper structure, budget, venues, analysis strategy, timeline |

## Quick Summary

### v1 — Exploratory Study (420 runs, complete)
- 7 models × 2 scenarios × 3 oversight levels × 10 runs
- Key finding: Child protection (87%) vs Corporate sabotage (50%) deception — but confounded
- Oversight reduces frequency but NOT sophistication (69.3% STRATEGIC across all levels)
- Single judge: Claude Sonnet 4

### v2 — Confirmatory Studies (540 runs, planned)

**Study 1 — Oversight Effect (270 runs):**
- 3 models × 3 oversight levels × 1 scenario × 1 goal_type (bare) × n=30
- Cleanly isolates the oversight variable

**Study 2 — Framing Effect (270 runs):**
- 3 models × 3 goal_types × 1 oversight level × 1 scenario × n=30
- Tests the rationalization hypothesis from v1

### Decisions Made
- **Approach:** Option B (two-phase) — clean answer to each question separately
- **Publication:** Single paper with v1 as exploratory pilot, v2 as two confirmatory studies
- **Models:** Gemini 3.1 Pro, GLM-5, DeepSeek V3.2 (all kept; Gemini ceiling effect treated as a finding)
- **Analysis:** Three-layer strategy — pooled, per-model, sensitivity analysis excluding ceiling models
- **Judge:** Single judge per prong + 20% cross-family validation subset

### Current Status
- Framework implemented and committed
- Judge system being refined (single judge per prong)
- v2 experiment NOT yet run
- Judge validation pilot pending

## Key Insight from v1

Models show higher deception rates when hidden goals include rationalizations they agree with (moral framing) vs bare instructions. v2 Study 2 isolates this variable.
