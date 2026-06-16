"""Qdrant client setup and collection initialization."""

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)
from app.core.config import get_settings

settings = get_settings()

# Global async Qdrant client
qdrant_client: AsyncQdrantClient | None = None


async def get_qdrant() -> AsyncQdrantClient:
    """Get the initialized Qdrant client."""
    global qdrant_client
    if qdrant_client is None:
        await init_qdrant()
    return qdrant_client


async def init_qdrant():
    """Initialize Qdrant client and ensure collection exists."""
    global qdrant_client

    connect_kwargs = {}
    if settings.qdrant_url == ":memory:":
        connect_kwargs["location"] = ":memory:"
    else:
        connect_kwargs["url"] = settings.qdrant_url

    if settings.qdrant_api_key:
        connect_kwargs["api_key"] = settings.qdrant_api_key

    qdrant_client = AsyncQdrantClient(**connect_kwargs)

    # Check if collection exists, create if not
    collections = await qdrant_client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if settings.qdrant_collection not in collection_names:
        await qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )

        # Create payload indexes for filtering
        await qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="artist",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="genres",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await qdrant_client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="popularity",
            field_schema=PayloadSchemaType.INTEGER,
        )

        print(f"Created Qdrant collection '{settings.qdrant_collection}' "
              f"with {settings.embedding_dimension}d vectors")


async def close_qdrant():
    """Close the Qdrant client connection."""
    global qdrant_client
    if qdrant_client:
        await qdrant_client.close()
        qdrant_client = None
