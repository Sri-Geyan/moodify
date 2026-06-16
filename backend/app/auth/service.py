"""Spotify OAuth service — token exchange, refresh, and profile fetching."""

import httpx
import base64
from urllib.parse import urlencode
from app.core.config import get_settings
from app.auth.schemas import SpotifyTokenResponse, SpotifyUserProfile

settings = get_settings()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SCOPES = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-private",
    "user-read-email",
]


def get_auth_url(state: str) -> str:
    """Build the Spotify authorization URL."""
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "show_dialog": "true",
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def _get_auth_header() -> str:
    """Base64 encode client credentials for token requests."""
    credentials = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    return base64.b64encode(credentials.encode()).decode()


async def exchange_code(code: str) -> SpotifyTokenResponse:
    """Exchange authorization code for access and refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            headers={
                "Authorization": f"Basic {_get_auth_header()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()
        return SpotifyTokenResponse(**response.json())


async def refresh_access_token(refresh_token: str) -> SpotifyTokenResponse:
    """Use refresh token to get a new access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={
                "Authorization": f"Basic {_get_auth_header()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()
        return SpotifyTokenResponse(**response.json())


async def get_user_profile(access_token: str) -> SpotifyUserProfile:
    """Fetch the current user's Spotify profile."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return SpotifyUserProfile(**response.json())
