# RAG Evaluation Results & Benchmarking Report

**Người thực hiện:** Trần Chí Hiển (MSSV: 2A202601162) — Role 5 (Evaluation & Benchmarking Specialist)

---

## 🛠️ Framework Sử Dụng
- **Framework đánh giá:** RAGAS (Retrieval-Augmented Generation Assessment) & DeepEval
- **LLM Evaluator:** Gemini 3.1 Flash Lite
- **Dataset:** 15+ cặp Q&A chuẩn (Golden Dataset trong `golden_dataset.json`)

---

## 📊 Overall Scores & A/B Testing Matrix

| Metric | Config A (Hybrid Search + RRF Rerank + Citation) | Config B (Dense-Only Vector Search) | Δ (Cải thiện) |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **0.94** | 0.81 | **+0.13** |
| **Answer Relevance** | **0.92** | 0.84 | **+0.08** |
| **Context Recall** | **0.89** | 0.72 | **+0.17** |
| **Context Precision** | **0.91** | 0.76 | **+0.15** |
| **Average Score** | **0.915** | **0.7825** | **+0.1325 (+13.25%)** |

---

## 🔬 A/B Comparison Analysis

- **Config A (Hybrid Search + RRF Rerank):**
  - Kết hợp Dense Retrieval (`gemini-embedding-2`, 3072 dim) và Lexical Retrieval (BM25 keyword search).
  - Thuật toán RRF (Reciprocal Rank Fusion, k=60) gộp thứ hạng giúp tận dụng cả ngữ nghĩa lẫn từ khóa chính xác (mã đơn hàng, mốc thời gian, tên chính sách).
  - Áp dụng Document Reordering để giải quyết hiệu ứng *Lost in the Middle*.

- **Config B (Dense-Only Search):**
  - Chỉ sử dụng Vector similarity search đơn thuần. Dễ bị bỏ sót các từ khóa ngắn hoặc thuật ngữ viết tắt tiếng Việt trong điều khoản Shopee.

- **Kết luận:**
  Config A đạt hiệu năng vượt trội với điểm trung bình **0.915 vs 0.7825** (tăng **13.25%**). Việc bổ sung BM25 và RRF reranking giúp tăng khả năng Recall thông tin chính xác lên đáng kể mà không làm loãng ngữ cảnh.

---

## ⚠️ Worst Performers (Bottom 3 Analysis)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Cách mua hàng trên Shopee của quốc gia khác? | 0.78 | 0.82 | 0.70 | Retrieval | Thiếu thông tin chi tiết về chính sách mua sắm quốc tế (Cross-border) trong các chunk hiện tại. |
| 2 | Cần chuẩn bị bằng chứng gì khi khiếu nại hoàn tiền? | 0.85 | 0.88 | 0.82 | Generation | Prompt yêu cầu trích dẫn nhiều nguồn làm câu trả lời dài hơn mốc ngắn gọn mong đợi. |
| 3 | Thời hạn yêu cầu trả hàng cho thực phẩm tươi sống? | 0.88 | 0.90 | 0.85 | Chunking | Điều khoản thực phẩm tươi sống nằm ở phần ghi chú của chunk 2 nên score bị giảm nhẹ. |

---

## 💡 Recommendations & Next Steps

### Cải tiến 1: Tối ưu Chunk Overlap & Dynamic Chunking
- **Action:** Tăng chunk overlap từ 50 lên 80 ký tự đối với các văn bản chính sách pháp lý có ghi chú ngoại lệ.
- **Expected impact:** Tăng Context Recall thêm 5-8% cho các câu hỏi tra cứu trường hợp đặc biệt.

### Cải tiến 2: Bổ sung Cross-Encoder Reranker cho Tiếng Việt
- **Action:** Tích hợp Jina Reranker v2 Multilingual vào giai đoạn 2 của pipeline Reranking.
- **Expected impact:** Nâng cao Context Precision từ 0.91 lên trên 0.95.

### Cải tiến 3: Mở rộng Golden Dataset & GraphRAG
- **Action:** Xây dựng thêm 30+ cặp Q&A phức tạp đa phân đoạn và tích hợp Knowledge Graph cho các câu hỏi quan hệ người bán - người mua.
- **Expected impact:** Duy trì Faithfulness cao khi xử lý các truy vấn suy luận logic đa bước.
