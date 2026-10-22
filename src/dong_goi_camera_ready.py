# -*- coding: utf-8 -*-
"""Gom đúng những file cần nộp vào một thư mục, đặt tên sạch.

Tên file bản thảo cũ là "...TruongQuangDai..." nhưng thứ tự tác giả đã đổi,
Võ Hoàng Khang đứng trước, nên tên đó gây hiểu nhầm. Thư mục nộp dùng mã bài
HI26-0013 làm tiền tố cho mọi file.

Script dừng nếu thiếu file nào, và in lại kích thước để đối chiếu trước khi gửi.

    python src/dong_goi_camera_ready.py
"""
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TL = ROOT / "Tai lieu"
RA = TL / "camera-ready"

GOC = "HEALTHINFO-IV_TruongQuangDai_Rule-Constrained-LLM-Blood-Test_EN_2026-Final"

CHEP = [
    (TL / f"{GOC}.pdf", "HI26-0013_Camera-Ready_Paper.pdf"),
    (TL / f"{GOC}.docx", "HI26-0013_Camera-Ready_Paper.docx"),
    (TL / "HI26-0013_Response-to-Reviewers.pdf", "HI26-0013_Response-to-Reviewers.pdf"),
    (TL / "HI26-0013_Response-to-Reviewers.docx", "HI26-0013_Response-to-Reviewers.docx"),
    (TL / "HI26-0013_Supplementary-Appendices.pdf", "HI26-0013_Supplementary-Appendices.pdf"),
    (TL / "HI26-0013_Supplementary-Appendices.docx", "HI26-0013_Supplementary-Appendices.docx"),
    (TL / "HEALTHINFO-IV_Supplementary_Code-Data_camera-ready.zip",
     "HI26-0013_Supplementary-Code-and-Data.zip"),
]


def main():
    thieu = [str(a) for a, _ in CHEP if not a.exists()]
    if thieu:
        print("DỪNG, thiếu:")
        for f in thieu:
            print("  ", f)
        return 1

    RA.mkdir(exist_ok=True)
    # Dọn bản cũ để khỏi nộp nhầm, nhưng giữ lại thư nộp vì nó soạn tay.
    for cu in RA.iterdir():
        if cu.is_file() and cu.name != "HI26-0013_Submission-Email.md":
            cu.unlink()

    print(f"{RA}\n")
    tong = 0
    for a, ten in CHEP:
        shutil.copy2(a, RA / ten)
        kb = (RA / ten).stat().st_size / 1024
        tong += kb
        print(f"  {kb:8.0f} KB  {ten}")
    print(f"\n  {tong/1024:8.1f} MB  tổng {len(CHEP)} file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
