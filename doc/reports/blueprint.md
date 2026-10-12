# Blueprint CI/CD cho RAG và guardrails

Nhóm: DoHoangNamKhanh (bài cá nhân)

Người phụ trách: Do Hoang Nam Khanh - 2A202602423

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: guard 2026-10-12T08:48:59+00:00; guard models: `mimo-v2.6-flash`.
Models generation/evaluator/judge từ A/B: generation = `muse-spark-1.3-contributor`; evaluator = `deepseek-v4.1-flash` + `BAAI/bge-m3`; judge = `muse-spark-1.3-contributor`; guard = `mimo-v2.6-flash`.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

Data flow: user input trước tiên qua Presidio để phát hiện và redact PII (CCCD/CMND, số điện thoại VN, email); nếu có PII định danh thì chặn ngay. Nếu không, input đi qua NeMo input rail (self-check LLM) để bắt jailbreak, đổi vai, đòi dữ liệu cá nhân/khóa, prompt injection và câu ngoài chủ đề. Input hợp lệ mới vào pipeline RAG (hybrid search + rerank) để sinh câu trả lời. Câu trả lời cuối chạy qua NeMo output rail để chặn/redact PII và nội dung nhạy cảm trước khi trả user. Failure action đề xuất: chặn PII ở tầng Presidio (log entity type, không log giá trị thô); chặn policy ở NeMo (trả câu từ chối chuẩn trong rails.co, log activated rail và lý do); mọi secret/khóa API chỉ nằm phía host, không đưa vào sandbox; khi LLM rail lỗi/timeout thì fail-closed cho input rủi ro và fail-open có cảnh báo cho câu hỏi HR thông thường tùy mức rủi ro.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 18.60 | 30.89 | 33.60 | Đo thật, rất nhanh |
| NeMo input | 4535.93 | 8795.08 | 8847.57 | Đo thật, chậm (LLM rail) |
| Input guard sequential | 4553.42 | 8815.48 | 8863.90 | Đo thật |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: 8815.48ms / False.
Bottleneck là tầng NeMo input vì mỗi lần kiểm tra là một lượt gọi LLM (p50 ~4.5s). Presidio chỉ ~19ms nên không đáng kể. Vì input_guard_ms là tổng tuần tự hai tầng, nó không đại diện cho request thật (vốn short-circuit khi bị chặn) hay RAG/output. Với mục tiêu 500ms, cần thay rail LLM bằng phân loại nhẹ (embedding kNN hoặc model nhỏ chạy local), cache kết quả cho input trùng, và/hoặc chạy rail song song với bước khác. Các phần ngoài phạm vi giữ "chưa đo" và có kế hoạch lấy mẫu khi triển khai (timestamp quanh từng tầng, tách cold/warm, thêm short-circuit để đo trải nghiệm người dùng thật).

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.
Kết quả lần chạy này: attacks 20/20, clean 8/8 (false_positive_rate=0), outputs 4/4 đạt; RAGAS avg_score tổng thể đạt nhưng multi_hop 0.5010 chưa đạt ngưỡng 0.65 nên gate RAGAS cần nhánh riêng theo distribution. Đề xuất lệnh job trả mã lỗi khác 0 khi bất kỳ ngưỡng nào không đạt. Biến MIN_* trong ví dụ chỉ là đề xuất, không tự tạo quality gate nếu runner chưa kiểm tra ngưỡng. Workflow này chưa được triển khai; đây là thiết kế.

## Monitoring và cải tiến

Metric theo dõi: (1) tỉ lệ chặn input/clean (false-positive), (2) phân bố lý do chặn theo rail, (3) P50/P95 latency từng tầng, (4) RAGAS faithfulness/recall trung bình theo distribution, (5) κ giữa judge và người định kỳ. Ngưỡng cảnh báo: false-positive >0.05, attack pass <18/20, input-guard P95 >2s (mục tiêu dài hạn 500ms), faithfulness RAG <0.6. Cách lấy mẫu: log có cấu trúc cho mọi quyết định rail và mọi điểm RAGAS, lưu raw latency samples; sampling user input ẩn danh theo tỉ lệ cố định. Xử lý false positive: tạo hàng đợi review, mỗi case chặn nhầm gán nhãn và đưa vào regression set. Phát hiện drift: so sánh phân bố điểm và tỉ lệ chặn theo tuần; theo dõi version policy trong corpus để bắt version conflict. Privacy: redact PII trước khi log, không log giá trị PII thô, luân chuyển khóa.

Kết quả thật: RAGAS mean tổng thể factual 0.7922, multi_hop 0.5010, adversarial 0.6714; distribution yếu nhất multi_hop; worst metric context_recall. Cohen’s κ: 1.0 trên 10 mẫu. Attacks passed: 20/20; clean false_positive_rate: 0.0.
Năm câu cải tiến có thể kiểm tra: (1) bật enrichment + cross-encoder rerank và đo lại context_recall multi_hop; (2) tăng RERANK_TOP_K và thêm query decomposition cho câu multi_hop; (3) thay NeMo input LLM bằng phân loại nhẹ để kéo P95 latency xuống dưới ngân sách; (4) bổ sung clean set đa dạng hơn để theo dõi false-positive; (5) chấm chéo bằng judge khác họ model để kiểm tra κ có vững khi đổi judge.
