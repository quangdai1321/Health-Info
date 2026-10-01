# Hệ thống diễn giải kết quả xét nghiệm máu có ràng buộc theo luật

Mã nguồn và dữ liệu cho bài nộp **HEALTHINFO IV** — Track B, trụ cột Health
Literacy.

Nguyên tắc trung tâm: **không giao phán đoán lâm sàng cho mô hình ngôn ngữ.**
Luật quyết định một chỉ số có bất thường hay không *trước khi* LLM được gọi;
LLM chỉ diễn đạt lại nhãn đã có; một bộ kiểm chứng đối chiếu văn bản sinh ra
với nhãn đó và thay bằng bản mẫu cố định khi không khớp.

## Trạng thái

Thực nghiệm **đã chạy xong**, số liệu trong bài đã đối chiếu khớp với
`results/summary.csv`. Bài báo đã hoàn chỉnh 10 trang. Việc còn lại là rà soát
y khoa (xem cuối file).

## Cấu trúc

```
Health-Info/
├── data/
│   ├── reference_ranges.csv        # 22 chỉ số CBC — CẦN RÀ SOÁT Y KHOA
│   └── synthetic_panels.json       # 150 phiếu sinh tự động, có nhãn đúng
├── src/
│   ├── classifier.py               # Tầng 1 (chuẩn hóa) + Tầng 2 (phân loại luật)
│   ├── prompt_builder.py           # Tầng 3 (prompt) + Tầng 4 (kiểm chứng, fallback)
│   ├── generate_data.py            # sinh 150 phiếu thử (seed 42)
│   ├── run_experiment.py           # chạy 3 cấu hình qua Ollama
│   └── analyze.py                  # tổng hợp -> summary.csv + bảng LaTeX
├── tests/
│   └── test_classifier.py          # 38 test cho Tầng 1+2, TẤT CẢ PHẢI QUA
├── results/
│   ├── baseline_qwen2.5-3b.jsonl   # 150 dòng, mỗi dòng một phiếu
│   ├── constrained_qwen2.5-3b.jsonl
│   ├── full_qwen2.5-3b.jsonl
│   └── summary.csv                 # nguồn số liệu của Bảng 1 trong bài
└── files/                          # bài báo
    ├── manuscript.tex / .pdf       # bản nộp (tiếng Anh, 10 trang)
    ├── bai-bao-tieng-viet.docx     # bản tiếng Việt để đọc/rà soát
    ├── ban-dich-tieng-viet.md      # nguồn của file .docx
    ├── references.bib
    ├── architecture.png            # Hình 1 (sinh bởi make_architecture_diagram.py)
    ├── svproc.cls, splncs03_unsrt.bst   # file Springer — KHÔNG SỬA
    └── CONTEXT.md                  # ngữ cảnh dự án, đọc trước khi sửa gì
```

## Phụ thuộc

Pipeline **không dùng thư viện bên thứ ba nào** — chỉ thư viện chuẩn Python
(gọi LLM qua `urllib`, không cần `requests`). Chỉ `pytest` là ngoài:

```bash
pip install -r requirements.txt     # chỉ pytest
```

Ngoài Python cần **Ollama** và mô hình:

```bash
curl -fsSL https://ollama.com/install.sh | sh    # Windows: tải installer từ ollama.com
ollama pull qwen2.5:3b
```

## Chạy

```bash
python -m pytest tests/ -q          # phải thấy "38 passed"
python src/classifier.py            # demo phân loại bằng luật
python src/prompt_builder.py        # demo prompt + bộ kiểm chứng
python src/generate_data.py         # sinh lại 150 phiếu (seed 42)
```

`generate_data.py` **tái lập chính xác từng byte**: chạy lại cho ra đúng file
`data/synthetic_panels.json` đang có (đã kiểm tra bằng md5). Các script tự ép
stdout sang UTF-8 nên chạy được trên console Windows mặc định, không cần
`chcp` hay đặt `PYTHONIOENCODING`.

## Tái lập kết quả thực nghiệm

Bật Ollama trước, rồi:

```bash
python src/run_experiment.py --limit 3   # chạy thử 3 phiếu, kiểm tra đã nối được
python src/run_experiment.py             # 150 phiếu x 3 cấu hình — MẤT ~6 TIẾNG
python src/analyze.py                    # tổng hợp + in bảng LaTeX
```

Kết quả ghi dần vào `results/*.jsonl`. Ngắt giữa chừng rồi chạy lại thì script
tự bỏ qua phiếu đã xong. `analyze.py` chỉ đọc file kết quả nên chạy lại bao
nhiêu lần cũng cho ra số y hệt.

**Cấu hình đo trong bài:** Intel Core i5-9400F, 24 GB RAM, **CPU only, không
GPU**, mô hình `qwen2.5:3b` qua Ollama. Thời gian trung bình mỗi phiếu: 38,9 s
(baseline), 35,8 s (constrained), 68,3 s (full).

So sánh với mô hình khác:

```bash
ollama pull qwen2.5:7b
python src/run_experiment.py --model qwen2.5:7b
```

## ⚠ Sửa gì thì phải chạy lại thực nghiệm

Nếu sửa **logic Tầng 2** (`classifier.py`) hoặc **`data/reference_ranges.csv`**
thì nhãn thay đổi, kéo theo prompt thay đổi, nên **toàn bộ kết quả trong
`results/` mất hiệu lực** và phải chạy lại (~6 tiếng). Cân nhắc kỹ trước khi
đụng vào. Sửa xong bắt buộc chạy `python -m pytest tests/ -q` trước khi commit.

## Bốn quyết định thiết kế đáng nêu trong bài

**Tầng 2 chạy trước Tầng 3.** Việc xác định chỉ số nào bất thường hoàn toàn
bằng luật, không có LLM tham gia. Nhờ vậy độ chính xác phân loại là thuộc tính
của thiết kế chứ không phải kết quả thực nghiệm, và LLM không có cơ hội phán
đoán sai.

**Chuẩn hóa tên giữ lại `%` và `#`.** Hai ký tự này phân biệt tỷ lệ phần trăm
với số lượng tuyệt đối. Xóa chúng thì `NEUT%` và `NEUT#` trùng khóa. Lỗi này
đã xảy ra trong lúc phát triển và được test bắt.

**Chuẩn hóa đơn vị trước khi so sánh.** Các phòng xét nghiệm Việt Nam dùng đơn
vị khác nhau cho cùng một chỉ số: Hb có nơi ghi `g/L`, nơi ghi `g/dL`, chênh 10
lần. So sánh mà bỏ qua đơn vị tạo ra cảnh báo giả ở mức nghiêm trọng nhất, và
lỗi xảy ra ngay tại tầng luật vốn được tuyên bố là chính xác tuyệt đối. Hệ
thống quy đổi về đơn vị chuẩn và **từ chối xử lý** khi đơn vị lạ, hoặc khi
phiếu thiếu đơn vị mà chỉ số đó có nhiều đơn vị khác bậc độ lớn. Không bao giờ
đoán.

**Vòng lặp kiểm chứng có đường lui.** Đầu ra không đạt thì sinh lại; quá số
lần cho phép thì rơi về bản mẫu cố định. Hệ thống không bao giờ trả ra nội
dung chưa qua kiểm chứng. Đổi lại, 36% số phiếu ở cấu hình `full` là do đường
lui chứ không phải mô hình tự viết được — con số này phải nêu rõ khi trình bày
kết quả.

## Sáu loại lỗi mà Tầng 4 phát hiện

| Mã | Nghĩa |
|---|---|
| `false_reassurance` | Nói mọi thứ bình thường trên phiếu bất thường — nguy hiểm nhất |
| `status_mismatch` | Trường trạng thái không khớp nhãn Tầng 2 |
| `contradictory_wording` | Văn xuôi nói ngược trạng thái (dù trường trạng thái đúng) |
| `forbidden_term` | Tên bệnh, thuốc, liều lượng, quy nguyên nhân |
| `hallucinated_analyte` | Bịa chỉ số không có trong đầu vào |
| `missing_analyte` | Bỏ sót chỉ số |

Ngoài ra `code_format` (điền tên hiển thị thay vì mã chuẩn) được đếm riêng —
đây là lỗi hình thức, không tính vào lỗi nội dung.

## Giới hạn (đã ghi vào bài)

- Dữ liệu là tổng hợp, chưa kiểm chứng trên phiếu lâm sàng thật
- Chưa xử lý OCR; giả định đầu vào đã có cấu trúc
- Khoảng tham chiếu chưa phân theo giới tính và độ tuổi
- Chỉ xử lý công thức máu; chưa hỗ trợ sinh hóa, miễn dịch, nước tiểu
- Chưa xử lý khoảng tham chiếu một phía (`> 40`, `< 130`, `≤ 8.2`)
- Chưa xử lý kết quả định tính (Negative/Positive)
- Tầng 4 khớp mẫu bề mặt, có thể bị lách bằng cách diễn đạt vòng vo
- Kết quả chỉ từ một mô hình 3B duy nhất

## Việc còn lại — cần người, không phải cần code

**1. Rà soát bảng tham chiếu — ưu tiên cao nhất.**
`data/reference_ranges.csv` hiện dùng khoảng tham chiếu lấy từ một phiếu xét
nghiệm mẫu (nam giới trưởng thành). Phải đối chiếu với tài liệu huyết học
chuẩn và ghi rõ nguồn trong bài — đây là chỗ phản biện soi kỹ nhất. Cột
`severe_factor` (ngưỡng phân biệt "theo dõi" với "khám sớm", hiện 0,15–0,50)
đang đặt theo kinh nghiệm; điều này đã được nêu thẳng trong phần Hạn chế của
bài, nhưng vẫn nên thay bằng danh mục giá trị nguy hiểm có căn cứ.

**2. Tìm người có nền y tế chấm đầu ra.** Hiện chưa có ai, và việc này đã được
ghi vào Limitations. Cần rà soát 30–40 mẫu ngẫu nhiên về độ chính xác và độ an
toàn.
