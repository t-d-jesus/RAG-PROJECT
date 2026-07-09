from openai import OpenAI

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
)
from app.context_builder import build_context
from app.embeddings.openai_embeddings import create_embedding
from app.metadata_filter import detect_metadata_filter
from app.question_rewriter import rewrite_question
from app.reranker import rerank
from app.retrieval.hybrid_search import hybrid_ranking
from app.retrieval.parent_retrieval import expand_with_parent
from app.vectorstore.chroma_store import search_chunks
from app.confidence import calculate_confidence


client = OpenAI(api_key=OPENAI_API_KEY)


def get_collection_from_filter(
    metadata_filter: dict | None,
) -> str:
    if not metadata_filter:
        return "documents"

    if metadata_filter.get("document_type") == "image":
        return "images"

    return "documents"


def ask(
    question: str,
    history: list[dict],
    metadata_filter: dict | None = None,
) -> tuple[str, list[dict], list[float], str, list[dict], list[str], list[str]]:

    if metadata_filter is None:
        metadata_filter = detect_metadata_filter(question)

    rewritten_question = rewrite_question(
        question=question,
        conversation_history=history,
    )

    query_embedding = create_embedding(rewritten_question)

    def get_collection_from_filter(metadata_filter: dict | None) -> str:
        if not metadata_filter:
            return "documents"

        if metadata_filter.get("document_type") == "image":
            return "images"

        return "documents"

    collection_name = get_collection_from_filter(metadata_filter)

    results = search_chunks(
        query_embedding=query_embedding,
        n_results=RETRIEVAL_RESULTS,
        where=metadata_filter,
        collection_name=collection_name,
    )

    if metadata_filter:
        print(f"\nFiltro aplicado: {metadata_filter}")

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

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

    candidates = hybrid_ranking(
        question=rewritten_question,
        candidates=candidates,
    )

    if not candidates:
        confidence = {
            "level": "low",
            "score": 0.0,
            "reason": "Nenhum candidato encontrado.",
        }

        return (
            "Não encontrei essa informação nos documentos.",
            [],
            [],
            rewritten_question,
            [],
            retrieved_sources,
            [],
            confidence,
        )

    candidate_documents = [document for document, metadata, distance in candidates]

    selected_indexes = rerank(
        question=rewritten_question,
        documents=candidate_documents,
        top_k=RERANK_TOP_K,
    )

    selected_chunks = [candidates[index] for index in selected_indexes]

    print("\nDEBUG PARENT IDS:")
    for _, metadata, _ in selected_chunks:
        print(metadata)

    selected_chunks = expand_with_parent(
        selected_chunks=selected_chunks,
        collection_name=collection_name,
    )

    reranked_sources = list({metadata["source"] for _, metadata, _ in selected_chunks})

    context, citations = build_context(
        selected_chunks=selected_chunks,
        max_chunks=MAX_CONTEXT_CHUNKS,
        max_chars=MAX_CONTEXT_CHARS,
    )

    print(f"\nContexto enviado: {len(context)} caracteres")

    response = client.responses.create(
        model=CHAT_MODEL,
        input=f"""
Você é um assistente de RAG.

Regras:
- Responda apenas usando o contexto fornecido.
- Não invente informações.
- Se a resposta não estiver no contexto, diga:
  "Não encontrei essa informação nos documentos."
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
        for document, metadata, distance in selected_chunks
    ]

    selected_distances = [distance for document, metadata, distance in selected_chunks]

    confidence = calculate_confidence(
        sources=sources,
        distances=selected_distances,
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
        ) = ask(
            question=question,
            history=history,
        )

        print("\nConfiança:")
        print(f"{confidence['level']} ({confidence['score']}) - {confidence['reason']}")

        print(f"\nPergunta reescrita:\n{rewritten_question}")

        print("\nResposta:")
        print(answer)

        print("\nFontes recuperadas pelo Chroma:")
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

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        history = history[-MAX_HISTORY_MESSAGES:]
