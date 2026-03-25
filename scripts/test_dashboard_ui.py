import time
import random
import threading
import concurrent.futures
from rich.live import Live
from src.dashboard import ExperimentDashboard, print_final_summary

def simulate_run(model, dashboard):
    """Simulate a single experiment run with random delay and outcome."""
    thread_id = threading.get_ident()
    scenario = f"scenario_{random.randint(1, 3)}"
    goal = random.choice(["self_serving", "moral", "bare", ""])
    
    dashboard.start_run(thread_id, model, scenario, goal)
    
    # Simulate work
    delay = random.uniform(1.0, 4.0)
    time.sleep(delay)
    
    success = random.random() > 0.3  # 70% success rate
    error = random.random() > 0.95   # 5% hard error rate
    tokens = random.randint(500, 3000)
    
    label = f"{model} | {scenario} | {goal or 'default'} | run 1"
    
    dashboard.complete_run(thread_id, model, success=success, tokens=tokens, duration=delay, error=error, label=label)
    
    return {
        "model": model,
        "scenario": scenario,
        "goal_type": goal,
        "oversight_level": random.choice(["low", "high"]),
        "success": success and not error,
        "total_tokens": tokens,
        "duration_seconds": delay
    }

def main():
    # Configuration for simulation: 3 models, more runs to test the grouped summary
    models = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"]
    total_runs = 27 # 3 models * 3 scenarios * 3 runs
    skipped = 3
    
    dashboard = ExperimentDashboard(total_runs, models, skipped=skipped)
    
    # Assign runs to models
    work_items = []
    for _ in range(total_runs):
        work_items.append(random.choice(models))
    
    # Update model totals in dashboard
    for model in models:
        count = work_items.count(model)
        dashboard.update_model_total(model, count)
    
    print("Starting Advanced Dashboard Simulation...")
    results = []
    
    with Live(dashboard.get_layout(), refresh_per_second=4, vertical_overflow="visible") as live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(simulate_run, model, dashboard) for model in work_items]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                live.update(dashboard.get_layout())
                
    # Show the final summary table
    print_final_summary(results)

if __name__ == "__main__":
    main()
