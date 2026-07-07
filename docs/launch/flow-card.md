# Flow Card

Use this as the source for a simple architecture image or carousel slide.

```text
工具返回事实
    |
    v
Ledger 本地账本
    |
    v
模型最终答案
    |
    v
GroundGuard 对账
    |
    +--> verified: 放行
    +--> contradicted: 拦截 / 修复 / 重问
    +--> omitted_required: 拦截
    +--> unverified: 标记 / 剥离 / 拦截
```

## One-Sentence Caption

GroundGuard makes tool data traceable: final answer numbers must match facts
registered from the current tool run.
