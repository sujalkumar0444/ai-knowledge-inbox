import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import get_connection, init_db
from app.logging_config import configure_logging, get_logger
from app.routers import ingest, items, query

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info(
        "App started",
        extra={
            "extra_fields": {
                "embedding_provider": settings.embedding_provider,
                "generation_provider": settings.generation_provider,
            }
        },
    )
    yield


app = FastAPI(
    title="AI Knowledge Inbox",
    description="Save notes/URLs, ask questions over them via a simple RAG pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    logger.info(
        "Request started",
        extra={"request_id": request_id, "extra_fields": {"method": request.method, "path": request.url.path}},
    )

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # pydantic's raw exc.errors() can contain non-JSON-serializable objects
    # (e.g. the original exception instance in ctx when a custom validator
    # raises ValueError) -- jsonable_encoder sanitizes that before we log or
    # return it.
    safe_errors = jsonable_encoder(exc.errors())
    logger.warning(
        "Validation error",
        extra={"extra_fields": {"path": request.url.path, "errors": safe_errors}},
    )
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": safe_errors},
    )


@app.get("/health")
def health() -> dict:
    db_status = "ok"
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"
        logger.error("Health check DB probe failed", extra={"extra_fields": {"error": str(exc)}})

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "embedding_provider": settings.embedding_provider,
        "generation_provider": settings.generation_provider,
        "openai_key_configured": bool(settings.openai_api_key),
    }


app.include_router(ingest.router, tags=["ingest"])
app.include_router(items.router, tags=["items"])
app.include_router(query.router, tags=["query"])
