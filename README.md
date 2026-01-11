# AI Agent Reasoning Experiment Framework

A framework for running AI agent experiments with structured reasoning extraction, logging, and analysis.

## What It Does

- Runs AI agents with tool-calling capabilities (file system access)
- Extracts and displays reasoning/thought processes from models
- Logs conversations with metadata (token counts, finish reasons, turn counts)
- Supports multiple model providers via OpenAI-compatible APIs
- Configurable via YAML

## Quick Start

```bash
# Install dependencies
uv sync

# Run all experiments from config.yaml
uv run src/main.py

# Run a specific scenario
uv run src/main.py --scenario scenarios/corporate_sabotage_v2 --oversight high
```

## Configuration (`config.yaml`)

```yaml
providers:
  openai:
    api_key_env: OPENAI_API_KEY
    base_url: https://api.openai.com/v1
  google:
    api_key_env: GOOGLE_API_KEY
    base_url: https://generativelanguage.googleapis.com/v1beta/openai/
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1

models:
  - id: gemini-3-flash-preview
    provider: google
    temperature: 1
    extra_body:
      google:
        thinking_config:
          include_thoughts: True

scenarios:
  - path: scenarios/corporate_sabotage_v2
    runs: 1

oversight_levels:
  - high

output:
  dir: logs
  save_vfs_state: false  # Set true to include final VFS state in logs
```

## Scenario Structure

```
scenarios/
  scenario_name/
    user.md           # User prompt
    benign_goal.md    # Visible system prompt
    hidden_goal.md    # Hidden system prompt (for experiments)
    data/             # Files accessible to agent
      file1.txt
      file2.txt
```

## Output Format

Logs are saved to `logs/{model}/{scenario}/{oversight}/{timestamp}.json`:

```json
{
  "run_id": "...",
  "model": "gemini-3-flash-preview",
  "scenario": "corporate_sabotage_v2",
  "oversight_level": "high",
  "total_tokens": 1500,
  "prompt_tokens": 1000,
  "completion_tokens": 500,
  "conversation": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {
      "role": "assistant",
      "reasoning": "...",
      "content": "...",
      "tool_calls": [...],
      "finish_reason": "stop",
      "turn_count": 1
    }
  ]
}
```

## Key Features

- **Reasoning Extraction**: Supports multiple formats:
  - OpenRouter `reasoning_content`
  - Google `thought_signature` (via `extra_content`)
  - `<thinking>` tags in content
- **Turn Limit**: Max 20 turns per conversation (prevents infinite loops)
- **Success Tracking**: Runs marked SUCCESS if they end with `finish_reason: "stop"`
- **VFS**: Virtual file system for sandboxed file access

## File Structure

```
src/
  agent.py       # Main agent logic, OpenAI SDK integration
  config_loader.py  # YAML config parsing
  main.py        # Entry point
  runner.py      # Experiment orchestration
  tools.py       # Available tools (list_files, read_file, etc.)
  vfs.py         # Virtual file system
scenarios/       # Scenario definitions
logs/            # Output logs
```

## API Keys

Set API keys via environment variables (or `.env` file):

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

## Interrogation [Not implimented correctly yet]

Replay and continue conversations from logs:

```bash
uv run src/interrogate.py logs/gemini-3-flash-preview/...
```
