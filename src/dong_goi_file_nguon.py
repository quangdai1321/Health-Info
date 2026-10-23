# -*- coding: utf-8 -*-
"""Dựng file .zip cho ô "File nguồn" của form camera-ready.

Form chỉ có ba ô nộp: bài PDF, file nguồn (.docx hoặc .zip), và phản hồi phản biện.
Không có ô nào cho tài liệu bổ sung, trong khi bài dẫn chiếu tới Phụ lục A, B, C.
Ô file nguồn nhận .zip, nên gói này gồm cả bản Word lẫn phần bổ sung, kèm một
file README ở gốc nói rõ trong gói có gì để ban tổ chức không phải đoán.

    python src/dong_goi_file_nguon.py
"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CR = ROOT / "Tai lieu" / "camera-ready"
RA = CR / "HI26-0013_Source-and-Supplementary.zip"

DOC = """HI26-0013 — Source file and supplementary material
==================================================

Paper: A Rule-Constrained Large Language Model Pipeline for Rule-Consistent
       Explanation of Vietnamese Complete Blood Count Results

The camera-ready form has no upload field for supplementary material, and the
paper refers to Appendices A, B and C. They are included here together with the
editable source, so that nothing the paper cites is missing.

Contents
--------

  HI26-0013_Camera-Ready_Paper.docx
      Editable source of the submitted PDF. Word, HEALTHINFO IV template.

  HI26-0013_Supplementary-Appendices.pdf
      Appendix A  Benchmark distributions, reference intervals, severity
                  factors, unit conversions and the alias table.
      Appendix B  Full specification of the Layer 4 validator: algorithm,
                  pattern tables, masking rules, and a false-positive mode we
                  found and disclose.
      Appendix C  One worked example per error class, taken from the run logs.

  code-and-data/
      Source code, the generated benchmark, and the raw output of every run
      reported in the paper, one JSON object per panel. See its README.md for
      how to reproduce. All seven configurations on Qwen2.5-3B, three
      configurations on Qwen2.5-7B, and five repeated runs are included.

Contact: Vo Hoang Khang, vh.khang@hutech.edu.vn
"""


def main():
    nguon_zip = CR / "HI26-0013_Supplementary-Code-and-Data.zip"
    can = [CR / "HI26-0013_Camera-Ready_Paper.docx",
           CR / "HI26-0013_Supplementary-Appendices.pdf",
           nguon_zip]
    thieu = [str(f) for f in can if not f.exists()]
    if thieu:
        print("DỪNG, thiếu:")
        for f in thieu:
            print("  ", f)
        return 1

    with zipfile.ZipFile(RA, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", DOC)
        z.write(can[0], can[0].name)
        z.write(can[1], can[1].name)
        # trải gói mã nguồn ra thay vì lồng zip trong zip
        with zipfile.ZipFile(nguon_zip) as trong:
            for ten in trong.namelist():
                z.writestr(f"code-and-data/{ten}", trong.read(ten))

    mb = RA.stat().st_size / 1e6
    with zipfile.ZipFile(RA) as z:
        n = len(z.namelist())
    print(f"{RA.name}: {n} file, {mb:.2f} MB")
    if mb > 10:
        print("  CẢNH BÁO: vượt giới hạn 10 MB của form")
    else:
        print(f"  còn dư {10-mb:.1f} MB so với giới hạn form")
    return 0


if __name__ == "__main__":
    sys.exit(main())
