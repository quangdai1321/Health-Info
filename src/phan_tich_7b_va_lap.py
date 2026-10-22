# -*- coding: utf-8 -*-
"""Phân tích hai mẻ chạy bổ sung: mô hình 7B, và năm lần chạy lặp.

Phản biện 1 ý 4 (mục 5) và Phản biện 2 ý R2.4: mới thử một mô hình 3B.
Phản biện 1 ý 6: mỗi cấu hình chỉ chạy một lần nên không biết biến thiên giải mã.

Script không gọi mô hình, chỉ đọc lại results/.
"""
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
LOI = [("false_reassurance", "Trấn an sai"), ("status_mismatch", "Sai chiều"),
       ("contradictory_wording", "Mâu thuẫn"), ("forbidden_term", "Từ cấm"),
       ("hallucinated_analyte", "Bịa chỉ số"), ("missing_analyte", "Bỏ sót")]


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


def mcnemar(a, b):
    b01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    b10 = sum(1 for x, y in zip(a, b) if x and (not y))
    n = b01 + b10
    if not n:
        return b01, b10, 1.0
    chi2 = max((abs(b01 - b10) - 1) ** 2 / n, 0.0)
    return b01, b10, (math.erfc(math.sqrt(chi2 / 2)) if chi2 > 0 else 1.0)


def ty_le(ds, t):
    return sum(1 for x in ds if any(v.get("type") == t for v in x["validation"].get("violations", [])))


def phan_so(ds):
    n = len(ds)
    qua = sum(1 for x in ds if x["validation"]["passed"])
    tu_viet = sum(1 for x in ds if x["validation"]["passed"] and not x.get("used_fallback"))
    return n, qua, tu_viet


def khoi_7b(ra):
    print("=" * 94)
    print("MÔ HÌNH 7B SO VỚI 3B — cùng 150 phiếu, cùng mã chấm")
    print("=" * 94)
    bang = {}
    for cau_hinh in ("baseline", "full"):
        a, b = doc(f"{cau_hinh}_qwen2.5-3b"), doc(f"{cau_hinh}_qwen2.5-7b")
        if not (a and b):
            continue
        print(f"\n### {cau_hinh}")
        print("%-20s %22s %22s" % ("chỉ số", "qwen2.5:3b", "qwen2.5:7b"))
        print("-" * 94)
        hang = {}
        for ten, (na, ka, ta) in (("3b", phan_so(a)), ("7b", phan_so(b))):
            hang[ten] = {"n": na, "qua": ka, "tu_viet": ta}
        for nhan, khoa in (("Qua kiểm chứng", "qua"), ("Mô hình tự viết", "tu_viet")):
            o = []
            for ten, ds in (("3b", a), ("7b", b)):
                k = hang[ten][khoa]
                n = hang[ten]["n"]
                lo, hi = wilson(k, n)
                o.append("%6.1f%% [%4.1f–%4.1f]" % (100 * k / n, lo, hi))
            print("%-20s %22s %22s" % (nhan, o[0], o[1]))
        for khoa, nhan in LOI:
            o = []
            for ds in (a, b):
                k = ty_le(ds, khoa)
                lo, hi = wilson(k, len(ds))
                o.append("%6.1f%% [%4.1f–%4.1f]" % (100 * k / len(ds), lo, hi))
            print("%-20s %22s %22s" % (nhan, o[0], o[1]))
            hang.setdefault("loi", {})[khoa] = (100 * ty_le(a, khoa) / len(a),
                                                100 * ty_le(b, khoa) / len(b))
        ga = sum(x["seconds"] for x in a) / len(a)
        gb = sum(x["seconds"] for x in b) / len(b)
        print("%-20s %21.1fs %21.1fs" % ("Giây mỗi phiếu", ga, gb))
        hang["giay"] = (ga, gb)
        la = sum(x.get("attempts", 1) for x in a) / len(a)
        lb = sum(x.get("attempts", 1) for x in b) / len(b)
        print("%-20s %22.2f %22.2f" % ("Lần sinh mỗi phiếu", la, lb))
        hang["lan_sinh"] = (la, lb)

        da = {x["panel_id"]: x["validation"]["passed"] for x in a}
        db = {x["panel_id"]: x["validation"]["passed"] for x in b}
        chung = sorted(set(da) & set(db))
        b01, b10, p = mcnemar([da[i] for i in chung], [db[i] for i in chung])
        pt = "< 0.001" if p < 0.001 else "= %.3f" % p
        print("McNemar ghép cặp trên tỷ lệ qua kiểm chứng: chỉ 7B đạt %d, chỉ 3B đạt %d, p %s"
              % (b01, b10, pt))
        hang["mcnemar"] = {"b01": b01, "b10": b10, "p": p}
        bang[cau_hinh] = hang
    ra["so_sanh_7b"] = bang


def khoi_lap(ra):
    print()
    print("=" * 94)
    print("NĂM LẦN CHẠY LẶP — constrained, qwen2.5:3b, cùng 150 phiếu")
    print("=" * 94)
    lan = [doc("constrained_qwen2.5-3b")] + [doc(f"constrained_qwen2.5-3b_lan{i}") for i in (2, 3, 4, 5)]
    lan = [d for d in lan if len(d) == 150]
    print(f"Số lần chạy đủ 150 phiếu: {len(lan)}")
    if len(lan) < 2:
        return

    def tom(vals):
        tb = sum(vals) / len(vals)
        dlc = math.sqrt(sum((v - tb) ** 2 for v in vals) / (len(vals) - 1))
        return tb, dlc, min(vals), max(vals)

    print("\n%-20s %9s %7s %15s %s" % ("chỉ số", "trung bình", "đlc", "khoảng", "từng lần"))
    print("-" * 94)
    kq = {}
    qua = [100 * phan_so(d)[1] / 150 for d in lan]
    tb, dlc, lo, hi = tom(qua)
    kq["qua_kiem_chung"] = {"tung_lan": qua, "tb": tb, "dlc": dlc}
    print("%-20s %8.1f%% %6.1f %7.1f–%-6.1f %s" % ("Qua kiểm chứng", tb, dlc, lo, hi,
          " ".join("%.1f" % v for v in qua)))
    for khoa, nhan in LOI:
        vals = [100 * ty_le(d, khoa) / 150 for d in lan]
        tb, dlc, lo, hi = tom(vals)
        kq[khoa] = {"tung_lan": vals, "tb": tb, "dlc": dlc}
        print("%-20s %8.1f%% %6.1f %7.1f–%-6.1f %s" % (nhan, tb, dlc, lo, hi,
              " ".join("%.1f" % v for v in vals)))
    g = [sum(x["seconds"] for x in d) / 150 for d in lan]
    tb, dlc, lo, hi = tom(g)
    kq["giay"] = {"tung_lan": g, "tb": tb, "dlc": dlc}
    print("%-20s %8.1fs %6.1f %7.1f–%-6.1f %s" % ("Giây mỗi phiếu", tb, dlc, lo, hi,
          " ".join("%.1f" % v for v in g)))

    # phiếu nào đạt ở lần này mà trượt ở lần khác: đo mức dao động theo phiếu
    dat = {}
    for d in lan:
        for x in d:
            dat.setdefault(x["panel_id"], []).append(x["validation"]["passed"])
    luon = sum(1 for v in dat.values() if all(v))
    khong = sum(1 for v in dat.values() if not any(v))
    doi = len(dat) - luon - khong
    print(f"\nTheo phiếu qua {len(lan)} lần: luôn đạt {luon}, luôn trượt {khong}, "
          f"lúc đạt lúc trượt {doi} ({100*doi/len(dat):.1f}%)")
    kq["theo_phieu"] = {"luon_dat": luon, "luon_truot": khong, "dao_dong": doi, "so_lan": len(lan)}
    ra["chay_lap"] = kq


def main():
    ra = {}
    khoi_7b(ra)
    khoi_lap(ra)
    f = ROOT / "results" / "phan_tich_7b_va_lap.json"
    json.dump(ra, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nĐã ghi:", f)


if __name__ == "__main__":
    main()
