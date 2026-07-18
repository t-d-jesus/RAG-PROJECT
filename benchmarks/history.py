import json
from pathlib import Path
from typing import Any

HISTORY_DIR = Path("benchmarks/history")


def ensure_history_dir() -> None:
    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def save_benchmark_to_history(
    benchmark: dict[str, Any],
) -> Path:
    ensure_history_dir()

    timestamp = benchmark["timestamp"]

    output_path = HISTORY_DIR / f"benchmark_{timestamp}.json"

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            benchmark,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def load_benchmark_history() -> list[dict[str, Any]]:
    ensure_history_dir()

    history = []

    for file_path in sorted(HISTORY_DIR.glob("benchmark_*.json")):
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            history.append(json.load(file))

    return history


def list_benchmarks() -> list[Path]:
    ensure_history_dir()

    return sorted(HISTORY_DIR.glob("benchmark_*.json"))


def get_latest_benchmark() -> dict[str, Any] | None:
    benchmarks = load_benchmark_history()

    if not benchmarks:
        return None

    return benchmarks[-1]


def get_benchmark_count() -> int:
    return len(list_benchmarks())


if __name__ == "__main__":
    print(f"Benchmarks encontrados: {get_benchmark_count()}")

    latest = get_latest_benchmark()

    if latest:
        print(f"Último benchmark: {latest['timestamp']}")
