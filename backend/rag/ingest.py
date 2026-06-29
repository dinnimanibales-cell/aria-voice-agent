import os
import hashlib
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions

from backend.config import settings

COLLECTION_NAME = "documents"


def ingest_document(file_path: str) -> int:
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")

    try:
        if ext == "pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)

        elif ext == "docx":
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(file_path)

        elif ext == "txt":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path, encoding="utf-8")

        else:
            return 0

        docs = loader.load()

        if not docs:
            return 0

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            return 0

        import chromadb

        chroma_path = os.environ.get("CHROMA_PATH", "/tmp/chroma_db")
        os.makedirs(chroma_path, exist_ok=True)

        texts = [chunk.page_content for chunk in chunks]

        # Use ChromaDB built-in embeddings — no sentence_transformers needed
        embed_fn = embedding_functions.ONNXMiniLM_L6_V2()
        embeddings = embed_fn(texts)

        file_key = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()
        ids = [f"{file_key}:{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                **chunk.metadata,
                "source": str(path),
                "chunk": idx,
            }
            for idx, chunk in enumerate(chunks)
        ]

        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn
        )
        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    except Exception as e:
        print(f"Ingest error: {e}")
        raise