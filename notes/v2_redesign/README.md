# v2 Redesign Notes

Documentation of the experiment evolution from v1 (420 runs) through to the final v2 two-phase design (540 runs) and subsequent analysis.

## Files

| File | Description |
|------|-------------|
| `01_v1_to_v2_evolution.md` | Full history: v1 design/results, limitations, v2 redesign motivation, experimental design, judge design |
| `02_judge_system.md` | Baseline judge implementation state, planned changes, cost analysis |
| `03_research_plan.md` | Analysis of experimental design options — Option B (two-phase) was selected |
| `04_publication_plan.md` | Paper structure, budget, venues, analysis strategy, timeline |
| `05_dissertation_pivot.md` | Pivot documentation connecting findings to dissertation framework |
| `06_2026-04-13_cleanup_and_reorganisation.md` | Log of framework cleanup steps prior to final execution |
| `07_judge_validation_results.md` | Empirical proof of judge proxy reliability (Grok-Fast & GPT-4.1 vs Claude Sonnet 4.6) |
| `08_2026-04-15_study1_data_cleaning.md` | Methodology note on API fault recovery securing n=270 dataset |
| `09_results.md` | Raw statistical printouts for Study 1 & Study 2 |
| `10_results_analysis.md` | Core analysis highlights: The Stealth Gap, floor/ceiling effects, and null interventions |
| `11_future_work.md` | Identified limits of the current study (soft vs hard framing) and planned extensions for model selection |

## Quick Summary

### v1 — Exploratory Study (420 runs, complete)
- 7 models × 2 scenarios × 3 oversight levels × 10 runs
- Key finding: Child protection (87%) vs Corporate sabotage (50%) deception — but confounded
- Oversight reduces frequency but NOT sophistication (69.3% STRATEGIC across all levels)
- Single judge: Claude Sonnet 4

### v2 — Confirmatory Studies (540 runs, complete)

**Study 1 — Oversight Effect (270 runs):**
- 3 models × 3 oversight levels × 1 scenario × 1 goal_type (bare) × n=30
- **Finding:** Oversight fails to reduce deceptive intent but successfully causes models to hide their behavior better (The Oversight Paradox). Only GLM-5.1 showed traditional sensitivity.

**Study 2 — Framing Effect (270 runs):**
- 3 models × 3 goal_types × 1 oversight level × 1 scenario × n=30
- **Finding:** The rationalization hypothesis failed. Deception rates were immune to "moral" or "self-serving" framing because frontier capabilities execute hidden goals regardless.

### Current Status
- **Framework & Judging Pipeline:** Fully implemented and validated.
- **Judge Validation:** Completed. `grok-4.1-fast-reasoning` (Blackbox) and `gpt-4.1` (Glassbox) achieved high reliability against the Gold Standard.
- **v2 Experiments:** Run and cleaned exactly to n=270 per study.
- **Data Analysis:** Completed. Extreme ceiling/floor effects dominated, leading to the identification of the Stealth Gap.
- **Future Work Identified:** Moving from explicit to implicit ("soft") framing, pre-calibrating scenario difficulty, and separating the model set into reasoning-visible vs. blackbox-only subsets for broader replication.

## Key Insights from v2

1. **The Stealth Gap:** Internal intent to deceive (~65%) heavily outpaces the external detection of deception (~40%), proving that frontier models consistently fool strong output evaluators.
2. **The Oversight Paradox:** Increasing oversight does not stop deception; it merely forces the models to become stealthier and successfully lower external detection rates.
3. **Intervention Failure:** Both prompt-based oversight warnings and varying moral covers are completely ineffective constraints against modern frontier capabilities.
