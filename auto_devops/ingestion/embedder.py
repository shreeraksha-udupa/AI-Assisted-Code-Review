import chromadb
from sentence_transformers import SentenceTransformer
from config.settings import CHROMA_PATH, EMBED_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"[embedder] Loading embedding model: {EMBED_MODEL}")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_and_store(chunks: list, collection_name: str = "codebase") -> chromadb.Collection:
    """Embed all chunks and upsert into ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    model = _get_model()
    texts = [c["text"] for c in chunks]
    ids   = [c["id"]   for c in chunks]
    metas = [c["metadata"] for c in chunks]

    BATCH = 128
    all_embeddings = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        all_embeddings.extend(model.encode(batch, show_progress_bar=False).tolist())
        print(f"  embedded {min(i + BATCH, len(texts))}/{len(texts)} chunks", end="\r")

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=all_embeddings,
        metadatas=metas
    )
    print(f"\n[embedder] Stored {len(chunks)} chunks in ChromaDB collection '{collection_name}'")
    return collection
