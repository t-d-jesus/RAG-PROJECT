from typing import Any

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        examples=["Quem é Sydney Sweeney?"],
    )
    history: list[HistoryMessage] = Field(default_factory=list)
    metadata_filter: dict[str, Any] | None = None


class SourceResponse(BaseModel):
    source: str
    file_type: str | None = None
    document_type: str | None = None
    chunk_index: int | None = None


class ConfidenceResponse(BaseModel):
    level: str
    score: float
    reason: str


class QueryResponse(BaseModel):
    answer: str
    rewritten_question: str
    sources: list[SourceResponse]
    distances: list[float]
    citations: list[dict[str, Any]]
    retrieved_sources: list[str]
    reranked_sources: list[str]
    confidence: ConfidenceResponse
    metrics: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    vector_store: str


class IngestResponse(BaseModel):
    status: str
    indexed_files: list[str]
    skipped_files: list[str]
    failed_files: list[str]


class ResetRequest(BaseModel):
    confirm: bool = False


class ResetResponse(BaseModel):
    status: str
    vector_store: str


class MetricsResponse(BaseModel):
    metrics: dict[str, Any]
