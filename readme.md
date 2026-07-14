# RAG Project

Projeto de estudo de Retrieval-Augmented Generation (RAG) utilizando:

- OpenAI Embeddings
- OpenAI Responses API
- ChromaDB
- PDF, DOCX e imagens
- Reranking
- Hybrid Search
- Metadata Filtering
- Evaluation Framework

---

## Pré-requisitos

- Python 3.13+
- Conta OpenAI
- Chave de API OpenAI

---

## Instalação

Clone o projeto:

```bash
git clone <repositorio>
cd rag-project
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente:

Mac/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração da OpenAI

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Exemplo:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## Adicionando documentos

Coloque seus arquivos na pasta:

```txt
data/raw/
```

Exemplo:

```txt
data/raw/
├── documento.pdf
├── documento.docx
└── imagem.jpg
```

Tipos suportados:

- PDF
- DOCX
- JPG
- JPEG
- PNG

---

## Indexação dos documentos

Antes de consultar os documentos, é necessário gerar os embeddings e indexá-los no ChromaDB.

Execute:

```bash
python -m app.ingest
```

Exemplo de saída:

```txt
documento.pdf: 5 chunks indexados
documento.docx: 3 chunks indexados
imagem.jpg: 1 chunks indexados
```

---

## Consultando os documentos

Execute:

```bash
python -m app.query
```

Exemplo:

```txt
Pergunta: Qual filme é mencionado?
```

Para sair:

```txt
sair
```

ou

```txt
exit
```

---

## Executando a avaliação

O projeto possui uma suíte de testes para validar:

- Retrieval
- Reranking
- Answer Quality
- Metadata Filtering

Execute:

```bash
python -m tests.evaluate
```

Exemplo:

```txt
Resumo geral:
Total: 8
Retrieval: 8/8
Rerank: 8/8
Answer: 8/8
Overall: 8/8
Score: 100.00%
```

---

## Resetando a base vetorial

Caso queira recriar o índice:

```bash
python reset_chroma.py
```

Depois execute novamente a ingestão:

```bash
python -m app.ingest
```

---

## Estrutura do projeto

```txt
rag-project/
│
├── app/
│   ├── embeddings/
│   ├── loaders/
│   ├── retrieval/
│   ├── settings/
│   ├── vectorstore/
│   ├── chunker.py
│   ├── ingest.py
│   ├── query.py
│   └── ...
│
├── data/
│   └── raw/
│
├── tests/
│   ├── unit/
│   ├── results/
│   ├── evaluate.py
│   └── test_cases.py
│
├── chroma/
├── .env
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Funcionalidades

- PDF Loader
- DOCX Loader
- Image Loader (Vision)
- Chunking
- OpenAI Embeddings
- ChromaDB
- Hybrid Search
- Metadata Filtering
- Reranking
- Context Expansion
- Conversational Memory
- Evaluation Framework


## Releases

- v0.1.0 - Initial RAG
- v0.2.0 - Parent Retrieval
- v0.3.0 - Multi Collections
- v0.4.0 - Observability
- v0.5.0 - BM25 Hybrid Ranking


## Supported Vector Stores

The project supports multiple vector-store backends:

| Backend | Status |
|----------|----------|
| ChromaDB | ✅ |
| Qdrant   | ✅ |
| PostgreSQL + pgvector | ✅ |

Backend selection:

```bash
export VECTOR_STORE=chroma
```

```bash
export VECTOR_STORE=qdrant
```

```bash
export VECTOR_STORE=pgvector
```