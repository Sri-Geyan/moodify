"""Auth router — Spotify OAuth endpoints."""

import secrets
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from app.auth import service as auth_service
from app.auth.schemas import AuthStatus
from app.core.config import get_settings
from app.core.security import create_session_token, verify_session_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.get("/login")
async def login():
    """Redirect user to Spotify authorization page."""
    state = secrets.token_urlsafe(32)
    auth_url = auth_service.get_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str, response: Response):
    """Handle Spotify OAuth callback — exchange code for tokens."""
    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_code(code)

        # Fetch user profile
        user_profile = await auth_service.get_user_profile(token_data.access_token)

        # Create session token with user data + Spotify tokens
        session_data = {
            "spotify_id": user_profile.id,
            "display_name": user_profile.display_name,
            "email": user_profile.email,
            "access_token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
        }
        session_token = create_session_token(session_data)

        # Redirect to frontend with session token
        redirect_url = f"{settings.frontend_url}?auth=success&token={session_token}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        redirect_url = f"{settings.frontend_url}?auth=error&message={str(e)}"
        return RedirectResponse(url=redirect_url)


@router.get("/me", response_model=AuthStatus)
async def get_current_user(request: Request):
    """Get the current authenticated user's info."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return AuthStatus(authenticated=False)

    session_data = verify_session_token(token)
    if not session_data:
        return AuthStatus(authenticated=False)

    try:
        # Use stored access token to get fresh profile
        profile = await auth_service.get_user_profile(session_data["access_token"])
        return AuthStatus(authenticated=True, user=profile)
    except Exception:
        return AuthStatus(authenticated=False)


@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh an expired Spotify access token."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_data = verify_session_token(token)

    if not session_data or "refresh_token" not in session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    try:
        new_tokens = await auth_service.refresh_access_token(
            session_data["refresh_token"]
        )
        # Update session with new access token
        session_data["access_token"] = new_tokens.access_token
        if new_tokens.refresh_token:
            session_data["refresh_token"] = new_tokens.refresh_token

        new_session_token = create_session_token(session_data)
        return {"token": new_session_token, "expires_in": new_tokens.expires_in}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")


@router.get("/logout")
async def logout():
    """Clear session (client-side token removal)."""
    return {"message": "Logged out successfully"}
