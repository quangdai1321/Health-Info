# Sửa bài theo phản biện vòng 2 — HI26-0013

Hạn nộp camera-ready: **31/10/2026**. File này theo dõi từng ý phản biện, việc đã làm,
và đoạn văn tiếng Anh viết sẵn để dán vào bài.

## Bảng theo dõi

| # | Ý phản biện | Việc phải làm | Tình trạng |
|---|---|---|---|
| 1 | Baseline lẫn lỗi định dạng, 97,3% dùng tên hiển thị nên 0% an toàn có thể là do định dạng | Chấm lại sau khi quy đổi mã | **Xong**, `src/cham_lai_bo_loi_dinh_dang.py` |
| 2 | Đóng góp về đơn vị đo không có số liệu trong phần Kết quả | Thí nghiệm định lượng | **Xong**, `src/thu_nghiem_don_vi.py` |
| 3 | RQ2 gộp ba thứ, thiếu cấu hình chỉ kiểm chứng | Chạy 3 cấu hình tách phần | Đang chạy |
| 4 | Chỉ thử một mô hình 3B nhưng nói về "general-purpose LLM" | Thu hẹp phát biểu trong Abstract và Introduction | Chưa |
| 5 | Không đo được "patient-friendly" | Thu hẹp phát biểu, nêu rõ là hạn chế | Chưa |
| 6 | Related work chưa đối thoại với dòng guardrail và data-to-text | Viết lại mục 2 | Bản nháp xong, xem dưới |
| 7 | "Exact by construction" trong khi ngưỡng tự đặt | Sửa thành "exact relative to the configured thresholds" | Chưa |
| 8 | Không phân theo giới tính và tuổi, nhất là HGB và HCT | Ghi vào Hạn chế, đánh dấu trong bảng nguồn | **Xong một nửa**, `data/nguon_khoang_tham_chieu.csv` |
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

## Việc còn lại theo thứ tự

1. Chờ ablation xong, dựng bảng mới cho mục 5, viết đoạn phân tích.
2. Sửa Abstract và Introduction: bỏ cách nói chung chung về "general-purpose LLM",
   nói rõ kết quả chỉ áp cho một mô hình 3B chạy tại chỗ.
3. Sửa "exact by construction" và phần "patient-friendly".
4. Thêm 4 trích dẫn vào `references.bib`, viết lại mục 2.
5. Cập nhật Hạn chế: giới tính và tuổi, phạm vi CBC, ngưỡng chưa thẩm định.
6. Soạn file trả lời phản biện, nộp kèm bản cuối.
