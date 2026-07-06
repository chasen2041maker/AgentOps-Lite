import json


def test_groundguard_demo_runs_before_after():
    from groundguard.cli.demo import run_demo

    result = run_demo()

    assert result["before"]["passed"] is False
    assert result["before"]["omitted_required"] == 2
    assert result["after"]["passed"] is True
    assert result["after"]["verified"] == 2


def test_groundguard_demo_cli_prints_json(capsys):
    from groundguard.cli.demo import main

    exit_code = main(["--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["before"]["passed"] is False
    assert payload["after"]["passed"] is True
