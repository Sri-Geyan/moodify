"""Security utilities — session tokens and CORS."""

from itsdangerous import URLSafeTimedSerializer
from app.core.config import get_settings

settings = get_settings()

serializer = URLSafeTimedSerializer(settings.secret_key)


def create_session_token(data: dict) -> str:
    """Create a signed session token from user data."""
    return serializer.dumps(data)


def verify_session_token(token: str, max_age: int = 86400) -> dict | None:
    """Verify and decode a session token. Returns None if invalid/expired."""
    try:
        return serializer.loads(token, max_age=max_age)
    except Exception:
        return None
