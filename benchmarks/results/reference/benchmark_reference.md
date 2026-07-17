# RAG Vector Store Benchmark

- Timestamp: `20260717_150420`
- Runs per vector store: `3`

## End-to-End Benchmark

| Vector Store | Score | Avg Latency | Std Dev | Avg Rerank | Avg LLM | Avg Tokens | Avg Cost | Fallbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| chroma | 100.00% | 3.6741s | 0.5255s | 1.3946s | 1.6738s | 725.80 | $0.00177525 | 0 |
| qdrant | 100.00% | 3.0373s | 0.2276s | 1.2341s | 1.2995s | 729.47 | $0.00178020 | 0 |
| pgvector | 100.00% | 3.1057s | 0.2344s | 1.3879s | 1.1904s | 714.91 | $0.00174910 | 0 |
| opensearch | 100.00% | 2.8918s | 0.2084s | 1.1964s | 1.2050s | 722.13 | $0.00175890 | 0 |

## Retrieval Benchmark

| Vector Store | Avg Retrieval | Min | Max | Std Dev |
|---|---:|---:|---:|---:|
| chroma | 0.0081s | 0.0079s | 0.0082s | 0.0002s |
| qdrant | 0.0288s | 0.0255s | 0.0328s | 0.0037s |
| pgvector | 0.0535s | 0.0514s | 0.0562s | 0.0025s |
| opensearch | 0.0720s | 0.0489s | 0.1132s | 0.0358s |

## Highlights

- Highest average score: chroma, qdrant, pgvector, opensearch (100.00%)
- Lowest average end-to-end latency: opensearch (2.8918s)
- Lowest average retrieval latency: chroma (0.0081s)
- Lowest end-to-end latency variation: opensearch (0.2084s)
- Lowest average token usage: pgvector (714.91)
- Lowest average cost per run: pgvector ($0.00174910)

## Notes

- End-to-end latency includes retrieval, reranking, LLM generation and fallback processing.
- Retrieval latency is the most direct metric for comparing vector-store performance.
- Token usage and cost may vary because each backend can produce a different chunk ordering and context.
- Results are specific to this dataset, configuration and local execution environment.
