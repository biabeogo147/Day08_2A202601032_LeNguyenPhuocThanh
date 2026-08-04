"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document (theo cấu trúc trang / section) thay vì embedding.

Cung cấp đầy đủ:
    1. Tích hợp PageIndex SDK / API khi có PAGEINDEX_API_KEY.
    2. Local Structural PageIndex Engine (phân tích cấu trúc tiêu đề, đề mục Markdown)
       khi chạy offline hoặc chưa cấu hình API key.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> list[str]:
    """
    Upload toàn bộ documents lên PageIndex (hoặc index cấu trúc cục bộ).

    Returns:
        List các document IDs / filenames đã được lập chỉ mục cấu trúc.
    """
    if not STANDARDIZED_DIR.exists():
        print(f"[WARN] Thu muc khong ton tai: {STANDARDIZED_DIR}")
        return []

    doc_ids = []

    # 1. Thử dùng PageIndex SDK nếu có API key
    if PAGEINDEX_API_KEY:
        try:
            from pageindex.client import PageIndexClient
            client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
            for md_file in STANDARDIZED_DIR.rglob("*.md"):
                resp = client.submit_document(str(md_file))
                doc_id = resp.get("doc_id") or resp.get("id") or md_file.name
                doc_ids.append(str(doc_id))
                print(f"  ✓ Uploaded to PageIndex: {md_file.name} -> {doc_id}")
            return doc_ids
        except Exception as e:
            print(f"[INFO] PageIndex API upload fallback to local structural index ({e})")

    # 2. Local structural document indexing
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        doc_ids.append(md_file.name)
        print(f"  ✓ Indexed structural doc: {md_file.name}")

    return doc_ids


def _parse_markdown_sections(text: str, filename: str) -> list[dict]:
    """Phân rã tài liệu Markdown thành các section dựa trên heading (#, ##, ###)."""
    lines = text.splitlines()
    sections = []
    current_title = filename
    current_lines = []

    for line in lines:
        if re.match(r"^#{1,3}\s+", line):
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append({
                        "title": current_title,
                        "content": sec_text,
                        "filename": filename
                    })
                current_lines = []
            current_title = re.sub(r"^#{1,3}\s+", "", line).strip()
        current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append({
                "title": current_title,
                "content": sec_text,
                "filename": filename
            })

    return sections


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex (hoặc Local Structural Document Engine).
    Dùng làm nguồn retrieval độc lập hoặc fallback khi hybrid search không đủ tự tin.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'
        }
    """
    if not query or not query.strip():
        return []

    # 1. Thử dùng PageIndex API nếu có API key
    if PAGEINDEX_API_KEY:
        try:
            from pageindex.client import PageIndexClient
            client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
            resp = client.submit_query(query=query)
            retrieval_id = resp.get("retrieval_id") or resp.get("id")
            if retrieval_id:
                retrieval = client.get_retrieval(retrieval_id)
                results = []
                for node in retrieval.get("retrieved_nodes", []):
                    for group in node.get("relevant_contents", []):
                        for item in group:
                            results.append({
                                "content": item.get("relevant_content", ""),
                                "score": 0.85,
                                "metadata": {"section": item.get("section_title")},
                                "source": "pageindex"
                            })
                if results:
                    return results[:top_k]
        except Exception:
            pass

    # 2. Local Structural Tree Search (Vectorless)
    if not STANDARDIZED_DIR.exists():
        return []

    all_sections = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            sections = _parse_markdown_sections(content, md_file.name)
            all_sections.extend(sections)
        except Exception:
            continue

    q_lower = query.lower()
    q_words = re.findall(r"\w+", q_lower, re.UNICODE)

    scored_sections = []
    for sec in all_sections:
        title_lower = sec["title"].lower()
        content_lower = sec["content"].lower()

        # Điểm tiêu đề (heading match)
        title_hits = sum(1 for w in q_words if w in title_lower)
        title_score = (title_hits / len(q_words)) if q_words else 0.0

        # Điểm nội dung
        content_hits = sum(1 for w in q_words if w in content_lower)
        content_score = (content_hits / len(q_words)) if q_words else 0.0

        # Phrase match bonus
        phrase_bonus = 0.3 if q_lower in content_lower or q_lower in title_lower else 0.0

        combined_score = 0.5 * title_score + 0.3 * content_score + phrase_bonus
        if combined_score > 0:
            scored_sections.append({
                "content": sec["content"],
                "score": round(min(combined_score, 1.0), 4),
                "metadata": {
                    "source": sec["filename"],
                    "section_title": sec["title"],
                    "type": "structural_pageindex"
                },
                "source": "pageindex"
            })

    # Sort descending
    scored_sections.sort(key=lambda x: x["score"], reverse=True)

    if not scored_sections and all_sections:
        # Fallback: trả về section đầu tiên nếu không có match rõ ràng
        return [{
            "content": all_sections[0]["content"],
            "score": 0.1,
            "metadata": {"source": all_sections[0]["filename"], "section_title": all_sections[0]["title"]},
            "source": "pageindex"
        }]

    return scored_sections[:top_k]


if __name__ == "__main__":
    print("Testing PageIndex Search:")
    res = pageindex_search("phương thức thanh toán shopee", top_k=3)
    for r in res:
        print(f"[{r['source']} - score {r['score']:.3f}] {r['metadata'].get('section_title')}")
        print(f"  {r['content'][:120]}...\n")
