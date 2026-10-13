
def split_text(text, chunk_size=500, overlap=50):
    """
    Split text into smaller chunks.

    chunk_size: maximum number of characters per chunk
    overlap: characters repeated between consecutive chunks
    """
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = text.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


if __name__ == "__main__":
    from backend.app.rag.document_loader import load_documents

    documents = load_documents()

    for document in documents:
        chunks = split_text(document["text"])

        print("\nDocument:", document["title"])
        print("Total chunks:", len(chunks))

        for index, chunk in enumerate(chunks, start=1):
            print(f"\nChunk {index}:")
            print(chunk[:200])
