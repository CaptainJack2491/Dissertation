#!/usr/bin/env python3
import os
import json
import argparse
from collections import defaultdict
from pathlib import Path

def summarize_tokens(log_dir):
    """
    Summarizes token usage from JSON logs in the specified directory.
    Groups the results by model and then by scenario.
    """
    # Grouped by model, then scenario
    # Totals: prompt, completion, total, run_count
    summary = defaultdict(lambda: defaultdict(lambda: {
        'prompt_tokens': 0, 
        'completion_tokens': 0, 
        'total_tokens': 0, 
        'run_count': 0
    }))
    
    overall_totals = {
        'prompt_tokens': 0, 
        'completion_tokens': 0, 
        'total_tokens': 0, 
        'run_count': 0
    }

    path = Path(log_dir)
    if not path.exists() or not path.is_dir():
        print(f"Error: '{log_dir}' is not a valid directory.")
        return

    # Iterate through all JSON files in the log directory
    files_processed = 0
    for json_file in path.rglob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if it has the required fields
                if all(k in data for k in ['prompt_tokens', 'completion_tokens', 'total_tokens', 'model', 'scenario']):
                    model = data['model']
                    scenario = data['scenario']
                    
                    p_tokens = data.get('prompt_tokens', 0)
                    c_tokens = data.get('completion_tokens', 0)
                    t_tokens = data.get('total_tokens', 0)

                    # Update model/scenario totals
                    summary[model][scenario]['prompt_tokens'] += p_tokens
                    summary[model][scenario]['completion_tokens'] += c_tokens
                    summary[model][scenario]['total_tokens'] += t_tokens
                    summary[model][scenario]['run_count'] += 1
                    
                    # Update overall totals
                    overall_totals['prompt_tokens'] += p_tokens
                    overall_totals['completion_tokens'] += c_tokens
                    overall_totals['total_tokens'] += t_tokens
                    overall_totals['run_count'] += 1
                    
                    files_processed += 1
        except json.JSONDecodeError:
            # We skip files that are not valid JSON or completely empty 
            print(f"Warning: Could not parse {json_file}")
            pass
        except Exception as e:
            print(f"Warning: Error processing {json_file}: {e}")

    if files_processed == 0:
        print(f"No valid log files with token metrics found in '{log_dir}'.")
        return

    # Print summary
    print("=" * 90)
    print(f"{'Token Usage Summary':^90}")
    print("=" * 90)
    print()

    for model, scenarios in sorted(summary.items()):
        print(f"Model: {model}")
        print("-" * 90)
        print(f"{'Scenario':<45} | {'Runs':<5} | {'Prompt':<10} | {'Completion':<10} | {'Total':<10}")
        print("-" * 90)
        
        model_p = 0
        model_c = 0
        model_t = 0
        model_runs = 0
        
        for scenario, counts in sorted(scenarios.items()):
            p = counts['prompt_tokens']
            c = counts['completion_tokens']
            t = counts['total_tokens']
            r = counts['run_count']
            
            model_p += p
            model_c += c
            model_t += t
            model_runs += r
            
            print(f"{scenario:<45} | {r:<5} | {p:<10,d} | {c:<10,d} | {t:<10,d}")
            
        print("-" * 90)
        print(f"{'Model Total':<45} | {model_runs:<5} | {model_p:<10,d} | {model_c:<10,d} | {model_t:<10,d}")
        print("=" * 90)
        print()

    print(f"{'OVERALL TOTALS':<45} | {overall_totals['run_count']:<5} | {overall_totals['prompt_tokens']:<10,d} | {overall_totals['completion_tokens']:<10,d} | {overall_totals['total_tokens']:<10,d}")
    print("=" * 90)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize token usage from JSON logs.")
    parser.add_argument("log_dir", type=str, help="Path to the directory containing JSON log files")
    args = parser.parse_args()
    
    summarize_tokens(args.log_dir)
