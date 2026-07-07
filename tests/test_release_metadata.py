from pathlib import Path
import tomllib


def test_release_metadata_is_consistent_for_next_patch_release():
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]
    readme = Path("README.md").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert version == "0.3.1"
    assert f"Latest PyPI release: `{version}`" in readme
    assert f"## v{version}" in changelog
