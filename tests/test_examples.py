def test_decorator_demo_runs_end_to_end():
    from examples.decorator_demo.run import run_demo

    result = run_demo()

    assert result.report.passed is True
    assert result.report.verified_count == 2


def test_langgraph_node_demo_shows_gate_states():
    from examples.langgraph_node.run import run_demo

    result = run_demo()

    assert result.before["groundguard_report"].passed is False
    assert result.before["groundguard_report"].omitted_required_count == 2
    assert result.after["groundguard_report"].passed is True
    assert result.after["groundguard_report"].verified_count == 2


def test_openai_demo_offline_mode_runs_without_api_key(monkeypatch):
    from examples.openai_demo.run import run_demo

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = run_demo(use_live_openai=False)

    assert result.report.passed is True
    assert result.report.verified_count == 2


def test_promptfoo_groundguard_demo_returns_assertion_payload():
    from examples.promptfoo_groundguard.run import run_demo

    payload = run_demo()

    assert payload["pass"] is False
    assert payload["assertion"]["type"] == "groundguard.fact_coverage"
    assert payload["componentResults"][0]["metadata"]["status"] == "contradicted"


def test_deepeval_groundguard_demo_returns_metric_result():
    from examples.deepeval_groundguard.run import run_demo

    payload = run_demo()

    assert payload["success"] is False
    assert payload["score"] == 0.0
    assert payload["metadata"]["groundguard"]["contradicted_count"] == 1
