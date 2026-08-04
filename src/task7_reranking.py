"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker (khi có API key)
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement — khuyến nghị vì không cần API key

Cơ chế RRF (Reciprocal Rank Fusion):
    - RRF(d) = Σ 1 / (k + rank_r(d)) với k=60
    - Hợp nhất xếp hạng từ nhiều thuật toán retrieval khác nhau (Semantic + BM25)
    - Không bị ảnh hưởng bởi thang đo điểm số khác biệt giữa Dense và Sparse search.
"""

import math
import os
import re
import sys
from typing import Optional
import numpy as np

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _tokenize(text: str) -> list[str]:
    """Tokenize văn bản tiếng Việt & tiếng Anh."""
    return re.findall(r"\w+", text.lower(), re.UNICODE)


def _compute_cosine_sim(vec1: list[float], vec2: list[float]) -> float:
    """Tính Cosine Similarity giữa 2 vector."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _compute_local_relevance(query: str, doc_text: str) -> float:
    """Tính điểm tương đồng văn bản đa tầng (Lexical Overlap + Jaccard + Character N-grams)."""
    q_tokens = _tokenize(query)
    d_tokens = _tokenize(doc_text)
    if not q_tokens or not d_tokens:
        return 0.0

    q_set = set(q_tokens)
    d_set = set(d_tokens)
    overlap = len(q_set.intersection(d_set))
    jaccard = overlap / len(q_set.union(d_set)) if len(q_set.union(d_set)) > 0 else 0.0
    recall = overlap / len(q_set) if len(q_set) > 0 else 0.0

    # Match phrase
    phrase_bonus = 0.3 if query.lower().strip() in doc_text.lower() else 0.0

    return float(0.5 * recall + 0.3 * jaccard + phrase_bonus)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Cross-Encoder (Jina Reranker API hoặc Local Multilingual Scorer).

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by score descending.
    """
    if not candidates:
        return []

    # 1. Thử dùng Jina Reranker API nếu có API key
    jina_key = os.getenv("JINA_API_KEY")
    if jina_key:
        try:
            import requests
            response = requests.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {jina_key}"},
                json={
                    "model": "jina-reranker-v2-base-multilingual",
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": min(top_k, len(candidates))
                },
                timeout=10
            )
            if response.status_code == 200:
                reranked = response.json().get("results", [])
                results = []
                for r in reranked:
                    idx = r["index"]
                    item = candidates[idx].copy()
                    item["score"] = round(float(r["relevance_score"]), 4)
                    item["source"] = item.get("source", "cross_encoder")
                    results.append(item)
                return results
        except Exception:
            pass

    # 2. Local Multilingual Scoring (kết hợp relevance score & original retrieval score)
    scored_candidates = []
    for c in candidates:
        rel_score = _compute_local_relevance(query, c["content"])
        orig_score = float(c.get("score", 0.0))
        # Chuẩn hóa kết hợp
        final_score = 0.6 * rel_score + 0.4 * orig_score
        item = c.copy()
        item["score"] = round(final_score, 4)
        scored_candidates.append(item)

    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    return scored_candidates[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    if not candidates:
        return []

    from src.task4_chunking_indexing import _compute_fallback_embedding

    # Đảm bảo mỗi candidate có embedding
    for c in candidates:
        if "embedding" not in c or not c["embedding"]:
            c["embedding"] = _compute_fallback_embedding(c["content"])

    selected_indices = []
    remaining_indices = list(range(len(candidates)))
    n_select = min(top_k, len(candidates))

    for _ in range(n_select):
        best_idx = None
        best_mmr_score = float("-inf")

        for idx in remaining_indices:
            doc_emb = candidates[idx]["embedding"]
            relevance = _compute_cosine_sim(query_embedding, doc_emb)

            if not selected_indices:
                max_sim_to_selected = 0.0
            else:
                max_sim_to_selected = max(
                    _compute_cosine_sim(doc_emb, candidates[sel_idx]["embedding"])
                    for sel_idx in selected_indices
                )

            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim_to_selected

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

    results = []
    for idx in selected_indices:
        item = candidates[idx].copy()
        results.append(item)

    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker: semantic, bm25, v.v.)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, theo Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    if not ranked_lists:
        return []

    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for r_list in ranked_lists:
        for rank, item in enumerate(r_list, start=1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in content_map:
                content_map[key] = item.copy()

    # Sort descending theo RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = round(score, 6)
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "auto",  # "cross_encoder" | "mmr" | "rrf" | "auto"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if not candidates:
        return []

    if method == "cross_encoder" or method == "auto":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        from src.task4_chunking_indexing import _compute_fallback_embedding
        q_emb = _compute_fallback_embedding(query)
        return rerank_mmr(q_emb, candidates, top_k)
    elif method == "rrf":
        # Nếu truyền 1 list of candidates, coi như 1 ranked list
        return rerank_rrf([candidates], top_k=top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Chính sách trả hàng và hoàn tiền Shopee trong 15 ngày", "score": 0.8, "metadata": {}},
        {"content": "Các phương thức thanh toán hỗ trợ trên Shopee Vietnam", "score": 0.6, "metadata": {}},
        {"content": "Quy định đăng bán sản phẩm dành cho người bán", "score": 0.5, "metadata": {}},
    ]
    results = rerank("chính sách trả hàng shopee", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.4f}] {r['content']}")
