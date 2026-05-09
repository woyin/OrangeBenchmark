# OrangeBenchmark — 模型 & Coding Agent 评测框架设计

## 概述

OrangeBenchmark 是一个面向个人/小团队的评测工具，用于对比不同大语言模型和 Coding Agent 在代码任务上的表现。提供结构化题目定义、多维度自动评分、终端排行榜输出。

## 项目结构

```
OrangeBenchmark/
├── runner/                  # Runner 核心
│   ├── __init__.py
│   ├── main.py              # CLI 入口（typer）
│   ├── executor.py          # 拉起模型/Agent，发送任务，收集结果
│   ├── scorer.py            # 调用题目的评分逻辑，汇总分数
│   └── reporter.py          # 终端表格输出排名
├── problems/                # 所有评测题目
│   ├── _template/           # 新题目模板（复制即用）
│   │   ├── problem.yaml
│   │   ├── solution.py      # 参考答案（可选）
│   │   ├── tests/
│   │   │   └── test_solution.py
│   │   └── scoring.py       # 评分逻辑（可选，覆盖默认）
│   ├── sorting-algo/
│   │   ├── problem.yaml
│   │   ├── tests/
│   │   │   └── test_solution.py
│   │   └── scoring.py
│   └── ...
├── results/                 # 评测结果（JSON）
│   └── 2026-05-09T120000.json
├── config.yaml              # 全局配置
├── pyproject.toml
└── .gitignore
```

## 题目定义格式（problem.yaml）

```yaml
name: "sorting-algo"
difficulty: medium          # easy / medium / hard
category: algorithm         # algorithm / web / system / tool-use / ...
tags: [sorting, algorithm, performance]

# 任务描述（发给模型/Agent 的 prompt）
prompt: |
  实现一个 merge_sort 函数，接受一个整数列表，
  返回排序后的列表。要求时间复杂度 O(n log n)。

# 评分配置
scoring:
  dimensions:
    - name: correctness
      weight: 0.5
    - name: code_quality
      weight: 0.3
    - name: performance
      weight: 0.2

# 目标文件名（模型需要生成的文件）
target_file: "solution.py"

# 超时（秒）
timeout: 30
```

## 评分系统

### 自定义评分（scoring.py）

每个题目目录下可选放 `scoring.py`，包含与 `problem.yaml` 中 `scoring.dimensions` 对应的评分函数：

```python
def score_correctness(generated_code: str, work_dir: str) -> float:
    """运行测试，返回 0.0~1.0 的通过率"""

def score_code_quality(generated_code: str, work_dir: str) -> float:
    """静态分析：风格、安全、可读性，返回 0.0~1.0"""

def score_performance(generated_code: str, work_dir: str) -> float:
    """运行效率：时间+内存，返回 0.0~1.0"""
```

### 默认评分（无自定义 scoring.py 时）

| 维度 | 默认行为 |
|------|---------|
| correctness | pytest 通过率（必须有 tests/） |
| code_quality | 0.8（固定值） |
| performance | 0.7（固定值） |

### 分数计算

```
题目总分 = Σ(维度分数 × 权重)
评测总分 = 所有题目总分的均值
```

## 评测目标：Model × Agent 组合

评测粒度是 Model + Agent 的组合，而非单独的 model 或 agent。

```yaml
# config.yaml
providers:
  - name: openai
    base_url: "https://api.openai.com/v1"
    api_key: "sk-xxx..."

  - name: anthropic
    base_url: "https://api.anthropic.com"
    api_key: "sk-ant-xxx..."

  - name: local-ollama
    base_url: "http://localhost:11434/v1"
    api_key: "not-needed"

models:
  - name: "gpt-4o"
    provider: openai
    model: "gpt-4o"

  - name: "claude-sonnet-4"
    provider: anthropic
    model: "claude-sonnet-4-20250514"

agents:
  - name: "raw-api"              # 裸 API 调用，无 Agent 包装
    type: raw
    description: "单轮直接调用模型"

  - name: "claude-code"
    type: agent
    description: "Claude Code CLI"

  - name: "codex"
    type: agent
    description: "OpenAI Codex CLI"

# 实际评测组合（手动指定或 --all-combos 笛卡尔积）
combos:
  - model: "gpt-4o"
    agent: "raw-api"
  - model: "gpt-4o"
    agent: "codex"
  - model: "claude-sonnet-4"
    agent: "raw-api"
  - model: "claude-sonnet-4"
    agent: "claude-code"
```

通过对比同一 model + 不同 agent，可以隔离出 Agent 框架的价值。`raw-api` 作为纯模型基准。

## Executor 执行流程

1. Runner 遍历 `combos × problems` 的笛卡尔积
2. 对每个组合：
   - 创建独立临时工作目录，复制 `tests/` 进去
   - 把 `problem.yaml` 中的 `prompt` 发给目标
   - **raw-api 模式**：单轮对话，直接返回代码，写入 `target_file`
   - **agent 模式**：多轮对话，Agent 可执行文件操作、运行命令，完成后读取 `target_file`
3. 超时后强制终止，超时视为该题 0 分
4. 收集结果进入评分阶段

## 结果存储

每次评测生成带时间戳的 JSON 文件：`results/2026-05-09T120000.json`

```json
{
  "timestamp": "2026-05-09T12:00:00",
  "combos": [
    {
      "model": "claude-sonnet-4",
      "agent": "claude-code",
      "problems": [
        {
          "name": "sorting-algo",
          "scores": {
            "correctness": 1.0,
            "code_quality": 0.9,
            "performance": 0.85
          },
          "total": 0.92,
          "status": "pass",
          "duration_seconds": 3.2
        }
      ],
      "overall": 0.93
    }
  ]
}
```

## CLI 命令

```bash
# 运行全部评测
uv run orangebench run

# 运行指定题目/组合
uv run orangebench run --problems sorting-algo,binary-tree --models gpt-4o

# 查看历史排名
uv run orangebench ranking

# 按条件筛选
uv run orangebench ranking --category algorithm --difficulty hard

# 查看某次详细结果
uv run orangebench show --model gpt-4o --agent codex --problem sorting-algo
```

## 终端输出示例

```
╔═══════════════════════════════════════════════════════════════╗
║  OrangeBenchmark — 2026-05-09 12:00                          ║
╠═══════════════════════════════════════════════════════════════╣
║ #   Model             Agent           Overall  C     Q    P  ║
╠═══════════════════════════════════════════════════════════════╣
║ 1   claude-sonnet-4   claude-code     0.93     1.0  0.9  0.9 ║
║ 2   gpt-4o            codex           0.88     0.9  0.9  0.8 ║
║ 3   claude-sonnet-4   raw-api         0.82     0.8  0.8  0.8 ║
║ 4   gpt-4o            raw-api         0.78     0.7  0.8  0.8 ║
║ 5   deepseek-v3       raw-api         0.75     0.7  0.8  0.7 ║
╚═══════════════════════════════════════════════════════════════╝
```

## 技术栈

- Python >= 3.11，通过 uv 管理虚拟环境
- typer — CLI 框架
- rich — 终端表格输出
- pyyaml — 读取配置和题目
- openai — 统一 API 调用（兼容 OpenAI-compatible providers）
- anthropic — Anthropic API（Agent 模式 tool_use）
- pytest — 测试运行
- ruff — 代码质量静态检查

## .gitignore

`config.yaml` 和 `results/` 应加入 `.gitignore`，避免泄露 API Key 和产生不必要的 diff。
