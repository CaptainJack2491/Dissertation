from typing import List, Dict, Optional, Deque
import threading
import time
from collections import deque
from rich.console import Console
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

# Thread-safe lock for dashboard updates
_dashboard_lock = threading.Lock()

class ExperimentDashboard:
    """Rich dashboard for real-time experiment tracking with per-model stats."""

    def __init__(self, total_runs: int, models: List[str], skipped: int = 0):
        self.console = Console()
        self.total_runs = total_runs
        self.skipped = skipped
        self.success_count = 0
        self.incomplete_count = 0
        self.failed_count = 0
        self.total_tokens = 0
        self.start_time = time.time()
        
        # Per-model stats
        self.model_stats = {
            model: {
                "success": 0,
                "total": 0,
                "target": 0,
                "tokens": 0,
                "time": 0.0
            } for model in models
        }
        
        # Track currently active runs
        self.active_runs = {} # thread_id -> info string
        
        # Recent activity log
        self.activity_log: Deque[str] = deque(maxlen=5)
        
        # Progress bars
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            expand=True
        )
        
        self.overall_task = self.progress.add_task("[yellow]Overall Progress", total=total_runs)
        self.model_tasks = {}
        for model in models:
            self.model_tasks[model] = self.progress.add_task(f"[blue]{model}", total=0)

    def update_model_total(self, model: str, count: int):
        """Update total runs for a specific model task."""
        with _dashboard_lock:
            if model in self.model_tasks:
                self.progress.update(self.model_tasks[model], total=count)
                self.model_stats[model]["target"] = count

    def start_run(self, thread_id: int, model: str, scenario: str, goal: str):
        """Mark a run as active."""
        with _dashboard_lock:
            goal_str = f" ({goal})" if goal else ""
            self.active_runs[thread_id] = f"[bold blue]{model}[/] | {scenario}{goal_str}"

    def complete_run(self, thread_id: int, model: str, success: bool, tokens: int = 0, duration: float = 0.0, error: bool = False, label: str = ""):
        """Update counts and progress when a run completes."""
        with _dashboard_lock:
            # Update global counts
            if error:
                self.failed_count += 1
                status_msg = "[red]ERROR[/]"
            elif success:
                self.success_count += 1
                status_msg = "[green]SUCCESS[/]"
            else:
                self.incomplete_count += 1
                status_msg = "[yellow]INCOMPLETE[/]"
            
            self.total_tokens += tokens
            
            # Update per-model stats
            if model in self.model_stats:
                m_stats = self.model_stats[model]
                m_stats["total"] += 1
                if success and not error:
                    m_stats["success"] += 1
                m_stats["tokens"] += tokens
                m_stats["time"] += duration
            
            # Update progress bars
            self.progress.update(self.overall_task, advance=1)
            if model in self.model_tasks:
                self.progress.update(self.model_tasks[model], advance=1)
            
            # Update activity log
            timestamp = time.strftime("%H:%M:%S")
            self.activity_log.append(f"[{timestamp}] {status_msg} {label}")
            
            # Remove from active runs
            if thread_id in self.active_runs:
                del self.active_runs[thread_id]

    def generate_model_table(self) -> Table:
        """Generate a detailed per-model statistics table."""
        table = Table(expand=True, box=None)
        table.add_column("Model", style="blue", ratio=2)
        table.add_column("Progress", justify="right", ratio=1)
        table.add_column("Success %", justify="right", ratio=1)
        table.add_column("Tokens", justify="right", ratio=1)
        table.add_column("Avg Time", justify="right", ratio=1)
        
        for model, stats in self.model_stats.items():
            if stats["target"] == 0: continue
            
            progress = f"{stats['total']}/{stats['target']}"
            success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            avg_time = (stats["time"] / stats["total"]) if stats["total"] > 0 else 0
            
            table.add_row(
                model,
                progress,
                f"{success_rate:.0f}%",
                f"{stats['tokens']:,}",
                f"{avg_time:.1f}s"
            )
        return table

    def format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS."""
        if seconds is None:
            return "--:--:--"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def generate_status_table(self) -> Table:
        """Generate a summary table of the current status."""
        table = Table(expand=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="magenta")
        
        completed = self.success_count + self.incomplete_count + self.failed_count
        remaining = self.total_runs - completed
        
        # Time calculations
        elapsed = time.time() - self.start_time
        time_remaining = self.progress.tasks[self.overall_task].time_remaining
        
        table.add_row("Success", f"[green]{self.success_count}[/green]")
        table.add_row("Incomplete", f"[yellow]{self.incomplete_count}[/yellow]")
        table.add_row("Failed", f"[red]{self.failed_count}[/red]")
        table.add_row("Remaining", f"[white]{remaining}[/white]")
        table.add_section()
        table.add_row("Total Tokens", f"[bold white]{self.total_tokens:,}[/bold white]")
        table.add_row("Elapsed", self.format_time(elapsed))
        table.add_row("Est. Left", self.format_time(time_remaining))
        table.add_row("Skipped", f"[grey50]{self.skipped}[/grey50]")
        
        return table

    def generate_active_panel(self) -> Panel:
        """Generate a panel showing currently active runs."""
        if not self.active_runs:
            content = Text("Waiting for workers...", style="italic grey50")
        else:
            # Fix: Join using Text.from_markup to ensure colors render
            lines = [Text.from_markup(line) for line in self.active_runs.values()]
            content = Text("\n").join(lines)
        return Panel(content, title="Currently Running", border_style="dim")

    def generate_log_panel(self) -> Panel:
        """Generate a panel showing recent activity log."""
        # Fix: Join using Text.from_markup to ensure colors render
        lines = [Text.from_markup(line) for line in self.activity_log]
        content = Text("\n").join(lines)
        return Panel(content, title="Recent Activity", border_style="dim")

    def get_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=7)
        )
        
        layout["main"].split_row(
            Layout(name="progress_col", ratio=2),
            Layout(name="stats_col", ratio=1)
        )
        
        layout["progress_col"].split_column(
            Layout(name="bars", ratio=1),
            Layout(name="model_details", ratio=1)
        )
        
        layout["footer"].split_row(
            Layout(name="active", ratio=1),
            Layout(name="logs", ratio=1)
        )
        
        layout["header"].update(Panel(Text("AI Agent Experiment Framework", justify="center", style="bold white"), style="blue"))
        layout["bars"].update(Panel(self.progress, title="Overall Progress", style="white"))
        layout["model_details"].update(Panel(self.generate_model_table(), title="Model Stats", style="white"))
        layout["stats_col"].update(Panel(self.generate_status_table(), title="Totals", style="white"))
        layout["active"].update(self.generate_active_panel())
        layout["logs"].update(self.generate_log_panel())
        
        return layout

def print_final_summary(results: List[Dict]):
    """Print a pretty grouped summary table at the end."""
    console = Console()
    console.print("\n")
    
    # Group results by Model and Scenario
    grouped = {}
    for r in results:
        key = (r['model'], r['scenario'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)

    table = Table(title="[bold]Final Experiment Summary[/bold]", show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Model", style="blue", no_wrap=True)
    table.add_column("Scenario", style="cyan")
    table.add_column("Goal Type", style="yellow")
    table.add_column("Successes", justify="center")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Avg Time", justify="right")

    for (model, scenario), group in sorted(grouped.items()):
        total = len(group)
        successes = sum(1 for r in group if r.get("success"))
        total_tokens = sum(r.get("total_tokens", 0) for r in group)
        avg_time = sum(r.get("duration_seconds", 0.0) for r in group) / total
        
        # Collect distinct goal types in this group
        goals = ", ".join(sorted(list(set(r.get("goal_type", "default") or "default" for r in group))))
        
        success_color = "green" if successes == total else "yellow" if successes > 0 else "red"
        
        table.add_row(
            model,
            scenario,
            goals,
            f"[{success_color}]{successes}/{total}[/]",
            f"{total_tokens:,}",
            f"{avg_time:.1f}s"
        )
    
    console.print(table)
    
    # Aggregated Per-Model Table
    model_table = Table(title="[bold]Aggregated Model Performance[/bold]", show_header=True, header_style="bold blue")
    model_table.add_column("Model")
    model_table.add_column("Total Runs", justify="right")
    model_table.add_column("Overall Success %", justify="right")
    model_table.add_column("Total Tokens", justify="right")

    models = sorted(list(set(r['model'] for r in results)))
    for model in models:
        m_results = [r for r in results if r['model'] == model]
        m_total = len(m_results)
        m_successes = sum(1 for r in m_results if r.get("success"))
        m_tokens = sum(r.get("total_tokens", 0) for r in m_results)
        
        rate = (m_successes / m_total * 100) if m_total > 0 else 0
        model_table.add_row(
            model,
            str(m_total),
            f"{rate:.1f}%",
            f"{m_tokens:,}"
        )
    
    console.print("\n")
    console.print(model_table)
