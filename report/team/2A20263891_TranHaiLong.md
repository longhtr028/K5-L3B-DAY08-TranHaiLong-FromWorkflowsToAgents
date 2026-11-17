# Báo cáo cá nhân — Trần Hải Long

## 1. Thông tin thành viên

- Họ tên: Trần Hải Long
- MSSV: 2A20263891
- Email: Không công khai
- GitHub: [longhtr028](https://github.com/longhtr028)

## 2. Phần việc phụ trách

Thành viên duy nhất của nhóm. Phạm vi bài gồm ba shape Python, kiểm thử ranh giới an toàn, chạy lại swarm tham chiếu, benchmark, ablation và báo cáo.

## 3. Đóng góp cụ thể

- Commit kỹ thuật: `6ff4325`. Ba shape dùng chung bước tính quote và giao việc ghi ledger cho host. Single giới hạn ReAct ở tám bước với tool chỉ đọc, orchestrator dùng handoff allowlist.
- [Test tích hợp](../../src/tests/test_student_shapes_safety.py) kiểm approval sai claim dù ticket yêu cầu thanh toán, che dữ liệu nhạy cảm, retry sau crash và giữ nguyên khoản hoàn khi retry gặp số tiền xung đột.
- Quyết định chọn workflow dựa trên độ chính xác ngang single/orchestrator và cost/success thấp hơn trong bộ public.

## 4. Bằng chứng

- `R-workflow-C-007-s11`: quote 35.000 VND, host từ chối và không tạo refund. `R-workflow-C-014-s11`: quote 150.000 VND, ledger 120.000 VND sau khoản cũ 30.000 VND.
- [Benchmark](../../src/reports/benchmark.json), [crash suite](../../src/reports/crash.json), [ADR](decision_adr.md) và [ablation](research_card.md).

## 5. Công cụ AI đã dùng

OpenAI Codex hỗ trợ đọc đề, triển khai các shape, viết test, chạy kiểm tra và soạn báo cáo. Bằng chứng kiểm tra trong repo: so kết quả và trace với ledger trong ma trận public, chạy suite crash và kiểm thử tích hợp, đối chiếu các số trong báo cáo với JSON do công cụ lab tạo. Các kiểm tra này do Codex chạy; báo cáo không xác nhận rằng sinh viên đã chạy lại độc lập.

## 6. Tự đánh giá

Đối chiếu theo bằng chứng trong repo: ba shape đạt mục tiêu public, test bổ sung kiểm tra được các ranh giới ghi tiền và trace, và ADR có số liệu để giải thích quyết định. Kết quả chưa đủ để khẳng định đạt hidden hoặc hiệu năng thực tế. Khi tự chạy lại, ba ca nên kiểm tra là T14 (quote đầy đủ), T12 (một refund sau crash) và T02 seed 55 (approval hợp lệ nhưng không đủ quyền lợi).
