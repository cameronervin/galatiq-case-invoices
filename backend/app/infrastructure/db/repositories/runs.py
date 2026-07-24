from backend.app.infrastructure.db.repositories.run_lifecycle import (
    RunLifecycleRepository,
)
from backend.app.infrastructure.db.repositories.run_queries import RunQueryRepository
from backend.app.infrastructure.db.repositories.run_results import RunResultRepository


class RunRepository(
    RunLifecycleRepository,
    RunResultRepository,
    RunQueryRepository,
):
    """SQLAlchemy run adapter composed from focused persistence operations."""
