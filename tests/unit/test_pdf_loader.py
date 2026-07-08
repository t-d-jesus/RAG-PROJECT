from app.loaders.pdf_loader import load_pdf

text = load_pdf("data/raw/rag_exemplo.pdf")

print(text[:2000])
