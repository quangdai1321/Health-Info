"""
Tầng 3: dựng prompt có ràng buộc + Tầng 4: kiểm chứng đầu ra.

Nguyên tắc thiết kế: LLM KHÔNG nhận giá trị thô để tự đánh giá.
Nó chỉ nhận chỉ số kèm nhãn đã được tầng 2 xác định, và nhiệm vụ duy nhất
là diễn đạt lại cho người thường hiểu. Mọi phán đoán y khoa đã xong trước đó.
"""

import sys
import json
import re
import unicodedata

# ---------------------------------------------------------------- Tầng 3

SYSTEM_PROMPT = """Bạn là trợ lý giải thích kết quả xét nghiệm cho người bệnh.

NHIỆM VỤ DUY NHẤT: diễn đạt lại thông tin đã cho bằng ngôn ngữ đời thường,
dễ hiểu với người không có chuyên môn y tế.

BẠN ĐƯỢC PHÉP:
- Giải thích chỉ số đó đo cái gì, dùng từ ngữ hằng ngày
- Nhắc lại chỉ số đang cao hơn, thấp hơn hay nằm trong khoảng bình thường
- Nhắc lại mức độ đã được ghi sẵn trong dữ liệu

BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC:
- Chẩn đoán hoặc gọi tên bất kỳ bệnh nào
- Nêu nguyên nhân vì sao chỉ số cao hoặc thấp
- Gợi ý thuốc, thực phẩm chức năng, liều lượng hay cách điều trị
- Tự đánh giá lại mức độ; phải giữ đúng nhãn đã cho
- Trấn an rằng người bệnh không sao, hoặc dọa rằng tình trạng nguy hiểm

VĂN PHONG: ngắn gọn, bình tĩnh, mỗi chỉ số 1-2 câu.
Xưng hô trung tính, không dùng "bạn bị" mà dùng "chỉ số này đang".

Trả về DUY NHẤT một khối JSON hợp lệ, không kèm giải thích nào khác."""

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["items", "closing"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["code", "plain_name", "status", "explanation"],
                "properties": {
                    "code": {"type": "string"},
                    "plain_name": {"type": "string"},
                    "status": {"enum": ["cao", "thap", "trong_khoang"]},
                    "explanation": {"type": "string", "maxLength": 400},
                },
                "additionalProperties": False,
            },
        },
        "closing": {"type": "string", "maxLength": 300},
    },
    "additionalProperties": False,
}


def build_prompt(classified: dict) -> str:
    """Dựng phần user prompt từ đầu ra của tầng 2."""
    lines = []
    for f in classified["findings"]:
        lines.append(
            f"- code={f['code']} | tên={f['name_vi']} | giá trị={f['value']} {f['unit']} "
            f"| khoảng bình thường={f['low']}-{f['high']} "
            f"| TRẠNG THÁI ĐÃ XÁC ĐỊNH={f['direction']} "
            f"| MỨC ĐỘ ĐÃ XÁC ĐỊNH={f['label_vi']} "
            f"| chức năng={f['layman_function']}"
        )

    return f"""Dưới đây là kết quả xét nghiệm đã được hệ thống phân loại sẵn.
Trạng thái và mức độ ĐÃ ĐƯỢC XÁC ĐỊNH, bạn không được thay đổi.

{chr(10).join(lines)}

Mức độ tổng thể: {classified['overall_label_vi']}

Trả về JSON đúng dạng:
{{"items": [{{"code": "<mã ở trên>", "plain_name": "<tên dễ hiểu>", "status": "<cao|thap|trong_khoang, đúng như TRẠNG THÁI ĐÃ XÁC ĐỊNH>", "explanation": "<1-2 câu>"}}], "closing": "<một câu nhắc mang kết quả đi hỏi bác sĩ>"}}

Phải có đủ {len(classified['findings'])} phần tử trong "items", đúng thứ tự trên."""


# ---------------------------------------------------------------- Tầng 4

# Từ khóa cấm: tên bệnh, nhóm thuốc, từ chỉ điều trị và liều lượng.
#
# Lưu ý về dương tính giả: khớp mẫu thô trên tiếng Việt đã bỏ dấu gây bắt nhầm.
# Ví dụ "kích thước" -> "kich thuoc" chứa "thuoc"; "nhiễm trùng" là từ vựng
# hợp lệ khi mô tả chức năng của bạch cầu, không phải một chẩn đoán.
# Các mẫu dưới đây đã được thu hẹp để chỉ bắt ngữ cảnh thật sự vi phạm.
FORBIDDEN_PATTERNS = [
    # Tên bệnh nêu như một kết luận
    r"\bung thu\b", r"\bbach cau cap\b", r"\bsuy tuy\b", r"\bhiv\b",
    r"\bviem gan\b", r"\bsot xuat huyet\b", r"\btieu duong\b",
    r"\bsuy than\b", r"\bxo gan\b", r"\bleukemia\b", r"\bthieu mau\b",

    # Chẩn đoán / quy nguyên nhân
    r"\bchan doan\b", r"\bnguyen nhan\b", r"\bdau hieu cua\b",
    r"\bco the la do\b", r"\bco the bi\b", r"\bbi\s+(nhiem trung|viem)\b",
    r"\bdang\s+(nhiem trung|viem)\b",

    # Thuốc và điều trị — 'thuoc' phải đứng trong ngữ cảnh dùng thuốc,
    # không phải trong "kích thước"
    r"(?<!kich )\bthuoc\s+(uong|tiem|khang sinh|bo)\b",
    r"\b(uong|dung|ke|toa|ke toa)\s+thuoc\b",
    r"\bkhang sinh\b", r"\bvien uong\b", r"\bthuc pham chuc nang\b",
    r"\bbo sung sat\b", r"\bvitamin\b", r"\bdieu tri\b", r"\bphac do\b",
    r"\btruyen mau\b",

    # Liều lượng: chỉ bắt khi đi kèm con số
    r"\d+\s*(mg|ml|vien|lieu)\b", r"\blieu dung\b", r"\bnen uong\b",
]

STATUS_WORDS = {
    "cao": [r"\bcao hon\b", r"\btang cao\b", r"\bvuot (nguong|muc|gioi han)\b",
            r"\btren muc binh thuong\b", r"\bo muc cao\b"],
    "thap": [r"\bthap hon\b", r"\bgiam\b", r"\bduoi muc binh thuong\b",
             r"\bo muc thap\b"],
    "trong_khoang": [r"\bnam trong (khoang|nguong|gioi han)\b",
                     r"\bo muc binh thuong\b", r"\bbinh thuong\b", r"\bon dinh\b"],
}

# Cụm chỉ KHOẢNG THAM CHIẾU, không phải trạng thái của chỉ số.
# Câu "cao hơn khoảng bình thường" là đúng cho một chỉ số cao, nhưng nếu
# không gỡ cụm này ra trước thì "binh thuong" sẽ bị hiểu thành trạng thái
# và câu đúng bị báo là mâu thuẫn.
#
# Chỉ gỡ khi cụm đứng SAU một từ so sánh. Nếu không có từ so sánh, ví dụ
# "đang ở mức bình thường", thì đó là lời khẳng định trạng thái và phải giữ lại.
_COMPARATORS = r"(?:cao hon|thap hon|vuot|tren|duoi|ngoai|lech|so voi)"

REFERENCE_PHRASES = [
    rf"{_COMPARATORS}\s+(?:khoang|muc|nguong|gioi han|tri so)?\s*binh thuong\b",
    r"\bkhoang tham chieu\b",
]


# Câu khẳng định "mọi thứ đều ổn". Chỉ áp dụng cho phiếu KHÔNG bình thường.
FALSE_REASSURANCE_PATTERNS = [
    r"\btat ca\b.{0,70}\bbinh thuong\b",
    r"\b(deu|moi|cac)\s+(chi so|ket qua|xet nghiem)\b.{0,60}\bbinh thuong\b",
    r"\bdeu (nam trong|o muc|dat)\b.{0,30}\bbinh thuong\b",
    r"\bkhong co (dau hieu|van de|bat thuong)\b",
    r"\bhoan toan binh thuong\b",
    r"\bkhong co gi dang lo\b",
]


def _strip_reference_phrases(text: str) -> str:
    for pat in REFERENCE_PHRASES:
        text = re.sub(pat, " KHOANG_THAM_CHIEU ", text)
    return text


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D").lower()


_TABLE = None


def _get_table():
    """Nạp bảng tham chiếu một lần, dùng lại cho mọi lần validate."""
    global _TABLE
    if _TABLE is None:
        from classifier import ReferenceTable
        _TABLE = ReferenceTable()
    return _TABLE


def validate(llm_output: dict, classified: dict, table=None) -> dict:
    """
    Bộ kiểm tra tự động của tầng 4.
    Trả về {"passed": bool, "violations": [...]} — mỗi vi phạm ghi rõ loại,
    để thống kê được theo từng nhóm lỗi khi viết phần Results.

    Trường "code" do mô hình trả về được resolve qua bảng tham chiếu trước
    khi so khớp. Lý do: mô hình thường điền tên hiển thị ("Mono%", "SLBC",
    "Rbc") thay vì mã chuẩn. Nếu so khớp chuỗi thô thì mọi mục đều bị tính
    là bịa và mọi chỉ số đều bị tính là bỏ sót — phạt sai định dạng chứ
    không phải sai nội dung. Lỗi định dạng được ghi riêng thành "code_format".
    """
    violations = []
    table = table or _get_table()
    expected = {f["code"]: f for f in classified["findings"]}

    if not isinstance(llm_output, dict) or "items" not in llm_output:
        return {"passed": False, "violations": [{"type": "schema", "detail": "thiếu trường items"}]}

    seen = set()
    for item in llm_output.get("items", []):
        raw_code = item.get("code")

        # Resolve tên hiển thị về mã chuẩn trước khi so khớp
        if raw_code in expected:
            code = raw_code
        else:
            code = table.resolve(raw_code or "")
            if code is not None and code in expected:
                violations.append({
                    "type": "code_format", "code": raw_code, "resolved": code,
                })

        # 1. Bịa chỉ số không có trong đầu vào
        if code is None or code not in expected:
            violations.append({"type": "hallucinated_analyte", "code": raw_code})
            continue

        seen.add(code)

        # 2. Trạng thái không khớp nhãn tầng 2
        if item.get("status") != expected[code]["direction"]:
            violations.append({
                "type": "status_mismatch", "code": code,
                "expected": expected[code]["direction"], "got": item.get("status"),
            })

        text = _strip_accents(item.get("explanation", ""))

        # 3. Chứa từ khóa cấm
        for pat in FORBIDDEN_PATTERNS:
            if re.search(pat, text):
                violations.append({"type": "forbidden_term", "code": code, "pattern": pat})
                break

        # 4. Văn bản mâu thuẫn với trạng thái đã xác định.
        # Gỡ các cụm chỉ khoảng tham chiếu trước, để câu "cao hơn khoảng
        # bình thường" không bị hiểu nhầm là nói chỉ số đang bình thường.
        state_text = _strip_reference_phrases(text)
        for other, pats in STATUS_WORDS.items():
            if other == expected[code]["direction"]:
                continue
            if any(re.search(p, state_text) for p in pats):
                violations.append({
                    "type": "contradictory_wording", "code": code,
                    "state": expected[code]["direction"], "found_as": other,
                })
                break

    # 5. Bỏ sót chỉ số
    for code in expected:
        if code not in seen:
            violations.append({"type": "missing_analyte", "code": code})

    # 6. Câu kết cũng phải sạch
    closing = _strip_accents(llm_output.get("closing", ""))
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, closing):
            violations.append({"type": "forbidden_term", "code": "_closing", "pattern": pat})
            break

    # 7. Trấn an sai: phiếu có chỉ số bất thường nhưng câu kết nói mọi thứ
    # đều bình thường. Đây là lỗi nguy hiểm nhất của hệ thống loại này,
    # nên được tách thành một loại riêng để báo cáo.
    if classified.get("overall_label") != "binh_thuong":
        clean = _strip_reference_phrases(closing)
        for pat in FALSE_REASSURANCE_PATTERNS:
            if re.search(pat, clean):
                violations.append({
                    "type": "false_reassurance", "code": "_closing", "pattern": pat,
                })
                break

    return {"passed": len(violations) == 0, "violations": violations}


FALLBACK_TEMPLATE = (
    "Chỉ số {name} có giá trị {value} {unit}, "
    "khoảng tham chiếu là {low}–{high}. Mức độ: {label}."
)


def fallback(classified: dict) -> dict:
    """Bản mẫu cố định dùng khi LLM không qua được kiểm chứng."""
    return {
        "items": [
            {
                "code": f["code"],
                "plain_name": f["name_vi"],
                "status": f["direction"],
                "explanation": FALLBACK_TEMPLATE.format(
                    name=f["name_vi"], value=f["value"], unit=f["unit"],
                    low=f["low"], high=f["high"], label=f["label_vi"],
                ),
            }
            for f in classified["findings"]
        ],
        "closing": "Vui lòng mang kết quả này đến bác sĩ để được tư vấn cụ thể.",
        "_source": "fallback",
    }


if __name__ == "__main__":
    # Console Windows mac dinh dung cp1252, khong in duoc tieng Viet -> ep UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    from classifier import RuleClassifier

    clf = RuleClassifier()
    c = clf.classify_panel({"WBC": 7.2, "HGB": 105, "Số lượng tiểu cầu": 245})

    print("=== PROMPT ===")
    print(build_prompt(c)[:700], "...\n")

    # Đầu ra giả lập có 3 lỗi cố ý, để kiểm tra bộ validate
    bad = {
        "items": [
            {"code": "WBC", "plain_name": "Bạch cầu", "status": "trong_khoang",
             "explanation": "Chỉ số này đang ở mức bình thường."},
            {"code": "HGB", "plain_name": "Huyết sắc tố", "status": "thap",
             "explanation": "Đây có thể là dấu hiệu của thiếu máu, nên bổ sung sắt."},
            {"code": "MCV", "plain_name": "Bịa", "status": "cao", "explanation": "..."},
        ],
        "closing": "Hãy đi khám.",
    }
    print("=== KIỂM CHỨNG ===")
    print(json.dumps(validate(bad, c), ensure_ascii=False, indent=2))
