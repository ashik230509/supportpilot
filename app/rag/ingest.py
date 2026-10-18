from pathlib import Path
import chromadb

POLICY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "policies"
CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "chroma_db"

def chunk_markdown(text: str):
    """Split a markdown file into chunks at '## ' headings."""
    chunks = []
    for part in text.split("\n## ")[1:] if "\n## " in text else []:
        chunks.append("## " + part.strip())
    return chunks

def ingest():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection("policies")
    except Exception:
        pass
    collection = client.create_collection("policies")

    docs, ids, metas = [], [], []
    for file in sorted(POLICY_DIR.glob("*.md")):
        for i, chunk in enumerate(chunk_markdown(file.read_text(encoding="utf-8"))):
            docs.append(chunk)
            ids.append(f"{file.stem}-{i}")
            metas.append({"source": file.name})

    collection.add(documents=docs, ids=ids, metadatas=metas)
    print(f"Ingested {len(docs)} chunks from {len(set(m['source'] for m in metas))} files")

if __name__ == "__main__":
    ingest()