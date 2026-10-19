# -*- coding: utf-8 -*-
"""Đóng gói file nộp kèm cho bản camera-ready.

Bản nộp lần đầu chỉ có ba cấu hình và năm file mã. Bài sửa vòng 2 dẫn chiếu tới
Phụ lục A, B, C và tới bảy cấu hình, nên gói cũ không còn khớp với bài. Script này
dựng lại gói từ cây mã hiện tại và kiểm tra rằng mọi thứ bài có nhắc tới đều nằm trong gói.

    python src/dong_goi_nop_kem.py
"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
RA = ROOT / "Tai lieu" / "HEALTHINFO-IV_Supplementary_Code-Data_camera-ready.zip"
GOC = "Rule-Constrained-LLM-Blood-Test"

# Bảy cấu hình trong Bảng 3 của bài; thiếu file nào thì dừng, không nộp gói hụt.
CAU_HINH = ["baseline", "chi_mau", "chi_nhan", "chi_rang_buoc",
            "chi_kiem_chung", "constrained", "full"]

FILE = [
    "README.md",
    "requirements.txt",
    # dữ liệu và nguồn gốc của luật
    "data/reference_ranges.csv",
    "data/nguon_khoang_tham_chieu.csv",
    "data/tu_cam_nguon.csv",
    "data/synthetic_panels.json",
    # mã
    "src/classifier.py",
    "src/generate_data.py",
    "src/prompt_builder.py",
    "src/run_experiment.py",
    "src/analyze.py",
    "src/chay_chi_mau.py",
    "src/cham_lai_bo_loi_dinh_dang.py",
    "src/thu_nghiem_don_vi.py",
    "src/phan_tich_ablation.py",
    "src/thong_ke_tin_cay.py",
    "src/vi_du_loi.py",
    "src/dung_phu_luc.py",
    # test giữ tài liệu khớp với mã
    "tests/test_classifier.py",
    "tests/test_nguon_khoang_tham_chieu.py",
    "tests/test_tu_cam_nguon.py",
    # kết quả phân tích
    "results/summary.csv",
    "results/bang_ablation.json",
    "results/baseline_cham_lai.json",
    "results/thu_nghiem_don_vi.json",
    "results/thong_ke_tin_cay.json",
    "results/vi_du_loi.json",
    # phụ lục bài dẫn chiếu
    "docs/phu_luc_bo_sung.md",
] + [f"results/{c}_qwen2.5-3b.jsonl" for c in CAU_HINH]


def main():
    thieu = [f for f in FILE if not (ROOT / f).exists()]
    if thieu:
        print("DỪNG, thiếu file:")
        for f in thieu:
            print("  ", f)
        return 1

    RA.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(RA, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILE:
            z.write(ROOT / f, f"{GOC}/{f}")

    tong = sum((ROOT / f).stat().st_size for f in FILE)
    print(f"{len(FILE)} file, {tong/1e6:.1f} MB thô, gói {RA.stat().st_size/1e6:.1f} MB")
    print("Đã ghi:", RA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
