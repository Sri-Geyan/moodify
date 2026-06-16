# 🎵 Moodify — AI-Powered Spotify Playlist Generator

An AI system that creates emotionally and sonically similar playlists by analyzing a seed song's lyrics, mood, themes, and metadata using open-source HuggingFace models and vector similarity search.

## ✨ How It Works

1. **Authenticate** with your Spotify account
2. **Search** for a seed song (e.g., "Hope" by XXXTENTACION)
3. **AI analyzes** the song's lyrics, mood, themes, and emotional character
4. **Vector search** finds the most similar songs from the database
5. **Hybrid scoring** ranks results using embedding similarity, genre overlap, and more
6. **Export** the playlist directly to your Spotify account

## 🧠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python) |
| **Database** | PostgreSQL (async via SQLAlchemy + asyncpg) |
| **Vector DB** | Qdrant |
| **AI — Mood Extraction** | Mistral-7B via HuggingFace Inference API (free) |
| **AI — Embeddings** | sentence-transformers/all-MiniLM-L6-v2 via HuggingFace (free) |
| **Lyrics** | Genius API + LRCLIB fallback |
| **Auth** | Spotify OAuth (Authorization Code flow) |
| **Frontend** | Vanilla HTML/CSS/JS with premium dark UI |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for PostgreSQL + Qdrant)
- Node.js (optional, for frontend dev server)
- API Keys:
  - [Spotify Developer](https://developer.spotify.com/dashboard) — Client ID + Secret
  - [HuggingFace](https://huggingface.co/settings/tokens) — Free API token
  - [Genius](https://genius.com/api-clients) — Free access token

### 1. Clone & Setup

```bash
cd "Spotify AI Playlist Generator"
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 5. Seed the Vector Database

```bash
cd backend
python -m app.seeder.pipeline
```

### 6. Serve Frontend

```bash
cd frontend
# Use any static file server:
python -m http.server 5173
# Or: npx serve -p 5173
```

### 7. Open the App

Visit `http://localhost:5173` and connect with Spotify!

## 📊 Recommendation Algorithm

### Hybrid Scoring Formula
```
score = 0.50 × embedding_similarity    (emotional/thematic closeness)
      + 0.20 × genre_similarity        (Jaccard index of genre tags)
      + 0.20 × artist_similarity       (style/mood overlap)
      + 0.10 × popularity_similarity   (1 - |pop_a - pop_b| / 100)
```

### Diversity Constraints
- Maximum 2 songs per artist
- Minimum 3 unique artists in playlist
- No duplicate tracks

## 🎨 Features

- **Mood Radar Chart** — Canvas-based visualization of emotional dimensions
- **Animated Meters** — Intensity, energy, and valence bars
- **Natural Language Prompts** — "Night-drive version" or "more upbeat"
- **Score Breakdown** — See why each song was recommended
- **One-Click Export** — Save directly to your Spotify account
- **Self-Growing Database** — Every queried song gets added automatically

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── core/            # Config, DB, security
│   │   ├── auth/            # Spotify OAuth
│   │   ├── songs/           # Track metadata & search
│   │   ├── lyrics/          # Genius + LRCLIB fetcher
│   │   ├── ai/              # Mood extraction & embeddings
│   │   ├── vectors/         # Qdrant vector operations
│   │   ├── recommendations/ # Hybrid scoring engine
│   │   ├── playlists/       # Spotify playlist creation
│   │   ├── seeder/          # Batch embedding pipeline
│   │   └── main.py          # FastAPI entry point
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/styles.css       # Premium dark design system
│   └── js/                  # Modular JS (api, auth, search, mood, playlist, animations)
├── docker-compose.yml       # PostgreSQL + Qdrant
└── .env.example
```

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Spotify OAuth redirect |
| GET | `/auth/callback` | OAuth callback handler |
| GET | `/auth/me` | Current user info |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/songs/search?q=` | Search Spotify tracks |
| GET | `/songs/{id}` | Get track details |
| POST | `/recommend` | Generate AI recommendations |
| POST | `/playlists/create` | Create Spotify playlist |
| GET | `/health` | System health check |
