from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.prometheus_metrics import (
    initialize_metrics,
    observe_query_error,
    observe_query_metrics,
)
from app.api.schemas import (
    BenchmarkDashboardResponse,
    BenchmarkHistoryResponse,
    BenchmarkLatestResponse,
    HealthResponse,
    IngestResponse,
    MetricsResponse,
    QueryRequest,
    QueryResponse,
    ResetRequest,
    ResetResponse,
)
from app.api.state import (
    get_last_query_metrics,
    save_query_metrics,
)
from app.config import DATA_PATH, VECTOR_STORE
from app.ingest import ingest_file
from app.query import ask
from app.vectorstore.store import reset_all_collections
from benchmarks.dashboard_data import load_dashboard_data
from benchmarks.history import (
    get_latest_benchmark,
    load_benchmark_history,
)

app = FastAPI(
    title="RAG Platform API",
    description=("RAG API with ChromaDB, Qdrant and PostgreSQL + pgvector."),
    version="1.4.0",
)

initialize_metrics(
    vector_store=VECTOR_STORE,
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        vector_store=VECTOR_STORE,
    )


@app.post(
    "/query",
    response_model=QueryResponse,
)
def query(request: QueryRequest) -> QueryResponse:
    try:
        history = [message.model_dump() for message in request.history]

        (
            answer,
            sources,
            distances,
            rewritten_question,
            citations,
            retrieved_sources,
            reranked_sources,
            confidence,
            metrics,
        ) = ask(
            question=request.question,
            history=history,
            metadata_filter=request.metadata_filter,
        )

        save_query_metrics(metrics)

        observe_query_metrics(
            metrics=metrics,
            confidence=confidence,
        )

        return QueryResponse(
            answer=answer,
            rewritten_question=rewritten_question,
            sources=sources,
            distances=distances,
            citations=citations,
            retrieved_sources=retrieved_sources,
            reranked_sources=reranked_sources,
            confidence=confidence,
            metrics=metrics,
        )

    except Exception as error:
        observe_query_error(
            vector_store=VECTOR_STORE,
        )

        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a consulta.",
        ) from error


@app.post(
    "/ingest",
    response_model=IngestResponse,
)
def ingest() -> IngestResponse:
    data_path = Path(DATA_PATH)

    if not data_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Diretório de dados não encontrado: {DATA_PATH}",
        )

    indexed_files = []
    skipped_files = []
    failed_files = []

    for file_path in data_path.iterdir():
        if not file_path.is_file():
            continue

        try:
            result = ingest_file(file_path)

            if result == "indexed":
                indexed_files.append(file_path.name)
            elif result == "skipped":
                skipped_files.append(file_path.name)

        except Exception:
            failed_files.append(file_path.name)

    status = "completed"

    if failed_files:
        status = "completed_with_errors"

    return IngestResponse(
        status=status,
        indexed_files=indexed_files,
        skipped_files=skipped_files,
        failed_files=failed_files,
    )


@app.post(
    "/reset",
    response_model=ResetResponse,
)
def reset(request: ResetRequest) -> ResetResponse:
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail=('Confirmação obrigatória. Envie {"confirm": true}.'),
        )

    try:
        reset_all_collections()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Erro ao resetar o vector store.",
        ) from error

    return ResetResponse(
        status="reset_completed",
        vector_store=VECTOR_STORE,
    )


@app.get(
    "/metrics",
    response_model=MetricsResponse,
)
def metrics() -> MetricsResponse:
    return MetricsResponse(
        metrics=get_last_query_metrics(),
    )


@app.get(
    "/metrics/prometheus",
    include_in_schema=False,
)
def prometheus_metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get(
    "/benchmarks/history",
    response_model=BenchmarkHistoryResponse,
)
def benchmark_history() -> BenchmarkHistoryResponse:
    return BenchmarkHistoryResponse(
        benchmarks=load_benchmark_history(),
    )


@app.get(
    "/benchmarks/latest",
    response_model=BenchmarkLatestResponse,
)
def benchmark_latest() -> BenchmarkLatestResponse:
    return BenchmarkLatestResponse(
        benchmark=get_latest_benchmark(),
    )


@app.get(
    "/benchmarks/dashboard",
    response_model=BenchmarkDashboardResponse,
)
def benchmark_dashboard() -> BenchmarkDashboardResponse:
    return BenchmarkDashboardResponse(
        data=load_dashboard_data(),
    )


for route in app.routes:
    print(route.path)
