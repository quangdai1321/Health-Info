# -*- coding: utf-8 -*-
"""Dựng bảng so sánh sáu cấu hình, trả lời ý R2.3 của phản biện vòng 2.

Phản biện nêu: cấu hình "constrained" gộp ba thứ (nhãn từ luật, ràng buộc nội dung,
khuôn JSON) nên không tách được phần nào đóng góp bao nhiêu, và thiếu cấu hình chỉ
có kiểm chứng. Ba cấu hình tách phần được chạy trên đúng 150 phiếu và đúng mô hình đó.

Cấu hình nào chưa chạy xong thì vẫn in, kèm số phiếu đã có, để theo dõi giữa chừng.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen2.5-3b"

CAU_HINH = [
    ("baseline", "Hỏi thẳng, không có gì", "không", "không", "không"),
    ("chi_nhan", "Chỉ nhãn từ luật", "có", "không", "không"),
    ("chi_rang_buoc", "Chỉ ràng buộc nội dung", "không", "có", "không"),
    ("chi_kiem_chung", "Chỉ kiểm chứng tầng 4", "không", "không", "có"),
    ("constrained", "Nhãn + ràng buộc", "có", "có", "không"),
    ("full", "Đủ bốn tầng", "có", "có", "có"),
]
LOI = [("false_reassurance", "Trấn an sai"), ("status_mismatch", "Sai chiều"),
       ("contradictory_wording", "Mâu thuẫn"), ("forbidden_term", "Từ cấm"),
       ("hallucinated_analyte", "Bịa chỉ số"), ("missing_analyte", "Bỏ sót")]
HONG = [("code_format", "Sai mã"), ("unparseable", "Hỏng JSON"),
        ("malformed_structure", "Sai cấu trúc")]


def doc(ten):
    f = ROOT / "results" / f"{ten}_{MODEL}.jsonl"
    if not f.exists():
        return []
    return [json.loads(l) for l in open(f, encoding="utf-8")]


def do(ds):
    n = len(ds)
    if not n:
        return None
    co = lambda x, t: any(v.get("type") == t for v in x["validation"].get("violations", []))  # noqa: E731
    r = {"n": n,
         "an_toan": 100.0 * sum(1 for x in ds if x["validation"].get("passed")) / n,
         "giay": sum(x.get("seconds", 0) for x in ds) / n,
         "lan_sinh": sum(x.get("attempts", 1) for x in ds) / n,
         "ban_mau": 100.0 * sum(1 for x in ds if x.get("used_fallback")) / n}
    for k, _ in LOI + HONG:
        r[k] = 100.0 * sum(1 for x in ds if co(x, k)) / n
    r["mo_hinh_tu_viet"] = r["an_toan"] - r["ban_mau"]
    return r


def main():
    bang = {}
    for ten, *_ in CAU_HINH:
        kq = do(doc(ten))
        if kq:
            bang[ten] = kq

    print("=" * 108)
    print("SO SÁNH SÁU CẤU HÌNH — 150 phiếu tổng hợp, mô hình qwen2.5:3b")
    print("=" * 108)
    print("%-16s %-26s %5s %7s %7s %7s" % ("cấu hình", "gồm những gì", "n", "an toàn", "tự viết", "giây"))
    print("-" * 108)
    for ten, mo_ta, nhan, rb, kc in CAU_HINH:
        k = bang.get(ten)
        if not k:
            print("%-16s %-26s %5s  chưa chạy" % (ten, mo_ta, "-"))
            continue
        dang_chay = "" if k["n"] >= 150 else "  (đang chạy)"
        print("%-16s %-26s %5d %6.1f%% %6.1f%% %6.1fs%s"
              % (ten, mo_ta, k["n"], k["an_toan"], k["mo_hinh_tu_viet"], k["giay"], dang_chay))

    print()
    print("TỶ LỆ PHIẾU MẮC TỪNG LOẠI LỖI (%)")
    print("-" * 108)
    cot = [t for t, *_ in CAU_HINH if t in bang]
    print("%-22s" % "loại lỗi" + "".join("%16s" % t for t in cot))
    for k, nhan in LOI + HONG:
        print("%-22s" % nhan + "".join("%15.1f " % bang[t][k] for t in cot))

    print()
    print("ĐÓNG GÓP RIÊNG CỦA TỪNG THÀNH PHẦN, so với baseline")
    print("-" * 108)
    goc = bang.get("baseline")
    if goc:
        for ten, mo_ta, *_ in CAU_HINH[1:]:
            k = bang.get(ten)
            if not k:
                continue
            print("%-16s %-26s an toàn %+6.1f điểm | sai chiều %+6.1f điểm | trấn an sai %+6.1f điểm"
                  % (ten, mo_ta, k["an_toan"] - goc["an_toan"],
                     k["status_mismatch"] - goc["status_mismatch"],
                     k["false_reassurance"] - goc["false_reassurance"]))

    ra = ROOT / "results" / "bang_ablation.json"
    json.dump(bang, open(ra, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("Đã ghi:", ra)


if __name__ == "__main__":
    main()
