# Ngữ cảnh dự án — HEALTHINFO IV

File này để Claude Code (hoặc bất kỳ ai tiếp nhận) nắm nhanh dự án đang ở đâu.
Đọc file này trước khi sửa bất cứ thứ gì.

---

## 1. Mục tiêu

Nộp một bài báo khoa học cho hội nghị **HEALTHINFO IV** (TP.HCM, 2–3/10/2026),
**Track B — Intelligent Health Information Technologies**, chủ đề thuộc trụ cột
**Health Literacy** (trụ cột 6 trong 7 trụ cột của hội nghị).

**Hạn nộp: 23/09/2026.** Thông báo kết quả 26/09. Đăng ký online hạn 30/09.

Tác giả: ThS. Võ Hoàng Khang, HUTECH.

### Tên bài

> A Rule-Constrained Large Language Model Pipeline for Patient-Friendly
> Interpretation of Vietnamese Blood Test Results

---

## 2. Nội dung nghiên cứu — tóm tắt trong 5 câu

1. **Vấn đề:** bệnh nhân Việt Nam không đọc hiểu được phiếu xét nghiệm, và
   ngày càng hỏi LLM phổ thông để được giải thích — nhưng LLM không ràng buộc
   trả lời sai và nguy hiểm.
2. **Dữ liệu:** 150 phiếu công thức máu **tổng hợp** (synthetic), tự sinh, có
   nhãn đúng biết trước, chia đều 3 lớp mức độ.
3. **Phương pháp:** quy trình 4 tầng, trong đó **mọi phán đoán lâm sàng do
   luật (rule) quyết định trước khi LLM được gọi**; LLM chỉ diễn đạt lại nhãn
   có sẵn; tầng 4 kiểm chứng đầu ra và có đường lui.
4. **Kết quả:** trấn an sai giảm 32,0% → 8,0% → 0%; sai chiều lệch 91,3% →
   12,7% → 0%; cấu hình đầy đủ đạt 100% đầu ra an toàn (64% do LLM sinh, 36%
   dùng mẫu cố định).
5. **Đóng góp:** kiến trúc tách phán đoán khỏi LLM + bộ kiểm chứng tự động +
   chỉ số "trấn an sai" (chưa từng được báo cáo riêng) + phát hiện vấn đề
   chuẩn hóa đơn vị giữa các phòng xét nghiệm VN.

---

## 3. Cấu trúc thư mục

```
I:\Health-Info\
├── data/
│   ├── reference_ranges.csv      # 22 chỉ số CBC — bảng tham chiếu + đơn vị
│   └── synthetic_panels.json     # 150 phiếu sinh tự động, có nhãn đúng
├── src/
│   ├── classifier.py             # Tầng 1 + 2 (chuẩn hóa, phân loại bằng luật)
│   ├── generate_data.py          # sinh dữ liệu thử
│   ├── prompt_builder.py         # Tầng 3 + 4 (prompt, validate, fallback)
│   ├── run_experiment.py         # chạy 3 cấu hình qua Ollama
│   └── analyze.py                # tổng hợp thành bảng + LaTeX
├── tests/
│   └── test_classifier.py        # 38 test, TẤT CẢ PHẢI QUA
├── results/
│   ├── baseline_qwen2.5-3b.jsonl      # 150 dòng
│   ├── constrained_qwen2.5-3b.jsonl   # 150 dòng
│   ├── full_qwen2.5-3b.jsonl          # 150 dòng
│   └── summary.csv
└── paper/
    ├── manuscript.tex            # BÀI CHÍNH — 10 trang
    ├── references.bib            # 12 trích dẫn
    ├── svproc.cls                # class Springer — KHÔNG SỬA
    ├── splncs03_unsrt.bst        # style trích dẫn — KHÔNG SỬA
    ├── ban-dich-tieng-viet.md    # bản dịch để tác giả đọc
    └── architecture.png          # ⚠ CHƯA CÓ — cần xuất từ draw.io
```

---

## 4. Kiến trúc hệ thống — 4 tầng

Nguyên tắc trung tâm: **không giao phán đoán lâm sàng cho LLM.**

| Tầng | Việc | Có LLM? |
|---|---|---|
| **1. Chuẩn hóa** | Ánh xạ tên chỉ số → mã chuẩn; quy đổi đơn vị về đơn vị chuẩn; **từ chối** nếu đơn vị lạ hoặc thiếu | Không |
| **2. Phân loại bằng luật** | So sánh với khoảng tham chiếu → gán nhãn 3 mức: `binh_thuong` / `theo_doi` / `kham_som` | Không |
| **3. Sinh có ràng buộc** | LLM nhận chỉ số **kèm nhãn đã gán**, chỉ diễn đạt lại. 3 lớp ràng buộc: đầu vào / nội dung / schema JSON | Có |
| **4. Kiểm chứng** | Đối chiếu văn bản sinh ra với nhãn tầng 2; không đạt thì sinh lại, quá số lần thì dùng mẫu cố định | Không |

Luồng: `Phiếu → T1 → T2 → T3 → T4 → (Đạt?) → Có: văn bản đã kiểm chứng / Không: sinh lại → quay về T3`

### Các loại vi phạm mà tầng 4 phát hiện

| Mã | Nghĩa |
|---|---|
| `false_reassurance` | Nói mọi thứ bình thường trên phiếu bất thường — **lỗi nguy hiểm nhất** |
| `status_mismatch` | Trạng thái nêu trong văn bản không khớp nhãn tầng 2 |
| `forbidden_term` | Dùng từ cấm: tên bệnh, thuốc, liều lượng, quy nguyên nhân |
| `hallucinated_analyte` | Bịa ra chỉ số không có trong đầu vào |
| `missing_analyte` | Bỏ sót chỉ số |
| `contradictory_wording` | Câu chữ mâu thuẫn với trạng thái |
| `code_format` | Điền tên hiển thị thay vì mã chuẩn — **lỗi hình thức, không tính vào lỗi nội dung** |

---

## 5. Kết quả thực nghiệm (đã có, KHÔNG cần chạy lại)

150 phiếu × 3 cấu hình. Chạy trên Intel Core i5-9400F, 24 GB RAM, **CPU only,
không GPU**. Mô hình: Qwen2.5-3B qua Ollama.

| Cấu hình | An toàn | LLM tự đạt | Trấn an sai | Sai TT | Từ cấm | Bịa | Sót | giây |
|---|---|---|---|---|---|---|---|---|
| baseline | 0,0 | 0,0 | 32,0 | 91,3 | 79,3 | 32,0 | 71,3 | 38,9 |
| constrained | 48,0 | 48,0 | 8,0 | 12,7 | 15,3 | 10,0 | 28,7 | 35,8 |
| full | 100,0 | 64,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 68,3 |

Phụ: sai định dạng mã 97,3% (baseline) → 0% (hai cấu hình sau). Lỗi JSON 2,0%
→ 0%. Cấu hình full: trung bình 1,97 lần sinh, 36% dùng mẫu cố định.

> ⚠ **Cách trình bày bắt buộc:** "100% an toàn" gồm 64% do LLM sinh và 36% do
> đường lui. **Không được** viết câu nào ngụ ý mô hình 3B tự đạt 100%.

---

## 6. VIỆC CÒN LẠI

### 6.1. Chặn compile — làm trước tiên

- [ ] **Xuất `architecture.png`** từ sơ đồ draw.io, đặt trong `paper/`.
      Dòng `\includegraphics` đã bật sẵn trong `manuscript.tex`; thiếu file
      này thì **không biên dịch được**.
      Xuất PNG ở zoom 200%. Nếu hình quá cao, giảm `width=0.98\textwidth`
      xuống `0.9`.

**Lỗi còn tồn trong sơ đồ (chưa sửa xong):**
1. Chú thích lặp dòng `G/L` hai lần — xóa một dòng.
2. Mũi tên nhánh **"Không"** đang đi lên ô "Văn bản đã kiểm chứng" — SAI.
   Nhánh "Không" chỉ được đi sang "Sinh lại / mẫu cố định", rồi nét đứt quay
   về Tầng 3.
3. Bài viết bằng tiếng Anh nên **nên làm thêm một bản hình thuần tiếng Anh,
   bỏ khối chú thích**, dùng cho bài nộp. Bản song ngữ hiện tại giữ cho slide.

### 6.2. Ba TODO trong `manuscript.tex`

Tìm bằng `grep "%% TODO %%" manuscript.tex`:

- [ ] **Mục 3.2 (Layer 2)** — thêm 1–2 câu về công thức ngưỡng.
      Công thức: `ngưỡng = severe_factor × (high − low)`, đặt riêng cho từng
      chỉ số, giá trị hiện tại 0.15–0.50.
      **Phải nói thẳng** rằng các hệ số này đặt theo kinh nghiệm (chi tiết đã
      có ở phần Limitations).
- [ ] **Mục 3.4 (Layer 4)** — thêm 1 câu về cách chuẩn hóa văn bản trước khi
      khớp mẫu: bỏ dấu tiếng Việt, và **gỡ các cụm chỉ khoảng tham chiếu**
      (vd "cao hơn mức bình thường") để chúng không bị hiểu nhầm thành khẳng
      định trạng thái.
- [ ] Dòng TODO thứ ba chỉ là ghi chú ở đầu file, xóa được.

### 6.3. Tài liệu tham khảo

- [ ] Hai mục trong `references.bib` đánh dấu `% CAN KIEM TRA LAI DOI TRUOC KHI NOP`
      → tra Google Scholar, điền DOI đúng.
- [ ] Vài mục thiếu trường `author` (bibtex báo `Warning--empty author`).
      Chạy `bibtex manuscript` để xem danh sách.

### 6.4. Việc ngoài code (Claude Code không làm thay được)

- [ ] **Gửi email `healthinfo@uit.edu.vn`** — vẫn chưa gửi. Ba câu hỏi:
      1. Thư mời (27/6 và 24/8) không nêu rõ vai trò — là diễn giả mời hay
         khách mời?
      2. Bài thuộc Track A hay Track B?
      3. **Abstract 150 từ (theo template Springer) hay 300 từ (theo trang
         Call for Papers)?** — hiện đang viết 131 từ theo chuẩn Springer.
- [ ] **Tìm người có nền y tế** để rà soát đầu ra. Hiện chưa có ai, và điều
      này đã được ghi vào Limitations.

---

## 7. RÀNG BUỘC — đọc kỹ trước khi sửa

**Giới hạn 10 trang.** Full paper của hội nghị là 6–10 trang *kể cả tài liệu
tham khảo*. Bài hiện đúng 10 trang. Thêm chữ ở đâu thì phải bớt ở chỗ khác.
Kiểm tra bằng dòng `Output written on manuscript.pdf (N pages...)`.

**Ẩn danh double-blind.** `\author` phải để `Anonymous Author(s)` và
`\institute` để `Anonymous Institution` cho vòng phản biện. Dòng tên thật đã
comment sẵn, chỉ bỏ comment ở bản camera-ready. Không thêm Acknowledgements
vào bản review.

**Không sửa `svproc.cls` và `splncs03_unsrt.bst`** — đây là file của Springer.

**Không dùng `\usepackage[T5]{fontenc}`** — encoding tiếng Việt không có sẵn ở
mọi bản TeX. Bài viết tiếng Anh, không cần.

**38 test phải qua.** Nếu sửa `classifier.py` hay `prompt_builder.py`, chạy
`python -m pytest tests/ -q` trước khi commit.

**Nếu sửa logic tầng 2 hoặc bảng tham chiếu → phải chạy lại toàn bộ thực
nghiệm** (~6 tiếng), vì nhãn thay đổi kéo theo prompt thay đổi. Cân nhắc kỹ.

---

## 8. Lệnh hay dùng

```bash
# Biên dịch bài (chạy đủ 4 bước)
cd paper
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex

# Kiểm tra code
python -m pytest tests/ -q          # phải thấy "38 passed"
python src/classifier.py            # demo phân loại
python src/prompt_builder.py        # demo prompt + validate

# Chạy lại thực nghiệm (CHỈ KHI CẦN — mất ~6 tiếng)
python src/run_experiment.py        # tự bỏ qua phiếu đã có
python src/analyze.py               # tổng hợp thành bảng

# Sinh lại dữ liệu thử
python src/generate_data.py
```

---

## 9. Hai lỗi thật đã gặp — đáng biết để không lặp lại

**Ký hiệu `%` và `#` bị xóa khi chuẩn hóa tên.** Hàm `_normalize_key` ban đầu
xóa hết dấu câu, khiến `NEUT%` (tỷ lệ) và `NEUT#` (số tuyệt đối) gộp thành một
khóa. Đã sửa bằng cách giữ chúng thành token `pct` / `abs`. Ký hiệu có thể
đứng trước (`% Neu`) hoặc sau (`NEUT%`) tùy phòng xét nghiệm.

**Đơn vị không đồng nhất gây cảnh báo giả nghiêm trọng.** Hb báo bằng `g/dL` ở
phòng này, `g/L` ở phòng kia — chênh 10 lần. So sánh mà không quy đổi thì một
giá trị bình thường bị xếp thành "nên khám sớm", **và lỗi xảy ra ngay trong
tầng luật được tuyên bố là chính xác 100%**. Đã sửa: quy đổi về đơn vị chuẩn,
và **từ chối xử lý** khi đơn vị lạ hoặc thiếu đơn vị mà chỉ số có nhiều đơn vị
khác bậc độ lớn. Nguyên tắc: **không bao giờ đoán**.

Phát hiện thứ hai này đã trở thành một mục riêng trong phần Discussion và nối
thẳng với chủ đề chuẩn hóa dữ liệu (LOINC / HL7 FHIR) của Panel 3 tại hội nghị.
