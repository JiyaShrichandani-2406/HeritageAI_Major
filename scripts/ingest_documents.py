from backend.app.rag.document_loader import load_documents
from backend.app.rag.vector_store import build_vector_store


def main():
    """Validate the available heritage documents and build the vector store."""

    print("=" * 55)
    print("HeritageAI - Document Ingestion")
    print("=" * 55)

    try:
        documents = load_documents()

        if not documents:
            print("No documents found.")
            print("Add .txt files to data/raw/heritage/ and try again.")
            return

        print(f"Documents found: {len(documents)}")

        for number, document in enumerate(documents, start=1):
            text = document.get("text", "").strip()
            title = document.get("title", "Untitled")
            source_url = document.get("source_url", "")

            if not text:
                print(f"Skipping empty document: {title}")
                continue

            print(f"\n{number}. {title}")
            print(f"   File: {document.get('file_name', 'Unknown')}")
            print(f"   Characters: {len(text)}")
            print(f"   Source URL: {source_url or 'Not provided'}")

            if "example.org" in source_url.lower():
                print("   WARNING: Placeholder URL; source is not verified.")

        print("\nBuilding the vector store...")
        build_vector_store()

        print("\nDocument ingestion completed.")
        print("Check data/vector_store/ for the generated index and chunks.")

    except (FileNotFoundError, ValueError) as error:
        print(f"Ingestion failed: {error}")
        raise


if __name__ == "__main__":
    main()