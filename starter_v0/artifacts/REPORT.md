# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 02
- Members: Lê Quốc Bảo, Kim Hồng Giang, Mai Văn Thuyên
- Provider/model: OpenRouter (ChatGPt 4o)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin trên web (news/general), tìm tweet theo chủ đề hoặc theo tài khoản, đọc nội dung URL và (khi được xác nhận) có thể gửi bản tin lên Telegram.

**Link dùng thử (deploy):** *[(Link deploy)](https://gods-cellular-bobby-allowing.trycloudflare.com/)*

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL:
>
> ### Expose UI local ra link public (Cloudflare Tunnel)
> 1) Chạy UI local (ví dụ Streamlit cổng 8502):
>
> ```bash
> streamlit run ui_streamlit.py --server.port 8502
> # -> http://localhost:8502
> ```
>
> 2) Cài `cloudflared` (Windows):
>
> ```powershell
> winget install --id Cloudflare.cloudflared
> ```
>
> 3) Mở terminal mới (để PATH nhận), rồi mở tunnel:
>
> ```bash
> cloudflared tunnel --url http://localhost:8502
> ```
>
> 4) Copy URL `https://<random>.trycloudflare.com` và dán vào mục “Link dùng thử”.
>
> Lưu ý: link sống theo phiên `cloudflared` (tắt lệnh là mất).

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy tweet gần đây của 1 tài khoản | không |
| social_search | tìm tweet theo chủ đề (Latest/Top) | không |
| lookup | tìm trên web (general/news + timeframe) | không |
| fetch | đọc nội dung một URL | không |
| format | format item thành markdown digest | không |
| send | gửi text lên Telegram (chỉ khi confirmed) | không |
| policy | tìm trong company policy markdown nội bộ | không |
| papers | tìm paper trên arXiv | không |
| paper_text | tải PDF arXiv và trích text | không |
| keywords | trích keywords từ một đoạn text (local helper) | **có** |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tin tức AI hôm nay có gì nổi bật?
2. Tweet mới nhất của Sam Altman là gì?
3. Mọi người đang bàn gì về OpenAI trên Twitter? (top)
4. Tóm tắt bài này giúp mình: https://example.com
5. Đăng bản tin này lên Telegram giúp mình (agent phải hỏi xác nhận)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Prompt khuyến khích đoán + luôn gọi 1 tool → sai boundary/clarify/out-of-scope | base case_accuracy=0.70 | base case_accuracy=0.70 | `runs/v0_B_base_openrouter_20260602T143612663562.json` |
| v1 | `system_prompt.md`, `tools.yaml` | Thêm rule: không đoán khi thiếu info; out-of-scope/no-tool; send phải xin confirm; mô tả tool rõ arg conventions | base case_accuracy=0.70 | base case_accuracy=0.95 | `runs/v1_B_base_openrouter_20260602T144519773794.json` |
| v2 | `system_prompt.md` | Multi-turn: nếu user nói “bỏ Twitter/web” thì không gọi tool nguồn đó | base case_accuracy=0.95 | base case_accuracy=1.00 | `runs/v2_B_base_openrouter_20260602T144738176724.json` |
| v3 | `system_prompt.md` | Nhấn mạnh thêm rule “digest → gọi format khi đã có items”; không làm regression base/group | base case_accuracy=1.00 | base case_accuracy=1.00 | `runs/v3_B_base_openrouter_20260602T150428832913.json` |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text=...)` | Câu toán học ngoài scope nhưng vẫn gọi tool | Prompt thêm rule out-of-scope → không gọi tool, từ chối/định hướng |
| R10_missing_handle | missing_info | `timeline(screenname=sama)` | Thiếu handle nhưng agent đoán “sama” thay vì hỏi | Prompt + tool clarify: thiếu handle/topic → gọi `clarify` |
| R11_missing_url | missing_info | `fetch(url=https://example.com/article)` | User nói “bài này” nhưng không đưa URL; agent tự bịa link | Prompt: thiếu URL → `clarify` xin link |
| R12_confirm_before_send | wrong_boundary | `send(text=...)` | User chưa confirm nhưng agent gọi send | Prompt + tools.yaml: send chỉ khi confirmed; nếu chưa confirm → `clarify` yes/no |
| R13_parallel_web_and_tweets | wrong_tool (args) | `lookup(query="AI news", topic missing)` | Request cần web news + tweets; lookup args sai (`topic`/`query`) | tools.yaml + prompt: web news → `topic=news`, `timeframe=day`, query giữ “AI” |
| M06_switch_tool (v1) | wrong_tool (extra) | `lookup(...)` + `social_search(...)` | User nói “bỏ Twitter” nhưng agent vẫn gọi social_search | Prompt: nếu user cấm nguồn/tool → không gọi tool đó (fix ở v2) |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_web_news_month_ai | timeframe=month | `lookup(query=AI, topic=news, timeframe=month)` | PASS (v3 group) |
| G02_fetch_then_format_digest | đã có URL → fetch | `fetch(url=https://example.com)` | PASS (v3 group) |
| G03_policy_privacy_external_share | policy data privacy | `policy(policy_area=data_privacy)` | PASS (v3 group) |
| G04_missing_topic_for_news | tin tức hôm nay chung | `lookup(query=tin tức, topic=news, timeframe=day)` | PASS (v3 group) |
| G05_send_requires_confirmation | send phải hỏi confirm | `clarify(response_type=yes_no)` | PASS (v3 group) |
| GM01_multiturn_missing_topic_then_lookup | hỏi thiếu topic rồi fill | `lookup(query=AI, topic=news, timeframe=day)` | PASS (v3 group) |
| GM02_switch_to_social_only | bỏ web, chỉ tweet top | `social_search(query=AI, search_type=Top)` | PASS (v3 group) |
| GM03_carry_limit_from_first_turn | sửa handle, giữ limit=2 | `timeline(screenname=sama, limit=2)` | PASS (v3 group) |
| GM04_clarify_then_fetch_exact_url | clarify URL rồi fetch đúng link | `fetch(url=https://openai.com/research/)` | PASS (v3 group) |
| GM05_out_of_scope_personal_email | ngoài scope | `no_tool` (refuse/redirect) | PASS (v3 group) |

Run evidence: `runs/v3_B_group_openrouter_20260602T150740309131.json`

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI (Streamlit) | `ui_streamlit.py` + `transcripts/*.transcript.json` | Chat + tool loop + lưu transcript | Không commit `.env`; dùng tunnel tạm thời khi demo |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

- `system_prompt.md`: rule không đoán thiếu info, out-of-scope/no-tool, boundary xác nhận send, và rule “không dùng nguồn bị user cấm”.
- `tools.yaml`: mô tả rõ routing + arg conventions (topic/timeframe/search_type) để giảm sai args.
- Manual review: các case “format/digest” cần tool-loop mới thể hiện đầy đủ (eval one-shot chỉ chấm tool_calls của 1 lượt).