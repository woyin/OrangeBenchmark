"""Terminal output using rich tables."""

from rich.console import Console
from rich.table import Table


def display_results(results: dict) -> None:
    """Display the main ranking table."""
    console = Console()

    title = f"OrangeBenchmark — {results['timestamp']}"
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Model", min_width=18)
    table.add_column("Agent", min_width=14)
    table.add_column("Overall", justify="right", min_width=8)

    # Collect all dimension names from results
    dim_names = []
    for combo in results.get("combos", []):
        for prob in combo.get("problems", []):
            for dim_name in prob.get("scores", {}):
                if dim_name not in dim_names:
                    dim_names.append(dim_name)

    for dim in dim_names:
        table.add_column(dim[0].upper(), justify="right", min_width=5)

    # Sort combos by overall score descending
    sorted_combos = sorted(
        results.get("combos", []),
        key=lambda c: c.get("overall", 0),
        reverse=True,
    )

    for idx, combo in enumerate(sorted_combos, 1):
        avg_scores = _avg_scores(combo)
        row = [
            str(idx),
            combo["model"],
            combo["agent"],
            f"{combo.get('overall', 0):.2f}",
        ]
        for dim in dim_names:
            row.append(f"{avg_scores.get(dim, 0):.2f}")
        table.add_row(*row)

    console.print()
    console.print(table)
    console.print()


def display_detail(result_entry: dict) -> None:
    """Display detailed breakdown for one combo+problem."""
    console = Console()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Problem", min_width=18)
    table.add_column("Status", min_width=8)
    table.add_column("Total", justify="right", min_width=8)
    table.add_column("Duration", justify="right", min_width=8)

    dim_names = []
    for prob in result_entry.get("problems", []):
        for dim_name in prob.get("scores", {}):
            if dim_name not in dim_names:
                dim_names.append(dim_name)

    for dim in dim_names:
        table.add_column(dim, justify="right", min_width=10)

    for prob in result_entry.get("problems", []):
        row = [
            prob["name"],
            prob.get("status", "unknown"),
            f"{prob.get('total', 0):.2f}",
            f"{prob.get('duration_seconds', 0):.1f}s",
        ]
        for dim in dim_names:
            row.append(f"{prob.get('scores', {}).get(dim, 0):.2f}")
        table.add_row(*row)

    console.print()
    console.print(
        f"[bold]Detail: {result_entry['model']} + {result_entry['agent']}[/bold]"
    )
    console.print(table)
    console.print()


def _avg_scores(combo: dict) -> dict[str, float]:
    """Average dimension scores across all problems for a combo."""
    dims: dict[str, list[float]] = {}
    for prob in combo.get("problems", []):
        for dim_name, val in prob.get("scores", {}).items():
            dims.setdefault(dim_name, []).append(val)
    return {k: sum(v) / len(v) for k, v in dims.items()}
