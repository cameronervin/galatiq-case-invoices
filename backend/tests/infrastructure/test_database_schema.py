from pathlib import Path

from sqlalchemy import UniqueConstraint, inspect

from backend.app.infrastructure.db.migrations import initialize_database
from backend.app.infrastructure.db.models import (
    AgentRun,
    Base,
    InventoryItem,
    Payment,
    RunEventRecord,
    RunResult,
    SchemaMigration,
)
from backend.app.infrastructure.db.session import Database


def test_metadata_creation_is_repeatable_and_preserves_schema(
    tmp_path: Path,
) -> None:
    database = Database(tmp_path / "app.db")

    initialize_database(database)
    initialize_database(database)

    schema = inspect(database.engine)
    assert set(schema.get_table_names()) == {
        "schema_migrations",
        "inventory_items",
        "agent_runs",
        "run_results",
        "payments",
        "run_events",
    }
    active_profile = next(
        index
        for index in schema.get_indexes("agent_runs")
        if index["name"] == "idx_agent_runs_active_profile"
    )
    assert active_profile["unique"] == 1
    assert active_profile["column_names"] == [
        "content_hash",
        "provider_name",
        "provider_model",
    ]
    assert schema.get_foreign_keys("run_results")[0]["referred_table"] == "agent_runs"
    assert schema.get_foreign_keys("payments")[0]["referred_table"] == "agent_runs"
    assert schema.get_foreign_keys("run_events")[0]["referred_table"] == "agent_runs"
    assert schema.get_check_constraints("agent_runs")
    assert schema.get_check_constraints("payments")
    database.close()


def test_focused_models_register_one_complete_metadata_graph() -> None:
    models = {
        AgentRun,
        InventoryItem,
        Payment,
        RunEventRecord,
        RunResult,
        SchemaMigration,
    }

    assert {model.__table__.metadata for model in models} == {Base.metadata}
    assert set(Base.metadata.tables) == {
        "agent_runs",
        "inventory_items",
        "payments",
        "run_events",
        "run_results",
        "schema_migrations",
    }
    assert {
        table.name: tuple(column.name for column in table.columns)
        for table in Base.metadata.sorted_tables
    } == {
        "agent_runs": (
            "run_id",
            "content_hash",
            "source_filename",
            "source_path",
            "source_format",
            "source_origin",
            "provider_name",
            "provider_model",
            "status",
            "stage",
            "error_code",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        ),
        "inventory_items": ("item_code", "display_name", "stock", "aliases_json"),
        "payments": (
            "run_id",
            "idempotency_key",
            "status",
            "amount_cents",
            "currency",
            "mock_reference",
            "error_code",
            "created_at",
            "updated_at",
        ),
        "run_events": (
            "event_id",
            "run_id",
            "stage",
            "status",
            "code",
            "safe_message",
            "duration_ms",
            "created_at",
        ),
        "run_results": (
            "run_id",
            "invoice_json",
            "findings_json",
            "recommendation_json",
            "review_json",
            "extraction_attempts",
            "reflection_count",
            "updated_at",
        ),
        "schema_migrations": ("version", "name", "applied_at"),
    }
    assert {
        table.name: {
            constraint.name for constraint in table.constraints if constraint.name
        }
        for table in Base.metadata.sorted_tables
    } == {
        "agent_runs": {
            "ck_agent_runs_source_format",
            "ck_agent_runs_source_origin",
            "ck_agent_runs_stage",
            "ck_agent_runs_status",
        },
        "inventory_items": {"ck_inventory_stock"},
        "payments": {"ck_payments_amount", "ck_payments_status"},
        "run_events": {"ck_run_events_duration"},
        "run_results": {
            "ck_run_results_extraction_attempts",
            "ck_run_results_reflection_count",
        },
        "schema_migrations": set(),
    }
    assert {
        tuple(constraint.columns.keys())
        for constraint in Payment.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    } == {("idempotency_key",)}
    assert {
        foreign_key.target_fullname
        for table in (Payment.__table__, RunEventRecord.__table__, RunResult.__table__)
        for foreign_key in table.foreign_keys
    } == {"agent_runs.run_id"}
    assert {
        table.name: {index.name for index in table.indexes}
        for table in Base.metadata.sorted_tables
    } == {
        "agent_runs": {"idx_agent_runs_active_profile", "idx_agent_runs_newest"},
        "inventory_items": set(),
        "payments": set(),
        "run_events": {"idx_run_events_run"},
        "run_results": set(),
        "schema_migrations": set(),
    }
