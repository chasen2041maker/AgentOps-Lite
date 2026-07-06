# GroundGuard

给会调用工具、会引用数据的 AI Agent 装一道"事实闸门"：生成阶段的每一个数字、每一条结论，都必须能追溯到一条已核实的事实记录，追溯不到就必须显式承认"未核实"，而不是编一个听起来合理的答案。

> 当前状态：pre-alpha。这个仓库正在公开构建中。第一阶段目标是完成一个最小可用的 Python 核心库（事实账本 + 核验 + 引用强制），以及一个能跑通真实案例的 demo。

## 为什么需要它

工具调用型 Agent 最常见、也最难排查的两类失败，不是报错，而是"看起来很正常"：

- **明明拿到了数据，却说没拿到**：工具已经返回了准确的数字，模型生成报告时却写"本轮未取得/无法核实"，或者干脆漏掉了这个数字。
- **拿不到数据时，编一个像样的答案**：工具没查到结果，模型没有"查不到该怎么说"的明确指令，于是凭训练知识编了一个格式正确、语气自信、但完全没有来源的结论。

这两类问题的共同根因是：现有的 Agent 框架里，"工具返回了什么"和"模型最终写了什么"之间没有强约束——模型可以自由地忽略、篡改或编造。市面上的可观测性工具（记录发生了什么）和 LLM-as-judge 评测工具（生成之后打个主观分）都是在事后检查，没有一个在**生成阶段就前置约束**："这句话里的每个事实点，必须能对应账本里的一条已核实记录"。

GroundGuard 想做的就是这一件事：把"工具结果"和"最终输出"之间的约束，从口头约定变成可执行、可测试的工程机制。

## 核心机制：一个事实账本 + 一张对账单

GroundGuard 的核心是三个互相配合的概念：

| 概念 | 类比 | 作用 |
| --- | --- | --- |
| **Claim（需求项）** | 点菜单 | 用户这次提问，实际需要核实哪些事实点 |
| **Ledger（事实账本）** | 备料台 | 工具调用返回的每一条可核实数据，连同来源、时间戳一起登记 |
| **Coverage Report（对账单）** | 出菜前的核对单 | 把"需要核实的"和"账本里有的"逐项比对，标出：已核实 / 未核实 / 有矛盾 |

生成阶段只允许引用账本里对上账的条目；账本里没有的数字，输出前会被拦下来，标记为"未核实"而不是静默通过。这不是一个"生成完之后打分"的评测工具，而是一个**贯穿工具调用到最终输出全过程的约束层**。

## 目标使用体验

```python
from groundguard import Ledger, tool_call, grounded_generate

with Ledger(session_id="req_001") as ledger:
    with tool_call("get_company_financials", args={"ticker": "AAPL"}) as call:
        result = fetch_financials("AAPL")
        call.record_facts(result)  # 结果连同来源、时间戳一起进账本

    answer = grounded_generate(
        prompt="总结一下这家公司最新的财务表现",
        ledger=ledger,
        on_unverified="flag",  # 引用不到账本的内容会被标记，而不是静默放行
    )

    report = ledger.coverage_report(answer)
    # report.verified   -> 有据可查的结论
    # report.unverified -> 模型写了、但账本里对不上的内容
    # report.contradicted -> 和账本数据冲突的内容
```

## 和其他工具有什么不同

- **不是又一个可观测性平台**：Langfuse、Arize Phoenix、Helicone、AgentOps 解决的是"看清 Agent 做了什么"，是事后的记录和展示。GroundGuard 解决的是"约束 Agent 能说什么"，作用在生成之前。
- **不是又一个 LLM-as-judge 评测框架**：promptfoo、DeepEval 这类工具用另一个模型给答案打分，衡量的是主观质量。GroundGuard 做的是确定性的引用核对，不依赖第二个模型的判断。
- **不是通用幻觉检测研究工具**：学术界的幻觉检测方法（基于内部表征、不确定性量化等）大多是黑盒式的事后打分。GroundGuard 假设你已经知道"事实应该从哪些工具调用里来"，直接在这条已知链路上做强约束，更适合有明确工具调用边界的生产场景（金融、医疗、法律等对数字负责的领域）。

GroundGuard 的目标不是替代这些工具，而是补上它们都没做的那一层：生成之前的强制核对。

## 计划功能

- 核心事实账本：登记、按来源查询、按时间戳失效
- 引用核对器：从生成文本里抽取声明，比对账本，输出 Coverage Report
- 框架适配器：LangChain callback、原生 OpenAI/兼容接口 wrapper
- CI 集成：输出与 promptfoo/DeepEval 断言兼容的 JSON，作为组件而不是替代品
- 可视化 diff：一次改动前后，Coverage Report 的变化对比

## 路线图

### Milestone 1：核心库

- Ledger 数据结构与记录 API
- 声明抽取与账本核对（先支持数字/命名实体类声明）
- Coverage Report 生成
- 一个可复现的真实失败案例 demo（工具有数据、模型说没有数据 → 接入 GroundGuard 后被拦截修正）

### Milestone 2：框架适配

- LangChain / LangGraph 回调适配
- 原生 Python 装饰器 / context manager 用法
- 常见 Agent 框架的接入示例

### Milestone 3：CI 集成

- 输出 JSON 报告，兼容主流评测工具的断言格式
- GitHub Action：PR 中标注"这次改动是否引入了新的未核实声明"

### Milestone 4：可视化

- 本地轻量 dashboard：查看账本、声明、核对结果的时间线
- 一次 prompt/工具改动前后的 Coverage Report 对比

## 典型使用场景

- 金融/医疗/法律等场景下，防止模型编造具体数字或结论
- 排查"工具明明返回了正确数据，报告却说没查到"这类隐藏 bug
- 在 CI 中拦截"这次改动让更多声明失去了事实依据"的回归
- 给已有的工具调用型 Agent 加一层可测试的事实边界，而不用重写整个框架

## 仓库结构

计划中的结构：

```text
groundguard/
  core/          Ledger、Claim、Coverage Report 核心实现
  adapters/      LangChain / OpenAI 等框架适配器
  cli/           命令行工具与 CI 集成
  examples/      可复现的失败案例与接入示例
  docs/          设计文档
```

## 参与贡献

项目还处于非常早期阶段。欢迎以下类型的贡献：

- 真实的"模型说没数据/编造数字"失败案例（脱敏后的输入输出即可，不需要还原具体业务）
- 声明抽取/核对算法的改进思路
- 框架适配器实现
- API 设计反馈

如果是较大的改动，请先开 issue，描述一个具体的小提案。

## 安全说明

Ledger 中可能包含 prompt、工具输出等敏感数据。GroundGuard 默认本地优先存储，不做静默远程上传，共享或导出前需要显式脱敏。

## License

本项目计划采用 MIT License。正式发布第一个 tag 前会补充 LICENSE 文件。
