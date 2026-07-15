import time

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
from app.vectorstore.store import search_chunks


client = OpenAI(api_key=OPENAI_API_KEY)


def get_collections_from_filter(
    metadata_filter: dict | None,
) -> list[str]:
    if not metadata_filter:
        return ["documents", "images"]

    if metadata_filter.get("document_type") == "image":
        return ["images"]

    return ["documents"]


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
    pipeline_metrics = {}
    pipeline_metrics["vector_store"] = VECTOR_STORE

    total_start = time.perf_counter()

    if metadata_filter is None:
        metadata_filter = detect_metadata_filter(question)

    with timer(pipeline_metrics, "question_rewrite_time"):
        rewritten_question = rewrite_question(
            question=question,
            conversation_history=history,
        )

    with timer(pipeline_metrics, "embedding_time"):
        query_embedding = create_embedding(rewritten_question)

    collection_names = get_collections_from_filter(metadata_filter)

    documents = []
    metadatas = []
    distances = []

    with timer(pipeline_metrics, "retrieval_time"):
        for collection_name in collection_names:
            results = search_chunks(
                query_embedding=query_embedding,
                n_results=RETRIEVAL_RESULTS,
                where=metadata_filter,
                collection_name=collection_name,
            )

            # Precisa ficar dentro do for.
            documents.extend(results["documents"][0])
            metadatas.extend(results["metadatas"][0])
            distances.extend(results["distances"][0])

    retrieved_sources = list({metadata["source"] for metadata in metadatas})

    all_candidates = list(zip(documents, metadatas, distances))

    if ENABLE_DISTANCE_FILTER:
        candidates = [
            (document, metadata, distance)
            for document, metadata, distance in all_candidates
            if distance <= MAX_DISTANCE
        ]
    else:
        candidates = all_candidates

    with timer(pipeline_metrics, "hybrid_ranking_time"):
        candidates = hybrid_ranking(
            question=rewritten_question,
            candidates=candidates,
        )

    pipeline_metrics["collections"] = collection_names
    pipeline_metrics["retrieved_chunks"] = len(all_candidates)
    pipeline_metrics["filtered_candidates"] = len(candidates)

    if not candidates:
        confidence = {
            "level": "low",
            "score": 0.0,
            "reason": "Nenhum candidato encontrado.",
        }

        pipeline_metrics["reranked_chunks"] = 0
        pipeline_metrics["expanded_chunks"] = 0
        pipeline_metrics["context_chunks"] = 0
        pipeline_metrics["context_chars"] = 0
        pipeline_metrics["total_time"] = round(
            time.perf_counter() - total_start,
            6,
        )

        return (
            "Não encontrei essa informação nos documentos.",
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

    with timer(pipeline_metrics, "rerank_time"):
        selected_indexes = rerank(
            question=rewritten_question,
            documents=candidate_documents,
            top_k=RERANK_TOP_K,
        )

    reranked_chunks = [candidates[index] for index in selected_indexes]

    # Fontes selecionadas diretamente pelo reranker.
    reranked_sources = list({metadata["source"] for _, metadata, _ in reranked_chunks})

    pipeline_metrics["reranked_chunks"] = len(reranked_chunks)

    with timer(pipeline_metrics, "parent_retrieval_time"):
        selected_chunks = expand_with_parent(
            selected_chunks=reranked_chunks,
        )

    pipeline_metrics["expanded_chunks"] = len(selected_chunks)

    with timer(pipeline_metrics, "context_build_time"):
        context, citations = build_context(
            selected_chunks=selected_chunks,
            max_chunks=MAX_CONTEXT_CHUNKS,
            max_chars=MAX_CONTEXT_CHARS,
        )
        if any(
            metadata.get("document_type") == "image"
            for _, metadata, _ in selected_chunks
        ):
            print("\nDEBUG CONTEXTO DE IMAGEM:")
            print(context)

    # Citações representam os chunks realmente incluídos no contexto.
    pipeline_metrics["context_chunks"] = len(citations)
    pipeline_metrics["context_chars"] = len(context)

    with timer(pipeline_metrics, "llm_time"):
        response = client.responses.create(
            model=CHAT_MODEL,
            input=f"""
Você é um assistente de RAG.

Regras:
- Responda apenas usando o contexto fornecido.
- Não invente informações.
- Se a resposta não estiver no contexto, diga:
  "Não encontrei essa informação nos documentos."
- Quando a pergunta solicitar o texto, título ou pergunta visível em uma imagem,
  transcreva literalmente o trecho correspondente presente no contexto.
- Sempre cite as referências utilizadas.
- Use o formato [1], [2], [3].

Contexto:

{context}

Pergunta:

{rewritten_question}
""",
        )

    sources = [
        {
            "source": metadata["source"],
            "file_type": metadata.get("file_type"),
            "document_type": metadata.get("document_type"),
            "chunk_index": metadata.get("chunk_index"),
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
        response.output_text,
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

        if question.lower() in ["sair", "exit", "quit"]:
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
        print("Fontes recuperadas:")
        for source in retrieved_sources:
            print(f"- {source}")

        print("\nFontes após reranking:")
        for source in reranked_sources:
            print(f"- {source}")

        print("\nChunks usados:")
        if not sources:
            print("- nenhum chunk relevante encontrado")
        else:
            for source, distance in zip(sources, distances):
                print(
                    f"- {source['source']} "
                    f"| type {source.get('document_type')} "
                    f"| chunk {source['chunk_index']} "
                    f"| distance={distance:.4f}"
                )

        print("\nReferências:")
        for citation in citations:
            print(
                f"{citation['reference']} "
                f"{citation['source']} "
                f"(chunk {citation['chunk_index']}, "
                f"distance={citation['distance']:.4f})"
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
