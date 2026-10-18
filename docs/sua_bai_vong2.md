# Sửa bài theo phản biện vòng 2 — HI26-0013

Hạn nộp camera-ready: **31/10/2026**. File này theo dõi từng ý phản biện, việc đã làm,
và đoạn văn tiếng Anh viết sẵn để dán vào bài.

## Bảng theo dõi

| # | Ý phản biện | Việc phải làm | Tình trạng |
|---|---|---|---|
| 1 | Baseline lẫn lỗi định dạng, 97,3% dùng tên hiển thị nên 0% an toàn có thể là do định dạng | Chấm lại sau khi quy đổi mã | **Xong**, `src/cham_lai_bo_loi_dinh_dang.py` |
| 2 | Đóng góp về đơn vị đo không có số liệu trong phần Kết quả | Thí nghiệm định lượng | **Xong**, `src/thu_nghiem_don_vi.py` |
| 3 | RQ2 gộp ba thứ, thiếu cấu hình chỉ kiểm chứng | Chạy 3 cấu hình tách phần | **Xong**, 450/450 phiếu, Bảng 3 |
| 4 | Chỉ thử một mô hình 3B nhưng nói về "general-purpose LLM" | Thu hẹp phát biểu trong Abstract và Introduction | **Xong**, đã chèn vào bài |
| 5 | Không đo được "patient-friendly" | Thu hẹp phát biểu, nêu rõ là hạn chế | **Xong**, Abstract và mục 6.2. Tiêu đề giữ nguyên |
| 6 | Related work chưa đối thoại với dòng guardrail và data-to-text | Viết lại mục 2 | **Xong**, thêm 4 tài liệu [18]–[21] |
| 7 | "Exact by construction" trong khi ngưỡng tự đặt | Sửa thành "exact relative to the configured thresholds" | **Xong**, mục 3.2 |
| 8 | Không phân theo giới tính và tuổi, nhất là HGB và HCT | Ghi vào Hạn chế, đánh dấu trong bảng nguồn | **Xong**, mục 6.2 tách câu riêng |
| 9 | Căn cứ của ngưỡng và từ cấm | Hai bảng nguồn kèm test | **Xong**, `data/tu_cam_nguon.csv` |

## Đoạn viết sẵn, mục Related Work

> Rules that decide and a model that only renders those decisions is an established
> pattern rather than a new one. Guardrail toolkits such as NeMo Guardrails [x] place
> programmable checks around a language model, and the data-to-text literature has long
> separated content selection from surface realisation [Gatt & Krahmer]. Work on
> data-to-document generation reports that neural generators misstate facts that are
> present in their input [Wiseman et al.], and accuracy evaluation in that field relies on
> careful human protocols rather than automatic scores [Thomson & Reiter]. Our pipeline
> inherits that division of labour and adds nothing to it architecturally.
>
> What we contribute is narrower and specific to patient-facing laboratory reporting.
> First, we measure false reassurance as a separate error class, which the evaluations of
> result-explanation systems cited above do not isolate. Second, we report what the
> guarantee costs: 36% of panels fall back to fixed templates, and we state this wherever
> the 100% figure appears. Third, we document a failure of the deterministic layer itself,
> caused by unit conventions in Vietnamese laboratory reports, and quantify it.

**Tài liệu cần thêm vào references.bib** (đã kiểm chứng là có thật):

| Khóa | Trích dẫn |
|---|---|
| `rebedea2023nemo` | Rebedea, T., Dinu, R., Sreedhar, M.N., Parisien, C., Cohen, J.: NeMo Guardrails: a toolkit for controllable and safe LLM applications with programmable rails. In: EMNLP 2023 System Demonstrations, pp. 431–445 (2023) |
| `gatt2018survey` | Gatt, A., Krahmer, E.: Survey of the state of the art in natural language generation: core tasks, applications and evaluation. Journal of Artificial Intelligence Research 61, 65–170 (2018) |
| `wiseman2017challenges` | Wiseman, S., Shieber, S.M., Rush, A.M.: Challenges in data-to-document generation. In: EMNLP 2017, pp. 2253–2263 (2017) |
| `thomson2020gold` | Thomson, C., Reiter, E.: A gold standard methodology for evaluating accuracy in data-to-text systems. In: INLG 2020, pp. 158–168 (2020) |

## Đoạn viết sẵn, phần chấm lại baseline

> One configuration detail deserves scrutiny. In the baseline, 97.3% of outputs identified
> analytes by display name instead of the canonical code, which raises the question of how
> much of its 0.0% safe-output rate reflects formatting rather than content. We therefore
> re-scored every baseline output after mapping each returned name back to its canonical
> code through the alias table, which removes code-format errors entirely. Safe output rises
> from 0.0% to 0.7%, that is from zero to one panel out of 150. Direction mismatch rises
> from 91.3% to 92.7%, because items previously counted as fabricated are now matched to a
> real analyte and judged on their stated direction. False reassurance (32.0%) and
> contradictory wording (56.0%) are unchanged. The baseline therefore fails on content, not
> on formatting.

## Đoạn viết sẵn, phần đơn vị đo

> Section 3.1 claims that unit heterogeneity is a safety problem rather than a data-reuse
> problem. The claim can be quantified on the same 150 panels. Of 2,118 analyte readings,
> 143 (6.8%) were reported in a unit of different magnitude from the canonical one. Had the
> pipeline compared those readings against the reference interval without conversion, 135 of
> them (94.4%) would have received the wrong label, affecting 97 of 150 panels (64.7%). All
> 135 errors were false alarms at the most severe level: a normal haemoglobin of 14.56 g/dL,
> for example, is classified as seek-care when compared against a 130–175 g/L interval.
> No error ran in the opposite direction. The failure is confined to the deterministic layer
> and is invisible to Layer 4, because every later stage faithfully reproduces the label.

## Câu cần sửa trong bài, bản trước và sau

### Ý 4 và 5 — Abstract (đoạn 7)

**Trước:** "Vietnamese patients increasingly ask general-purpose language models to explain
laboratory reports..." và "The contribution is an auditable architecture and a separately
reported false-reassurance metric, not evidence of clinical benefit."

**Sau:** thêm hai câu giới hạn phạm vi, đặt ngay trước câu cuối:

> All results come from a single 3-billion-parameter model served locally, so they bound
> what a small on-premises model does, not what the larger hosted services patients
> typically use would do. Readability and patient comprehension were not measured; the
> evaluation establishes consistency with the assigned labels only.

### Ý 7 — câu "exact by construction" (đoạn 27)

**Trước:** "The panel label is the most severe analyte label, so classification is exact by
construction and cannot be altered by the model."

**Sau:**

> The panel label is the most severe analyte label. Classification is therefore exact with
> respect to the configured intervals and severity factors, and cannot be altered by the
> model; it is not a claim that those thresholds are clinically validated. The reference
> intervals are those printed by one Vietnamese laboratory for adults, and the severity
> factors are ours. Both are listed per analyte, with their provenance, in the supplementary
> table `nguon_khoang_tham_chieu.csv`.

### Ý 8 — Hạn chế (đoạn 50)

**Trước:** "...one-sided intervals, qualitative results, and sex- or age-specific intervals
are not handled..."

**Sau:** tách thành câu riêng để không bị đọc lướt:

> Sex- and age-specific intervals are not handled. This matters most for haemoglobin,
> haematocrit and red cell count, where adult reference intervals differ between men and
> women, so a woman's result may be labelled abnormal against a male-derived interval.

### Ý 5 — tiêu đề bài

Từ "Patient-Friendly" trong tiêu đề là một tuyên bố chưa đo được. Hai lựa chọn:

1. **Giữ tiêu đề**, và nói rõ trong Abstract rằng chưa đo độ dễ hiểu. Ưu điểm: tiêu đề đã
   in trong chương trình hội nghị và trong thư chấp nhận, đổi thì lệch hồ sơ.
2. **Đổi thành "Patient-Facing"**, đúng hơn về mặt khoa học vì chỉ mô tả đối tượng đọc,
   không hứa hẹn dễ hiểu.

Khuyến nghị: chọn 1, vì form camera-ready ghi rõ tên bài phải khớp với bài đã nộp, và
đã khai báo tên bài ở bước nộp. Thay vào đó xử lý bằng câu giới hạn trong Abstract.

## Đoạn viết sẵn, mục 4.2 — mô tả ba cấu hình tách phần

> The Constrained configuration bundles three mechanisms: rule-assigned labels, the content
> prohibitions in the prompt, and the fixed JSON schema. To separate them, we ran three
> further configurations on the same 150 panels with the same model.
>
> **Labels only** supplies the rule-assigned labels and the JSON schema, with the content
> prohibitions removed from the system prompt. **Constraints only** keeps the prohibitions
> and the schema but gives the model raw values, as in the baseline, with no labels.
> **Validator only** uses the baseline prompt unchanged and adds Layer 4: validation,
> regeneration up to the retry limit, and template fallback. Comparing these against the
> baseline isolates what each mechanism contributes, and the validator-only configuration
> answers what Layer 4 can guarantee when it has no labels to check against.

## Ghi chú kỹ thuật về đánh số trích dẫn

Bài đang dùng 17 tài liệu, đánh số theo thứ tự xuất hiện. Thêm 4 tài liệu mới vào mục 2
sẽ đẩy số của các tài liệu sau đó, nên phải đánh số lại toàn bộ cả trong thân bài lẫn
trong danh mục. Sẽ làm bằng script một lượt khi chèn cả mục 2 và mục 5, để tránh sửa tay
dễ sót. Kiểm tra sau khi chèn: mọi số trong thân bài phải có trong danh mục, và mọi tài
liệu trong danh mục phải được trích ít nhất một lần.

## Phản biện 1 — bản 13 trang, 12 vấn đề, Major Revision, 5,8/10

| # | Ý | Việc đã làm | Tình trạng |
|---|---|---|---|
| R1.1 | "safe output" tự tham chiếu | Đổi tên thước đo, thêm cấu hình chỉ mẫu cố định | **Xong** |
| R1.2 | Nhãn monitor/seek care là heuristic | Nói rõ là nhóm độ lệch, không phải chỉ định phân luồng | **Xong** |
| R1.3 | Bộ sinh dữ liệu không tái lập được | Phụ lục A: seed, phân bố, bảng chỉ số, đơn vị, bí danh | **Xong** |
| R1.4 | Baseline quá yếu, cần 5 đối chứng | Bảy cấu hình, thêm chỉ-mẫu và full-không-sinh-lại | **Xong 4/5**, thiếu mô hình lớn hơn |
| R1.5 | Chưa đo độ hiểu của bệnh nhân | **Đổi tên bài** theo đúng đề xuất của phản biện | **Xong** |
| R1.6 | Thiếu KTC, chạy lặp, tham số giải mã | KTC Wilson, McNemar, tham số đầy đủ | **Xong một phần**, chưa chạy lặp |
| R1.7 | Validator chưa đặc tả để audit | Phụ lục B, sinh thẳng từ mã | **Xong** |
| R1.8 | Phạm vi rộng hơn thực nghiệm | Tên bài và Abstract thu về CBC | **Xong** |
| R1.9 | Runtime chưa đủ để bàn triển khai | p50/p95/p99, lý do phải sinh lại | **Xong một phần**, chưa đo RAM |
| R1.10 | Thiếu phân tích lỗi định tính | Đoạn ví dụ thật trong mục 5 + Phụ lục C | **Xong** |
| R1.11 | Related work chưa định vị đủ | Viết lại đoạn đóng góp theo ba khoảng trống | **Xong** |
| R1.12 | Câu chữ quá tuyệt đối | Bỏ hết "guarantee", "no unsafe output" | **Xong** |

### Hai điều bất lợi phải báo cáo trung thực

1. **Mẫu cố định đạt 100% qua kiểm chứng**, không khác pipeline đủ tầng (McNemar p = 1,000).
   Thước đo hiện tại không phân biệt được hai thứ. Đã viết thẳng vào mục 5 và 6.2.
2. **Ràng buộc nội dung không cải thiện có ý nghĩa** so với chỉ có nhãn (p = 0,082). Đoạn
   phân tích đã sửa lại cho đúng.

Ngoài ra, khi soạn phụ lục B phát hiện bộ kiểm chứng có một kiểu **báo nhầm hệ thống**:
câu trích dẫn khoảng tham chiếu mà không có từ so sánh bị đọc thành lời khẳng định trạng
thái, ước tính khoảng 24% số câu bị lớp này từ chối. Giữ nguyên, không chỉnh validator sau
khi đã thấy kết quả, và ghi rõ ở mục 6.2 và phụ lục B.5.

## Việc còn lại theo thứ tự

Cả hai bản phản biện đã xử lý xong trong bài. Còn lại là việc nộp và hai việc tùy chọn:

1. Xuất `docs/phan_hoi_phan_bien.md` và `docs/phu_luc_bo_sung.md` ra PDF để nộp kèm.
2. Báo ban tổ chức là tên bài đổi theo yêu cầu của Phản biện 1, vì form camera-ready
   yêu cầu tên bài khớp với bài đã nộp.
3. Nộp trước 31/10/2026: bản PDF cuối, file nguồn Word, bản trả lời phản biện, phụ lục,
   mã nguồn và dữ liệu.
4. *Tùy chọn, còn 13 ngày:* chạy thêm một mô hình lớn hơn (R1.4 ý 5, R2.4) và chạy lặp
   5 lần mỗi cấu hình (R1.6). Cả hai đều chạy được trên máy hiện tại nhưng mất nhiều giờ.

## Số trang

Bản cuối ra **11 trang PDF**, hơn giới hạn gốc 1 trang. Tác giả đã đồng ý thêm 1 trang.
Word báo 14 trang vì đếm theo phân trang màn hình; bản PDF mới là bản nộp.
