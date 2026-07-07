# Social Posts

Use these posts when you want to point people to GroundGuard without making
them decode the whole architecture first.

## Show HN

```text
Show HN: Assertions for AI agent answers, without an LLM judge

I built GroundGuard after seeing a recurring failure in tool-using agents:
the tool returned the number, but the final answer either rewrote it, omitted
it, or claimed the data was unavailable.

GroundGuard records important tool facts in a local ledger, then checks the
final answer before release. It is deterministic, local-first, and does not
call a second LLM judge.

Reproducible benchmark:
- 200 bilingual realistic cases
- 71/71 expected failures caught
- 0 false positives
- 0 false negatives

Repo: https://github.com/chasen2041maker/GroundGuard
```

## r/LocalLLaMA

```text
I built a small local-first fact gate for tool-using agents.

The specific failure it targets: your agent calls tools, gets numeric facts,
then the final answer ignores, rewrites, or omits those facts. GroundGuard does
not use an LLM judge. It records tool facts in a local ledger and checks the
final answer deterministically before release.

The included benchmark catches 71/71 expected failures in 200 bilingual cases
with 0 false positives and 0 false negatives.

Install:
python -m pip install groundguard-ai
groundguard-demo
groundguard-benchmark
```

## WeChat / Friends

```text
我做了一个开源小工具 GroundGuard。

它解决的是 AI Agent 一个很隐蔽的问题：工具明明查到了数字，模型最后回答时却写错、漏写，甚至说“没查到”。

GroundGuard 的思路很简单：工具返回的重要事实先记进本地账本，最终答案放行前再对账。不用第二个 LLM 当评委，不依赖数据库，适合塞进现有 Agent 后端。

现在已经有 PyPI 包、GitHub Action、OpenAI/LangGraph/promptfoo/DeepEval 等接入方式。内置 200 条中英文 benchmark，当前抓到 71/71 个预期失败，0 false positive。

如果你也做 AI Agent，欢迎帮我点个 Star：
https://github.com/chasen2041maker/GroundGuard
```

## Xiaohongshu

```text
我给 AI Agent 做了一个“事实闸门”

痛点：工具已经返回了数字，模型最后却可能写错、漏写，或者装作没拿到数据。

GroundGuard 做的事很朴素：
1. 工具返回关键数字，先记账
2. 模型生成最终答案
3. 放行前对账
4. 数字不一致、必需事实漏掉，就拦住

它不是观测平台，也不是 LLM 评委，而是一个本地、确定性、可测试的小关卡。

目前已发布到 PyPI，支持 GitHub Action、OpenAI、LangGraph、promptfoo、DeepEval 等接入。

开源地址：github.com/chasen2041maker/GroundGuard
```
