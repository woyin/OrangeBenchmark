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
├── problems/                # 评测题目（56 道，6 种语言）
│   ├── _template/           # 新题目脚手架
│   ├── _examples/           # 题目结构参考示例
│   ├── two-sum/             # Python 题目
│   ├── java-reverse-string/ # Java 题目
│   ├── react-counter-app/   # React 题目
│   ├── bash-file-renamer/   # Bash 题目
│   ├── dotnet-fizz-buzz/    # .NET/C# 题目
│   └── wasm-calculator/     # Rust/Wasm 题目
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

## 题目列表（56 道，6 种语言）

### Python（16 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 1 | two-sum | easy | algorithm |
| 2 | csv-stats | easy | data |
| 3 | url-parser | easy | string |
| 4 | lru-cache | medium | algorithm |
| 5 | rest-api | medium | api |
| 6 | log-analyzer | medium | data |
| 7 | text-editor | hard | algorithm |
| 8 | task-scheduler | hard | system |
| 9 | python-runway-monitor | medium | aviation |
| 10 | regex-engine | hard | algorithm |
| 11 | mini-db | hard | system |
| 12 | python-jwt-decoder | medium | security |
| 13 | python-metar-parser | medium | aviation |
| 14 | python-route-planner | hard | aviation |
| 15 | python-word-ladder | hard | algorithm |
| 16 | python-markdown-parser | medium | parsing |

### Java（17 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 17 | java-reverse-string | easy | string |
| 18 | java-flight-plan-parser | medium | aviation |
| 19 | java-conflict-detector | hard | aviation |
| 20 | java-expression-evaluator | medium | algorithm |
| 21 | java-concurrent-queue | hard | concurrency |
| 22 | java-graph-shortest-path | medium | algorithm |
| 23 | java-http-server | hard | system |
| 24 | java-fizz-buzz | easy | algorithm |
| 25 | java-palindrome-checker | easy | string |
| 26 | java-json-parser | medium | parsing |
| 27 | java-sorting-library | medium | algorithm |
| 28 | java-thread-pool | hard | concurrency |
| 29 | java-matrix-ops | medium | math |
| 30 | java-aircraft-scheduler | hard | aviation |
| 31 | java-password-validator | easy | security |
| 32 | java-morse-code | easy | encoding |
| 33 | java-tcp-chat-server | hard | system |

### React（7 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 34 | react-counter-app | easy | frontend |
| 35 | react-todo-list | easy | frontend |
| 36 | react-color-picker | medium | frontend |
| 37 | react-data-table | medium | frontend |
| 38 | react-form-validator | medium | frontend |
| 39 | react-drag-kanban | hard | frontend |
| 40 | react-infinite-scroll | hard | frontend |

### Bash（5 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 41 | bash-file-renamer | easy | system |
| 42 | bash-log-summary | easy | data |
| 43 | bash-csv-merger | medium | data |
| 44 | bash-process-monitor | medium | system |
| 45 | bash-backup-rotation | hard | system |

### .NET / C#（6 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 46 | dotnet-fizz-buzz | easy | algorithm |
| 47 | dotnet-adsb-decoder | hard | aviation |
| 48 | dotnet-crew-scheduler | hard | aviation |
| 49 | dotnet-json-transform | medium | data |
| 50 | dotnet-rate-limiter | hard | concurrency |
| 51 | dotnet-text-search | medium | algorithm |

### Rust（1 道）

| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 52 | wasm-calculator | hard | multi-lang |

## 评分维度

| 维度 | 说明 | 默认行为 |
|------|------|---------|
| correctness | 代码正确性 | 运行测试，非线性通过率 |
| code_quality | 代码质量 | Python: lint + 类型注解 + 复杂度 + docstring; Java: mvn compile; .NET: dotnet build 警告数 |
| performance | 运行性能 | 连续评分（部分题目有自定义基准测试） |

## 添加新题目

1. 复制 `problems/_template/` 为新目录
2. 编辑 `problem.yaml`：设置 name、difficulty、category、prompt、target_file、copy_paths
3. 编写测试用例
4. 可选：添加 `scoring.py` 自定义评分逻辑

## 依赖

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) 包管理器
- 可选：`mvn`（Java 题目）、`dotnet`（.NET 题目）、`cargo`（Rust 题目）、`npm`（React 题目）、`bash`（Bash 题目）

## License

MIT
