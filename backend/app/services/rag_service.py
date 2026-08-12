from app.config import settings
from app.database import get_connection
from app.logging_config import get_logger
from app.services.embeddings import get_embedding_provider
from app.services.generation import get_generation_provider
from app.services.vector_store import search

logger = get_logger(__name__)


def answer_question(question: str) -> dict:
    embedding_provider = get_embedding_provider()
    retrieved = search(embedding_provider, question, top_k=settings.top_k)

    if not retrieved:
        logger.info("No content available for query", extra={"extra_fields": {"question": question}})

    item_ids = list({chunk.item_id for chunk in retrieved})
    items_by_id = _fetch_items(item_ids)

    generation_provider = get_generation_provider()
    result = generation_provider.generate(
        question=question, context_chunks=[c.content for c in retrieved]
    )

    sources = []
    for chunk in retrieved:
        item = items_by_id.get(chunk.item_id, {})
        snippet = chunk.content
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "…"
        sources.append(
            {
                "item_id": chunk.item_id,
                "title": item.get("title"),
                "source_type": item.get("source_type"),
                "source_url": item.get("source_url"),
                "snippet": snippet,
                "similarity": round(chunk.similarity, 4),
            }
        )

    logger.info(
        "Query answered",
        extra={
            "extra_fields": {
                "question": question,
                "retrieved_chunks": len(retrieved),
                "generation_mode": result.mode,
            }
        },
    )

    return {"answer": result.answer, "sources": sources, "generation_mode": result.mode}


def _fetch_items(item_ids: list[str]) -> dict[str, dict]:
    if not item_ids:
        return {}
    placeholders = ",".join("?" for _ in item_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT id, title, source_type, source_url FROM items WHERE id IN ({placeholders})",
            item_ids,
        ).fetchall()
    return {row["id"]: dict(row) for row in rows}
