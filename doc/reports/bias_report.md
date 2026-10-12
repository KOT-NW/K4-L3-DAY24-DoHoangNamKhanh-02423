# Đánh giá LLM Judge Phase B

Nhóm: DoHoangNamKhanh (bài cá nhân)

Người phụ trách: Do Hoang Nam Khanh - 2A202602423

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T08:31:45+00:00.
Models generation/judge: generation = `muse-spark-1.3-contributor`; judge = `muse-spark-1.3-contributor` (qua Responses API).

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| id | winner_pass1 | winner_pass2 | final_winner | position_consistent | scores_pass1 | scores_pass2 |
|---|---|---|---|---|---|---|
| 1 | B | B | B | True | A=0.75 B=0.95 | A=0.60 B=0.90 |
| 5 | A | A | A | True | A=0.30 B=0.00 | A=0.30 B=0.00 |
| 12 | A | A | A | True | A=1.00 B=0.80 | A=0.95 B=0.85 |
| 21 | B | B | B | True | A=0.50 B=1.00 | A=0.50 B=1.00 |
| 41 | A | A | A | True | A=0.90 B=0.20 | A=0.90 B=0.20 |

Position bias count/rate: 0 / 0.0 (0 trên 5 case).
Verbosity win rate: 0.4; decisive cases: 5.

Tóm tắt lý do hai lượt: cặp 1 B đầy đủ hơn (nêu "có lương"); cặp 5 A không bịa còn B sai ngưỡng phê duyệt; cặp 12 A nêu đúng điều kiện "chính thức từ 6 tháng" còn B khái quát thiếu điều kiện; cặp 21 B nêu đủ cả phép lẫn khung lương; cặp 41 A dùng đúng phiên bản v2024 (15 ngày) còn B dùng chính sách v2023 đã bị thay thế (12 ngày). Cả 5 cặp đều nhất quán sau khi hoán đổi thứ tự, nên không case nào là position bias. Không có case không nhất quán (final_winner luôn khác "tie"). Verbosity: trong 5 case decisive, chỉ 2 lần winner có câu dài hơn (a_wins_a_longer=1, b_wins_b_longer=1) nên win rate theo độ dài 0.4 < 0.6, chưa đủ dấu hiệu thiên vị độ dài. Lưu ý đây là dấu hiệu thống kê trên 5 mẫu rất nhỏ, không đủ để kết luận nhân quả; muốn khẳng định phải đọc nội dung từng cặp.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| question_id | model_answer | judge_label | reasoning | human_label | agree |
|---|---|---|---|---|---|
| 1 | Nghỉ 3 ngày làm việc có lương khi kết hôn | 1 | Đúng ý thiết yếu, khớp reference | 1 | True |
| 5 | Cần Giám đốc phòng ban phê duyệt | 0 | Vượt ngưỡng 50 triệu nên phải CEO, answer sai | 0 | True |
| 12 | Thưởng Tết tối thiểu 1 tháng lương | 1 | Đúng mức tối thiểu, khớp reference | 1 | True |
| 21 | Nghỉ 18 ngày phép và lương Senior | 1 | Đủ 2 ý thiết yếu (18 ngày và 20-35 triệu) | 1 | True |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm | 1 | Đúng số tiền và điều kiện cam kết | 1 | True |
| 29 | Trưởng phòng phê duyệt, phạt 2% tháng | 0 | Thiếu Kế toán trưởng và tính sai phí phạt | 0 | True |
| 33 | Phép 19 ngày, phụ cấp 1.500.000 | 1 | Đủ 2 ý, đúng phiên bản v2024 | 1 | True |
| 41 | Nghỉ 12 ngày phép năm | 0 | Dùng chính sách v2023 cũ thay vì v2024 | 0 | True |
| 46 | Thử việc không được nghỉ phép năm | 1 | Giữ đúng phủ định, đủ ý thiết yếu | 1 | True |
| 50 | Được, miễn là kết nối an toàn | 0 | Đảo phủ định, reference cấm VPN cá nhân | 0 | True |

Cohen’s κ: 1.0.
Observed/chance agreement: observed = 10/10 = 1.0; judge có 6 nhãn 1 và 4 nhãn 0, human cũng 6/1 và 4/0 nên chance = (6/10*6/10) + (4/10*4/10) = 0.52; κ = (1.0 - 0.52) / (1 - 0.52) = 1.0. Nhận xét: judge đồng thuận tuyệt đối với nhãn người trên đúng 10 `model_answer` được cung cấp; judge bám vào version (v2023/v2024), phủ định và các điều kiện (ngưỡng tiền, thâm niên) đúng như tiêu chí 0/1.

## Giới hạn và cách dùng judge

Model/prompt: một judge duy nhất `muse-spark-1.3-contributor` với prompt nhị phân cố định, temperature 0. Cỡ mẫu nhỏ: 5 cặp pairwise và 10 nhãn calibration, trong đó chỉ 2 nhãn human=0 nên κ=1.0 kém ổn định về mặt thống kê dù rất tốt trên mẫu này. Không có case lệch với human trong lần chạy này; nếu có, cần đọc kỹ reference để kiểm chứng thay vì tin judge tuyệt đối. Judge chỉ là một công cụ ước lượng: cùng họ mô hình có thể thiên vị (ở đây judge và generator là cùng một model Muse Spark, có nguy cơ tự ưu ái), và kết quả chỉ có nghĩa cho đúng 10 answer nguồn, không dùng để chấm answer mới của pipeline.
