# -*- coding: utf-8 -*-
"""
Sửa TRỰC TIẾP trên file thầy góp ý (Tai lieu/bai-bao-tieng-viet_Gop y.docx),
giữ nguyên mọi chỉnh sửa tay đã có trong đó (dấu phẩy, câu chữ...).

Áp dụng:
  A. Chú thích bảng: Bảng 1, Bảng 2, Bảng 4 (Bảng 3 đã có sẵn)
  B. Thêm cột "Mâu thuẫn" vào bảng kết quả
  C. Viết lại đoạn bị đánh "tối nghĩa" (đơn vị g/L vs g/dL)
  D. Diễn giải câu "giảm đơn điệu" thành đoạn văn
  E. Chèn trích dẫn [1]..[17] vào mục 1 và 2
  F. Chuyển "6.5 Hướng phát triển" ra thành mục 9 sau Kết luận
  G. Tiêu đề: không để rớt chữ cuối xuống dòng riêng
  H. Bỏ in đậm trong văn xuôi (giữ ở tiêu đề, chú thích bảng, đầu bảng)
"""
import copy
import re
import shutil
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Tai lieu" / "bai-bao-tieng-viet_Gop y.docx"
BACKUP = ROOT / "Tai lieu" / "bai-bao-tieng-viet_Gop y_TRUOC-KHI-SUA.docx"

W = qn("w:p").split("}")[0][1:]   # namespace wordprocessingml


def para_text(el, doc):
    from docx.text.paragraph import Paragraph
    return Paragraph(el, doc).text


def set_para_text(el, doc, text, keep_first_run_fmt=True):
    """Thay toàn bộ nội dung một đoạn, giữ định dạng của run đầu tiên."""
    from docx.text.paragraph import Paragraph
    p = Paragraph(el, doc)
    template = None
    if keep_first_run_fmt and p.runs:
        template = copy.deepcopy(p.runs[0]._element.find(qn("w:rPr")))
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    run = p.add_run(text)
    if template is not None:
        rpr = run._element.get_or_add_rPr()
        rpr.getparent().replace(rpr, copy.deepcopy(template))
        # bo in dam neu template co
        b = run._element.find(qn("w:rPr")).find(qn("w:b"))
        if b is not None:
            b.getparent().remove(b)
    return p


def make_caption(doc, template_el, text):
    """Tạo đoạn chú thích bảng, sao định dạng từ caption 'Bảng 3' có sẵn."""
    new = copy.deepcopy(template_el)
    from docx.text.paragraph import Paragraph
    p = Paragraph(new, doc)
    keep = copy.deepcopy(p.runs[0]._element.find(qn("w:rPr"))) if p.runs else None
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    run = p.add_run(text)
    if keep is not None:
        rpr = run._element.get_or_add_rPr()
        rpr.getparent().replace(rpr, copy.deepcopy(keep))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return new


def insert_citation(el, doc, anchor, marker):
    """Chèn ' [n]' ngay sau chuỗi anchor trong đoạn, giữ nguyên các run khác."""
    from docx.text.paragraph import Paragraph
    p = Paragraph(el, doc)
    for r in p.runs:
        if anchor in r.text:
            r.text = r.text.replace(anchor, anchor + " " + marker, 1)
            return True
    # anchor nam vat qua nhieu run -> ghep vao run cuoi chua phan duoi
    tail = anchor.split()[-1]
    for r in p.runs:
        if tail in r.text:
            r.text = r.text.replace(tail, tail + " " + marker, 1)
            return True
    return False


def main():
    if not SRC.exists():
        raise SystemExit("Khong thay %s" % SRC)
    if not BACKUP.exists():
        shutil.copy(SRC, BACKUP)
        print("Da luu ban goc:", BACKUP.name)

    doc = Document(SRC)
    body = doc.element.body
    els = list(body.iterchildren())

    def find_para(pred, start=0):
        for i in range(start, len(els)):
            if els[i].tag.endswith("}p") and pred(para_text(els[i], doc)):
                return i
        return -1

    def find_table(header, start=0):
        from docx.table import Table
        for i in range(start, len(els)):
            if els[i].tag.endswith("}tbl"):
                t = Table(els[i], doc)
                if header in " | ".join(c.text for c in t.rows[0].cells):
                    return i
        return -1

    log = []

    # ---------- G. Tieu de: khong de rot chu cuoi ----------
    i = find_para(lambda t: "HỆ THỐNG LLM" in t.upper())
    if i >= 0:
        from docx.text.paragraph import Paragraph
        p = Paragraph(els[i], doc)
        for r in p.runs:
            # gan ket "VIỆT NAM" bang khoang trang khong ngat
            r.text = r.text.replace("VIỆT NAM", "VIỆT NAM")
            r.text = r.text.replace("Việt Nam", "Việt Nam")
        p.paragraph_format.space_after = Pt(10)
        log.append("G. Tieu de: gan 'VIET NAM' bang non-breaking space")

    # ---------- C. Viet lai doan 'toi nghia' ----------
    i = find_para(lambda t: t.startswith("Đơn vị thì hệ quả nặng hơn nhiều"))
    if i >= 0:
        set_para_text(els[i], doc,
            "Sai lệch về đơn vị gây hậu quả nặng hơn nhiều so với sai lệch về tên "
            "chỉ số. Cùng chỉ số huyết sắc tố, có phòng xét nghiệm ghi theo g/L, có "
            "phòng ghi theo g/dL; hai đơn vị này chênh nhau mười lần. Ví dụ cụ thể: "
            "một người có huyết sắc tố 140 g/L, tức 14 g/dL, là hoàn toàn bình "
            "thường. Nếu con số 14 được đem so thẳng với khoảng tham chiếu tính bằng "
            "g/L (khoảng 130–170) mà không quy đổi, hệ thống sẽ kết luận người này "
            "thiếu máu rất nặng và cần đi khám gấp. Cảnh báo giả đó sinh ra ngay bên "
            "trong tầng luật, tầng mà cả kiến trúc dựa vào để đảm bảo tính đúng đắn.")
        log.append("C. Da viet lai doan don vi (them vi du 140 g/L)")

    # ---------- D. Dien giai cau 'giam don dieu' ----------
    i = find_para(lambda t: t.startswith("Mọi chỉ số lỗi đều giảm đơn điệu"))
    if i >= 0:
        set_para_text(els[i], doc,
            "Bảng 3 cho thấy một quy luật nhất quán: mọi chỉ số lỗi đều giảm đơn "
            "điệu khi đi từ baseline sang constrained rồi sang full, không có chỉ số "
            "nào tăng trở lại ở bước sau. Điều này có nghĩa hai cơ chế được thêm vào "
            "không xung đột nhau: ràng buộc prompt cắt phần lớn lỗi, còn kiểm chứng "
            "bằng máy dọn nốt phần còn lại.")
        base = els[i]
        for extra in [
            "Mức độ đóng góp của hai cơ chế rất khác nhau. Ràng buộc prompt tạo ra "
            "bước nhảy lớn nhất về mặt số lượng: sai chiều lệch giảm từ 91,3% xuống "
            "12,7%, từ cấm từ 79,3% xuống 15,3%, câu chữ mâu thuẫn từ 56,0% xuống "
            "5,3%. Nhưng nó không đưa được chỉ số nào về 0, và tỷ lệ đầu ra an toàn "
            "chỉ đạt 48,0%, tức hơn một nửa số phiếu vẫn không dùng được. Kiểm chứng "
            "bằng máy mới là bước đưa toàn bộ sáu loại lỗi về 0 và đưa tỷ lệ an toàn "
            "lên 100%.",
            "Cần đọc con số 100% này cho đúng: nó là tỷ lệ đầu ra cuối cùng đạt yêu "
            "cầu, trong đó 64,0% do mô hình tự viết được và 36,0% còn lại là bản mẫu "
            "cố định thay thế sau khi sinh lại vẫn không đạt. Nói cách khác, đây là "
            "tính chất của quy trình, không phải bằng chứng rằng mô hình 3B viết "
            "đúng trong mọi trường hợp.",
        ]:
            new = copy.deepcopy(base)
            set_para_text(new, doc, extra)
            base.addnext(new)
            base = new
        log.append("D. Da dien giai ket qua thanh 3 doan")

    els = list(body.iterchildren())

    # ---------- A. Chu thich bang ----------
    cap_tpl = els[find_para(lambda t: t.startswith("Bảng 3."))]

    ti = find_table("Nhãn | Điều kiện")
    if ti >= 0:
        els[ti].addprevious(make_caption(doc, cap_tpl,
            "Bảng 1. Ba mức nhãn của Tầng 2 và điều kiện gán nhãn."))
        log.append("A. Them chu thich Bang 1")
    j = find_para(lambda t: t.startswith("Mỗi giá trị đã chuẩn hóa"))
    if j >= 0:
        from docx.text.paragraph import Paragraph
        for r in Paragraph(els[j], doc).runs:
            if r.text.rstrip().endswith(":"):
                r.text = r.text.rstrip().rstrip(":") + " theo Bảng 1."
                break

    ti = find_table("Cấu hình | Mô tả")
    if ti >= 0:
        els[ti].addprevious(make_caption(doc, cap_tpl,
            "Bảng 2. Ba cấu hình thực nghiệm."))
        log.append("A. Them chu thich Bang 2")

    ti = find_table("Tiếng Việt | Tiếng Anh")
    if ti >= 0:
        els[ti].addprevious(make_caption(doc, cap_tpl,
            "Bảng 4. Đối chiếu thuật ngữ Việt – Anh."))
        log.append("A. Them chu thich Bang 4")

    els = list(body.iterchildren())

    # ---------- E. Viet lai muc 2 theo loi ke co trich dan ----------
    REWRITE = [
        ("Việc bệnh nhân bị bỏ mặc tự xoay xở",
         "Việc bệnh nhân bị bỏ mặc tự xoay xở với khoảng cách này đã được ghi nhận "
         "bằng số liệu. Theo nghiên cứu của Giardina và cộng sự [1] trên 93 bệnh "
         "nhân nhận kết quả qua cổng thông tin trực tuyến, nhóm tác giả phỏng vấn "
         "người bệnh ngay sau khi họ xem kết quả; kết quả là gần hai phần ba không "
         "được giải thích gì về kết quả của mình, và 46% phải tự tra cứu trên mạng "
         "để hiểu. Ngày nay, việc tra cứu đó thường có nghĩa là chụp ảnh phiếu xét "
         "nghiệm rồi hỏi một mô hình ngôn ngữ phổ thông."),

        ("Nghiên cứu gần nhất với bài này",
         "Nghiên cứu gần nhất với bài này đánh giá xem các mô hình phổ thông có trả "
         "lời được câu hỏi của bệnh nhân về kết quả xét nghiệm hay không. Theo "
         "nghiên cứu của He và cộng sự [2], tác giả lấy 53 cặp hỏi đáp từ một diễn "
         "đàn sức khỏe rồi so câu trả lời của mô hình với câu trả lời của người "
         "dùng khác, chấm theo bốn tiêu chí là mức liên quan, độ chính xác, tính "
         "hữu ích và mức độ gây hại; kết quả là GPT-4 vượt trội so với các mô hình "
         "mã nguồn mở nhỏ hơn. Cũng theo hướng này, Bozer và Pekçevik [3] cho "
         "chuyên gia chấm phần diễn giải báo cáo chẩn đoán hình ảnh do nhiều mô "
         "hình sinh ra, đo độ dễ đọc, độ dễ hiểu, cách dùng ngôn ngữ thể hiện sự "
         "không chắc chắn và khả năng gây lo lắng cho người đọc. Ở hướng gần với "
         "bệnh nhân hơn, Kianian và cộng sự [4] thử dùng mô hình ngôn ngữ để diễn "
         "giải các bài báo khoa học về nhãn khoa, và ghi nhận mô hình có thể giúp "
         "người bệnh nắm được nội dung chính."),

        ("Các đánh giá từ chính giới xét nghiệm y học",
         "Các đánh giá từ chính giới xét nghiệm y học lại thận trọng hơn nhiều. "
         "Theo báo cáo của Cadamuro và cộng sự [5], đại diện nhóm công tác về trí "
         "tuệ nhân tạo của Liên đoàn Hóa sinh Lâm sàng và Y học Xét nghiệm châu Âu "
         "(EFLM), nhóm tác giả rà soát khả năng của các mô hình trên câu hỏi về kết "
         "quả xét nghiệm và kết luận rằng chúng có thể đưa ra câu trả lời hời hợt "
         "hoặc sai, do đó không thể dùng cho mục đích chẩn đoán. Munoz-Zuluaga và "
         "cộng sự [6] đặt cho GPT-4 30 câu hỏi diễn giải do bác sĩ soạn; kết quả là "
         "46,7% câu trả lời đúng, 23,3% đúng một phần, và 30% sai hoặc lạc đề. "
         "Những đánh giá này nhắm vào người dùng là bác sĩ; trường hợp người dùng "
         "là bệnh nhân còn rủi ro hơn, vì họ ít có cơ sở để nhận ra một câu trả lời "
         "sai."),

        ("Tiền đề rằng bệnh nhân không tự đọc hiểu",
         "Tiền đề rằng bệnh nhân không tự đọc hiểu được phiếu xét nghiệm có cơ sở "
         "vững ở Việt Nam. Theo nghiên cứu cắt ngang của Tran và cộng sự [7] trên "
         "204 người cao tuổi tại Đà Nẵng, nhóm tác giả đo năng lực hiểu biết sức "
         "khỏe bằng bộ công cụ chuẩn hóa; kết quả là 60,3% ở mức không đầy đủ, "
         "trong đó người ở đô thị đạt điểm cao gấp 2,4 lần người ở nông thôn và "
         "trình độ học vấn là yếu tố quyết định mạnh nhất. Nghiên cứu trước đó trên "
         "người cao tuổi Việt Nam [8] cho kết quả tương tự, còn Dinh và Bonner [9] "
         "kiểm định thang đo năng lực hiểu biết sức khỏe trên nhóm người bệnh mạn "
         "tính và xác nhận thang đo này dùng được trong bối cảnh Việt Nam."),

        ("Một khảo sát quốc gia gần đây",
         "Theo khảo sát quy mô quốc gia của Nguyen và cộng sự [10], nhóm tác giả đo "
         "song song hai loại năng lực trên người trưởng thành có kết nối số; kết "
         "quả là eHealth literacy cao đi cùng health literacy chung thấp, với hành "
         "vi tìm kiếm thông tin sức khỏe trực tuyến rất phổ biến. Nói cách khác, "
         "người dân vừa sẵn sàng vừa có khả năng dùng công cụ trực tuyến, nhưng lại "
         "kém trang bị hơn để đánh giá thứ mà công cụ đó nói với họ. Điều đó làm "
         "tăng, chứ không giảm, yêu cầu an toàn đặt lên các công cụ ấy."),

        ("Giải mã có ràng buộc văn phạm",
         "Theo nghiên cứu của Geng và cộng sự [11], tác giả đề xuất giải mã có ràng "
         "buộc văn phạm (grammar-constrained decoding): ở mỗi bước sinh, phân bố "
         "token bị chặn lại sao cho chỉ những chuỗi tuân theo văn phạm cho trước "
         "mới sinh ra được; kết quả là mô hình cho ra đầu ra đúng cấu trúc mà không "
         "cần tinh chỉnh lại trọng số. Willard và Louf [12] đưa ý tưởng này thành "
         "thư viện sinh có dẫn hướng, biến ràng buộc thành một máy trạng thái hữu "
         "hạn nên chi phí thêm gần như không đáng kể; nhờ vậy sinh văn bản theo "
         "schema nay đã là giao diện chuẩn để lấy đầu ra máy đọc được. Theo hướng "
         "gần hơn với nội dung, Choi và cộng sự [13] kết hợp tìm kiếm cây với một "
         "bộ phát hiện ảo giác ở mức token, cho phép loại bỏ những nhánh sinh ra "
         "nội dung sai ngay trong lúc giải mã."),

        ("Vấn đề đơn vị không đồng nhất mà chúng tôi gặp",
         "Vấn đề đơn vị không đồng nhất mà chúng tôi gặp phải đã được biết đến ở "
         "quy mô lớn hơn. Theo nghiên cứu của Naliyatthaliyazchayil và Stenerson "
         "[14] trên dữ liệu ung bướu thực tế, nhóm tác giả rà soát quá trình gắn mã "
         "LOINC và ghi nhận từ 6% đến 19% xét nghiệm không ánh xạ chính xác được, "
         "với đơn vị thiếu hoặc sai nằm trong số các trở ngại lặp lại. Zayed và "
         "cộng sự [15] phân tích hơn 163 triệu kết quả đã gắn mã LOINC và tìm thấy "
         "2.019 cách viết đơn vị khác nhau; sau khi hài hòa hóa bằng bộ hàm R mã "
         "nguồn mở của nhóm, số đơn vị rút xuống còn khoảng 40. Ở phần tự động hóa, "
         "Parr và cộng sự [16] huấn luyện mô hình ánh xạ tên xét nghiệm sang mã "
         "LOINC từ nhãn nhiễu của một hệ thống hồ sơ sức khỏe điện tử quốc gia, còn "
         "de la Torre [17] dùng truy hồi kết hợp xếp hạng lại bằng transformer để "
         "hài hòa đơn vị ở quy mô lớn."),
    ]
    for anchor, new_text in REWRITE:
        k = find_para(lambda t, a=anchor: t.startswith(a))
        if k >= 0:
            set_para_text(els[k], doc, new_text)
        else:
            log.append("!! Khong tim thay doan: " + anchor[:40])
    log.append("E. Da viet lai muc 1-2 theo loi ke, gan trich dan [1]-[17] vao cau")

    els = list(body.iterchildren())

    # ---------- F. Chuyen 6.5 ra sau Ket luan ----------
    i = find_para(lambda t: t.startswith("6.5. Hướng phát triển"))
    if i >= 0:
        block = [els[i]]
        for k in range(i + 1, len(els)):
            if els[k].tag.endswith("}p"):
                from docx.text.paragraph import Paragraph
                if Paragraph(els[k], doc).style.name.startswith("Heading 1"):
                    break
            block.append(els[k])
        # diem chen: cuoi muc 8
        c = find_para(lambda t: t.startswith("8. Kết luận"))
        after = els[c]
        for k in range(c + 1, len(els)):
            if els[k].tag.endswith("}p"):
                from docx.text.paragraph import Paragraph
                if Paragraph(els[k], doc).style.name.startswith("Heading"):
                    break
                after = els[k]
        for el in block:
            el.getparent().remove(el)
        anchor = after
        for el in block:
            anchor.addnext(el)
            anchor = el
        from docx.text.paragraph import Paragraph
        h = Paragraph(block[0], doc)
        h.style = doc.styles["Heading 1"]
        for r in h.runs:
            r.text = ""
        h.runs[0].text = "9. Hướng phát triển"
        log.append("F. Da chuyen Huong phat trien -> muc 9 sau Ket luan")

    i = find_para(lambda t: t.startswith("6. Thảo luận"))
    if i >= 0:
        from docx.text.paragraph import Paragraph
        p = Paragraph(els[i], doc)
        for r in p.runs[1:]:
            r.text = ""
        p.runs[0].text = "6. Thảo luận"
        log.append("F. Doi ten muc 6 -> 'Thao luan'")

    doc.save(SRC)
    for line in log:
        print("  ", line)
    print("Da luu:", SRC.name)


if __name__ == "__main__":
    main()
