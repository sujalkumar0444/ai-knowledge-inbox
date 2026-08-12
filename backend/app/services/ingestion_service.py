import uuid

from app.database import get_connection, now_iso
from app.logging_config import get_logger
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_provider
from app.services.fetch_url import UrlFetchError, fetch_url_content
from app.services.vector_store import store_chunk_embeddings

logger = get_logger(__name__)


class IngestionError(Exception):
    """Raised for any failure during ingestion that the API should surface as 4xx."""


def ingest_note(content: str, title: str | None) -> dict:
    result = _ingest_item(
        source_type="note", raw_content=content, title=title, source_url=None
    )
    result["already_existed"] = False
    return result


def ingest_url(url: str) -> dict:
    # Idempotency: re-submitting a URL that's already saved should not
    # re-fetch the page, re-chunk it, and re-spend embedding calls. This
    # matters in practice -- clients retry on timeout -- and it's a single
    # cheap lookup, not a reason to reach for a bigger abstraction.
    existing = _find_item_by_url(url)
    if existing is not None:
        logger.info(
            "URL already ingested; returning existing item instead of re-fetching",
            extra={"extra_fields": {"item_id": existing["id"], "url": url}},
        )
        existing["already_existed"] = True
        return existing

    try:
        content, page_title = fetch_url_content(url)
    except UrlFetchError as exc:
        raise IngestionError(str(exc)) from exc

    result = _ingest_item(
        source_type="url", raw_content=content, title=page_title, source_url=url
    )
    result["already_existed"] = False
    return result


def _find_item_by_url(url: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT items.id, items.source_type, items.title, items.created_at,
                   COUNT(chunks.id) AS chunk_count
            FROM items
            LEFT JOIN chunks ON chunks.item_id = items.id
            WHERE items.source_url = ?
            GROUP BY items.id
            """,
            (url,),
        ).fetchone()
    return dict(row) if row else None


def _ingest_item(
    source_type: str, raw_content: str, title: str | None, source_url: str | None
) -> dict:
    item_id = str(uuid.uuid4())
    created_at = now_iso()

    chunks = chunk_text(raw_content)
    if not chunks:
        raise IngestionError("Content produced no usable chunks after processing.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO items (id, source_type, source_url, title, raw_content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, source_type, source_url, title, raw_content, created_at),
        )

        chunk_rows: list[tuple[str, str]] = []
        for index, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO chunks (id, item_id, chunk_index, content, embedding, created_at)
                VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (chunk_id, item_id, index, chunk, created_at),
            )
            chunk_rows.append((chunk_id, chunk))

        conn.commit()

    # Embedding generation happens after commit so a slow/failing embed call
    # (e.g. an OpenAI API hiccup) never rolls back an otherwise-successful
    # save -- the item is still there and searchable via keyword fallback
    # even if this step fails.
    try:
        provider = get_embedding_provider()
        store_chunk_embeddings(provider, chunk_rows)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Embedding generation failed post-ingest; item saved without embeddings",
            extra={"extra_fields": {"item_id": item_id, "error": str(exc)}},
        )

    logger.info(
        "Item ingested",
        extra={
            "extra_fields": {
                "item_id": item_id,
                "source_type": source_type,
                "chunk_count": len(chunks),
            }
        },
    )

    return {
        "id": item_id,
        "source_type": source_type,
        "title": title,
        "chunk_count": len(chunks),
        "created_at": created_at,
    }
