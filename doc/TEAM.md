# Nhóm thực hiện K4 Track 3B

Tên nhóm: DoHoangNamKhanh (bài cá nhân)

Repo chung: K4-L3-DAY24-DoHoangNamKhanh-02423

Trưởng nhóm/người nộp: Do Hoang Nam Khanh - 2A202602423

Ngày lab/deadline áp dụng: 2026-10-12 - Asia/Ho_Chi_Minh (UTC+07:00)

Commit đang được chấm: nhánh main, commit mới nhất của repo bài nộp.

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Do Hoang Nam Khanh | 2A202602423 | Phase A/B/C, tích hợp pipeline m1-m5, viết report | artifacts/ragas_50q.json, judge_results.json, guard_results.json; doc/reports/*.md |

Người tích hợp/chạy batch/nộp link: Do Hoang Nam Khanh - chạy setup_answers, ba phase live và nộp link repo.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows, Python 3.12 (starter ghi mục tiêu 3.11), không có MSVC nên không build được annoy.

Virtualenv/dependencies/imports: venv tại .venv; đã cài presidio, spacy, nemoguardrails 0.10.0, ragas 0.1.22, sentence-transformers, qdrant-client, torch CPU. Không cài được annoy nên dùng shim thuần Python cho AnnoyIndex trong venv (chỉ môi trường, không nộp).

Models/Qdrant/50 answers đã chuẩn bị: Qdrant v1.9.7 chạy qua infra/docker-compose.yml; bge-m3 và bge-reranker-v2-m3 lấy từ cache; sinh 50 answers thật lưu ở artifacts/answers_50q.json. Giới hạn: reranker cross-encoder không load được do xung đột NumPy/pyarrow nên dùng lexical fallback; enrichment chunk tắt để tiết kiệm chi phí.

## INDIVIDUAL

### DoHoangNamKhanh-2A202602423

- Phần được giao và phần thực tế đã làm: implement Tasks 1-12 trong src/phase_a_ragas.py, src/phase_b_judge.py, src/phase_c_guard.py; viết adapter src/m4_eval.py và src/llm.py; tích hợp m1-m5; chạy Phase A/B/C live; điền ba report và TEAM.
- Bằng chứng: artifacts/answers_50q.json, artifacts/ragas_50q.json, artifacts/judge_results.json, artifacts/guard_results.json; doc/reports/failure_clusters.md, bias_report.md, blueprint.md.
- Cách kiểm tra: pytest tests/ (86 passed, 3 deselected); python scripts/check_lab.py; chạy live từng phase bằng run_experiments.py --phase a|b|c --live.
- Điều đã học: masking/đóng băng baseline, llm-as-judge swap-and-average và Cohen kappa, guardrail hai tầng Presidio + NeMo, đo latency percentile nội suy tuyến tính và giới hạn của phép đo input layers.
- Giới hạn/cách xử lý: Muse Spark 1.3 chỉ có trên Responses API nên generation/judge dùng client Responses còn NeMo dùng model chat/completions mimo-v2.6-flash; NeMo mặc định max_tokens=3 khiến model trả rỗng và chặn nhầm clean, đã sửa bằng max_tokens 200 trong guardrails/config.yml.
- Nguồn/AI hỗ trợ nếu có: dùng trợ lý AI để soạn scaffolding và gỡ lỗi môi trường; mọi số liệu trong report lấy từ artifacts chạy thật.

## Cập nhật sau khi nộp

Không có cập nhật sau deadline.
