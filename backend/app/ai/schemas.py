"""Pydantic schemas for AI analysis results."""

from pydantic import BaseModel, Field


class MoodProfile(BaseModel):
    """Structured mood/theme analysis of a song."""

    moods: list[str] = Field(
        default_factory=list,
        description="Primary mood descriptors (e.g., melancholic, hopeful, aggressive, dreamy)",
    )
    themes: list[str] = Field(
        default_factory=list,
        description="Thematic content (e.g., heartbreak, mental health, loneliness, ambition)",
    )
    atmosphere: list[str] = Field(
        default_factory=list,
        description="Atmospheric descriptors (e.g., late night, rainy day, uplifting, cinematic)",
    )
    emotional_intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How emotionally intense the song is (0=subtle, 1=overwhelming)",
    )
    energy_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Energy level (0=calm/ambient, 1=high-energy/hype)",
    )
    valence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Emotional positivity (0=very negative/dark, 1=very positive/happy)",
    )
    genre_tags: list[str] = Field(
        default_factory=list,
        description="Inferred genre/subgenre tags from lyrics and style",
    )
    description: str = Field(
        default="",
        description="One-paragraph natural language summary of the song's emotional character",
    )


class AnalysisRequest(BaseModel):
    """Request to analyze a song."""
    spotify_id: str
    include_lyrics_fetch: bool = True


class AnalysisResponse(BaseModel):
    """Full analysis response."""
    spotify_id: str
    name: str
    artist: str
    lyrics_found: bool
    lyrics_source: str | None = None
    mood_profile: MoodProfile
    embedding_generated: bool
