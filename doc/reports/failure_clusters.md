# Phân tích lỗi Phase A

Nhóm: DoHoangNamKhanh (bài cá nhân)

Người phụ trách: Do Hoang Nam Khanh - 2A202602423

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T08:29:07+00:00.
Generation mode/fallback và điều kiện chạy: generation dùng Muse Spark 1.3 qua Responses API (generation_mode=llm cho cả 50 câu); enrichment chunk bị tắt để tiết kiệm chi phí nên không có LLM call khi index; reranker cross-encoder không load được (xung đột NumPy/pyarrow) nên dùng lexical fallback.
Models generation/evaluator: generation = `muse-spark-1.3-contributor`; evaluator = `deepseek-v4.1-flash` (RAGAS LLM judge) + `BAAI/bge-m3` (embeddings, chạy local).

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.8500 | 0.4905 | 0.8500 |
| answer_relevancy | 0.7770 | 0.4969 | 0.7854 |
| context_precision | 0.8167 | 0.6583 | 0.7417 |
| context_recall | 0.7250 | 0.3583 | 0.3083 |
| avg_score | 0.7922 | 0.5010 | 0.6714 |

## Bottom 10 và nguyên nhân

| rank | id | distribution | avg_score | worst_metric | diagnosis | suggested_fix | question |
|---|---|---|---|---|---|---|---|
| 1 | 5 | factual | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt |
| 2 | 6 | factual | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Thông tin lương thuộc cấp độ phân loại dữ liệu nào |
| 3 | 7 | factual | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Nghỉ phép không lương 20 ngày cần ai phê duyệt |
| 4 | 22 | multi_hop | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Mua laptop 30 triệu cho nhân viên mới: ai phê duyệt và cần gì từ CNTT |
| 5 | 33 | multi_hop | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Manager thâm niên 12 năm: phụ cấp tháng và phép năm v2024 |
| 6 | 34 | multi_hop | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Tạm ứng 4 triệu và 7 triệu khác nhau quy trình thế nào |
| 7 | 40 | multi_hop | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Manager thử việc 90 ngày vi phạm bảo mật nên và không nên làm gì |
| 8 | 47 | adversarial | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Phát hiện malware có nên tự xử lý không |
| 9 | 27 | multi_hop | 0.2500 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Thâm niên 7 năm v2024 nghỉ bao nhiêu ngày, trừ 4 ngày ốm còn lại bao nhiêu |
| 10 | 26 | multi_hop | 0.3333 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature | Vừa kết hôn và cùng tuần có con kết hôn: tổng ngày nghỉ đặc biệt có lương |

Đối chiếu answer/contexts/reference cho thấy 8/10 câu đáy có `answer = "Không tìm thấy."`. Nguyên nhân không nằm ở generation mà ở **retrieval**: contexts lấy về lạc chủ đề. Ví dụ câu 5 (mua thiết bị 55 triệu) nhận context về "đăng ký khóa học qua Learning Portal"; câu 22 (laptop 30 triệu) nhận context về "tài trợ chi phí đào tạo bên ngoài"; câu 33 (phụ cấp Manager) nhận context về "cách tính ngày phép theo năm dương lịch". Khi context không chứa bằng chứng, generation theo đúng chỉ dẫn "chỉ trả lời dựa trên context" nên trả "Không tìm thấy.", khiến faithfulness = 0 (không có statement nào) và answer_relevancy = 0. Câu 27/26 có context_precision cao (0.99 / gần 0) nhưng context_recall = 0 vì đoạn lấy về đúng cụm nhưng thiếu điều kiện version/thâm niên cần cho đáp án. Đây là lỗi retrieval (recall) chứ không phải lỗi prompt generation.

## Matrix và nhóm yếu nhất

Matrix đếm worst_metric của mọi câu (không coi mọi câu là failure):

| worst_metric | factual | multi_hop | adversarial | total |
|---|---|---|---|---|
| faithfulness | 3 | 11 | 1 | 15 |
| answer_relevancy | 11 | 2 | 0 | 13 |
| context_precision | 2 | 2 | 1 | 5 |
| context_recall | 4 | 5 | 8 | 17 |

Nhóm yếu theo mean thấp nhất: multi_hop; mean: 0.5010.
Worst metric xuất hiện nhiều nhất: context_recall; số câu: 17.

Tổng theo cột là kích thước nhóm (20/20/10), không đo chất lượng; nhóm yếu được chọn theo avg_score trung bình thấp nhất nên multi_hop (0.5010) yếu hơn adversarial (0.6714) và factual (0.7922). Multi_hop yếu vì cần gộp bằng chứng từ nhiều tài liệu (phép năm + phụ cấp + quy trình phê duyệt) mà retrieval chỉ trả về 3 chunk không chứa đủ mảnh, và pipeline không enrich/không rerank mạnh nên recall thấp. context_recall chiếm ưu thế (17/50) cho thấy nút thắt chính là **retrieval thiếu evidence**. Đề xuất: bật enrichment + cross-encoder rerank, tăng `RERANK_TOP_K`, và thêm truy vấn theo nhiều bước (decompose) cho câu multi_hop. Chạy lại `--phase a --live` sau khi sửa và so sánh avg_score theo distribution để biết có hiệu quả.

## Bẫy adversarial và giới hạn

adversarial mean = 0.6714 thấp hơn factual mean = 0.7922 (đủ điều kiện phân tích bẫy), nhưng cao hơn multi_hop. Điểm thấp của adversarial tập trung ở context_recall (8/10 câu có worst_metric là context_recall, trung bình 0.3083): các câu chứa phiên bản cũ/mới (v2023 vs v2024) và phủ định ("không nên tự xử lý") cần đúng đoạn policy; retrieval trả sai phiên bản nên answer dễ sai. Điểm thấp hơn **không tự chứng minh** pipeline đã nhận diện được bẫy version/negation; muốn khẳng định phải đọc thủ công từng câu và đối chiếu reference. Giới hạn: 50 câu (adversarial chỉ 10), một lượt chạy, generation/enrichment phụ thuộc provider bên thứ ba và embedding local bge-m3; kết quả có thể khác khi bật lại enrichment và reranker.
