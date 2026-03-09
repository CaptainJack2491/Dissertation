"""
FastAPI server for the AI Evaluation Visualization Dashboard.
Serves read-only results, JSON logs, and static visuals.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import json
import math

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path to import core modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.config_loader import ConfigLoader

app = FastAPI(
    title="AI Agent Evaluation Dashboard",
    description="Web GUI for analyzing experiment results",
    version="0.2.0"
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def get_config():
    """Helper to load config safely."""
    try:
        config = ConfigLoader(str(PROJECT_ROOT / "config.yaml"))
        config.load()
        return config
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        return None

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
    """List all CSV files in the output directory."""
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    output_dir = PROJECT_ROOT / config.output_dir
    if not output_dir.exists():
        return []
    
    files = []
    for p in output_dir.rglob("*.csv"):
        files.append(str(p.relative_to(output_dir)))
    return sorted(files)

@app.get("/api/results")
async def get_results(file: str = None):
    """Get experiment results as JSON, optionally for a specific file."""
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    output_dir = PROJECT_ROOT / config.output_dir
    
    csv_files = []
    if file:
        file_path = output_dir / file
        if not file_path.exists() or ".." in file:
            raise HTTPException(status_code=404, detail="File not found")
        csv_files.append(file_path)
    else:
        csv_files = list(output_dir.glob("*.csv")) if output_dir.exists() else []
    
    results = {}
    for csv_file in csv_files:
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
    config = get_config()
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
    config = get_config()
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

@app.get("/api/judge/files")
async def get_judge_files():
    """Get list of judge result files."""
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    judge_log_dir = config._config.get('judge', {}).get('log_dir', 'judge_logs')
    judge_dir = PROJECT_ROOT / judge_log_dir
    
    if not judge_dir.exists():
        return []
    
    files = []
    for p in judge_dir.rglob("*"):
        if p.suffix in ['.csv', '.json']:
            files.append(str(p.relative_to(judge_dir)))
    return sorted(files)

@app.get("/api/judge/results")
async def get_judge_results(file: str = None):
    """Get judge results if available."""
    config = get_config()
    if not config:
        raise HTTPException(status_code=500, detail="Config not loaded")
    
    judge_log_dir = config._config.get('judge', {}).get('log_dir', 'judge_logs')
    judge_dir = PROJECT_ROOT / judge_log_dir
    
    if not judge_dir.exists():
        return {"message": "No judge results found"}
    
    result_files = []
    if file:
        file_path = judge_dir / file
        if not file_path.exists() or ".." in file:
            raise HTTPException(status_code=404, detail="File not found")
        result_files.append(file_path)
    else:
        result_files = list(judge_dir.glob("*.csv")) + list(judge_dir.glob("*.json"))
    
    results = {}
    for rf in result_files:
        if rf.suffix == '.csv':
            try:
                df = pd.read_csv(rf)
                results[rf.stem] = {
                    "type": "csv",
                    "columns": df.columns.tolist(),
                    "data": df.to_dict(orient="records")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
