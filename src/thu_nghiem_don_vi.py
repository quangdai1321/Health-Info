# -*- coding: utf-8 -*-
"""Thí nghiệm định lượng về đơn vị đo (trả lời phản biện vòng 2).

Phản biện nêu: đóng góp về chuẩn hóa đơn vị không có số liệu nào trong phần Kết quả.

Thí nghiệm này không cần gọi mô hình. Nó so hai cách xếp mức trên đúng 150 phiếu
đã dùng trong bài:

  A. Có quy đổi đơn vị  — đúng như Tầng 1 đang làm.
  B. Không quy đổi      — đem thẳng con số trên phiếu so với khoảng tham chiếu,
                          đây là cách một hệ thống bỏ qua đơn vị sẽ làm.

Rồi đếm xem khác biệt gây ra bao nhiêu nhãn sai, và sai theo hướng nào.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from classifier import RuleClassifier  # noqa: E402

GOC = Path(__file__).resolve().parent.parent
MUC = {"binh_thuong": 0, "theo_doi": 1, "kham_som": 2}
TEN_MUC = {"binh_thuong": "Bình thường", "theo_doi": "Theo dõi", "kham_som": "Khám sớm"}


def xep_muc(a, gt):
    """Lặp lại đúng luật của Tầng 2 cho một giá trị đã ở đơn vị nào đó."""
    if a.low <= gt <= a.high:
        return "binh_thuong"
    lech = a.low - gt if gt < a.low else gt - a.high
    return "theo_doi" if lech <= a.severe_factor * (a.high - a.low) + 1e-9 else "kham_som"


def main():
    c = RuleClassifier()
    panels = json.load(open(GOC / "data/synthetic_panels.json", encoding="utf-8"))

    tong = khac_dv = sai_nhan = 0
    chuyen = Counter()
    phieu_doi = 0
    vi_du = []

    for p in panels:
        doi_trong_phieu = False
        for ten, payload in p["results"].items():
            v, u = (payload[0], payload[1]) if isinstance(payload, (list, tuple)) else (payload, None)
            ma = c.table.resolve(ten)
            if ma is None:
                continue
            a = c.table.analytes[ma]
            tong += 1
            he_so = a.unit_factors.get(str(u).strip().lower()) if u else None
            if he_so is None or he_so == 1:
                continue                       # không có đơn vị, hoặc đã là đơn vị chuẩn
            khac_dv += 1
            dung = xep_muc(a, v * he_so)       # A: có quy đổi
            tho = xep_muc(a, v)                # B: không quy đổi
            if dung == tho:
                continue
            sai_nhan += 1
            doi_trong_phieu = True
            chuyen[(dung, tho)] += 1
            if len(vi_du) < 6:
                vi_du.append((ma, v, u, a.low, a.high, a.canonical_unit, dung, tho))
        if doi_trong_phieu:
            phieu_doi += 1

    print("=" * 76)
    print("ẢNH HƯỞNG CỦA VIỆC KHÔNG QUY ĐỔI ĐƠN VỊ — 150 phiếu, %d chỉ số" % tong)
    print("=" * 76)
    print("Chỉ số ghi bằng đơn vị khác đơn vị chuẩn: %d (%.1f%% tổng số)" % (khac_dv, 100 * khac_dv / tong))
    print("Trong đó bị xếp sai mức nếu không quy đổi: %d (%.1f%% số chỉ số khác đơn vị)"
          % (sai_nhan, 100 * sai_nhan / khac_dv if khac_dv else 0))
    print("Số phiếu có ít nhất một chỉ số bị xếp sai: %d / %d (%.1f%%)"
          % (phieu_doi, len(panels), 100 * phieu_doi / len(panels)))
    print()
    print("Sai theo hướng nào:")
    print("%-26s %-26s %8s" % ("mức đúng", "mức khi bỏ quy đổi", "số lần"))
    nguy = bao_dong_gia = 0
    for (dung, tho), n in sorted(chuyen.items(), key=lambda x: -x[1]):
        ghi = ""
        if MUC[tho] < MUC[dung]:
            ghi = "  <- bỏ sót, nguy hiểm"
            nguy += n
        elif MUC[tho] > MUC[dung]:
            ghi = "  <- báo động giả"
            bao_dong_gia += n
        print("%-26s %-26s %8d%s" % (TEN_MUC[dung], TEN_MUC[tho], n, ghi))
    print()
    print("Tổng: %d lần báo động giả, %d lần bỏ sót mức nặng hơn." % (bao_dong_gia, nguy))
    print()
    print("Vài ví dụ cụ thể:")
    for ma, v, u, lo, hi, dv, dung, tho in vi_du:
        print("  %-10s phiếu ghi %g %-6s | khoảng %g–%g %-5s | đúng: %-12s | bỏ quy đổi: %s"
              % (ma, v, u, lo, hi, dv, TEN_MUC[dung], TEN_MUC[tho]))

    ket = {
        "tong_chi_so": tong, "khac_don_vi": khac_dv, "xep_sai_neu_khong_quy_doi": sai_nhan,
        "phieu_bi_anh_huong": phieu_doi, "tong_phieu": len(panels),
        "bao_dong_gia": bao_dong_gia, "bo_sot": nguy,
        "chuyen_muc": {f"{a}->{b}": n for (a, b), n in chuyen.items()},
    }
    out = GOC / "results/thu_nghiem_don_vi.json"
    json.dump(ket, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("Đã ghi:", out)


if __name__ == "__main__":
    main()
