"""
Chạy thực nghiệm 3 cấu hình trên bộ 150 phiếu tổng hợp.

    baseline    Đưa giá trị thô cho LLM, hỏi "giải thích cho bệnh nhân".
                Không có tầng 2, không ràng buộc, không kiểm chứng.
    constrained Tầng 1-3: LLM nhận nhãn đã phân loại + 3 lớp ràng buộc.
    full        Tầng 1-4: thêm kiểm chứng tự động, sinh lại nếu không đạt.

Kết quả lưu dần ra file, chạy lại sẽ bỏ qua phần đã xong.

Dùng:
    python run_experiment.py                      # cả 3 cấu hình, 150 phiếu
    python run_experiment.py --limit 5            # chạy thử 5 phiếu
    python run_experiment.py --config baseline    # một cấu hình
"""

import sys
import argparse
import json
import re
import time
from pathlib import Path

import urllib.request
import urllib.error

from classifier import RuleClassifier
from prompt_builder import SYSTEM_PROMPT, build_prompt, validate, fallback

ROOT = Path(__file__).resolve().parent.parent
PANELS = ROOT / "data" / "synthetic_panels.json"
RESULTS = ROOT / "results"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"
MAX_RETRY = 2          # số lần sinh lại ở cấu hình full


# ------------------------------------------------------------------ gọi model

def call_ollama(messages, model=MODEL, timeout=300, num_predict=2048):
    """
    Gọi Ollama qua HTTP. Trả về (text, thời gian giây).

    num_predict phải đủ lớn: một phiếu 18 chỉ số cần ~50 token mỗi chỉ số
    cộng cấu trúc JSON, vượt xa mức 800 ban đầu. Đầu ra bị cắt cụt sẽ
    thành JSON không hợp lệ và bị tính nhầm thành lỗi của mô hình.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",          # ép đầu ra là JSON hợp lệ
        "options": {"temperature": 0.2, "num_predict": num_predict},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["message"]["content"], time.time() - t0


def parse_json(text):
    """Bóc JSON khỏi đầu ra, chịu được trường hợp model bọc trong ```."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group()), None
            except json.JSONDecodeError:
                pass
        return None, str(e)


# ------------------------------------------------------------------ cấu hình

BASELINE_SYSTEM = (
    "Bạn là trợ lý y tế. Hãy giải thích kết quả xét nghiệm cho bệnh nhân hiểu."
)


def baseline_prompt(panel):
    """
    Cấu hình đối chứng: đưa thẳng giá trị thô, không nhãn, không ràng buộc.
    Mô phỏng cách người dùng thường hỏi thẳng một chatbot.
    """
    lines = []
    for name, payload in panel["results"].items():
        value, unit = (payload[0], payload[1]) if isinstance(payload, (list, tuple)) else (payload, "")
        lines.append(f"- {name}: {value} {unit}".rstrip())

    return (
        "Đây là kết quả xét nghiệm máu của tôi:\n\n"
        + "\n".join(lines)
        + '\n\nHãy giải thích cho tôi hiểu. Trả về JSON dạng '
          '{"items": [{"code": "...", "plain_name": "...", '
          '"status": "cao|thap|trong_khoang", "explanation": "..."}], "closing": "..."}'
    )


def run_baseline(panel, classified):
    text, dt = call_ollama([
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": baseline_prompt(panel)},
    ])
    out, err = parse_json(text)
    if out is None:
        return {"output": None, "parse_error": err, "raw_tail": text[-300:], "raw_len": len(text),
                "validation": {"passed": False, "violations": [{"type": "unparseable"}]},
                "seconds": dt, "attempts": 1}
    return {"output": out, "parse_error": None,
            "validation": validate(out, classified),   # chấm bằng cùng thước đo
            "seconds": dt, "attempts": 1}


def run_constrained(panel, classified):
    text, dt = call_ollama([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(classified)},
    ])
    out, err = parse_json(text)
    if out is None:
        return {"output": None, "parse_error": err, "raw_tail": text[-300:], "raw_len": len(text),
                "validation": {"passed": False, "violations": [{"type": "unparseable"}]},
                "seconds": dt, "attempts": 1}
    return {"output": out, "parse_error": None,
            "validation": validate(out, classified),
            "seconds": dt, "attempts": 1}


def run_full(panel, classified):
    """Tầng 1-4: sinh lại tối đa MAX_RETRY lần, không đạt thì dùng mẫu cố định."""
    total, attempts, last = 0.0, 0, None

    for attempt in range(1, MAX_RETRY + 2):
        attempts = attempt
        text, dt = call_ollama([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(classified)},
        ])
        total += dt
        out, _ = parse_json(text)
        if out is None:
            continue
        v = validate(out, classified)
        last = (out, v)
        if v["passed"]:
            return {"output": out, "parse_error": None, "validation": v,
                    "seconds": total, "attempts": attempts, "used_fallback": False}

    fb = fallback(classified)
    return {"output": fb, "parse_error": None,
            "validation": validate(fb, classified),
            "seconds": total, "attempts": attempts, "used_fallback": True,
            "last_rejected": last[0] if last else None}


CONFIGS = {"baseline": run_baseline, "constrained": run_constrained, "full": run_full}


# ------------------------------------------------------------------ vòng chạy

def to_classifier_input(results):
    """JSON đọc lên biến tuple thành list, đưa về dạng classifier nhận."""
    return {
        k: (tuple(v) if isinstance(v, list) else v)
        for k, v in results.items()
    }


def run(config_name, panels, limit=None, model=MODEL):
    RESULTS.mkdir(exist_ok=True)
    out_path = RESULTS / f"{config_name}_{model.replace(':', '-')}.jsonl"

    done = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["panel_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        print(f"  đã có {len(done)} phiếu, bỏ qua")

    clf = RuleClassifier()
    todo = [p for p in panels if p["panel_id"] not in done]
    if limit:
        todo = todo[:limit]

    t_start = time.time()
    with open(out_path, "a", encoding="utf-8") as f:
        for i, panel in enumerate(todo, 1):
            classified = clf.classify_panel(to_classifier_input(panel["results"]))
            try:
                res = CONFIGS[config_name](panel, classified)
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"\n  LỖI KẾT NỐI ở {panel['panel_id']}: {e}")
                print("  Kiểm tra Ollama có đang chạy không, rồi chạy lại script.")
                break

            rec = {
                "panel_id": panel["panel_id"],
                "config": config_name,
                "model": model,
                "target_label": panel["target_label"],
                "rule_label": classified["overall_label"],
                "n_analytes": len(classified["findings"]),
                "n_rejected_unit": len(classified["rejected_unknown_unit"]),
                **res,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()

            elapsed = time.time() - t_start
            eta = elapsed / i * (len(todo) - i)
            ok = "✓" if res["validation"]["passed"] else "✗"
            print(f"  [{i}/{len(todo)}] {panel['panel_id']} {ok} "
                  f"{res['seconds']:.1f}s  còn ~{eta/60:.0f} phút", end="\r")

    print(f"\n  xong -> {out_path.name}")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=list(CONFIGS) + ["all"], default="all")
    ap.add_argument("--limit", type=int, default=None, help="số phiếu, để thử nhanh")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    panels = json.loads(PANELS.read_text(encoding="utf-8"))
    names = list(CONFIGS) if args.config == "all" else [args.config]

    for name in names:
        print(f"\n=== {name} ({args.model}) ===")
        run(name, panels, args.limit, args.model)


if __name__ == "__main__":
    # Console Windows mac dinh dung cp1252, khong in duoc tieng Viet -> ep UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()
