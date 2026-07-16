from typing import Any

from prometheus_client import Counter, Gauge, Histogram
from app.config import CHAT_MODEL


QUERY_REQUESTS = Counter(
    "rag_query_requests_total",
    "Total de consultas processadas pelo RAG.",
    ["vector_store", "retrieval_mode"],
)

QUERY_ERRORS = Counter(
    "rag_query_errors_total",
    "Total de erros durante consultas do RAG.",
    ["vector_store"],
)

PIPELINE_DURATION = Histogram(
    "rag_pipeline_stage_duration_seconds",
    "Duração das etapas do pipeline RAG.",
    ["stage", "vector_store", "retrieval_mode"],
)

RETRIEVED_CHUNKS = Histogram(
    "rag_retrieved_chunks",
    "Quantidade de chunks recuperados por consulta.",
    ["vector_store", "retrieval_mode"],
)

FILTERED_CANDIDATES = Histogram(
    "rag_filtered_candidates",
    "Quantidade de candidatos após filtros e ranking.",
    ["vector_store", "retrieval_mode"],
)

RERANKED_CHUNKS = Histogram(
    "rag_reranked_chunks",
    "Quantidade de chunks selecionados pelo reranker.",
    ["vector_store", "retrieval_mode"],
)

CONTEXT_CHUNKS = Histogram(
    "rag_context_chunks",
    "Quantidade de chunks incluídos no contexto final.",
    ["vector_store", "retrieval_mode"],
)

CONTEXT_CHARACTERS = Histogram(
    "rag_context_characters",
    "Quantidade de caracteres enviados ao LLM.",
    ["vector_store", "retrieval_mode"],
)

LAST_QUERY_CONFIDENCE = Gauge(
    "rag_last_query_confidence_score",
    "Score de confiança da última consulta.",
    ["vector_store"],
)


TIMING_METRICS = {
    "question_rewrite_time",
    "embedding_time",
    "retrieval_time",
    "hybrid_ranking_time",
    "rerank_time",
    "parent_retrieval_time",
    "context_build_time",
    "llm_time",
    "total_time",
}


VECTOR_STORE_INFO = Gauge(
    "rag_vector_store_info",
    "Vector store atualmente configurado.",
    ["vector_store"],
)

INPUT_TOKENS = Counter(
    "rag_input_tokens_total",
    "Total de tokens de entrada.",
    ["model", "vector_store"],
)

OUTPUT_TOKENS = Counter(
    "rag_output_tokens_total",
    "Total de tokens de saída.",
    ["model", "vector_store"],
)

TOTAL_TOKENS = Counter(
    "rag_total_tokens_total",
    "Total de tokens consumidos.",
    ["model", "vector_store"],
)


QUERY_COST_USD = Histogram(
    "rag_query_cost_usd",
    "Custo estimado em USD por consulta.",
    ["model", "vector_store"],
    buckets=(
        0.00001,
        0.00005,
        0.0001,
        0.0005,
        0.001,
        0.005,
        0.01,
        0.05,
        0.1,
    ),
)

TOTAL_COST_USD = Counter(
    "rag_estimated_cost_usd_total",
    "Custo estimado acumulado em USD.",
    ["model", "vector_store"],
)


def observe_query_metrics(
    metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> None:
    vector_store = str(
        metrics.get(
            "vector_store",
            "unknown",
        )
    )

    retrieval_mode = str(
        metrics.get(
            "retrieval_mode",
            "unknown",
        )
    )

    QUERY_REQUESTS.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).inc()

    for metric_name in TIMING_METRICS:
        value = metrics.get(metric_name)

        if isinstance(value, int | float):
            PIPELINE_DURATION.labels(
                stage=metric_name,
                vector_store=vector_store,
                retrieval_mode=retrieval_mode,
            ).observe(float(value))

    RETRIEVED_CHUNKS.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).observe(float(metrics.get("retrieved_chunks", 0)))

    FILTERED_CANDIDATES.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).observe(float(metrics.get("filtered_candidates", 0)))

    RERANKED_CHUNKS.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).observe(float(metrics.get("reranked_chunks", 0)))

    CONTEXT_CHUNKS.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).observe(float(metrics.get("context_chunks", 0)))

    CONTEXT_CHARACTERS.labels(
        vector_store=vector_store,
        retrieval_mode=retrieval_mode,
    ).observe(float(metrics.get("context_chars", 0)))

    LAST_QUERY_CONFIDENCE.labels(
        vector_store=vector_store,
    ).set(float(confidence.get("score", 0.0)))

    INPUT_TOKENS.labels(
        model=CHAT_MODEL,
        vector_store=vector_store,
    ).inc(float(metrics.get("input_tokens", 0)))

    OUTPUT_TOKENS.labels(
        model=CHAT_MODEL,
        vector_store=vector_store,
    ).inc(float(metrics.get("output_tokens", 0)))

    TOTAL_TOKENS.labels(
        model=CHAT_MODEL,
        vector_store=vector_store,
    ).inc(float(metrics.get("total_tokens", 0)))

    estimated_cost_usd = float(
        metrics.get(
            "estimated_cost_usd",
            0.0,
        )
    )

    QUERY_COST_USD.labels(
        model=CHAT_MODEL,
        vector_store=vector_store,
    ).observe(estimated_cost_usd)

    TOTAL_COST_USD.labels(
        model=CHAT_MODEL,
        vector_store=vector_store,
    ).inc(estimated_cost_usd)


def observe_query_error(
    vector_store: str,
) -> None:
    QUERY_ERRORS.labels(
        vector_store=vector_store,
    ).inc()


def initialize_metrics(
    vector_store: str,
) -> None:
    QUERY_ERRORS.labels(
        vector_store=vector_store,
    ).inc(0)

    VECTOR_STORE_INFO.labels(
        vector_store=vector_store,
    ).set(1)
