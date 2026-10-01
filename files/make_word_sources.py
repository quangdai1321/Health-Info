# -*- coding: utf-8 -*-
"""
Sinh file nguồn tài liệu tham khảo cho Word (References > Manage Sources).

Cách dùng trong Word:
  1. Tab References > Style: chọn **IEEE**
  2. References > Manage Sources > Browse... > chọn file Sources.xml này
  3. Chọn hết bên Master List > Copy sang Current List
  4. Đặt con trỏ ở mục "Tài liệu tham khảo" > References > Bibliography >
     Insert Bibliography
  5. Chèn trích dẫn trong bài: References > Insert Citation > chọn nguồn

Sau đó Word tự đánh số [1], [2]... theo đúng chuẩn IEEE và tự cập nhật.
"""
from pathlib import Path
from xml.sax.saxutils import escape

NS = "http://schemas.openxmlformats.org/officeDocument/2006/bibliography"
OUT = Path(__file__).resolve().parent / "TaiLieuThamKhao-IEEE-Sources.xml"

# (tag, tác giả [(họ, tên, đệm)], tiêu đề, tên tạp chí/kỷ yếu, năm, vol, issue, pages, loại)
SOURCES = [
    ("Gia18", [("Giardina", "T", "D"), ("Baldwin", "J", ""), ("Nystrom", "D", "T"),
               ("Sittig", "D", "F"), ("Singh", "H", "")],
     "Patient perceptions of receiving test results via online portals: A mixed-methods study",
     "Journal of the American Medical Informatics Association", "2018", "25", "4", "440-446", "JournalArticle"),

    ("He24", [("He", "Z", ""), ("Bhasuran", "B", ""), ("Jin", "Q", ""), ("Tian", "S", ""),
              ("Hanna", "K", ""), ("Shavor", "C", ""), ("Lu", "Z", "")],
     "Quality of answers of generative large language models versus peer users for interpreting laboratory test results for lay patients: Evaluation study",
     "Journal of Medical Internet Research", "2024", "26", "", "e56655", "JournalArticle"),

    ("Boz25", [("Bozer", "A", ""), ("Pekcevik", "Y", "")],
     "Comparative evaluation of large language models in explaining radiology reports: Expert assessment of readability, understandability, and communication features",
     "Insights into Imaging", "2025", "16", "", "232", "JournalArticle"),

    ("Kia24", [("Kianian", "R", ""), ("Sun", "D", ""), ("Rojas-Carabali", "W", ""),
               ("Agrawal", "R", ""), ("Tsui", "E", "")],
     "Large language models may help patients understand peer-reviewed scientific articles about ophthalmology: Development and usability study",
     "Journal of Medical Internet Research", "2024", "26", "", "e59843", "JournalArticle"),

    ("Cad23", [("Cadamuro", "J", ""), ("Cabitza", "F", ""), ("Debeljak", "Z", ""),
               ("De Bruyne", "S", ""), ("Frans", "G", ""), ("Perez", "S", "M")],
     "Potentials and pitfalls of ChatGPT and natural-language artificial intelligence models for the understanding of laboratory medicine test results: An assessment by the European Federation of Clinical Chemistry and Laboratory Medicine (EFLM) Working Group on Artificial Intelligence",
     "Clinical Chemistry and Laboratory Medicine", "2023", "61", "7", "1158-1166", "JournalArticle"),

    ("Mun23", [("Munoz-Zuluaga", "C", ""), ("Zhao", "Z", ""), ("Wang", "F", ""),
               ("Greenblatt", "M", "B"), ("Yang", "H", "S")],
     "Assessing the accuracy and clinical utility of ChatGPT in laboratory medicine",
     "Clinical Chemistry", "2023", "69", "8", "939-940", "JournalArticle"),

    ("Tra25", [("Tran", "M", "T"), ("Lai", "H", "T"), ("Hoang", "H", "T")],
     "Health literacy among older adults: A descriptive cross-sectional analysis in Vietnam",
     "Journal of Health Literacy", "2025", "10", "2", "91-100", "JournalArticle"),

    ("Duo20", [],
     "Factors associated with health literacy among the elderly people in Vietnam",
     "BioMed Research International", "2020", "2020", "", "3490635", "JournalArticle"),

    ("Din25", [("Dinh", "T", "T H"), ("Bonner", "A", "")],
     "Psychometric properties of the health literacy questionnaire tested in Vietnamese adults with chronic diseases",
     "BMC Public Health", "2025", "25", "", "44", "JournalArticle"),

    ("Ngu26", [("Nguyen", "B", "N"), ("Ngo", "T", "T")],
     "Health and eHealth literacy in Vietnam: Evidence from a national survey",
     "Patient Education and Counseling", "2026", "148", "", "109583", "JournalArticle"),

    ("Gen23", [("Geng", "S", ""), ("Josifoski", "M", ""), ("Peyrard", "M", ""), ("West", "R", "")],
     "Grammar-constrained decoding for structured NLP tasks without finetuning",
     "Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
     "2023", "", "", "", "ConferenceProceedings"),

    ("Wil23", [("Willard", "B", "T"), ("Louf", "R", "")],
     "Efficient guided generation for large language models",
     "arXiv preprint arXiv:2307.09702", "2023", "", "", "", "JournalArticle"),

    ("Cho23", [("Choi", "S", ""), ("Fang", "T", ""), ("Wang", "Z", ""), ("Song", "Y", "")],
     "KCTS: Knowledge-constrained tree search decoding with token-level hallucination detection",
     "Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
     "2023", "", "", "", "ConferenceProceedings"),

    ("Nal26", [("Naliyatthaliyazchayil", "P", ""), ("Stenerson", "T", "")],
     "Harmonizing Logical Observation Identifiers Names and Codes (LOINC) codes and units in real-world oncology data: Method development and evaluation",
     "JMIR Medical Informatics", "2026", "14", "", "e81254", "JournalArticle"),

    ("Zay25", [("Zayed", "A", "M"), ("Sarikakis", "I", ""), ("Delvaux", "N", "")],
     "Automated standardization and harmonization of laboratory units in large-scale clinical data using open-source R functions",
     "International Journal of Medical Informatics", "2025", "205", "", "106131", "JournalArticle"),

    ("Par18", [("Parr", "S", "K"), ("Shotwell", "M", "S"), ("Jeffery", "A", "D"),
               ("Lasko", "T", "A"), ("Matheny", "M", "E")],
     "Automated mapping of laboratory tests to LOINC codes using noisy labels in a national electronic health record system database",
     "Journal of the American Medical Informatics Association", "2018", "25", "10", "1292-1300", "JournalArticle"),

    ("Tor26", [("de la Torre", "J", "")],
     "Scalable unit harmonization in medical informatics via Bayesian-optimized retrieval and transformer-based re-ranking",
     "International Journal of Medical Informatics", "2026", "206", "", "106180", "JournalArticle"),
]


def person_xml(last, first, middle):
    parts = [f"<b:Last>{escape(last)}</b:Last>"]
    if first:
        parts.append(f"<b:First>{escape(first)}</b:First>")
    if middle:
        parts.append(f"<b:Middle>{escape(middle)}</b:Middle>")
    return "<b:Person>" + "".join(parts) + "</b:Person>"


def source_xml(tag, authors, title, container, year, vol, issue, pages, stype):
    out = ["<b:Source>",
           f"<b:Tag>{escape(tag)}</b:Tag>",
           f"<b:SourceType>{stype}</b:SourceType>"]
    if authors:
        people = "".join(person_xml(*a) for a in authors)
        out.append("<b:Author><b:Author><b:NameList>"
                   + people + "</b:NameList></b:Author></b:Author>")
    out.append(f"<b:Title>{escape(title)}</b:Title>")
    if stype == "ConferenceProceedings":
        out.append(f"<b:ConferenceName>{escape(container)}</b:ConferenceName>")
    else:
        out.append(f"<b:JournalName>{escape(container)}</b:JournalName>")
    out.append(f"<b:Year>{escape(year)}</b:Year>")
    if vol:
        out.append(f"<b:Volume>{escape(vol)}</b:Volume>")
    if issue:
        out.append(f"<b:Issue>{escape(issue)}</b:Issue>")
    if pages:
        out.append(f"<b:Pages>{escape(pages)}</b:Pages>")
    out.append("<b:RefOrder>%d</b:RefOrder>" % source_xml.counter)
    source_xml.counter += 1
    out.append("</b:Source>")
    return "".join(out)


source_xml.counter = 1


def main():
    body = "".join(source_xml(*s) for s in SOURCES)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<b:Sources SelectedStyle="\\IEEE.XSL" StyleName="IEEE" '
        'xmlns:b="%s" xmlns="%s">' % (NS, NS)
        + body + "</b:Sources>"
    )
    OUT.write_text(xml, encoding="utf-8", newline="\n")
    print("Da tao", OUT.name, "-", len(SOURCES), "nguon")


if __name__ == "__main__":
    main()
