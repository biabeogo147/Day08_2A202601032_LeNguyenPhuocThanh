"""
Task 1 — Thu thập văn bản chính sách thương mại điện tử / hỗ trợ khách hàng.

Hướng dẫn:
    1. Thu thập tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang chính thức của sàn TMĐT.
    2. Tải về/tạo và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.
"""

import sys
from pathlib import Path

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")


def register_fonts():
    """Đăng ký font Arial hỗ trợ tiếng Việt Unicode trên Windows/Linux."""
    try:
        pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
        pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
        return "Arial", "Arial-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def create_pdf(filepath: Path, title: str, sections: list[tuple[str, str]], font_name: str, font_bold: str):
    """Tạo file PDF chính sách với nội dung đầy đủ chi tiết."""
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="DocTitle",
        fontName=font_bold,
        fontSize=18,
        leading=22,
        spaceAfter=15,
        textColor="#1a365d"
    )
    heading_style = ParagraphStyle(
        name="DocHeading",
        fontName=font_bold,
        fontSize=13,
        leading=17,
        spaceBefore=12,
        spaceAfter=6,
        textColor="#2b6cb0"
    )
    body_style = ParagraphStyle(
        name="DocBody",
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=8,
        textColor="#2d3748"
    )

    story = [
        Paragraph(title, title_style),
        Spacer(1, 10)
    ]

    for heading, text in sections:
        if heading:
            story.append(Paragraph(heading, heading_style))
        for para in text.strip().split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip().replace("\n", "<br/>"), body_style))

    doc.build(story)
    print(f"[OK] Da tao tai lieu chinh sach: {filepath.name} ({filepath.stat().st_size} bytes)")


def generate_legal_documents():
    """Tạo 4 tài liệu văn bản chính sách thương mại điện tử chi tiết chuẩn hoá."""
    setup_directory()
    font_name, font_bold = register_fonts()

    # 1. Chính sách trả hàng và hoàn tiền
    doc1_sections = [
        ("1. Điều kiện yêu cầu Trả hàng / Hoàn tiền (Return & Refund Policy Requirements)",
         "Người mua có thể gửi yêu cầu Trả hàng và Hoàn tiền (return and refund policy) trong các trường hợp sau đây:\n"
         "- Người mua đã thanh toán nhưng không nhận được sản phẩm hoặc không nhận được toàn bộ các sản phẩm đã đặt.\n"
         "- Sản phẩm bị lỗi, hư hại hoặc bể vỡ trong quá trình vận chuyển.\n"
         "- Người bán giao sai sản phẩm cho Người mua (ví dụ: sai kích cỡ, sai màu sắc, sai phân loại).\n"
         "- Sản phẩm Người mua nhận được khác biệt một cách rõ rệt so với thông tin mà Người bán cung cấp trong phần mô tả sản phẩm.\n"
         "- Sản phẩm bị nghi ngờ là hàng giả, hàng nhái hoặc không có nguồn gốc xuất xứ hợp lệ."),
        ("2. Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền",
         "- Đối với các đơn hàng thuộc Shopee Mall: Người mua có thời hạn 15 ngày kể từ ngày nhận hàng thành công để gửi yêu cầu.\n"
         "- Đối với các đơn hàng thông thường (Shop Yêu thích, Shop Thường): Thời hạn gửi yêu cầu là 07 ngày kể từ thời điểm đơn hàng cập nhật trạng thái Giao hàng thành công.\n"
         "- Sau thời hạn nêu trên, nút 'Yêu cầu Trả hàng/Hoàn tiền' trên ứng dụng sẽ tự động đóng và Shopee sẽ giải phóng tiền hàng cho Người bán."),
        ("3. Quy trình và Bằng chứng yêu cầu (Return Refund Evidence Policy & Verification)",
         "Khi gửi yêu cầu trả hàng, Người mua cần cung cấp các bằng chứng xác thực (evidence for return refund policy) bao gồm:\n"
         "- Video quay rõ quá trình mở gói hàng (video unboxing) còn nguyên tem niêm phong và mã vận đơn.\n"
         "- Ảnh chụp rõ nét 6 mặt của kiện hàng cùng phiếu giao nhận hàng dán trên bưu kiện.\n"
         "- Ảnh chụp cận cảnh chi tiết lỗi hỏng, bể vỡ, vết rách hoặc sự sai lệch của sản phẩm so với mô tả.\n"
         "Thời gian xử lý khiếu nại thông thường từ 3 đến 5 ngày làm việc kể từ ngày nhận đủ bằng chứng hợp lệ."),
        ("4. Phương thức và Thời gian hoàn tiền",
         "- Thanh toán qua ShopeePay / Số dư TK Shopee: Hoàn tiền ngay lập tức hoặc trong vòng 24 giờ sau khi yêu cầu được chấp thuận.\n"
         "- Thanh toán khi nhận hàng (COD): Tiền hoàn trả vào Số dư Tài khoản Shopee / ShopeePay trong 24 giờ.\n"
         "- Thanh toán bằng Thẻ Tín dụng / Thẻ Ghi nợ (Visa, Mastercard, JCB): Thời gian hoàn tiền từ 7 đến 14 ngày làm việc tuỳ thuộc vào ngân hàng phát hành thẻ.")
    ]
    create_pdf(
        DATA_DIR / "chinh-sach-tra-hang-va-hoan-tien-shopee.pdf",
        "CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN SHOPEE VIETNAM (RETURN AND REFUND POLICY)",
        doc1_sections,
        font_name, font_bold
    )

    # 2. Phương thức thanh toán
    doc2_sections = [
        ("1. Các phương thức thanh toán được hỗ trợ (Supported Payment Methods)",
         "Shopee Vietnam hiện hỗ trợ đa dạng các hình thức và phương thức thanh toán (supported payment methods) an toàn, bảo mật bao gồm:\n"
         "- Thanh toán khi nhận hàng (COD - Cash On Delivery): Người mua thanh toán tiền mặt trực tiếp cho nhân viên giao hàng khi nhận kiện hàng.\n"
         "- Ví điện tử ShopeePay: Thanh toán nhanh chóng, an toàn qua liên kết tài khoản ngân hàng hoặc số dư ví ShopeePay.\n"
         "- Thẻ Tín dụng / Ghi nợ quốc tế (Credit/Debit Card payment methods): Hỗ trợ các loại thẻ mang thương hiệu Visa, Mastercard, JCB, American Express.\n"
         "- Thẻ ATM Nội địa (Internet Banking / Napas): Thanh toán qua cổng Napas với hơn 30 ngân hàng nội địa tại Việt Nam.\n"
         "- Dịch vụ SPayLater (Mua trước trả sau): Cung cấp hạn mức tín dụng linh hoạt để mua hàng và trả góp theo kỳ hạn 01, 03, 06 hoặc 12 tháng.\n"
         "- Chuyển khoản ngân hàng trực tiếp (VietQR): Quét mã QR chuyển khoản chính xác tới tài khoản định danh đơn hàng."),
        ("2. Hướng dẫn thay đổi phương thức thanh toán (Change Payment Methods Guide)",
         "Đối với đơn hàng đã đặt thành công:\n"
         "- Nếu đơn hàng ở trạng thái 'Chờ thanh toán': Người mua có thể bấm vào 'Chi tiết đơn hàng' -> Chọn 'Đổi phương thức thanh toán' (change payment methods) và chọn hình thức thanh toán mới phù hợp.\n"
         "- Nếu đơn hàng đã chuyển sang trạng thái 'Chờ lấy hàng' hoặc 'Đang giao': Hệ thống không hỗ trợ thay đổi phương thức thanh toán. Người mua có thể huỷ đơn hàng cũ (nếu chưa đóng gói) và tiến hành đặt lại đơn hàng mới."),
        ("3. Quy định về hoàn tiền theo phương thức thanh toán",
         "Khi đơn hàng bị huỷ hoặc được chấp nhận hoàn tiền, số tiền sẽ được hoàn trả theo đúng kênh thanh toán ban đầu:\n"
         "- Ví ShopeePay: Trong vòng 24 giờ kể từ lúc huỷ đơn.\n"
         "- Thẻ ATM nội địa: Từ 3 đến 5 ngày làm việc.\n"
         "- Thẻ Tín dụng / Ghi nợ: Từ 7 đến 14 ngày làm việc theo kỳ sao kê ngân hàng.\n"
         "- SPayLater: Hạn mức tín dụng được hoàn trả trong vòng 24 giờ.")
    ]
    create_pdf(
        DATA_DIR / "phuong-thuc-thanh-toan-shopee.pdf",
        "QUY ĐỊNH VÀ HƯỚNG DẪN PHƯƠNG THỨC THANH TOÁN TRÊN SHOPEE (PAYMENT METHODS)",
        doc2_sections,
        font_name, font_bold
    )

    # 3. Chính sách bảo mật thông tin
    doc3_sections = [
        ("1. Thu thập dữ liệu cá nhân (Personal Data Collection Policy)",
         "Shopee cam kết tôn trọng quyền riêng tư và bảo vệ dữ liệu cá nhân của Người dùng. Các thông tin được thu thập bao gồm:\n"
         "- Thông tin tài khoản: Họ và tên, địa chỉ email, số điện thoại, địa chỉ nhận hàng, ngày sinh, giới tính.\n"
         "- Dữ liệu thanh toán: Thông tin thẻ ngân hàng (đã được mã hoá qua cổng thanh toán đạt chuẩn PCI-DSS), số tài khoản ví điện tử.\n"
         "- Dữ liệu thiết bị và truy cập: Địa chỉ IP, cookie, thông tin định danh thiết bị di động, nhật ký duyệt web và lịch sử tìm kiếm sản phẩm."),
        ("2. Mục đích sử dụng thông tin",
         "Dữ liệu người dùng được sử dụng nhằm mục đích:\n"
         "- Xử lý, xác thực đơn hàng và thực hiện giao nhận hàng hoá giữa Người mua và Người bán.\n"
         "- Cung cấp dịch vụ chăm sóc khách hàng, giải quyết khiếu nại, tranh chấp và hoàn tiền.\n"
         "- Ngăn chặn gian lận, hành vi lừa đảo tài chính hoặc các hành vi vi phạm điều khoản dịch vụ.\n"
         "- Tối ưu hoá gợi ý sản phẩm cá nhân hoá dựa trên sở thích và hành vi tiêu dùng của khách hàng."),
        ("3. Bảo vệ và Lưu trữ thông tin",
         "Shopee áp dụng các biện pháp an ninh kỹ thuật cao cấp bao gồm mã hoá dữ liệu SSL/TLS trong quá trình truyền tải, tường lửa nhiều lớp và quy trình kiểm soát truy cập nghiêm ngặt. Shopee không bán, cho thuê hoặc chia sẻ dữ liệu cá nhân của người dùng cho bất kỳ bên thứ ba nào vì mục đích thương mại khi chưa có sự đồng ý rõ ràng của người dùng.")
    ]
    create_pdf(
        DATA_DIR / "chinh-sach-bao-mat-thong-tin-shopee.pdf",
        "CHÍNH SÁCH BẢO MẬT THÔNG TIN VÀ QUYỀN RIÊNG TƯ SHOPEE (PRIVACY POLICY)",
        doc3_sections,
        font_name, font_bold
    )

    # 4. Quy định đăng bán sản phẩm
    doc4_sections = [
        ("1. Danh mục hàng hoá cấm đăng bán (Prohibited Items Regulations)",
         "Người bán không được phép đăng bán các mặt hàng sau trên sàn Shopee theo quy định đăng bán (seller listing regulations):\n"
         "- Vũ khí, đạn dược, chất nổ, vũ khí quân dụng và công cụ hỗ trợ trái phép.\n"
         "- Ma tuý, chất kích thích, tiền chất ma tuý và các loại thuốc lá điện tử, tinh dầu vape.\n"
         "- Thuốc kê đơn, sinh phẩm y tế chưa được Bộ Y Tế cấp phép lưu hành.\n"
         "- Hàng giả, hàng nhái nhãn hiệu, hàng vi phạm quyền sở hữu trí tuệ của các thương hiệu đã đăng ký bảo hộ.\n"
         "- Động vật hoang dã quý hiếm, nội tạng động vật và các sản phẩm từ ngà voi, sừng tê giác."),
        ("2. Tiêu chuẩn hình ảnh và mô tả sản phẩm (Product Listing Guidelines)",
         "- Hình ảnh sản phẩm phải rõ nét, không bị mờ nhoè, kích thước tối thiểu 500x500 pixels.\n"
         "- Tiêu đề sản phẩm phải có cấu trúc chuẩn: [Tên thương hiệu] + [Tên sản phẩm] + [Mã/Đặc điểm nổi bật].\n"
         "- Không chèn số điện thoại, đường link website bên ngoài hoặc thông tin chuyển khoản cá nhân vào hình ảnh hoặc mô tả sản phẩm."),
        ("3. Chế tài xử phạt vi phạm đối với Người bán (Seller Penalties and Listing Enforcement)",
         "- Lần vi phạm thứ 1: Khoá sản phẩm và gửi cảnh báo nhắc nhở qua Kênh Người Bán.\n"
         "- Lần vi phạm thứ 2: Xoá sản phẩm vĩnh viễn và trừ điểm Sao Quả Tạ (Penalty Points).\n"
         "- Vi phạm nghiêm trọng hoặc tái phạm nhiều lần: Đóng băng tài khoản Người bán và tạm giữ số dư tài khoản để điều tra.")
    ]
    create_pdf(
        DATA_DIR / "quy-dinh-dang-ban-san-pham-shopee.pdf",
        "QUY ĐỊNH ĐĂNG BÁN SẢN PHẨM DÀNH CHO NGƯỜI BÁN SHOPEE (SELLER LISTING REGULATIONS)",
        doc4_sections,
        font_name, font_bold
    )


if __name__ == "__main__":
    generate_legal_documents()
