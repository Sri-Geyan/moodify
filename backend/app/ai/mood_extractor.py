"""Mood extraction using HuggingFace Inference API with Mistral."""

import json
import re
from huggingface_hub import AsyncInferenceClient
from app.core.config import get_settings
from app.ai.schemas import MoodProfile
from app.ai.prompts import MOOD_EXTRACTION_PROMPT, NLP_QUERY_PROMPT

settings = get_settings()

# Initialize HuggingFace Inference client
hf_client = AsyncInferenceClient(
    model=settings.hf_llm_model,
    token=settings.huggingface_api_token,
)


def _extract_json(text: str) -> dict:
    """Extract JSON object from LLM response, handling markdown fences and extra text."""
    # Try to find JSON in code fences first
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1))

    # Try to find a JSON object directly
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))

    raise ValueError(f"No valid JSON found in response: {text[:200]}")


async def extract_mood(
    lyrics: str,
    artist: str,
    song_name: str,
    genres: list[str] | None = None,
) -> MoodProfile:
    """
    Extract mood profile from song lyrics using HuggingFace LLM.

    Uses Mistral-7B-Instruct via HuggingFace Inference API (free tier).
    """
    # Truncate lyrics to ~1500 chars to fit context window
    lyrics_excerpt = lyrics[:1500] if lyrics else "No lyrics available."

    genre_info = f"Genres: {', '.join(genres)}" if genres else "Genres: unknown"

    user_message = f"""Analyze this song:

Song: "{song_name}" by {artist}
{genre_info}

Lyrics:
{lyrics_excerpt}"""

    try:
        response = await hf_client.text_generation(
            prompt=f"<s>[INST] {MOOD_EXTRACTION_PROMPT}\n\n{user_message} [/INST]",
            max_new_tokens=600,
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.1,
        )

        data = _extract_json(response)
        return MoodProfile(**data)

    except Exception as e:
        print(f"Mood extraction failed: {e}")
        # Return a sensible default based on available info
        return MoodProfile(
            moods=["unknown"],
            themes=["unanalyzed"],
            atmosphere=["neutral"],
            emotional_intensity=0.5,
            energy_level=0.5,
            valence=0.5,
            genre_tags=genres or [],
            description=f"Analysis pending for '{song_name}' by {artist}.",
        )


async def interpret_nlp_query(query: str, seed_mood: MoodProfile) -> dict:
    """
    Interpret a natural language playlist query.

    Example: "songs like Hope but more upbeat" → mood adjustments
    """
    user_message = f"""User query: "{query}"

The seed song has these moods: {seed_mood.moods}
Themes: {seed_mood.themes}
Atmosphere: {seed_mood.atmosphere}
Current valence: {seed_mood.valence}
Current energy: {seed_mood.energy_level}
Current intensity: {seed_mood.emotional_intensity}

What mood adjustments is the user requesting?"""

    try:
        response = await hf_client.text_generation(
            prompt=f"<s>[INST] {NLP_QUERY_PROMPT}\n\n{user_message} [/INST]",
            max_new_tokens=300,
            temperature=0.3,
            top_p=0.9,
        )

        return _extract_json(response)

    except Exception as e:
        print(f"NLP query interpretation failed: {e}")
        return {
            "mood_shifts": {"valence": 0.0, "energy": 0.0, "intensity": 0.0},
            "add_moods": [],
            "add_themes": [],
            "add_atmosphere": [],
            "interpretation": query,
        }
