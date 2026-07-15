from pathlib import Path
import tomllib


def test_release_metadata_is_consistent_for_release_candidate():
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    readme = Path("README.md").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert version == "0.4.0rc1"
    assert "Latest stable release: `0.3.1`" in readme
    assert f"Current pre-release: `{version}`" in readme
    assert f"python -m pip install --pre groundguard-ai=={version}" in readme
    assert f"## v{version}" in changelog
    assert "release candidate is for downstream integration validation" in changelog


def test_release_docs_state_checker_and_finance_scope_boundaries():
    readme = Path("README.md").read_text(encoding="utf-8")
    chinese_readme = Path("README.zh-CN.md").read_text(encoding="utf-8")
    limitations = Path("docs/limitations.md").read_text(encoding="utf-8")

    assert "Not an LLM-as-judge or general hallucination detector" in readme
    assert "does not call a second LLM by default" in readme
    assert "SSE/SZSE" in readme
    assert "0.4.0rc1" in chinese_readme
    assert "OrphanNumberChecker" in chinese_readme
    assert "RelativeFreshnessChecker" in chinese_readme
    assert "severity=\"hard\"" in chinese_readme
    assert "finance_cn" in chinese_readme
    assert "python -m pip install --pre groundguard-ai==0.4.0rc1" in chinese_readme
    assert "BSE" in limitations
    assert "2026-07-06" in limitations
