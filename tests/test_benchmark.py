def test_fact_gate_benchmark_reports_detection_metrics():
    from benchmarks.fact_gate_benchmark import run_benchmark

    result = run_benchmark()

    assert result["cases_total"] >= 20
    assert result["expected_failures"] == 14
    assert result["detected_failures"] == result["expected_failures"]
    assert result["false_positives"] == 0
    assert result["mean_elapsed_ms"] >= 0
