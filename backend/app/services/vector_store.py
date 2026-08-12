"""
Vector storage + retrieval.

Storage: chunk embeddings live in a TEXT (JSON) column in the `chunks`
SQLite table -- see database.py. Retrieval is brute-force cosine similarity
computed in Python over every stored chunk.

Why this is fine here: single user, expected corpus size of dozens to a few
hundred chunks for a demo/take-home. Brute force over a few hundred
384-4096 dim vectors is sub-millisecond.

Why this breaks at scale (see README): brute force is O(n) per query with
no index, all vectors are pulled into Python memory, and there is no ANN
(approximate nearest neighbor) index. Past a few tens of thousands of
chunks -- or with concurrent multi-user traffic -- this needs a real vector
index (pgvector, Qdrant, Pinecone, FAISS) with an ANN algorithm (HNSW/IVF).

Local (TF-IDF) provider special case: because TF-IDF's vector space depends
on the exact corpus it was fit on, we don't trust previously-stored
embeddings for that provider -- we refit over the live corpus on every
query instead. This is called out explicitly rather than silently doing
the "wrong but easy" thing of comparing embeddings from different fits.
"""
from dataclasses import dataclass

from app.config import settings
from app.database import decode_embedding, encode_embedding, get_connection
from app.logging_config import get_logger
from app.services.embeddings import EmbeddingProvider, cosine_similarity

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    item_id: str
    content: str
    similarity: float


def store_chunk_embeddings(
    provider: EmbeddingProvider, chunk_rows: list[tuple[str, str]]
) -> None:
    """
    chunk_rows: list of (chunk_id, content).
    For OpenAI, computes and persists a real embedding per chunk.
    For local TF-IDF, this is a no-op (embeddings are computed fresh at
    query time -- see module docstring) beyond leaving the row unembedded.
    """
    if settings.embedding_provider != "openai" or not chunk_rows:
        return

    contents = [content for _, content in chunk_rows]
    vectors = provider.embed(contents)

    with get_connection() as conn:
        for (chunk_id, _), vector in zip(chunk_rows, vectors):
            conn.execute(
                "UPDATE chunks SET embedding = ? WHERE id = ?",
                (encode_embedding(vector), chunk_id),
            )
        conn.commit()

    logger.info(
        "Stored chunk embeddings",
        extra={"extra_fields": {"count": len(chunk_rows), "provider": "openai"}},
    )


def search(provider: EmbeddingProvider, question: str, top_k: int) -> list[RetrievedChunk]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT chunks.id AS chunk_id, chunks.item_id, chunks.content, chunks.embedding
            FROM chunks
            """
        ).fetchall()

    if not rows:
        return []

    contents = [row["content"] for row in rows]

    if settings.embedding_provider == "openai":
        query_vector = provider.embed_query(question, contents)
        candidate_vectors = [decode_embedding(row["embedding"]) for row in rows]
    else:
        # Local TF-IDF: refit over the live corpus so query + corpus vectors
        # come from the same fitted vocabulary space.
        candidate_vectors = provider.embed(contents)
        query_vector = provider.embed_query(question, contents)

    scored = [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            item_id=row["item_id"],
            content=row["content"],
            similarity=cosine_similarity(query_vector, candidate_vector),
        )
        for row, candidate_vector in zip(rows, candidate_vectors)
    ]

    scored.sort(key=lambda c: c.similarity, reverse=True)
    return scored[:top_k]
