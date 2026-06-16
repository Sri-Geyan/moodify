"""Playlist service — create and manage Spotify playlists."""

import httpx

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def create_spotify_playlist(
    access_token: str,
    user_id: str,
    name: str,
    description: str = "",
    public: bool = True,
    track_uris: list[str] | None = None,
) -> dict:
    """
    Create a new playlist on the user's Spotify account and add tracks.

    Args:
        access_token: Spotify OAuth access token
        user_id: Spotify user ID
        name: Playlist name
        description: Playlist description
        public: Whether the playlist is public
        track_uris: List of Spotify track URIs to add (e.g., ["spotify:track:ABC123"])

    Returns:
        Dict with playlist_id, playlist_url, name, track_count, snapshot_id
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Create the playlist
        create_response = await client.post(
            f"{SPOTIFY_API_BASE}/users/{user_id}/playlists",
            json={
                "name": name,
                "description": description,
                "public": public,
            },
            headers=headers,
        )
        create_response.raise_for_status()
        playlist_data = create_response.json()

        playlist_id = playlist_data["id"]
        snapshot_id = playlist_data.get("snapshot_id", "")

        # Step 2: Add tracks in batches of 100 (Spotify limit)
        if track_uris:
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i + 100]
                add_response = await client.post(
                    f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks",
                    json={"uris": batch},
                    headers=headers,
                )
                add_response.raise_for_status()
                result = add_response.json()
                snapshot_id = result.get("snapshot_id", snapshot_id)

    return {
        "playlist_id": playlist_id,
        "playlist_url": playlist_data.get("external_urls", {}).get("spotify", ""),
        "name": name,
        "track_count": len(track_uris) if track_uris else 0,
        "snapshot_id": snapshot_id,
    }
