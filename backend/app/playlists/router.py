"""Playlist router — create and export playlists to Spotify."""

from fastapi import APIRouter, HTTPException, Request
from app.core.security import verify_session_token
from app.playlists import service as playlist_service
from app.playlists.schemas import CreatePlaylistRequest, PlaylistResponse

router = APIRouter(prefix="/playlists", tags=["Playlists"])


def _get_session_data(request: Request) -> dict:
    """Extract and verify session data from auth header."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_data = verify_session_token(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_data


@router.post("/create", response_model=PlaylistResponse)
async def create_playlist(body: CreatePlaylistRequest, request: Request):
    """Create a playlist on the user's Spotify account."""
    session_data = _get_session_data(request)

    # Build playlist name and description
    name = body.name or f"AI Mix: Songs like {body.seed_song_name}"
    description = body.description or (
        f"🤖 AI-generated playlist inspired by \"{body.seed_song_name}\" "
        f"by {body.seed_artist}. Created with Spotify AI Playlist Generator."
    )

    # Convert track IDs to Spotify URIs
    track_uris = [f"spotify:track:{tid}" for tid in body.track_spotify_ids]

    try:
        result = await playlist_service.create_spotify_playlist(
            access_token=session_data["access_token"],
            user_id=session_data["spotify_id"],
            name=name,
            description=description,
            public=body.public,
            track_uris=track_uris,
        )
        return PlaylistResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to create Spotify playlist: {str(e)}"
        )
