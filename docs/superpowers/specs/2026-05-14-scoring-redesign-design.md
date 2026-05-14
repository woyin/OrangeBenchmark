# 评分机制重设计

## 概览

重新设计 OrangeBenchmark 评分机制，解决当前分数过于集中的问题（多数 Agent 总分在 0.82–1.0，差距仅为 0.01 级别）。核心思路：非线性计分 + 罚分制 + 可选维度 + 总量拉伸，让不同能力水平的 Agent 得分产生 3–5 倍于当前的分辨率。

---

## 当前问题诊断

| 问题 | 表现 | 根源 |
|------|------|------|
| Correctness 无区分度 | 通过 Agent 均为 1.0，失败均为 0.0 | `pass_ratio²` 指数过弱 + 测试全通过即满分 |
| Code Quality 范围压缩 | 大多数在 0.80–0.96，仅 0.16 区间 | 加权平均让各子项互相平均，不易拉开 |
| Performance 形同虚设 | 大量从默认值 0.5–0.7 | 未正确配置 fast/slow + Python 默认 0.7 |
| 总分聚集 | 0.82–0.99 区间密集分布 | 各维度效应叠加后被加权求和稀释 |

---

## 改动总览

### 1. Correctness: 非线性指数拉伸

$$
\text{score} = \text{pass\_ratio}^K
$$

- 默认 K=4（可配置，每个问题的 scoring.config 可覆盖）
- 80% 正确 = 0.41、90% = 0.66、95% = 0.81、100% = 1.0
- K 值存储在 yaml 配置 `scoring.correctness_exponent` 中
- 未运行测试的问题自动得 0

| 正确率 | 旧分 (K=2) | 新分 (K=4) |
|--------|-----------|-----------|
| 100% | 1.000 | 1.000 |
| 95% | 0.902 | 0.815 |
| 90% | 0.810 | 0.656 |
| 80% | 0.640 | 0.410 |
| 50% | 0.250 | 0.062 |

### 2. Code Quality: 罚分制

废除现有加权平均，改为从 1.0 起步、发现问题扣分。

```
score = max(0.0, 1.0 - deductions)
```

| 检查项 | 扣分规则 | 上限 |
|--------|---------|------|
| Lint 违规（每条） | -0.03 | 最多 -0.30 |
| 缺类型标注（每个公开参数/返回值） | -0.02 | 最多 -0.25 |
| 缺 Docstring（每个公开函数/类） | -0.03 | 最多 -0.20 |
| 圈复杂度超标（ratio > 0.3） | -0.05 每额外 0.1 | 最多 -0.20 |
| 缺 Error Handling（每个公开函数无 try/raise） | -0.02 | 最多 -0.20 |
| 所有扣减叠加 | **扣减和按 0.80 缩放**，避免极端扣到 0 | 下限 0.10 |

**扣减和按 0.80 缩放**的含义：$display = max(0.10, 1.0 - deductions \times 0.80)$，避免单一维度把分数打到 0，保留区分空间。

| 场景 | 旧分 | 新分 |
|------|------|------|
| 零问题 | ~0.96 | ~0.98–1.0 |
| 少量 lint + 缺 hint | ~0.88 | ~0.80–0.88 |
| 较多 lint + 缺文档 | ~0.80 | ~0.60–0.75 |
| 质量差 | ~0.55 | ~0.30–0.50 |

### 3. Performance: 指数衰减

$$
\text{score} = (1 - t)^2, \quad t = \frac{\text{elapsed} - \text{fast}}{\text{slow} - \text{fast}}
$$

- 到达 fast 阈值即满分 1.0，超过 slow 即 0.0
- 中间区间从线性衰减改为平方衰减，拉开中间段差距
- fast/slow 必须在每个问题的 yaml 配置中显式声明（`scoring.performance.fast_seconds` / `slow_seconds`）
- 未配置 fast/slow 的问题：performance 维度**临时失效**，权重按比例重新分配给其他维度

| 耗时 (fast=1s, slow=10s) | 旧分（线性） | 新分（平方衰减） |
|-------------------------|------------|----------------|
| 1s                      | 1.000      | 1.000          |
| 3s                      | 0.844      | 0.716          |
| 5s                      | 0.689      | 0.494          |
| 7s                      | 0.422      | 0.284          |
| 9s                      | 0.156      | 0.062          |

### 4. 新增可选维度

使用问题级别的 `scoring.dimensions` 声明启用哪些维度。以下维度**仅当被声明时才启用**：

| 维度 | 启用场景 | 计分方式 | 权重建议范围 |
|------|---------|---------|-------------|
| **security** | I/O 类：Web API、文件操作、数据库、命令执行 | 静态扫描 + 代码扫描：发现安全模式（subprocess shell=True、SQL 拼接、路径穿越等），每项 -0.25 | 0.15–0.20 |
| **resource_efficiency** | 性能敏感：大数据处理、循环/递归 | 检测未关闭资源、不必要对象分配、低效循环。1.0起扣，每项 -0.10 | 0.10–0.15 |
| **robustness** | 边界复杂：空/异常/边界输入验证 | 代码中处理了空输入 +0.25、异常类型 +0.25、边界值 +0.25、输入校验 +0.25 | 0.10–0.15 |

每个维度的默认权重在 yaml 中声明。

**示例配置**——简单问题：

```yaml
scoring:
  dimensions:
    - {name: correctness, weight: 0.45}
    - {name: code_quality, weight: 0.35}
    - {name: performance, weight: 0.20}
  performance:
    fast_seconds: 1.0
    slow_seconds: 10.0
  correctness_exponent: 4
```

**示例配置**——Web API 问题：

```yaml
scoring:
  dimensions:
    - {name: correctness, weight: 0.30}
    - {name: code_quality, weight: 0.25}
    - {name: performance, weight: 0.15}
    - {name: security, weight: 0.20}
    - {name: robustness, weight: 0.10}
  performance:
    fast_seconds: 0.5
    slow_seconds: 5.0
  correctness_exponent: 4
```

### 5. 总分聚合

**加权求和逻辑不变**——保持透明、可追溯。

$$
\text{raw\_total} = \sum_{\text{dim}} \text{dim\_score} \times \text{dim\_weight}
$$

**新增展示层拉伸**（仅影响显示排名、不影响 JSON 存储的 raw_total）：

$$
\text{display\_total} = \text{raw\_total}^{0.85}
$$

**生效范围**：未配置 performance 时，其权重按比例重分配到其他维度。计算公式：

```
effective_weights = {}
total_active_weight = sum(w for dims where have_score)
for each active dim: effective_weight = dim.weight / total_active_weight
```

**Overall（跨问题聚合）**：去掉最低 10% 分数（outlier 过滤），剩余取平均。

```
sorted_scores = sorted(all_problem_totals)
trim_count = max(1, len(sorted_scores) // 10)
trimmed = sorted_scores[trim_count:]
overall = sum(trimmed) / len(trimmed)
```

### 6. 展示改进

排名表新增列和颜色：

| 展示项 | 格式变化 |
|--------|---------|
| 总分 | 3 位小数（如 `0.847`）代替 2 位 |
| Grade 等级 | ≥0.95=A+（绿）、≥0.85=A（蓝）、≥0.70=B（黄）、≥0.50=C（橙）、<0.50=D（红） |
| 不可用维度 | 显示 `—` 代替隐式 0.7 |

---

## 分数预估分布对比

| Agent 水平 | 旧分布 | 新分布 |
|-----------|--------|--------|
| 顶尖（全对 + 优质代码） | 0.96–1.00 | 0.90–1.00 |
| 良好（大部分对 + 少量质量缺陷） | 0.88–0.95 | 0.65–0.88 |
| 一般（部分正确 + 中等质量） | 0.70–0.87 | 0.35–0.62 |
| 差（大面积失败） | 0.00–0.50 | 0.00–0.30 |

---

## 改动的源文件清单

| 文件 | 改动内容 |
|------|---------|
| `runner/scorer.py` | `_default_correctness`: 改用指数 K=4；`_default_code_quality`: 改为罚分制；`_continuous_performance_score`: 平方衰减；新增 `_security_score`, `_robustness_score`, `_resource_efficiency_score`；`score_problem`: 处理可选维度的权重重分配 |
| `runner/reporter.py` | 总分显示 3 位小数；新增 Grade 颜色列；不可用维度显示 `—` |
| `runner/main.py` | Overall 聚合改为 trim-mean |
| 各 `problem.yaml` | 按需添加 `performance.fast_seconds/slow_seconds`、`correctness_exponent`、可选维度声明 |

---

## 不做的事

- 不改 executor.py（工作目录准备逻辑不变）
- 不改结果 JSON 存储格式（保持向后兼容，新增字段可选添加）
- 不改 CLI 命令结构（不新增/删除命令）
- 不改问题的 prompt 和测试用例本身
