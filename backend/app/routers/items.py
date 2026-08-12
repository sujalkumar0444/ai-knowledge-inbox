from fastapi import APIRouter

from app.database import get_connection
from app.schemas import ItemsListResponse, ItemSummary

router = APIRouter()


@router.get("/items", response_model=ItemsListResponse)
def list_items() -> ItemsListResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                items.id,
                items.source_type,
                items.source_url,
                items.title,
                items.raw_content,
                items.created_at,
                COUNT(chunks.id) AS chunk_count
            FROM items
            LEFT JOIN chunks ON chunks.item_id = items.id
            GROUP BY items.id
            ORDER BY items.created_at DESC
            """
        ).fetchall()

    items = []
    for row in rows:
        preview = row["raw_content"][:180]
        if len(row["raw_content"]) > 180:
            preview = preview.rsplit(" ", 1)[0] + "…"
        items.append(
            ItemSummary(
                id=row["id"],
                source_type=row["source_type"],
                source_url=row["source_url"],
                title=row["title"],
                preview=preview,
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
            )
        )

    return ItemsListResponse(items=items, total=len(items))
