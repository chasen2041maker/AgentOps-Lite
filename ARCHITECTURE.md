# GroundGuard 架构设计（可开工版本）

本文档是 [PLAN.md](PLAN.md) 的工程落地版本：定义数据模型、核心算法、目录结构、模块职责边界，以及按 Sprint 拆分的开工任务清单。目标是任何一个 Sprint 都能独立写完、独立测试，不需要等其他模块就绪。

## 当前实现状态

截至当前版本，S0-S6 的核心闭环已经落地并有测试覆盖：

- Python 包骨架、`pyproject.toml`、pytest 配置。
- `Fact`、`RequiredFact`、`OutputClaim`、`CoverageReport` 数据模型。
- `Ledger` 内存账本、TTL 过滤、JSONL 落盘/加载。
- `tool_call` 上下文管理器和显式 `record_facts`。
- 规则版输出声明抽取器、Matcher、Coverage、Policy。
- `grounded_generate()` 生成后门禁，支持返回 `GroundedResult`、策略阻断和剥离未核实声明。
- `examples/financial_report_demo/` 端到端 demo。
- `groundguard-report` CLI 基础 JSON 报告。
- 最小 OpenAI-compatible wrapper 与 LangChain-compatible callback handler。

后续路线图的剩余重点是更多框架配方、真实项目接入反馈和可视化 diff；基础适配、assertion schema 与 PR 注释示例已落地。

声明抽取边界：当前版本只抽取带单位或量级词的数值声明，例如 `823.2 亿元`、`21.5%`、`10.25 亿美元`。没有单位的裸数字不会被识别，这是为了降低误报；如果要支持裸数字，需要先有更强的上下文约束。

## 0. 设计原则（贯穿所有模块）

1. **v1 不依赖任何外部服务**：Ledger 默认纯内存 + 可选 JSONL 落盘，不要求 Postgres/Redis/向量库。保持"本地优先、零基础设施"的定位。
2. **v1 不依赖第二个 LLM 做核对**：声明抽取和核对逻辑是确定性规则（显式 fact key + 正则 + 数值容差），保证可重复、可单测、可解释。LLM 辅助抽取作为 v2 的可插拔扩展，不进入 v1 关键路径。
3. **v1 是输出放行前门禁，不承诺 token 级生成控制**：`grounded_generate` 可以包装模型调用并在返回前检查/标记/阻断，但不承诺在模型逐 token 生成时强制约束。
4. **区分 Required Fact 和 Output Claim**：`RequiredFact` 表示本轮必须覆盖的账本事实，`OutputClaim` 表示模型最终写出的待核实声明。二者不能混用，否则无法抓住"工具有数据但模型没用上"的失败。
5. **阈值制，不是零容忍**：默认策略不是"一个未核实声明就 fail"，而是可配置阈值；但 `contradicted` 和 `omitted_required` 默认一票否决。
6. **每个模块都能单独单测**：核心链路（Ledger → Output Claim Extractor → Matcher → Coverage/Policy）之间用纯数据结构传递，不互相持有对方实例，方便隔离测试。

## 1. 核心数据模型

```python
# groundguard/core/models.py
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from decimal import Decimal

@dataclass(frozen=True)
class Fact:
    """一条从工具调用里登记进账本的可核实事实。"""
    id: str                          # fact_<uuid>
    source_tool: str                 # 工具名，例如 "get_company_financials"
    source_call_id: str              # 对应的 tool_call 上下文 id，用于溯源
    key: str                         # 归一化后的事实键，例如 "net_profit_2025"
    value: Decimal | str             # v1 只支持数值/短文本事实，复杂 dict 留给 raw
    value_kind: Literal["numeric", "entity", "text"] = "numeric"
    unit: Optional[str] = None       # 例如 "CNY_100M"、"%"、"USD"
    display_value: Optional[str] = None  # 面向报告展示的值，例如 "823.2 亿元"
    raw: Any = None                  # 原始工具返回片段，供人工核查
    recorded_at: float = 0.0         # unix 时间戳
    ttl_seconds: Optional[int] = None  # 时效性事实（如实时行情）的过期时间，None 表示不过期
    confidence: float = 1.0          # 工具自报置信度，确定性工具默认 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1          # JSONL 兼容演进用

@dataclass
class RequiredFact:
    """本轮回答必须覆盖的账本事实。"""
    key: str
    reason: str = ""                 # 为什么必须覆盖，例如 "用户明确要求总结该指标"
    severity: Literal["required", "optional"] = "required"

@dataclass
class OutputClaim:
    """从生成文本里抽取出的一条待核实声明。"""
    id: str                          # claim_<uuid>
    text_span: str                   # 命中的原文片段
    claim_type: Literal["numeric", "entity", "comparison", "assertion"]
    normalized_value: Any            # 归一化后用于匹配的值
    unit: Optional[str] = None
    fact_key: Optional[str] = None    # 显式引用，例如 [fact:net_profit_2025]
    matched_fact_id: Optional[str] = None
    status: Literal["verified", "candidate_match", "unverified", "contradicted"] = "unverified"
    diff: Optional[str] = None       # 矛盾时记录差异说明，例如 "账本 823.20亿，生成 800亿"

@dataclass
class CoverageReport:
    """一次生成结果的账本核对单。"""
    session_id: str
    output_claims: list[OutputClaim] = field(default_factory=list)
    required_facts: list[RequiredFact] = field(default_factory=list)
    omitted_required_facts: list[RequiredFact] = field(default_factory=list)
    verified_count: int = 0
    candidate_match_count: int = 0
    unverified_count: int = 0
    contradicted_count: int = 0
    omitted_required_count: int = 0
    passed: bool = True              # 根据 policy 计算出的整体门禁结果
    policy_reason: str = ""          # 未通过时的原因说明
```

## 2. 模块划分与职责边界

```text
groundguard/
  __init__.py                     # 对外只导出 Ledger / tool_call / grounded_generate / Policy 等稳定 API
  core/
    __init__.py
    models.py                     # Fact / RequiredFact / OutputClaim / CoverageReport 数据结构
    ledger.py                     # Ledger：register_fact / query / all_facts / expire
    tool_call.py                  # tool_call 上下文管理器，封装一次工具调用
    output_claim_extractor.py     # 从生成文本抽取 OutputClaim（v1 规则版 + 可插拔协议）
    matcher.py                    # OutputClaim <-> Fact 匹配、容差判断、矛盾检测
    coverage.py                   # 汇总 OutputClaim + RequiredFact，生成 CoverageReport
    policy.py                     # 门禁策略：阈值配置、pass/fail 判定
  generate/
    __init__.py
    grounded_generate.py          # 包一层模型调用：生成 -> 抽取 -> 匹配 -> 按策略处理
  adapters/                       # Milestone 2 starter：OpenAI wrapper / LangChain callback
    langchain_callback.py
    openai_wrapper.py
  cli/                            # Milestone 3 starter：report CLI / assertion schema
    report.py
    ci_gate.py
  examples/
    financial_report_demo/        # 旗舰 demo：见第 5 节
  tests/
    test_ledger.py
    test_output_claim_extractor.py
    test_matcher.py
    test_coverage.py
    test_policy.py
```

**边界规则**：`core/` 下每个文件优先只依赖 `models.py`，互相之间不直接持有对方实例（例如 `matcher.py` 不 import `ledger.py`，而是接收 `list[Fact]` 作为参数）。`coverage.py` 可以组合 extractor/matcher 的输出，但不负责查询 Ledger。这样任何一个模块都能脱离其他模块单独写单测。

## 3. 核心算法

### 3.1 Ledger（`core/ledger.py`）

职责很薄，就是一个带查询能力的事实存储：

- `register_fact(fact: Fact) -> None`：登记一条事实，`recorded_at` 由 Ledger 补全。
- `query(key: str) -> list[Fact]`：按 key 精确查询（一个 key 可能有多条，例如同一指标不同时间点）。
- `all_facts(exclude_expired: bool = True) -> list[Fact]`：返回全部事实，默认过滤掉超过 `ttl_seconds` 的条目。
- `to_jsonl(path) / from_jsonl(path)`：可选落盘/加载，v1 用普通文件，不引入数据库依赖。

### 3.2 tool_call 上下文管理器（`core/tool_call.py`）

```python
with tool_call("get_company_financials", args={"ticker": "AAPL"}, ledger=ledger) as call:
    result = fetch_financials("AAPL")
    call.record_facts(
        {"net_profit_2025": (Decimal("82320000000"), "CNY")},
        raw=result,
    )
```

- 自动记录耗时、参数、原始返回（供 `raw` 字段溯源）。
- `record_facts` 是 v1 唯一登记入口，要求调用方显式给出 `key/value/unit`——**v1 不做"自动从任意 JSON 里猜哪些字段是事实"**，因为这一步做错比不做还危险（会把无关字段当成事实登记，产生虚假的"已核实"）。自动抽取作为 v2 可选扩展，且必须允许用户审核映射规则。
- `raw` 只用于溯源和调试，不参与 v1 的自动匹配；匹配只看显式登记后的 `Fact`。

### 3.3 Output Claim Extractor（`core/output_claim_extractor.py`）

v1 只处理可确定抽取的输出声明，这是能做到高精度、高确定性的子集：

1. 优先识别显式 fact key 引用：例如 `823.2 亿元 [fact:net_profit_2025]`，抽取为 `OutputClaim(fact_key="net_profit_2025")`。
2. 正则抽取候选数值片段：`(\d[\d,]*\.?\d*)\s*(亿|万|千|%|美元|元|股|倍)?`，同时保留前后 N 个字符作为 `text_span` 上下文。
3. 归一化：统一单位换算（例如"亿"统一转成基础单位的 `Decimal`），生成 `normalized_value` + `unit`。
4. 输出 `OutputClaim` 列表，`claim_type="numeric"`，此时 `status` 默认 `unverified`，交给 matcher 处理。

抽取器定义为一个协议（`Protocol`），预留非数值声明（比如"营收同比增长"这类比较型声明）未来接入 LLM 辅助抽取器的扩展点，但**协议接口在 v1 就定好，具体的 LLM 实现推到 v2**，避免 v1 引入模型依赖。

### 3.4 Matcher（`core/matcher.py`）

```python
def match(
    claims: list[OutputClaim],
    facts: list[Fact],
    tolerance: float = 0.005,
) -> list[OutputClaim]:
    ...
```

匹配优先级：

1. **显式 fact key 命中**：如果 `OutputClaim.fact_key` 存在，直接按 key 找对应 `Fact`。数值/实体一致时 → `status="verified"`；存在同 key 但值超出容差 → `status="contradicted"`。
2. **同单位数值候选匹配**：没有显式 key 时，在同单位的 Fact 里找数值最接近的一条。若相对误差在 `tolerance` 内（默认 0.5%），只标记为 `status="candidate_match"`，写入 `matched_fact_id`。candidate match 是调试线索，不默认计入 verified。
3. **矛盾判定**：只有显式 key 或上游强关联上下文存在时，才把值不一致判为 `contradicted`。单纯"账本里有另一个相近/不相近数字"不能构成矛盾。
4. **完全找不到候选** → `status="unverified"`。

`contradicted` 和 `unverified` 的区分很关键：前者是"账本里有答案但对不上"（大概率是模型算错或引用错条目），后者是"账本里压根没有这个数"（大概率是编造）。两者在下游策略里应该给不同严重度。

### 3.5 Coverage + Policy（`core/coverage.py` / `core/policy.py`）

```python
@dataclass
class Policy:
    max_unverified_ratio: float = 0.1
    max_contradicted: int = 0
    max_omitted_required: int = 0
    allow_candidate_matches: bool = False
    on_unverified: Literal["flag", "strip", "block"] = "flag"
    on_contradicted: Literal["flag", "block"] = "block"
    on_omitted_required: Literal["flag", "block"] = "block"

def evaluate(report: CoverageReport, policy: Policy) -> CoverageReport:
    ...  # 计算 passed / policy_reason
```

Coverage 负责两类核对：

1. **输出声明核对**：统计 `verified / candidate_match / unverified / contradicted`。
2. **必需事实覆盖核对**：对每个 `RequiredFact.key`，检查最终输出是否显式引用或通过策略允许的候选匹配覆盖；未覆盖则写入 `omitted_required_facts`。

默认策略：**矛盾和必需事实遗漏一票否决，未核实走比例阈值，candidate match 不默认当作 verified**。这个默认值本身要在 v1 的测试里用真实文本验证一遍，避免拍脑袋定的阈值不可用。

## 4. 对外 API（`groundguard/__init__.py` 导出）

```python
from groundguard import Ledger, tool_call, grounded_generate, Policy

with Ledger(session_id="req_001") as ledger:
    with tool_call("get_company_financials", args={"ticker": "AAPL"}, ledger=ledger) as call:
        result = fetch_financials("AAPL")
        call.record_facts(
            {
                "net_profit_2025": (Decimal(result["net_profit"]), "CNY"),
                "revenue_2025": (Decimal(result["revenue"]), "CNY"),
            },
            raw=result,
        )

    answer = grounded_generate(
        prompt="总结一下这家公司最新的财务表现",
        llm_call=lambda p: my_llm.complete(p),   # 调用方自己的模型调用函数，保持框架无关
        ledger=ledger,
        required_fact_keys=["net_profit_2025", "revenue_2025"],
        policy=Policy(),  # 可选，不传则用默认策略
    )

    report = ledger.coverage_report(
        answer,
        required_fact_keys=["net_profit_2025", "revenue_2025"],
    )
    if not report.passed:
        print(report.policy_reason)
```

`grounded_generate` 本身不内置任何具体模型 SDK 依赖——它接收一个 `llm_call: Callable[[str], str]`，调用方传入自己的模型调用函数。这保证了框架无关：无论用的是 OpenAI SDK、LangChain 还是自研 HTTP 调用，都能直接用。

v1 的 `grounded_generate` 应尽量在 prompt 中要求模型使用显式 fact key 标记，例如 `[fact:net_profit_2025]`。如果模型没有标记，系统仍可做数值候选匹配，但候选匹配不默认通过门禁。

## 5. 旗舰 Demo（`examples/financial_report_demo/`）

这是冷启动最重要的交付物，必须在 Sprint 6 之前就有真实（脱敏后）素材：

```text
examples/financial_report_demo/
  README.md              # 30 秒讲清楚问题：before/after 对比
  fixtures/
    tool_response.json    # 工具的真实返回（脱敏后的通用案例，非公司具体业务数据）
    bad_model_output.txt  # 未接入 GroundGuard 时的错误输出：说没数据，或漏掉工具已返回的关键数据
  run.py                  # 跑一遍完整链路，打印 CoverageReport，展示 unverified/contradicted 被拦下来
```

`README.md` 里必须包含一段清晰的 before/after：不接入时模型说"没有数据"或漏掉关键数字，接入后 `CoverageReport` 显示"该事实在账本中已核实为 X，但生成文本未覆盖/引用有误"，并给出修正建议。这段素材是发布时最有传播力的部分，需要单独打磨。

## 6. Sprint 拆分（可直接排期）

| Sprint | 交付物 | 验收标准 |
| --- | --- | --- |
| S0 基建 | 仓库骨架、`pyproject.toml`、pytest + CI 脚手架 | `pytest` 能跑（即使 0 个测试） |
| S1 数据模型 + Ledger | `models.py`、`ledger.py` + 单测 | register/query/expire 全部有测试覆盖 |
| S2 tool_call | `tool_call.py` + 单测 | 能记录耗时、参数、`record_facts` 写入 Ledger |
| S3 Output Claim Extractor | `output_claim_extractor.py` + 单测（含 fact key 与中文单位）| 覆盖显式 `[fact:key]`、"亿/万/%/美元"等常见单位归一化 |
| S4 Matcher | `matcher.py` + 单测 | verified/candidate_match/unverified/contradicted 四种场景都有用例，且无 key 数值匹配不默认 verified |
| S5 Coverage + Policy | `coverage.py`、`policy.py`，串通 `grounded_generate` | 端到端跑通 `__init__.py` 里的示例代码，并能识别 omitted_required |
| S6 旗舰 Demo | `examples/financial_report_demo/` | 一条命令跑出 before/after 对比 |
| S7 发布打磨 | LICENSE、CONTRIBUTING.md、issue 模板、发布文案草稿 | README/PLAN/ARCHITECTURE 三份文档互相链接一致 |

每个 Sprint 结束都应该是一个可独立合并的 PR，不依赖后续 Sprint 才能跑通（S0-S4 都是纯单测验证，S5 才第一次串联端到端）。

## 7. 测试策略

- **单元测试**：`core/` 下每个模块规则确定、无外部依赖，S1-S4 阶段的测试不需要真实模型调用。
- **回归 fixture 集**：收集几个真实（改写脱敏后）的失败案例作为长期回归用例，防止未来改动 matcher/policy 时悄悄破坏已修好的 case。
- **容差边界测试**：数值容差（四舍五入、单位换算）需要专门写边界用例，比如 0.49% vs 0.51% 误差。
- **必需事实遗漏测试**：账本里存在 required fact、输出没有引用时，必须产生 `omitted_required`，这是旗舰 demo 的核心失败模式。

## 8. 明确不做的事（防止范围膨胀）

- v1 不做任何持久化数据库依赖（Postgres/Redis/向量库）。
- v1 不做 LLM-as-judge 式的主观打分。
- v1 不做 dashboard/可视化。
- v1 不做非数值类声明的自动抽取（比较级、定性判断等留到 v2，且需要明确协议接口后再引入 LLM 依赖）。
- v1 不把无显式 fact key 的数值近邻匹配默认视为已核实，只作为 candidate match。
- 任何新增功能提案，先对照 [PLAN.md](PLAN.md) 第 4 节的"明确不做的事"清单检查是否重复造轮子。
