from app.loaders.docx_loader import load_docx

text = load_docx("data/raw/rag_exemplo.docx")

print(text[:2000])
