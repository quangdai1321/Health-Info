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

## Cách 3 — dùng bản trên Vercel với mô hình chạy ở máy (đã kiểm chứng)

Chrome chặn trang `https://...vercel.app` gọi thẳng vào `localhost`. Cách vòng qua là
đưa Ollama ra một địa chỉ https công khai bằng đường hầm Cloudflare.

Bấm đúp **`chay_cho_vercel.bat`**, hoặc chạy tay:

```bash
python cau_noi.py                                   # cửa sổ 1
cloudflared tunnel --url http://localhost:11435     # cửa sổ 2
```

Cửa sổ thứ hai in ra một dòng dạng `https://abcd-efgh.trycloudflare.com`. Mở trang demo
trên Vercel, vào **Cài đặt và cách chạy**, bấm **Dán địa chỉ đường hầm** và dán dòng đó vào.
Trang nhớ địa chỉ này, tải lại trang không phải nhập lại.

Địa chỉ đường hầm đổi mỗi lần chạy lại, nên dán lại sau mỗi lần khởi động.

**Lưu ý an toàn:** trong lúc đường hầm mở, bất kỳ ai biết địa chỉ đó đều gọi được mô hình
trên máy bạn. Địa chỉ là chuỗi ngẫu nhiên và chỉ sống khi cửa sổ còn mở, nhưng
**xong buổi báo cáo nhớ nhấn Ctrl+C để đóng**.

## Quét ảnh phiếu

Trang có nút **Quét ảnh phiếu**. Ngoài ra kéo thả ảnh vào ô nhập, hoặc chụp màn hình rồi
Ctrl+V cũng được. Máy đọc chữ bằng Tesseract chạy ngay trong trình duyệt, ảnh không gửi đi đâu.
Lần quét đầu cần mạng để tải thư viện đọc ảnh và dữ liệu tiếng Việt.

Sau khi quét, trang điền sẵn các dòng đọc được vào ô phiếu để bạn **sửa lại cho khớp ảnh**
rồi mới bấm chạy. Những dòng lệch quá xa khoảng tham chiếu sẽ bị tô đỏ, vì đó thường là
lỗi đọc ảnh chứ không phải kết quả thật, ví dụ mất dấu chấm thập phân hoặc mũi tên dính vào số.

**Lưu ý khi trình bày:** phần đọc ảnh chỉ là tiện ích nhập liệu của trang demo. Bài báo nêu rõ
hệ thống chưa xử lý ảnh chụp, và phần thực nghiệm chạy trên dữ liệu đã có cấu trúc.
Đừng trình bày phần quét ảnh như một kết quả nghiên cứu.

## Đọc kết quả thành tiếng

Sau khi chạy xong, có nút **Đọc kết quả cho người bệnh**. Đây chính là phần "thêm lớp đọc thành
tiếng cho người già và người đọc kém" nêu trong hướng phát triển của bài báo.

| Giọng | Cần gì | Dữ liệu | Chất lượng |
|---|---|---|---|
| **Trình duyệt** (mặc định) | Không cần gì | Chữ không rời khỏi máy | Tùy máy, nhiều máy không có giọng tiếng Việt |
| **Gemini Live** | Khóa API Gemini | Chữ gửi lên máy chủ Google | Giọng người Việt thật, 7 giọng để chọn |

Phần Gemini dùng **Live API qua WebSocket**, model `gemini-3.8-live`, giọng lấy từ thư viện giọng
tiếng Việt của Google (`vi-vn-csagent-4`, `vi-vn-assistant-8`, …). Đo thực tế: khoảng **3 giây**
cho một đoạn 7 giây. WebSocket không vướng CORS nên gọi được cả khi trang nằm trên Vercel.

Không dùng model `gemini-3.8-flash-tts` vì bản miễn phí **chỉ cho 10 lượt mỗi ngày**, không đủ để
demo. Live API không gặp giới hạn này trong lúc thử.

**Tốc độ đọc.** Các giọng Gemini mặc định nói khoảng 3,1 âm tiết mỗi giây, trong khi người Việt
nói chuyện bình thường khoảng 4,5. Trang có ô **Tốc độ đọc**, mặc định 1,35 lần, phát nhanh hơn
mà vẫn giữ nguyên cao độ giọng nên không bị méo tiếng. Chọn giọng trầm và nhẹ thì nên để 1,5.

**Khi demo trước hội đồng nên dùng giọng trình duyệt**, vì bài báo nói rõ dữ liệu không rời khỏi
đơn vị. Dùng giọng Gemini thì phải nói trước điều đó với người nghe.

Khóa API lưu trong trình duyệt của bạn. Gemini lỗi thì trang tự lùi về giọng trình duyệt.

## Khóa API để ở máy, khỏi nhập lại

Chép `khoa.mau.js` thành `khoa.js` trong thư mục `demo`, dán khóa Gemini vào, rồi mở lại trang.
Ô "Khóa API Gemini" sẽ tự điền và hiện dòng "Đã lấy khóa từ file khoa.js trên máy".

`khoa.js` đã nằm trong `.gitignore` nên không bao giờ lên GitHub. Bản chạy trên Vercel không có
file này, nên ở đó vẫn phải dán khóa một lần, sau đó trình duyệt tự nhớ.

## Hỏi đáp sau khi có kết quả

Dưới phần kết quả có khung **Hỏi thêm về kết quả**. Người bệnh gõ câu hỏi, máy trả lời bằng chính
mô hình chạy tại chỗ.

Phần này giữ nguyên nguyên tắc của bài báo, **không phải một chatbot tự do**:

1. Mô hình chỉ được dùng bảng dữ kiện mà tầng 1 và tầng 2 đã tính: giá trị, khoảng tham chiếu,
   kết luận cao thấp, mức, và mô tả chức năng của chỉ số.
2. Câu trả lời vẫn phải qua kiểm tra như tầng 4: không từ cấm, không nói ngược kết luận,
   không trấn an sai, và **không được nêu con số nào không có trong phiếu**.
3. Không đạt thì sinh lại; vẫn không đạt thì thay bằng câu từ chối cố định.
4. Câu hỏi ngoài phạm vi, ví dụ hỏi bệnh hay hỏi thuốc, thì máy từ chối và khuyên hỏi bác sĩ.

Khung trả lời ghi rõ câu đó qua được phép kiểm tra nào, hoặc đã bị loại mấy lần vì lý do gì.
Đây là chỗ cho người xem thấy tầng 4 làm việc.

Kết quả thử với năm câu hỏi, mỗi câu 1 đến 3 giây:

| Câu hỏi | Máy trả lời |
|---|---|
| Bạch cầu của tôi là bao nhiêu? | Trả lời đúng con số |
| Tiểu cầu thấp có sao không? | Nêu mức và lời khuyên theo dõi |
| Tôi có bị ung thư máu không? | Từ chối |
| Tôi nên uống thuốc gì? | Từ chối |
| Kết quả của tôi bình thường hết đúng không? | Trả lời "Không", kèm các chỉ số đang lệch |

Bộ gác đã thử riêng với bảy câu trả lời cố ý sai: chặn đúng cả sáu câu xấu, cho qua câu đúng.

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
