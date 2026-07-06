# GroundGuard 重构方案

> 基于对全量源码（`groundguard/core/*`、`adapters/*`、`generate/*`、`cli/report.py`）
> 及同类项目（guardrails-ai、NeMo-Guardrails、uqlm、LettuceDetect、promptfoo、DeepEval）
> 的调研得出。

## 0. 审核状态（2026-07-06）

这份文件已按当前 `main` 代码重新校准，不再只是外部调研草稿：

- **已落地（v0.1.3）**：归一化层核心、英文金额/量级/百分比补齐、单位感知匹配、`ambiguous` 歧义状态、assertion JSON 的 per-claim 明细、`strip` 策略边界收拢。
- **已落地（v0.1.4）**：阶段 1 的 `OutputClaim.start/end` span 偏移，以及基于 span 的未核实声明剥离。
- **仍待执行**：阶段 2.5 的未覆盖数字透明化、阶段 3 的可插拔提取器注册表、阶段 4 的 `fix/reask` 策略扩展、阶段 5 的 promptfoo/DeepEval 专用适配、阶段 6 的账本索引和匹配分桶。

执行原则：每一阶段仍按 TDD 单独落地，保持默认路径确定性、无数据库、无第二个 LLM。

## 一、指导原则

1. **确定性是命根子，不能碰**。任何重构不得引入"默认需要 LLM/模型"的路径。
   可选的 LLM 提取器可留口子，但默认必须零推理、零成本、可复现。
2. **不破坏现有测试**。~1111 行测试是资产。走"加新层 + 旧接口转发"，不推倒重来。
   对外函数签名（`extract_output_claims`、`coverage_report`、`grounded_generate`）保持不变，内部换实现。
3. **落实或删除已声明未实现的 API**。`ClaimType` 的 `entity/comparison/assertion`、
   `FactValueKind` 的 `entity/text`、`Fact.confidence`、`display_value` 现在是"画饼"，误导用户。

## 二、核心洞察（决定优先级）

### 三块蓝海（重构中必须保护、放大，绝不弄丢）
- **确定性数值核查（无模型）** —— 搜遍 GitHub 无同类命名项目。
- **单位感知的矛盾检测** —— 所有竞品都是"单位盲"。
- **"漏写必需事实"检测（omitted_required）** —— 6 个竞品无一人做"该说的说全了没"。

### 缺的都是"工程成熟度"，不是核心能力
可插拔、span 偏移、下游集成接口、修复动作。
→ 重构不是重写核心，是给核心加"骨架和接口"，让别人能用、能扩、能集成。

## 三、分层目标架构

```
答案文本
   │
   ▼
1. Normalizer 归一化层（新增）      "$3.83B"→3.83e9/USD, "八百亿"→8e10
2. Extractor 可插拔提取器（重构）    @register_extractor 注册; 每条 claim 带 start/end
     - NumericExtractor (现有正则)
     - CurrencyExtractor (新, 英文)
     - PercentExtractor (新)
     - (可选) LLMExtractor 留口不默认开
3. Matcher 匹配层（基本不动）       Decimal + 相对误差, 保护此层; + 歧义标记
4. Policy 策略层（收拢 + 扩展）      flag/strip/block/fix/reask
5. Report/集成层（重构输出）         span明细 + componentResults + to_df
     + promptfoo get_assert
     + DeepEval GroundGuardMetric
```

匹配层（第 3 层）几乎不动——那是最对的地方。重构集中在上游（1、2）和下游（4、5）。

## 四、分阶段实施（按 ROI 排序，每阶段独立交付）

### 阶段 1：span 偏移（半天，ROI 最高，零风险）
正则已算出 `match.start()/end()`，现在扔掉了。
- `models.py` `OutputClaim` 加 `start: int | None`、`end: int | None`
- `output_claim_extractor.py:34-43` 构造时填入偏移
- `grounded_generate.py:124` `_strip_claim_span` 改用 `claim.start/end` 精确切片，
  扔掉脆弱的 `answer.find(text_span)`

收益：精确高亮、可靠 strip、下游 UI 定位。风险：极低。

### 阶段 2：归一化层 + 英文单位（1-2 天，打开国际用户的门）
最大功能缺口：正则只有 `亿|万|千` 和 `%|美元|元|股|倍`，英文（$3.83 billion / 383M / 21.5%）一个抓不到。
- 新增 `groundguard/core/normalizer.py`（纯函数）：
  - `normalize_magnitude` 亿→1e8, billion→1e9, million→1e6, K/M/B
  - `normalize_unit` $→USD, ¥/元→CNY, €→EUR, %→percent
  - `normalize_number` 去千分位 3,830 / 科学计数法
- 扩展 `output_claim_extractor.py:10-15` 正则增加英文分支
- `matcher.py:33` 单位比较前双方过 `normalize_unit`，让 `元`↔`CNY` 判等

收益：国际用户可用；单位不再因写法误报。风险：中，需足量测试；改前跑 pytest 基线。

### 阶段 2.5：覆盖率提升与透明化（关键，回应"覆盖太少"的担忧）

**核心认知**：不追求"一个理解一切的通用规则"（那只有 LLM 能做，会杀死确定性）。
"通用" = 归一化收敛写法 + 一组可注册规则覆盖所有规整形状 + 可选 LLM 口（默认关）。

**A. 补全"形状规整、只是没写"的表达（能覆盖，属补齐不属换技术）：**
- 中文数字：八百亿 → 800亿（归一层做）
- 英文量级：$3.83 billion / 383M / 1.2B / K/M/B
- 货币符号：$ / ¥ / € / £
- 百分比含区间：10-15% / 21.5 percent
- 千分位与科学计数法：3,830 / 1.2e9
- 负数、正负号

**B. 语义模糊表达（"接近四百亿""两成左右""几乎翻倍"）：**
确定性方法搞不定，不用正则硬扛。仅通过阶段 3 的可选 LLM 提取口覆盖，默认关闭。

**C. 覆盖率透明化（比提高覆盖率更重要）：**
当前：没被提取的数字被静默忽略，报告仍 `passed: True` —— 用户误以为"全查过"。
改为：提取时统计"文本中疑似数字总数 N vs 已覆盖 M"，报告给出 `coverage_ratio`
和"未覆盖数字清单"。即使覆盖非 100%，用户也知道边界。
对事实核查工具而言，"诚实暴露没查什么" > "假装查全了"。
- `CoverageReport` 加 `uncovered_numbers: list[str]`、`extraction_coverage: float`
- 用一个宽松的"疑似数字"探测正则统计分母，与实际提取的分子对比

### 阶段 3：可插拔提取器注册表（2-3 天，架构升级）
把"一个大正则"变成"一组可注册小提取器"，让画饼的 ClaimType 落地。
- 新增 `groundguard/core/registry.py`：`register_extractor(claim_type)` 装饰器 + `_EXTRACTORS` dict
- 现有 `extract_output_claims` 拆成注册项：`@register_extractor("numeric"/"currency"/"percent")`
- 顶层函数变成"跑所有已注册提取器并合并"，对外签名不变
- 采用 guardrails 的 `validate()/_validate()` 分层：外层统一处理 span 附加/单位归一/去重，内层只识别形状

收益：用户可加自定义提取器不用 fork；entity/comparison 有落地的家。风险：中，最大结构调整。

### 阶段 4：策略层收拢 + fix/reask（2 天，独一份卖点）
先修 bug 级问题：`on_unverified="strip"` 执行散在 `grounded_generate.py`，
而 `policy.py:evaluate_policy` 根本不处理 strip。收拢到统一的 `apply_policy(answer, report, policy)`。
- 新增 `fix`：仅对挂了 `[fact:key]` 标签的 contradicted，用账本 `display_value` 替换错误数字。
  竞品结构上做不到（无账本真值）。**差异化王牌，但默认关闭**，防掩盖幻觉。
- 新增 `reask`：把矛盾/漏写反馈回传 `llm_call` 重新生成（正道：让模型重写而非工具改文本）。
- `Policy` 扩展 `on_contradicted: flag|block|fix|reask`

收益：fix 是独家营销点；策略执行不再分裂。风险：中，fix 严格限定+默认关。

### 阶段 5：下游集成层（2-3 天，从"能跑"到"能被别人用"）
- per-claim 明细进 JSON：`report.py` 增加 `componentResults`（每条 claim 一个 pass/score/reason/start/end/status/diff）
- 新增 `groundguard/integrations/promptfoo.py`：`get_assert(output, context) -> dict`
- 新增 `groundguard/integrations/deepeval.py`：`GroundGuardMetric(BaseMetric)`
  （measure/a_measure/is_successful/__name__；从 test_case.tools_called 或 context 填账本）
- `CoverageReport.to_records()/to_df()`：pandas 友好
- 清理 CLI 冗余键：promptfoo 只读 `pass`、DeepEval 只读 `success`，`passed` 是噪音

收益：升级成 promptfoo/DeepEval 即插即用插件。风险：低，纯新增适配器。

### 阶段 6：清理技术债（穿插，1 天）
- 落实或删除 `Fact.confidence`（传播到 claim + policy 可阈值化）、`display_value`（fix 要用）、`metadata`
- matcher 歧义标记：`_nearest_fact` 有多条同单位近似事实时标 `ambiguous`
- 可选 `groundguard.yml` 配置（容差/必需事实/单位同义词/策略阈值），对齐 NeMo

## 五、规模与性能（当"上万上百万"时）

正则本身对文本长度是线性的，几乎不是瓶颈。真正扛不住规模的是匹配层与账本查询：

- `matcher.py` 无 key 的候选匹配是 O(claims × facts)：账本上万条事实 + 答案上百声明 → 百万级比较。
- `_nearest_fact`（`matcher.py:73`）每条 claim 对全账本线性扫描。
- `ledger.all_facts()`（`ledger.py:40`）每次调用重新过滤过期项，无索引。
- `query(key)`（`ledger.py:37`）是 O(n) 线性查找，非 dict 索引。

**扩展方向（作为阶段 6+ 或独立阶段）：**
1. 账本建 `dict[key -> list[Fact]]` 索引，`query` 降到 O(1)；显式 key 匹配直接命中。
2. 无 key 候选匹配按 `(unit -> sorted values)` 分桶 + 二分找最近邻，从 O(n) 降到 O(log n)。
3. `all_facts` 的过期过滤加缓存/惰性失效，避免每次全扫。
4. 若真到百万级答案吞吐：提取用 `re` 编译好的单一 pattern（已是）+ 批处理；考虑把
   `coverage_report` 做成可流式/分块。
5. 正则灾难性回溯审计：确保新增的英文分支不引入嵌套量词导致 ReDoS。

结论：正则不是规模瓶颈；**先加账本索引和匹配分桶**，这是规模化的真正杠杆。

## 六、执行顺序与依赖

```
阶段1 (span) ──┬─→ 阶段4 (fix 依赖 span 精确定位)
               └─→ 阶段5 (高亮依赖 span)
阶段2 (归一化) ──→ 阶段3 (提取器注册表)
阶段4/5 独立可并行
阶段6 穿插
```

建议节奏：1 → 2 → 3 →（4 和 5 并行）→ 6。

**每阶段铁律**：动手前 `pytest` 存基线，改完 `pytest` 对比，红了先修再进下一阶段。

## 七、一句话总结

别重写核心（匹配层是最对的地方），而是给它加上游的归一化+可插拔提取，
和下游的 span 明细+集成适配器。保护三块蓝海（确定性、单位感知、漏写检测），
把 `fix` 做成默认关闭的独家卖点。规模化的真正杠杆是账本索引与匹配分桶，不是正则。
## v0.2.0 Implementation Status

Implemented from this refactor plan:

- Stage 2.5: uncovered-number transparency through `suspected_numbers`,
  `uncovered_numbers`, and `extraction_coverage`.
- Stage 3: pluggable extractor registry through `register_extractor(...)`.
- Stage 4: `fix` and `reask` contradicted-claim policy actions.
- Stage 5: promptfoo / DeepEval helper adapters and per-claim
  `componentResults`.
- Stage 6: Ledger key index and matcher unit buckets.

Remaining follow-ups are now quality/distribution work, not blockers for the
core refactor described in this file.
