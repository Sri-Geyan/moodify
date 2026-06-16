"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    # --- Spotify ---
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8000/auth/callback"

    # --- HuggingFace ---
    huggingface_api_token: str

    # --- Genius ---
    genius_access_token: str

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./spotify_ai.db"

    # --- Qdrant ---
    qdrant_url: str = ":memory:"
    qdrant_api_key: str = ""
    qdrant_collection: str = "songs"

    # --- App ---
    secret_key: str = "dev-secret-key-change-in-production"
    frontend_url: str = "http://localhost:5173"
    debug: bool = True

    # --- AI Model Config ---
    hf_llm_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # Matches all-MiniLM-L6-v2 output

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
