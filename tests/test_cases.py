DOCUMENT_SOURCES = [
    "rag_exemplo.pdf",
    "rag_exemplo.docx",
    "rag_exemplo_maior.pdf",
    "rag_exemplo_maior.docx",
]

TEST_CASES = [
    {
        "id": "sydney_001",
        "category": "document",
        "question": "Quem é Sydney Sweeney?",
        "expected_keywords": [
            "atriz",
            "norte-americana",
        ],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_002",
        "category": "document",
        "question": "Quais séries são mencionadas?",
        "expected_keywords": [
            "Euphoria",
            "The White Lotus",
        ],
        "expected_sources": DOCUMENT_SOURCES,
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "sydney_003",
        "category": "document",
        "question": "Qual filme é mencionado?",
        "expected_keywords": [
            "Anyone But You",
        ],
        "expected_sources": [
            "rag_exemplo.pdf",
            "rag_exemplo.docx",
            "rag_exemplo_maior.pdf",
            "rag_exemplo_maior.docx",
        ],
        "expected_retrieval_sources": DOCUMENT_SOURCES,
        "expected_rerank_sources": DOCUMENT_SOURCES,
    },
    {
        "id": "image_001",
        "category": "image",
        "question": "O que perguntaram sobre Sydney Sweeney na imagem?",
        "expected_keywords": [
            "HOW WELL DOES SYDNEY SWEENEY KNOW HER IMDb PAGE",
        ],
        "expected_sources": [
            "imagem.jpg",
        ],
        "expected_retrieval_sources": [
            "imagem.jpg",
        ],
        "expected_rerank_sources": [
            "imagem.jpg",
        ],
    },
    {
        "id": "negative_001",
        "category": "negative",
        "question": "Qual é a data de nascimento de Sydney Sweeney?",
        "expected_keywords": [
            "Não encontrei essa informação",
        ],
        "expected_sources": [],
        "expected_retrieval_sources": [],
        "expected_rerank_sources": [],
    },
    {
        "id": "metadata_image_001",
        "category": "metadata",
        "question": "Busque apenas nas imagens: o que perguntaram sobre Sydney Sweeney?",
        "expected_keywords": [
            "HOW WELL DOES SYDNEY SWEENEY KNOW HER IMDb PAGE",
        ],
        "expected_sources": [
            "imagem.jpg",
        ],
        "expected_retrieval_sources": [
            "imagem.jpg",
        ],
        "expected_rerank_sources": [
            "imagem.jpg",
        ],
    },
    {
        "id": "metadata_pdf_001",
        "category": "metadata",
        "question": "Busque apenas nos PDFs: qual filme é mencionado sobre Sydney Sweeney?",
        "expected_keywords": [
            "Anyone But You",
        ],
        "expected_sources": [
            "rag_exemplo.pdf",
            "rag_exemplo_maior.pdf",
        ],
        "expected_retrieval_sources": [
            "rag_exemplo.pdf",
            "rag_exemplo_maior.pdf",
        ],
        "expected_rerank_sources": [
            "rag_exemplo.pdf",
            "rag_exemplo_maior.pdf",
        ],
    },
    {
        "id": "metadata_docx_001",
        "category": "metadata",
        "question": "Busque apenas nos arquivos Word: quais séries são mencionadas sobre Sydney Sweeney?",
        "expected_keywords": [
            "Euphoria",
            "The White Lotus",
        ],
        "expected_sources": [
            "rag_exemplo.docx",
            "rag_exemplo_maior.docx",
        ],
        "expected_retrieval_sources": [
            "rag_exemplo.docx",
            "rag_exemplo_maior.docx",
        ],
        "expected_rerank_sources": [
            "rag_exemplo.docx",
            "rag_exemplo_maior.docx",
        ],
    },
]
