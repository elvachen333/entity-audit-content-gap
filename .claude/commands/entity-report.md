Generate a copywriting strategy report from the latest entity analysis results.

## Steps

1. Find the most recently modified `summary.json` under any `third_step_google_entity_analysis/results/` folder in this project. Also find the matching `cited_winning_entities.csv` in the sibling `charts/` folder.

2. Read both files fully. Also find the most recently modified `serp_*.json` in the sibling `first_step_aio_seo/` folder to identify the keyword.

3. Analyse the data and write a **copywriting strategy report in Traditional Chinese** saved to the sibling `fourth_step_conclusion/` folder as `copywriting_report_<keyword>.md`.

## Report structure

Write the report as a consultant briefing your copywriting team. Be specific and opinionated — don't just describe the numbers, tell them exactly what to do.

### Section 1 — 關鍵洞察（3–5 bullet points）
State the most important findings in plain language. Example: "被引用頁面幾乎都包含完整地址，非引用頁面只有三分之二有，這是最容易改進的差距。"

### Section 2 — 必寫 vs 可省
Two columns: entity types the team MUST include (coverage lift > 1.05x) and types they should NOT over-stuff (lift < 0.95x). For each must-have type, explain *why* it matters for this specific keyword topic.

### Section 3 — 具體詞彙清單
From `top_named_entity_gaps`, list the specific named entities (filtered to meaningful ones — skip bare numbers, single characters, and generic UI words like 首頁) grouped by entity type. For each group, write one sentence explaining what kind of content this implies (e.g. "these are specific venue names → the article should review each venue individually, not just list them").

### Section 4 — 文章架構建議
Based on the entity pattern, recommend a concrete article structure (section headings) that would naturally incorporate the high-lift entities. Make it specific to the keyword topic.

### Section 5 — 撰寫檢查清單
A checkbox list (- [ ] items) the writer ticks before submitting. Maximum 10 items, most important first.

## Tone
- Write in Traditional Chinese throughout
- Be direct and actionable, not academic
- Use the entity data as evidence, not as the main point — the main point is always "here's what to write"
- Sample size note: always mention the cited vs non-cited doc count so the team knows how confident to be in the findings
