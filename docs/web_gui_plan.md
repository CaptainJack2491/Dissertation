# Web GUI Implementation Plan

## Overview

A lightweight, decoupled web interface for the AI Agent Reasoning Experiment Framework. The goal is to allow non-technical users (e.g., supervisors, dissertation examiners) to understand and interact with the project without using the CLI.

**Core Principle**: Keep it fast, reactive, and modular. No bloat. The GUI is a separate layer that wraps the existing core project without modifying it.

---

## Architecture

### Decoupled Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Web GUI (Frontend)                      │
│                 Vanilla JS + HTML + CSS                     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (API)                     │
│              api/server.py (new, separate)                  │
│  - Wraps core functions (ConfigLoader, run_from_config)     │
│  - Exposes endpoints for scenarios, models, runs, logs     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                   Core Project (Unchanged)                  │
│  - src/main.py, src/judge_runner.py                         │
│  - config.yaml, scenarios/, logs/                           │
└─────────────────────────────────────────────────────────────┘
```

### Why This Approach?

1. **Zero Changes to Core**: The dissertation code remains untouched and pure.
2. **Modular**: Adding new scenarios automatically updates the GUI.
3. **No Bloat**: FastAPI + Vanilla JS. Fast, reactive, minimal dependencies.
4. **Showcase-Ready**: Clean dashboard for non-technical users.

---

## File Structure

```
dissertation/
├── api/                      # New API layer
│   ├── __init__.py
│   ├── server.py             # FastAPI application
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── config.py         # Config read/write endpoints
│   │   ├── scenarios.py      # Scenario discovery endpoints
│   │   ├── runs.py            # Experiment run triggers
│   │   └── results.py         # Results/logs fetching
│   └── static/               # Frontend (served by FastAPI)
│       ├── index.html
│       ├── app.js
│       ├── style.css
│       └── assets/
│
├── src/                      # Core project (UNCHANGED)
│   ├── main.py
│   ├── runner.py
│   ├── config_loader.py
│   └── ...
│
├── docs/
│   └── web_gui_plan.md       # This file
│
└── config.yaml
```

---

## API Endpoints

### 1. Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Read current `config.yaml` |
| PUT | `/api/config` | Update/save `config.yaml` |
| GET | `/api/logging` | Get current logging configuration (file path, level) |

### 2. Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List all available scenarios from `scenarios/` |
| GET | `/api/scenarios/{name}` | Get details (oversight levels, files) for a scenario |
| GET | `/api/models` | List models from config |
| GET | `/api/providers` | List providers from config |

### 3. Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/run` | Start an experiment run (non-blocking) |
| GET | `/api/run/status` | Get current run status (idle/running/complete) |
| DELETE | `/api/run` | Cancel current run |
| GET | `/api/logs/stream` | Server-Sent Events (SSE) for live log streaming |

### 4. Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/results` | Get experiment results (CSV data as JSON) |
| GET | `/api/results/images` | List generated visualization images |
| GET | `/api/results/images/{name}` | Serve a specific image |
| GET | `/api/judge/results` | Get judge results if available |

---

## Implementation Steps

### Phase 1: Backend (FastAPI)

1. **Setup**: Add `fastapi`, `uvicorn` to dependencies (via `uv add`)
2. **Server**: Create `api/server.py` with basic FastAPI app
3. **Config Endpoint**: Wrap `ConfigLoader` to expose config read/write
4. **Scenario Discovery**: Auto-scan `scenarios/` directory
5. **Run Trigger**: Execute `uv run src/main.py` as subprocess
6. **Log Streaming**: Implement SSE endpoint to tail log file
7. **Results Endpoint**: Read CSV files and serve as JSON

### Phase 2: Frontend (Vanilla JS)

1. **Static Files**: Create `api/static/` directory
2. **index.html**: Main dashboard layout
3. **style.css**: Clean, minimal styling
4. **app.js**: 
   - Fetch scenarios/models and populate dropdowns
   - Handle "Run" button click → POST to `/api/run`
   - Connect to `/api/logs/stream` for live output
   - Display results in tables
   - Render images from `/api/results/images`

### Phase 3: Integration & Polish

1. **Auto-discovery**: Ensure new scenarios appear automatically
2. **Error Handling**: Graceful errors for missing API keys, etc.
3. **Run Status**: Visual indicator (spinner/green check) during runs

---

## Key Implementation Details

### Log File Location

The log file path is **not hardcoded**. It is read dynamically from `config.yaml` at runtime:

```python
# From config_loader.py
logging_config = config.logging_config
log_file = logging_config.get('file')  # e.g., 'logs/gpt/experiment.log'
```

The API uses this to tail the correct file during live streaming.

### Non-Blocking Runs

Experiment runs can take a long time. The API uses `asyncio` or `subprocess.Popen` to start the run in the background, returning a `run_id` or status immediately. The frontend can poll for status or stream logs in real-time.

### Server-Sent Events (SSE) for Log Streaming

Instead of WebSockets (which add bloat), we use SSE:

```python
@app.get("/api/logs/stream")
async def log_stream():
    async def event_generator():
        # Tail log file line by line
        yield {"event": "log", "data": line}
    return EventSourceResponse(event_generator())
```

---

## Dependencies

New dependencies to add via `uv add`:

```toml
[dependencies]
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.32.0"}
sse-starlette = ">=2.0.0"
```

Frontend uses **zero** external dependencies (pure Vanilla JS).

---

## Running the GUI

```bash
# Start the API server
uv run api/server.py

# Open in browser
# http://localhost:8000
```

---

## Future Considerations (Out of Scope for Initial Version)

- [ ] Authentication (not needed for local dissertation showcase)
- [ ] Multi-user support
- [ ] Judge runner integration via GUI
- [ ] Dark mode
- [ ] Mobile responsiveness

---

## Author

Created: March 2026

Purpose: Dissertation showcase for AI Agent Reasoning Experiment Framework
