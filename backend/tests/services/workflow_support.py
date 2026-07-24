from pathlib import Path

from backend.app.bootstrap.invoice_runtime import build_invoice_processor
from backend.app.core.config import Settings
from backend.app.services.invoice_processing import InvoiceProcessingService

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def settings_for(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "app.db",
        upload_dir=tmp_path / "uploads",
        llm_provider="offline",
        llm_model="deterministic-v1",
    )


def service_for(tmp_path: Path) -> InvoiceProcessingService:
    return build_invoice_processor(settings_for(tmp_path))
