"""
FastAPI server for the Web GUI.
Wraps core project functionality without modifying it.
"""
import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import yaml

# Add project root to path to import core modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import ConfigLoader


# Global state for run management
class RunManager:
    """Manages experiment runs."""
    
    def __init__(self):
        self.current_process: Optional[subprocess.Popen] = None
        self.status: str = "idle"  # idle, running, complete, error
        self.start_time: Optional[datetime] = None
        self.log_file_path: Optional[str] = None
        self.config: Optional[ConfigLoader] = None
    
    def load_config(self, config_path: str = "config.yaml"):
        """Load configuration and update log file path."""
        self.config = ConfigLoader(config_path)
        self.config.load()
        self.log_file_path = self.config.logging_config.get('file')
        
        # If relative path, make it absolute from project root
        if self.log_file_path and not os.path.isabs(self.log_file_path):
            self.log_file_path = os.path.join(PROJECT_ROOT, self.log_file_path)
        
        return self.config
    
    async def start_run(self, config_path: str = "config.yaml"):
        """Start an experiment run in background."""
        if self.status == "running":
            raise HTTPException(status_code=409, detail="A run is already in progress")
        
        # Load config to get log file path
        self.load_config(config_path)
        
        self.status = "running"
        self.start_time = datetime.now()
        
        # Start the run in background
        cmd = [sys.executable, "-m", "uv", "run", "src/main.py"]
        self.current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=PROJECT_ROOT
        )
        
        return {"status": "started", "message": "Experiment run started"}
    
    def cancel_run(self):
        """Cancel the current run."""
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
            self.status = "cancelled"
            return {"status": "cancelled"}
        return {"status": "idle", "message": "No run to cancel"}
    
    def get_status(self):
        """Get current run status."""
        if self.current_process and self.current_process.poll() is None:
            self.status = "running"
        elif self.status == "running":
            self.status = "complete"
        
        return {
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
        }


# Global instance
run_manager = RunManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Load config
    try:
        run_manager.load_config()
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
    
    yield
    
    # Shutdown: Cancel any running process
    if run_manager.current_process:
        run_manager.cancel_run()


# Create FastAPI app
app = FastAPI(
    title="AI Agent Reasoning Experiment Framework",
    description="Web GUI for running experiments and viewing results",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


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
# Config Endpoints
# ============================================================================

@app.get("/api/config")
async def get_config():
    """Read current config.yaml."""
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="config.yaml not found")
    
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    
    return config_data


@app.put("/api/config")
async def update_config(config_data: Dict[str, Any]):
    """Update config.yaml."""
    config_path = PROJECT_ROOT / "config.yaml"
    
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    # Reload config in run manager
    run_manager.load_config()
    
    return {"status": "saved", "message": "Configuration updated"}


@app.get("/api/logging")
async def get_logging_config():
    """Get logging configuration including file path."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    return {
        "level": config.logging_config.get('level'),
        "format": config.logging_config.get('format'),
        "output": config.logging_config.get('output'),
        "file": config.logging_config.get('file'),
        "file_absolute": run_manager.log_file_path
    }


# ============================================================================
# Discovery Endpoints
# ============================================================================

@app.get("/api/scenarios")
async def list_scenarios():
    """List all available scenarios from scenarios/ directory."""
    scenarios_dir = PROJECT_ROOT / "scenarios"
    if not scenarios_dir.exists():
        return []
    
    scenarios = []
    for item in scenarios_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check for oversight levels
            oversight_dir = item / "oversight"
            oversight_levels = []
            if oversight_dir.exists():
                oversight_levels = [f.stem for f in oversight_dir.glob("*.md")]
            
            scenarios.append({
                "name": item.name,
                "path": str(item.relative_to(PROJECT_ROOT)),
                "oversight_levels": oversight_levels
            })
    
    return scenarios


@app.get("/api/scenarios/{scenario_name}")
async def get_scenario(scenario_name: str):
    """Get details for a specific scenario."""
    scenario_path = PROJECT_ROOT / "scenarios" / scenario_name
    if not scenario_path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Read scenario files
    files = {}
    for md_file in scenario_path.glob("*.md"):
        if md_file.name != "regex_rules.yaml":
            with open(md_file) as f:
                files[md_file.stem] = f.read()
    
    # Check oversight levels
    oversight_dir = scenario_path / "oversight"
    oversight_levels = {}
    if oversight_dir.exists():
        for md_file in oversight_dir.glob("*.md"):
            with open(md_file) as f:
                oversight_levels[md_file.stem] = f.read()
    
    return {
        "name": scenario_name,
        "files": files,
        "oversight_levels": oversight_levels
    }


@app.get("/api/models")
async def list_models():
    """List models from config."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    return [
        {
            "id": model.id,
            "provider": model.provider,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens
        }
        for model in config.models
    ]


@app.get("/api/providers")
async def list_providers():
    """List providers from config."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    return {
        name: {
            "base_url": provider.base_url,
            "api_key_env": provider.api_key_env
        }
        for name, provider in config.providers.items()
    }


# ============================================================================
# Execution Endpoints
# ============================================================================

@app.post("/api/run")
async def start_run(background_tasks: BackgroundTasks):
    """Start an experiment run."""
    try:
        result = await run_manager.start_run()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/run/status")
async def get_run_status():
    """Get current run status."""
    return run_manager.get_status()


@app.delete("/api/run")
async def cancel_run():
    """Cancel the current run."""
    return run_manager.cancel_run()


@app.get("/api/logs/stream")
async def log_stream():
    """Stream logs in real-time using SSE."""
    async def event_generator():
        log_file = run_manager.log_file_path
        
        if not log_file or not os.path.exists(log_file):
            yield {"event": "error", "data": "Log file not found"}
            return
        
        # Track file position for tailing
        file_pos = 0
        
        while True:
            # Check if process is still running
            status = run_manager.get_status()
            if status["status"] == "idle" and not run_manager.current_process:
                break
            
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        f.seek(file_pos)
                        new_lines = f.readlines()
                        file_pos = f.tell()
                        
                        for line in new_lines:
                            yield {"event": "log", "data": line.rstrip()}
                
                # Check if process ended
                if run_manager.current_process and run_manager.current_process.poll() is not None:
                    # Process finished, yield remaining logs
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            f.seek(file_pos)
                            remaining = f.read()
                            if remaining:
                                yield {"event": "log", "data": remaining}
                    break
                        
            except Exception as e:
                yield {"event": "error", "data": str(e)}
                break
            
            await asyncio.sleep(0.5)
        
        yield {"event": "done", "data": "Run completed"}
    
    return EventSourceResponse(event_generator())


# ============================================================================
# Results Endpoints
# ============================================================================

@app.get("/api/results")
async def get_results():
    """Get experiment results as JSON."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    output_dir = PROJECT_ROOT / config.output_dir
    
    # Look for CSV files
    csv_files = list(output_dir.glob("*.csv")) if output_dir.exists() else []
    
    results = {}
    for csv_file in csv_files:
        import pandas as pd
        import math
        try:
            df = pd.read_csv(csv_file)
            
            # Convert NaN values to None for JSON serialization
            def clean_value(val):
                if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    return None
                return val
            
            # Clean each row
            cleaned_data = []
            for record in df.to_dict(orient="records"):
                cleaned_record = {k: clean_value(v) for k, v in record.items()}
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
    """List generated visualization images."""
    config = run_manager.config
    if not config:
        return []
    
    output_dir = PROJECT_ROOT / config.output_dir
    viz_dir = output_dir / "viz"
    
    if not viz_dir.exists():
        return []
    
    images = []
    for img in viz_dir.glob("*"):
        if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            images.append({
                "name": img.name,
                "path": str(img.relative_to(PROJECT_ROOT))
            })
    
    return images


@app.get("/api/results/images/{image_name}")
async def get_result_image(image_name: str):
    """Serve a specific image."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    output_dir = PROJECT_ROOT / config.output_dir
    viz_dir = output_dir / "viz"
    image_path = viz_dir / image_name
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)


# ============================================================================
# Judge Results Endpoints
# ============================================================================

@app.get("/api/judge/results")
async def get_judge_results():
    """Get judge results if available."""
    config = run_manager.config
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    judge_log_dir = config.logging_config.get('file')
    if judge_log_dir:
        judge_dir = Path(judge_log_dir).parent / "judge"
    else:
        judge_dir = PROJECT_ROOT / "logs" / "judge"
    
    if not judge_dir.exists():
        return {"message": "No judge results found"}
    
    # Look for judge result files
    import glob
    result_files = list(judge_dir.glob("*.csv")) + list(judge_dir.glob("*.json"))
    
    results = {}
    for rf in result_files:
        if rf.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(rf)
            results[rf.stem] = {
                "type": "csv",
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records")
            }
        elif rf.suffix == '.json':
            import json
            with open(rf) as f:
                results[rf.stem] = {"type": "json", "data": json.load(f)}
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
