import os
import hashlib
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from backend.config import settings

COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


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

        os.makedirs(settings.CHROMA_PATH, exist_ok=True)

        texts = [chunk.page_content for chunk in chunks]
        embed_model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = embed_model.encode(
            texts,
            normalize_embeddings=True,
        ).tolist()
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

        client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
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
