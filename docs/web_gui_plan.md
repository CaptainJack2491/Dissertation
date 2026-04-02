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

### 1. Configuration & Discovery (Removed)

*Note: In v0.2.0, the GUI was pivoted to a pure Data Visualization Dashboard. Execution logic (triggering runs, stopping runs, tailing live logs, and configuration editing) has been removed to keep the interface focused on analysis.*

### 2. Results & Analysis

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
3. **Data Serving**: Read CSV/JSON files dynamically based on URL queries.
4. **Token Usage**: The CSV data includes token metrics that were injected during the run or post-processed.

### Phase 2: Frontend (Vanilla ES6)

1. **Static Architecture**: Implement a modular JS structure (`js/components/`).
2. **Dashboard Layout**: Fixed left sidebar for global filtering, main viewport for data analysis.
3. **Aesthetics**: "Industrial Control Room" dark theme (high contrast, sans-serif UI).
4. **Interactive Visualizations**: Integrate `Chart.js` to dynamically generate pie, bar, and stacked bar charts from CSV data endpoints.
5. **Chart Zooming**: Implement a full-screen modal overlay for examining charts closely.

### Phase 3: Integration & Polish

1. **Auto-discovery**: Ensure new scenarios and result files populate dropdowns automatically.
2. **Data Parsing**: Ensure long text fields (like judge justifications) wrap nicely in tables.
3. **Global Filters**: Add checkbox filtering to slice data by Model, Scenario, and Oversight level dynamically on the frontend.
4. **Chart Cleanup**: Ensure the Chart.js instances are destroyed and re-created cleanly when switching data sources or filters.

---

## Dependencies

Backend dependencies added via `uv`:

```toml
[dependencies]
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.32.0"}
```
*(sse-starlette was removed as live log streaming is no longer required)*

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

- [x] Pure Data Visualization Dashboard
- [x] High-contrast Dark Mode ("Control Room" aesthetic)
- [x] Dynamic File Selection for CSV/Judge Reports
- [x] Multi-select Checkbox Global Filters (Model, Scenario, Oversight)
- [x] Interactive Chart.js Visualizations (Deception Rates, Categories)
- [x] Average & Total Token Usage Visualizations (Prompt vs Completion)
- [x] Click-to-Zoom interactive charts (Modal overlay)
- [x] Responsive data tables with word-wrapping
- [x] Modular ES6 Javascript (No build step)

---

## Author

Created: March 2026

Purpose: Dissertation showcase for AI Agent Reasoning Experiment Framework
