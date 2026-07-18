from collections import defaultdict
from typing import Any

from benchmarks.history import load_benchmark_history

DashboardEntry = dict[str, Any]
DashboardData = dict[str, list[DashboardEntry]]


def build_dashboard_data(
    history: list[dict[str, Any]],
) -> DashboardData:
    series: dict[str, list[DashboardEntry]] = defaultdict(list)

    for benchmark in history:
        timestamp = str(
            benchmark.get(
                "timestamp",
                "",
            )
        )

        runs = int(
            benchmark.get(
                "runs",
                1,
            )
        )

        aggregated_results = benchmark.get(
            "aggregated_results",
            [],
        )

        for result in aggregated_results:
            vector_store = result.get(
                "vector_store",
            )

            if not vector_store:
                continue

            series[str(vector_store)].append(
                {
                    "timestamp": timestamp,
                    "runs": runs,
                    "score": float(
                        result.get(
                            "score_avg",
                            0.0,
                        )
                    ),
                    "score_min": float(
                        result.get(
                            "score_min",
                            0.0,
                        )
                    ),
                    "score_max": float(
                        result.get(
                            "score_max",
                            0.0,
                        )
                    ),
                    "latency": float(
                        result.get(
                            "latency_avg",
                            0.0,
                        )
                    ),
                    "latency_min": float(
                        result.get(
                            "latency_min",
                            0.0,
                        )
                    ),
                    "latency_max": float(
                        result.get(
                            "latency_max",
                            0.0,
                        )
                    ),
                    "latency_std": float(
                        result.get(
                            "latency_std",
                            0.0,
                        )
                    ),
                    "retrieval_latency": float(
                        result.get(
                            "retrieval_avg",
                            0.0,
                        )
                    ),
                    "retrieval_min": float(
                        result.get(
                            "retrieval_min",
                            0.0,
                        )
                    ),
                    "retrieval_max": float(
                        result.get(
                            "retrieval_max",
                            0.0,
                        )
                    ),
                    "retrieval_std": float(
                        result.get(
                            "retrieval_std",
                            0.0,
                        )
                    ),
                    "rerank_latency": float(
                        result.get(
                            "rerank_avg",
                            0.0,
                        )
                    ),
                    "llm_latency": float(
                        result.get(
                            "llm_avg",
                            0.0,
                        )
                    ),
                    "tokens": float(
                        result.get(
                            "tokens_avg",
                            0.0,
                        )
                    ),
                    "cost": float(
                        result.get(
                            "cost_avg",
                            0.0,
                        )
                    ),
                    "fallbacks": int(
                        result.get(
                            "fallbacks",
                            0,
                        )
                    ),
                }
            )

    for vector_store_results in series.values():
        vector_store_results.sort(
            key=lambda item: item["timestamp"],
        )

    return dict(series)


def load_dashboard_data() -> DashboardData:
    history = load_benchmark_history()

    return build_dashboard_data(
        history=history,
    )


def build_dashboard_rows(
    history: list[dict[str, Any]],
) -> list[DashboardEntry]:
    dashboard_data = build_dashboard_data(
        history=history,
    )

    rows = []

    for vector_store, entries in dashboard_data.items():
        for entry in entries:
            rows.append(
                {
                    "vector_store": vector_store,
                    **entry,
                }
            )

    rows.sort(
        key=lambda item: (
            item["timestamp"],
            item["vector_store"],
        )
    )

    return rows


def load_dashboard_rows() -> list[DashboardEntry]:
    history = load_benchmark_history()

    return build_dashboard_rows(
        history=history,
    )


if __name__ == "__main__":
    from pprint import pprint

    pprint(
        load_dashboard_data(),
        sort_dicts=False,
    )
