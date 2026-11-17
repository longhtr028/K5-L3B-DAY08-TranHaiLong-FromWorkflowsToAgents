# ADR — Chọn workflow cho LogiX-VN

## Quyết định

- Shape chọn: workflow
- Commit hash: 6ff4325
- Run id dẫn chứng: R-workflow-C-002-s55, R-workflow-C-007-s11, R-workflow-C-014-s11
- Pass rate / pass^5 / seed min-max / variance: 70/70 (100%) / 14/14 (100%) / 100%–100% / 0
- Cost per success (mô phỏng, VND): 34,29
- Crash safety: 20/20 (crash suite chính thức; thêm kiểm tra crash/resume trên workflow ở T12 và test tích hợp)
- Secret leak / approval bypass: 0/70 trace public có canary; 0/15 trial public thiếu approval hợp lệ tạo refund. Test tích hợp cũng quét trace, kết quả và stdout/stderr với approval sai claim. Chưa đo trên hidden.

## Vì sao shape này

Trên cùng 14 claim, năm seed và bảng giá, workflow, single và orchestrator đều qua 70/70 trial. Workflow không gọi MockLLM và trả cùng kết quả với ít lượt đọc hơn, nên có cost/success thấp nhất: 34,29 VND, so với 43,99 của single, 52,86 của orchestrator và 49,57 của swarm. Swarm qua 69/70: ở T02 seed 55, nó dùng lời khai trễ 5 ngày thay cho 2 ngày trong hệ thống. Cổng approval vẫn chạy, nhưng approval có sẵn không chứng minh đơn đủ điều kiện hoàn phí.

## Có đáng đổi lấy multi-agent không

Trong bộ public, điều phối thêm không tăng số trial đúng. Có thể cân nhắc orchestrator nếu cần thu thập dữ kiện độc lập từ nhiều hệ thống và kiểm thử có nhãn cho thấy chênh lệch độ chính xác hoặc thời gian đủ bù chi phí. Khi đó cần đo cùng corpus, seed, evaluator và bảng giá, đồng thời giữ nguyên kiểm soát approval, phạm vi truy cập và crash. Ablation ở [research card](research_card.md) bỏ được lỗi T02 của swarm nhưng cost/success vẫn là 48,72 VND, cao hơn workflow.

## Trace và bằng chứng

Workflow ghi kết quả đọc claim, phạm vi truy cập đơn, quote, quyết định host (nếu được gọi) và trạng thái cuối. T02 chứng minh quote dùng ngày trễ trong DB; T07 giữ quote 35.000 VND và host từ chối do approval hỏng; T14 giữ quote 150.000 VND và host chỉ ghi 120.000 VND. Trace không ghi ticket, parent secret, header, principal thô, SĐT, địa chỉ, ghi chú nội bộ, tên hàng, prompt hoặc phản hồi model. Các status lạ từ DB được chuẩn hóa trước khi đưa vào trace/kết quả. Mỗi kết quả trả đường dẫn đến trace vừa ghi với cùng run id. Kiểm thử quét cả kết quả và stdout/stderr; không dùng file debug ngoài phạm vi trace, vì scanner theo run id sẽ không nhìn thấy các file đó.

## Giới hạn

[Benchmark public](../../src/reports/benchmark.json) đo trên dữ liệu giả với MockLLM, giá mô phỏng và latency `unavailable`. [Crash report](../../src/reports/crash.json) là suite host chính thức; T12 và test tích hợp xác minh riêng cách các shape chuyển tiếp điểm crash. Hidden pack không có trong workspace; kết quả public không xác nhận ngưỡng hidden 0,75.
