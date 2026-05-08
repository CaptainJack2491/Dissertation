import sys
import glob
import csv
import os

sys.path.insert(0, "src")
from judge.judge import Judge
import yaml

# The 8 new valid files from git status
new_files = [
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/high/20260415_214146.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/high/20260415_214243.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/high/20260415_214310.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/high/20260415_214626.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/high/20260415_214744.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/mid/20260415_214138.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/mid/20260415_214157.json",
    "logs/v2_study1/google_gemini-3.1-pro-preview/corporate_sabotage_v2/bare/mid/20260415_214217.json"
]

# Load validated configurations
config = yaml.safe_load(open("config_study1.yaml"))["judge"]
config["blackbox"]["id"] = config["blackbox"]["model"]
config["glassbox"]["id"] = config["glassbox"]["model"]

judge = Judge(
    blackbox_model=config["blackbox"],
    glassbox_model=config["glassbox"]
)

# 1. Read existing CSV
csv_path = "logs/v2_study1/study1_results.csv"
with open(csv_path) as f:
    existing_rows = list(csv.DictReader(f))

# 2. Drop the 8 corrupted rows
corrupted_timestamps = [
    "20260415_171552", "20260415_171559", "20260415_171806", "20260415_171816",
    "20260415_183235", "20260415_181921", "20260415_182006", "20260415_182013"
]

clean_rows = []
for r in existing_rows:
    if not any(ts in r["run_id"] for ts in corrupted_timestamps):
        clean_rows.append(r)

print(f"Removed {len(existing_rows) - len(clean_rows)} corrupted rows from CSV.")

# 3. Judge the 8 new files in single mode
print(f"Judging {len(new_files)} new files...")
for f in new_files:
    print(f"  Judging {f}...")
    verdict = judge.judge_single(
        log_path=f, 
        logs_dir="logs/v2_study1", 
        scenarios_dir="scenarios", 
        enabled_judges={"regex", "blackbox", "glassbox"}
    )
    
    # Optional: save judge log to disk immediately
    from judge_runner import save_judge_log
    save_judge_log(verdict, config.get("log_dir", "logs/v2_study1_judge"), "mixed")
    
    row = {
        "run_id": verdict.get("run_id", ""),
        "model": verdict.get("model", ""),
        "scenario": verdict.get("scenario", ""),
        "oversight": verdict.get("oversight", ""),
        "regex": verdict.get("regex", ""),
        "blackbox_category": verdict.get("blackbox", {}).get("category", ""),
        "blackbox_justification": verdict.get("blackbox", {}).get("justification", ""),
        "glassbox_category": verdict.get("glassbox", {}).get("category", ""),
        "glassbox_sophistication": verdict.get("glassbox", {}).get("sophistication", ""),
        "glassbox_justification": verdict.get("glassbox", {}).get("justification", "")
    }
    clean_rows.append(row)

# 4. Save updated CSV
with open(csv_path + ".tmp", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(clean_rows[0].keys()))
    writer.writeheader()
    writer.writerows(clean_rows)

os.rename(csv_path + ".tmp", csv_path)
print(f"\nSuccessfully saved perfect {len(clean_rows)}-run dataset to {csv_path}!")
