"""OrangeBenchmark CLI entry point."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml

from runner.executor import prepare_work_dir, run_task
from runner.reporter import display_detail, display_results
from runner.scorer import score_problem

app = typer.Typer(name="orangebench", help="OrangeBenchmark — LLM & Coding Agent evaluation framework")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
PROBLEMS_DIR = PROJECT_ROOT / "problems"
RESULTS_DIR = PROJECT_ROOT / "results"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        typer.echo("Error: config.yaml not found. Copy config.example.yaml to config.yaml and fill in your API keys.")
        raise typer.Exit(1)
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _discover_problems() -> list[tuple[str, Path, dict]]:
    """Discover all problems. Returns list of (name, dir_path, config)."""
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


def _resolve_combos(config: dict, models_filter: Optional[str], agents_filter: Optional[str], all_combos: bool) -> list[dict]:
    """Resolve which model×agent combos to run."""
    models = config.get("models", [])
    agents = config.get("agents", [])
    providers = config.get("providers", [])

    if models_filter:
        names = [n.strip() for n in models_filter.split(",")]
        models = [m for m in models if m["name"] in names]
    if agents_filter:
        names = [n.strip() for n in agents_filter.split(",")]
        agents = [a for a in agents if a["name"] in names]

    if all_combos:
        combos = []
        for m in models:
            for a in agents:
                combos.append({"model": m["name"], "agent": a["name"]})
        return combos

    combos = config.get("combos", [])
    if models_filter or agents_filter:
        if models_filter:
            m_names = {n.strip() for n in models_filter.split(",")}
            combos = [c for c in combos if c["model"] in m_names]
        if agents_filter:
            a_names = {n.strip() for n in agents_filter.split(",")}
            combos = [c for c in combos if c["agent"] in a_names]
    return combos


@app.command()
def run(
    problems: Optional[str] = typer.Option(None, "--problems", help="Comma-separated problem names"),
    models: Optional[str] = typer.Option(None, "--models", help="Comma-separated model names"),
    agents: Optional[str] = typer.Option(None, "--agents", help="Comma-separated agent names"),
    all_combos: bool = typer.Option(False, "--all-combos", help="Use cartesian product of all models×agents"),
):
    """Run evaluations."""
    config = _load_config()
    providers = config.get("providers", [])
    all_problems = _discover_problems()
    combos = _resolve_combos(config, models, agents, all_combos)

    if not combos:
        typer.echo("No combos to evaluate. Check config.yaml combos section.")
        raise typer.Exit(1)

    # Filter problems if specified
    if problems:
        names = {n.strip() for n in problems.split(",")}
        all_problems = [(n, p, c) for n, p, c in all_problems if n in names]

    if not all_problems:
        typer.echo("No problems found in problems/ directory.")
        raise typer.Exit(1)

    # Build lookup maps
    model_map = {m["name"]: m for m in config.get("models", [])}
    agent_map = {a["name"]: a for a in config.get("agents", [])}

    typer.echo(f"Running {len(combos)} combos × {len(all_problems)} problems ...")

    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "combos": [],
    }

    with tempfile.TemporaryDirectory(prefix="orangebench_") as tmpdir:
        tmpdir_path = Path(tmpdir)

        for combo in combos:
            model_name = combo["model"]
            agent_name = combo["agent"]
            model_cfg = model_map.get(model_name)
            agent_cfg = agent_map.get(agent_name)

            if not model_cfg or not agent_cfg:
                typer.echo(f"  Skipping unknown combo: {model_name} + {agent_name}")
                continue

            combo_result = {
                "model": model_name,
                "agent": agent_name,
                "problems": [],
            }

            for prob_name, prob_dir, prob_config in all_problems:
                typer.echo(f"  [{model_name}+{agent_name}] {prob_name} ... ", nl=False)

                work_dir = prepare_work_dir(prob_dir, tmpdir_path / f"{model_name}__{agent_name}")
                exec_result = run_task(
                    problem_config=prob_config,
                    model_cfg=model_cfg,
                    agent_cfg=agent_cfg,
                    providers=providers,
                    work_dir=work_dir,
                    timeout_seconds=prob_config.get("timeout", 30),
                )

                if exec_result["status"] == "pass" and exec_result["generated_code"]:
                    score_result = score_problem(
                        problem_dir=prob_dir,
                        work_dir=work_dir,
                        generated_code=exec_result["generated_code"],
                        problem_config=prob_config,
                    )
                else:
                    score_result = {"scores": {}, "total": 0.0}

                problem_result = {
                    "name": prob_name,
                    "scores": score_result.get("scores", {}),
                    "total": score_result.get("total", 0.0),
                    "status": exec_result["status"],
                    "duration_seconds": exec_result["duration_seconds"],
                }
                if exec_result.get("error"):
                    problem_result["error"] = exec_result["error"]

                combo_result["problems"].append(problem_result)
                typer.echo(f"{exec_result['status']} (score: {score_result.get('total', 0):.2f})")

            # Calculate overall score for this combo
            totals = [p["total"] for p in combo_result["problems"]]
            combo_result["overall"] = round(sum(totals) / max(len(totals), 1), 4)
            results["combos"].append(combo_result)

    # Save results
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    result_path = RESULTS_DIR / f"{ts}.json"
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    typer.echo(f"\nResults saved to {result_path}")

    # Display ranking
    display_results(results)


@app.command()
def ranking(
    category: Optional[str] = typer.Option(None, "--category", help="Filter by problem category"),
    difficulty: Optional[str] = typer.Option(None, "--difficulty", help="Filter by difficulty"),
):
    """Show historical ranking from results."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench run` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    # Load latest result
    with open(result_files[-1]) as f:
        results = json.load(f)

    # Apply filters if problems metadata available
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
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Agent name"),
    problem: Optional[str] = typer.Option(None, "--problem", help="Problem name"),
):
    """Show detailed result for a specific combo+problem."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench run` first.")
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
        if agent and combo["agent"] != agent:
            continue
        if problem:
            combo["problems"] = [p for p in combo.get("problems", []) if p["name"] == problem]

        if combo.get("problems"):
            display_detail(combo)


if __name__ == "__main__":
    app()
