def test_realistic_dataset_reports_no_mismatches():
    from benchmarks.fact_gate_benchmark import run_realistic_dataset_benchmark

    result = run_realistic_dataset_benchmark()

    assert result["cases_total"] == 200
    assert result["expected_failures"] >= 60
    assert result["detected_failures"] == result["expected_failures"]
    assert result["false_positives"] == 0
    assert result["mismatches"] == []
