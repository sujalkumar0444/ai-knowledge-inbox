"""
API-facing request/response models.

Kept separate from any internal/domain representations so the HTTP contract
can evolve independently of internal storage details.
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class IngestNoteRequest(BaseModel):
    source_type: Literal["note"] = "note"
    content: str = Field(..., min_length=1, max_length=50_000)
    title: str | None = Field(default=None, max_length=200)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v.strip()


class IngestUrlRequest(BaseModel):
    source_type: Literal["url"] = "url"
    url: str = Field(..., min_length=1, max_length=2000)

    @field_validator("url")
    @classmethod
    def url_looks_valid(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class IngestResponse(BaseModel):
    id: str
    source_type: Literal["note", "url"]
    title: str | None
    chunk_count: int
    created_at: str
    already_existed: bool = False


class ItemSummary(BaseModel):
    id: str
    source_type: Literal["note", "url"]
    source_url: str | None
    title: str | None
    preview: str
    chunk_count: int
    created_at: str


class ItemsListResponse(BaseModel):
    items: list[ItemSummary]
    total: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


class SourceSnippet(BaseModel):
    item_id: str
    title: str | None
    source_type: Literal["note", "url"]
    source_url: str | None
    snippet: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]
    generation_mode: Literal["openai", "extractive_fallback"]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
