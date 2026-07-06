# Financial Report Demo

This demo shows the smallest GroundGuard loop:

1. A tool returns structured financial facts.
2. A model answer says the facts were not available.
3. GroundGuard marks the required facts as omitted.
4. A corrected answer cites the registered fact keys and passes the gate.

Run:

```powershell
python examples/financial_report_demo/run.py
```

Expected output:

```text
Before GroundGuard correction
-----------------------------
passed: False
verified: 0
unverified: 0
contradicted: 0
omitted_required: 2
policy_reason: omitted_required_count=2 > max_omitted_required=0

After fact-key correction
-------------------------
passed: True
verified: 2
unverified: 0
contradicted: 0
omitted_required: 0
```

## 中文说明

这个 demo 展示 GroundGuard 最小闭环：

1. 工具返回结构化财务事实。
2. 模型回答说没有拿到这些事实。
3. GroundGuard 把 required facts 标记为遗漏。
4. 修正后的回答引用已登记的 fact keys，并通过门禁。

运行：

```powershell
python examples/financial_report_demo/run.py
```
