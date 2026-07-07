from __future__ import annotations

from pathlib import Path


def test_init_github_action_template_creates_starter_files(tmp_path: Path):
    from groundguard.cli.init import main

    exit_code = main(["--template", "github-action", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "groundguard.yml").exists()
    assert (tmp_path / "groundguard-ledger.jsonl").exists()
    assert (tmp_path / "answer.txt").exists()
    workflow = tmp_path / ".github" / "workflows" / "groundguard.yml"
    assert workflow.exists()
    assert "chasen2041maker/GroundGuard@v0.3.0" in workflow.read_text(
        encoding="utf-8"
    )


def test_init_refuses_to_overwrite_without_force(tmp_path: Path):
    from groundguard.cli.init import main

    config_path = tmp_path / "groundguard.yml"
    config_path.write_text("custom: true\n", encoding="utf-8")

    exit_code = main(["--template", "openai", "--output-dir", str(tmp_path)])

    assert exit_code == 2
    assert config_path.read_text(encoding="utf-8") == "custom: true\n"


def test_init_force_overwrites_existing_files(tmp_path: Path):
    from groundguard.cli.init import main

    config_path = tmp_path / "groundguard.yml"
    config_path.write_text("custom: true\n", encoding="utf-8")

    exit_code = main(
        ["--template", "openai", "--output-dir", str(tmp_path), "--force"]
    )

    assert exit_code == 0
    assert "required_facts:" in config_path.read_text(encoding="utf-8")
    assert (tmp_path / "examples" / "openai_groundguard.py").exists()
