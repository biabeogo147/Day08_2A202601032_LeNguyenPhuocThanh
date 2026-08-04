"""
Task 5 — Semantic Search Module.

Module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.
"""

import json
import os
import sys
from pathlib import Path
import numpy as np

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
INDEX_FILE = CHROMA_DIR / "indexed_chunks.json"


def _get_query_embedding(query: str, dim: int = 1024) -> list[float]:
    """Tạo vector embedding cho câu truy vấn query."""
    # 1. Thử dùng Google GenAI nếu có API key
    if os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            resp = client.models.embed_content(
                model="text-embedding-004",
                contents=[query]
            )
            return resp.embeddings[0].values
        except Exception:
            pass

    # 2. Fallback hashing dense embedding
    from src.task4_chunking_indexing import _compute_fallback_embedding
    return _compute_fallback_embedding(query, dim=dim)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not query or not query.strip():
        return []

    # 1. Thử dùng ChromaDB nếu có
    try:
        import chromadb
        from src.task4_chunking_indexing import COLLECTION_NAME
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name=COLLECTION_NAME)
        query_emb = _get_query_embedding(query)

        results = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        if results and results.get("documents") and results["documents"][0]:
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                score = float(max(0.0, 1.0 - dist))
                output.append({
                    "content": doc,
                    "score": round(score, 4),
                    "metadata": meta,
                    "source": "semantic"
                })
            output.sort(key=lambda x: x["score"], reverse=True)
            return output[:top_k]
    except Exception:
        pass

    # 2. Fallback dùng snapshot indexed_chunks.json
    chunks = []
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        except Exception:
            chunks = []

    if not chunks:
        # Nếu chưa index, chạy nhanh index
        from src.task4_chunking_indexing import load_documents, chunk_documents, embed_chunks
        docs = load_documents()
        chunks = chunk_documents(docs)
        chunks = embed_chunks(chunks)

    if not chunks:
        return []

    query_emb = np.array(_get_query_embedding(query), dtype=np.float32)
    q_norm = np.linalg.norm(query_emb)

    scored_chunks = []
    for c in chunks:
        c_emb = np.array(c.get("embedding", []), dtype=np.float32)
        if c_emb.size == 0:
            continue
        c_norm = np.linalg.norm(c_emb)
        if q_norm > 0 and c_norm > 0:
            sim = float(np.dot(query_emb, c_emb) / (q_norm * c_norm))
        else:
            sim = 0.0

        scored_chunks.append({
            "content": c["content"],
            "score": round(sim, 4),
            "metadata": c.get("metadata", {}),
            "source": "semantic"
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


if __name__ == "__main__":
    results = semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
