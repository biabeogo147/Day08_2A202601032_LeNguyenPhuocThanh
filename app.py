"""
RAG Chatbot — E-commerce Support System
Streamlit Frontend App (Role 3: Nguyễn Văn Nam)
Giao diện hỏi đáp chính sách e-commerce và hỗ trợ khách hàng với RAG Pipeline.

Chạy:
    streamlit run app.py
"""

import os
import sys
import time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load môi trường & cấu hình path
load_dotenv()
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG & CUSTOM STYLING (Aesthetics & Modern Theme)
# =============================================================================

st.set_page_config(
    page_title="Shopee Support RAG Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS cho giao diện hiện đại, sang trọng
st.markdown(
    """
    <style>
    /* Gradient Header Styling */
    .main-header {
        background: linear-gradient(135deg, #ee4d2d 0%, #ff7337 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(238, 77, 45, 0.2);
    }
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.9) !important;
        margin-top: 8px;
        margin-bottom: 0;
        font-size: 1.05rem;
    }
    /* Metric & Badge Styling */
    .stBadge {
        background-color: #fce4e4;
        color: #ee4d2d;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
    }
    /* Source Card Styling */
    .source-box {
        border-left: 4px solid #ee4d2d;
        background-color: #fcfcfc;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_dict=True,
)

# =============================================================================
# SIDEBAR — CONTROLS & CONFIGURATIONS
# =============================================================================

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/fe/fe/Shopee.svg", width=120)
    st.title("🛒 E-Commerce RAG")
    st.caption("Trợ lý AI chính sách & Hỗ trợ khách hàng Shopee Vietnam")

    st.divider()

    # Thống kê & Model Info
    st.subheader("🤖 Hệ Thống & Mô Hình")
    st.markdown("**LLM:** `Gemini 3.1 Flash Lite`")
    st.markdown("**Embedding:** `Gemini Embedding 2` (3072 dim)")
    st.markdown("**Vector Store:** `ChromaDB` (Persistent)")

    st.divider()

    # Thiết lập RAG Pipeline
    st.subheader("⚙️ Cấu Hình RAG Pipeline")
    
    top_k = st.slider("Số chunks retrieval (top_k)", min_value=3, max_value=10, value=5, help="Số lượng đoạn văn bản tham khảo gửi vào context")
    
    temperature = st.slider("Độ sáng tạo (Temperature)", min_value=0.0, max_value=1.0, value=0.2, step=0.1, help="Nhiệt độ thấp giúp đảm bảo độ chính xác thực tế (factuality)")

    retrieval_mode_map = {
        "Hybrid Search (Semantic + BM25 + RRF)": "hybrid",
        "Semantic Search (Gemini Embedding 2)": "semantic",
        "Lexical Search (BM25 Only)": "lexical",
        "PageIndex Vectorless Fallback": "pageindex"
    }
    
    selected_mode_label = st.selectbox(
        "Chiến lược Retrieval",
        options=list(retrieval_mode_map.keys()),
        index=0,
        help="Chọn chiến lược truy vấn thông tin tài liệu"
    )
    retrieval_mode = retrieval_mode_map[selected_mode_label]

    st.divider()

    # Gợi ý câu hỏi
    st.subheader("💡 Câu Hỏi Gợi Ý")
    suggestions = [
        "Shopee hỗ trợ những phương thức thanh toán nào?",
        "Thời hạn yêu cầu trả hàng/hoàn tiền là bao lâu?",
        "Cần chuẩn bị bằng chứng gì khi khiếu nại hoàn tiền?",
        "Quy định đăng bán sản phẩm dành cho người bán?",
        "Thời gian xử lý hoàn tiền vào thẻ ATM/ShopeePay?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{hash(s)}"):
            st.session_state["pending_query"] = s

    st.divider()
    if st.button("🗑️ Xoá lịch sử hội thoại", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN UI AREA
# =============================================================================

st.markdown(
    """
    <div class="main-header">
        <h1>🛒 Shopee E-Commerce RAG Assistant</h1>
        <p>Hệ thống hỏi đáp chính sách & trợ giúp khách hàng TMĐT với trích dẫn nguồn chuẩn xác (Citations)</p>
    </div>
    """,
    unsafe_allow_dict=True,
)

# Hiển thị lịch sử trò chuyện
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Nếu là câu trả lời của trợ lý và có thông tin nguồn
        if msg["role"] == "assistant":
            sources = msg.get("sources", [])
            latency = msg.get("latency", 0.0)
            ret_src = msg.get("retrieval_source", "hybrid")
            
            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks | Via: `{ret_src}` | Latency: `{latency:.2f}s`)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown Document")
                        doc_type = meta.get("type", "standardized_doc")
                        score = src.get("score", 0.0)
                        
                        st.markdown(f"**[{i}] {source_name}** | Loại: `{doc_type}` | Score: `{score:.4f}`")
                        st.caption(src.get("content", "")[:350] + ("..." if len(src.get("content", "")) > 350 else ""))
                        if i < len(sources):
                            st.divider()

# =============================================================================
# QUERY PROCESSING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách thanh toán, đổi trả, bảo mật...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("🔍 Đang truy vấn tài liệu & tổng hợp câu trả lời từ Gemini 3.1 Flash Lite..."):
            start_time = time.time()
            try:
                from src.task10_generation import generate_with_citation
                
                response = generate_with_citation(
                    query=query,
                    top_k=top_k,
                    temperature=temperature,
                    retrieval_mode=retrieval_mode
                )
                
                answer = response.get("answer", "Tôi không thể tìm thấy câu trả lời phù hợp.")
                sources = response.get("sources", [])
                ret_source = response.get("retrieval_source", "hybrid")
                
            except Exception as e:
                answer = f"❌ **Lỗi khi thực thi RAG Pipeline:** {e}"
                sources = []
                ret_source = "error"
            
            elapsed = time.time() - start_time

            # Hiển thị câu trả lời
            st.markdown(answer)

            # Hiển thị nguồn tham khảo nếu có
            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks | Via: `{ret_source}` | Latency: `{elapsed:.2f}s`)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown Document")
                        doc_type = meta.get("type", "standardized_doc")
                        score = src.get("score", 0.0)
                        
                        st.markdown(f"**[{i}] {source_name}** | Loại: `{doc_type}` | Score: `{score:.4f}`")
                        st.caption(src.get("content", "")[:350] + ("..." if len(src.get("content", "")) > 350 else ""))
                        if i < len(sources):
                            st.divider()

    # Lưu lịch sử chat
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": ret_source,
        "latency": elapsed,
    })
