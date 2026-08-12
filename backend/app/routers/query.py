from fastapi import APIRouter, HTTPException

from app.logging_config import get_logger
from app.schemas import QueryRequest, QueryResponse
from app.services.rag_service import answer_question

logger = get_logger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    try:
        result = answer_question(payload.question)
    except Exception as exc:  # noqa: BLE001
        logger.error("Query failed", extra={"extra_fields": {"error": str(exc)}})
        raise HTTPException(status_code=500, detail="Failed to answer question.") from exc

    return QueryResponse(**result)
