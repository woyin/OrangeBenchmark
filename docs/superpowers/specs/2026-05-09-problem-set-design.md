# OrangeBenchmark — 题目集设计

## 概述

OrangeBenchmark 题目集按 **能力维度 × 难度层次** 组织，初期 9 道题，覆盖 6 个维度。每道题包含边界用例以测试模型/Agent 的健壮性。Python 为主，包含一道 Rust/Wasm 多语言题目。

## 能力维度

| 维度 | 说明 |
|------|------|
| algorithm | 算法与数据结构 |
| string | 字符串处理与解析 |
| api | API / Web 接口开发 |
| data | 数据处理与文件 I/O |
| system | 系统与并发 |
| multi-lang | 多语言能力 |

## 难度层次

- **Easy**：单一职责，函数级别，重点考察正确性
- **Medium**：类级别或模块级别，涉及设计决策和边界处理
- **Hard**：系统级别，涉及状态管理、并发或多语言

---

## Easy 层

### E1. two-sum（algorithm, Python）

**目录**：`problems/two-sum/`

**题目描述**：
实现 `two_sum(nums: list[int], target: int) -> list[int]`，在数组中找到两个数使其和等于 target，返回它们的下标。假设每组输入恰好有一个解，同一元素不能使用两次。

**target_file**：`solution.py`

**测试用例**：
- 基本用例：`[2, 7, 11, 15], target=9` → `[0, 1]`
- 重复元素：`[3, 3], target=6` → `[0, 1]`
- 负数：`[-1, -2, -3, -4, -5], target=-8` → `[2, 4]`
- 无解情况：返回空列表 `[]`
- 空列表：返回 `[]`
- 单元素：返回 `[]`
- 超大数组：10^5 个元素
- 和为 0：包含正负数对

**评分维度**：
- correctness（weight: 0.6）— pytest 通过率
- code_quality（weight: 0.4）— ruff 检查

---

### E2. csv-stats（data, Python）

**目录**：`problems/csv-stats/`

**题目描述**：
实现 `analyze_csv(filepath: str) -> dict`，读取 CSV 文件，返回每列的统计信息。返回格式：`{列名: {"mean": float, "max": float, "min": float, "null_count": int}}`。仅对数值列计算统计，非数值列跳过并在返回中标记 `{"type": "non-numeric"}`。

**target_file**：`solution.py`

**测试用例**：
- 正常多列 CSV
- 空文件 → 返回空 dict
- 只有表头无数据行 → 每列 mean/max/min 为 None，null_count=0
- 列含非数值 → 标记 non-numeric
- 行数不一致（缺失列）→ 视为 null
- 混合数值和文本列
- 单列 CSV

**评分维度**：
- correctness（weight: 0.6）— pytest 通过率
- code_quality（weight: 0.4）— ruff 检查

---

### E3. url-parser（string, Python）

**目录**：`problems/url-parser/`

**题目描述**：
实现 `parse_url(url: str) -> dict`，不使用标准库 urllib/urllib3，手工解析 URL 字符串。返回 dict 包含：`scheme`、`host`、`port`（默认值 80/443）、`path`、`query_params`（dict）、`fragment`。不要求处理 userinfo（user:pass@host）。

**target_file**：`solution.py`

**测试用例**：
- 完整 URL：`https://example.com:8080/path?key=value&foo=bar#section`
- 无 scheme → 返回 scheme=None
- 默认端口：`http://host/path` → port=80，`https://host/path` → port=443
- 无 path：`https://example.com` → path=""
- 空 query → query_params={}
- query 含编码字符：`?q=%E4%B8%AD%E6%96%87`
- 空 URL → 返回各字段均为 None 或空
- 只有 path：`/foo/bar` → scheme=None, host=None, path="/foo/bar"
- fragment 为空：`https://host/path#` → fragment=""

**评分维度**：
- correctness（weight: 0.6）— pytest 通过率
- code_quality（weight: 0.4）— ruff 检查

---

## Medium 层

### M1. lru-cache（algorithm, Python）

**目录**：`problems/lru-cache/`

**题目描述**：
实现 `LRUCache` 类，支持 `get(key)` 和 `put(key, value)` 操作，容量满时淘汰最近最少使用的元素。要求 `get` 和 `put` 均为 O(1) 时间复杂度。

接口：
```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key: int) -> int:      # 不存在返回 -1
    def put(self, key: int, value: int) -> None: ...
```

**target_file**：`solution.py`

**测试用例**：
- 基本操作：put 3 个（容量 2）后第一个被淘汰
- get 更新访问顺序
- 容量为 1
- 容量为 0 → 所有 get 返回 -1，put 无效
- put 已存在的 key → 更新值并刷新顺序
- 连续 get 同一个 key
- 大量操作：10^4 次 put/get 混合

**评分维度**：
- correctness（weight: 0.4）— pytest 通过率
- code_quality（weight: 0.3）— ruff 检查
- performance（weight: 0.3）— 自定义：验证 O(1) 特性（10^4 操作在合理时间内完成）

---

### M2. rest-api（api, Python）

**目录**：`problems/rest-api/`

**题目描述**：
使用 Python 标准库 `http.server` 实现一个简易 REST API 服务，支持对内存中 `tasks` 列表的 CRUD 操作：

- `GET /tasks` — 返回所有任务，支持 `?status=done` 筛选
- `POST /tasks` — 创建任务，body: `{"title": "xxx", "status": "todo"}`
- `PUT /tasks/{id}` — 更新任务
- `DELETE /tasks/{id}` — 删除任务

每个 task 包含：`id`（自增整数）、`title`、`status`（todo/done）、`created_at`（ISO 格式字符串）。

实现 `create_app()` 函数返回可用的 HTTPServer 实例。

**target_file**：`solution.py`

**测试用例**：
- GET 空列表 → `[]`
- POST 创建 → 返回带 id 的 task
- PUT 更新存在的 task → 200 + 更新后的 task
- PUT 更新不存在的 id → 404
- DELETE 存在的 task → 204
- DELETE 不存在的 id → 404
- GET + status 筛选
- POST malformed JSON → 400
- 重复 ID 不允许（自增保证）
- 多次 GET 不影响数据

**评分维度**：
- correctness（weight: 0.6）— pytest 通过率
- code_quality（weight: 0.4）— ruff 检查

---

### M3. log-analyzer（data, Python）

**目录**：`problems/log-analyzer/`

**题目描述**：
实现 `analyze_log(filepath: str) -> dict`，解析 nginx combined 格式的 access.log，返回：

```python
{
    "total_requests": int,
    "methods": {"GET": int, "POST": int, ...},
    "status_codes": {"200": int, "404": int, ...},
    "top_paths": [("/index.html", count), ...],   # Top 10
    "avg_response_time": float,                     # 秒
}
```

nginx combined 格式示例：
```
192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326 "http://example.com" "Mozilla/5.0" 0.023
```

最后一列为响应时间（秒），部分日志行可能缺失此字段。

**target_file**：`solution.py`

**测试用例**：
- 正常日志文件（多种 method、status code 混合）
- 空文件 → total_requests=0
- 格式不一致的行 → 跳过，不计入统计
- 缺失响应时间 → avg_response_time 仅统计有值的行
- 超大文件（流式处理，不一次性读入内存）— 用自定义 scoring 验证内存使用
- 单行日志
- 所有请求相同路径

**评分维度**：
- correctness（weight: 0.4）— pytest 通过率
- code_quality（weight: 0.3）— ruff 检查
- performance（weight: 0.3）— 自定义：大文件流式处理验证

---

## Hard 层

### H1. text-editor（algorithm, Python）

**目录**：`problems/text-editor/`

**题目描述**：
实现行编辑器类 `TextEditor`：

```python
class TextEditor:
    def __init__(self): ...
    def insert(self, line: int, col: int, text: str) -> None: ...
    def delete(self, line: int, col: int, length: int) -> None: ...
    def replace(self, line: int, col: int, length: int, new_text: str) -> None: ...
    def get_text(self) -> str: ...           # 返回完整文本
    def undo(self) -> None: ...              # 撤销上一步操作
    def redo(self) -> None: ...              # 重做
```

undo/redo 栈支持嵌套多步操作。undo 到最初始状态后再 undo 无效果。新操作会清空 redo 栈。

**target_file**：`solution.py`

**测试用例**：
- 基本插入 → 单行 → 多行（含换行符）
- 删除跨行
- replace 覆盖
- undo 恢复插入/删除/replace
- redo 重复撤销
- 连续 undo 到初始状态
- undo 后新 insert → redo 栈清空
- 行列越界 → 抛出 IndexError
- 大文档：10^4 行，频繁 insert/undo
- 空文档 undo → 无效果

**评分维度**：
- correctness（weight: 0.4）— pytest 通过率
- code_quality（weight: 0.3）— ruff 检查
- performance（weight: 0.3）— 自定义：10^4 行文档频繁操作在合理时间内完成

---

### H2. task-scheduler（system, Python）

**目录**：`problems/task-scheduler/`

**题目描述**：
实现 `TaskScheduler` 类：

```python
class TaskScheduler:
    def __init__(self, max_workers: int = 4): ...
    def add_task(self, name: str, fn: Callable, dependencies: list[str] = []) -> None: ...
    def run_all(self) -> dict[str, Any]: ...   # 返回 {task_name: result}
```

任务按拓扑序执行，依赖的任务先完成。支持 `max_workers` 并发。检测循环依赖并抛出 `ValueError("Cycle detected")`。

**target_file**：`solution.py`

**测试用例**：
- 无依赖单任务
- 全链式依赖：A → B → C → D（严格串行）
- 菱形依赖：A → B, A → C, B → D, C → D
- 循环依赖：A → B → C → A → 抛 ValueError
- 某任务抛异常 → 其他任务结果仍收集，失败任务标记错误
- max_workers=1 退化为串行
- 验证并发执行：无依赖的多个任务实际并行（通过执行时间验证）
- 空任务列表 → 返回空 dict
- 任务返回 None → 正常收集

**评分维度**：
- correctness（weight: 0.4）— pytest 通过率
- code_quality（weight: 0.3）— ruff 检查
- performance（weight: 0.3）— 自定义：验证并发效率

---

### H3. wasm-calculator（multi-lang, Rust → Wasm）

**目录**：`problems/wasm-calculator/`

**题目描述**：
用 Rust 实现一个计算器库，编译为 WebAssembly（wasm32-unknown-unknown）。暴露以下函数：

- `add(a: f64, b: f64) -> f64`
- `sub(a: f64, b: f64) -> f64`
- `mul(a: f64, b: f64) -> f64`
- `div(a: f64, b: f64) -> f64`
- `eval_expression(expr: &str) -> f64` — 解析并计算数学表达式字符串，支持 +、-、*、/、括号、浮点数

提供 `src/lib.rs`、`Cargo.toml`、`tests/test_calculator.rs`（Rust 单元测试）、`index.js`（Node.js 胶水代码用于 Wasm 调用测试）。

**target_file**：`src/lib.rs`

**测试用例**（Rust 单元测试）：
- `add(2.0, 3.0)` → `5.0`
- `sub(5.0, 3.0)` → `2.0`
- `mul(2.0, 3.0)` → `6.0`
- `div(6.0, 3.0)` → `2.0`
- `div(1.0, 0.0)` → `f64::INFINITY`
- `eval_expression("1 + 2 * 3")` → `7.0`
- `eval_expression("(1 + 2) * 3")` → `9.0`
- `eval_expression("  3.5  +  2.5  ")` → `6.0`（含空格）
- `eval_expression("((1 + 2))")` → `3.0`（嵌套括号）
- `eval_expression("")` → panic 或返回 NaN
- `eval_expression("1 / 0")` → `f64::INFINITY`
- `eval_expression("1 + + 2")` → panic 或返回 NaN（非法表达式）
- 大数：`eval_expression("999999 * 999999")` → 验证精度
- 负数：`eval_expression("-5 + 3")` → `-2.0`

**评分维度**：
- correctness（weight: 0.5）— cargo test 通过率
- code_quality（weight: 0.3）— cargo clippy 检查
- performance（weight: 0.2）— 自定义：eval_expression 大量调用效率

**注意事项**：
- Runner 需要支持 Rust 题目的特殊处理：`cargo test` 替代 `pytest`，`cargo clippy` 替代 `ruff`
- 需要安装 `wasm-pack` 或 `wasm-bindgen` 进行 Wasm 编译
- 此题的 scoring.py 需要调用 `cargo` 命令而非 Python 工具链

---

## 题目汇总

| # | 名称 | 难度 | 维度 | 语言 | 评分维度 |
|---|------|------|------|------|---------|
| E1 | two-sum | easy | algorithm | Python | correctness, code_quality |
| E2 | csv-stats | easy | data | Python | correctness, code_quality |
| E3 | url-parser | easy | string | Python | correctness, code_quality |
| M1 | lru-cache | medium | algorithm | Python | correctness, code_quality, performance |
| M2 | rest-api | medium | api | Python | correctness, code_quality |
| M3 | log-analyzer | medium | data | Python | correctness, code_quality, performance |
| H1 | text-editor | hard | algorithm | Python | correctness, code_quality, performance |
| H2 | task-scheduler | hard | system | Python | correctness, code_quality, performance |
| H3 | wasm-calculator | hard | multi-lang | Rust/Wasm | correctness, code_quality, performance |

---

## 新增题目

### E4. java-reverse-string（string, Java）

**目录**：`problems/java-reverse-string/`

**题目描述**：
在 `src/main/java/StringReverser.java` 中实现 `StringReverser` 类，提供静态方法 `reverse(String s) -> String`。要求逐字符反转输入字符串，输入为 `null` 时返回空字符串。

**target_file**：`src/main/java/StringReverser.java`

**测试用例**：
- 基本字符串：`"hello"` → `"olleh"`
- 空字符串：`""` → `""`
- `null` 输入 → `""`
- 单字符：`"a"` → `"a"`
- Unicode：`"你好世界"` → `"界世好你"`
- 回文：`"abcba"` → `"abcba"`

**评分维度**：
- correctness（weight: 0.6）— `mvn test` 通过率
- code_quality（weight: 0.4）— `mvn compile` 编译通过

**注意事项**：
- 使用 Maven 构建，需提供 `pom.xml`
- Java 版本要求 17
- Runner 需支持 Maven 项目自动检测（通过 `pom.xml`）

---

### E5. dotnet-fizz-buzz（algorithm, .NET / C#）

**目录**：`problems/dotnet-fizz-buzz/`

**题目描述**：
在 `FizzBuzz.cs` 中实现 `FizzBuzz` 类，提供静态方法 `Generate(int n) -> List<string>`。返回 1 到 n 的字符串列表：3 的倍数替换为 "Fizz"，5 的倍数替换为 "Buzz"，同时是 3 和 5 的倍数替换为 "FizzBuzz"，其余使用数字本身。`n <= 0` 时返回空列表。

**target_file**：`FizzBuzz.cs`

**测试用例**：
- `Generate(15)` 返回完整 FizzBuzz 序列
- `Generate(0)` → 空列表
- `Generate(-5)` → 空列表
- `Generate(3)` 仅到 "Fizz"
- `Generate(5)` 仅到 "Buzz"
- `Generate(15)[14]` 为 "FizzBuzz"

**评分维度**：
- correctness（weight: 0.6）— `dotnet test` 通过率
- code_quality（weight: 0.4）— `dotnet build` 编译通过及警告数量

**注意事项**：
- 使用 .NET 8 SDK，需提供 `.csproj` 文件
- 测试框架使用 xUnit
- Runner 需支持 .NET 项目自动检测（通过 `.csproj`）

---

## 更新后题目汇总

| # | 名称 | 难度 | 维度 | 语言 | 评分维度 |
|---|------|------|------|------|---------|
| E1 | two-sum | easy | algorithm | Python | correctness, code_quality |
| E2 | csv-stats | easy | data | Python | correctness, code_quality |
| E3 | url-parser | easy | string | Python | correctness, code_quality |
| E4 | java-reverse-string | easy | string | Java | correctness, code_quality |
| E5 | dotnet-fizz-buzz | easy | algorithm | .NET/C# | correctness, code_quality |
| M1 | lru-cache | medium | algorithm | Python | correctness, code_quality, performance |
| M2 | rest-api | medium | api | Python | correctness, code_quality |
| M3 | log-analyzer | medium | data | Python | correctness, code_quality, performance |
| H1 | text-editor | hard | algorithm | Python | correctness, code_quality, performance |
| H2 | task-scheduler | hard | system | Python | correctness, code_quality, performance |
| H3 | wasm-calculator | hard | multi-lang | Rust/Wasm | correctness, code_quality, performance |
