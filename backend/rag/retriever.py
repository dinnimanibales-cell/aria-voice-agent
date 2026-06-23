from backend.config import settings
from backend.rag.ingest import COLLECTION_NAME, EMBEDDING_MODEL

_client = None
_collection = None
_model = None


def _get_collection():
    global _client, _collection

    if _collection is None:
        try:
            import chromadb
        except ModuleNotFoundError as exc:
            raise ImportError(
                "Document retrieval requires the 'chromadb' package. "
                "Install it with: pip install chromadb"
            ) from exc

        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)

    return _collection


def _get_model():
    global _model

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            raise ImportError(
                "Document retrieval requires the 'sentence-transformers' package. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def query_documents(query: str, k: int = 3):
    """Return top-k relevant chunks for a query."""
    if not query.strip():
        return []

    try:
        collection = _get_collection()
        model = _get_model()
        query_embedding = model.encode(
            [query],
            normalize_embeddings=True,
        )[0].tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        documents = results.get("documents") or [[]]
        return documents[0]
    except Exception as exc:
        print(f"Retriever error: {exc}")
        return []
