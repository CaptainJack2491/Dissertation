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
│        Modular ES6 Vanilla JS + HTML + Chart.js             │
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
2. **Modular Frontend**: Splitting JS and CSS into logical components prevents a monolithic file structure, making future expansions (like new charts) effortless. 
3. **No Build Step**: Native ES6 modules mean no Webpack or React overhead.
4. **Showcase-Ready**: Clean, dark-themed "Control Room" dashboard for non-technical users.

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
│       ├── index.html        # Main DOM
│       ├── css/              # Modular CSS (base, layout, components, etc.)
│       └── js/               # ES6 Modules
│           ├── main.js       # Entry point
│           ├── api.js        # API wrapper
│           ├── ui.js         # Global DOM utilities
│           └── components/   # Specific feature logic (results, config, terminal)
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

### 4. Results & Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/results/files`| List all CSV files in the logs directory |
| GET | `/api/results` | Get experiment results (CSV data as JSON), accepts `?file=` |
| GET | `/api/results/images` | List generated visualization images |
| GET | `/api/results/images/{name}` | Serve a specific image |
| GET | `/api/judge/files`| List all judge reports in the configured log directory |
| GET | `/api/judge/results` | Get judge results as JSON, accepts `?file=` |

---

## Implementation Steps

### Phase 1: Backend (FastAPI)

1. **Setup**: Add `fastapi`, `uvicorn` to dependencies (via `uv add`)
2. **Server**: Create `api/server.py` with basic FastAPI app
3. **Config Endpoint**: Wrap `ConfigLoader` to expose config read/write
4. **Scenario Discovery**: Auto-scan `scenarios/` directory
5. **Run Trigger**: Execute `uv run src/main.py` as subprocess
6. **Log Streaming**: Implement SSE endpoint to tail log file
7. **Results Endpoint**: Read CSV/JSON files dynamically based on URL queries.

### Phase 2: Frontend (Vanilla ES6)

1. **Static Architecture**: Implement a modular JS structure (`js/components/`).
2. **Dashboard Layout**: Fixed left sidebar for configuration, main viewport for data analysis, and a docked live terminal.
3. **Aesthetics**: "Industrial Control Room" dark theme (high contrast, sans-serif UI, monospace terminal).
4. **Live Data**: Connect `EventSource` to SSE endpoint for a real-time log feed.
5. **Interactive Visualizations**: Integrate `Chart.js` to dynamically generate pie and bar charts from CSV data endpoints.

### Phase 3: Integration & Polish

1. **Auto-discovery**: Ensure new scenarios and result files populate dropdowns automatically.
2. **Data Parsing**: Ensure long text fields (like judge justifications) wrap nicely in tables.
3. **Chart Cleanup**: Ensure the Chart.js instances are destroyed and re-created cleanly when switching data sources.

---

## Dependencies

Backend dependencies added via `uv`:

```toml
[dependencies]
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.32.0"}
sse-starlette = ">=2.0.0"
```

Frontend uses `Chart.js` via CDN. No other external dependencies are required.

---

## Running the GUI

```bash
# Start the API server
uv run api/server.py

# Open in browser
# http://localhost:8000
```

---

## Features Implemented

- [x] Run Trigger and Cancellation
- [x] Live log tailing via SSE
- [x] High-contrast Dark Mode ("Control Room" aesthetic)
- [x] Dynamic File Selection for CSV/Judge Reports
- [x] Interactive Chart.js Visualizations (Pie & Bar charts based on columns)
- [x] Responsive data tables with word-wrapping
- [x] Modular ES6 Javascript (No build step)

---

## Author

Created: March 2026

Purpose: Dissertation showcase for AI Agent Reasoning Experiment Framework
