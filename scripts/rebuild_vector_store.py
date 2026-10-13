from backend.app.rag.vector_store import build_vector_store


def main():
    """Rebuild the FAISS index using the current heritage documents."""

    print("=" * 55)
    print("HeritageAI - Rebuild Vector Store")
    print("=" * 55)
    print("Reading current documents and rebuilding the index...")

    try:
        build_vector_store()
        print("\nVector store rebuild completed successfully.")

    except (FileNotFoundError, ValueError) as error:
        print(f"\nVector store rebuild failed: {error}")
        raise


if __name__ == "__main__":
    main()