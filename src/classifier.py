"""
Tầng 1 + Tầng 2: Chuẩn hóa tên chỉ số, chuẩn hóa đơn vị, phân loại bằng luật.

Tầng này KHÔNG dùng LLM. Toàn bộ quyết định "chỉ số nào bất thường"
xảy ra ở đây, trước khi LLM tham gia.

Về chuẩn hóa đơn vị: các phòng xét nghiệm Việt Nam dùng đơn vị khác nhau cho
cùng một chỉ số (Hb có nơi ghi g/L, nơi ghi g/dL — chênh nhau 10 lần).
So sánh giá trị mà bỏ qua đơn vị sẽ tạo ra cảnh báo sai ở mức nguy hiểm.
Nguyên tắc ở đây: đơn vị không nhận ra thì TỪ CHỐI xử lý chỉ số đó,
tuyệt đối không đoán.
"""

import sys
import csv
import re
import unicodedata
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

REF_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_ranges.csv"

NORMAL = "binh_thuong"
WATCH = "theo_doi"
URGENT = "kham_som"
UNKNOWN_UNIT = "khong_ro_don_vi"

LABEL_VI = {
    NORMAL: "Bình thường",
    WATCH: "Theo dõi",
    URGENT: "Nên khám sớm",
    UNKNOWN_UNIT: "Không xác định (đơn vị lạ)",
}


def _normalize_unit(u: str) -> str:
    """Đưa đơn vị về dạng so khớp được: µ->u, bỏ khoảng trắng, hạ chữ thường."""
    if not u:
        return ""
    u = u.replace("µ", "u").replace("μ", "u")
    u = u.replace("×", "x").replace("·", "")
    return re.sub(r"\s+", "", u).lower()


@dataclass
class Analyte:
    code: str
    name_vi: str
    aliases: list
    canonical_unit: str
    low: float
    high: float
    severe_factor: float
    layman_function: str
    unit_factors: dict = field(default_factory=dict)

    @property
    def span(self) -> float:
        return self.high - self.low

    def to_canonical(self, value: float, unit: Optional[str]):
        """
        Quy đổi giá trị về đơn vị chuẩn.
        Trả về (giá trị đã quy đổi, None) nếu được,
        hoặc (None, đơn vị gây lỗi) nếu đơn vị không nhận ra.

        Phiếu không ghi đơn vị thì giả định là đơn vị chuẩn — giả định
        có rủi ro, nên được đánh dấu trong kết quả để báo cáo.
        """
        if unit in (None, ""):
            # Thiếu đơn vị: chỉ an toàn khi mọi đơn vị chấp nhận được đều
            # cùng hệ số. Nếu chỉ số có đơn vị khác hệ số (vd Hb: g/L và g/dL
            # chênh 10 lần) thì đoán bừa sẽ tạo cảnh báo giả -> từ chối.
            if len(set(self.unit_factors.values())) > 1:
                return None, "(thiếu đơn vị)"
            return value, None
        key = _normalize_unit(unit)
        if key not in self.unit_factors:
            return None, unit
        return value * self.unit_factors[key], None


@dataclass
class Finding:
    code: str
    name_vi: str
    value: float              # đã quy đổi về đơn vị chuẩn
    raw_value: float          # giá trị gốc trên phiếu
    unit: str                 # đơn vị chuẩn
    raw_unit: Optional[str]   # đơn vị gốc trên phiếu
    converted: bool
    low: float
    high: float
    direction: str
    label: str
    label_vi: str
    deviation_ratio: float
    layman_function: str

    def to_dict(self):
        return asdict(self)


def _normalize_key(text: str) -> str:
    """
    Bỏ dấu tiếng Việt, hạ chữ thường, tách token.

    '%' và '#' được giữ lại dưới dạng cờ pct/abs vì chúng phân biệt
    tỷ lệ phần trăm với số lượng tuyệt đối. Ký hiệu có thể đứng trước
    ('% Neu') hoặc sau ('NEUT%') tùy phòng xét nghiệm.
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D").lower()
    text = text.replace("*", " ")                       # '* WBC' -> 'WBC'
    text = text.replace("%", " pct ").replace("#", " abs ")

    if re.search(r"\bty le\b|\bti le\b", text):
        text += " pct "
    if re.search(r"\bso luong\b|\bsl\b", text):
        text += " abs "

    tokens = re.findall(r"[a-z0-9]+", text)
    has_pct, has_abs = "pct" in tokens, "abs" in tokens
    core = "".join(t for t in tokens if t not in ("pct", "abs"))
    return core + ("|pct" if has_pct else "") + ("|abs" if has_abs else "")


class ReferenceTable:
    """Tầng 1: ánh xạ tên chỉ số và đơn vị."""

    def __init__(self, path: Path = REF_PATH):
        self.analytes: dict[str, Analyte] = {}
        self._index: dict[str, str] = {}

        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                factors = {}
                for pair in row["accepted_units"].split("|"):
                    if not pair:
                        continue
                    u, k = pair.rsplit("=", 1)
                    factors[_normalize_unit(u)] = float(k)

                a = Analyte(
                    code=row["code"],
                    name_vi=row["name_vi"],
                    aliases=[s for s in row["aliases"].split("|") if s],
                    canonical_unit=row["canonical_unit"],
                    low=float(row["low"]),
                    high=float(row["high"]),
                    severe_factor=float(row["severe_factor"]),
                    layman_function=row["layman_function"],
                    unit_factors=factors,
                )
                self.analytes[a.code] = a
                for key in [a.code, a.name_vi, *a.aliases]:
                    self._index[_normalize_key(key)] = a.code

    def resolve(self, raw_name: str) -> Optional[str]:
        return self._index.get(_normalize_key(raw_name))

    def __len__(self):
        return len(self.analytes)


class RuleClassifier:
    """
    Tầng 2: quy đổi đơn vị rồi so sánh với khoảng tham chiếu.

    Phân mức:
      - Trong khoảng [low, high]                    -> NORMAL
      - Ngoài khoảng, lệch <= severe_factor * span  -> WATCH
      - Lệch nhiều hơn                              -> URGENT
      - Đơn vị không nhận ra                        -> UNKNOWN_UNIT (từ chối)
    """

    def __init__(self, table: Optional[ReferenceTable] = None):
        self.table = table or ReferenceTable()

    def classify_one(self, code: str, value: float, unit: Optional[str] = None) -> Finding:
        a = self.table.analytes[code]
        canon, bad_unit = a.to_canonical(float(value), unit)

        if bad_unit is not None:
            return Finding(
                code=a.code, name_vi=a.name_vi, value=float("nan"), raw_value=float(value),
                unit=a.canonical_unit, raw_unit=bad_unit, converted=False,
                low=a.low, high=a.high, direction="khong_xac_dinh",
                label=UNKNOWN_UNIT, label_vi=LABEL_VI[UNKNOWN_UNIT],
                deviation_ratio=float("nan"), layman_function=a.layman_function,
            )

        if a.low <= canon <= a.high:
            direction, label, ratio = "trong_khoang", NORMAL, 0.0
        else:
            if canon < a.low:
                direction, excess = "thap", a.low - canon
            else:
                direction, excess = "cao", canon - a.high
            ratio = excess / a.span if a.span > 0 else float("inf")
            label = WATCH if ratio <= a.severe_factor + 1e-9 else URGENT

        return Finding(
            code=a.code, name_vi=a.name_vi, value=round(canon, 4), raw_value=float(value),
            unit=a.canonical_unit, raw_unit=unit,
            converted=(unit is not None and abs(canon - float(value)) > 1e-12),
            low=a.low, high=a.high, direction=direction,
            label=label, label_vi=LABEL_VI[label],
            deviation_ratio=round(ratio, 4), layman_function=a.layman_function,
        )

    def classify_panel(self, raw_results: dict) -> dict:
        """
        Nhận {tên chỉ số: giá trị} hoặc {tên chỉ số: (giá trị, đơn vị)}.
        Chỉ số có đơn vị lạ được tách riêng, KHÔNG tính vào nhãn tổng thể.
        """
        findings, unresolved, rejected = [], [], []

        for raw_name, payload in raw_results.items():
            if isinstance(payload, (tuple, list)):
                value, unit = payload[0], payload[1]
            else:
                value, unit = payload, None

            if value is None or value == "":
                continue

            code = self.table.resolve(raw_name)
            if code is None:
                unresolved.append(raw_name)
                continue

            f = self.classify_one(code, value, unit)
            (rejected if f.label == UNKNOWN_UNIT else findings).append(f)

        if any(f.label == URGENT for f in findings):
            overall = URGENT
        elif any(f.label == WATCH for f in findings):
            overall = WATCH
        else:
            overall = NORMAL

        return {
            "findings": [f.to_dict() for f in findings],
            "overall_label": overall,
            "overall_label_vi": LABEL_VI[overall],
            "abnormal_count": sum(1 for f in findings if f.label != NORMAL),
            "converted_count": sum(1 for f in findings if f.converted),
            "unresolved_names": unresolved,
            "rejected_unknown_unit": [f.to_dict() for f in rejected],
        }


if __name__ == "__main__":
    # Console Windows mac dinh dung cp1252, khong in duoc tieng Viet -> ep UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    clf = RuleClassifier()
    print(f"Đã nạp {len(clf.table)} chỉ số\n")

    # Phiếu kiểu phòng xét nghiệm dùng K/µL và g/dL
    panel = {
        "* WBC": (8.977, "K/µL"),
        "% Neu": (60.05, "%"),
        "# Neu": (5.391, "K/µL"),
        "* RBC": (5.212, "M/µL"),
        "Hb": (14.56, "g/dL"),
        "Hct": (44.01, "%"),
        "MCHC": (33.08, "g/dL"),
        "* PLT": (308.7, "K/µL"),
        "MCV": (84.44, "fL"),
        "Chỉ số lạ ABC": (1.0, "mmol/L"),
    }
    out = clf.classify_panel(panel)

    print(f"{'Mã':10s} {'gốc':>9s} {'đơn vị':8s} {'chuẩn':>9s} {'đơn vị':7s} nhãn")
    print("-" * 62)
    for f in out["findings"]:
        mark = "  (đã quy đổi)" if f["converted"] else ""
        print(f"{f['code']:10s} {f['raw_value']:>9} {str(f['raw_unit']):8s} "
              f"{f['value']:>9} {f['unit']:7s} {f['label_vi']}{mark}")

    print(f"\nSố chỉ số phải quy đổi : {out['converted_count']}")
    print(f"Tên không nhận ra      : {out['unresolved_names']}")
    print(f"Từ chối vì đơn vị lạ   : {[f['code'] for f in out['rejected_unknown_unit']]}")
    print(f"Nhãn tổng thể          : {out['overall_label_vi']}")
