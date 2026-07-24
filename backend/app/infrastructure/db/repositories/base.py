from backend.app.infrastructure.db.session import SessionContext


class SessionRepository:
    """Base for repository operations that share an injected session factory."""

    def __init__(self, sessions: SessionContext) -> None:
        self.sessions = sessions
