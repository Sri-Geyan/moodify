"""Qdrant vector operations — upsert and search."""

from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from app.vectors.client import get_qdrant
from app.core.config import get_settings

settings = get_settings()


async def upsert_song_vector(
    song_id: str,
    spotify_id: str,
    embedding: list[float],
    payload: dict,
):
    """Store a song's embedding vector in Qdrant with metadata payload."""
    client = await get_qdrant()

    # Use a deterministic integer ID from spotify_id hash
    point_id = abs(hash(spotify_id)) % (2**63)

    await client.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "song_id": str(song_id),
                    "spotify_id": spotify_id,
                    "name": payload.get("name", ""),
                    "artist": payload.get("artist", ""),
                    "album": payload.get("album", ""),
                    "genres": payload.get("genres", []),
                    "popularity": payload.get("popularity", 0),
                    "moods": payload.get("moods", []),
                    "themes": payload.get("themes", []),
                    "atmosphere": payload.get("atmosphere", []),
                    "album_art_url": payload.get("album_art_url", ""),
                    "preview_url": payload.get("preview_url", ""),
                },
            )
        ],
    )


async def search_similar(
    query_vector: list[float],
    limit: int = 50,
    exclude_spotify_id: str | None = None,
) -> list[dict]:
    """
    Search for the most similar songs by embedding vector.

    Returns top-K results with similarity scores and payloads.
    """
    client = await get_qdrant()

    # Build exclusion filter if needed
    query_filter = None
    if exclude_spotify_id:
        # Qdrant doesn't have a "not equal" for search directly in basic filter,
        # so we'll filter post-search
        pass

    results = await client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit + 5,  # Fetch extra in case we need to filter
        with_payload=True,
        score_threshold=0.1,  # Minimum similarity
    )

    # Format results and exclude the seed song
    formatted = []
    for hit in results:
        payload = hit.payload or {}
        if exclude_spotify_id and payload.get("spotify_id") == exclude_spotify_id:
            continue

        formatted.append({
            "spotify_id": payload.get("spotify_id", ""),
            "song_id": payload.get("song_id", ""),
            "name": payload.get("name", ""),
            "artist": payload.get("artist", ""),
            "album": payload.get("album", ""),
            "genres": payload.get("genres", []),
            "popularity": payload.get("popularity", 0),
            "moods": payload.get("moods", []),
            "themes": payload.get("themes", []),
            "atmosphere": payload.get("atmosphere", []),
            "album_art_url": payload.get("album_art_url", ""),
            "preview_url": payload.get("preview_url", ""),
            "embedding_similarity": float(hit.score),
        })

    return formatted[:limit]


async def get_collection_count() -> int:
    """Get the number of vectors in the collection."""
    client = await get_qdrant()
    info = await client.get_collection(settings.qdrant_collection)
    return info.points_count or 0
