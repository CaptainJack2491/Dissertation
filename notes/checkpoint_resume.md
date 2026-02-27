# Checkpoint & Resume for Experiment Runs

**Date:** 2026-02-26  
**Branch:** `feat/checkpoint-resume`  
**Files changed:** `src/runner.py`, `src/agent.py`

## Context

The full experimental matrix consists of 5 models × 2 scenarios × 3 oversight levels × 10 runs = **300 individual runs**. Each run involves an API call to an LLM, making the full pipeline both time-consuming and non-trivially expensive. There is a realistic chance of failure mid-run (API rate limits, network errors, OOM, process killed, etc.), and re-running all 300 experiments from scratch would be wasteful.

## What We Did

### 1. Resume Logic (`runner.py`)

Before starting each model/scenario/oversight combination, the runner now counts the number of existing `.json` log files in the corresponding output directory (e.g. `logs/{model}/{scenario}/{oversight}/`). If that count meets or exceeds the configured number of runs, the combination is skipped entirely. Otherwise, the runner resumes from run N+1, where N is the number of existing logs.

This works because each successfully completed run produces exactly one `.json` log file. The log files themselves act as implicit checkpoints — no separate state file or database is needed.

A `--no-resume` CLI flag is available to override this behaviour and force a clean start.

### 2. Atomic Log Writes (`agent.py`)

To prevent a corrupted log file from being falsely counted as a completed run, the `save_logs` method now writes to a temporary file (`.json.tmp` suffix) first, then atomically renames it to the final `.json` path using `os.rename()`. On Linux, `os.rename()` is an atomic filesystem operation, meaning the `.json` file either exists in its entirety or not at all. If the process crashes mid-write, only a `.json.tmp` file is left behind, which the resume logic ignores (it only counts `*.json`).

## Rationale (for methodology)

- **Reproducibility:** Resume support does not alter the experimental procedure. Each run is independent — resuming from run 6 produces the same result as if runs 1–10 were executed sequentially without interruption, since there is no shared state between runs.
- **Data integrity:** Atomic writes guarantee that only fully completed runs are counted, eliminating the risk of analysing partial or corrupted data.
- **Pragmatic necessity:** With 300 runs over multiple LLM providers, intermittent failures are expected. Without resume support, any failure would require restarting the entire matrix, wasting both API credits and time.
