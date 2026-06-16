"""Recommendation router — the main playlist generation endpoint."""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_session_token
from app.songs import service as song_service
from app.lyrics import service as lyrics_service
from app.ai.mood_extractor import extract_mood, interpret_nlp_query
from app.ai.embeddings import generate_embedding, generate_query_embedding
from app.ai.schemas import MoodProfile
from app.vectors import service as vector_service
from app.recommendations.engine import compute_hybrid_scores, enforce_diversity
from app.recommendations.explainer import generate_quick_explanation
from app.recommendations.schemas import (
    RecommendRequest,
    RecommendResponse,
    RecommendedTrack,
)

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


def _get_session_data(request: Request) -> dict:
    """Extract and verify session data from auth header."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_data = verify_session_token(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_data


@router.post("", response_model=RecommendResponse)
async def generate_recommendations(
    body: RecommendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate song recommendations based on a seed song.

    Pipeline:
    1. Fetch seed song metadata from Spotify
    2. Fetch lyrics (Genius → LRCLIB)
    3. Extract mood profile via AI
    4. Generate embedding
    5. Search vector DB for similar songs
    6. Apply hybrid scoring
    7. Enforce diversity
    8. Generate explanations
    """
    session_data = _get_session_data(request)
    access_token = session_data["access_token"]

    # --- Step 1: Get seed song details ---
    try:
        track = await song_service.get_track_details(
            body.seed_spotify_id, access_token
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch song: {str(e)}")

    # Store/retrieve song in DB
    song = await song_service.get_or_create_song(db, track)

    # --- Step 2: Fetch lyrics if not cached ---
    if not song.lyrics:
        lyrics, source = await lyrics_service.get_lyrics(
            track.name, track.artist, track.album
        )
        if lyrics:
            song.lyrics = lyrics
            song.lyrics_source = source
            await db.flush()

    # --- Step 3: Extract mood profile ---
    if not song.mood_profile:
        mood_profile = await extract_mood(
            lyrics=song.lyrics or "",
            artist=track.artist,
            song_name=track.name,
            genres=track.genres,
        )
        song.mood_profile = mood_profile.model_dump()
        await db.flush()
    else:
        mood_profile = MoodProfile(**song.mood_profile)

    # --- Step 4: Generate embedding and store in vector DB ---
    if not song.has_embedding:
        embedding = await generate_embedding(
            song_name=track.name,
            artist=track.artist,
            mood_profile=mood_profile,
            lyrics=song.lyrics,
        )
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
        await db.flush()

    # --- Step 5: Handle NLP query adjustments ---
    mood_adjustments = body.mood_adjustments
    if body.natural_language_prompt:
        nlp_result = await interpret_nlp_query(
            body.natural_language_prompt, mood_profile
        )
        mood_adjustments = nlp_result

    # --- Step 6: Generate query embedding ---
    query_embedding = await generate_query_embedding(
        mood_profile=mood_profile,
        mood_adjustments=mood_adjustments,
    )

    # --- Step 7: Vector search ---
    candidates = await vector_service.search_similar(
        query_vector=query_embedding,
        limit=50,
        exclude_spotify_id=body.seed_spotify_id,
    )

    # --- Step 8: Hybrid scoring ---
    scored = compute_hybrid_scores(
        candidates=candidates,
        seed_genres=track.genres,
        seed_moods=mood_profile.moods,
        seed_popularity=track.popularity,
    )

    # --- Step 9: Diversity enforcement ---
    diverse = enforce_diversity(
        scored_candidates=scored,
        max_per_artist=2,
        min_unique_artists=3,
        target_count=body.playlist_length,
    )

    # --- Step 10: Generate explanations ---
    recommended_tracks = []
    for candidate in diverse:
        explanation = generate_quick_explanation(
            seed_moods=mood_profile.moods,
            seed_themes=mood_profile.themes,
            candidate_moods=candidate.get("moods", []),
            candidate_themes=candidate.get("themes", []),
            candidate_atmosphere=candidate.get("atmosphere", []),
            genre_similarity=candidate.get("genre_similarity", 0.0),
            embedding_similarity=candidate.get("embedding_similarity", 0.0),
        )

        recommended_tracks.append(RecommendedTrack(
            spotify_id=candidate["spotify_id"],
            name=candidate["name"],
            artist=candidate["artist"],
            album=candidate.get("album", ""),
            album_art_url=candidate.get("album_art_url", ""),
            preview_url=candidate.get("preview_url", ""),
            popularity=candidate.get("popularity", 0),
            genres=candidate.get("genres", []),
            moods=candidate.get("moods", []),
            themes=candidate.get("themes", []),
            atmosphere=candidate.get("atmosphere", []),
            hybrid_score=candidate["hybrid_score"],
            embedding_similarity=candidate["embedding_similarity"],
            genre_similarity=candidate["genre_similarity"],
            artist_similarity=candidate["artist_similarity"],
            popularity_similarity=candidate["popularity_similarity"],
            explanation=explanation,
        ))

    # Get vector DB size for display
    db_size = await vector_service.get_collection_count()

    return RecommendResponse(
        seed_song={
            "spotify_id": song.spotify_id,
            "name": song.name,
            "artist": song.artist,
            "album": song.album,
            "album_art_url": song.album_art_url,
            "popularity": song.popularity,
            "genres": song.genres or [],
        },
        seed_mood_profile=mood_profile,
        tracks=recommended_tracks,
        total_candidates=len(scored),
        vector_db_size=db_size,
        natural_language_prompt=body.natural_language_prompt,
    )
