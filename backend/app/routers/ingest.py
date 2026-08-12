from typing import Union

from fastapi import APIRouter, HTTPException, Response

from app.logging_config import get_logger
from app.schemas import IngestNoteRequest, IngestResponse, IngestUrlRequest
from app.services.ingestion_service import IngestionError, ingest_note, ingest_url

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=201)
def create_item(payload: Union[IngestNoteRequest, IngestUrlRequest], response: Response) -> IngestResponse:
    try:
        if payload.source_type == "note":
            result = ingest_note(content=payload.content, title=payload.title)
        else:
            result = ingest_url(url=payload.url)
    except IngestionError as exc:
        logger.warning("Ingestion rejected", extra={"extra_fields": {"reason": str(exc)}})
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Idempotent re-submission of an already-saved URL: 200 (returning the
    # existing resource), not 201 (nothing was created this call).
    if result.get("already_existed"):
        response.status_code = 200

    return IngestResponse(**result)
