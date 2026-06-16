"""Lyrics service — fetch lyrics from Genius (primary) and LRCLIB (fallback)."""

import re
import httpx
import lyricsgenius
from app.core.config import get_settings

settings = get_settings()

# LRCLIB API base
LRCLIB_BASE = "https://lrclib.net/api"


def _clean_lyrics(raw_lyrics: str) -> str:
    """Clean raw lyrics text — remove annotations, headers, and excess whitespace."""
    if not raw_lyrics:
        return ""

    # Remove content in square brackets like [Verse 1], [Chorus], etc.
    text = re.sub(r"\[.*?\]", "", raw_lyrics)

    # Remove "XXXContributor" style Genius annotations
    text = re.sub(r"\d+\s*Contributors?.*?\n", "", text)

    # Remove "Embed" footer that Genius appends
    text = re.sub(r"\d*Embed$", "", text, flags=re.MULTILINE)

    # Remove "You might also like" Genius artifacts
    text = text.replace("You might also like", "")

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


async def fetch_from_genius(track_name: str, artist_name: str) -> str | None:
    """Fetch lyrics from Genius API using lyricsgenius library."""
    try:
        genius = lyricsgenius.Genius(
            settings.genius_access_token,
            timeout=15,
            retries=2,
            remove_section_headers=True,
            skip_non_songs=True,
            verbose=False,
        )

        # Search for the song
        song = genius.search_song(track_name, artist_name)
        if song and song.lyrics:
            return _clean_lyrics(song.lyrics)

        return None
    except Exception as e:
        print(f"Genius lyrics fetch failed: {e}")
        return None


async def fetch_from_lrclib(
    track_name: str, artist_name: str, album_name: str | None = None
) -> str | None:
    """Fetch lyrics from LRCLIB (free, community-driven) as fallback."""
    try:
        params = {
            "track_name": track_name,
            "artist_name": artist_name,
        }
        if album_name:
            params["album_name"] = album_name

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LRCLIB_BASE}/get",
                params=params,
                headers={"User-Agent": "SpotifyAIPlaylistGen/1.0"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                # Prefer plain lyrics, fall back to synced lyrics
                lyrics = data.get("plainLyrics") or data.get("syncedLyrics")
                if lyrics:
                    return _clean_lyrics(lyrics)

        return None
    except Exception as e:
        print(f"LRCLIB lyrics fetch failed: {e}")
        return None


async def get_lyrics(
    track_name: str, artist_name: str, album_name: str | None = None
) -> tuple[str | None, str | None]:
    """
    Fetch lyrics using multi-provider strategy.

    Returns:
        Tuple of (lyrics_text, source_name) or (None, None) if not found.
    """
    # Try Genius first (larger catalog, better for hip-hop/rap)
    lyrics = await fetch_from_genius(track_name, artist_name)
    if lyrics and len(lyrics) > 50:  # Ensure we got actual lyrics, not just metadata
        return lyrics, "genius"

    # Fallback to LRCLIB
    lyrics = await fetch_from_lrclib(track_name, artist_name, album_name)
    if lyrics and len(lyrics) > 50:
        return lyrics, "lrclib"

    return None, None
