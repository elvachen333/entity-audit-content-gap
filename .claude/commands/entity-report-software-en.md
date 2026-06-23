Generate a copywriting strategy report in English, tailored for B2B software / SaaS content targeting ecommerce and Shopify merchants.

## Steps

1. Find the most recently modified `summary.json` under any `third_step_google_entity_analysis/results/` folder in this project. Also find the matching `cited_winning_entities.csv` in the sibling `charts/` folder.

2. Read both files fully. Also find the most recently modified `serp_*.json` in the sibling `first_step_aio_seo/` folder to identify the keyword.

3. Analyse the data and write a **copywriting strategy report in English** saved to the sibling `fourth_step_conclusion/` folder as `copywriting_report_en_<keyword>.md`.

## Report structure

Write the report as a senior content strategist briefing a B2B SaaS copywriting team. Be opinionated and specific — translate data signals into concrete content decisions, not generic SEO advice.

### Section 1 — Key Insights (3–5 bullet points)
State the most important findings in plain English. Interpret what the entity patterns reveal about *search intent* and *content format* — e.g. "Cited pages are product comparison articles, not how-to guides" or "Pricing specificity separates cited from non-cited pages."

### Section 2 — Must-Write vs. Skip
Two clear columns:
- **Must-Write**: entity types where cited coverage lift > 1.05x — explain *why* each matters specifically for this software/SaaS topic and what it implies about content depth
- **Skip / Don't Over-stuff**: entity types with lift < 0.95x — explain the signal (e.g. "readers aren't looking for personal stories here")

For density lift outliers (> 3x), call them out separately — they reveal where cited pages go *much deeper* than non-cited ones.

### Section 3 — Specific Entity Vocabulary List
From `top_named_entity_gaps`, group meaningful named entities by type (skip bare numbers, single letters, generic UI labels like "copy link"). For each group:
- List the entities with cited% / non-cited% / lift
- Write one sentence on what content angle this implies (e.g. "These are specific product names → each needs its own dedicated section with feature breakdown, pricing, and use-case fit")

Focus especially on:
- Named software tools / brands (CONSUMER_GOOD / PERSON)
- Specific features and capabilities (OTHER / CONSUMER_GOOD)
- Pricing tiers and numbers (PRICE / NUMBER)
- Geographic markets and platform integrations (LOCATION / ORGANIZATION)

### Section 4 — Recommended Article Structure
Based on entity patterns, propose a concrete article outline with actual section headings tailored to this keyword. Make it ready to hand to a writer — specific H2s and H3s, not abstract descriptions. Reflect the SaaS comparison/review format if that's what the data suggests.

### Section 5 — Pre-Submission Checklist
A checkbox list (- [ ] items) the writer ticks before submitting. Maximum 10 items, most important first. Make each item concrete and testable — not "include pricing" but "every tool reviewed has a pricing table with at least 2 plan tiers listed."

## Tone & style
- Write entirely in English
- Consultative and direct — tell the writer what to do, not what the data shows
- Use the entity lift data as evidence to support recommendations, not as the main point
- For SaaS/software topics: emphasise product specificity (named tools, exact pricing, feature names, supported integrations, geographic availability)
- Always note the cited vs non-cited doc count so the team can calibrate confidence in the findings
