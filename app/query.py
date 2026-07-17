import time
import unicodedata

from openai import OpenAI

from app.confidence import calculate_confidence
from app.config import (
    CHAT_MODEL,
    ENABLE_DISTANCE_FILTER,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_CHUNKS,
    MAX_DISTANCE,
    MAX_HISTORY_MESSAGES,
    OPENAI_API_KEY,
    OPENAI_INPUT_PRICE_PER_MILLION,
    OPENAI_OUTPUT_PRICE_PER_MILLION,
    RERANK_TOP_K,
    RETRIEVAL_RESULTS,
    VECTOR_STORE,
)
from app.context_builder import build_context
from app.embeddings.openai_embeddings import create_embedding
from app.metadata_filter import detect_metadata_filter
from app.observability import timer
from app.question_rewriter import rewrite_question
from app.reranker import rerank
from app.retrieval.hybrid_search import hybrid_ranking
from app.retrieval.parent_retrieval import expand_with_parent
from app.vectorstore.store import (
    search_chunks,
    search_hybrid_chunks,
)

client = OpenAI(api_key=OPENAI_API_KEY)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )

    return without_accents.lower()


def is_negative_answer(answer: str) -> bool:
    normalized_answer = normalize_text(answer)

    return "nao encontrei essa informacao" in normalized_answer


def get_collections_from_filter(
    metadata_filter: dict | None,
) -> list[str]:
    if not metadata_filter:
        return [
            "documents",
            "images",
        ]

    if metadata_filter.get("document_type") == "image":
        return ["images"]

    return ["documents"]


def calculate_usage_cost(
    input_tokens: int,
    output_tokens: int,
) -> tuple[float, float, float]:
    input_cost_usd = input_tokens / 1_000_000 * OPENAI_INPUT_PRICE_PER_MILLION

    output_cost_usd = output_tokens / 1_000_000 * OPENAI_OUTPUT_PRICE_PER_MILLION

    estimated_cost_usd = input_cost_usd + output_cost_usd

    return (
        input_cost_usd,
        output_cost_usd,
        estimated_cost_usd,
    )


def ask(
    question: str,
    history: list[dict],
    metadata_filter: dict | None = None,
) -> tuple[
    str,
    list[dict],
    list[float],
    str,
    list[dict],
    list[str],
    list[str],
    dict,
    dict,
]:
    pipeline_metrics: dict = {
        "vector_store": VECTOR_STORE,
    }

    total_start = time.perf_counter()

    if metadata_filter is None:
        metadata_filter = detect_metadata_filter(
            question,
        )

    with timer(
        pipeline_metrics,
        "question_rewrite_time",
    ):
        rewritten_question = rewrite_question(
            question=question,
            conversation_history=history,
        )

    with timer(
        pipeline_metrics,
        "embedding_time",
    ):
        query_embedding = create_embedding(
            rewritten_question,
        )

    collection_names = get_collections_from_filter(
        metadata_filter,
    )

    documents: list[str] = []
    metadatas: list[dict] = []
    distances: list[float] = []

    native_hybrid_search = (
        VECTOR_STORE == "opensearch" and search_hybrid_chunks is not None
    )

    pipeline_metrics["retrieval_mode"] = (
        "opensearch_native_hybrid" if native_hybrid_search else "local_hybrid"
    )

    with timer(
        pipeline_metrics,
        "retrieval_time",
    ):
        for collection_name in collection_names:
            if native_hybrid_search:
                results = search_hybrid_chunks(
                    question=rewritten_question,
                    query_embedding=query_embedding,
                    n_results=RETRIEVAL_RESULTS,
                    where=metadata_filter,
                    collection_name=collection_name,
                )
            else:
                results = search_chunks(
                    query_embedding=query_embedding,
                    n_results=RETRIEVAL_RESULTS,
                    where=metadata_filter,
                    collection_name=collection_name,
                )

            documents.extend(
                results["documents"][0],
            )
            metadatas.extend(
                results["metadatas"][0],
            )
            distances.extend(
                results["distances"][0],
            )

    retrieved_sources = list({metadata["source"] for metadata in metadatas})

    all_candidates = list(
        zip(
            documents,
            metadatas,
            distances,
        )
    )

    if native_hybrid_search:
        candidates = all_candidates

        pipeline_metrics["hybrid_ranking_time"] = 0.0
    else:
        if ENABLE_DISTANCE_FILTER:
            candidates = [
                (
                    document,
                    metadata,
                    distance,
                )
                for (
                    document,
                    metadata,
                    distance,
                ) in all_candidates
                if distance <= MAX_DISTANCE
            ]
        else:
            candidates = all_candidates

        with timer(
            pipeline_metrics,
            "hybrid_ranking_time",
        ):
            candidates = hybrid_ranking(
                question=rewritten_question,
                candidates=candidates,
            )

    pipeline_metrics["collections"] = collection_names
    pipeline_metrics["retrieved_chunks"] = len(
        all_candidates,
    )
    pipeline_metrics["filtered_candidates"] = len(
        candidates,
    )

    if not candidates:
        confidence = {
            "level": "low",
            "score": 0.0,
            "reason": ("Nenhum candidato encontrado."),
        }

        pipeline_metrics["reranked_chunks"] = 0
        pipeline_metrics["expanded_chunks"] = 0
        pipeline_metrics["context_chunks"] = 0
        pipeline_metrics["context_chars"] = 0
        pipeline_metrics["input_tokens"] = 0
        pipeline_metrics["output_tokens"] = 0
        pipeline_metrics["total_tokens"] = 0
        pipeline_metrics["input_cost_usd"] = 0.0
        pipeline_metrics["output_cost_usd"] = 0.0
        pipeline_metrics["estimated_cost_usd"] = 0.0
        pipeline_metrics["image_fallback_used"] = False
        pipeline_metrics["total_time"] = round(
            time.perf_counter() - total_start,
            6,
        )

        return (
            ("Não encontrei essa informação nos documentos."),
            [],
            [],
            rewritten_question,
            [],
            retrieved_sources,
            [],
            confidence,
            pipeline_metrics,
        )

    candidate_documents = [document for document, _, _ in candidates]

    with timer(
        pipeline_metrics,
        "rerank_time",
    ):
        selected_indexes = rerank(
            question=rewritten_question,
            documents=candidate_documents,
            top_k=RERANK_TOP_K,
        )

    reranked_chunks = [candidates[index] for index in selected_indexes]

    reranked_sources = list({metadata["source"] for _, metadata, _ in reranked_chunks})

    pipeline_metrics["reranked_chunks"] = len(
        reranked_chunks,
    )

    with timer(
        pipeline_metrics,
        "parent_retrieval_time",
    ):
        selected_chunks = expand_with_parent(
            selected_chunks=reranked_chunks,
        )

    pipeline_metrics["expanded_chunks"] = len(
        selected_chunks,
    )

    with timer(
        pipeline_metrics,
        "context_build_time",
    ):
        context, citations = build_context(
            selected_chunks=selected_chunks,
            max_chunks=MAX_CONTEXT_CHUNKS,
            max_chars=MAX_CONTEXT_CHARS,
        )

    pipeline_metrics["context_chunks"] = len(
        citations,
    )
    pipeline_metrics["context_chars"] = len(
        context,
    )

    has_image_context = any(
        metadata.get("document_type") == "image" for _, metadata, _ in selected_chunks
    )

    with timer(
        pipeline_metrics,
        "llm_time",
    ):
        response = client.responses.create(
            model=CHAT_MODEL,
            input=f"""
Você é um assistente de RAG.

Regras:
- Responda apenas usando o contexto fornecido.
- Não invente informações.
- Verifique todo o contexto antes de concluir que a
  informação não foi encontrada.
- Se a resposta realmente não estiver no contexto,
  responda exatamente:
  "Não encontrei essa informação nos documentos."
- Ao usar a resposta negativa acima, não adicione
  citações, explicações ou qualquer outro texto.
- Quando a pergunta solicitar texto, título ou pergunta
  visível em uma imagem, copie exatamente o trecho
  correspondente presente no contexto.
- Para textos extraídos de imagens, não traduza,
  não parafraseie e não altere capitalização,
  pontuação ou idioma.
- Nas respostas baseadas no contexto, cite as
  referências utilizadas.
- Use o formato [1], [2], [3].

Contexto:

{context}

Pergunta:

{rewritten_question}
""",
        )

        answer = response.output_text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        image_fallback_used = has_image_context and is_negative_answer(answer)

        if image_fallback_used:
            fallback_response = client.responses.create(
                model=CHAT_MODEL,
                input=f"""
Extraia a resposta diretamente do contexto.

Regras obrigatórias:
- O contexto contém conteúdo extraído de uma imagem.
- Examine todo o contexto antes de responder.
- Identifique o texto que responde à pergunta.
- Copie esse texto exatamente como aparece.
- Não traduza.
- Não parafraseie.
- Preserve idioma, capitalização e pontuação.
- Não responda que a informação não foi encontrada
  se houver no contexto um trecho relacionado à
  pergunta.
- Inclua a referência utilizada no formato [1],
  [2] ou [3].

Contexto:

{context}

Pergunta:

{rewritten_question}
""",
            )

            answer = fallback_response.output_text

            input_tokens += fallback_response.usage.input_tokens
            output_tokens += fallback_response.usage.output_tokens

    total_tokens = input_tokens + output_tokens

    (
        input_cost_usd,
        output_cost_usd,
        estimated_cost_usd,
    ) = calculate_usage_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    pipeline_metrics["input_tokens"] = input_tokens
    pipeline_metrics["output_tokens"] = output_tokens
    pipeline_metrics["total_tokens"] = total_tokens
    pipeline_metrics["input_cost_usd"] = round(
        input_cost_usd,
        8,
    )
    pipeline_metrics["output_cost_usd"] = round(
        output_cost_usd,
        8,
    )
    pipeline_metrics["estimated_cost_usd"] = round(
        estimated_cost_usd,
        8,
    )
    pipeline_metrics["image_fallback_used"] = image_fallback_used

    sources = [
        {
            "source": metadata["source"],
            "file_type": metadata.get(
                "file_type",
            ),
            "document_type": metadata.get(
                "document_type",
            ),
            "chunk_index": metadata.get(
                "chunk_index",
            ),
        }
        for _, metadata, _ in selected_chunks
    ]

    selected_distances = [distance for _, _, distance in selected_chunks]

    confidence = calculate_confidence(
        sources=sources,
        distances=selected_distances,
    )

    pipeline_metrics["total_time"] = round(
        time.perf_counter() - total_start,
        6,
    )

    return (
        answer,
        sources,
        selected_distances,
        rewritten_question,
        citations,
        retrieved_sources,
        reranked_sources,
        confidence,
        pipeline_metrics,
    )


if __name__ == "__main__":
    history = []

    while True:
        question = input("\nPergunta: ")

        if question.lower() in [
            "sair",
            "exit",
            "quit",
        ]:
            break

        (
            answer,
            sources,
            distances,
            rewritten_question,
            citations,
            retrieved_sources,
            reranked_sources,
            confidence,
            pipeline_metrics,
        ) = ask(
            question=question,
            history=history,
        )

        print("\nConfiança:")
        print(f"{confidence['level']} ({confidence['score']}) - {confidence['reason']}")

        print(f"\nPergunta reescrita:\n{rewritten_question}")

        print("\nResposta:")
        print(answer)

        print(f"\nVector Store: {pipeline_metrics['vector_store']}")
        print(f"Retrieval Mode: {pipeline_metrics['retrieval_mode']}")

        print("\nFontes recuperadas:")
        for source in retrieved_sources:
            print(f"- {source}")

        print("\nFontes após reranking:")
        for source in reranked_sources:
            print(f"- {source}")

        print("\nChunks usados:")

        if not sources:
            print("- nenhum chunk relevante encontrado")
        else:
            for source, distance in zip(
                sources,
                distances,
            ):
                print(
                    f"- {source['source']} "
                    f"| type "
                    f"{source.get('document_type')} "
                    f"| chunk "
                    f"{source['chunk_index']} "
                    f"| distance="
                    f"{distance:.4f}"
                )

        print("\nReferências:")

        for citation in citations:
            print(
                f"{citation['reference']} "
                f"{citation['source']} "
                f"(chunk "
                f"{citation['chunk_index']}, "
                f"distance="
                f"{citation['distance']:.4f})"
            )

        print("\nMétricas:")

        for key, value in pipeline_metrics.items():
            print(f"- {key}: {value}")

        history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        history = history[-MAX_HISTORY_MESSAGES:]
