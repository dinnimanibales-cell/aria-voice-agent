import os
import chromadb
from chromadb.utils import embedding_functions

COLLECTION_NAME = "documents"

_client = None
_collection = None
_embed_fn = None


def _get_embed_fn():
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = embedding_functions.DefaultEmbeddingFunction()
    return _embed_fn


def _get_collection():
    global _client, _collection
    if _collection is None:
        chroma_path = os.environ.get("CHROMA_PATH", "/tmp/chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=chroma_path)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embed_fn()
        )
    return _collection


def query_documents(query: str, k: int = 3):
    """Return top-k relevant chunks for a query."""
    if not query.strip():
        return []

    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=k,
        )
        documents = results.get("documents") or [[]]
        return documents[0]
    except Exception as exc:
        print(f"Retriever error: {exc}")
        return []