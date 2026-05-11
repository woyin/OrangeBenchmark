"""Execute model/agent calls and collect generated code."""

import shutil
import time
from pathlib import Path

from openai import OpenAI

from runner.tracer import RawTracer, TraceResult


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
        for i in range(1, len(parts), 2):
            code = parts[i]
            lines = code.split("\n")
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

    Returns dict with: generated_code, duration_seconds, status, trace (optional)
    """
    provider = _get_provider_config(providers, model_cfg["provider"])
    prompt = problem_config["prompt"]
    target_file = problem_config.get("target_file", "solution.py")
    target_path = work_dir / target_file

    agent_type = agent_cfg.get("type", "raw")
    tracer = RawTracer(model=model_cfg["model"])
    tracer.start_session()
    tracer.result.problem = problem_config.get("name", "")

    start = time.time()
    try:
        if agent_type == "raw":
            generated_code = _run_raw(prompt, model_cfg, provider, timeout_seconds, tracer)
        else:
            # Agent mode: future support for CLI agents
            generated_code = _run_raw(prompt, model_cfg, provider, timeout_seconds, tracer)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(generated_code)
        duration = time.time() - start
        trace_result = tracer.finish_session()

        return {
            "generated_code": generated_code,
            "duration_seconds": round(duration, 2),
            "status": "pass" if generated_code else "fail",
            "trace": trace_result.to_dict(),
        }

    except TimeoutError:
        return {
            "generated_code": "",
            "duration_seconds": timeout_seconds,
            "status": "timeout",
            "error": "Execution timed out",
            "trace": tracer.finish_session().to_dict(),
        }
    except Exception as e:
        return {
            "generated_code": "",
            "duration_seconds": round(time.time() - start, 2),
            "status": "error",
            "error": str(e),
            "trace": tracer.finish_session().to_dict(),
        }


def _run_raw(prompt: str, model_cfg: dict, provider: dict, timeout: int, tracer: RawTracer) -> str:
    """Single-turn API call using OpenAI-compatible client with tracing."""
    client = _create_client(provider)

    start = time.time()
    response = client.chat.completions.create(
        model=model_cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    duration_ms = int((time.time() - start) * 1000)

    # Extract usage information
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or 0
    output_tokens = getattr(usage, "completion_tokens", 0) or 0

    tracer.record_api_call(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        model_name=model_cfg.get("model", ""),
    )

    text = response.choices[0].message.content or ""
    return _extract_code_from_response(text)


def prepare_work_dir(
    problem_dir: Path,
    base_work_dir: Path,
    problem_config: dict | None = None,
) -> Path:
    """Create a temp work dir and copy problem scaffold files into it."""
    work_dir = base_work_dir / problem_dir.name
    work_dir.mkdir(parents=True, exist_ok=True)

    copy_paths = (problem_config or {}).get("copy_paths")
    if copy_paths:
        for rel_path in copy_paths:
            src = problem_dir / rel_path
            dst = work_dir / rel_path
            if not src.exists():
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return work_dir

    tests_src = problem_dir / "tests"
    if tests_src.exists():
        tests_dst = work_dir / "tests"
        if tests_dst.exists():
            shutil.rmtree(tests_dst)
        shutil.copytree(tests_src, tests_dst)

    conftest_src = problem_dir / "conftest.py"
    if conftest_src.exists():
        shutil.copy2(conftest_src, work_dir / "conftest.py")

    return work_dir
