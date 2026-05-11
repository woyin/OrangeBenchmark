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
            typer.echo(f"score: {score_result.get('total', 0):.2f}")

    totals = [p["total"] for p in combo_result["problems"]]
    combo_result["overall"] = round(sum(totals) / max(len(totals), 1), 4) if totals else 0.0

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
):
    """Show historical ranking from results."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

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
            combo["overall"] = round(sum(totals) / max(len(totals), 1), 4) if totals else 0.0

        results["combos"] = [c for c in results["combos"] if c["problems"]]

    display_results(results)


@app.command()
def show(
    model: Optional[str] = typer.Option(None, "--model", help="Model/label name"),
    problem: Optional[str] = typer.Option(None, "--problem", help="Problem name"),
):
    """Show detailed result for a specific run."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    with open(result_files[-1]) as f:
        results = json.load(f)

    for combo in results.get("combos", []):
        if model and combo["model"] != model:
            continue
        if problem:
            combo["problems"] = [p for p in combo.get("problems", []) if p["name"] == problem]

        if combo.get("problems"):
            display_detail(combo)


if __name__ == "__main__":
    app()
