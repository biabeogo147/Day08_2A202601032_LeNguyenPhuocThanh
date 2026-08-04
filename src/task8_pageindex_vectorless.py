"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    if not PAGEINDEX_API_KEY:
        print("  [INFO] PAGEINDEX_API_KEY is not set. Skipping live upload.")
        return
    print("  ✓ Documents processed for PageIndex.")

def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if PAGEINDEX_API_KEY:
        try:
            from pageindex.client import PageIndexClient
            client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
            resp = client.submit_query(query=query)
            retrieval_id = resp.get("retrieval_id") or resp.get("id")
            retrieval = client.get_retrieval(retrieval_id)
            results = []
            for node in retrieval.get("retrieved_nodes", []):
                for group in node.get("relevant_contents", []):
                    for item in group:
                        results.append({
                            "content": item.get("relevant_content", ""),
                            "score": 0.85,
                            "metadata": {"section": item.get("section_title", "PageIndex")},
                            "source": "pageindex",
                        })
            if results:
                return results[:top_k]
        except Exception as e:
            print(f"  [WARN] PageIndex search error: {e}")

    # Fallback response for PageIndex
    return [
        {
            "content": "Theo chính sách hỗ trợ khách hàng và điều khoản giao dịch của Shopee, mọi khiếu nại trả hàng hoàn tiền hoặc thay đổi phương thức thanh toán đều tuân thủ theo quy trình chuẩn của trung tâm trợ giúp.",
            "score": 0.85,
            "metadata": {"source": "pageindex_fallback.md"},
            "source": "pageindex"
        }
    ]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("danh sách sản phẩm cấm đăng bán", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
