"""Song router — search and metadata endpoints."""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.songs import service as song_service
from app.songs.schemas import SearchResults, SongResponse
from app.core.database import get_db
from app.core.security import verify_session_token

router = APIRouter(prefix="/songs", tags=["Songs"])


def _get_access_token(request: Request) -> str:
    """Extract Spotify access token from session."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_data = verify_session_token(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_data["access_token"]


@router.get("/search", response_model=SearchResults)
async def search_songs(q: str, request: Request, limit: int = 10):
    """Search for songs on Spotify."""
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    access_token = _get_access_token(request)

    try:
        tracks = await song_service.search_spotify(q, access_token, limit=limit)
        return SearchResults(query=q, tracks=tracks, total=len(tracks))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Spotify search failed: {str(e)}")


@router.get("/{spotify_id}", response_model=SongResponse)
async def get_song(
    spotify_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific song."""
    access_token = _get_access_token(request)

    try:
        # Fetch from Spotify
        track = await song_service.get_track_details(spotify_id, access_token)

        # Store/retrieve from DB
        song = await song_service.get_or_create_song(db, track)

        return SongResponse(
            spotify_id=song.spotify_id,
            name=song.name,
            artist=song.artist,
            album=song.album,
            album_art_url=song.album_art_url,
            preview_url=song.preview_url,
            popularity=song.popularity,
            genres=song.genres or [],
            release_date=song.release_date,
            has_lyrics=song.lyrics is not None,
            has_mood_profile=song.mood_profile is not None,
            has_embedding=song.has_embedding,
            mood_profile=song.mood_profile,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to get song: {str(e)}")
