"""
Seeder pipeline — batch process songs: fetch → lyrics → analyze → embed → store.

Run this script to populate the vector database with pre-computed embeddings.
Usage: python -m app.seeder.pipeline
"""

import asyncio
import httpx
import time
from app.core.config import get_settings
from app.core.database import async_session_factory, init_db
from app.songs.models import Song
from app.songs.schemas import SpotifyTrack
from app.songs import service as song_service
from app.lyrics import service as lyrics_service
from app.ai.mood_extractor import extract_mood
from app.ai.embeddings import generate_embedding
from app.vectors import service as vector_service
from app.vectors.client import init_qdrant
from app.seeder.sources import SEED_PLAYLISTS
from sqlalchemy import select

settings = get_settings()

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def get_client_token() -> str:
    """Get a Spotify access token using client credentials flow (no user auth needed)."""
    import base64
    credentials = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def fetch_playlist_tracks(
    playlist_id: str, access_token: str, limit: int = 50
) -> list[SpotifyTrack]:
    """Fetch tracks from a Spotify playlist."""
    tracks = []
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks",
            params={"limit": limit, "fields": "items(track(id,name,artists,album,popularity,preview_url,duration_ms))"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            print(f"  ⚠ Failed to fetch playlist {playlist_id}: {response.status_code}")
            return []

        data = response.json()
        for item in data.get("items", []):
            track = item.get("track")
            if not track or not track.get("id"):
                continue

            artists = ", ".join(a["name"] for a in track.get("artists", []))
            images = track.get("album", {}).get("images", [])
            album_art = images[0]["url"] if images else None

            # Fetch artist genres
            artist_id = track["artists"][0]["id"] if track.get("artists") else None
            genres = []
            if artist_id:
                try:
                    artist_resp = await client.get(
                        f"{SPOTIFY_API_BASE}/artists/{artist_id}",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if artist_resp.status_code == 200:
                        genres = artist_resp.json().get("genres", [])
                except Exception:
                    pass

            tracks.append(SpotifyTrack(
                spotify_id=track["id"],
                name=track["name"],
                artist=artists,
                album=track.get("album", {}).get("name"),
                album_art_url=album_art,
                preview_url=track.get("preview_url"),
                popularity=track.get("popularity", 0),
                duration_ms=track.get("duration_ms"),
                genres=genres,
            ))

            # Rate limit: Spotify allows ~30 req/s but let's be conservative
            await asyncio.sleep(0.1)

    return tracks


async def process_song(db_session, track: SpotifyTrack) -> bool:
    """Process a single song through the full pipeline."""
    try:
        # Check if already processed
        result = await db_session.execute(
            select(Song).where(Song.spotify_id == track.spotify_id)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.has_embedding:
            return False  # Already done

        # Create or get song
        song = await song_service.get_or_create_song(db_session, track)

        # Fetch lyrics
        if not song.lyrics:
            lyrics, source = await lyrics_service.get_lyrics(
                track.name, track.artist, track.album
            )
            if lyrics:
                song.lyrics = lyrics
                song.lyrics_source = source

        # Extract mood
        mood_profile = await extract_mood(
            lyrics=song.lyrics or "",
            artist=track.artist,
            song_name=track.name,
            genres=track.genres,
        )
        song.mood_profile = mood_profile.model_dump()

        # Generate embedding
        embedding = await generate_embedding(
            song_name=track.name,
            artist=track.artist,
            mood_profile=mood_profile,
            lyrics=song.lyrics,
        )

        # Store in Qdrant
        await vector_service.upsert_song_vector(
            song_id=str(song.id),
            spotify_id=song.spotify_id,
            embedding=embedding,
            payload={
                "name": song.name,
                "artist": song.artist,
                "album": song.album,
                "genres": song.genres or [],
                "popularity": song.popularity,
                "moods": mood_profile.moods,
                "themes": mood_profile.themes,
                "atmosphere": mood_profile.atmosphere,
                "album_art_url": song.album_art_url,
                "preview_url": song.preview_url,
            },
        )
        song.has_embedding = True

        await db_session.commit()
        return True

    except Exception as e:
        print(f"  ✗ Error processing {track.name}: {e}")
        await db_session.rollback()
        return False


async def run_seeder(max_playlists: int | None = None, tracks_per_playlist: int = 30):
    """Run the full seeding pipeline."""
    print("🌱 Starting Spotify AI Playlist Seeder")
    print("=" * 50)

    # Initialize infrastructure
    await init_db()
    await init_qdrant()

    # Get Spotify token
    access_token = await get_client_token()
    print("✓ Spotify access token obtained")

    playlists = SEED_PLAYLISTS[:max_playlists] if max_playlists else SEED_PLAYLISTS
    total_processed = 0
    total_skipped = 0
    total_errors = 0

    for i, (playlist_id, genre, description) in enumerate(playlists):
        print(f"\n📋 [{i+1}/{len(playlists)}] Processing: {description} ({genre})")

        # Fetch tracks
        tracks = await fetch_playlist_tracks(
            playlist_id, access_token, limit=tracks_per_playlist
        )
        print(f"  Found {len(tracks)} tracks")

        for j, track in enumerate(tracks):
            async with async_session_factory() as session:
                success = await process_song(session, track)

            if success:
                total_processed += 1
                print(f"  ✓ [{j+1}/{len(tracks)}] {track.name} by {track.artist}")
            else:
                total_skipped += 1

            # Rate limiting for HuggingFace + Genius APIs
            await asyncio.sleep(1.5)

        # Refresh token every 10 playlists (tokens expire in ~1hr)
        if (i + 1) % 10 == 0:
            try:
                access_token = await get_client_token()
                print("  ✓ Refreshed Spotify token")
            except Exception:
                pass

    # Final stats
    db_count = await vector_service.get_collection_count()
    print(f"\n{'=' * 50}")
    print(f"🎉 Seeding complete!")
    print(f"  Processed: {total_processed}")
    print(f"  Skipped (already done): {total_skipped}")
    print(f"  Total vectors in DB: {db_count}")


if __name__ == "__main__":
    asyncio.run(run_seeder())
