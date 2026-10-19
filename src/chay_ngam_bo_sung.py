# -*- coding: utf-8 -*-
"""Chạy nốt hai việc còn lại của phản biện, tuần tự, không cần trông.

Phản biện 1 ý 4 (mục 5) và Phản biện 2 ý R2.4: mới thử một mô hình 3B.
Phản biện 1 ý 6: mỗi cấu hình chỉ chạy một lần nên không có biến thiên giải mã.

Thứ tự ưu tiên, vì cả hai cùng đòi CPU nên phải chạy lần lượt:

  1. qwen2.5:7b trên baseline và full.
     Đây là việc đáp được hai phản biện cùng lúc nên chạy trước. Đo thật trên
     máy này là 215 giây một phiếu, gấp 5,5 lần mô hình 3B, nên bỏ cấu hình
     constrained trên 7B để cắt khoảng 8 tiếng: baseline cho biết tỷ lệ lỗi đầu
     bài có đúng với mô hình lớn hơn không, full cho biết mô hình lớn hơn có
     giảm được 36% rơi về bản mẫu không. Constrained chỉ là điểm giữa của hai
     cái đó, tốn 8 tiếng để biết thêm rất ít.
  2. constrained trên 3B, chạy thêm 4 lần nữa cho đủ 5 lần.
     Chọn constrained vì tỷ lệ qua kiểm chứng của nó là 48%, tức là có chỗ để
     dao động. Cấu hình full luôn ra 100% theo thiết kế nên lặp lại chỉ đo được
     biến thiên của tỷ lệ văn mô hình, ít thông tin hơn trên cùng số giờ CPU.

Mỗi bước ghi ra file kết quả riêng, và `run_experiment.run` tự bỏ qua phiếu đã
xong, nên ngắt giữa chừng rồi chạy lại script này là tiếp được, không mất gì.

    python src/chay_ngam_bo_sung.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import run_experiment as rx   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANELS = json.loads((ROOT / "data" / "synthetic_panels.json").read_text(encoding="utf-8"))

VIEC = (
    [("qwen2.5:7b", c, None) for c in ("baseline", "full")]
    + [("qwen2.5:3b", "constrained", lan) for lan in (2, 3, 4, 5)]
)


def xong_chua(model, config, lan):
    hau_to = f"_lan{lan}" if lan else ""
    f = ROOT / "results" / f"{config}_{model.replace(':', '-')}{hau_to}.jsonl"
    if not f.exists():
        return 0
    return sum(1 for _ in open(f, encoding="utf-8"))


def main():
    t0 = time.time()
    print(f"Bắt đầu {time.strftime('%d/%m %H:%M')} — {len(VIEC)} việc\n", flush=True)

    for i, (model, config, lan) in enumerate(VIEC, 1):
        nhan = f"{config} / {model}" + (f" / lần {lan}" if lan else "")
        da = xong_chua(model, config, lan)
        if da >= len(PANELS):
            print(f"[{i}/{len(VIEC)}] {nhan}: đã đủ {da} phiếu, bỏ qua", flush=True)
            continue

        print(f"\n[{i}/{len(VIEC)}] {nhan} — còn {len(PANELS) - da} phiếu "
              f"({time.strftime('%H:%M')})", flush=True)
        rx.MODEL_DANG_CHAY = model

        # rx.run() có thể dừng sớm khi Ollama trục trặc. Lần chạy đầu đã dừng ở
        # phiếu thứ 4 mà vẫn in "xong", nên ở đây phải đếm lại số phiếu thật và
        # gọi tiếp cho tới khi đủ, thay vì tin vào việc hàm đã trả về.
        for vong in range(1, 6):
            try:
                rx.run(config, PANELS, None, model, lan)
            except Exception as e:                   # noqa: BLE001
                print(f"  HỎNG ở {nhan}: {type(e).__name__}: {e}", flush=True)
            co = xong_chua(model, config, lan)
            if co >= len(PANELS):
                break
            print(f"  mới {co}/{len(PANELS)} phiếu, chạy tiếp (vòng {vong})", flush=True)
            time.sleep(30)

        co = xong_chua(model, config, lan)
        trang_thai = "xong" if co >= len(PANELS) else f"CHƯA ĐỦ, mới {co}/{len(PANELS)}"
        print(f"  {trang_thai} lúc {time.strftime('%H:%M')}, "
              f"tổng đã chạy {(time.time()-t0)/3600:.1f} giờ", flush=True)

    print(f"\nHẾT. Tổng {(time.time()-t0)/3600:.1f} giờ.", flush=True)
    for model, config, lan in VIEC:
        print(f"  {config:14} {model:12} {('lần '+str(lan)) if lan else '':8} "
              f"{xong_chua(model, config, lan):3}/{len(PANELS)} phiếu", flush=True)


if __name__ == "__main__":
    main()
