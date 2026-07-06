import ast
from pathlib import Path


def test_core_modules_do_not_shadow_top_level_functions():
    duplicate_allowed: dict[str, set[str]] = {}
    for path in [
        Path("groundguard/core/units.py"),
        Path("groundguard/core/output_claim_extractor.py"),
    ]:
        module = ast.parse(path.read_text(encoding="utf-8"))
        seen: set[str] = set()
        duplicates: set[str] = set()
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                if node.name in seen:
                    duplicates.add(node.name)
                seen.add(node.name)

        assert duplicates == duplicate_allowed.get(str(path), set())
