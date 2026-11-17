# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: TranHaiLong (L3A)
- Thành viên: Trần Hải Long — 2A20263891
- Commit chốt dùng để chấm: `6ff4325` (trùng [ADR](decision_adr.md))

## 2. Mục tiêu và cách tiếp cận

Xử lý cùng một claim vận chuyển bằng bốn kiến trúc để tìm phương án ít tự chủ nhất vẫn đáp ứng luật nghiệp vụ. Nhóm một người kiểm tra starter và swarm tham chiếu, triển khai lần lượt workflow, single và orchestrator, kiểm tra lại ledger/trace khi có lỗi, sau đó chạy benchmark trên cùng dữ liệu và seed. Swarm giữ nguyên để làm đối chứng.

## 3. Giải pháp

| Shape | Thu thập bằng chứng | Quyết định |
| --- | --- | --- |
| Workflow | Đọc claim qua `get_claim_view` và đơn qua `lookup_order` theo principal thật | Chuỗi bước Python cố định, không gọi model |
| Single | `run_react(max_steps=8, worker=True)`; MockLLM chọn thứ tự giữa hai lượt đọc order/policy, rồi code dừng khi đủ dữ kiện hoặc đơn không truy cập được | Tập action chỉ đọc; mã đơn và principal lấy từ claim, không lấy từ ticket hoặc model |
| Orchestrator | `make_handoff` tạo `handoff.v1` chỉ chứa metadata đã lọc và hai tool đọc `lookup_order`/`lookup_policy`; runner cung cấp phạm vi principal từ host | Investigator không có tool ghi; orchestrator dùng order view đã kiểm tra để tính quote |

Cả ba shape dùng `compute_compensation` để áp dụng policy có hiệu lực và lấy giá trị lớn nhất giữa các quyền lợi hợp lệ. Thiếu mã đơn thì hỏi thêm; đơn không tồn tại hoặc không thuộc principal thì chuyển xử lý; quote bằng 0 thì từ chối ngay. Quote dương được gửi **đầy đủ** vào `durability.issue_refund`. Host kiểm approval gắn với claim, số tiền đã trả và phần đã hoàn theo đơn. Nếu shape tự trừ tiền đã hoàn thì host sẽ trừ hai lần (T14). Host ghi refund và audit trong cùng giao dịch; retry dùng khóa `refund:{claim_id}`. Checkpoint giúp resume nhưng ledger mới quyết định khoản nào đã được ghi.

Trace ghi các thao tác đọc, kết quả kiểm phạm vi, quote và trạng thái cuối; single thêm action đọc, orchestrator thêm handoff đã lọc. Trace không chép raw claim/order, ticket, principal thô, header, secret, SĐT, địa chỉ, ghi chú nội bộ, tên hàng hay nội dung model. RunResult và trace đều dùng lý do đã chuẩn hóa khi dữ liệu trạng thái trong DB không hợp lệ.

## 4. Kết quả

[Benchmark](../../src/reports/benchmark.json): 14 claim × 5 seed (11, 22, 33, 44, 55) × 4 shape = 280 trial. Mỗi trial có SQLite mới, dùng cùng policy, bảng giá và evaluator. Steps là số event trace.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | VND mô phỏng/success | Mean / p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Workflow | 70/70 (100%) | 14/14 | 100%–100% | 0 | 34,29 | 4,43 / 5 |
| Single | 70/70 (100%) | 14/14 | 100%–100% | 0 | 43,99 | 8,11 / 9 |
| Orchestrator | 70/70 (100%) | 14/14 | 100%–100% | 0 | 52,86 | 6,29 / 7 |
| Swarm | 69/70 (98,57%) | 13/14 | 92,86%–100% | 0,000816 | 49,57 | 2,80 / 3 |

[Crash suite](../../src/reports/crash.json): **20/20**. Ma trận public xác nhận retry T11 và crash/resume T12 trên cả bốn shape. Test riêng kiểm thêm crash trước effect, sau checkpoint, xung đột khi số tiền đổi lúc retry và approval của claim khác. Workflow có 0 trial public tạo refund khi approval không hợp lệ và 0/70 trace public có canary. Hidden pack chưa có nên chưa tính pass rate hidden.

[ADR](decision_adr.md) chọn workflow. [Research card](research_card.md) kiểm tra vì sao swarm hỏng T02: tắt đường cho phép delay trong ticket ghi đè order đưa swarm từ 69/70 lên 70/70 nhưng không giảm chi phí xuống mức workflow.

## 5. Khó khăn và cách xử lý

- Môi trường: `python3 --version` của shell trả `Python 3.9.6`, thấp hơn phiên bản lab yêu cầu. Tạo venv bằng `uv venv --python 3.13 .venv`, cài `requirements.txt` và chạy lại smoke.
- Độ bền: `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2`. Ba shape chuyển tiếp `crash_at` cho host và để lỗi crash thoát ra. Các test chạy lại trên cùng DB để kiểm tra ledger và audit.
- Rò rỉ: review phát hiện helper quote/approval có thể đưa giá trị trạng thái bất thường từ DB vào lý do lỗi. Chuẩn hóa lý do trước khi trả kết quả hoặc ghi trace; `test_malformed_status_is_not_copied_to_trace` kiểm tra cả hai trường hợp.

## 6. Tổng hợp đóng góp

Xem [TEAM.md](../../TEAM.md) và [báo cáo cá nhân](2A20263891_TranHaiLong.md) về commit, test và hỗ trợ AI.

## 7. Hạn chế và hướng cải thiện

MockLLM không đại diện cho model sản xuất, chi phí là mô phỏng, latency là `unavailable`. Bộ public nhỏ; trace cũng có mức chi tiết khác nhau giữa các shape, nên số event không đo trực tiếp lượng công việc hay thời gian. Bước tiếp theo là xác nhận trên hidden có nhãn; chỉ thử đổi kiến trúc nếu nhiệm vụ thực sự cần thêm nguồn dữ liệu hoặc có bằng chứng tăng chất lượng đủ bù chi phí.

## 8. Tài liệu tham khảo

- [Luật nghiệp vụ](../../docs/business_rules.md), [contract](../../docs/contracts.md), [định nghĩa metric](../../docs/metrics.md) và [lệnh tái lập](../../src/reports/README.md) của lab.
- Cemri và cộng sự, [Why Do Multi-Agent LLM Systems Fail?](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html), NeurIPS 2025.
