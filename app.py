"""
RAG Chatbot — E-commerce Support (Starter Template)
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chạy:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="E-commerce Support RAG Chatbot",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Background & Glassmorphism Styling
import base64

def set_custom_background(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            b64_str = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <style>
            /* 1. Fullscreen Background & Container Transparency */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"], [data-testid="stToolbar"] {{
                background: transparent !important;
            }}
            .stApp {{
                background-image: linear-gradient(rgba(15, 23, 42, 0.4), rgba(15, 23, 42, 0.6)), url("data:image/png;base64,{b64_str}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            /* 2. Transparent Header Navbar */
            header[data-testid="stHeader"] {{
                background: transparent !important;
            }}
            /* 3. Glassmorphism Sidebar */
            section[data-testid="stSidebar"] {{
                background: rgba(15, 23, 42, 0.75) !important;
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
            }}
            section[data-testid="stSidebar"] *, 
            section[data-testid="stSidebar"] p, 
            section[data-testid="stSidebar"] span, 
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] h1, 
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3 {{
                color: #f8fafc !important;
            }}
            /* Suggestion Buttons in Sidebar (No White Background) */
            section[data-testid="stSidebar"] .stButton > button,
            section[data-testid="stSidebar"] button {{
                background: rgba(30, 41, 59, 0.75) !important;
                color: #f1f5f9 !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 12px !important;
                padding: 0.75rem 1rem !important;
                backdrop-filter: blur(10px) !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
                transition: all 0.2s ease-in-out !important;
            }}
            section[data-testid="stSidebar"] .stButton > button:hover,
            section[data-testid="stSidebar"] button:hover {{
                background: rgba(51, 65, 85, 0.9) !important;
                border-color: #38bdf8 !important;
                color: #ffffff !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 16px rgba(56, 189, 248, 0.25) !important;
            }}
            /* 4. Header Banner Card High Contrast */
            .header-banner {{
                background: rgba(15, 23, 42, 0.8) !important;
                backdrop-filter: blur(20px) !important;
                -webkit-backdrop-filter: blur(20px) !important;
                border-radius: 18px !important;
                padding: 2rem 2.5rem !important;
                margin-bottom: 2rem !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4) !important;
            }}
            .header-banner h1 {{
                color: #ffffff !important;
                font-size: 2.3rem !important;
                font-weight: 700 !important;
                margin-bottom: 0.5rem !important;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6) !important;
            }}
            .header-banner p {{
                color: #cbd5e1 !important;
                font-size: 1.1rem !important;
                margin: 0 !important;
            }}
            /* 5. Chat Container Cards */
            .stChatMessage {{
                background: rgba(15, 23, 42, 0.78) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border-radius: 16px !important;
                padding: 1.2rem 1.5rem !important;
                margin-bottom: 1rem !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
                border: 1px solid rgba(255, 255, 255, 0.18) !important;
                color: #f8fafc !important;
            }}
            .stChatMessage p, .stChatMessage span, .stChatMessage div {{
                color: #f8fafc !important;
            }}
            /* 6. Bottom Chat Input Area (No White Background) */
            [data-testid="stBottom"], [data-testid="stBottom"] > div {{
                background: transparent !important;
            }}
            [data-testid="stChatInput"], 
            [data-testid="stChatInput"] > div,
            [data-baseweb="input"],
            [data-baseweb="base-input"] {{
                background: rgba(15, 23, 42, 0.85) !important;
                backdrop-filter: blur(20px) !important;
                border-radius: 16px !important;
                border: 1px solid rgba(255, 255, 255, 0.25) !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
            }}
            [data-testid="stChatInput"] textarea, input {{
                color: #ffffff !important;
                background: transparent !important;
            }}
            /* 7. Chat Avatar Badges */
            [data-testid="stChatMessageAvatarUser"], [data-testid="chatAvatarIcon-user"] {{
                background: linear-gradient(135deg, #0ea5e9, #2563eb) !important;
                border-radius: 50% !important;
                border: 2px solid rgba(255, 255, 255, 0.4) !important;
                box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4) !important;
            }}
            [data-testid="stChatMessageAvatarAssistant"], [data-testid="chatAvatarIcon-assistant"] {{
                background: linear-gradient(135deg, #f59e0b, #ea580c) !important;
                border-radius: 50% !important;
                border: 2px solid rgba(255, 255, 255, 0.4) !important;
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

BG_IMAGE_PATH = r"C:\Users\Namdr\Downloads\Gemini_Generated_Image_5vdihz5vdihz5vdi.png"
set_custom_background(BG_IMAGE_PATH)

# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("🛒 E-commerce Support RAG")
    st.caption("Trợ lý hỏi đáp về chính sách thương mại điện tử và hỗ trợ khách hàng (đổi trả, thanh toán, bảo mật, người bán)")

    st.divider()

    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Thời hạn yêu cầu trả hàng/hoàn tiền là bao lâu?",
        "Shopee hỗ trợ những phương thức thanh toán nào?",
        "Làm sao để đổi phương thức thanh toán đơn hàng?",
        "Quy định về đăng bán sản phẩm cho người bán?",
        "Cách mua hàng trên Shopee của quốc gia khác?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:20]}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.subheader("⚙️ Thiết lập")
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")

# =============================================================================
# SESSION STATE
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.markdown(
    """
    <div class="header-banner">
        <h1>🛒 E-commerce Support RAG Chatbot</h1>
        <p>Hệ thống hỏi đáp chính sách thương mại điện tử và hỗ trợ khách hàng thông minh</p>
    </div>
    """,
    unsafe_allow_html=True
)

def format_score_display(score: float) -> str:
    """Format RRF score hoặc Cosine similarity score thành % trực quan cho người dùng."""
    if score <= 0.1:  # RRF Fusion Score (công thức toán 1/(60+rank_dense) + 1/(60+rank_sparse))
        pct = min(99.0, max(65.0, (score / 0.0328) * 96.0))
        return f"Độ phù hợp: **{pct:.1f}%** `RRF Score: {score:.4f}`"
    else:
        return f"Độ phù hợp: **{score * 100:.1f}%** `Score: {score:.4f}`"

USER_AVATAR = "👤"
BOT_AVATAR = "🛒"

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Unknown")
                    doc_type = meta.get("type", "unknown")
                    score = src.get("score", 0)
                    st.markdown(f"**[{i}] {source_name}** `{doc_type}` | {format_score_display(score)}")
                    st.text(src.get("content", "")[:300] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách/hỗ trợ e-commerce...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy hoàn thành `src/task10_generation.py` để kết nối pipeline vào UI!"
                sources = []
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        st.markdown(f"**[{i}] {source_name}** `{doc_type}` | {format_score_display(score)}")
                        st.text(src.get("content", "")[:300] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
