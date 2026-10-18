# -*- coding: utf-8 -*-
"""Bảng nguồn khoảng tham chiếu phải phủ đủ 22 chỉ số và khớp đúng số đang dùng.

Phản biện hỏi: dựa vào đâu để quyết định một chỉ số là bất thường. Câu trả lời gồm
hai phần tách bạch: khoảng tham chiếu lấy từ phiếu của phòng xét nghiệm, còn hệ số
phân mức nặng nhẹ là do nhóm tự đặt. Bảng này ghi cả hai, kèm tình trạng thẩm định.
Test giữ cho bảng không lệch khỏi file luật đang chạy.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classifier import RuleClassifier  # noqa: E402

BANG = ROOT / "data" / "nguon_khoang_tham_chieu.csv"


def doc_bang():
    with open(BANG, encoding="utf-8") as f:
        return {h["code"]: h for h in csv.DictReader(f)}


def test_phu_du_moi_chi_so():
    bang, luat = doc_bang(), RuleClassifier().table.analytes
    assert set(bang) == set(luat), (
        f"Lệch danh sách chỉ số: thiếu {set(luat) - set(bang)}, thừa {set(bang) - set(luat)}")


def test_so_trong_bang_khop_voi_luat_dang_chay():
    bang = doc_bang()
    for ma, a in RuleClassifier().table.analytes.items():
        h = bang[ma]
        assert float(h["thap"]) == a.low, f"{ma}: cận dưới lệch"
        assert float(h["cao"]) == a.high, f"{ma}: cận trên lệch"
        assert float(h["he_so_nang"]) == a.severe_factor, f"{ma}: hệ số nặng lệch"
        assert h["don_vi"] == a.canonical_unit, f"{ma}: đơn vị lệch"


def test_moi_dong_deu_ghi_nguon_va_tinh_trang():
    for ma, h in doc_bang().items():
        assert h["nguon_khoang"].strip(), f"{ma}: thiếu nguồn khoảng tham chiếu"
        assert h["tinh_trang_tham_dinh"].strip(), f"{ma}: thiếu tình trạng thẩm định"


def test_cac_chi_so_phu_thuoc_gioi_tinh_duoc_danh_dau():
    bang = doc_bang()
    for ma in ("HGB", "HCT", "RBC"):
        assert "giới tính" in bang[ma]["phu_thuoc"], (
            f"{ma} phụ thuộc giới tính theo y văn huyết học, phải được đánh dấu")
