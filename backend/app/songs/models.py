"""SQLAlchemy models for songs."""

import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Text, Boolean, Date, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Song(Base):
    """A song with metadata, lyrics, and AI-generated mood profile."""

    __tablename__ = "songs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    spotify_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    artist: Mapped[str] = mapped_column(String(512), nullable=False)
    album: Mapped[str] = mapped_column(String(512), nullable=True)
    genres: Mapped[dict] = mapped_column(JSON, default=list)
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    preview_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    album_art_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    release_date: Mapped[date] = mapped_column(Date, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    # Lyrics
    lyrics: Mapped[str] = mapped_column(Text, nullable=True)
    lyrics_source: Mapped[str] = mapped_column(String(32), nullable=True)  # "genius" | "lrclib"

    # AI Analysis
    mood_profile: Mapped[dict] = mapped_column(JSON, nullable=True)
    has_embedding: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Song {self.name} by {self.artist}>"
