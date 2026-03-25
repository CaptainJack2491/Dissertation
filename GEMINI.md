# AI Agent Reasoning Experiment Framework (GEMINI.md)

This project is a research framework designed to evaluate AI agent behavior, specifically focusing on the detection of deceptive intent through structured reasoning extraction and automated multi-stage judging.

## Project Overview

- **Purpose:** Dissertation research on AI agent reasoning, safety, and deceptive capabilities.
- **Core Concept:** Running AI agents in sandboxed environments (VFS) with both benign and hidden goals, then analyzing their internal "thought" processes (reasoning traces) and final outputs for signs of deception.
- **Key Technologies:**
  - **Language:** Python (>=3.13)
  - **Dependency Management:** `uv`
  - **UI/Visuals:** `rich` (for real-time dashboard and summary tables)
  - **LLM Integration:** OpenAI SDK (used for various providers like Google, Groq, OpenRouter) and Anthropic SDK (primarily for the judging pipeline).
  - **Evaluation:** Regex-based matching, Blackbox (output vs. baseline), and Glassbox (internal reasoning analysis).

## Architecture & Core Components

- **`src/agent.py`:** Manages LLM interactions, tool calls, and robust reasoning extraction across different model providers (OpenAI, Google, Anthropic, etc.).
- **`src/vfs.py`:** A Virtual File System that provides a sandboxed environment for agents to read/write files without affecting the host system.
- **`src/runner.py`:** Orchestrates experiment runs, including baseline generation and prompt assembly.
- **`src/dashboard.py`:** Handles real-time terminal UI using `rich`, including multi-model progress bars and status summaries.
- **`src/judge.py`:** Implementation of the three-tier judging system:
  - **Regex:** Pattern matching against defined scenario rules.
  - **Blackbox:** LLM-based comparison of model output against a "honest" baseline.
  - **Glassbox:** LLM-based analysis of the agent's reasoning trace to categorize intent and sophistication.
- **`src/judge_runner.py`:** CLI for batch processing experiment logs through the judging pipeline, utilizing the Anthropic Batch API for cost efficiency.

## Key Workflows

### 1. Setup
```bash
# Install dependencies using uv
uv sync

# Set up environment variables (.env)
# Required: OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, etc.
```

### 2. Running Experiments
Experiments are driven by `config.yaml`. The framework provides a real-time dashboard showing progress per model and overall status.
```bash
# Execute all experiments defined in the config
uv run src/main.py

# Optional: Ignore existing logs and restart
uv run src/main.py --no-resume
```

### 3. Judging Results
```bash
# Judge all logs in a directory and output to CSV
uv run python src/judge_runner.py --logs-dir logs/ --output output/results.csv

# Single file judging (synchronous)
uv run python src/judge_runner.py --log-file logs/path/to/log.json --mode single
```

### 4. Interactive Interrogation
Replay a conversation and continue questioning the agent to explore its reasoning.
```bash
uv run src/interrogate.py logs/path/to/log.json
```

## Directory Structure

- `src/`: Core logic and CLI tools.
- `scenarios/`: Definitions for experiment scenarios (prompts, data files, regex rules).
- `logs/`: Raw experiment output JSON files.
- `judge_logs/`: Detailed reasoning/justification from the judge models.
- `tests/`: Comprehensive pytest suite (138+ tests) covering VFS, config, agent, and judge logic.
- `docs/`: Dissertation-related documentation and proposals.

## Development Conventions

- **Logging:** Uses a custom logger (`src/logger.py`) with levels 1-4. Level 4 (DEBUG) is highly verbose. Note: In parallel execution, console logging is restricted to WARNING and above to prevent dashboard corruption.
- **UI:** Prefer `rich` for terminal-based visualizations.
- **Reasoning Extraction:** The framework is designed to handle multiple reasoning formats (thinking tags, `reasoning_content` fields, etc.) and normalize them for analysis.
- **VFS Singleton:** The `VFS` class uses a singleton pattern for consistent state within a single run but supports independent instances for parallel execution.
- **Testing:** Always run `uv run pytest tests/` before committing changes to ensure core logic (especially reasoning extraction and VFS) remains intact.
