# Day 04 Lab v2 Report — Research Agent

## Team

- Team: Group AI Thực Chiến
- Members: Mai Văn Thuyên (2221050712)
- Provider/model: gemini / gemini-3.1-flash-lite

## Final Metrics

- Final version: v3
- Final artifact_version: v3+pd64e7a0765a5+t3cb6b27e06b4
- Best base run file: runs/v1_B_base_gemini_20260602T154259177401.json
- Base case accuracy: 0.75
- Base tool routing accuracy: 1.0
- Base argument accuracy: 0.75
- Group eval run file: runs/v3_B_group_gemini_20260602T164024749956.json
- Group eval accuracy: 0.80
- Chat transcript file: transcripts/v3_gemini_...transcript.json (Xem trong folder transcripts)

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi chưa tối ưu trước khi sửa | N/A | 0.66 | runs/v0_B_base_gemini_20260602T135641886768.json |
| v1 | system_prompt.md | Thêm rule clarify(yes_no) sẽ chặn được lỗi tự ý gửi tin (wrong_boundary). | 0.66 | 0.75 | runs/v1_B_base_gemini_20260602T154259177401.json |
| v2 | app.py, tools.yaml | Xây dựng tool weather và sửa lỗi Invalid Argument do JSON format của SDK. | 0.75 | 0.80 | runs/v2_B_group_gemini_20260602T161210119826.json |
| v3 | eval_group.json | Thêm 7 cases mở rộng sẽ test bao phủ toàn bộ Multi-turn và Out-of-scope. | 0.80 | 0.80 | runs/v3_B_group_gemini_20260602T164024749956.json |

## Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | lookup(query="AI news") | Agent tự nối thêm chữ "news" vào query | Thêm rule giữ nguyên query gốc |
| R10_missing_handle | missing_info | clarify() | Thiếu field response_type="text" | Nhấn mạnh response_type trong prompt |
| R12_confirm_before_send | wrong_boundary | send() | Tự gửi tin mà không hỏi | Bắt buộc dùng clarify(yes_no) |

## Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G03_weather_multiturn_carryover | Đổi địa điểm trong ngữ cảnh thời tiết nhiều lượt. | weather(city="Sài Gòn") | PASS |
| G04_out_of_scope_math | Từ chối giải toán (nằm ngoài phạm vi). | no_tool (refuse) | PASS |
| G07_multiturn_weather_to_news | Đổi tool đột ngột từ weather sang lookup trong multi-turn. | lookup(topic="news") | PASS |
| G08_multiturn_clarify_then_send | User xác nhận gửi -> tool send phải có confirmed=true. | send(confirmed=true) | PASS |
| G10_multiturn_missing_url | Nhớ url ở lượt 2 và map vào fetch. | fetch(url) | PASS |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Streamlit UI | app.py | Chạy mượt mà, render text kết hợp thông tin tool tự nhiên. | Bị lỗi 400 Bad Request lúc đầu, khắc phục bằng mô phỏng System Context. |
| Custom Tool | tools/weather/tool.py | Tự viết tool lấy thời tiết, Agent route chuẩn xác. | Agent có xu hướng dùng default param nếu không ép. |

## Reflection

- **Which fixes belonged in `system_prompt.md`?** Việc cấm đoán (`CẤM dùng social_search cho tin tức`) và thiết lập rào chắn an toàn (bắt buộc dùng `clarify(yes_no)`) giải quyết triệt để trong System Prompt.
- **Which fixes belonged in `tools.yaml`?** Mô tả parameter chi tiết và enum ràng buộc giúp Agent nhận diện đúng tham số (ví dụ: topic="news").
- **What would you improve next?** Cải thiện tham số default trong các tool để bắt Agent hỏi lại (clarify) thay vì tự động điền dữ liệu mặc định.