"""
Task 6 — Lexical Search Module (BM25).

Cơ chế BM25 (Best Matching 25):
    - Term Frequency (TF): tần suất từ xuất hiện trong văn bản
    - Inverse Document Frequency (IDF): từ càng hiếm trong corpus càng có trọng số cao
    - Document Length Normalization: cân bằng độ dài văn bản qua avgdl và tham số b
    - Tham số tối ưu: k1 = 1.5 (term saturation), b = 0.75 (length normalization)
"""

import json
import math
import re
import sys
from pathlib import Path

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
INDEX_FILE = CHROMA_DIR / "indexed_chunks.json"


def _tokenize(text: str) -> list[str]:
    """Tokenize văn bản tiếng Việt & tiếng Anh, loại bỏ ký tự đặc biệt."""
    text = text.lower()
    tokens = re.findall(r"\w+", text, re.UNICODE)
    return tokens


class SimpleBM25Okapi:
    """Triển khai thuật toán BM25Okapi chuẩn, độc lập và tối ưu."""

    def __init__(self, corpus_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.doc_lens = [len(doc) for doc in corpus_tokens]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 1.0

        self.doc_freqs: dict[str, int] = {}
        self.doc_tfs: list[dict[str, int]] = []

        for doc in corpus_tokens:
            tf: dict[str, int] = {}
            for word in doc:
                tf[word] = tf.get(word, 0) + 1
            self.doc_tfs.append(tf)

            for word in set(doc):
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        # Tính IDF: ln((N - n + 0.5) / (n + 0.5) + 1)
        self.idf: dict[str, float] = {}
        for word, freq in self.doc_freqs.items():
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        for q in query_tokens:
            if q not in self.idf:
                continue
            idf_val = self.idf[q]
            for idx in range(self.corpus_size):
                tf_val = self.doc_tfs[idx].get(q, 0)
                if tf_val > 0:
                    doc_len = self.doc_lens[idx]
                    denom = tf_val + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                    scores[idx] += idf_val * (tf_val * (self.k1 + 1.0)) / denom
        return scores


# Global cache
_CACHED_CORPUS: list[dict] = []
_CACHED_BM25 = None


def load_corpus() -> list[dict]:
    """Tải chunks từ indexed_chunks.json hoặc từ Task 4."""
    global _CACHED_CORPUS
    if _CACHED_CORPUS:
        return _CACHED_CORPUS

    chunks = []
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        except Exception:
            chunks = []

    if not chunks:
        from src.task4_chunking_indexing import load_documents, chunk_documents
        docs = load_documents()
        chunks = chunk_documents(docs)

    _CACHED_CORPUS = chunks
    return _CACHED_CORPUS


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    global _CACHED_BM25
    corpus_tokens = [_tokenize(doc["content"]) for doc in corpus]

    try:
        from rank_bm25 import BM25Okapi
        _CACHED_BM25 = BM25Okapi(corpus_tokens)
    except Exception:
        _CACHED_BM25 = SimpleBM25Okapi(corpus_tokens)

    return _CACHED_BM25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not query or not query.strip():
        return []

    corpus = load_corpus()
    if not corpus:
        return []

    global _CACHED_BM25
    if _CACHED_BM25 is None:
        _CACHED_BM25 = build_bm25_index(corpus)

    query_tokens = _tokenize(query)
    scores = _CACHED_BM25.get_scores(query_tokens)

    results = []
    for idx, doc in enumerate(corpus):
        score = float(scores[idx]) if idx < len(scores) else 0.0
        results.append({
            "content": doc["content"],
            "score": round(score, 4),
            "metadata": doc.get("metadata", {}),
            "source": "bm25"
        })

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    results = lexical_search("phương thức thanh toán shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
