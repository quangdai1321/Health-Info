# -*- coding: utf-8 -*-
"""Cham lai baseline sau khi quy doi ten hien thi ve ma chuan.

Phan bien noi: 97,3% dau ra baseline dung ten hien thi thay vi ma chuan, nen mot phan
cua con so 0,0% an toan co the chi la loi dinh dang. Script nay tra loi bang chinh
du lieu da co: quy doi ma roi cham lai bang dung bo kiem chung cu.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "I:/Health-Info/src")
sys.stdout.reconfigure(encoding="utf-8")
from classifier import RuleClassifier          # noqa: E402
from prompt_builder import validate            # noqa: E402

GOC = Path("I:/Health-Info")
LOAI = ["false_reassurance", "status_mismatch", "contradictory_wording",
        "forbidden_term", "hallucinated_analyte", "missing_analyte"]
TEN = {"false_reassurance": "Trấn an sai", "status_mismatch": "Sai chiều lệch",
       "contradictory_wording": "Câu chữ mâu thuẫn", "forbidden_term": "Dùng từ cấm",
       "hallucinated_analyte": "Bịa thêm chỉ số", "missing_analyte": "Bỏ sót chỉ số"}

c = RuleClassifier()
panels = {p["panel_id"]: p for p in json.load(open(GOC / "data/synthetic_panels.json", encoding="utf-8"))}


def quy_doi(out):
    """Doi code cua tung muc ve ma chuan, uu tien code, sau do plain_name."""
    if not isinstance(out, dict):
        return out, 0
    moi, doi = [], 0
    for it in out.get("items", []) or []:
        if not isinstance(it, dict):
            continue
        ma = c.table.resolve(str(it.get("code", "")))
        if ma is None:
            ma = c.table.resolve(str(it.get("plain_name", "")))
        it2 = dict(it)
        if ma and ma != it.get("code"):
            it2["code"] = ma
            doi += 1
        moi.append(it2)
    return {**out, "items": moi}, doi


def ty_le(ds, lay):
    return 100.0 * sum(1 for x in ds if lay(x)) / len(ds)


def cot(ds, v_key):
    co = lambda x, t: any(v.get("type") == t for v in x[v_key].get("violations", []))   # noqa: E731
    return {
        "an_toan": ty_le(ds, lambda x: x[v_key].get("passed")),
        **{t: ty_le(ds, lambda x, t=t: co(x, t)) for t in LOAI},
        "code_format": ty_le(ds, lambda x: co(x, "code_format")),
        "unparseable": ty_le(ds, lambda x: co(x, "unparseable")),
    }


for ten_file in ["baseline", "constrained", "full"]:
    f = GOC / f"results/{ten_file}_qwen2.5-3b.jsonl"
    ds = [json.loads(l) for l in open(f, encoding="utf-8")]
    tong_doi = 0
    for x in ds:
        p = panels[x["panel_id"]]
        cls = c.classify_panel(p["results"])
        if x.get("output") is None:
            x["vmoi"] = {"passed": False, "violations": [{"type": "unparseable"}]}
            continue
        out2, doi = quy_doi(x["output"])
        tong_doi += doi
        x["vmoi"] = validate(out2, cls)

    cu, moi = cot(ds, "validation"), cot(ds, "vmoi")
    print("=" * 74)
    print("%s  (%d phiếu, đã quy đổi %d mã chỉ số về mã chuẩn)" % (ten_file.upper(), len(ds), tong_doi))
    print("%-26s %12s %12s %10s" % ("", "chấm như cũ", "bỏ lỗi mã", "chênh"))
    hang = [("An toàn", "an_toan")] + [(TEN[t], t) for t in LOAI] + \
           [("Lỗi định dạng mã", "code_format"), ("Không đọc được JSON", "unparseable")]
    for nhan, k in hang:
        print("%-26s %11.1f%% %11.1f%% %+9.1f" % (nhan, cu[k], moi[k], moi[k] - cu[k]))

    if ten_file == "baseline":
        json.dump({"cu": cu, "moi": moi}, open(GOC / "results/baseline_cham_lai.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
print()
print("Ghi chu: cot 'bo loi ma' la ket qua khi quy doi ten hien thi ve ma chuan truoc khi cham,")
print("tuc la bo han anh huong cua loi dinh dang ma phan bien neu.")
