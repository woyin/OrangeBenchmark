"""Execute model/agent calls and collect generated code."""

import shutil
import time
from pathlib import Path

from openai import OpenAI


def _get_provider_config(providers: list[dict], provider_name: str) -> dict:
    for p in providers:
        if p["name"] == provider_name:
            return p
    raise ValueError(f"Provider '{provider_name}' not found in config")


def _create_client(provider: dict):
    """Create an OpenAI-compatible client for the given provider."""
    return OpenAI(
        base_url=provider["base_url"],
        api_key=provider["api_key"],
    )


def _extract_code_from_response(response_text: str) -> str:
    """Extract code from a model response, handling markdown code blocks."""
    if "```" in response_text:
        parts = response_text.split("```")
        # Take the content of the first code block
        for i in range(1, len(parts), 2):
            code = parts[i]
            lines = code.split("\n")
            # Remove language identifier line if present
            if lines and lines[0].strip() and not lines[0].strip().startswith(
                (" ", "\t", "import", "from", "def", "class", "#", "\"", "'")
            ):
                lines = lines[1:]
            return "\n".join(lines).strip()
    return response_text.strip()


def run_task(
    problem_config: dict,
    model_cfg: dict,
    agent_cfg: dict,
    providers: list[dict],
    work_dir: Path,
    timeout_seconds: int = 30,
) -> dict:
    """Run a single problem against a model+agent combo.

    Returns dict with: generated_code, duration_seconds, status, error (optional)
    """
    provider = _get_provider_config(providers, model_cfg["provider"])
    prompt = problem_config["prompt"]
    target_file = problem_config.get("target_file", "solution.py")
    target_path = work_dir / target_file

    agent_type = agent_cfg.get("type", "raw")

    start = time.time()
    try:
        if agent_type == "raw":
            generated_code = _run_raw(prompt, model_cfg, provider, timeout_seconds)
        else:
            # Agent mode: future support for CLI agents
            generated_code = _run_raw(prompt, model_cfg, provider, timeout_seconds)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(generated_code)
        duration = time.time() - start
        return {
            "generated_code": generated_code,
            "duration_seconds": round(duration, 2),
            "status": "pass" if generated_code else "fail",
        }

    except TimeoutError:
        return {
            "generated_code": "",
            "duration_seconds": timeout_seconds,
            "status": "timeout",
            "error": "Execution timed out",
        }
    except Exception as e:
        return {
            "generated_code": "",
            "duration_seconds": round(time.time() - start, 2),
            "status": "error",
            "error": str(e),
        }


def _run_raw(prompt: str, model_cfg: dict, provider: dict, timeout: int) -> str:
    """Single-turn API call using OpenAI-compatible client."""
    client = _create_client(provider)

    response = client.chat.completions.create(
        model=model_cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    text = response.choices[0].message.content or ""
    return _extract_code_from_response(text)


def prepare_work_dir(problem_dir: Path, base_work_dir: Path) -> Path:
    """Create a temp work dir and copy problem's tests/ and conftest.py into it."""
    work_dir = base_work_dir / problem_dir.name
    work_dir.mkdir(parents=True, exist_ok=True)

    # Copy tests directory
    tests_src = problem_dir / "tests"
    if tests_src.exists():
        tests_dst = work_dir / "tests"
        if tests_dst.exists():
            shutil.rmtree(tests_dst)
        shutil.copytree(tests_src, tests_dst)

    # Copy conftest.py if exists
    conftest_src = problem_dir / "conftest.py"
    if conftest_src.exists():
        shutil.copy2(conftest_src, work_dir / "conftest.py")

    return work_dir
