"""Curated Spotify playlist IDs for seeding the vector database."""

# Each entry: (playlist_id, genre_category, description)
# These are Spotify editorial playlists with broad genre coverage
SEED_PLAYLISTS = [
    # --- Pop ---
    ("37i9dQZF1DXcBWIGoYBM5M", "pop", "Today's Top Hits"),
    ("37i9dQZF1DX0kbJZpiYdZl", "pop", "Hot Hits USA"),

    # --- Hip-Hop / Rap ---
    ("37i9dQZF1DX0XUsuxWHRQd", "hip-hop", "RapCaviar"),
    ("37i9dQZF1DX2RxBh64BHjQ", "hip-hop", "Most Necessary"),
    ("37i9dQZF1DWY4xHQp97fN6", "emo-rap", "Get Turnt"),

    # --- R&B / Soul ---
    ("37i9dQZF1DX4SBhb3fqCJd", "rnb", "Are & Be"),
    ("37i9dQZF1DWYbLCm0Z0QGr", "rnb", "R&B Favourites"),

    # --- Rock / Alternative ---
    ("37i9dQZF1DX1lVhptIYRda", "rock", "Hot Hits Rock"),
    ("37i9dQZF1DXcF6B6QPhFDv", "rock", "Rock This"),
    ("37i9dQZF1DX873GaRGUmPl", "indie", "Alternative Hip-Hop"),

    # --- Electronic / Dance ---
    ("37i9dQZF1DX4dyzvuaRJ0n", "electronic", "mint"),
    ("37i9dQZF1DXa8NOEUOYkr0", "electronic", "Electronic Essentials"),

    # --- Lo-Fi / Chill ---
    ("37i9dQZF1DWWQRwui0ExPn", "lofi", "Lo-Fi Beats"),
    ("37i9dQZF1DX4WYpdgoIcn6", "chill", "Chill Hits"),

    # --- Sad / Emotional ---
    ("37i9dQZF1DX7qK8ma5wgG1", "sad", "Sad Songs"),
    ("37i9dQZF1DX3YSRoSdA634", "sad", "Life Sucks"),
    ("37i9dQZF1DWVV27DiNWxkR", "sad", "Sad Bops"),

    # --- Mood: Night ---
    ("37i9dQZF1DX2pSTOxoPbx9", "night", "Late Night Vibes"),
    ("37i9dQZF1DXbcPC6Vvqudd", "night", "Night Rider"),

    # --- Mood: Motivational ---
    ("37i9dQZF1DXdxcBWuJkbcy", "motivational", "Get Motivated!"),
    ("37i9dQZF1DX35X4JNyBWtb", "motivational", "Motivation Mix"),

    # --- Country ---
    ("37i9dQZF1DX1lVhptIYRda", "country", "Hot Country"),

    # --- Latin ---
    ("37i9dQZF1DX10zKzsJ2jva", "latin", "Viva Latino"),

    # --- Decades ---
    ("37i9dQZF1DX4o1oenSJRJd", "2010s", "All Out 2010s"),
    ("37i9dQZF1DXbTxeAdrVG2l", "2000s", "All Out 2000s"),
]
