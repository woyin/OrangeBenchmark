# OrangeBenchmark

一个面向 LLM 和 Coding Agent 的代码能力评测框架。

给定一组编码题目，让 Coding Agent 解题，然后自动评分并记录历史结果。

## Quick Start

```bash
# 1. 克隆仓库
git clone https://github.com/woyin/OrangeBenchmark.git
cd OrangeBenchmark

# 2. 安装依赖
uv sync

# 3. 让 Coding Agent 根据 AGENT_INSTRUCTIONS.md 完成所有题目
#    （告诉你的 coding agent: "请阅读 AGENT_INSTRUCTIONS.md 并完成其中的所有题目"）

# 4. 评分并查看结果
uv run orangebench score

# 5. 查看历史排名
uv run orangebench ranking
```

## 项目结构

```
OrangeBenchmark/
├── AGENT_INSTRUCTIONS.md    # 给 Coding Agent 的任务说明
├── problems/                # 评测题目
│   ├── two-sum/             # easy, algorithm, Python
│   ├── csv-stats/           # easy, data, Python
│   ├── url-parser/          # easy, string, Python
│   ├── lru-cache/           # medium, algorithm, Python
│   ├── rest-api/            # medium, api, Python
│   ├── log-analyzer/        # medium, data, Python
│   ├── text-editor/         # hard, algorithm, Python
│   ├── task-scheduler/      # hard, system, Python
│   ├── wasm-calculator/     # hard, multi-lang, Rust/Wasm
│   ├── java-reverse-string/ # easy, string, Java
│   └── dotnet-fizz-buzz/    # easy, algorithm, .NET/C#
├── runner/                  # 评分引擎
├── results/                 # 历史评测结果 (JSON)
└── tests/                   # 测试
```

每个题目目录包含：
- `problem.yaml` — 题目描述、prompt、评分配置
- `solution.py`（或语言对应的目标文件）— Agent 需要覆盖此文件
- `tests/` — 验证正确性的测试用例
- `scoring.py`（可选）— 自定义评分逻辑

## 使用方式

### 方式一：让 Coding Agent 自动完成

将 `AGENT_INSTRUCTIONS.md` 的内容提供给你的 Coding Agent（如 Claude Code、Codex CLI 等），让它按说明完成所有题目，然后运行评分：

```bash
uv run orangebench score
```

### 方式二：手动指定题目

```bash
# 只评测部分题目
uv run orangebench score --problems two-sum,lru-cache

# 给本次评测加标签
uv run orangebench score --label "gpt-4o"
```

### 查看结果

```bash
# 查看最新一次评测的排名
uv run orangebench ranking

# 按难度/分类筛选
uv run orangebench ranking --difficulty hard
uv run orangebench ranking --category algorithm

# 查看某个评测的详细分数
uv run orangebench show --model "gpt-4o"
```

## 题目列表

| # | 题目 | 难度 | 类别 | 语言 | 评分维度 |
|---|------|------|------|------|---------|
| 1 | two-sum | easy | algorithm | Python | correctness, code_quality |
| 2 | csv-stats | easy | data | Python | correctness, code_quality |
| 3 | url-parser | easy | string | Python | correctness, code_quality |
| 4 | lru-cache | medium | algorithm | Python | correctness, code_quality, performance |
| 5 | rest-api | medium | api | Python | correctness, code_quality |
| 6 | log-analyzer | medium | data | Python | correctness, code_quality, performance |
| 7 | text-editor | hard | algorithm | Python | correctness, code_quality, performance |
| 8 | task-scheduler | hard | system | Python | correctness, code_quality, performance |
| 9 | wasm-calculator | hard | multi-lang | Rust | correctness, code_quality, performance |
| 10 | java-reverse-string | easy | string | Java | correctness, code_quality |
| 11 | dotnet-fizz-buzz | easy | algorithm | .NET/C# | correctness, code_quality |

## 评分维度

| 维度 | 说明 | 默认行为 |
|------|------|---------|
| correctness | 代码正确性 | 运行测试，计算通过率 |
| code_quality | 代码质量 | Python: ruff 检查; Java: mvn compile; .NET: dotnet build 警告数 |
| performance | 运行性能 | 自定义（部分题目有） |

## 添加新题目

1. 复制 `problems/_template/` 为新目录
2. 编辑 `problem.yaml`：设置 name、difficulty、category、prompt、target_file
3. 编写 `tests/test_solution.py`
4. 可选：添加 `scoring.py` 自定义评分逻辑

## 依赖

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) 包管理器
- 可选：`cargo`（Rust 题目）、`mvn`（Java 题目）、`dotnet`（.NET 题目）

## License

MIT
