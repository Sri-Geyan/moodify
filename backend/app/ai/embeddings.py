"""Embedding generation using HuggingFace Inference API with sentence-transformers."""

from huggingface_hub import AsyncInferenceClient
from app.core.config import get_settings
from app.ai.schemas import MoodProfile

settings = get_settings()

# Initialize HuggingFace Inference client for embeddings
hf_client = AsyncInferenceClient(
    model=settings.hf_embedding_model,
    token=settings.huggingface_api_token,
)


def _build_embedding_text(
    song_name: str,
    artist: str,
    mood_profile: MoodProfile,
    lyrics_excerpt: str | None = None,
) -> str:
    """
    Build composite text for embedding that captures emotional AND sonic qualities.

    This is the key insight: we embed a rich text description, not just raw lyrics.
    The embedding captures mood, themes, atmosphere, and genre context all at once.
    """
    parts = [
        f"Song: {song_name} by {artist}.",
        f"Moods: {', '.join(mood_profile.moods)}.",
        f"Themes: {', '.join(mood_profile.themes)}.",
        f"Atmosphere: {', '.join(mood_profile.atmosphere)}.",
        f"Genres: {', '.join(mood_profile.genre_tags)}.",
        f"Emotional character: {mood_profile.description}",
    ]

    if lyrics_excerpt:
        # Include first ~500 chars of lyrics for additional semantic signal
        parts.append(f"Lyrics excerpt: {lyrics_excerpt[:500]}")

    return " ".join(parts)


async def generate_embedding(
    song_name: str,
    artist: str,
    mood_profile: MoodProfile,
    lyrics: str | None = None,
) -> list[float]:
    """
    Generate a vector embedding for a song using HuggingFace sentence-transformers.

    The embedding captures the song's emotional and thematic fingerprint by combining
    mood tags, themes, atmosphere, genres, and lyrics into a single vector.
    """
    text = _build_embedding_text(song_name, artist, mood_profile, lyrics)

    try:
        embedding = await hf_client.feature_extraction(text)

        # HF returns nested list for single input — flatten
        if isinstance(embedding, list):
            if isinstance(embedding[0], list):
                return embedding[0]
            return embedding

        return list(embedding)

    except Exception as e:
        print(f"Embedding generation failed: {e}")
        raise


async def generate_query_embedding(
    mood_profile: MoodProfile,
    mood_adjustments: dict | None = None,
) -> list[float]:
    """
    Generate a query embedding for similarity search.

    Optionally applies mood adjustments from user sliders or NLP input
    by modifying the text representation before embedding.
    """
    # Start with mood profile text
    parts = [
        f"Looking for songs with moods: {', '.join(mood_profile.moods)}.",
        f"Themes: {', '.join(mood_profile.themes)}.",
        f"Atmosphere: {', '.join(mood_profile.atmosphere)}.",
        f"Genres: {', '.join(mood_profile.genre_tags)}.",
        mood_profile.description,
    ]

    # Apply NLP adjustments if provided
    if mood_adjustments:
        if mood_adjustments.get("add_moods"):
            parts.append(f"Also include moods: {', '.join(mood_adjustments['add_moods'])}.")
        if mood_adjustments.get("add_themes"):
            parts.append(f"Also include themes: {', '.join(mood_adjustments['add_themes'])}.")
        if mood_adjustments.get("add_atmosphere"):
            parts.append(f"Atmosphere should also feel: {', '.join(mood_adjustments['add_atmosphere'])}.")

    text = " ".join(parts)

    try:
        embedding = await hf_client.feature_extraction(text)

        if isinstance(embedding, list):
            if isinstance(embedding[0], list):
                return embedding[0]
            return embedding

        return list(embedding)

    except Exception as e:
        print(f"Query embedding generation failed: {e}")
        raise
