"""
Recommendation engine — hybrid scoring with diversity enforcement.

Scoring formula:
    score = 0.5 * embedding_similarity
          + 0.2 * genre_similarity
          + 0.2 * artist_similarity
          + 0.1 * popularity_similarity

Diversity constraints:
    - Max 2 songs per artist
    - At least 3 different artists in final playlist
"""

from collections import Counter


def compute_genre_similarity(genres_a: list[str], genres_b: list[str]) -> float:
    """
    Compute genre similarity using Jaccard index.

    Also accounts for partial matches (e.g., "indie rock" partially matches "indie pop").
    """
    if not genres_a or not genres_b:
        return 0.0

    set_a = set(g.lower() for g in genres_a)
    set_b = set(g.lower() for g in genres_b)

    # Exact matches via Jaccard
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    jaccard = intersection / union if union > 0 else 0.0

    # Partial matches — check if individual words overlap
    words_a = set()
    for g in set_a:
        words_a.update(g.split())
    words_b = set()
    for g in set_b:
        words_b.update(g.split())

    word_intersection = len(words_a & words_b)
    word_union = len(words_a | words_b)
    word_jaccard = word_intersection / word_union if word_union > 0 else 0.0

    # Weighted combination: exact matches matter more
    return 0.6 * jaccard + 0.4 * word_jaccard


def compute_artist_similarity(
    seed_genres: list[str],
    seed_moods: list[str],
    candidate_genres: list[str],
    candidate_moods: list[str],
) -> float:
    """
    Compute artist/style similarity based on genre overlap and mood alignment.

    Since we can't rely on Spotify's deprecated "related artists" easily,
    we approximate style similarity through shared genre tags and mood overlap.
    """
    genre_sim = compute_genre_similarity(seed_genres, candidate_genres)

    # Mood overlap
    if seed_moods and candidate_moods:
        mood_set_a = set(m.lower() for m in seed_moods)
        mood_set_b = set(m.lower() for m in candidate_moods)
        mood_intersection = len(mood_set_a & mood_set_b)
        mood_union = len(mood_set_a | mood_set_b)
        mood_sim = mood_intersection / mood_union if mood_union > 0 else 0.0
    else:
        mood_sim = 0.0

    return 0.5 * genre_sim + 0.5 * mood_sim


def compute_popularity_similarity(pop_a: int, pop_b: int) -> float:
    """Compute popularity similarity (1 = identical popularity, 0 = maximum difference)."""
    return 1.0 - abs(pop_a - pop_b) / 100.0


def compute_hybrid_scores(
    candidates: list[dict],
    seed_genres: list[str],
    seed_moods: list[str],
    seed_popularity: int,
) -> list[dict]:
    """
    Apply hybrid scoring formula to all candidates.

    score = 0.5 * embedding + 0.2 * genre + 0.2 * artist + 0.1 * popularity
    """
    scored = []

    for candidate in candidates:
        emb_sim = candidate.get("embedding_similarity", 0.0)
        genre_sim = compute_genre_similarity(
            seed_genres, candidate.get("genres", [])
        )
        artist_sim = compute_artist_similarity(
            seed_genres, seed_moods,
            candidate.get("genres", []), candidate.get("moods", [])
        )
        pop_sim = compute_popularity_similarity(
            seed_popularity, candidate.get("popularity", 0)
        )

        hybrid = (
            0.5 * emb_sim
            + 0.2 * genre_sim
            + 0.2 * artist_sim
            + 0.1 * pop_sim
        )

        candidate["hybrid_score"] = round(hybrid, 4)
        candidate["genre_similarity"] = round(genre_sim, 4)
        candidate["artist_similarity"] = round(artist_sim, 4)
        candidate["popularity_similarity"] = round(pop_sim, 4)
        candidate["embedding_similarity"] = round(emb_sim, 4)

        scored.append(candidate)

    # Sort by hybrid score descending
    scored.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored


def enforce_diversity(
    scored_candidates: list[dict],
    max_per_artist: int = 2,
    min_unique_artists: int = 3,
    target_count: int = 20,
) -> list[dict]:
    """
    Enforce diversity constraints on the scored candidate list.

    Rules:
    1. Maximum `max_per_artist` songs per artist
    2. Ensure at least `min_unique_artists` different artists
    3. Return exactly `target_count` tracks (or all available if fewer)
    """
    artist_counts = Counter()
    selected = []
    deferred = []

    for candidate in scored_candidates:
        artist = candidate.get("artist", "Unknown").lower().strip()

        if artist_counts[artist] < max_per_artist:
            selected.append(candidate)
            artist_counts[artist] += 1
        else:
            deferred.append(candidate)

        if len(selected) >= target_count:
            break

    # If we don't have enough, pull from deferred (relaxing artist constraint)
    if len(selected) < target_count:
        remaining = target_count - len(selected)
        selected.extend(deferred[:remaining])

    # Check minimum unique artists
    unique_artists = len(set(c.get("artist", "").lower() for c in selected))
    if unique_artists < min_unique_artists and len(deferred) > 0:
        # Try to swap in tracks from underrepresented artists
        existing_artists = set(c.get("artist", "").lower() for c in selected)
        for candidate in deferred:
            if candidate.get("artist", "").lower() not in existing_artists:
                # Replace the lowest-scored track from an overrepresented artist
                for i in range(len(selected) - 1, -1, -1):
                    artist = selected[i].get("artist", "").lower()
                    if artist_counts[artist] > 1:
                        selected[i] = candidate
                        artist_counts[artist] -= 1
                        break
                unique_artists += 1
                if unique_artists >= min_unique_artists:
                    break

    return selected[:target_count]
