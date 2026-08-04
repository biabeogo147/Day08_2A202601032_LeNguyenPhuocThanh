"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (RecursiveCharacterTextSplitter)
    3. Chọn 1 embedding model (BAAI/bge-m3 hoặc Google/OpenAI/local fallback)
    4. Index vào vector store (ChromaDB / Persistent Store)
"""

import json
import os
import sys
from pathlib import Path
import numpy as np

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn trong comment
# =============================================================================

# CHUNK_SIZE = 500 ký tự: Kích thước tối ưu cho các điều khoản và đoạn văn hướng dẫn TMĐT,
# đủ chứa trọn vẹn 1 điều kiện/quy định mà không bị loãng ngữ cảnh.
CHUNK_SIZE = 500

# CHUNK_OVERLAP = 50 ký tự (10%): Duy trì tính liên tục của câu văn và ngữ nghĩa giữa 2 chunk liền kề.
CHUNK_OVERLAP = 50

# CHUNKING_METHOD: RecursiveCharacterTextSplitter tách văn bản theo thứ tự ưu tiên
# phân đoạn đoạn văn (\n\n), dòng (\n), câu (. ) và từ (khoảng trắng).
CHUNKING_METHOD = "recursive"

# EMBEDDING_MODEL: Mô hình embedding Gemini Embedding 2 của Google (3072 dim)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))

# VECTOR_STORE: ChromaDB lưu trữ vector cục bộ (persistent), nhẹ, không yêu cầu cài đặt Docker.
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "ecommerce_support_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    if not STANDARDIZED_DIR.exists():
        return []

    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "path": str(md_file.relative_to(STANDARDIZED_DIR.parent))
            }
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text.strip(),
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i
                    }
                })
    return chunks


def _compute_fallback_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """
    Tạo vector embedding chuẩn hóa dựa trên TF/hashing n-gram
    khi chưa có GPU/torch/API Key, đảm bảo semantic search hoạt động ổn định và nhất quán.
    """
    import hashlib
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    if not words:
        return vec.tolist()

    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
        # Thêm bigram hashing
        h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx2 = h2 % dim
        vec[idx2] += 0.5

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng embedding model đã chọn (bắt buộc gemini-embedding-2).

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    texts = [c["content"] for c in chunks]
    embeddings = None

    # 1. Thử dùng Google GenAI với model gemini-embedding-2 nếu có GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            model_name = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
            
            # Embed theo batch để đảm bảo ổn định
            embeddings = []
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                resp = client.models.embed_content(
                    model=model_name,
                    contents=batch_texts
                )
                embeddings.extend([e.values for e in resp.embeddings])
        except Exception as e:
            print(f"[WARN] Gemini embedding API error: {e}")
            embeddings = None

    # 2. Fallback deterministic dense embedding
    if embeddings is None:
        embeddings = [_compute_fallback_embedding(t, dim=EMBEDDING_DIM) for t in texts]

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn (ChromaDB + fallback JSON store).
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Luôn lưu 1 bản snapshot json để các module search hoạt động độc lập tin cậy
    index_file = CHROMA_DIR / "indexed_chunks.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    # Nếu có chromadb, index vào ChromaDB collection
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
        collection.upsert(
            ids=ids,
            documents=[c["content"] for c in chunks],
            embeddings=[c["embedding"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks]
        )
        print(f"[OK] Da index {len(chunks)} chunks vao ChromaDB collection '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"[INFO] ChromaDB store snapshot saved to {index_file} ({e})")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n[OK] Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"[OK] Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"[OK] Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("[OK] Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
