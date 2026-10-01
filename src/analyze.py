"""
Tổng hợp kết quả thực nghiệm thành bảng so sánh 3 cấu hình.

Xuất ra:
  - bảng in ra màn hình
  - results/summary.csv  (dán vào Excel hoặc chuyển thành bảng LaTeX)

Dùng:  python analyze.py

Hai chỉ số "đạt" được tách riêng, vì gộp lại sẽ báo cáo sai sự thật:
  - An toàn   : đầu ra cuối cùng qua được kiểm chứng, TÍNH CẢ mẫu cố định.
                Đây là tính chất của hệ thống.
  - LLM tự đạt: mô hình tự viết được bản qua kiểm chứng, KHÔNG dùng đường lui.
                Đây là năng lực của mô hình.
Cấu hình full có thể đạt 100% an toàn trong khi LLM tự đạt chỉ 60% — chênh
lệch đó chính là phần do cơ chế đường lui gánh.
"""

import sys
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Các loại vi phạm do tầng 4 phát hiện, xếp theo mức nghiêm trọng.
# false_reassurance đứng đầu: nói với người bệnh rằng mọi thứ bình thường
# trong khi phiếu có chỉ số bất thường là lỗi nguy hiểm nhất của hệ thống này.
VIOLATION_TYPES = [
    ("false_reassurance", "Trấn an sai"),
    ("status_mismatch", "Sai trạng thái"),
    ("forbidden_term", "Vượt giới hạn an toàn"),
    ("hallucinated_analyte", "Bịa chỉ số"),
    ("missing_analyte", "Bỏ sót chỉ số"),
    ("contradictory_wording", "Câu chữ mâu thuẫn"),
    ("code_format", "Sai định dạng mã"),
    ("unparseable", "Không đọc được JSON"),
]


def load_all():
    runs = defaultdict(list)
    for path in sorted(RESULTS.glob("*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                runs[(rec["config"], rec["model"])].append(rec)
    return runs


def summarize(records):
    n = len(records)
    if n == 0:
        return None

    counts = Counter()
    for r in records:
        seen = {v["type"] for v in r["validation"]["violations"]}
        counts.update(seen)          # đếm theo phiếu, không theo số lỗi

    passed = sum(1 for r in records if r["validation"]["passed"])
    fallbacks = sum(1 for r in records if r.get("used_fallback"))
    # LLM tự đạt: qua kiểm chứng mà không phải dùng đường lui
    llm_passed = sum(
        1 for r in records
        if r["validation"]["passed"] and not r.get("used_fallback")
    )

    secs = [r["seconds"] for r in records]
    attempts = [r.get("attempts", 1) for r in records]

    row = {
        "n": n,
        "safe_rate": passed / n,
        "llm_pass_rate": llm_passed / n,
        "fallback_rate": fallbacks / n,
        "mean_sec": sum(secs) / n,
        "mean_attempts": sum(attempts) / n,
    }
    for key, _ in VIOLATION_TYPES:
        row[key] = counts.get(key, 0) / n
    return row


def main():
    runs = load_all()
    if not runs:
        print("Chưa có kết quả. Chạy run_experiment.py trước.")
        return

    order = {"baseline": 0, "constrained": 1, "full": 2}
    keys = sorted(runs, key=lambda k: (k[1], order.get(k[0], 9)))

    rows = []
    for key in keys:
        s = summarize(runs[key])
        if s:
            rows.append({"config": key[0], "model": key[1], **s})

    # ---- bảng chính: an toàn và các lỗi nội dung ----
    print(f"\n{'Cấu hình':13s} {'n':>4s} {'AnToàn':>7s} {'LLMĐạt':>7s} "
          f"{'TrấnAn':>7s} {'SaiTT':>6s} {'Cấm':>6s} {'Bịa':>6s} "
          f"{'Sót':>6s} {'MThuẫn':>7s} {'giây':>7s}")
    print("-" * 86)
    for r in rows:
        print(f"{r['config']:13s} {r['n']:>4d} "
              f"{r['safe_rate']:>6.0%} {r['llm_pass_rate']:>7.0%} "
              f"{r['false_reassurance']:>7.0%} {r['status_mismatch']:>6.0%} "
              f"{r['forbidden_term']:>6.0%} {r['hallucinated_analyte']:>6.0%} "
              f"{r['missing_analyte']:>6.0%} {r['contradictory_wording']:>7.0%} "
              f"{r['mean_sec']:>7.1f}")

    # ---- bảng phụ: lỗi hình thức, tách riêng ----
    print(f"\n{'Cấu hình':13s} {'SaiĐịnhDạngMã':>14s} {'LỗiJSON':>9s}")
    print("-" * 40)
    for r in rows:
        print(f"{r['config']:13s} {r['code_format']:>13.0%} {r['unparseable']:>9.0%}")
    print("  (sai định dạng mã = điền tên hiển thị thay vì mã chuẩn;")
    print("   lỗi hình thức, không phải lỗi nội dung)")

    # ---- cấu hình full ----
    full = [r for r in rows if r["config"] == "full"]
    if full:
        print("\nCấu hình full:")
        for r in full:
            print(f"  {r['model']}: trung bình {r['mean_attempts']:.2f} lần sinh, "
                  f"dùng mẫu cố định {r['fallback_rate']:.0%}")
            gap = r["safe_rate"] - r["llm_pass_rate"]
            if gap > 0:
                print(f"    -> {gap:.0%} số phiếu đạt là nhờ đường lui, "
                      f"không phải do mô hình tự viết được.")

    # ---- ghi CSV ----
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "summary.csv"
    fields = ["config", "model", "n", "safe_rate", "llm_pass_rate",
              "fallback_rate", "mean_sec", "mean_attempts"] + \
             [k for k, _ in VIOLATION_TYPES]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, 0) for k in fields})
    print(f"\n-> {out}")

    # ---- bảng LaTeX cho bài ----
    print("\n--- LaTeX ---")
    print("\\begin{table}[t]")
    print("\\caption{So sánh ba cấu hình trên bộ dữ liệu tổng hợp (\\%)}")
    print("\\label{tab:results}")
    print("\\centering")
    print("\\begin{tabular}{lrrrrrrr}")
    print("\\hline")
    print("Cấu hình & An toàn & LLM đạt & Trấn an sai & Sai TT & "
          "Cấm & Bịa & Sót \\\\")
    print("\\hline")
    for r in rows:
        print(f"{r['config']} & {r['safe_rate']*100:.1f} & "
              f"{r['llm_pass_rate']*100:.1f} & {r['false_reassurance']*100:.1f} & "
              f"{r['status_mismatch']*100:.1f} & {r['forbidden_term']*100:.1f} & "
              f"{r['hallucinated_analyte']*100:.1f} & "
              f"{r['missing_analyte']*100:.1f} \\\\")
    print("\\hline")
    print("\\end{tabular}")
    print("\\end{table}")


if __name__ == "__main__":
    # Console Windows mac dinh dung cp1252, khong in duoc tieng Viet -> ep UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()