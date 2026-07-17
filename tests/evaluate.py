import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.query import ask
from tests.metrics import (
    contains_keywords,
    source_found,
    sources_from_dicts,
)
from tests.test_cases import TEST_CASES


def evaluate() -> None:
    results = []
    category_stats = defaultdict(
        lambda: {
            "total": 0,
            "retrieval_passed": 0,
            "rerank_passed": 0,
            "answer_passed": 0,
            "overall_passed": 0,
        }
    )

    for test_case in TEST_CASES:
        print(f"\nRodando: {test_case['id']}")

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
            question=test_case["question"],
            history=[],
        )

        retrieval_ok = source_found(
            actual_sources=retrieved_sources,
            expected_sources=test_case["expected_retrieval_sources"],
        )

        rerank_ok = source_found(
            actual_sources=reranked_sources,
            expected_sources=test_case["expected_rerank_sources"],
        )

        answer_ok = contains_keywords(
            answer=answer,
            expected_keywords=test_case["expected_keywords"],
        )

        final_sources = sources_from_dicts(sources)

        sources_ok = source_found(
            actual_sources=final_sources,
            expected_sources=test_case["expected_sources"],
        )

        overall_passed = retrieval_ok and rerank_ok and answer_ok and sources_ok

        result = {
            "id": test_case["id"],
            "category": test_case["category"],
            "question": test_case["question"],
            "rewritten_question": rewritten_question,
            "retrieval_ok": retrieval_ok,
            "rerank_ok": rerank_ok,
            "answer_ok": answer_ok,
            "sources_ok": sources_ok,
            "overall_passed": overall_passed,
            "answer": answer,
            "retrieved_sources": retrieved_sources,
            "reranked_sources": reranked_sources,
            "final_sources": final_sources,
            "citations": citations,
            "confidence": confidence,
            "metrics": metrics,
        }

        results.append(result)

        category = test_case["category"]
        category_stats[category]["total"] += 1

        if retrieval_ok:
            category_stats[category]["retrieval_passed"] += 1

        if rerank_ok:
            category_stats[category]["rerank_passed"] += 1

        if answer_ok:
            category_stats[category]["answer_passed"] += 1

        if overall_passed:
            category_stats[category]["overall_passed"] += 1

        print(f"Retrieval: {'PASSOU' if retrieval_ok else 'FALHOU'}")
        print(f"Rerank: {'PASSOU' if rerank_ok else 'FALHOU'}")
        print(f"Answer: {'PASSOU' if answer_ok else 'FALHOU'}")
        print(f"Sources: {'PASSOU' if sources_ok else 'FALHOU'}")
        print(f"Overall: {'PASSOU' if overall_passed else 'FALHOU'}")
        print(
            f"Confidence: {confidence['level']} "
            f"({confidence['score']}) - "
            f"{confidence['reason']}"
        )

        if not overall_passed:
            print("\nDEBUG FALHA:")
            print(f"Expected retrieval: {test_case['expected_retrieval_sources']}")
            print(f"Actual retrieval: {retrieved_sources}")
            print(f"Expected rerank: {test_case['expected_rerank_sources']}")
            print(f"Actual rerank: {reranked_sources}")
            print(f"Expected keywords: {test_case['expected_keywords']}")
            print(f"Answer: {answer}")

    total = len(results)
    overall_passed_total = sum(1 for result in results if result["overall_passed"])

    retrieval_passed_total = sum(1 for result in results if result["retrieval_ok"])

    rerank_passed_total = sum(1 for result in results if result["rerank_ok"])

    answer_passed_total = sum(1 for result in results if result["answer_ok"])

    print("\nResumo geral:")
    print(f"Total: {total}")
    print(f"Retrieval: {retrieval_passed_total}/{total}")
    print(f"Rerank: {rerank_passed_total}/{total}")
    print(f"Answer: {answer_passed_total}/{total}")
    print(f"Overall: {overall_passed_total}/{total}")
    print(f"Score: {overall_passed_total / total:.2%}")

    print("\nResumo por categoria:")

    for category, stats in category_stats.items():
        total_category = stats["total"]

        print(
            f"- {category}: "
            f"overall {stats['overall_passed']}/{total_category}, "
            f"retrieval {stats['retrieval_passed']}/{total_category}, "
            f"rerank {stats['rerank_passed']}/{total_category}, "
            f"answer {stats['answer_passed']}/{total_category}"
        )

    results_dir = Path("tests/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    output = {
        "timestamp": timestamp,
        "total": total,
        "overall_passed": overall_passed_total,
        "score": overall_passed_total / total,
        "category_stats": dict(category_stats),
        "results": results,
    }

    output_path = results_dir / f"evaluation_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print(f"\nResultado salvo em: {output_path}")


if __name__ == "__main__":
    evaluate()
