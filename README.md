# Hệ thống diễn giải kết quả xét nghiệm máu có ràng buộc theo luật

Mã nguồn và dữ liệu cho bài **HEALTHINFO IV**, mã số HI26-0013 — Track B, trụ
cột Health Literacy.

> **A Rule-Constrained Large Language Model Pipeline for Rule-Consistent
> Explanation of Vietnamese Complete Blood Count Results**

Nguyên tắc trung tâm: **không giao phán đoán lâm sàng cho mô hình ngôn ngữ.**
Luật quyết định một chỉ số có bất thường hay không *trước khi* LLM được gọi;
LLM chỉ diễn đạt lại nhãn đã có; một bộ kiểm chứng đối chiếu văn bản sinh ra
với nhãn đó và thay bằng bản mẫu cố định khi không khớp.

## Trạng thái

Bản **camera-ready**, đã sửa theo hai bản phản biện vòng 2 (hạn nộp
31/10/2026). Bài ra 11 trang PDF. Thực nghiệm chạy xong **bảy cấu hình** trên
cùng 150 phiếu.

Tên bài đã đổi theo yêu cầu của Phản biện 1: bỏ "Patient-Friendly" vì chưa đo
được độ dễ hiểu với bệnh nhân, và thu "Blood Test" về "Complete Blood Count"
cho khớp phạm vi thực nghiệm.

## Ba điều phải nói rõ khi trình bày kết quả

Đây không phải là cảnh báo chung chung, mà là ba kết luận từ chính số liệu
trong `results/`. Bỏ chúng đi là báo cáo sai.

**1. Mẫu cố định một mình đã đạt 100% qua kiểm chứng.** Cấu hình `chi_mau`
không gọi mô hình lần nào, chỉ in bản mẫu của Tầng 2, và đạt đúng tỷ lệ của
pipeline đủ bốn tầng trong 0,38 giây cho cả 150 phiếu. Kiểm định McNemar ghép
cặp không phân biệt được hai cấu hình (p = 1,000). Nghĩa là **thước đo này
không chứng minh được mô hình đóng góp gì**: một tỷ lệ định nghĩa theo mức
khớp với luật thì đạt cực đại ở chính văn bản do luật viết ra. Cái mô hình
thêm vào là 64% số phiếu có văn tự viết thay vì câu mẫu, và độ dễ đọc của
phần văn đó thì chưa ai đo.

**2. Ràng buộc nội dung trong prompt không cải thiện tính đúng.** Khi không có
nhãn, nó làm trấn an sai *tăng* từ 32,0% lên 43,3%, cao hơn cả baseline. Tác
dụng đo được duy nhất của nó là lên từ ngữ (từ cấm giảm 79,3% → 35,3%). Thêm
nó lên trên nhãn thì tỷ lệ qua kiểm chứng đi từ 38,7% lên 48,0%, chênh lệch
**không đạt mức ý nghĩa** trên 150 phiếu (McNemar, p = 0,082).

**3. Bộ kiểm chứng có một kiểu báo nhầm hệ thống.** Lớp mâu thuẫn diễn đạt chỉ
gỡ cụm chỉ khoảng tham chiếu khi có từ so sánh đứng trước, nên câu trích thẳng
khoảng tham chiếu, kiểu *"mức Plt bình thường nằm trong khoảng 150–400"*, bị
đọc thành lời khẳng định trạng thái. Quét theo mẫu thấy khoảng 24% số câu bị
lớp này từ chối rơi vào dạng đó. **Cố ý không sửa**, vì chỉnh bộ kiểm chứng sau
khi đã thấy kết quả thì mọi so sánh giữa các cấu hình mất hiệu lực. Hướng lệch
đã ghi rõ trong bài: nó làm tăng tỷ lệ rơi về mẫu, tức là thiệt cho mô hình,
chứ không thổi phồng tỷ lệ qua.

**4. Mô hình lớn hơn không an toàn hơn.** `qwen2.5:7b` trên cùng 150 phiếu:
baseline vẫn 0% qua kiểm chứng, và trấn an sai *tăng* từ 32,0% lên **46,7%**,
bịa chỉ số tăng từ 32,0% lên 41,3%. Nó chỉ giỏi hơn ở chỗ ít sai chiều và ít bỏ
sót. Trong pipeline đủ tầng thì ngược lại: cũng 100% qua kiểm chứng nhưng văn mô
hình lên **96,0%** so với 64,0%, tức là giảm tỷ lệ rơi về mẫu từ 36% xuống 4%.
Mô hình to hơn mua được ít phải vứt bỏ hơn, không mua được an toàn hơn.

**5. Cùng một cấu hình chạy 5 lần cho kết quả khác nhau theo từng phiếu.** Tỷ lệ
qua kiểm chứng của `constrained` là 50,3% ± 2,4 (48,0–53,3), tổng thể khá ổn
định. Nhưng theo phiếu thì chỉ **31/150 phiếu luôn đạt, 37 luôn trượt, còn 82
phiếu (54,7%) lúc đạt lúc trượt**. Con số tổng tái lập được, lời giải thích cho
một bệnh nhân cụ thể thì không. Đây là lý do phải kiểm chứng từng đầu ra chứ
không phải chọn cấu hình nào chấm điểm cao.

## Cấu trúc

```
Health-Info/
├── data/
│   ├── reference_ranges.csv            # 22 chỉ số CBC, bảng mà mã đang chạy
│   ├── nguon_khoang_tham_chieu.csv     # nguồn gốc từng khoảng + hệ số nặng + tình trạng thẩm định
│   ├── tu_cam_nguon.csv                # 32 mẫu từ cấm, kèm căn cứ pháp lý/chuyên môn
│   └── synthetic_panels.json           # 150 phiếu sinh tự động (seed 42), có nhãn đúng
├── src/
│   ├── classifier.py                   # Tầng 1 (chuẩn hóa) + Tầng 2 (phân loại luật)
│   ├── prompt_builder.py               # Tầng 3 (prompt) + Tầng 4 (kiểm chứng, bản mẫu)
│   ├── generate_data.py                # sinh 150 phiếu (seed 42)
│   ├── run_experiment.py               # chạy 6 cấu hình có gọi mô hình
│   ├── chay_chi_mau.py                 # cấu hình chỉ mẫu cố định, không gọi mô hình
│   ├── analyze.py                      # tổng hợp -> summary.csv
│   ├── phan_tich_ablation.py           # bảng so sánh các cấu hình -> Bảng 3
│   ├── thong_ke_tin_cay.py             # KTC Wilson, McNemar, p50/p95/p99, lý do bị loại
│   ├── cham_lai_bo_loi_dinh_dang.py    # chấm lại baseline sau khi quy đổi mã
│   ├── thu_nghiem_don_vi.py            # thí nghiệm đơn vị đo, tất định
│   ├── vi_du_loi.py                    # rút ví dụ thật mỗi lớp lỗi
│   ├── phan_tich_7b_va_lap.py          # so sánh 7B với 3B, và 5 lần chạy lặp
│   ├── chay_ngam_bo_sung.py            # điều phối chạy 7B và chạy lặp
│   ├── dung_phu_luc.py                 # sinh Phụ lục A/B/C từ mã đang chạy
│   └── dong_goi_nop_kem.py             # dựng file zip nộp kèm
├── tests/                              # 46 test, TẤT CẢ PHẢI QUA
├── results/                            # 7 file .jsonl + các file phân tích
└── docs/
    ├── phu_luc_bo_sung.md              # Phụ lục A/B/C nộp kèm bài
    ├── phan_hoi_phan_bien.md           # trả lời phản biện, R1.1–R1.12 và R2.1–R2.8
    └── sua_bai_vong2.md                # theo dõi từng ý phản biện
```

`docs/phu_luc_bo_sung.md` **sinh ra từ mã, không gõ tay** (`src/dung_phu_luc.py`),
nên bảng khoảng tham chiếu, bảng bí danh, bảng mẫu của bộ kiểm chứng và các ví
dụ lỗi trong phụ lục không thể lệch khỏi code. Hai file `data/*_nguon.csv` cũng
được hai file test giữ khớp với mã.

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
python -m pytest tests/ -q          # phải thấy "46 passed"
python src/classifier.py            # demo phân loại bằng luật
python src/prompt_builder.py        # demo prompt + bộ kiểm chứng
python src/generate_data.py         # sinh lại 150 phiếu (seed 42)
```

`generate_data.py` **tái lập chính xác từng byte**: chạy lại cho ra đúng file
`data/synthetic_panels.json` đang có. Các script tự ép stdout sang UTF-8 nên
chạy được trên console Windows mặc định, không cần `chcp` hay
`PYTHONIOENCODING`.

## Tái lập kết quả thực nghiệm

Bật Ollama trước, rồi:

```bash
python src/run_experiment.py --limit 3            # chạy thử, kiểm tra đã nối được
python src/run_experiment.py                      # 150 phiếu x 6 cấu hình — MẤT ~12 TIẾNG
python src/chay_chi_mau.py                        # cấu hình thứ 7, vài giây, không cần Ollama
python src/analyze.py                             # tổng hợp
python src/phan_tich_ablation.py                  # bảng so sánh các cấu hình
python src/thong_ke_tin_cay.py                    # KTC, McNemar, phân vị thời gian
python src/dung_phu_luc.py                        # sinh lại phụ lục
```

Ba script phân tích này **không gọi mô hình**, chỉ đọc lại `results/`, nên chạy
bao nhiêu lần cũng cho ra số y hệt.

**Cấu hình đo trong bài:** Intel Core i5-9400F, 24 GB RAM, **NVIDIA GTX 1050 Ti
4 GB**. Mô hình `qwen2.5:3b` qua Ollama, lượng tử hóa Q4_K_M, temperature 0,2,
giới hạn 2.048 token, chế độ JSON, **không đặt seed cố định**.

> **Đính chính:** bản nộp lần đầu ghi "CPU only, không GPU". Sai. Đo lại bằng
> `ollama ps` và `nvidia-smi`: `qwen2.5:3b` chiếm khoảng 3 GB VRAM và được đẩy
> **100% sang card**, GPU chạy 100%. Mọi con số thời gian của 3B trong bài đều
> là số có GPU. `qwen2.5:7b` nặng 5,2 GB nên không vừa 4 GB, chạy khoảng một nửa
> trên card, vì thế chậm gấp 2,4 lần chứ không phải tỷ lệ với số tham số.

Thời gian mỗi phiếu ở cấu hình `full`: trung bình 68,3 s, p50 66,4 s, p95
121,5 s, p99 134,1 s.

So sánh với mô hình lớn hơn (**đã chạy**, baseline và full):

```bash
ollama pull qwen2.5:7b
python src/run_experiment.py --config baseline --model qwen2.5:7b
python src/run_experiment.py --config full --model qwen2.5:7b
python src/phan_tich_7b_va_lap.py
```

Chạy lặp để đo biến thiên giải mã (**đã chạy 5 lần cho `constrained`**):

```bash
for i in 2 3 4 5; do python src/run_experiment.py --config constrained --lan $i; done
```

Cả hai mẻ trên chạy bằng `src/chay_ngam_bo_sung.py`, mất 18,5 giờ.

## Bảy cấu hình

| Cấu hình | Gồm những gì | Qua kiểm chứng | Mô hình tự viết |
|---|---|---|---|
| `baseline` | Hỏi thẳng, không nhãn, không ràng buộc, không kiểm chứng | 0,0% | 0,0% |
| `chi_mau` | Chỉ Tầng 1+2, in bản mẫu, **không gọi mô hình** | 100,0% | 0,0% |
| `chi_nhan` | Nhãn từ luật + khuôn JSON, bỏ cấm nội dung | 38,7% | 38,7% |
| `chi_rang_buoc` | Cấm nội dung + khuôn JSON, không có nhãn | 0,0% | 0,0% |
| `chi_kiem_chung` | Prompt baseline + Tầng 4 | 100,0% | 0,0% |
| `constrained` | Tầng 1–3, không kiểm chứng | 48,0% | 48,0% |
| `full` | Đủ bốn tầng | 100,0% | 64,0% |

Thêm cấu hình **`full` không sinh lại**, suy ra được từ nhật ký của `full`:
cùng 100,0% qua kiểm chứng nhưng chỉ 46,0% văn mô hình, ở một nửa thời gian.

## ⚠ Sửa gì thì phải chạy lại thực nghiệm

Nếu sửa **logic Tầng 2** (`classifier.py`), **`data/reference_ranges.csv`**,
hoặc **bất kỳ mẫu nào của Tầng 4** (`prompt_builder.py`) thì nhãn hoặc cách
chấm thay đổi, nên **toàn bộ kết quả trong `results/` mất hiệu lực** và phải
chạy lại (~12 tiếng). Riêng với bộ kiểm chứng còn một lý do nữa: sửa nó sau khi
đã thấy kết quả thì các cấu hình không còn so sánh được với nhau nữa. Sửa xong
bắt buộc chạy `python -m pytest tests/ -q` trước khi commit.

## Bốn quyết định thiết kế đáng nêu trong bài

**Tầng 2 chạy trước Tầng 3.** Việc xác định chỉ số nào bất thường hoàn toàn
bằng luật, không có LLM tham gia. Phân loại vì thế **chính xác so với khoảng
tham chiếu và hệ số nặng đang cấu hình**, và mô hình không sửa được nó. Đây
không phải lời khẳng định rằng các ngưỡng đó đã được thẩm định lâm sàng —
chúng chưa. Hai nhãn `theo_doi` và `kham_som` là **nhóm độ lệch**, không phải
chỉ định phân luồng khám.

**Chuẩn hóa tên giữ lại `%` và `#`.** Hai ký tự này phân biệt tỷ lệ phần trăm
với số lượng tuyệt đối. Xóa chúng thì `NEUT%` và `NEUT#` trùng khóa. Lỗi này
đã xảy ra trong lúc phát triển và được test bắt.

**Chuẩn hóa đơn vị trước khi so sánh.** Các phòng xét nghiệm Việt Nam dùng đơn
vị khác nhau cho cùng một chỉ số: Hb có nơi ghi `g/L`, nơi ghi `g/dL`, chênh 10
lần. Đã đo được hậu quả: trong 2.118 lần đọc, 143 lần (6,8%) ghi bằng đơn vị
khác bậc độ lớn, và nếu không quy đổi thì 135 trong số đó (94,4%) bị gán sai
nhãn, chạm 97 trên 150 phiếu. Tất cả đều là báo động giả ở mức nặng nhất. Hệ
thống quy đổi về đơn vị chuẩn và **từ chối xử lý** khi đơn vị lạ. Không bao giờ
đoán.

**Vòng lặp kiểm chứng có đường lui.** Đầu ra không đạt thì sinh lại; quá số lần
cho phép thì rơi về bản mẫu cố định, nên **không có văn bản nào của mô hình
được trả ra mà chưa qua kiểm chứng**. Đổi lại, 36% số phiếu ở cấu hình `full`
là do đường lui chứ không phải mô hình tự viết được — con số này phải nêu kèm
mỗi lần nhắc tới tỷ lệ 100%.

## Sáu loại lỗi mà Tầng 4 phát hiện

| Mã | Nghĩa |
|---|---|
| `false_reassurance` | Nói mọi thứ bình thường trên phiếu bất thường — nguy hiểm nhất |
| `status_mismatch` | Trường trạng thái không khớp nhãn Tầng 2 |
| `contradictory_wording` | Văn xuôi nói ngược trạng thái (dù trường trạng thái đúng) |
| `forbidden_term` | Tên bệnh, thuốc, liều lượng, quy nguyên nhân |
| `hallucinated_analyte` | Bịa chỉ số không có trong đầu vào |
| `missing_analyte` | Bỏ sót chỉ số |

Ngoài ra `code_format` (điền tên hiển thị thay vì mã chuẩn), `unparseable` và
`malformed_structure` được đếm riêng — lỗi hình thức, không tính vào lỗi nội
dung.

Trong 54 phiếu phải rơi về bản mẫu ở cấu hình `full`, lý do bị loại là: bỏ sót
chỉ số 66,7%, từ cấm 38,9%, sai chiều 29,6%, trấn an sai 18,5%, bịa chỉ số
14,8%, mâu thuẫn 5,6%. Cái mà vòng sinh lại chủ yếu phải chống là **bỏ sót**,
không phải từ ngữ.

## Giới hạn (đã ghi vào bài)

- Tỷ lệ qua kiểm chứng **không phải bằng chứng an toàn độc lập**: bộ kiểm chứng
  vừa là bộ lọc vừa là thước đo, và một bản mẫu tất định cũng đạt đúng tỷ lệ đó
- Bộ kiểm chứng khớp mẫu bề mặt, bị lách được bằng diễn đạt vòng vo, và có kiểu
  báo nhầm đã nêu ở trên
- Chưa có người có nền y tế chấm đầu ra, chưa đo độ dễ hiểu với bệnh nhân
- Khoảng tham chiếu chưa thẩm định y văn, chưa phân theo giới tính và độ tuổi
- Mỗi cấu hình chỉ chạy **một lần**, nên có KTC theo mẫu 150 phiếu nhưng không
  có biến thiên giải mã giữa các lần chạy
- Dữ liệu là tổng hợp, chưa kiểm chứng trên phiếu lâm sàng thật; chưa xử lý OCR
- Chỉ xử lý công thức máu; chưa hỗ trợ sinh hóa, miễn dịch, nước tiểu
- Chưa xử lý khoảng tham chiếu một phía (`> 40`, `< 130`) và kết quả định tính
- Kết quả chỉ từ một mô hình 3B duy nhất

## Việc còn lại — cần người, không phải cần code

**1. Tìm người có nền y tế chấm đầu ra.** Đây giờ là việc quan trọng nhất, vì
cả hai phản biện đều chỉ vào nó. Cần 2–3 người đọc mù 30–40 mẫu ngẫu nhiên và
chấm theo tính đúng, mức gây hại, và độ dễ hiểu, kèm hệ số đồng thuận.

**2. Thẩm định bảng tham chiếu.** `data/nguon_khoang_tham_chieu.csv` đã ghi rõ
nguồn và tình trạng của từng khoảng, nhưng cột tình trạng hiện là "chưa đối
chiếu y văn" ở cả 22 dòng. Cần đối chiếu tài liệu huyết học chuẩn, và thay cột
`severe_factor` bằng danh mục giá trị nguy hiểm của phòng xét nghiệm.

**3. Chạy lặp cho các cấu hình còn lại.** Mới lặp `constrained` 5 lần. Các cấu
hình khác vẫn chỉ chạy một lần, đã ghi là hạn chế trong mục 6.2.
