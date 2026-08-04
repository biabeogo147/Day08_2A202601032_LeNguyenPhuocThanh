"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft / PyPDF:
    https://github.com/microsoft/markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import sys
from pathlib import Path

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Thử khởi tạo MarkItDown, nếu lỗi dùng pypdf
    md_converter = None
    try:
        from markitdown import MarkItDown
        md_converter = MarkItDown()
    except Exception:
        md_converter = None

    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting legal doc: {filepath.name}")
            output_path = output_dir / f"{filepath.stem}.md"
            content = ""

            if md_converter is not None:
                try:
                    result = md_converter.convert(str(filepath))
                    content = result.text_content
                except Exception:
                    content = ""

            # Fallback sang pypdf nếu markitdown chưa có kết quả
            if not content.strip() and filepath.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(str(filepath))
                    extracted_pages = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            extracted_pages.append(t)
                    content = "\n\n".join(extracted_pages)
                except Exception as e:
                    print(f"  Error reading {filepath.name} with pypdf: {e}")

            if content:
                output_path.write_text(content, encoding="utf-8")
                print(f"  [OK] Saved: {output_path.name} ({len(content)} chars)")
            else:
                print(f"  [WARN] Khong the extract text tu {filepath.name}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() == ".json":
            print(f"Converting news article: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            output_path = output_dir / f"{filepath.stem}.md"

            # Thêm metadata header
            header = f"# {data.get('title', 'Unknown')}\n\n"
            header += f"**Source:** {data.get('url', 'N/A')}\n"
            header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"

            content = header + data.get("content_markdown", "")
            output_path.write_text(content, encoding="utf-8")
            print(f"  [OK] Saved: {output_path.name} ({len(content)} chars)")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown / PyPDF)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n[OK] Done! Output tai:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
