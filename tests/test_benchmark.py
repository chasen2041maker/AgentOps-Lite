def test_fact_gate_benchmark_reports_detection_metrics():
    from benchmarks.fact_gate_benchmark import run_benchmark

    result = run_benchmark()

    assert result["cases_total"] >= 20
    assert result["expected_failures"] == 14
    assert result["detected_failures"] == result["expected_failures"]
    assert result["false_positives"] == 0
    assert result["mean_elapsed_ms"] >= 0


def test_benchmark_suite_includes_realistic_dataset_summary():
    from benchmarks.fact_gate_benchmark import run_benchmark_suite

    result = run_benchmark_suite()

    assert result["smoke"]["cases_total"] >= 20
    assert result["realistic_dataset"]["cases_total"] == 200
    assert result["realistic_dataset"]["detected_failures"] == 71
    assert result["realistic_dataset"]["false_positives"] == 0
    assert result["realistic_dataset"]["false_negatives"] == 0
