# -*- coding: utf-8 -*-
"""Rà soát mọi con số trong bài, đối chiếu với file kết quả.

Bài đã qua nhiều vòng sửa, số liệu được chèn tay nhiều lần, nên phải có một
bước đối chiếu máy làm trước khi nộp. Script đọc file .docx, rút mọi cụm
"<số>%" và "<số> s", rồi tra xem con số đó có khớp với dữ liệu trong results/
hay không.

Không sửa gì, chỉ báo cáo. Cái nào không tra được thì liệt kê riêng để đọc tay.

    python src/ra_soat_so_lieu.py
"""
import json
import math
import re
import sys
from pathlib import Path

from docx import Document

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
BAI = ROOT / "Tai lieu" / "HEALTHINFO-IV_TruongQuangDai_Rule-Constrained-LLM-Blood-Test_EN_2026-Final.docx"

LOI = ["false_reassurance", "status_mismatch", "contradictory_wording",
       "forbidden_term", "hallucinated_analyte", "missing_analyte"]


def doc(ten):
    f = ROOT / "results" / f"{ten}.jsonl"
    return [json.loads(l) for l in open(f, encoding="utf-8")] if f.exists() else []


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    t = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, t - h), 100 * min(1.0, t + h))


def dung_kho(ds):
    """Mọi tỷ lệ và thời gian rút được từ một file kết quả."""
    n = len(ds)
    if not n:
        return {}
    ra = {}
    qua = sum(1 for x in ds if x["validation"]["passed"])
    tu = sum(1 for x in ds if x["validation"]["passed"] and not x.get("used_fallback"))
    ra["pass"] = 100.0 * qua / n
    ra["model_text"] = 100.0 * tu / n
    ra["fallback"] = 100.0 * sum(1 for x in ds if x.get("used_fallback")) / n
    for t in LOI + ["code_format", "unparseable"]:
        k = sum(1 for x in ds if any(v.get("type") == t for v in x["validation"].get("violations", [])))
        ra[t] = 100.0 * k / n
        ra[t + "_ktc"] = wilson(k, n)
    ra["pass_ktc"] = wilson(qua, n)
    ra["model_text_ktc"] = wilson(tu, n)
    ra["giay"] = sum(x.get("seconds", 0) for x in ds) / n
    ra["lan_sinh"] = sum(x.get("attempts", 1) for x in ds) / n
    return ra


def main():
    kho = {}
    for ten in ("baseline", "chi_mau", "chi_nhan", "chi_rang_buoc", "chi_kiem_chung",
                "constrained", "full"):
        kho[f"{ten}_3b"] = dung_kho(doc(f"{ten}_qwen2.5-3b"))
    for ten in ("baseline", "constrained", "full"):
        kho[f"{ten}_7b"] = dung_kho(doc(f"{ten}_qwen2.5-7b"))

    # mọi giá trị hợp lệ, làm tròn một chữ số, để tra ngược
    hop_le = {}
    for nguon, d in kho.items():
        for khoa, v in d.items():
            if khoa.endswith("_ktc"):
                for x in v:
                    hop_le.setdefault(round(x, 1), []).append(f"{nguon}.{khoa}")
            else:
                hop_le.setdefault(round(v, 1), []).append(f"{nguon}.{khoa}")

    # số từ các file phân tích phụ
    for f, nhan in (("thu_nghiem_don_vi.json", "don_vi"),
                    ("baseline_cham_lai.json", "cham_lai"),
                    ("thong_ke_tin_cay.json", "tin_cay"),
                    ("phan_tich_7b_va_lap.json", "7b_lap")):
        p = ROOT / "results" / f
        if not p.exists():
            continue

        def di(o, duong=nhan):
            if isinstance(o, dict):
                for k, v in o.items():
                    di(v, f"{duong}.{k}")
            elif isinstance(o, list):
                for v in o:
                    di(v, duong)
            elif isinstance(o, (int, float)):
                hop_le.setdefault(round(float(o), 1), []).append(duong)
                if 0 < o <= 1:
                    hop_le.setdefault(round(100 * float(o), 1), []).append(duong + "*100")
        di(json.load(open(p, encoding="utf-8")))

    d = Document(BAI)
    than = [p.text for p in d.paragraphs if p.style.name not in ("referenceitem",)]
    van = "\n".join(than)

    print("=" * 88)
    print("RÀ SOÁT SỐ LIỆU TRONG BÀI")
    print("=" * 88)

    pct = sorted(set(re.findall(r"(\d+\.\d)%", van)))
    khop, le = [], []
    for s in pct:
        v = float(s)
        (khop if round(v, 1) in hop_le else le).append(s)
    print(f"\nTỷ lệ % xuất hiện trong bài: {len(pct)} giá trị khác nhau")
    print(f"  khớp với dữ liệu: {len(khop)}")
    print(f"  KHÔNG tra được  : {len(le)}")
    if le:
        for s in le:
            dong = [t.strip()[:110] for t in than if s + "%" in t]
            print(f"\n  >> {s}%  — không có trong results/")
            for t in dong[:2]:
                print(f"     {t}")

    giay = sorted(set(re.findall(r"(\d+\.\d) s\b", van)))
    le_g = [s for s in giay if round(float(s), 1) not in hop_le]
    print(f"\nGiá trị giây trong bài: {len(giay)}, không tra được: {len(le_g)} {le_g or ''}")

    # kiểm tra bảng
    print("\n" + "=" * 88)
    print("BẢNG")
    print("=" * 88)
    for i, b in enumerate(d.tables, 1):
        print(f"  Bảng {i}: {len(b.rows)} hàng x {len(b.columns)} cột")

    # đối chiếu từng ô Bảng 3 với dữ liệu
    b3 = d.tables[-1]
    nguon = {"Baseline": "baseline_3b", "Template only": "chi_mau_3b",
             "Labels only": "chi_nhan_3b", "Constraints only": "chi_rang_buoc_3b",
             "Validator only": "chi_kiem_chung_3b", "Constrained": "constrained_3b",
             "Full": "full_3b"}
    cot = ["pass", "model_text", "status_mismatch", "false_reassurance",
           "forbidden_term", "giay"]
    print("\nĐối chiếu từng ô Bảng 3:")
    sai = 0
    for r in b3.rows[1:]:
        ten = r.cells[0].text.strip()
        if ten not in nguon:
            print(f"  {ten:18} (suy ra từ nhật ký, không có file riêng — đọc tay)")
            continue
        k = kho[nguon[ten]]
        for j, khoa in enumerate(cot, 1):
            o = r.cells[j].text.strip()
            try:
                v = float(o)
            except ValueError:
                continue
            that = k[khoa]
            if abs(v - that) > 0.05:
                print(f"  LỆCH {ten}/{khoa}: bài ghi {v}, dữ liệu {that:.1f}")
                sai += 1
    print(f"  số ô lệch: {sai}")

    # trích dẫn
    print("\n" + "=" * 88)
    print("TRÍCH DẪN")
    print("=" * 88)
    tl = [p for p in d.paragraphs if p.style.name == "referenceitem"]
    so = set()
    for t in than:
        for m in re.findall(r"\[([0-9]+(?:\s*[,–-]\s*[0-9]+)*)\]", t):
            for phan in re.split(r"\s*,\s*", m):
                r2 = re.match(r"^(\d+)\s*[–-]\s*(\d+)$", phan)
                if r2:
                    so.update(range(int(r2.group(1)), int(r2.group(2)) + 1))
                elif phan.strip().isdigit():
                    so.add(int(phan.strip()))
    print(f"  tài liệu trong danh mục: {len(tl)}")
    print(f"  số được trích: {len(so)}, lớn nhất [{max(so)}]")
    chua = sorted(set(range(1, len(tl) + 1)) - so)
    print(f"  chưa trích lần nào: {chua or 'không'}")
    print(f"  trích vượt danh mục: {sorted(s for s in so if s > len(tl)) or 'không'}")


if __name__ == "__main__":
    main()
