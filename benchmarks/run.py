import argparse
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Any

VECTOR_STORES = [
    "chroma",
    "qdrant",
    "pgvector",
    "opensearch",
]


def run_store_benchmark(
    vector_store: str,
    temporary_dir: Path,
    run_number: int,
) -> dict[str, Any]:
    output_path = temporary_dir / f"{vector_store}_run_{run_number}.json"

    environment = os.environ.copy()
    environment["VECTOR_STORE"] = vector_store

    print(
        f"\n{'=' * 60}\n"
        f"Executando benchmark: {vector_store}\n"
        f"Rodada: {run_number}\n"
        f"{'=' * 60}"
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmarks.run_single",
            "--output",
            str(output_path),
        ],
        env=environment,
        check=True,
    )

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        result = json.load(file)

    result["run"] = run_number

    return result


def save_json_report(
    raw_results: list[dict[str, Any]],
    aggregated_results: list[dict[str, Any]],
    output_path: Path,
    timestamp: str,
    runs: int,
) -> None:
    output = {
        "timestamp": timestamp,
        "runs": runs,
        "raw_results": raw_results,
        "aggregated_results": aggregated_results,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )


def save_raw_csv_report(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    fields = [
        "run",
        "vector_store",
        "timestamp",
        "total_cases",
        "overall_passed",
        "score",
        "retrieval_score",
        "rerank_score",
        "answer_score",
        "avg_total_time",
        "avg_retrieval_time",
        "min_retrieval_time",
        "max_retrieval_time",
        "std_retrieval_time",
        "avg_rerank_time",
        "avg_llm_time",
        "avg_input_tokens",
        "avg_output_tokens",
        "avg_total_tokens",
        "avg_cost_usd",
        "total_cost_usd",
        "image_fallback_count",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(results)


def save_aggregated_csv_report(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    fields = [
        "vector_store",
        "runs",
        "score_avg",
        "score_min",
        "score_max",
        "latency_avg",
        "latency_min",
        "latency_max",
        "latency_std",
        "retrieval_avg",
        "retrieval_min",
        "retrieval_max",
        "retrieval_std",
        "rerank_avg",
        "llm_avg",
        "tokens_avg",
        "cost_avg",
        "fallbacks",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(results)


def aggregate_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for result in results:
        grouped[result["vector_store"]].append(result)

    aggregated_results = []

    for vector_store in VECTOR_STORES:
        store_results = grouped.get(vector_store, [])

        if not store_results:
            continue

        total_times = [float(result["avg_total_time"]) for result in store_results]

        retrieval_times = [
            float(result["avg_retrieval_time"]) for result in store_results
        ]

        rerank_times = [float(result["avg_rerank_time"]) for result in store_results]

        llm_times = [float(result["avg_llm_time"]) for result in store_results]

        scores = [float(result["score"]) for result in store_results]

        tokens = [float(result["avg_total_tokens"]) for result in store_results]

        costs = [float(result["total_cost_usd"]) for result in store_results]

        aggregated_results.append(
            {
                "vector_store": vector_store,
                "runs": len(store_results),
                "score_avg": mean(scores),
                "score_min": min(scores),
                "score_max": max(scores),
                "latency_avg": mean(total_times),
                "latency_min": min(total_times),
                "latency_max": max(total_times),
                "latency_std": (stdev(total_times) if len(total_times) > 1 else 0.0),
                "retrieval_avg": mean(retrieval_times),
                "retrieval_min": min(retrieval_times),
                "retrieval_max": max(retrieval_times),
                "retrieval_std": (
                    stdev(retrieval_times) if len(retrieval_times) > 1 else 0.0
                ),
                "rerank_avg": mean(rerank_times),
                "llm_avg": mean(llm_times),
                "tokens_avg": mean(tokens),
                "cost_avg": mean(costs),
                "fallbacks": sum(
                    int(
                        result.get(
                            "image_fallback_count",
                            0,
                        )
                    )
                    for result in store_results
                ),
            }
        )

    return aggregated_results


def format_seconds(value: Any) -> str:
    if not isinstance(value, int | float):
        return "-"

    return f"{float(value):.4f}s"


def format_number(value: Any) -> str:
    if not isinstance(value, int | float):
        return "-"

    return f"{float(value):.2f}"


def format_cost(value: Any) -> str:
    if not isinstance(value, int | float):
        return "-"

    return f"${float(value):.8f}"


def print_aggregated_results(
    results: list[dict[str, Any]],
) -> None:
    print("\nBenchmark Consolidado:\n")

    header = (
        f"{'Store':<12}"
        f"{'Score':>10}"
        f"{'Latency':>12}"
        f"{'StdDev':>12}"
        f"{'Rerank':>12}"
        f"{'LLM':>12}"
        f"{'Tokens':>12}"
        f"{'Cost':>17}"
        f"{'Fallbacks':>12}"
    )

    print(header)
    print("-" * len(header))

    for result in results:
        print(
            f"{result['vector_store']:<12}"
            f"{result['score_avg']:>9.2%}"
            f"{format_seconds(result['latency_avg']):>12}"
            f"{format_seconds(result['latency_std']):>12}"
            f"{format_seconds(result['rerank_avg']):>12}"
            f"{format_seconds(result['llm_avg']):>12}"
            f"{format_number(result['tokens_avg']):>12}"
            f"{format_cost(result['cost_avg']):>17}"
            f"{result['fallbacks']:>12}"
        )


def print_retrieval_benchmark(
    results: list[dict[str, Any]],
) -> None:
    print("\nRetrieval Benchmark:\n")

    header = f"{'Store':<12}{'Avg':>12}{'Min':>12}{'Max':>12}{'StdDev':>12}"

    print(header)
    print("-" * len(header))

    for result in results:
        print(
            f"{result['vector_store']:<12}"
            f"{format_seconds(result['retrieval_avg']):>12}"
            f"{format_seconds(result['retrieval_min']):>12}"
            f"{format_seconds(result['retrieval_max']):>12}"
            f"{format_seconds(result['retrieval_std']):>12}"
        )


def print_rankings(
    results: list[dict[str, Any]],
) -> None:
    if not results:
        return

    best_score = max(result["score_avg"] for result in results)

    highest_score_stores = [
        result["vector_store"]
        for result in results
        if result["score_avg"] == best_score
    ]

    fastest_total = min(
        results,
        key=lambda result: result["latency_avg"],
    )

    fastest_retrieval = min(
        results,
        key=lambda result: result["retrieval_avg"],
    )

    most_stable = min(
        results,
        key=lambda result: result["latency_std"],
    )

    lowest_tokens = min(
        results,
        key=lambda result: result["tokens_avg"],
    )

    lowest_cost = min(
        results,
        key=lambda result: result["cost_avg"],
    )

    print("\nDestaques:")

    best_score = max(result["score_avg"] for result in results)

    highest_score_stores = [
        result["vector_store"]
        for result in results
        if result["score_avg"] == best_score
    ]

    print(f"- Maior score médio: {', '.join(highest_score_stores)} ({best_score:.2%})")

    print(
        "- Menor latência total média: "
        f"{fastest_total['vector_store']} "
        f"({fastest_total['latency_avg']:.4f}s)"
    )

    print(
        "- Menor latência de retrieval: "
        f"{fastest_retrieval['vector_store']} "
        f"({fastest_retrieval['retrieval_avg']:.4f}s)"
    )

    print(
        "- Menor variação de latência: "
        f"{most_stable['vector_store']} "
        f"({most_stable['latency_std']:.4f}s)"
    )

    print(
        "- Menor média de tokens: "
        f"{lowest_tokens['vector_store']} "
        f"({lowest_tokens['tokens_avg']:.2f})"
    )

    print(
        "- Menor custo médio por rodada: "
        f"{lowest_cost['vector_store']} "
        f"(${lowest_cost['cost_avg']:.8f})"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Executa benchmarks comparativos entre os vector stores.")
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Quantidade de rodadas por vector store.",
    )

    arguments = parser.parse_args()

    if arguments.runs < 1:
        parser.error("--runs deve ser maior ou igual a 1.")

    return arguments


def save_markdown_report(
    aggregated_results: list[dict[str, Any]],
    output_path: Path,
    timestamp: str,
    runs: int,
) -> None:
    best_score = max(result["score_avg"] for result in aggregated_results)

    highest_score_stores = [
        result["vector_store"]
        for result in aggregated_results
        if result["score_avg"] == best_score
    ]

    fastest_total = min(
        aggregated_results,
        key=lambda result: result["latency_avg"],
    )

    fastest_retrieval = min(
        aggregated_results,
        key=lambda result: result["retrieval_avg"],
    )

    most_stable = min(
        aggregated_results,
        key=lambda result: result["latency_std"],
    )

    lowest_tokens = min(
        aggregated_results,
        key=lambda result: result["tokens_avg"],
    )

    lowest_cost = min(
        aggregated_results,
        key=lambda result: result["cost_avg"],
    )

    lines = [
        "# RAG Vector Store Benchmark",
        "",
        f"- Timestamp: `{timestamp}`",
        f"- Runs per vector store: `{runs}`",
        "",
        "## End-to-End Benchmark",
        "",
        (
            "| Vector Store | Score | Avg Latency | Std Dev | "
            "Avg Rerank | Avg LLM | Avg Tokens | Avg Cost | Fallbacks |"
        ),
        ("|---|---:|---:|---:|---:|---:|---:|---:|---:|"),
    ]

    for result in aggregated_results:
        lines.append(
            "| "
            f"{result['vector_store']} | "
            f"{result['score_avg']:.2%} | "
            f"{result['latency_avg']:.4f}s | "
            f"{result['latency_std']:.4f}s | "
            f"{result['rerank_avg']:.4f}s | "
            f"{result['llm_avg']:.4f}s | "
            f"{result['tokens_avg']:.2f} | "
            f"${result['cost_avg']:.8f} | "
            f"{result['fallbacks']} |"
        )

    lines.extend(
        [
            "",
            "## Retrieval Benchmark",
            "",
            ("| Vector Store | Avg Retrieval | Min | Max | Std Dev |"),
            "|---|---:|---:|---:|---:|",
        ]
    )

    for result in aggregated_results:
        lines.append(
            "| "
            f"{result['vector_store']} | "
            f"{result['retrieval_avg']:.4f}s | "
            f"{result['retrieval_min']:.4f}s | "
            f"{result['retrieval_max']:.4f}s | "
            f"{result['retrieval_std']:.4f}s |"
        )

    lines.extend(
        [
            "",
            "## Highlights",
            "",
            (
                "- Highest average score: "
                f"{', '.join(highest_score_stores)} "
                f"({best_score:.2%})"
            ),
            (
                "- Lowest average end-to-end latency: "
                f"{fastest_total['vector_store']} "
                f"({fastest_total['latency_avg']:.4f}s)"
            ),
            (
                "- Lowest average retrieval latency: "
                f"{fastest_retrieval['vector_store']} "
                f"({fastest_retrieval['retrieval_avg']:.4f}s)"
            ),
            (
                "- Lowest end-to-end latency variation: "
                f"{most_stable['vector_store']} "
                f"({most_stable['latency_std']:.4f}s)"
            ),
            (
                "- Lowest average token usage: "
                f"{lowest_tokens['vector_store']} "
                f"({lowest_tokens['tokens_avg']:.2f})"
            ),
            (
                "- Lowest average cost per run: "
                f"{lowest_cost['vector_store']} "
                f"(${lowest_cost['cost_avg']:.8f})"
            ),
            "",
            "## Notes",
            "",
            (
                "- End-to-end latency includes retrieval, reranking, "
                "LLM generation and fallback processing."
            ),
            (
                "- Retrieval latency is the most direct metric for "
                "comparing vector-store performance."
            ),
            (
                "- Token usage and cost may vary because each backend "
                "can produce a different chunk ordering and context."
            ),
            (
                "- Results are specific to this dataset, configuration "
                "and local execution environment."
            ),
            "",
        ]
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    arguments = parse_arguments()

    timestamp = datetime.now(
        timezone.utc,
    ).strftime("%Y%m%d_%H%M%S")

    results_dir = Path("benchmarks/results")
    temporary_dir = results_dir / ".tmp" / timestamp

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_results: list[dict[str, Any]] = []

    for run_number in range(
        1,
        arguments.runs + 1,
    ):
        print(f"\n{'#' * 60}\nRodada {run_number}/{arguments.runs}\n{'#' * 60}")

        for vector_store in VECTOR_STORES:
            result = run_store_benchmark(
                vector_store=vector_store,
                temporary_dir=temporary_dir,
                run_number=run_number,
            )

            raw_results.append(result)

    aggregated_results = aggregate_results(
        raw_results,
    )

    json_path = results_dir / f"benchmark_{timestamp}.json"

    raw_csv_path = results_dir / f"benchmark_{timestamp}_raw.csv"

    aggregated_csv_path = results_dir / f"benchmark_{timestamp}_aggregated.csv"
    markdown_path = results_dir / f"benchmark_{timestamp}.md"

    save_json_report(
        raw_results=raw_results,
        aggregated_results=aggregated_results,
        output_path=json_path,
        timestamp=timestamp,
        runs=arguments.runs,
    )

    save_raw_csv_report(
        results=raw_results,
        output_path=raw_csv_path,
    )

    save_aggregated_csv_report(
        results=aggregated_results,
        output_path=aggregated_csv_path,
    )

    save_markdown_report(
        aggregated_results=aggregated_results,
        output_path=markdown_path,
        timestamp=timestamp,
        runs=arguments.runs,
    )

    print(f"Relatório Markdown salvo em: {markdown_path}")

    print_aggregated_results(
        aggregated_results,
    )

    print_retrieval_benchmark(
        aggregated_results,
    )

    print_rankings(
        aggregated_results,
    )

    print(f"\nJSON salvo em: {json_path}")
    print(f"CSV bruto salvo em: {raw_csv_path}")
    print(f"CSV consolidado salvo em: {aggregated_csv_path}")


if __name__ == "__main__":
    main()
