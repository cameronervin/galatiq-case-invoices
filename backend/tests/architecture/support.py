import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def backend_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("backend.app."):
                imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(
                alias.name
                for alias in node.names
                if alias.name.startswith("backend.app.")
            )
    return imports
