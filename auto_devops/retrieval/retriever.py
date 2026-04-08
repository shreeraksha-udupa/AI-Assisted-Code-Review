import chromadb
from sentence_transformers import SentenceTransformer
from config.settings import CHROMA_PATH, EMBED_MODEL, RETRIEVAL_TOP_K


def get_collection(collection_name: str = "codebase") -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(collection_name)


def retrieve_context(query: str, collection=None, top_k: int = RETRIEVAL_TOP_K) -> list:
    """
    Given a natural-language or code query, return the top-k most relevant
    code chunks from the vector store.
    """
    if collection is None:
        collection = get_collection()

    model = SentenceTransformer(EMBED_MODEL)
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "path": meta["path"],
            "start_line": meta["start_line"],
            "end_line": meta["end_line"],
            "relevance_score": round(1 - dist, 4)
        })

    return chunks
