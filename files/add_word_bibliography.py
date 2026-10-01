# -*- coding: utf-8 -*-
"""
Biến danh mục tài liệu tham khảo TĨNH trong file .docx thành BIBLIOGRAPHY
TỰ ĐỘNG của Word, theo đúng quy trình thầy yêu cầu:

  - Nhúng sẵn 17 nguồn vào chính file .docx (customXml), nên mở
    References > Manage Sources là thấy đủ trong Current List, KHÔNG cần Browse.
  - Thay các dấu [1]...[17] trong bài bằng trường CITATION của Word.
  - Thay danh sách tài liệu tĩnh bằng trường BIBLIOGRAPHY (style IEEE).

Chạy sau khi đã sinh file bằng make_vietnamese_docx.py:
    python make_vietnamese_docx.py
    python add_word_bibliography.py
"""
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCX = HERE / "HEALTHINFO-IV_TruongQuangDai_LLM-dien-giai-xet-nghiem-mau_TiengViet.docx"
BACKUP = HERE / "bai-bao-tieng-viet_tltk-tinh.docx"   # bản dự phòng, danh mục tĩnh
SOURCES_XML = HERE / "TaiLieuThamKhao-IEEE-Sources.xml"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ITEM_ID = "{B5B1A1E4-0D2C-4C6E-9F4B-7A1C3E5D9A21}"

# Thứ tự trích dẫn [1]..[17] -> Tag trong Manage Sources
TAGS = ["Gia18", "He24", "Boz25", "Kia24", "Cad23", "Mun23", "Tra25", "Duo20",
        "Din25", "Ngu26", "Gen23", "Wil23", "Cho23", "Nal26", "Zay25", "Par18",
        "Tor26"]

ITEM_PROPS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<ds:datastoreItem ds:itemID="%s" '
    'xmlns:ds="http://schemas.openxmlformats.org/officeDocument/2006/customXml">'
    '<ds:schemaRefs><ds:schemaRef ds:uri="http://schemas.openxmlformats.org/'
    'officeDocument/2006/bibliography"/></ds:schemaRefs></ds:datastoreItem>' % ITEM_ID
)

ITEM_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
    '2006/relationships/customXmlProps" Target="itemProps1.xml"/></Relationships>'
)


def citation_field(num: int, shown: str) -> str:
    """Trường CITATION của Word, kèm sẵn nội dung hiển thị [n]."""
    tag = TAGS[num - 1]
    return (
        '<w:fldSimple w:instr=" CITATION %s \\l 1033 ">'
        '<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
        'w:cs="Times New Roman"/><w:sz w:val="26"/></w:rPr>'
        '<w:t xml:space="preserve">%s</w:t></w:r></w:fldSimple>' % (tag, shown)
    )


def convert_citations(doc_xml: str) -> tuple[str, int]:
    """Đổi mọi run chứa [n] thành trường CITATION."""
    count = 0

    def fix_run(m):
        nonlocal count
        run = m.group(0)
        texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', run, re.S)
        if not texts:
            return run
        body = texts[0]
        if not re.search(r'\[\d{1,2}\]', body):
            return run
        pieces, last = [], 0
        for mm in re.finditer(r'\[(\d{1,2})\]', body):
            n = int(mm.group(1))
            if not 1 <= n <= len(TAGS):
                continue
            before = body[last:mm.start()]
            if before:
                pieces.append('<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" '
                              'w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr>'
                              '<w:t xml:space="preserve">%s</w:t></w:r>' % before)
            pieces.append(citation_field(n, mm.group(0)))
            last = mm.end()
            count += 1
        if not pieces:
            return run
        tail = body[last:]
        if tail:
            pieces.append('<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" '
                          'w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr>'
                          '<w:t xml:space="preserve">%s</w:t></w:r>' % tail)
        return "".join(pieces)

    doc_xml = re.sub(r'<w:r>(?:(?!</w:r>).)*?</w:r>', fix_run, doc_xml, flags=re.S)
    return doc_xml, count


MARKER = "<!--BIBLIO_FIELD_HERE-->"


def extract_biblio(doc_xml: str) -> tuple[str, str, int]:
    """Gỡ các đoạn '[n] Tác giả...' ra khỏi thân bài, đặt mốc để chèn lại sau.

    Làm việc này TRƯỚC khi đổi trích dẫn, để các số [n] trong chính danh mục
    không bị biến thành trường CITATION.
    """
    paras = re.findall(r'<w:p[ >](?:(?!</w:p>).)*?</w:p>', doc_xml, re.S)
    ref_paras = []
    for p in paras:
        txt = "".join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S))
        # đoạn danh mục: bắt đầu bằng [n] và đủ dài (không phải trích dẫn trong câu)
        if re.match(r'^\s*\[\d{1,2}\]\s', txt) and len(txt) > 60:
            ref_paras.append(p)
    if not ref_paras:
        return doc_xml, "", 0

    doc_xml = doc_xml.replace(ref_paras[0], MARKER, 1)
    for p in ref_paras[1:]:
        doc_xml = doc_xml.replace(p, "", 1)
    return doc_xml, "".join(ref_paras), len(ref_paras)


def insert_biblio_field(doc_xml: str, cached: str) -> str:
    """Chèn trường BIBLIOGRAPHY vào vị trí đã đánh mốc."""
    field = (
        '<w:sdt><w:sdtPr><w:id w:val="1234567"/>'
        '<w:docPartObj><w:docPartGallery w:val="Bibliographies"/><w:docPartUnique/>'
        '</w:docPartObj></w:sdtPr><w:sdtContent>'
        '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> BIBLIOGRAPHY \\l 1033 </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r></w:p>'
        + cached +
        '<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        '</w:sdtContent></w:sdt>'
    )
    return doc_xml.replace(MARKER, field, 1)


def main():
    if not DOCX.exists():
        raise SystemExit("Chua co %s - chay make_vietnamese_docx.py truoc." % DOCX.name)
    if not SOURCES_XML.exists():
        raise SystemExit("Chua co %s - chay make_word_sources.py truoc." % SOURCES_XML.name)

    shutil.copy(DOCX, BACKUP)
    sources = SOURCES_XML.read_text(encoding="utf-8")

    zin = zipfile.ZipFile(DOCX)
    parts = {n: zin.read(n) for n in zin.namelist()}
    zin.close()

    doc = parts["word/document.xml"].decode("utf-8")
    doc, cached, n_ref = extract_biblio(doc)      # gỡ danh mục ra trước
    doc, n_cit = convert_citations(doc)           # rồi mới đổi trích dẫn trong bài
    doc = insert_biblio_field(doc, cached)        # chèn trường BIBLIOGRAPHY vào chỗ cũ
    parts["word/document.xml"] = doc.encode("utf-8")

    # 1. nhúng nguồn
    parts["customXml/item1.xml"] = sources.encode("utf-8")
    parts["customXml/itemProps1.xml"] = ITEM_PROPS.encode("utf-8")
    parts["customXml/_rels/item1.xml.rels"] = ITEM_RELS.encode("utf-8")

    # 2. khai báo content type
    ct = parts["[Content_Types].xml"].decode("utf-8")
    if "customXmlProperties" not in ct:
        ct = ct.replace(
            "</Types>",
            '<Override PartName="/customXml/itemProps1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.customXmlProperties+xml"/>'
            "</Types>")
    if 'Extension="xml"' not in ct:
        ct = ct.replace("<Types ", '<Types ', 1)
    parts["[Content_Types].xml"] = ct.encode("utf-8")

    # 3. nối quan hệ từ document -> customXml
    rels = parts["word/_rels/document.xml.rels"].decode("utf-8")
    if "customXml/item1.xml" not in rels:
        rels = rels.replace(
            "</Relationships>",
            '<Relationship Id="rIdBib1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/customXml" '
            'Target="../customXml/item1.xml"/></Relationships>')
    parts["word/_rels/document.xml.rels"] = rels.encode("utf-8")

    with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)

    print("Da chuyen %d trich dan -> truong CITATION" % n_cit)
    print("Da gop %d dong tai lieu -> mot truong BIBLIOGRAPHY (IEEE)" % n_ref)
    print("Da nhung 17 nguon vao file (Manage Sources se thay san)")
    print("Ban du phong danh muc tinh:", BACKUP.name)


if __name__ == "__main__":
    main()
