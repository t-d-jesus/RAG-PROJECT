# Vector Store Benchmark

## Objective

Compare three vector-store backends used in this project:

- ChromaDB
- Qdrant
- PostgreSQL + pgvector

The goal is not to determine an absolute winner, but to understand trade-offs regarding:

- Ingestion performance
- Retrieval quality
- Operational complexity
- Production readiness

---

## Test Environment

Dataset:

- 1 image
- 2 small documents
- 2 larger documents

Approximate indexed chunks:

- Documents: ~25
- Images: ~1

Pipeline:

```txt
Load Documents
↓
Chunking
↓
OpenAI Embeddings
↓
Vector Store
↓
Hybrid Search (Vector + BM25)
↓
Reranker
↓
Parent Retrieval
↓
LLM
```

---

## Benchmark Results

### Ingestion Time

| Backend | Time |
|----------|--------|
| ChromaDB | 17.50s |
| Qdrant | 16.68s |
| PostgreSQL + pgvector | 14.68s |

---

### Evaluation Results

| Backend | Retrieval | Rerank | Answer | Overall |
|----------|----------|----------|----------|----------|
| ChromaDB | 15/15 | 15/15 | 15/15 | 15/15 |
| Qdrant | 15/15 | 15/15 | 15/15 | 15/15 |
| PostgreSQL + pgvector | 15/15 | 15/15 | 15/15 | 15/15 |

---

## Observations

### ChromaDB

Pros:

- Extremely simple setup
- Great for prototypes
- Easy local development

Cons:

- Less common in production environments
- Limited ecosystem compared to PostgreSQL and Qdrant

Recommended for:

- Learning
- PoCs
- Small internal tools

---

### Qdrant

Pros:

- Purpose-built vector database
- Excellent filtering capabilities
- High-performance ANN search
- Production-ready architecture

Cons:

- Additional infrastructure component
- Requires separate operational management

Recommended for:

- AI-first applications
- Large-scale vector search
- Semantic search platforms

---

### PostgreSQL + pgvector

Pros:

- SQL support
- JSONB support
- Joins and aggregations
- Existing operational knowledge
- Easy integration with transactional workloads

Cons:

- Not specialized exclusively for vector search
- May require additional tuning at scale

Recommended for:

- RAG applications integrated with business data
- Analytics + AI workloads
- Systems already using PostgreSQL

---

## Important Notes

This benchmark was executed on a small dataset.

Most of the ingestion time is dominated by:

- PDF parsing
- DOCX parsing
- Image OCR
- OpenAI Embedding generation

As a result, the differences between vector stores are not yet representative of large-scale workloads.

For larger datasets (100k+ chunks), dedicated vector databases such as Qdrant may show more significant advantages in retrieval performance.

---

## Conclusion

All three backends achieved:

```txt
15/15 Retrieval
15/15 Rerank
15/15 Answer
15/15 Overall
```

For the current project:

- ChromaDB is ideal for experimentation.
- Qdrant is the most specialized vector database.
- PostgreSQL + pgvector provides the best balance between AI and traditional data workloads.

The project now supports all three backends through a common adapter interface.