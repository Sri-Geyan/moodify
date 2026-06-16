"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.vectors.client import init_qdrant, close_qdrant, get_qdrant
from app.vectors import service as vector_service

# Import routers
from app.auth.router import router as auth_router
from app.songs.router import router as songs_router
from app.recommendations.router import router as recommend_router
from app.playlists.router import router as playlists_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # --- Startup ---
    print("[STARTING] Spotify AI Playlist Generator")
    await init_db()
    print("  [OK] Database initialized")

    try:
        await init_qdrant()
        count = await vector_service.get_collection_count()
        print(f"  [OK] Qdrant connected ({count} vectors)")
    except Exception as e:
        print(f"  [ERROR] Qdrant connection failed: {e}")
        print("    (Recommendations will fail until Qdrant is available)")

    yield

    # --- Shutdown ---
    await close_db()
    await close_qdrant()
    print("[SHUTDOWN] Complete")


app = FastAPI(
    title="Spotify AI Playlist Generator",
    description="AI-powered playlist generation using mood analysis and vector similarity",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers ---
app.include_router(auth_router)
app.include_router(songs_router)
app.include_router(recommend_router)
app.include_router(playlists_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    qdrant_status = "unknown"
    vector_count = 0
    try:
        vector_count = await vector_service.get_collection_count()
        qdrant_status = "connected"
    except Exception:
        qdrant_status = "disconnected"

    return {
        "status": "healthy",
        "service": "Spotify AI Playlist Generator",
        "version": "1.0.0",
        "qdrant": qdrant_status,
        "vector_count": vector_count,
        "ai_model": settings.hf_llm_model,
        "embedding_model": settings.hf_embedding_model,
    }

# --- Serve Frontend (Last to avoid intercepting API routes) ---
import os
from fastapi.staticfiles import StaticFiles

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

