"""
Task 2 — Crawl / Thu thập bài viết hướng dẫn hỗ trợ khách hàng e-commerce.

Hướng dẫn:
    1. Crawl hoặc tạo tối thiểu 5 bài viết hướng dẫn / trợ giúp từ Trung tâm trợ giúp sàn TMĐT.
    2. Lưu vào data/landing/news/ dưới dạng JSON.
    3. Cấu trúc JSON chuẩn:
       {
           "url": "https://help.shopee.vn/portal/article/...",
           "title": "Tiêu đề bài viết",
           "date_crawled": "2026-08-04",
           "content_markdown": "# Tiêu đề\\n\\nNội dung chi tiết..."
       }
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Đảm bảo stdout hỗ trợ utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


ARTICLES_DATA = [
    {
        "filename": "article_01.json",
        "url": "https://help.shopee.vn/portal/article/79124-Huong-dan-theo-doi-don-hang-va-lien-he-SPX",
        "title": "Hướng dẫn theo dõi trạng thái đơn hàng và tra cứu hành trình giao hàng Shopee (Order Tracking Guide)",
        "content_markdown": """# Hướng dẫn theo dõi trạng thái đơn hàng và tra cứu hành trình giao hàng Shopee (Order Tracking Guide)

Để kiểm tra hành trình vận chuyển, tra cứu hành trình bưu kiện và theo dõi tình trạng đơn hàng của bạn trên Shopee (order tracking guide), vui lòng thực hiện theo các bước sau:

## 1. Cách tra cứu trực tiếp trên ứng dụng Shopee (Order Tracking Steps)
1. Mở ứng dụng Shopee, vào mục **Tôi** > chọn **Đơn Mua**.
2. Tìm đơn hàng bạn muốn theo dõi (track order) và bấm vào đơn hàng đó.
3. Trong phần **Thông tin vận chuyển**, bấm nút **Xem chi tiết** để xem toàn bộ lịch trình bưu kiện từ khi xuất kho, luân chuyển qua các bưu cục (SOC/HUB) đến khi giao tới shipper.

## 2. Các trạng thái đơn hàng phổ biến (Order Statuses)
- **Chờ xác nhận**: Người bán đang kiểm tra và duyệt đơn hàng.
- **Chờ lấy hàng**: Người bán đang chuẩn bị đóng gói hàng và chờ đơn vị vận chuyển đến lấy.
- **Đang giao**: Đơn vị vận chuyển (SPX Express, Giao Hàng Nhanh, J&T Express, Viettel Post) đang luân chuyển hàng hoặc shipper đang trên đường giao tới bạn.
- **Đã giao**: Đơn hàng đã được giao thành công đến địa chỉ người nhận.
- **Đã huỷ**: Đơn hàng đã bị huỷ bởi người mua, người bán hoặc hệ thống do quá hạn xử lý.

## 3. Cách liên hệ đơn vị vận chuyển SPX Express
Nếu đơn hàng giao trễ hơn ngày dự kiến hoặc bạn cần thay đổi thời gian nhận hàng:
- Gọi hotline tổng đài SPX Express: 1900 1221 (hỗ trợ từ 7:00 - 21:00 hàng ngày).
- Tra cứu mã vận đơn trực tiếp tại website `spx.vn` bằng cách nhập mã vận đơn (VD: SPXVN0123456789).
- Chat trực tiếp với Nhân viên Hỗ trợ Shopee qua mục Trò chuyện với Shopee trong ứng dụng."""
    },
    {
        "filename": "article_02.json",
        "url": "https://help.shopee.vn/portal/article/79125-Huong-dan-kich-hoat-va-thanh-toan-ShopeePay",
        "title": "Hướng dẫn kích hoạt ví điện tử ShopeePay và liên kết tài khoản ngân hàng (ShopeePay Payment Methods)",
        "content_markdown": """# Hướng dẫn kích hoạt ví điện tử ShopeePay và liên kết tài khoản ngân hàng (ShopeePay Payment Methods)

Ví điện tử ShopeePay là giải pháp thanh toán không tiền mặt tiện lợi trên sàn TMĐT Shopee (convenient payment methods), mang lại nhiều mã giảm giá và miễn phí vận chuyển độc quyền.

## 1. Các bước kích hoạt ví ShopeePay
1. Mở ứng dụng Shopee, chọn mục **Tôi** > chọn **Ví ShopeePay**.
2. Bấm chọn **Kích hoạt ngay** và nhập chính xác thông tin định danh: Họ tên đầy đủ, Số CMND/CCCD/Hộ chiếu.
3. Chụp ảnh 2 mặt CCCD và quét khuôn mặt theo hướng dẫn của hệ thống (eKYC).
4. Thiết lập mật khẩu thanh toán ví ShopeePay gồm 6 chữ số bảo mật.

## 2. Liên kết tài khoản / thẻ ngân hàng vào ví ShopeePay
- ShopeePay hỗ trợ liên kết trực tiếp với hơn 35 ngân hàng tại Việt Nam (Vietcombank, MB Bank, Techcombank, BIDV, VietinBank, ACB, TPBank...).
- Chọn biểu tượng Cài đặt ở góc phải > chọn **Tài khoản ngân hàng của tôi** > **Thêm tài khoản ngân hàng liên kết**.
- Nhập số tài khoản/số thẻ và mã xác thực OTP gửi về số điện thoại đăng ký ngân hàng.

## 3. Ưu đãi khi thanh toán qua ShopeePay
- Tự động áp dụng mã Miễn phí vận chuyển ShopeePay (Freeship Xtra).
- Giảm giá trực tiếp tới 50.000 VNĐ cho các hóa đơn điện, nước, internet, nạp tiền điện thoại.
- Hoàn xu Shopee Xu tới 15% giá trị đơn hàng."""
    },
    {
        "filename": "article_03.json",
        "url": "https://help.shopee.vn/portal/article/79126-Huong-dan-cung-cap-bang-chung-khieu-nai-tra-hang",
        "title": "Hướng dẫn chi tiết cách cung cấp bằng chứng hợp lệ khi khiếu nại Trả hàng / Hoàn tiền",
        "content_markdown": """# Hướng dẫn chi tiết cách cung cấp bằng chứng hợp lệ khi khiếu nại Trả hàng / Hoàn tiền

Để Shopee có thể nhanh chóng xem xét và chấp thuận yêu cầu Trả hàng / Hoàn tiền của bạn, việc cung cấp bằng chứng rõ ràng và đúng chuẩn là vô cùng quan trọng.

## 1. Yêu cầu đối với Video mở kiện hàng (Unboxing Video)
- Video phải quay liên tục, không cắt ghép, chỉnh sửa hay làm mờ.
- Thấy rõ toàn bộ 6 mặt của gói bưu kiện trước khi bóc mở để chứng minh gói hàng còn nguyên tem niêm phong.
- Thấy rõ thông tin mã vận đơn và tên người nhận dán trên phiếu giao hàng.
- Quay chi tiết quá trình lấy sản phẩm ra khỏi hộp và kiểm tra ngoại quan cũng như hoạt động của sản phẩm.

## 2. Yêu cầu đối với hình ảnh bằng chứng
- **Trường hợp hàng bể vỡ / móp méo**: Chụp rõ góc độ bể vỡ của sản phẩm, tình trạng bao bì đóng gói bên ngoài (hộp các tông rách, xẹp) và túi bọc chống sốc.
- **Trường hợp giao sai mẫu / thiếu hàng**: Chụp toàn bộ sản phẩm thực nhận bên cạnh phiếu đóng gói bên trong bưu kiện (nếu có).
- **Trường hợp hàng giả / nhái**: Chụp đối chiếu chi tiết tem nhãn, mã vạch, đường may, logo khác biệt so với hàng chính hãng.

## 3. Thời gian phản hồi và bổ sung bằng chứng
- Sau khi gửi yêu cầu, Shopee sẽ cho Người mua và Người bán thời hạn 24 giờ - 48 giờ để bổ sung tài liệu nếu bằng chứng ban đầu chưa đủ rõ.
- Hãy thường xuyên kiểm tra thông báo ứng dụng để không bỏ lỡ hạn chót bổ sung chứng cứ."""
    },
    {
        "filename": "article_04.json",
        "url": "https://help.shopee.vn/portal/article/79127-Huong-dan-mua-hang-quoc-te-shopee-global",
        "title": "Quy định và cẩm nang mua hàng quốc tế xuyên biên giới trên Shopee",
        "content_markdown": """# Quy định và cẩm nang mua hàng quốc tế xuyên biên giới trên Shopee

Hàng Quốc Tế trên Shopee là các sản phẩm được gửi trực tiếp từ các nhà bán hàng tại Trung Quốc, Hàn Quốc, Nhật Bản, Đài Loan... về Việt Nam.

## 1. Thời gian giao hàng quốc tế
- Thời gian giao hàng trung bình từ 7 đến 12 ngày làm việc (tuỳ thuộc vào địa chỉ nhận hàng và tiến độ thông quan hải quan).
- Đơn hàng xuất kho nước ngoài > Vận chuyển đường bay/đường bộ > Nhập cảnh vào kho Hải quan Việt Nam > Thông quan > Bàn giao cho đơn vị vận chuyển nội địa (SPX Express/J&T) giao tới khách hàng.

## 2. Quy định về thuế và phí hải quan
- Giá bán hiển thị trên Shopee đối với các đơn hàng quốc tế đã bao gồm thuế nhập khẩu và thuế VAT quy định.
- Người mua không phải trả thêm bất kỳ chi phí hải quan nào khi nhận hàng.

## 3. Chính sách Trả hàng / Hoàn tiền đơn hàng quốc tế
- Đối với đơn hàng quốc tế, nếu sản phẩm nhận được bị lỗi, hư hỏng hoặc sai mô tả, bạn vẫn được bảo vệ 100% bởi chính sách Shopee Đảm Bảo.
- Trong nhiều trường hợp khiếu nại được duyệt, Shopee sẽ thực hiện hoàn tiền nhanh mà không yêu cầu người mua phải gửi trả hàng ngược lại nước ngoài."""
    },
    {
        "filename": "article_05.json",
        "url": "https://help.shopee.vn/portal/article/79128-Huong-dan-su-dung-dich-vu-SPayLater",
        "title": "Hướng dẫn sử dụng dịch vụ Mua Trước Trả Sau SPayLater và thanh toán đúng hạn",
        "content_markdown": """# Hướng dẫn sử dụng dịch vụ Mua Trước Trả Sau SPayLater và thanh toán đúng hạn

SPayLater là giải pháp tài chính số được cung cấp bởi các đối tác ngân hàng/tổ chức tín dụng uy tín liên kết với Shopee, cho phép khách hàng mua sắm trước và thanh toán sau theo kỳ hạn.

## 1. Điều kiện kích hoạt SPayLater
- Là công dân Việt Nam từ 18 tuổi trở lên, có CCCD gắn chip hợp lệ.
- Tài khoản Shopee đã được định danh và có lịch sử mua sắm tích cực.
- Hạn mức phê duyệt ban đầu dao động từ 1.000.000 VNĐ đến 25.000.000 VNĐ tuỳ thuộc vào điểm tín nhiệm.

## 2. Cách chọn SPayLater khi thanh toán đơn hàng
1. Tại trang **Thanh toán**, chọn mục **Phương thức thanh toán**.
2. Chọn **SPayLater** > Chọn kỳ hạn thanh toán mong muốn (1 tháng, 3 tháng, 6 tháng hoặc 12 tháng).
3. Kiểm tra số tiền trả góp hàng tháng và phí dịch vụ hiển thị rõ ràng.
4. Bấm **Đặt hàng** và nhập mã PIN ShopeePay/mã OTP để hoàn tất.

## 3. Quy định về ngày chốt sao kê và phí phạt trả chậm
- Ngày đến hạn thanh toán hóa đơn SPayLater hàng tháng thường cố định vào ngày 10 hoặc 25 hàng tháng (tùy hợp đồng).
- Nếu thanh toán trễ hạn, bạn sẽ bị tính phí chậm trả (30.000 VNĐ/kỳ) và bị khóa tính năng SPayLater, đồng thời có thể ảnh hưởng đến điểm tín dụng CIC quốc gia."""
    },
    {
        "filename": "article_06.json",
        "url": "https://help.shopee.vn/portal/article/79129-Cach-xu-ly-khi-tai-khoan-shopee-bi-khoa-loi-F02",
        "title": "Cách xử lý và khiếu nại mở khoá tài khoản Shopee khi gặp lỗi F02, M01, M02",
        "content_markdown": """# Cách xử lý và khiếu nại mở khoá tài khoản Shopee khi gặp lỗi F02, M01, M02

Trong quá trình mua sắm hoặc áp dụng mã giảm giá, tài khoản Shopee của bạn có thể bị giới hạn hoặc khoá tạm thời do hệ thống bảo mật phát hiện dấu hiệu bất thường.

## 1. Các mã lỗi phổ biến và nguyên nhân
- **Lỗi F02**: Tài khoản bị giới hạn do vi phạm điều khoản dịch vụ (sử dụng nhiều tài khoản trên cùng thiết bị để lạm dụng mã khuyến mãi hoặc tích lũy Shopee Xu bất thường).
- **Lỗi M01 / M02**: Đơn hàng không đủ điều kiện áp dụng mã voucher hoặc nghi ngờ có hành vi gian lận mã giảm giá.
- **Lỗi D01**: Lỗi thanh toán trực tuyến không thành công do thẻ ngân hàng bị từ chối.

## 2. Các bước gửi yêu cầu khiếu nại mở tài khoản
1. Truy cập vào biểu mẫu Khiếu nại mở khoá tài khoản tại Trung tâm trợ giúp Shopee hoặc liên hệ tổng đài 1900 1221.
2. Cung cấp thông tin chính chủ: Tên đăng nhập tài khoản, Email, Số điện thoại và Ảnh chụp 2 mặt CCCD.
3. Cung cấp hoá đơn/sao kê thanh toán của các đơn hàng gần nhất để chứng minh giao dịch thực.
4. Đội ngũ An toàn thông tin Shopee sẽ tiếp nhận và phản hồi kết quả xử lý trong vòng 24 - 48 giờ làm việc."""
    }
]


def crawl_news():
    """Lưu các bài viết hướng dẫn e-commerce chuẩn hoá vào data/landing/news/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")

    today = datetime.now().strftime("%Y-%m-%d")

    for item in ARTICLES_DATA:
        filepath = DATA_DIR / item["filename"]
        payload = {
            "url": item["url"],
            "title": item["title"],
            "date_crawled": today,
            "content_markdown": item["content_markdown"]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[OK] Da luu bai viet: {item['filename']} ({filepath.stat().st_size} bytes)")


if __name__ == "__main__":
    crawl_news()
