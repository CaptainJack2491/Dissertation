# Cleanup and Repository Reorganisation

**Date:** 2026-04-13
**Purpose:** Document repository cleanup actions taken before dissertation submission

---

## Deleted Files (Garbage Removed)

| File | Reason |
|------|--------|
| AGENT.md | Stale agent configuration |
| PLAN_judge_dashboard.md | Ad-hoc planning doc |
| PLAN_judge_multi_model.md | Ad-hoc planning doc |
| analyze.py | Debug script |
| analyze_gpt.py | Debug script |
| bruh.csv | Debug artifact |
| config_test_eval.yaml | Redundant config |
| grok_batchapi.md | Stray note |
| oversight_competence_filter.md | Stray note |
| pharma_trial_scenario_spec.md | Stray spec |
| pilot_judge.py | Debug script |
| results_plan.md | Stray planning doc |
| src/quick_judge.py | Debug script |
| task.md | Stray task doc |
| test.config.yaml | Debug config |
| test.csv | Debug artifact |

## Updated Files

### .gitignore
- Added `videos/` to gitignore (656MB recordings, already gitignored locally)

## Commits Made (11 Total)

### Commit 1: ignore
```
ignore: add videos/ to gitignore
```
- Updated `.gitignore` to exclude `videos/`

### Commit 2: docs
```
docs: update dissertation intro, lit review, and methodology chapters
```
- `docs/final/intro.typ`
- `docs/final/lit.typ`
- `docs/final/methodology.typ`
- `docs/final/methodology_1.typ`

### Commit 3: viz
```
viz: add architecture diagrams for thesis
```
- `viz/ai_evaluation_dashboard.png`
- `viz/ai_evaluation_heatmaps.png`
- `viz/ai_evaluation_oversight_analysis.png`
- `viz/ai_evaluation_radar.png`
- `viz/architecture.mmd`
- `viz/architecture.pdf`
- `viz/architecture.svg`
- `viz/gem.png`
- `viz/model_evaluation_summary.csv`

### Commit 4: papers
```
papers: add 2512.16041v1 deception alignment paper
```
- `papers/2512.16041v1.pdf`

### Commit 5: docs/paper
```
docs: add paper draft with alternative structure for publication
```
- `docs/paper/TODO.md`
- `docs/paper/abstract.typ`
- `docs/paper/conclusion.typ`
- `docs/paper/introduction.typ`
- `docs/paper/main.pdf`
- `docs/paper/main.typ`
- `docs/paper/methodology.typ`
- `docs/paper/plan.md`
- `docs/paper/questions.md`
- `docs/paper/references.bib`
- `docs/paper/results.md`
- `docs/paper/results.typ`
- `docs/paper/uel.svg`

### Commit 6: judge_validation
```
judge_validation: add v2 judge comparison results
```
- `judge_validation/comparison_results.csv`
- `judge_validation/results_claude_haiku_4_5_20251001.csv`
- `judge_validation/results_claude_sonnet_4_6.csv`
- `judge_validation/results_gpt_4_1_mini.csv`
- `judge_validation/results_gpt_5_mini_2025_08_07.csv`
- `judge_validation/results_grok_4_1_fast_non_reasoning.csv`
- `judge_validation/results_grok_4_1_fast_reasoning.csv`

### Commit 7: docs
```
docs: add judging specification and config template
```
- `judging_spec.md` (kept for documentation value)
- `example.config.yaml` (template for other users, main config.yaml is gitignored)

### Commit 8: notes
```
notes: add dissertation pivot plan and additional research notes
```
- `notes/concerns.md`
- `notes/safe_goal_experiments.md`
- `notes/v2_redesign/05_dissertation_pivot.md`

### Commit 9: docs
```
docs: add progress presentation from start of Term 2 (Jan 2026)
```
- `docs/04_ppt/Presentation Template.pdf`
- `docs/04_ppt/harward.csl`
- `docs/04_ppt/main.html`
- `docs/04_ppt/main.qmd`
- `docs/04_ppt/plan.md`
- `docs/04_ppt/progress_presentation.html`

### Commit 10: api
```
api: add chat interface styles to results dashboard
```
- `api/static/css/results.css` (152 insertions)
- `api/static/js/ui.js` (1 insertion, 1 deletion)

### Commit 11: deps
```
deps: add scikit-learn for statistical analysis
```
- `pyproject.toml` (added scikit-learn>=1.8.0)
- `uv.lock`

## Retained (Not Committed)

### Untracked - Keep as-is
- `save.csv`, `save_if.csv` — debug artifacts, keep untracked
- `docs/final/claude_mathodology.md` — older draft methodology
- `docs/final/main1.pdf/typ` — older draft version
- `docs/final/methodology_1.pdf` — alternate methodology draft
- `docs/final/template.typ`, `harward.csl`, `uel.svg` — reference files

### Modified - Active Work (Left Uncommitted)
- `src/judge/batch_providers.py` — v2 judge implementation
- `src/judge/judge.py` — v2 judge system
- `src/judge/prompts.py` — v2 judge prompts
- `scripts/judge_comparison.py` — judge utility
- `scripts/test_dashboard_ui.py` — dashboard utility
- `config_dryrun.yaml` — dry run config (intentionally uncommitted)
- `logs/` — separate worktree on different branch

## Final Status

- Branch: `main`, 24 commits ahead of `origin/main`
- Clean state for dissertation work
- v2 judge system and experiment code left in working state for post-dissertation completion
