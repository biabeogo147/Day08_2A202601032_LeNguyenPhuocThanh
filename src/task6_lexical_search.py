"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path

import json
import re
from pathlib import Path

_CORPUS_CACHE = None

def _get_corpus():
    global _CORPUS_CACHE
    if _CORPUS_CACHE is None:
        indexed_json = Path(__file__).parent.parent / "chroma_db" / "indexed_chunks.json"
        if indexed_json.exists():
            with open(indexed_json, encoding="utf-8") as f:
                _CORPUS_CACHE = json.load(f)
        else:
            _CORPUS_CACHE = []
    return _CORPUS_CACHE

def build_bm25_index(corpus: list[dict]):
    try:
        from rank_bm25 import BM25Okapi
        tokenized = [re.findall(r"\w+", doc["content"].lower()) for doc in corpus]
        return BM25Okapi(tokenized)
    except Exception:
        return None

def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    corpus = _get_corpus()
    if not corpus:
        return []

    tokens = re.findall(r"\w+", query.lower())
    if not tokens:
        return []

    bm25 = build_bm25_index(corpus)
    if bm25:
        scores = bm25.get_scores(tokens)
        scored_chunks = []
        for idx, score in enumerate(scores):
            if score > 0:
                scored_chunks.append({
                    "content": corpus[idx]["content"],
                    "score": round(float(score), 4),
                    "metadata": corpus[idx]["metadata"]
                })
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    # Keyword overlap fallback if rank_bm25 is missing
    scored_chunks = []
    for doc in corpus:
        text = doc["content"].lower()
        score = sum(text.count(t) for t in tokens)
        if score > 0:
            scored_chunks.append({
                "content": doc["content"],
                "score": float(score),
                "metadata": doc["metadata"]
            })
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


if __name__ == "__main__":
    # Test
    results = lexical_search("phương thức thanh toán shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
