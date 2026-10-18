# -*- coding: utf-8 -*-
"""Khoảng tin cậy, kiểm định ghép cặp, phân vị thời gian chạy.

Phản biện 1, ý 6: mọi tỷ lệ trong bài đều từ một lần chạy trên 150 phiếu, không có
khoảng tin cậy và không có kiểm định. Vì cùng 150 phiếu đó được dùng cho mọi cấu hình,
kiểm định ghép cặp (McNemar) đúng hơn là so hai tỷ lệ độc lập.

Phản biện 1, ý 9: chỉ có thời gian trung bình, không đủ để bàn về triển khai. Thêm
p50/p95/p99, độ lệch chuẩn, và phân bố số lần sinh lại.

Script này không gọi mô hình, chỉ đọc lại các file kết quả đã có.

Thêm cấu hình "full không sinh lại", suy ra được từ nhật ký của cấu hình full: phiếu nào
đạt ngay lần đầu (attempts == 1) thì bản không-sinh-lại cũng đạt bằng văn của mô hình;
phiếu nào phải sinh lại thì bản không-sinh-lại rơi thẳng về mẫu cố định.
"""
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen2.5-3b"

CAU_HINH = ["baseline", "chi_mau", "chi_nhan", "chi_rang_buoc",
            "chi_kiem_chung", "constrained", "full"]
TEN = {"baseline": "Hỏi thẳng", "chi_mau": "Chỉ mẫu cố định", "chi_nhan": "Chỉ nhãn",
       "chi_rang_buoc": "Chỉ ràng buộc", "chi_kiem_chung": "Chỉ kiểm chứng",
       "constrained": "Nhãn + ràng buộc", "full": "Đủ bốn tầng",
       "full_khong_sinh_lai": "Đủ bốn tầng, không sinh lại"}
LOI = ["false_reassurance", "status_mismatch", "contradictory_wording",
       "forbidden_term", "hallucinated_analyte", "missing_analyte"]


def doc(ten):
    f = ROOT / "results" / f"{ten}_{MODEL}.jsonl"
    return [json.loads(l) for l in open(f, encoding="utf-8")] if f.exists() else []


def wilson(k, n, z=1.96):
    """Khoảng tin cậy Wilson. Dùng thay vì Wald vì nhiều tỷ lệ ở đây là 0% hoặc 100%,
    chỗ mà Wald cho khoảng rộng bằng 0 — vô nghĩa."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / d
    nua = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, tam - nua), 100 * min(1.0, tam + nua))


def mcnemar(a, b):
    """McNemar một phía đôi, hiệu chỉnh liên tục. a, b là hai list bool cùng độ dài,
    ghép cặp theo phiếu. Trả về (b01, b10, chi2, p)."""
    b01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    b10 = sum(1 for x, y in zip(a, b) if x and (not y))
    n = b01 + b10
    if n == 0:
        return b01, b10, 0.0, 1.0
    chi2 = (abs(b01 - b10) - 1) ** 2 / n if n > 0 else 0.0
    chi2 = max(chi2, 0.0)
    # p từ chi-bình phương 1 bậc tự do, không cần scipy
    p = math.erfc(math.sqrt(chi2 / 2)) if chi2 > 0 else 1.0
    return b01, b10, chi2, p


def phan_vi(ds, q):
    if not ds:
        return 0.0
    s = sorted(ds)
    i = (len(s) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (i - lo)


def main():
    du_lieu = {c: doc(c) for c in CAU_HINH}
    du_lieu = {c: d for c, d in du_lieu.items() if d}

    # cấu hình suy ra: full nhưng không sinh lại
    f = du_lieu.get("full")
    if f:
        suy = []
        for x in f:
            dat_ngay = x["attempts"] == 1 and not x.get("used_fallback")
            suy.append({"panel_id": x["panel_id"],
                        "validation": {"passed": True, "violations": []},
                        "used_fallback": not dat_ngay,
                        "attempts": 1,
                        "seconds": x["seconds"] if dat_ngay else x["seconds"] / max(x["attempts"], 1)})
        du_lieu["full_khong_sinh_lai"] = suy

    thu_tu = ["baseline", "chi_mau", "chi_nhan", "chi_rang_buoc", "chi_kiem_chung",
              "constrained", "full_khong_sinh_lai", "full"]
    thu_tu = [c for c in thu_tu if c in du_lieu]

    print("=" * 96)
    print("TỶ LỆ QUA KIỂM CHỨNG VÀ TỶ LỆ VĂN DO MÔ HÌNH VIẾT, kèm KTC Wilson 95%")
    print("=" * 96)
    print("%-28s %5s %22s %22s" % ("cấu hình", "n", "qua kiểm chứng", "mô hình tự viết"))
    print("-" * 96)
    bang = {}
    for c in thu_tu:
        d = du_lieu[c]
        n = len(d)
        k = sum(1 for x in d if x["validation"]["passed"])
        m = sum(1 for x in d if x["validation"]["passed"] and not x.get("used_fallback"))
        lo, hi = wilson(k, n)
        lo2, hi2 = wilson(m, n)
        bang[c] = {"n": n, "qua": k, "tu_viet": m,
                   "qua_pct": 100.0 * k / n, "qua_ktc": [lo, hi],
                   "tu_viet_pct": 100.0 * m / n, "tu_viet_ktc": [lo2, hi2]}
        print("%-28s %5d %8.1f%% [%5.1f–%5.1f] %8.1f%% [%5.1f–%5.1f]"
              % (TEN[c], n, 100.0 * k / n, lo, hi, 100.0 * m / n, lo2, hi2))

    print()
    print("KIỂM ĐỊNH GHÉP CẶP McNEMAR trên tỷ lệ qua kiểm chứng (cùng 150 phiếu)")
    print("-" * 96)
    cap = [("baseline", "chi_nhan"), ("baseline", "chi_rang_buoc"),
           ("chi_nhan", "constrained"), ("constrained", "full"),
           ("chi_mau", "full"), ("chi_kiem_chung", "full")]
    ghep = {}
    for a, b in cap:
        if a not in du_lieu or b not in du_lieu:
            continue
        da = {x["panel_id"]: x["validation"]["passed"] for x in du_lieu[a]}
        db = {x["panel_id"]: x["validation"]["passed"] for x in du_lieu[b]}
        chung = sorted(set(da) & set(db))
        va = [da[i] for i in chung]
        vb = [db[i] for i in chung]
        b01, b10, chi2, p = mcnemar(va, vb)
        ghep[f"{a}|{b}"] = {"n": len(chung), "b01": b01, "b10": b10, "chi2": chi2, "p": p}
        pt = "< 0.001" if p < 0.001 else f"= {p:.3f}"
        print("%-18s vs %-18s n=%d  chỉ B đạt %3d, chỉ A đạt %3d, chi2=%7.2f, p %s"
              % (TEN[a], TEN[b], len(chung), b01, b10, chi2, pt))

    print()
    print("THỜI GIAN MỘT PHIẾU (giây) và SỐ LẦN SINH")
    print("-" * 96)
    print("%-28s %8s %8s %8s %8s %8s %10s" % ("cấu hình", "trung bình", "đlc", "p50", "p95", "p99", "lần sinh tb"))
    for c in thu_tu:
        d = du_lieu[c]
        gs = [x.get("seconds", 0.0) for x in d]
        tb = sum(gs) / len(gs)
        dlc = math.sqrt(sum((g - tb) ** 2 for g in gs) / len(gs))
        ls = sum(x.get("attempts", 1) for x in d) / len(d)
        bang[c].update({"giay_tb": tb, "giay_dlc": dlc, "p50": phan_vi(gs, .50),
                        "p95": phan_vi(gs, .95), "p99": phan_vi(gs, .99), "lan_sinh": ls})
        print("%-28s %8.1f %8.1f %8.1f %8.1f %8.1f %10.2f"
              % (TEN[c], tb, dlc, phan_vi(gs, .50), phan_vi(gs, .95), phan_vi(gs, .99), ls))

    # vì sao phải sinh lại: chấm lại bản bị loại được lưu trong last_rejected
    ly_do = {}
    if f:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from classifier import RuleClassifier            # noqa: E402
        from prompt_builder import validate as kiem       # noqa: E402
        from run_experiment import to_classifier_input    # noqa: E402

        panels = {x["panel_id"]: x for x in
                  json.load(open(ROOT / "data" / "synthetic_panels.json", encoding="utf-8"))}
        clf = RuleClassifier()
        so_phieu = 0
        for x in f:
            lr = x.get("last_rejected")
            if not lr:
                continue
            so_phieu += 1
            cls = clf.classify_panel(to_classifier_input(panels[x["panel_id"]]["results"]))
            # đếm theo phiếu, không theo số lần vi phạm: một phiếu sai ba chỉ số
            # vẫn chỉ là một phiếu bị loại vì lý do đó
            for t in {v.get("type") for v in kiem(lr, cls).get("violations", [])}:
                ly_do[t] = ly_do.get(t, 0) + 1

        print()
        print("LÝ DO BỊ LOẠI — chấm lại bản cuối cùng bị tầng 4 từ chối, %d phiếu" % so_phieu)
        print("-" * 96)
        for k, v in sorted(ly_do.items(), key=lambda t: -t[1]):
            print("  %-24s %3d phiếu  (%4.1f%% số phiếu rơi về mẫu)"
                  % (k, v, 100.0 * v / so_phieu))

    ra = ROOT / "results" / "thong_ke_tin_cay.json"
    json.dump({"bang": bang, "mcnemar": ghep, "ly_do_bi_loai": ly_do}, open(ra, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nĐã ghi:", ra)


if __name__ == "__main__":
    main()
