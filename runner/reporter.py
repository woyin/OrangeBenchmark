"""Terminal output using rich tables."""

import json
from rich.console import Console
from rich.table import Table


def _grade_label(score: float) -> str:
    """Return styled grade label based on score."""
    if score >= 0.95:
        return "[green]A+[/green]"
    elif score >= 0.85:
        return "[blue]A[/blue]"
    elif score >= 0.70:
        return "[yellow]B[/yellow]"
    elif score >= 0.50:
        return "[orange1]C[/orange1]"
    else:
        return "[red]D[/red]"


def display_results(results: dict) -> None:
    """Display the main ranking table."""
    console = Console()

    title = f"OrangeBenchmark — {results['timestamp']}"
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Model", min_width=18)
    table.add_column("Agent", min_width=14)
    table.add_column("Overall", justify="right", min_width=8)
    table.add_column("Grade", justify="center", min_width=5)

    dim_names = []
    for combo in results.get("combos", []):
        for prob in combo.get("problems", []):
            for dim_name in prob.get("scores", {}):
                if dim_name not in dim_names:
                    dim_names.append(dim_name)

    for dim in dim_names:
        table.add_column(dim, justify="right", min_width=8)

    sorted_combos = sorted(
        results.get("combos", []),
        key=lambda c: c.get("overall", 0),
        reverse=True,
    )

    for idx, combo in enumerate(sorted_combos, 1):
        avg_scores = _avg_scores(combo)
        overall = combo.get("overall", 0)
        display_overall = round(overall ** 0.85, 3) if overall > 0 else 0.0
        row = [
            str(idx),
            combo["model"],
            combo["agent"],
            f"{display_overall:.3f}",
            _grade_label(display_overall),
        ]
        for dim in dim_names:
            val = avg_scores.get(dim)
            if val is None:
                row.append("—")
            else:
                row.append(f"{val:.3f}")
        table.add_row(*row)

    console.print()
    console.print(table)
    console.print()


def display_detail(result_entry: dict, show_trace: bool = False) -> None:
    """Display detailed breakdown for one combo+problem."""
    console = Console()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Problem", min_width=18)
    table.add_column("Status", min_width=8)
    table.add_column("Total", justify="right", min_width=8)
    table.add_column("Grade", justify="center", min_width=5)
    table.add_column("Duration", justify="right", min_width=8)

    dim_names = []
    for prob in result_entry.get("problems", []):
        for dim_name in prob.get("scores", {}):
            if dim_name not in dim_names:
                dim_names.append(dim_name)

    for dim in dim_names:
        table.add_column(dim, justify="right", min_width=10)

    for prob in result_entry.get("problems", []):
        total = prob.get("total", 0)
        row = [
            prob["name"],
            prob.get("status", "unknown"),
            f"{total:.3f}",
            _grade_label(total),
            f"{prob.get('duration_seconds', 0):.1f}s",
        ]
        for dim in dim_names:
            val = prob.get("scores", {}).get(dim)
            if val is None:
                row.append("—")
            else:
                row.append(f"{val:.3f}")
        table.add_row(*row)

    console.print()
    console.print(
        f"[bold]Detail: {result_entry['model']} + {result_entry['agent']}[/bold]"
    )
    console.print(table)
    console.print()

    if show_trace:
        for prob in result_entry.get("problems", []):
            trace = prob.get("trace")
            if trace:
                console.print(f"[bold cyan]Trace: {prob['name']}[/bold cyan]")
                console.print(f"  Summary: {json.dumps(trace.get('summary', {}), indent=4)}")
                console.print(f"  Events ({len(trace.get('events', []))}):")
                for event in trace.get("events", []):
                    event_type = event.get("type", "?")
                    ts = event.get("timestamp", "")
                    extra = {k: v for k, v in event.items() if k not in ("type", "timestamp")}
                    console.print(f"    [{event_type}] {ts}  {extra}")
                console.print()


def _avg_scores(combo: dict) -> dict[str, float | None]:
    """Average dimension scores across all problems for a combo."""
    dims: dict[str, list[float]] = {}
    for prob in combo.get("problems", []):
        for dim_name, val in prob.get("scores", {}).items():
            dims.setdefault(dim_name, []).append(val)
    return {k: sum(v) / len(v) for k, v in dims.items()}
