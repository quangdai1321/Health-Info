# -*- coding: utf-8 -*-
"""Rút ví dụ thật cho bảng phân tích lỗi định tính.

Phản biện 1, ý 10: bảng tỷ lệ cho biết lỗi xảy ra bao nhiêu lần nhưng không cho thấy
lỗi trông như thế nào. Script này lấy ví dụ thật từ nhật ký, mỗi lớp lỗi một ví dụ,
kèm giá trị gốc, nhãn luật gán, câu mô hình viết, và lý do tầng 4 từ chối.

Không bịa ví dụ: mọi câu in ra đều nằm trong file kết quả.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen2.5-3b"

LOP = ["false_reassurance", "status_mismatch", "contradictory_wording",
       "forbidden_term", "hallucinated_analyte", "missing_analyte"]


def doc(ten):
    f = ROOT / "results" / f"{ten}_{MODEL}.jsonl"
    return [json.loads(l) for l in open(f, encoding="utf-8")] if f.exists() else []


def tim(ds, lop):
    """Phiếu đầu tiên mắc đúng lớp lỗi này, kèm vi phạm cụ thể."""
    for x in ds:
        for v in x["validation"].get("violations", []):
            if v.get("type") == lop:
                return x, v
    return None, None


def cau_cua(out, ma):
    if not isinstance(out, dict):
        return None
    for it in out.get("items", []):
        if isinstance(it, dict) and it.get("code") == ma:
            return it
    return None


def main():
    nguon = [("baseline", doc("baseline")), ("constrained", doc("constrained")),
             ("chi_rang_buoc", doc("chi_rang_buoc"))]
    ra = {}
    for lop in LOP:
        for ten, ds in nguon:
            x, v = tim(ds, lop)
            if not x:
                continue
            ma = v.get("code") or v.get("analyte")
            it = cau_cua(x.get("output"), ma) if ma else None
            ra[lop] = {
                "cau_hinh": ten, "panel_id": x["panel_id"], "nhan_phieu": x["rule_label"],
                "ma": ma, "vi_pham": v,
                "status_mo_hinh": (it or {}).get("status"),
                "cau_mo_hinh": (it or {}).get("explanation"),
                "ket": (x.get("output") or {}).get("closing") if isinstance(x.get("output"), dict) else None,
            }
            break

    for lop, d in ra.items():
        print("=" * 92)
        print(f"{lop}  —  {d['cau_hinh']}, {d['panel_id']}, nhãn phiếu: {d['nhan_phieu']}")
        print(f"  chỉ số: {d['ma']}   mô hình ghi status: {d['status_mo_hinh']}")
        print(f"  vi phạm tầng 4 ghi nhận: {json.dumps(d['vi_pham'], ensure_ascii=False)}")
        if d["cau_mo_hinh"]:
            print(f"  câu mô hình viết: “{d['cau_mo_hinh']}”")
        if d["ket"]:
            print(f"  câu kết: “{d['ket']}”")

    f = ROOT / "results" / "vi_du_loi.json"
    json.dump(ra, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nĐã ghi:", f)


if __name__ == "__main__":
    main()
