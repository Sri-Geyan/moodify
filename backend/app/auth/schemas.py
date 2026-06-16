"""Pydantic schemas for authentication."""

from pydantic import BaseModel
from typing import Optional


class SpotifyTokenResponse(BaseModel):
    """Token data received from Spotify OAuth."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str


class SpotifyUserProfile(BaseModel):
    """Spotify user profile data."""
    id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    images: list = []
    product: Optional[str] = None


class AuthStatus(BaseModel):
    """Authentication status response."""
    authenticated: bool
    user: Optional[SpotifyUserProfile] = None
