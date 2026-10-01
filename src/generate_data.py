"""
Sinh bộ dữ liệu tổng hợp (synthetic benchmark) cho đánh giá hệ thống.

Vì sao dùng dữ liệu tổng hợp thay vì phiếu xét nghiệm thật:
  1. Cần nhãn đúng (ground truth) biết trước để đo độ chính xác;
     phiếu thật không kèm nhãn mức lệch.
  2. Cần kiểm soát phân bố — phiếu thật đa số là bình thường,
     không đủ ca lệch nhiều để kiểm thử cơ chế cảnh báo.
  3. Không đụng dữ liệu bệnh nhân, nên không cần phê duyệt đạo đức
     và không có rủi ro lộ thông tin định danh.

Hạn chế này được nêu rõ trong phần Limitations của bài.
"""

import sys
import json
import random
from pathlib import Path

from classifier import _normalize_unit as _norm


def a_units(a):
    """Danh sách đơn vị hiển thị của một chỉ số, đọc lại từ bảng tham chiếu."""
    return _UNIT_DISPLAY[a.code]


_UNIT_DISPLAY = {}

from classifier import ReferenceTable, RuleClassifier, NORMAL, WATCH, URGENT

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_panels.json"

# Số chỉ số xuất hiện trên mỗi phiếu (phiếu thật thường bỏ trống một số dòng)
MIN_ANALYTES, MAX_ANALYTES = 10, 18


def _sample_normal(a, rng):
    """Giá trị nằm gọn trong khoảng tham chiếu."""
    pad = a.span * 0.05
    return rng.uniform(a.low + pad, a.high - pad)


def _sample_watch(a, rng):
    """Lệch ra ngoài nhưng chưa vượt ngưỡng severe_factor."""
    excess = rng.uniform(0.05, a.severe_factor * 0.9) * a.span
    if a.low <= 0 or rng.random() < 0.5:
        return a.high + excess
    return max(0.0, a.low - excess)


def _sample_urgent(a, rng):
    """Lệch vượt ngưỡng severe_factor."""
    excess = rng.uniform(a.severe_factor * 1.2, a.severe_factor * 3.0) * a.span
    if a.low <= 0 or rng.random() < 0.5:
        return a.high + excess
    return max(0.0, a.low - excess)


def _sample_borderline(a, rng):
    """Ca khó: giá trị sát mép khoảng tham chiếu."""
    edge = a.span * 0.01
    return rng.choice([
        a.low + rng.uniform(0, edge),
        a.high - rng.uniform(0, edge),
        a.low - rng.uniform(0, edge),
        a.high + rng.uniform(0, edge),
    ])


def _round_like(a, value):
    """Làm tròn theo cách phiếu xét nghiệm thật hay in."""
    if a.canonical_unit in ("G/L", "T/L") and a.high < 20:
        return round(value, 2)
    if a.canonical_unit in ("%", "fL", "pg"):
        return round(value, 1)
    return round(value, 1) if a.high < 100 else int(round(value))


def _load_unit_display():
    import csv as _csv
    path = Path(__file__).resolve().parent.parent / "data" / "reference_ranges.csv"
    with open(path, encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            _UNIT_DISPLAY[row["code"]] = [
                p.rsplit("=", 1)[0] for p in row["accepted_units"].split("|") if p
            ]


def generate(n_per_group=50, seed=42, borderline_rate=0.15):
    _load_unit_display()
    """
    Sinh 3 nhóm bằng nhau: bình thường / theo dõi / khám sớm.
    Nhãn tổng thể của phiếu = mức nghiêm trọng nhất trong các chỉ số,
    khớp đúng quy tắc của RuleClassifier.
    """
    rng = random.Random(seed)
    table = ReferenceTable()
    clf = RuleClassifier(table)
    codes = list(table.analytes.keys())
    panels = []

    plan = [(NORMAL, n_per_group), (WATCH, n_per_group), (URGENT, n_per_group)]

    for target, count in plan:
        made = 0
        while made < count:
            chosen = rng.sample(codes, rng.randint(MIN_ANALYTES, MAX_ANALYTES))
            results, hard = {}, False

            # Với nhóm bất thường, chọn 1-3 chỉ số mang mức lệch đích
            n_dev = rng.randint(1, 3) if target != NORMAL else 0
            deviant = set(rng.sample(chosen, n_dev)) if n_dev else set()

            for code in chosen:
                a = table.analytes[code]
                if code in deviant:
                    v = _sample_watch(a, rng) if target == WATCH else _sample_urgent(a, rng)
                elif target == NORMAL and rng.random() < borderline_rate:
                    # ca khó chỉ dùng trong nhóm bình thường để không phá nhãn đích
                    v = _sample_borderline(a, rng)
                    v = min(max(v, a.low), a.high)   # kẹp lại trong khoảng
                    hard = True
                else:
                    v = _sample_normal(a, rng)

                # dùng ngẫu nhiên một alias để kiểm thử tầng 1
                label_name = rng.choice([a.name_vi, *a.aliases]) if a.aliases else a.name_vi
                # Mô phỏng việc mỗi phòng xét nghiệm dùng đơn vị khác nhau:
                # chọn ngẫu nhiên một đơn vị chấp nhận được và quy đổi ngược lại.
                unit_key = rng.choice(list(a.unit_factors.keys()))
                factor = a.unit_factors[unit_key]
                shown_unit = next(u for u in a_units(a) if _norm(u) == unit_key)
                results[label_name] = (_round_like(a, v / factor), shown_unit)

            # Làm tròn có thể đẩy giá trị trở lại trong khoảng và phá nhãn đích.
            # Kiểm tra lại bằng chính bộ phân loại; không khớp thì bỏ, sinh lại.
            if clf.classify_panel(results)["overall_label"] != target:
                continue

            panels.append({
                "panel_id": f"SYN-{len(panels)+1:04d}",
                "target_label": target,
                "has_borderline": hard,
                "results": results,
            })
            made += 1

    rng.shuffle(panels)
    return panels


def verify(panels):
    """Kiểm tra nhãn đích khớp với đầu ra của bộ phân loại."""
    clf = RuleClassifier()
    mismatch, unresolved = 0, 0
    for p in panels:
        out = clf.classify_panel(p["results"])
        if out["overall_label"] != p["target_label"]:
            mismatch += 1
        unresolved += len(out["unresolved_names"])
    return mismatch, unresolved


if __name__ == "__main__":
    # Console Windows mac dinh dung cp1252, khong in duoc tieng Viet -> ep UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    panels = generate()
    mismatch, unresolved = verify(panels)

    # newline="\n": ghi LF trên mọi hệ điều hành, để chạy lại trên Windows
    # cho ra file giống hệt từng byte thay vì đổi hết sang CRLF.
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(panels, ensure_ascii=False, indent=2))

    print(f"Đã sinh {len(panels)} phiếu -> {OUT_PATH.name}")
    for lbl in (NORMAL, WATCH, URGENT):
        print(f"  {lbl:14s}: {sum(1 for p in panels if p['target_label']==lbl)}")
    print(f"  ca sát ngưỡng : {sum(1 for p in panels if p['has_borderline'])}")
    print(f"\nKiểm tra nhất quán nhãn : {mismatch} lệch / {len(panels)}")
    print(f"Tên chỉ số không nhận ra: {unresolved}")
