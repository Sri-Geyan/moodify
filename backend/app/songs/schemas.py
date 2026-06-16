"""Pydantic schemas for songs."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class SpotifyTrack(BaseModel):
    """Track data from Spotify search results."""
    spotify_id: str
    name: str
    artist: str
    album: Optional[str] = None
    album_art_url: Optional[str] = None
    preview_url: Optional[str] = None
    popularity: int = 0
    duration_ms: Optional[int] = None
    release_date: Optional[str] = None
    genres: list[str] = []


class SongResponse(BaseModel):
    """Full song response with metadata and AI analysis."""
    spotify_id: str
    name: str
    artist: str
    album: Optional[str] = None
    album_art_url: Optional[str] = None
    preview_url: Optional[str] = None
    popularity: int = 0
    genres: list[str] = []
    release_date: Optional[date] = None
    has_lyrics: bool = False
    has_mood_profile: bool = False
    has_embedding: bool = False
    mood_profile: Optional[dict] = None


class SearchResults(BaseModel):
    """Search results response."""
    query: str
    tracks: list[SpotifyTrack]
    total: int
