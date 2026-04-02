"""
FastAPI server for the AI Evaluation Visualization Dashboard.
Serves read-only results, JSON logs, and static visuals.

Discovers data from multiple directories:
- CSV results: logs/full_experiment/, output/, and config.output_dir
- Viz images: viz/ (project root) and output_dir/viz
- Judge logs: judge_logs/ and logs/judge_full_experiment/
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import json
import math

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path to import core modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from src.config_loader import ConfigLoader
from src.agent import Agent
from src.interrogate import get_provider_from_log, sanitize_for_api
from src.vfs import VFS
from pydantic import BaseModel
import uuid

app = FastAPI(
    title="AI Agent Evaluation Dashboard",
    description="Web GUI for analyzing experiment results",
    version="0.3.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Interrogation Session Cache
# In a production app, use Redis. For local dashboard, dict is fine.
ACTIVE_SESSIONS: Dict[str, Agent] = {}

class InterrogateStartRequest(BaseModel):
    log_path: str

class InterrogateChatRequest(BaseModel):
    session_id: str
    message: str


def get_config():
    """Helper to load config safely."""
    try:
        config = ConfigLoader(str(PROJECT_ROOT / "config.yaml"))
        config.load()
        return config
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        return None


def _discover_csv_dirs() -> List[Path]:
    """Discover all directories containing CSV result files."""
    candidates = [
        PROJECT_ROOT / "logs" / "full_experiment",
        PROJECT_ROOT / "logs" / "v2_experiment",
        PROJECT_ROOT / "output",
    ]
    # Also add whatever the config says
    config = get_config()
    if config:
        candidates.append(PROJECT_ROOT / config.output_dir)

    return [d for d in candidates if d.exists()]


def _discover_viz_dirs() -> List[Path]:
    """Discover all directories containing visualization images."""
    candidates = [
        PROJECT_ROOT / "viz",
        PROJECT_ROOT / "output" / "charts",
    ]
    config = get_config()
    if config:
        candidates.append(PROJECT_ROOT / config.output_dir / "viz")

    return [d for d in candidates if d.exists()]


def _discover_judge_dirs() -> List[Path]:
    """Discover all directories containing judge logs."""
    candidates = [
        PROJECT_ROOT / "judge_logs",
        PROJECT_ROOT / "logs" / "judge_full_experiment",
    ]
    config = get_config()
    if config:
        judge_log_dir = config._config.get('judge', {}).get('log_dir', 'judge_logs')
        candidates.append(PROJECT_ROOT / judge_log_dir)

    return [d for d in candidates if d.exists()]


def _clean_value(val):
    """Convert NaN/Inf to None for JSON serialization."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


# ============================================================================
# Root Endpoint - Serve HTML
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)


# ============================================================================
# Results Endpoints
# ============================================================================

@app.get("/api/results/files")
async def get_results_files():
    """List all CSV files across all discovered result directories."""
    all_files = {}
    for csv_dir in _discover_csv_dirs():
        dir_label = str(csv_dir.relative_to(PROJECT_ROOT))
        for p in sorted(csv_dir.rglob("*.csv")):
            rel = str(p.relative_to(csv_dir))
            # Prefix with directory label to distinguish sources
            key = f"{dir_label}/{rel}"
            all_files[key] = str(p)

    return sorted(all_files.keys())


@app.get("/api/results")
async def get_results(file: str = None):
    """Get experiment results as JSON, optionally for a specific file."""
    if file:
        # Resolve back to absolute path from the prefixed key
        file_path = PROJECT_ROOT / file
        if not file_path.exists() or ".." in file:
            raise HTTPException(status_code=404, detail=f"File not found: {file}")
        csv_files = [file_path]
    else:
        # Load everything from first discovered dir
        csv_files = []
        for csv_dir in _discover_csv_dirs():
            csv_files.extend(csv_dir.glob("*.csv"))

    results = {}
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)

            cleaned_data = []
            for record in df.to_dict(orient="records"):
                cleaned_record = {k: _clean_value(v) for k, v in record.items()}
                cleaned_data.append(cleaned_record)

            results[csv_file.stem] = {
                "columns": df.columns.tolist(),
                "data": cleaned_data
            }
        except Exception as e:
            results[csv_file.stem] = {"error": str(e)}

    return results


@app.get("/api/results/images")
async def list_result_images():
    """List generated visualization images from all viz directories."""
    images = []
    seen = set()
    for viz_dir in _discover_viz_dirs():
        for img in sorted(viz_dir.glob("*")):
            if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                if img.name not in seen:
                    seen.add(img.name)
                    images.append({
                        "name": img.name,
                        "path": str(img.relative_to(PROJECT_ROOT)),
                        "source": str(viz_dir.relative_to(PROJECT_ROOT))
                    })

    return images


@app.get("/api/results/images/{image_name}")
async def get_result_image(image_name: str):
    """Serve a specific image from any viz directory."""
    if ".." in image_name:
        raise HTTPException(status_code=400, detail="Invalid path")

    for viz_dir in _discover_viz_dirs():
        image_path = viz_dir / image_name
        if image_path.exists():
            return FileResponse(image_path)

    raise HTTPException(status_code=404, detail="Image not found")


# ============================================================================
# Judge Results Endpoints
# ============================================================================

@app.get("/api/judge/files")
async def get_judge_files():
    """Get list of judge result files from all judge directories."""
    all_files = {}
    for judge_dir in _discover_judge_dirs():
        dir_label = str(judge_dir.relative_to(PROJECT_ROOT))
        for p in sorted(judge_dir.rglob("*")):
            if p.suffix in ['.csv', '.json'] and p.is_file():
                key = f"{dir_label}/{p.relative_to(judge_dir)}"
                all_files[key] = str(p)

    return sorted(all_files.keys())


@app.get("/api/judge/results")
async def get_judge_results(file: str = None):
    """Get judge results if available."""
    if file:
        file_path = PROJECT_ROOT / file
        if not file_path.exists() or ".." in file:
            raise HTTPException(status_code=404, detail="File not found")
        result_files = [file_path]
    else:
        result_files = []
        for judge_dir in _discover_judge_dirs():
            result_files.extend(judge_dir.glob("*.csv"))
            result_files.extend(judge_dir.glob("*.json"))

    results = {}
    for rf in result_files:
        if rf.suffix == '.csv':
            try:
                df = pd.read_csv(rf)
                cleaned_data = []
                for record in df.to_dict(orient="records"):
                    cleaned_record = {k: _clean_value(v) for k, v in record.items()}
                    cleaned_data.append(cleaned_record)
                results[rf.stem] = {
                    "type": "csv",
                    "columns": df.columns.tolist(),
                    "data": cleaned_data
                }
            except Exception as e:
                results[rf.stem] = {"error": str(e)}
        elif rf.suffix == '.json':
            try:
                with open(rf) as f:
                    results[rf.stem] = {"type": "json", "data": json.load(f)}
            except Exception as e:
                results[rf.stem] = {"error": str(e)}

    return results


# ============================================================================
# Experiment Logs Endpoints (NEW - browse raw JSON logs)
# ============================================================================

@app.get("/api/logs/dirs")
async def get_log_dirs():
    """List available log directories."""
    logs_root = PROJECT_ROOT / "logs"
    if not logs_root.exists():
        return []

    dirs = []
    for d in sorted(logs_root.iterdir()):
        if d.is_dir() and d.name != ".git":
            json_count = len(list(d.rglob("*.json")))
            if json_count > 0:
                dirs.append({
                    "name": d.name,
                    "path": str(d.relative_to(PROJECT_ROOT)),
                    "files": json_count
                })
    return dirs


@app.get("/api/logs/browse")
async def browse_log(path: str):
    """Browse a specific log JSON file."""
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = PROJECT_ROOT / path
    if not file_path.exists() or file_path.suffix != '.json':
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        with open(file_path) as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Interrogation Endpoints
# ============================================================================

@app.post("/api/interrogate/start")
async def start_interrogation(req: InterrogateStartRequest):
    """Start an interactive session from a log file."""
    if ".." in req.log_path:
        raise HTTPException(status_code=400, detail="Invalid path")
        
    file_path = PROJECT_ROOT / req.log_path
    if not file_path.exists() or file_path.suffix != '.json':
        raise HTTPException(status_code=404, detail="Log file not found")
        
    try:
        with open(file_path) as f:
            log_data = json.load(f)
            
        conversation_history = log_data.get("conversation", [])
        if not conversation_history:
            raise HTTPException(status_code=400, detail="No conversation history in log")
            
        system_prompt = conversation_history[0].get('content', '') if conversation_history else ''
        scenario = log_data.get('scenario', 'interrogation')
        oversight_level = log_data.get('oversight_level', 'N/A')
        
        provider_config, model_config = get_provider_from_log(log_data)
        
        # Load VFS state if present
        final_vfs_state = log_data.get("final_vfs_state")
        
        # Determine goal_type from log or default to standard
        goal_type = log_data.get("goal_type", "")
        
        # VFS is singleton but we pass state nicely
        vfs_instance = VFS.get_instance(fs_data=final_vfs_state) if final_vfs_state else VFS.get_instance()
        
        agent = Agent.from_configs(
            system_prompt=system_prompt,
            provider_config=provider_config,
            model_config=model_config,
            scenario=scenario,
            oversight_level=oversight_level,
            user_prompt_type=log_data.get('user_prompt_type', 'interrogation'),
            goal_type=goal_type,
            save_vfs_state=True if final_vfs_state else False,
            vfs_instance=vfs_instance
        )
        
        clean_history = sanitize_for_api(conversation_history)
        agent.load_conversation(
            conversation_history=clean_history,
            total_tokens=log_data.get('total_tokens', 0),
            prompt_tokens=log_data.get('prompt_tokens', 0),
            completion_tokens=log_data.get('completion_tokens', 0)
        )
        
        session_id = str(uuid.uuid4())
        ACTIVE_SESSIONS[session_id] = agent
        
        return {"session_id": session_id, "status": "active", "model": agent.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interrogate/chat")
async def chat_interrogation(req: InterrogateChatRequest):
    """Send a message to an active interrogation session."""
    if req.session_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=404, detail="Session expired or not found")
        
    agent = ACTIVE_SESSIONS[req.session_id]
    
    try:
        # Blocks until completion
        agent.chat(req.message)
        
        # Save log after every turn
        log_file = agent.save_logs(output_dir="interrogation_logs", scenario=agent.scenario, oversight_level=agent.oversight_level)
        
        # Extract the latest response logic to send back
        response_msg = None
        for msg in reversed(agent.logs):
            if msg.get("role") == "assistant":
                response_msg = msg
                break
                
        if not response_msg:
             raise HTTPException(status_code=500, detail="No assistant response generated")
             
        return {
            "content": response_msg.get("content", ""),
            "reasoning": response_msg.get("reasoning", ""),
            "tool_calls": response_msg.get("tool_calls", []),
            "log_saved_at": log_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="AI Evaluation Dashboard Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
