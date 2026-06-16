"""Explainer — generate human-readable reasons for song recommendations."""

from huggingface_hub import InferenceClient
from app.core.config import get_settings
from app.ai.prompts import PLAYLIST_EXPLANATION_PROMPT

settings = get_settings()

hf_client = InferenceClient(
    model=settings.hf_llm_model,
    token=settings.huggingface_api_token,
)


def generate_quick_explanation(
    seed_moods: list[str],
    seed_themes: list[str],
    candidate_moods: list[str],
    candidate_themes: list[str],
    candidate_atmosphere: list[str],
    genre_similarity: float,
    embedding_similarity: float,
) -> str:
    """
    Generate a quick rule-based explanation without calling the LLM.

    Uses overlap analysis between seed and candidate mood profiles.
    This is faster and doesn't consume API quota.
    """
    shared_moods = set(m.lower() for m in seed_moods) & set(m.lower() for m in candidate_moods)
    shared_themes = set(t.lower() for t in seed_themes) & set(t.lower() for t in candidate_themes)

    parts = []

    if shared_moods:
        mood_str = ", ".join(list(shared_moods)[:3])
        parts.append(f"shares a **{mood_str}** emotional tone")

    if shared_themes:
        theme_str = ", ".join(list(shared_themes)[:2])
        parts.append(f"explores similar themes of **{theme_str}**")

    if candidate_atmosphere:
        parts.append(f"has a **{candidate_atmosphere[0]}** atmosphere")

    if genre_similarity > 0.5:
        parts.append("lives in a similar genre space")
    elif genre_similarity > 0.2:
        parts.append("crosses genre boundaries in a complementary way")

    if not parts:
        if embedding_similarity > 0.7:
            return "Strong overall emotional and sonic similarity detected."
        return "Selected based on deep embedding similarity analysis."

    explanation = "Selected because it " + ", and ".join(parts) + "."
    return explanation


async def generate_llm_explanation(
    seed_name: str,
    seed_artist: str,
    seed_moods: list[str],
    seed_themes: list[str],
    candidate_name: str,
    candidate_artist: str,
    candidate_moods: list[str],
    candidate_themes: list[str],
) -> str:
    """
    Generate an AI-powered explanation using the HuggingFace LLM.

    More natural and engaging than rule-based, but slower and uses API quota.
    Use sparingly — e.g., for top 5 recommendations only.
    """
    user_message = f"""Seed song: "{seed_name}" by {seed_artist}
Seed moods: {', '.join(seed_moods)}
Seed themes: {', '.join(seed_themes)}

Recommended song: "{candidate_name}" by {candidate_artist}
Recommended moods: {', '.join(candidate_moods)}
Recommended themes: {', '.join(candidate_themes)}

Why was this song recommended?"""

    try:
        response = hf_client.text_generation(
            prompt=f"<s>[INST] {PLAYLIST_EXPLANATION_PROMPT}\n\n{user_message} [/INST]",
            max_new_tokens=150,
            temperature=0.5,
            top_p=0.9,
        )
        return response.strip().strip('"')
    except Exception as e:
        # Fall back to rule-based
        return generate_quick_explanation(
            seed_moods, seed_themes,
            candidate_moods, candidate_themes,
            [], 0.0, 0.0
        )
