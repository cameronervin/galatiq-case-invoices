from pathlib import Path

from backend.app.core.config import Settings


def test_settings_use_neutral_app_environment_prefix(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DATABASE_PATH", "tmp/inventory.sqlite")

    settings = Settings()

    assert settings.env == "test"
    assert settings.database_path == Path("tmp/inventory.sqlite")


def test_cors_origins_include_localhost_variants() -> None:
    settings = Settings(frontend_origin="http://localhost:3100")

    assert settings.cors_origins == [
        "http://localhost:3100",
        "http://127.0.0.1:3000",
    ]
