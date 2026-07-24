import ast

from backend.tests.architecture.support import APP_ROOT


def test_database_repository_adapters_are_split_by_responsibility() -> None:
    legacy_module = APP_ROOT / "infrastructure/db/repositories.py"
    repository_package = APP_ROOT / "infrastructure/db/repositories"

    assert not legacy_module.exists()
    assert {
        path.name
        for path in repository_package.glob("*.py")
        if path.name != "__init__.py"
    } == {
        "base.py",
        "inventory.py",
        "mappers.py",
        "payments.py",
        "run_lifecycle.py",
        "run_queries.py",
        "run_results.py",
        "runs.py",
    }
    package_tree = ast.parse((repository_package / "__init__.py").read_text())
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for node in ast.walk(package_tree)
    )
    assert len((repository_package / "runs.py").read_text().splitlines()) <= 40


def test_database_models_are_split_by_aggregate_with_one_shared_base() -> None:
    legacy_module = APP_ROOT / "infrastructure/db/models.py"
    model_package = APP_ROOT / "infrastructure/db/models"

    assert not legacy_module.exists()
    assert {
        path.name for path in model_package.glob("*.py") if path.name != "__init__.py"
    } == {
        "agent_runs.py",
        "base.py",
        "catalog.py",
        "events.py",
        "payments.py",
        "results.py",
    }
    for path in model_package.glob("*.py"):
        assert len(path.read_text().splitlines()) <= 140

    declarative_bases: list[tuple[str, str]] = []
    for path in model_package.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "DeclarativeBase":
                        declarative_bases.append((path.name, node.name))
    assert declarative_bases == [("base.py", "Base")]


def test_workflow_nodes_are_split_by_responsibility() -> None:
    node_package = APP_ROOT / "agents/nodes"
    responsibility_modules = {
        "approval.py",
        "extraction.py",
        "payment.py",
        "review.py",
        "shared.py",
        "validation.py",
    }

    assert {
        path.name for path in node_package.glob("*.py") if path.name != "__init__.py"
    } == responsibility_modules
    for module_name in responsibility_modules:
        assert len((node_package / module_name).read_text().splitlines()) <= 150


def test_invoice_processing_facade_delegates_to_small_use_case_modules() -> None:
    facade = APP_ROOT / "services" / "invoice_processing.py"
    assert len(facade.read_text().splitlines()) <= 150
    for module_name in {
        "invoice_execution.py",
        "invoice_intake.py",
        "invoice_reviews.py",
        "run_queries.py",
    }:
        assert (APP_ROOT / "services" / module_name).is_file()


def test_domain_validation_is_split_by_rule_family() -> None:
    legacy_module = APP_ROOT / "domain" / "validation.py"
    validation_package = APP_ROOT / "domain" / "validation"

    assert not legacy_module.exists()
    assert {
        path.name
        for path in validation_package.glob("*.py")
        if path.name != "__init__.py"
    } == {
        "extraction.py",
        "findings.py",
        "integrity.py",
        "inventory.py",
    }
    for path in validation_package.glob("*.py"):
        assert len(path.read_text().splitlines()) <= 130


def test_domain_schemas_are_split_by_aggregate() -> None:
    schema_package = APP_ROOT / "schemas"
    responsibility_modules = {
        "errors.py",
        "invoice.py",
        "payment.py",
        "review.py",
        "runs.py",
        "workflow.py",
    }

    assert responsibility_modules <= {path.name for path in schema_package.glob("*.py")}
    for module_name in responsibility_modules:
        assert len((schema_package / module_name).read_text().splitlines()) <= 140

    compatibility_tree = ast.parse((schema_package / "domain.py").read_text())
    assert not any(
        isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(compatibility_tree)
    )
