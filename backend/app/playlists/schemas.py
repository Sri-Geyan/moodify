"""Pydantic schemas for playlists."""

from pydantic import BaseModel


class CreatePlaylistRequest(BaseModel):
    """Request to create a Spotify playlist from recommendations."""
    name: str = ""
    description: str = ""
    track_spotify_ids: list[str]
    seed_song_name: str = ""
    seed_artist: str = ""
    public: bool = True


class PlaylistResponse(BaseModel):
    """Response after creating a Spotify playlist."""
    playlist_id: str
    playlist_url: str
    name: str
    track_count: int
    snapshot_id: str = ""
