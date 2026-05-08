# Study 1 Data Cleaning & Error Handling

**Date:** 2026-04-15

## Issue

During the full execution of Study 1 (270 runs), we discovered that exactly 8 out of 90 runs for `google/gemini-3.1-pro-preview` were corrupted. These runs terminated prematurely, meaning the agent failed to execute the target action or write the final output file, leading to them failing the regex check and dropping out of meaningful blackbox judgement.

## Root Cause Analysis

Investigation revealed two primary culprits:

1. **Client-Side Parser Bug:** Gemini occasionally returns a `finish_reason` of `"stop"` even when it successfully populates `tool_calls`. The agent loop in `src/agent.py` was evaluating `finish_reason == "stop"` first, which caused the agent loop to immediately exit and return the raw text rather than executing the requested tools.
2. **Upstream API Inference Error:** OpenRouter/Google API intermittently returned an HTTP 400 error: `Unable to submit request because Thought signature is not valid.` This is a known infrastructure issue when Gemini's internal reasoning tokens fail upstream validation, causing the API call to crash.

## Mitigation & Cleaning Protocol

In computational experiments, it is standard academic practice to discard technically corrupted trials caused by infrastructure failures and safely regenerate them to hit the intended sample size (`n=30`), provided the failure is not behavioural (e.g., the model didn't refuse the prompt; the API literally crashed).

We executed the following pipeline to secure a clean 270/270 dataset:

1. **Patched the Agent Loop:** Modified `src/agent.py` to prioritize `if response_message.tool_calls` over `finish_reason`, effectively bypassing Gemini's buggy finish reason.
2. **Isolated & Removed Corrupted Runs:** Traced the generated JSON timestamps of the 8 faulty runs and safely deleted them from `logs/v2_study1/`.
3. **Targeted Regeneration:** Re-ran `config_study1.yaml`. Because the experiment runner framework is idempotent, it skipped the 262 existing, valid runs and successfully generated the 8 missing runs under the exact same experimental condition.
4. **Targeted Judging:** Dropped the 8 corrupted rows from `output/study1_results.csv` and executed the validated judging pipeline (Grok 4.1 Fast + GPT-4.1) strictly on the 8 new JSON logs via a standalone batch script (`scripts/judge_missing.py`).
5. **Re-aggregation:** Manually appended the 8 new verdicts into the CSV.

## Final Result

The `study1_results.csv` now reflects a perfectly balanced, 270-run validated dataset. This data cleaning step must be briefly mentioned in the dissertation's Methodology Limitations section to maintain full experimental transparency.

Note: if someone wants to see the deleted logs, they are still preserved in the git history.
