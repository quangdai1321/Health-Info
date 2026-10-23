# Điền form Camera-ready — HI26-0013

Hạn 31/10/2026. Form có sẵn dữ liệu cũ, **hai ô phải sửa** trước khi nộp.

---

## ⚠ Ô "Tên bài cuối cùng" — PHẢI SỬA

Form đang điền sẵn tên **cũ**. Xóa đi, dán đúng dòng này:

```
A Rule-Constrained Large Language Model Pipeline for Rule-Consistent Explanation of Vietnamese Complete Blood Count Results
```

Lý do: Phản biện 1 yêu cầu đổi tên (ý 5), và ô tick cuối form bắt cam kết tên bài
khớp với file nộp. Để nguyên tên cũ là form và bài mâu thuẫn nhau.

---

## ⚠ Ô "Danh sách tác giả theo thứ tự" — PHẢI SỬA

Form đang ghi mỗi người một đơn vị, nhưng bài có ba dòng đơn vị. Dán hai dòng này:

```
Vo Hoang Khang — Vietnam-Korea Institute of Technology, HUTECH University; Faculty of Information Technology, HUTECH University
Truong Quang Dai — Vietnam-Korea Institute of Technology, HUTECH University; Faculty of Information Technology, HUTECH University; FPT Telecom
```

Đối chiếu với khối tác giả in trong bài:

> Vo Hoang Khang^1,2,* and Truong Quang Dai^1,2,3
> ^1 Vietnam-Korea Institute of Technology, HUTECH University, Ho Chi Minh City, Vietnam
> ^2 Faculty of Information Technology, HUTECH University, Ho Chi Minh City, Vietnam
> ^3 FPT Telecom, Ho Chi Minh City, Vietnam
> \* Corresponding author: Vo Hoang Khang (vh.khang@hutech.edu.vn)

**Ba lỗi hay mắc, đã gặp một lần khi xem preview:**

1. Đơn vị thứ hai của thầy Khang phải là `Faculty of Information Technology, HUTECH
   University`, không phải `HUTECH University` trống không — ghi vậy là trùng nửa sau
   của đơn vị thứ nhất.
2. Truong Quang Dai có **ba** đơn vị, không phải hai. Thiếu Vietnam-Korea Institute of
   Technology và Faculty of IT là lệch với bài.
3. Form đánh số tách rời cho từng tác giả (1 và 2), còn bài dùng 1,2 và 1,2,3 vì hai
   tác giả **dùng chung** hai đơn vị đầu. Đây là giới hạn của form, không sửa được;
   đã nêu trong ô Ghi chú để ban tổ chức xếp lại khi dàn trang.

Nếu ô không nhận dòng dài, rút gọn thành `Vo Hoang Khang — HUTECH University` và
`Truong Quang Dai — HUTECH University; FPT Telecom`, rồi ghi đầy đủ vào ô Ghi chú.

---

## Ba ô upload

| Ô trong form | File | Dung lượng | Giới hạn |
|---|---|---|---|
| Bài hoàn chỉnh — PDF | `HI26-0013_Camera-Ready_Paper.pdf` | 0,50 MB | 10 MB |
| File nguồn — Word / LaTeX | `HI26-0013_Source-and-Supplementary.zip` | 1,36 MB | 10 MB |
| Phản hồi nhận xét reviewer | `HI26-0013_Response-to-Reviewers.pdf` | 0,49 MB | 5 MB |

**Vì sao ô "File nguồn" lại là .zip, không phải .docx:** form không có ô nào cho tài
liệu bổ sung, mà bài dẫn chiếu tới Phụ lục A, B, C. Ô này nhận `.zip`, nên gói gồm
bản Word nguồn + phụ lục + mã nguồn và dữ liệu, kèm `README.txt` ở gốc nói rõ có gì.
Nếu ban tổ chức chỉ muốn đúng file Word thì dùng `HI26-0013_Camera-Ready_Paper.docx`
và gửi phần còn lại qua email.

---

## Ô "Ghi chú cho Ban Tổ chức" / "Notes to the organizers"

Không bắt buộc, nhưng nên điền: đổi tên bài và nộp file nguồn dạng zip là hai việc
bất thường, không nói trước dễ bị hỏi lại.

```
Title changed at Reviewer 1's request (point 5). The reviewer asked us either to add a
patient comprehension study or to narrow the title; we used his own wording. Happy to
revert if the committee prefers the original.

Both authors share affiliations 1 and 2. In the paper: Vo Hoang Khang^1,2 and Truong
Quang Dai^1,2,3, where 1 = Vietnam-Korea Institute of Technology, 2 = Faculty of
Information Technology (both HUTECH University), 3 = FPT Telecom.

The source upload is a .zip because the form has no supplementary field and the paper
cites Appendices A-C. It holds the Word source, the appendices, and the code and data,
with a README.txt at the root.

The paper is 11 pages, one over the guideline, owing to the experiments both reviewers
requested. We can shorten it if required.
```

Cần ngắn nữa thì bỏ đoạn **Affiliations** — ban tổ chức nhìn file PDF cũng thấy.

---

## Kiểm trước khi tick ô cam kết

Ô tick ghi: *"Tôi xác nhận bài đã đúng định dạng và tên bài, tác giả, đơn vị ở trên
khớp với file nộp."* Mở `HI26-0013_Camera-Ready_Paper.pdf` trang 1 và soi đúng bốn thứ:

- [ ] Tên bài có chữ **"Rule-Consistent Explanation"** và **"Complete Blood Count"** — nếu còn thấy "Patient-Friendly" là mở nhầm file cũ ở thư mục `Tai lieu\`
- [ ] **Vo Hoang Khang** đứng trước Truong Quang Dai
- [ ] Ba dòng đơn vị: Vietnam-Korea Institute of Technology / Faculty of IT / FPT Telecom
- [ ] Trang 11 kết thúc ở tài liệu **[21] Thomson, C., Reiter, E.**

Mấy mục trong checklist của form đã kiểm bằng máy rồi:

- Font trong PDF: **đã nhúng toàn bộ** (Arial, Times New Roman, Times New Roman Bold). Bản xuất lần đầu thiếu hai font nên đã xuất lại ở chế độ PDF/A.
- Tài liệu tham khảo: **21/21 đều được trích**, không có số nào vượt danh mục.
- Bảng: 3 bảng, đối chiếu từng ô với dữ liệu gốc, **không lệch ô nào**.
