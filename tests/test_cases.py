DOCUMENT_SOURCES = [
    "rag_exemplo.pdf",
    "rag_exemplo.docx",
    "rag_exemplo_maior.pdf",
    "rag_exemplo_maior.docx",
]

PDF_SOURCES = [
    "rag_exemplo.pdf",
    "rag_exemplo_maior.pdf",
]

DOCX_SOURCES = [
    "rag_exemplo.docx",
    "rag_exemplo_maior.docx",
]

IMAGE_SOURCES = [
    "imagem.jpg",
]


TEST_CASES = [
    {
        "id": "sydney_001",
        "category": "document",
        "question": "Quem é Sydney Sweeney?",
        "expected_keywords": ["atriz", "norte-americana"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_002",
        "category": "document",
        "question": "Quais séries são mencionadas?",
        "expected_keywords": ["Euphoria", "The White Lotus"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_003",
        "category": "document",
        "question": "Qual filme é mencionado?",
        "expected_keywords": ["Anyone But You"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_004",
        "category": "document",
        "question": "Qual é a profissão de Sydney Sweeney?",
        "expected_keywords": ["atriz"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_005",
        "category": "document",
        "question": "Qual é a nacionalidade mencionada?",
        "expected_keywords": ["Estados Unidos"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_006",
        "category": "document",
        "question": "Para que este documento foi criado?",
        "expected_keywords": ["testar", "RAG"],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "image_001",
        "category": "image",
        "question": "O que perguntaram sobre Sydney Sweeney na imagem?",
        "expected_keywords": ["HOW WELL DOES SYDNEY SWEENEY KNOW HER IMDb PAGE"],
        "expected_sources": IMAGE_SOURCES,
        "expected_retrieval_sources": IMAGE_SOURCES,
        "expected_rerank_sources": IMAGE_SOURCES,
    },
    {
        "id": "image_002",
        "category": "image",
        "question": "Qual texto aparece na imagem?",
        "expected_keywords": ["HOW WELL DOES SYDNEY SWEENEY KNOW HER IMDb PAGE"],
        "expected_sources": IMAGE_SOURCES,
        "expected_retrieval_sources": IMAGE_SOURCES,
        "expected_rerank_sources": IMAGE_SOURCES,
    },
    {
        "id": "metadata_image_001",
        "category": "metadata",
        "question": (
            "Busque apenas nas imagens: o que perguntaram sobre Sydney Sweeney?"
        ),
        "expected_keywords": ["HOW WELL DOES SYDNEY SWEENEY KNOW HER IMDb PAGE"],
        "expected_sources": IMAGE_SOURCES,
        "expected_retrieval_sources": IMAGE_SOURCES,
        "expected_rerank_sources": IMAGE_SOURCES,
    },
    {
        "id": "metadata_pdf_001",
        "category": "metadata",
        "question": (
            "Busque apenas nos PDFs: qual filme é mencionado sobre Sydney Sweeney?"
        ),
        "expected_keywords": ["Anyone But You"],
        "expected_sources": PDF_SOURCES,
        "expected_retrieval_sources": PDF_SOURCES,
        "expected_rerank_sources": PDF_SOURCES,
    },
    {
        "id": "metadata_pdf_002",
        "category": "metadata",
        "question": "Busque apenas nos PDFs: quais séries são mencionadas?",
        "expected_keywords": ["Euphoria", "The White Lotus"],
        "expected_sources": PDF_SOURCES,
        "expected_retrieval_sources": PDF_SOURCES,
        "expected_rerank_sources": PDF_SOURCES,
    },
    {
        "id": "metadata_docx_001",
        "category": "metadata",
        "question": (
            "Busque apenas nos arquivos Word: "
            "quais séries são mencionadas sobre Sydney Sweeney?"
        ),
        "expected_keywords": ["Euphoria", "The White Lotus"],
        "expected_sources": DOCX_SOURCES,
        "expected_retrieval_sources": DOCX_SOURCES,
        "expected_rerank_sources": DOCX_SOURCES,
    },
    {
        "id": "metadata_docx_002",
        "category": "metadata",
        "question": "Busque apenas nos DOCX: qual filme é mencionado?",
        "expected_keywords": ["Anyone But You"],
        "expected_sources": DOCX_SOURCES,
        "expected_retrieval_sources": DOCX_SOURCES,
        "expected_rerank_sources": DOCX_SOURCES,
    },
    {
        "id": "negative_001",
        "category": "negative",
        "question": "Qual é a data de nascimento de Sydney Sweeney?",
        "expected_keywords": ["Não encontrei essa informação"],
        "expected_sources": [],
        "expected_retrieval_sources": [],
        "expected_rerank_sources": [],
    },
    {
        "id": "negative_002",
        "category": "negative",
        "question": "Qual é o endereço residencial de Sydney Sweeney?",
        "expected_keywords": ["Não encontrei essa informação"],
        "expected_sources": [],
        "expected_retrieval_sources": [],
        "expected_rerank_sources": [],
    },
]
