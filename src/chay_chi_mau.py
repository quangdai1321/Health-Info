# -*- coding: utf-8 -*-
"""Cấu hình "chỉ mẫu cố định": bỏ hẳn mô hình ngôn ngữ, chỉ render bản mẫu của tầng 2.

Phản biện 1, ý 4: baseline hiện tại (paste thẳng vào chatbot) là kịch bản rủi ro chứ
không phải đối chứng kỹ thuật mạnh. Muốn biết mô hình ngôn ngữ thật sự thêm được gì,
phải so với bản mà luật tự viết ra, không có mô hình nào tham gia.

Cấu hình này tất định: cùng phiếu thì cùng kết quả, không gọi Ollama, chạy trong vài giây.
Nó đặt trần dưới cho mọi cấu hình có mô hình: bất cứ cấu hình nào không hơn được nó thì
mô hình không đóng góp gì ngoài thời gian chạy.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from classifier import RuleClassifier          # noqa: E402
from prompt_builder import fallback, validate     # noqa: E402
from run_experiment import to_classifier_input    # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen2.5-3b"   # giữ cùng hậu tố tên file để các script phân tích đọc được


def main():
    panels = json.load(open(ROOT / "data" / "synthetic_panels.json", encoding="utf-8"))
    clf = RuleClassifier()
    ra = ROOT / "results" / f"chi_mau_{MODEL}.jsonl"

    with open(ra, "w", encoding="utf-8") as f:
        for p in panels:
            t0 = time.perf_counter()
            cls = clf.classify_panel(to_classifier_input(p["results"]))
            out = fallback(cls)
            v = validate(out, cls)
            dt = time.perf_counter() - t0
            f.write(json.dumps({
                "panel_id": p["panel_id"], "config": "chi_mau", "model": "khong_dung",
                "rule_label": cls["overall_label"], "target_label": p.get("target_label"),
                "n_analytes": len(cls["findings"]),
                "output": out, "parse_error": None, "validation": v,
                "seconds": dt, "attempts": 0, "used_fallback": True,
            }, ensure_ascii=False) + "\n")

    ds = [json.loads(l) for l in open(ra, encoding="utf-8")]
    dat = sum(1 for x in ds if x["validation"]["passed"])
    print(f"{len(ds)} phiếu, qua kiểm chứng {dat} ({100.0*dat/len(ds):.1f}%), "
          f"{sum(x['seconds'] for x in ds):.2f}s tổng")
    print("Đã ghi:", ra)


if __name__ == "__main__":
    main()
