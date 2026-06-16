"""Pydantic schemas for recommendation requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional
from app.ai.schemas import MoodProfile


class RecommendRequest(BaseModel):
    """Request to generate song recommendations."""
    seed_spotify_id: str
    playlist_length: int = Field(default=20, ge=5, le=50)
    natural_language_prompt: Optional[str] = None
    mood_adjustments: Optional[dict] = None  # {"valence": +0.2, "energy": -0.1}


class RecommendedTrack(BaseModel):
    """A single recommended track with scoring breakdown."""
    spotify_id: str
    name: str
    artist: str
    album: str = ""
    album_art_url: str = ""
    preview_url: str = ""
    popularity: int = 0
    genres: list[str] = []
    moods: list[str] = []
    themes: list[str] = []
    atmosphere: list[str] = []

    # Scoring
    hybrid_score: float = 0.0
    embedding_similarity: float = 0.0
    genre_similarity: float = 0.0
    artist_similarity: float = 0.0
    popularity_similarity: float = 0.0
    explanation: str = ""


class RecommendResponse(BaseModel):
    """Full recommendation response."""
    seed_song: dict
    seed_mood_profile: MoodProfile
    tracks: list[RecommendedTrack]
    total_candidates: int = 0
    vector_db_size: int = 0
    natural_language_prompt: Optional[str] = None
