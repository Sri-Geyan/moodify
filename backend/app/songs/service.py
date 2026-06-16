"""Song service — Spotify search, metadata fetching, and DB operations."""

import httpx
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.songs.schemas import SpotifyTrack
from app.songs.models import Song

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def search_spotify(query: str, access_token: str, limit: int = 10) -> list[SpotifyTrack]:
    """Search Spotify for tracks matching the query."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/search",
            params={"q": query, "type": "track", "limit": limit},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

    tracks = []
    for item in data.get("tracks", {}).get("items", []):
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        images = item.get("album", {}).get("images", [])
        album_art = images[0]["url"] if images else None

        tracks.append(SpotifyTrack(
            spotify_id=item["id"],
            name=item["name"],
            artist=artists,
            album=item.get("album", {}).get("name"),
            album_art_url=album_art,
            preview_url=item.get("preview_url"),
            popularity=item.get("popularity", 0),
            duration_ms=item.get("duration_ms"),
            release_date=item.get("album", {}).get("release_date"),
        ))

    return tracks


async def get_track_details(spotify_id: str, access_token: str) -> SpotifyTrack:
    """Fetch detailed track info from Spotify."""
    async with httpx.AsyncClient() as client:
        # Get track info
        response = await client.get(
            f"{SPOTIFY_API_BASE}/tracks/{spotify_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        item = response.json()

        # Get artist info for genres
        artist_id = item["artists"][0]["id"] if item.get("artists") else None
        genres = []
        if artist_id:
            artist_resp = await client.get(
                f"{SPOTIFY_API_BASE}/artists/{artist_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if artist_resp.status_code == 200:
                genres = artist_resp.json().get("genres", [])

    artists = ", ".join(a["name"] for a in item.get("artists", []))
    images = item.get("album", {}).get("images", [])
    album_art = images[0]["url"] if images else None

    return SpotifyTrack(
        spotify_id=item["id"],
        name=item["name"],
        artist=artists,
        album=item.get("album", {}).get("name"),
        album_art_url=album_art,
        preview_url=item.get("preview_url"),
        popularity=item.get("popularity", 0),
        duration_ms=item.get("duration_ms"),
        release_date=item.get("album", {}).get("release_date"),
        genres=genres,
    )


async def get_or_create_song(
    db: AsyncSession, track: SpotifyTrack
) -> Song:
    """Get existing song from DB or create a new entry."""
    result = await db.execute(
        select(Song).where(Song.spotify_id == track.spotify_id)
    )
    song = result.scalar_one_or_none()

    if song:
        return song

    # Parse release date
    release = None
    if track.release_date:
        try:
            if len(track.release_date) == 4:
                release = date(int(track.release_date), 1, 1)
            elif len(track.release_date) == 7:
                parts = track.release_date.split("-")
                release = date(int(parts[0]), int(parts[1]), 1)
            else:
                release = date.fromisoformat(track.release_date)
        except (ValueError, IndexError):
            release = None

    song = Song(
        spotify_id=track.spotify_id,
        name=track.name,
        artist=track.artist,
        album=track.album,
        genres=track.genres,
        popularity=track.popularity,
        preview_url=track.preview_url,
        album_art_url=track.album_art_url,
        release_date=release,
        duration_ms=track.duration_ms,
    )
    db.add(song)
    await db.flush()
    return song
