from pathlib import Path
import chromadb

CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "chroma_db"

def retrieve(query: str, k: int = 3) -> list[dict]:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection("policies")
    res = collection.query(query_texts=[query], n_results=k)
    return [
        {"text": doc, "source": meta["source"], "distance": round(dist, 3)}
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]