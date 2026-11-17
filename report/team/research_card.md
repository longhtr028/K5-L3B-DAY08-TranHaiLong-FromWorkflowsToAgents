# Research card — R2: lỗi kiểm chứng trong swarm

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, [Why Do Multi-Agent LLM Systems Fail?](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html), NeurIPS 2025; nghiên cứu thực nghiệm từ trace có gán nhãn. Xem [Phụ lục A](https://arxiv.org/html/2503.13657v3#A1) để đối chiếu FM-3.3. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Phân tích trace của tác giả nhận diện 14 kiểu lỗi theo ba nhóm, trong đó có nhóm kiểm chứng nhiệm vụ. FM-3.3 mô tả việc kiểm tra chéo thông tin hoặc quyết định quan trọng không đầy đủ. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | MAST-Data gồm hơn 1.600 trace từ bảy framework, có các tác vụ lập trình, toán và agent tổng quát. Nguồn không đo hoàn phí LogiX-VN hay chi phí MockLLM; ở đây chỉ dùng taxonomy để diễn giải lỗi quan sát được. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nếu không cho kết quả parse delay ghi đè dữ liệu đơn, dự kiến sửa một lần sai của C-002 seed 55: pass rate tăng khoảng 1,43 điểm phần trăm (69/70 → 70/70), pass^5 tăng 13/14 → 14/14, variance về 0. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cùng swarm, world, MockLLM, tool registry, 14 claim public, năm seed, bảng giá và evaluator. Biến duy nhất: dữ kiện delay lấy từ ticket có thể ghi đè hay không. Patch chỉ tác động đến binding của parser ở module swarm, không tác động lời gọi MockLLM nội bộ, file nguồn hay policy host. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | T02 gần với FM-3.3: đã đọc order nhưng chấp nhận 5 ngày từ ticket dù order ghi 2. So trạng thái/ledger với nhãn, rồi đối chiếu pass rate, pass^5, variance và cost/success giữa hai lượt. |

## Kết quả ablation

Lệnh đã chạy trong `src/` (với Python trong venv):

```bash
python - <<'PY'
from unittest.mock import patch
from lab8.benchmark import main

with patch("lab8.shapes.swarm_reference.parse_delay_days", return_value=None):
    raise SystemExit(main([
        "--shapes", "swarm",
        "--cases", "data/public_claims.jsonl",
        "--seeds", "11,22,33,44,55",
        "--out", "reports/ablation_swarm_no_override.json",
    ]))
PY
```

- Run id / file report: `R-swarm-C-002-s55` trong [benchmark gốc](../../src/reports/benchmark.json) và [báo cáo ablation](../../src/reports/ablation_swarm_no_override.json). Hai lần chạy giữ cùng shape, claim và seed nên trùng run id; file report phân biệt hai lượt.
- Kết quả: đúng với dự đoán trên bộ public. T02 seed 55 đổi từ `resolved` sai sang `denied` đúng, 69 trial còn lại giữ kết quả pass. Pass rate 98,57% → 100%; pass^5 92,86% → 100%; variance 0,000816 → 0; cost/success 49,57 → 48,72 VND mô phỏng. Khi không override, T02 không cần tính lại quote và cũng không trả refund.
- Giới hạn: chỉ cô lập một hành vi của swarm trên fixture public. Không tách riêng hiệu ứng topology của bốn shape và không suy ra hiệu quả trên hidden hay model sản xuất; latency là `unavailable`.
