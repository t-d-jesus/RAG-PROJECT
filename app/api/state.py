from typing import Any

_last_query_metrics: dict[str, Any] = {}


def save_query_metrics(metrics: dict[str, Any]) -> None:
    global _last_query_metrics
    _last_query_metrics = metrics.copy()


def get_last_query_metrics() -> dict[str, Any]:
    return _last_query_metrics.copy()
