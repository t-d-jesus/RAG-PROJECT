from statistics import mean
from typing import Any

from tests.evaluate import evaluate


def safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return mean(values)


def extract_metric(
    results: list[dict[str, Any]],
    metric_name: str,
) -> list[float]:
    values = []

    for result in results:
        metrics = result.get("metrics", {})
        value = metrics.get(metric_name)

        if isinstance(value, int | float):
            values.append(float(value))

    return values


def run_benchmark(
    vector_store: str,
) -> dict[str, Any]:
    evaluation = evaluate()
    results = evaluation["results"]

    total_times = extract_metric(
        results,
        "total_time",
    )
    retrieval_times = extract_metric(
        results,
        "retrieval_time",
    )
    rerank_times = extract_metric(
        results,
        "rerank_time",
    )
    llm_times = extract_metric(
        results,
        "llm_time",
    )
    input_tokens = extract_metric(
        results,
        "input_tokens",
    )
    output_tokens = extract_metric(
        results,
        "output_tokens",
    )
    total_tokens = extract_metric(
        results,
        "total_tokens",
    )
    costs = extract_metric(
        results,
        "estimated_cost_usd",
    )

    image_fallback_count = sum(
        1
        for result in results
        if result.get("metrics", {}).get(
            "image_fallback_used",
            False,
        )
    )

    return {
        "vector_store": vector_store,
        "timestamp": evaluation["timestamp"],
        "total_cases": evaluation["total"],
        "overall_passed": evaluation["overall_passed"],
        "score": evaluation["score"],
        "retrieval_score": evaluation["retrieval_score"],
        "rerank_score": evaluation["rerank_score"],
        "answer_score": evaluation["answer_score"],
        "avg_total_time": safe_mean(total_times),
        "avg_retrieval_time": safe_mean(
            retrieval_times,
        ),
        "avg_rerank_time": safe_mean(
            rerank_times,
        ),
        "avg_llm_time": safe_mean(llm_times),
        "avg_input_tokens": safe_mean(
            input_tokens,
        ),
        "avg_output_tokens": safe_mean(
            output_tokens,
        ),
        "avg_total_tokens": safe_mean(
            total_tokens,
        ),
        "avg_cost_usd": safe_mean(costs),
        "total_cost_usd": sum(costs),
        "image_fallback_count": image_fallback_count,
    }
