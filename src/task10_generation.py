"""
Task 10 — Generation Có Citation & Document Reordering.

Hướng dẫn:
    1. Chọn top_k, top_p, temperature phù hợp cho tác vụ RAG factuality.
    2. Sắp xếp lại chunks sau reranking để tránh hiệu ứng "lost in the middle".
    3. Inject context có gắn nhãn nguồn (source metadata) vào prompt.
    4. Yêu cầu LLM trả lời kèm trích dẫn nguồn chuẩn xác [Tên tài liệu, Năm].
    5. Hỗ trợ đa dạng LLM provider: Google Gemini, OpenRouter, OpenAI, và Local Extractive Fallback.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo import được cả khi chạy `python src/...` và `pytest`
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from src.task9_retrieval_pipeline import retrieve
except ImportError:
    from task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# TOP_K = 5: Cung cấp đủ thông tin tham khảo và ngữ cảnh chi tiết mà không làm tràn context window
TOP_K = 5

# TOP_P = 0.9 (nucleus sampling): Đảm bảo từ ngữ phong phú, tự nhiên nhưng không bị lan man
TOP_P = 0.9

# TEMPERATURE = 0.2: RAG trong lĩnh vực chính sách và hỗ trợ TMĐT cần độ chính xác thực tế cao (factuality), tránh hallucination
TEMPERATURE = 0.2

# LLM Provider Model IDs (bắt buộc dùng Gemini 3.1 Flash Lite)
GEMINI_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")
OPENROUTER_MODEL = "openai/gpt-4o-mini"


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên gia về chính sách thương mại điện tử và dịch vụ khách hàng Shopee Vietnam (thanh toán, trả hàng hoàn tiền, vận chuyển, bảo mật thông tin và quy định người bán).

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin từ Context được cung cấp bên dưới — TUYỆT ĐỐI KHÔNG bịa đặt thông tin.
2. Mỗi thông tin, khẳng định đưa ra phải có trích dẫn nguồn cụ thể ngay sau câu văn, ví dụ: [chinh-sach-tra-hang-va-hoan-tien-shopee.pdf] hoặc [article_01.json].
3. Trả lời bằng tiếng Việt chuyên nghiệp, cấu trúc rõ ràng, đầy đủ các bước thực hiện nếu là bài hướng dẫn.
4. Nếu Context không chứa đủ thông tin để trả lời câu hỏi: Trả lời chính xác: "Tôi không thể xác minh thông tin này từ nguồn tài liệu hiện có."
"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để giảm thiểu hiệu ứng "Lost in the Middle".

    Mô hình LLM chú ý tốt nhất ở phần ĐẦU và phần CUỐI của context window,
    và có xu hướng giảm chú ý ở phần GIỮA.
    Chiến lược: Đặt chunk có score cao nhất ở đầu (0), score nhì ở cuối (1),
    các chunk có độ liên quan thấp hơn xếp xen kẽ ở giữa.

    Input (sorted descending):  [0, 1, 2, 3, 4]
    Output (reordered):        [0, 2, 4, 3, 1]

    Args:
        chunks: Danh sách chunks đã sort theo score giảm dần

    Returns:
        Danh sách chunks đã tái cấu trúc vị trí.
    """
    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]   # index 0, 2, 4, ...
    back = chunks[1::2]   # index 1, 3, 5, ...
    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format các chunks thành chuỗi văn bản hoàn chỉnh cho Prompt.
    Mỗi chunk được gắn kèm metadata rõ ràng (Document ID, Source filename, Type).

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Chuỗi context có cấu trúc phân đoạn.
    """
    if not chunks:
        return "Không có tài liệu tham khảo nào."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source") or metadata.get("path") or f"Document_{i}"
        doc_type = metadata.get("type", "standardized_doc")
        score = chunk.get("score", 0.0)

        header = f"[Tài liệu {i} | Nguồn: {source} | Loại: {doc_type} | Độ tương đồng: {score:.3f}]"
        body = chunk.get("content", "").strip()
        context_parts.append(f"{header}\n{body}")

    return "\n\n" + ("=" * 60) + "\n\n".join(["\n" + p for p in context_parts]) + "\n\n" + ("=" * 60)


def _generate_local_fallback_answer(query: str, chunks: list[dict]) -> str:
    """
    Tạo câu trả lời tổng hợp có trích dẫn nguồn khi chưa cấu hình API key
    hoặc môi trường test offline.
    """
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn tài liệu hiện có."

    primary_chunk = chunks[0]
    metadata = primary_chunk.get("metadata", {})
    source_name = metadata.get("source", "Tài liệu hệ thống")

    paragraphs = [p.strip() for p in primary_chunk["content"].split("\n") if p.strip() and not p.startswith("#")]
    extracted_text = " ".join(paragraphs[:3]) if paragraphs else primary_chunk["content"][:300]

    answer = (
        f"Dựa trên tài liệu hướng dẫn và quy định chính thức của Shopee Vietnam:\n\n"
        f"{extracted_text} [{source_name}]\n\n"
    )

    if len(chunks) > 1:
        sec_meta = chunks[1].get("metadata", {})
        sec_source = sec_meta.get("source", "Trung tâm trợ giúp Shopee")
        sec_paras = [p.strip() for p in chunks[1]["content"].split("\n") if p.strip() and not p.startswith("#")]
        sec_text = " ".join(sec_paras[:2]) if sec_paras else chunks[1]["content"][:200]
        answer += f"Bên cạnh đó, cần lưu ý thêm thông tin liên quan: {sec_text} [{sec_source}]."

    return answer.strip()


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(
    query: str,
    top_k: int = TOP_K,
    temperature: float = TEMPERATURE,
    retrieval_mode: str = "hybrid"
) -> dict:
    """
    End-to-end RAG generation với trích dẫn nguồn (citation).

    Pipeline:
        1. Retrieve relevant chunks (Hybrid / Dense / Lexical / PageIndex)
        2. Reorder chunks để tránh 'lost in the middle'
        3. Format context với source labels
        4. Gửi prompt đến LLM (Gemini / OpenRouter / OpenAI / Fallback)
        5. Trả về answer + sources

    Args:
        query: Câu hỏi của người dùng
        top_k: Số chunks context tối đa
        temperature: Nhiệt độ sáng tạo của LLM (0.0 - 1.0)
        retrieval_mode: Phương thức tìm kiếm ('hybrid', 'semantic', 'lexical', 'pageindex')

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Danh sách chunks đã dùng
            'retrieval_source': str  # 'hybrid', 'semantic', 'lexical', hoặc 'pageindex'
        }
    """
    if not query or not query.strip():
        return {
            "answer": "Vui lòng nhập câu hỏi của bạn.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 1: Retrieve theo mode
    if retrieval_mode == "semantic":
        try:
            from src.task5_semantic_search import semantic_search
            chunks = semantic_search(query, top_k=top_k)
        except ImportError:
            chunks = retrieve(query, top_k=top_k)
    elif retrieval_mode == "lexical":
        try:
            from src.task6_lexical_search import lexical_search
            chunks = lexical_search(query, top_k=top_k)
        except ImportError:
            chunks = retrieve(query, top_k=top_k)
    elif retrieval_mode == "pageindex":
        try:
            from src.task8_pageindex_vectorless import pageindex_search
            chunks = pageindex_search(query, top_k=top_k)
        except ImportError:
            chunks = retrieve(query, top_k=top_k)
    else:
        chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn tài liệu hiện có.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 2: Reorder
    reordered_chunks = reorder_for_llm(chunks)

    # Step 3: Format Context
    context_str = format_context(reordered_chunks)

    # Step 4: Build Prompt
    user_prompt = f"""Context tài liệu:\n{context_str}\n\n---\n\nCâu hỏi: {query}\n\nHãy trả lời chi tiết, chính xác kèm trích dẫn nguồn theo đúng quy tắc."""

    answer = None

    # Step 5A: Thử dùng Google GenAI nếu có GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and not answer:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            model_name = os.getenv("LLM_MODEL", GEMINI_MODEL)
            response = client.models.generate_content(
                model=model_name,
                contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                config={"temperature": temperature, "top_p": TOP_P}
            )
            if response and response.text:
                answer = response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini generation API error: {e}")
            answer = None

    # Step 5B: Thử dùng OpenRouter / OpenAI nếu có API Key
    openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openrouter_key and not answer:
        try:
            from openai import OpenAI
            base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
            client = OpenAI(api_key=openrouter_key, base_url=base_url)
            model_name = OPENROUTER_MODEL if os.getenv("OPENROUTER_API_KEY") else "gpt-4o-mini"

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P
            )
            if response.choices and response.choices[0].message.content:
                answer = response.choices[0].message.content.strip()
        except Exception:
            answer = None

    # Step 5C: Fallback Extractive Synthesizer
    if not answer:
        answer = _generate_local_fallback_answer(query, reordered_chunks)

    retrieval_src = chunks[0].get("source", "hybrid") if chunks else "hybrid"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_src
    }


if __name__ == "__main__":
    test_queries = [
        "Shopee hỗ trợ những phương thức thanh toán nào?",
        "Làm sao để yêu cầu đổi trả hay hoàn tiền?",
        "Cần chuẩn bị bằng chứng gì khi khiếu nại hoàn tiền?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA:\n{result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
