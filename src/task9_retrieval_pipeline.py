"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song / tuần tự
    2. Merge kết quả qua RRF (Reciprocal Rank Fusion)
    3. Rerank kết quả
    4. Nếu best cosine score của semantic search < score_threshold → fallback sang PageIndex
    5. Trả về top_k results với đầy đủ metadata, score và source ('hybrid' hoặc 'pageindex')
"""

import sys
from pathlib import Path

# Đảm bảo import được cả khi chạy `python src/...` và `pytest`
sys.path.insert(0, str(Path(__file__).parent.parent))

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from src.task5_semantic_search import semantic_search
    from src.task6_lexical_search import lexical_search
    from src.task7_reranking import rerank, rerank_rrf
    from src.task8_pageindex_vectorless import pageindex_search
except ImportError:
    from task5_semantic_search import semantic_search
    from task6_lexical_search import lexical_search
    from task7_reranking import rerank, rerank_rrf
    from task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

# Calibrated cosine similarity threshold:
# Điểm tương đồng dense query liên quan: ~0.4 - 0.95
# Query lạc đề / nonsense: < 0.25
SCORE_THRESHOLD = 0.25
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với hybrid search và fallback logic.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm cosine gốc tối thiểu để kích hoạt fallback
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    if not query or not query.strip():
        return []

    fetch_k = max(top_k * 2, 10)

    # Step 1: Chạy song song semantic (dense) + lexical (sparse)
    try:
        dense_results = semantic_search(query, top_k=fetch_k)
    except Exception:
        dense_results = []

    try:
        sparse_results = lexical_search(query, top_k=fetch_k)
    except Exception:
        sparse_results = []

    # Step 2: Kiểm tra fallback dựa trên điểm Cosine gốc (dense_results)
    best_dense_score = float(dense_results[0]["score"]) if dense_results else 0.0

    if (not dense_results and not sparse_results) or (best_dense_score < score_threshold):
        # Fallback sang PageIndex Vectorless
        fallback_results = pageindex_search(query, top_k=top_k)
        if fallback_results:
            for item in fallback_results:
                item["source"] = "pageindex"
            return fallback_results[:top_k]

    # Step 3: Merge kết quả bằng RRF (Reciprocal Rank Fusion)
    merged_items = []
    if dense_results and sparse_results:
        merged_items = rerank_rrf([dense_results, sparse_results], top_k=fetch_k)
    elif dense_results:
        merged_items = dense_results[:fetch_k]
    elif sparse_results:
        merged_items = sparse_results[:fetch_k]

    # Đánh dấu nguồn gốc hybrid
    for item in merged_items:
        item["source"] = "hybrid"

    # Step 4: Rerank kết quả
    if use_reranking and merged_items:
        try:
            final_results = rerank(query, merged_items, top_k=top_k, method=RERANK_METHOD)
            for r in final_results:
                r["source"] = "hybrid"
        except Exception:
            final_results = merged_items[:top_k]
    else:
        final_results = merged_items[:top_k]

    # Đảm bảo source và các trường bắt buộc luôn chuẩn xác
    output = []
    for r in final_results[:top_k]:
        output.append({
            "content": r.get("content", ""),
            "score": round(float(r.get("score", 0.0)), 4),
            "metadata": r.get("metadata", {}),
            "source": r.get("source", "hybrid")
        })

    return output


if __name__ == "__main__":
    test_queries = [
        "What payment methods does Shopee support?",
        "How do I request a return or refund?",
        "What evidence do I need for a refund request?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] [{r['source']}] {r['content'][:80]}...")
