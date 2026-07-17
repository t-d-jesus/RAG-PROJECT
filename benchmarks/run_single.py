import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import VECTOR_STORE
from benchmarks.benchmark_runner import run_benchmark


def save_result(
    result: dict[str, Any],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )


def print_summary(result: dict[str, Any]) -> None:
    print("\nResumo do benchmark:")
    print(f"- Vector store: {result['vector_store']}")
    print(f"- Score: {result['score']:.2%}")
    print(f"- Retrieval: {result['retrieval_score']:.2%}")
    print(f"- Rerank: {result['rerank_score']:.2%}")
    print(f"- Answer: {result['answer_score']:.2%}")
    print(f"- Avg total time: {result['avg_total_time']:.4f}s")
    print(f"- Avg retrieval time: {result['avg_retrieval_time']:.4f}s")
    print(f"- Avg tokens: {result['avg_total_tokens']:.2f}")
    print(f"- Total cost: ${result['total_cost_usd']:.8f}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    result = run_benchmark(
        vector_store=VECTOR_STORE,
    )

    if args.output is None:
        timestamp = datetime.now(
            timezone.utc,
        ).strftime("%Y%m%d_%H%M%S")

        output_path = Path(
            "benchmarks/results",
            f"benchmark_{VECTOR_STORE}_{timestamp}.json",
        )
    else:
        output_path = args.output

    save_result(
        result=result,
        output_path=output_path,
    )

    print_summary(result)

    print(f"\nResultado salvo em: {output_path}")


if __name__ == "__main__":
    main()
