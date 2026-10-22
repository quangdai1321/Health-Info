# -*- coding: utf-8 -*-
"""Chuyển hai file Markdown nộp kèm sang HTML để Word xuất ra PDF và .docx.

Ban tổ chức nhận file PDF hoặc Word, không nhận Markdown. Máy này không có
pandoc nên tự dựng: Markdown -> HTML -> Word COM -> PDF/.docx.

Bộ chuyển chỉ xử lý đúng những thứ hai file đang dùng: tiêu đề, đoạn, đậm,
nghiêng, mã nội dòng, khối mã, bảng, trích dẫn, danh sách, đường kẻ. Không
cố làm một bộ Markdown đầy đủ.

    python src/xuat_tai_lieu.py
"""
import html
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

CSS = """
@page { margin: 2cm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt;
       line-height: 1.3; margin: 0; width: 100%; color: #111; }
h1 { font-size: 17pt; border-bottom: 2px solid #333; padding-bottom: 4pt;
     margin: 0 0 8pt 0; }
h2 { font-size: 13.5pt; margin: 16pt 0 6pt 0; border-bottom: 1px solid #bbb;
     padding-bottom: 2pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt 0; }
h4 { font-size: 10.5pt; margin: 9pt 0 3pt 0; }
p { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 6pt 0; padding-left: 18pt; }
li { margin: 0 0 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9pt; }
th, td { border: 1px solid #999; padding: 2pt 5pt; text-align: left;
         vertical-align: top; line-height: 1.2; }
th { background: #eee; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 9pt; }
pre { font-family: Consolas, 'Courier New', monospace; font-size: 8pt;
      background: #f6f6f6; border: 1px solid #ddd; padding: 5pt;
      white-space: pre-wrap; line-height: 1.15; margin: 5pt 0; }
blockquote { border-left: 3px solid #888; margin: 6pt 0 6pt 0; padding-left: 10pt;
             color: #333; font-style: italic; }
hr { border: none; border-top: 1px solid #bbb; margin: 12pt 0; }
"""


def noi_dong(t):
    """Đậm, nghiêng, mã nội dòng, liên kết. Mã xử lý trước để khỏi bị diễn giải."""
    giu = []

    def cat(m):
        giu.append(m.group(1))
        return f"\x00{len(giu)-1}\x00"

    t = re.sub(r"`([^`]+)`", cat, t)
    t = html.escape(t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    for i, m in enumerate(giu):
        t = t.replace(f"\x00{i}\x00", f"<code>{html.escape(m)}</code>")
    return t


def chuyen(md):
    ra, i, dong = [], 0, md.split("\n")
    trong_ds = None
    while i < len(dong):
        d = dong[i]

        if d.startswith("```"):                      # khối mã
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            i += 1
            body = []
            while i < len(dong) and not dong[i].startswith("```"):
                body.append(dong[i]); i += 1
            i += 1
            ra.append("<pre>" + html.escape("\n".join(body)) + "</pre>")
            continue

        if re.match(r"^\s*\|.*\|\s*$", d) and i + 1 < len(dong) \
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", dong[i + 1]):
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            def o(hang):
                return [c.strip() for c in hang.strip().strip("|").split("|")]
            dau = o(d); i += 2
            ra.append("<table><tr>" + "".join(f"<th>{noi_dong(c)}</th>" for c in dau) + "</tr>")
            while i < len(dong) and re.match(r"^\s*\|.*\|\s*$", dong[i]):
                ra.append("<tr>" + "".join(f"<td>{noi_dong(c)}</td>" for c in o(dong[i])) + "</tr>")
                i += 1
            ra.append("</table>")
            continue

        m = re.match(r"^(#{1,5})\s+(.*)$", d)
        if m:
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            n = len(m.group(1))
            ra.append(f"<h{n}>{noi_dong(m.group(2))}</h{n}>")
            i += 1
            continue

        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", d):
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            ra.append("<hr>"); i += 1
            continue

        if d.startswith(">"):
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            body = []
            while i < len(dong) and dong[i].startswith(">"):
                body.append(dong[i].lstrip(">").strip()); i += 1
            ra.append("<blockquote>" + noi_dong(" ".join(body)) + "</blockquote>")
            continue

        m = re.match(r"^\s*([-*])\s+(.*)$", d)
        if m:
            if trong_ds != "ul":
                if trong_ds:
                    ra.append(f"</{trong_ds}>")
                ra.append("<ul>"); trong_ds = "ul"
            ra.append(f"<li>{noi_dong(m.group(2))}</li>"); i += 1
            continue

        m = re.match(r"^\s*\d+\.\s+(.*)$", d)
        if m:
            if trong_ds != "ol":
                if trong_ds:
                    ra.append(f"</{trong_ds}>")
                ra.append("<ol>"); trong_ds = "ol"
            ra.append(f"<li>{noi_dong(m.group(1))}</li>"); i += 1
            continue

        if not d.strip():
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            i += 1
            continue

        # đoạn thường: gom các dòng liền nhau
        body = []
        while i < len(dong) and dong[i].strip() and not re.match(
                r"^(#{1,5}\s|```|>|\s*[-*]\s|\s*\d+\.\s|\s*\|)", dong[i]):
            body.append(dong[i].strip()); i += 1
        if body:
            if trong_ds:
                ra.append(f"</{trong_ds}>"); trong_ds = None
            ra.append("<p>" + noi_dong(" ".join(body)) + "</p>")
        else:
            i += 1
    if trong_ds:
        ra.append(f"</{trong_ds}>")
    return "\n".join(ra)


def main():
    viec = [
        ("docs/phan_hoi_phan_bien.md", "HI26-0013_Response-to-Reviewers"),
        ("docs/phu_luc_bo_sung.md", "HI26-0013_Supplementary-Appendices"),
    ]
    ra_dir = ROOT / "Tai lieu"
    tam = ROOT / "results" / "_html_tam"
    tam.mkdir(exist_ok=True)

    duong = []
    for nguon, ten in viec:
        md = (ROOT / nguon).read_text(encoding="utf-8")
        h = (f"<!doctype html><html><head><meta charset='utf-8'>"
             f"<title>{ten}</title><style>{CSS}</style></head><body>"
             f"{chuyen(md)}</body></html>")
        f = tam / f"{ten}.html"
        f.write_text(h, encoding="utf-8")
        duong.append((f, ra_dir / f"{ten}.pdf", ra_dir / f"{ten}.docx"))
        print(f"  {nguon} -> {f.name} ({len(h)} ký tự)")

    print("\nMở bằng Word để xuất PDF và .docx:")
    for h, pdf, docx in duong:
        print(f"  {h}")
        print(f"    -> {pdf.name}")
        print(f"    -> {docx.name}")


if __name__ == "__main__":
    main()
