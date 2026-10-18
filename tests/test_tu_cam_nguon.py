# -*- coding: utf-8 -*-
"""Danh mục từ cấm trong code phải khớp đúng với bảng căn cứ trong data/tu_cam_nguon.csv.

Phản biện hỏi: các từ cấm dựa vào đâu. Bảng CSV ghi từng mẫu kèm nhóm hành vi bị cấm
và căn cứ pháp lý hoặc chuyên môn. Test này giữ cho hai bên không lệch nhau: thêm một
từ cấm vào code mà quên ghi căn cứ thì test đỏ.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prompt_builder import FORBIDDEN_PATTERNS  # noqa: E402

CSV = ROOT / "data" / "tu_cam_nguon.csv"
NHOM_HOP_LE = {"ten_benh", "quy_nguyen_nhan", "thuoc_dieu_tri", "lieu_luong"}


def doc_bang():
    with open(CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_moi_mau_trong_code_deu_co_can_cu():
    trong_bang = {h["mau"] for h in doc_bang()}
    thieu = [p for p in FORBIDDEN_PATTERNS if p not in trong_bang]
    assert not thieu, f"Các mẫu trong code chưa ghi căn cứ trong {CSV.name}: {thieu}"


def test_khong_co_dong_thua_trong_bang():
    thua = [h["mau"] for h in doc_bang() if h["mau"] not in FORBIDDEN_PATTERNS]
    assert not thua, f"Bảng căn cứ còn mẫu không có trong code: {thua}"


def test_moi_dong_deu_ghi_du_nhom_hanh_vi_va_can_cu():
    for h in doc_bang():
        assert h["nhom"] in NHOM_HOP_LE, f"Nhóm lạ: {h['nhom']}"
        assert h["hanh_vi_bi_cam"].strip(), f"Thiếu hành vi bị cấm: {h['mau']}"
        assert h["can_cu"].strip(), f"Thiếu căn cứ: {h['mau']}"


def test_bon_nhom_deu_co_it_nhat_mot_mau():
    co = {h["nhom"] for h in doc_bang()}
    assert co == NHOM_HOP_LE, f"Thiếu nhóm: {NHOM_HOP_LE - co}"
