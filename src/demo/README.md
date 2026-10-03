# Trang demo — Diễn giải kết quả xét nghiệm máu có ràng buộc theo luật

Trang web một file, dùng để demo trực tiếp khi báo cáo. Tầng 1, 2, 4 chạy ngay trong
trình duyệt bằng JavaScript. Chỉ tầng 3 gọi mô hình Qwen2.5-3B qua Ollama trên máy bạn,
nên dữ liệu không gửi ra ngoài.

## Cách 1 — chạy tại chỗ (khuyên dùng khi báo cáo)

```bash
ollama serve                 # hoặc mở Ollama từ khay hệ thống
cd demo
python -m http.server 8000
```

Mở trình duyệt vào `http://localhost:8000`. Cách này chắc ăn nhất vì trang và mô hình
cùng nằm trên `localhost`, không vướng chặn của trình duyệt, và vẫn chạy khi hội trường
mất mạng.

## Cách 2 — deploy lên Vercel

Kéo cả thư mục `demo` vào Vercel, hoặc trỏ Vercel vào repo và đặt Root Directory là `demo`.
Sau khi có link, **phải cho Ollama chấp nhận trang đó**, nếu không trình duyệt sẽ chặn:

```powershell
setx OLLAMA_ORIGINS "*"
```

Rồi thoát hẳn Ollama trong khay hệ thống và mở lại.

Lưu ý: trang chạy trên tên miền `https://...vercel.app` gọi về `http://localhost` có thể bị
Chrome chặn theo chính sách Private Network Access. Nếu bấm nút mà không có gì xảy ra,
hãy quay về Cách 1. **Trước khi lên trình bày nên thử trước cả hai cách.**

## Khi trang chạy trên Vercel mà báo "Failed to fetch"

Chrome chặn trang `https://...vercel.app` gọi vào `http://localhost`, dù Ollama đã cho phép.
Mở thêm một cửa sổ lệnh:

```bash
cd demo
python cau_noi.py
```

Rồi trong trang, mở **Cài đặt và cách chạy** và bấm **Dùng cầu nối cổng 11435**.
Cầu nối chỉ thêm header mà Chrome đòi rồi chuyển tiếp sang Ollama, không sửa gì nội dung.

## Cách dùng khi trình bày

1. Bấm **Hỏi thẳng AI**: mô hình nhận nguyên phiếu, không ràng buộc gì. Đây là thứ xảy ra
   khi người bệnh dán phiếu vào một chatbot.
2. Bấm **Chạy qua hệ thống 4 tầng**: trang hiện bảng tầng 1 và 2 đã xếp mức trước khi gọi
   AI, sau đó là câu AI viết, kèm báo cáo tầng 4 đã kiểm tra những gì.
3. Nút **Phiếu ví dụ khác** đổi giữa ba phiếu: một phiếu nhiều chỉ số lệch, một phiếu nặng,
   một phiếu bình thường hoàn toàn.

Phiếu mẫu có sẵn hai dòng cố ý sai để cho thấy tầng 1 từ chối thay vì đoán: một dòng tên lạ
và một dòng thiếu đơn vị.

## Thời gian chạy

Đo trên máy Intel Core i5-9400F, 24 GB RAM, không có card đồ họa: khoảng 7 đến 40 giây cho
một phiếu, tùy mô hình có phải viết lại hay không. Lần gọi đầu tiên sau khi bật Ollama lâu
hơn vì mô hình phải nạp vào bộ nhớ, nên **hãy chạy thử một lần trước khi lên trình bày**.

## File

| File | Nội dung |
|---|---|
| `index.html` | Giao diện |
| `pipeline.js` | Bốn tầng, viết lại từ `src/classifier.py` và `src/prompt_builder.py` |
| `_chiso.js` | Bảng 22 chỉ số, sinh từ `data/reference_ranges.csv` |
