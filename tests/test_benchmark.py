def test_fact_gate_benchmark_reports_detection_metrics():
    from benchmarks.fact_gate_benchmark import run_benchmark

    result = run_benchmark()

    assert result["cases_total"] == 4
    assert result["expected_failures"] == 3
    assert result["detected_failures"] == 3
    assert result["false_positives"] == 0
    assert result["mean_elapsed_ms"] >= 0

