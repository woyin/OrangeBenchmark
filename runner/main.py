"""OrangeBenchmark CLI entry point."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from runner.executor import prepare_work_dir
from runner.reporter import display_detail, display_results
from runner.scorer import score_problem

app = typer.Typer(name="orangebench", help="OrangeBenchmark — LLM & Coding Agent evaluation framework")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = PROJECT_ROOT / "problems"
RESULTS_DIR = PROJECT_ROOT / "results"


def _trim_mean(values: list[float]) -> float:
    """Compute trim-mean: remove bottom 10%, average the rest."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    trim_count = max(1, len(sorted_vals) // 10)
    trimmed = sorted_vals[trim_count:]
    if not trimmed:
        return sorted_vals[0]
    return round(sum(trimmed) / len(trimmed), 4)


def _discover_problems() -> list[tuple[str, Path, dict]]:
    """Discover all problems. Returns list of (name, dir_path, config)."""
    import yaml
    problems = []
    if not PROBLEMS_DIR.exists():
        return problems
    for subdir in sorted(PROBLEMS_DIR.iterdir()):
        if subdir.name.startswith("_"):
            continue
        yaml_path = subdir / "problem.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                config = yaml.safe_load(f)
            problems.append((config.get("name", subdir.name), subdir, config))
    return problems


@app.command()
def list_problems(
    difficulty: Optional[str] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty (easy/medium/hard)"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter by language (python/java/dotnet/react/bash/rust)"),
):
    """List all available problems."""
    all_problems = _discover_problems()
    if not all_problems:
        typer.echo("No problems found in problems/ directory.")
        raise typer.Exit(1)

    # Apply filters
    filtered = []
    for name, prob_dir, config in all_problems:
        diff = config.get("difficulty", "unknown")
        cat = config.get("category", "unknown")
        lang = _detect_language(name)

        if difficulty and diff != difficulty:
            continue
        if category and cat != category:
            continue
        if language and lang != language.lower():
            continue
        filtered.append((name, config, lang))

    if not filtered:
        typer.echo("No problems match the specified filters.")
        raise typer.Exit(1)

    # Group by language
    from collections import defaultdict
    grouped = defaultdict(list)
    for name, config, lang in filtered:
        grouped[lang].append((name, config))

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title=f"OrangeBenchmark Problems ({len(filtered)} total)", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Problem", min_width=25)
    table.add_column("Difficulty", min_width=8)
    table.add_column("Category", min_width=12)
    table.add_column("Language", min_width=8)

    idx = 0
    for lang in sorted(grouped.keys()):
        for name, config in grouped[lang]:
            idx += 1
            diff = config.get("difficulty", "unknown")
            cat = config.get("category", "unknown")
            # Color-code difficulty
            diff_display = {
                "easy": "[green]easy[/green]",
                "medium": "[yellow]medium[/yellow]",
                "hard": "[red]hard[/red]",
            }.get(diff, diff)
            table.add_row(str(idx), name, diff_display, cat, lang)

    console.print()
    console.print(table)
    console.print()


def _detect_language(name: str) -> str:
    """Detect problem language from name prefix."""
    if name.startswith("java-"):
        return "java"
    elif name.startswith("dotnet-"):
        return "dotnet"
    elif name.startswith("react-"):
        return "react"
    elif name.startswith("bash-"):
        return "bash"
    elif name.startswith("python-"):
        return "python"
    elif name.startswith("rust-") or name == "wasm-calculator":
        return "rust"
    # Python problems without prefix
    return "python"


@app.command()
def score(
    problems: Optional[str] = typer.Option(None, "--problems", help="Comma-separated problem names (default: all)"),
    label: Optional[str] = typer.Option(None, "--label", help="Label for this evaluation run (e.g. model name)"),
):
    """Score already-written solutions in the repository (no API calls).

    For each problem, copies tests + scaffold into a temp directory,
    copies the agent's solution in, runs tests, and produces a score.
    Results are saved to results/ for historical tracking.
    """
    all_problems = _discover_problems()
    if problems:
        names = {n.strip() for n in problems.split(",")}
        all_problems = [(n, p, c) for n, p, c in all_problems if n in names]

    if not all_problems:
        typer.echo("No problems found in problems/ directory.")
        raise typer.Exit(1)

    label = label or "local-agent"
    ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    typer.echo(f"Scoring {len(all_problems)} problems for label '{label}' ...")

    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "combos": [
            {
                "model": label,
                "agent": "local",
                "problems": [],
            }
        ],
    }
    combo_result = results["combos"][0]

    with tempfile.TemporaryDirectory(prefix="orangebench_score_") as tmpdir:
        tmpdir_path = Path(tmpdir)

        for prob_name, prob_dir, prob_config in all_problems:
            typer.echo(f"  {prob_name} ... ", nl=False)

            target_file = prob_config.get("target_file", "solution.py")
            target_path = prob_dir / target_file

            work_dir = prepare_work_dir(
                prob_dir,
                tmpdir_path / label,
                prob_config,
            )

            work_target = work_dir / target_file
            if not target_path.exists():
                typer.echo("SKIP (no solution file)")
                combo_result["problems"].append({
                    "name": prob_name,
                    "scores": {},
                    "total": 0.0,
                    "status": "missing",
                })
                continue

            work_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, work_target)

            generated_code = target_path.read_text()

            score_result = score_problem(
                problem_dir=prob_dir,
                work_dir=work_dir,
                generated_code=generated_code,
                problem_config=prob_config,
            )

            problem_result = {
                "name": prob_name,
                "scores": score_result.get("scores", {}),
                "total": score_result.get("total", 0.0),
                "status": "scored",
            }
            combo_result["problems"].append(problem_result)
            typer.echo(f"score: {score_result.get('total', 0):.3f}")

    totals = [p["total"] for p in combo_result["problems"]]
    combo_result["overall"] = _trim_mean(totals)

    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = RESULTS_DIR / f"{ts}.json"
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    typer.echo(f"\nResults saved to {result_path}")
    display_results(results)


@app.command()
def ranking(
    category: Optional[str] = typer.Option(None, "--category", help="Filter by problem category"),
    difficulty: Optional[str] = typer.Option(None, "--difficulty", help="Filter by difficulty"),
    all_runs: bool = typer.Option(False, "--all", "-a", help="Show all historical runs (not just the latest)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Limit number of runs to display"),
):
    """Show historical ranking from results."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    if all_runs:
        # Show summary of all runs
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="OrangeBenchmark — All Runs", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Timestamp", min_width=20)
        table.add_column("Models", min_width=20)
        table.add_column("Problems", justify="right", min_width=8)
        table.add_column("Best Score", justify="right", min_width=10)

        files_to_show = result_files
        if limit:
            files_to_show = result_files[-limit:]

        for idx, result_file in enumerate(files_to_show, 1):
            with open(result_file) as f:
                data = json.load(f)
            ts = data.get("timestamp", result_file.stem)
            combos = data.get("combos", [])
            models = ", ".join(set(c.get("model", "?") for c in combos))
            prob_count = sum(len(c.get("problems", [])) for c in combos)
            best = max((c.get("overall", 0) for c in combos), default=0)
            table.add_row(str(idx), ts, models, str(prob_count), f"{best:.3f}")

        console.print()
        console.print(table)
        console.print()
    else:
        # Show latest run (existing behavior)
        with open(result_files[-1]) as f:
            results = json.load(f)

        if category or difficulty:
            problems_list = _discover_problems()
            prob_meta = {}
            for name, _, config in problems_list:
                prob_meta[name] = config

            for combo in results.get("combos", []):
                filtered = []
                for p in combo.get("problems", []):
                    meta = prob_meta.get(p["name"], {})
                    if category and meta.get("category") != category:
                        continue
                    if difficulty and meta.get("difficulty") != difficulty:
                        continue
                    filtered.append(p)
                combo["problems"] = filtered
                totals = [p["total"] for p in filtered]
                combo["overall"] = _trim_mean(totals)

            results["combos"] = [c for c in results["combos"] if c["problems"]]

        display_results(results)


@app.command()
def show(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model/label name"),
    problem: Optional[str] = typer.Option(None, "--problem", "-p", help="Problem name"),
    all_runs: bool = typer.Option(False, "--all", "-a", help="Show results from all runs (not just the latest)"),
):
    """Show detailed result for a specific run. If no model specified, list all models."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    with open(result_files[-1]) as f:
        results = json.load(f)

    combos = results.get("combos", [])

    if not model:
        # List all models with their scores
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Available Models", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Model", min_width=18)
        table.add_column("Agent", min_width=14)
        table.add_column("Problems", justify="right", min_width=8)
        table.add_column("Overall", justify="right", min_width=10)

        for idx, combo in enumerate(combos, 1):
            table.add_row(
                str(idx),
                combo.get("model", "?"),
                combo.get("agent", "?"),
                str(len(combo.get("problems", []))),
                f"{combo.get('overall', 0):.3f}",
            )

        console.print()
        console.print(table)
        console.print("\nUse --model <name> to see detailed results.")
    else:
        for combo in combos:
            if combo["model"] != model:
                continue
            if problem:
                combo["problems"] = [p for p in combo.get("problems", []) if p["name"] == problem]

            if combo.get("problems"):
                display_detail(combo)


if __name__ == "__main__":
    app()
