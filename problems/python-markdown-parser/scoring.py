import importlib.util
import time
from pathlib import Path

SAMPLE_MD = """# Title

This is **bold** and *italic* text with [a link](https://example.com).

## Section

- item one with `code`
- item two with **bold**

```
def hello():
    print("world")
```

### Subsection

1. first
2. second

End paragraph.
"""

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "markdown_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    start = time.perf_counter()
    for _ in range(1000):
        module.markdown_to_html(SAMPLE_MD)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=1.0, slow=4.0)
