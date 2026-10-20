"""Guard for the Dependency Rule (AGENTS.md, ADR-001, ADR-008) and for the
independence of the two bounded contexts (docs/PROJECT.md)."""
import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[3] / "src" / "order_pdf_orchestration"
FORBIDDEN = ("pydantic", "fastapi", "sqlalchemy", "fpdf", "procurement")


def _imported_modules(path: Path) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_import_no_framework_and_not_the_other_context(layer):
    offenders = {
        f"{path.relative_to(PACKAGE)}: {module}"
        for path in (PACKAGE / layer).rglob("*.py")
        for module in _imported_modules(path)
        if module.split(".")[0] in FORBIDDEN
    }
    assert not offenders


def test_no_module_of_this_context_imports_the_procurement_context():
    offenders = {
        str(path.relative_to(PACKAGE))
        for path in PACKAGE.rglob("*.py")
        if any(m.split(".")[0] == "procurement" for m in _imported_modules(path))
    }
    assert not offenders
