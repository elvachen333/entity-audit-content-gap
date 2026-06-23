Run the full "All Models in One" pipeline for one set of prompts on a single topic, then author per-model copywriting reports and the cross-platform comparison.

## When to use

Invoke this skill when the user gives you:
- A list of prompts on a shared topic (1 or more)
- A DataForSEO `location_name` (e.g. `"United States"`, `"Taiwan"`, `"Japan"`)
- A DataForSEO `language_code` (e.g. `"en"`, `"zh-TW"`, `"ja"`)
- Optionally, a short topic slug for the run folder

If any of those are missing, ask the user. Format hint to show:

```
Required:
  prompts   pipe-separated, e.g. "Best Shopify shipping apps|Top tracking tools"
  location  DataForSEO location_name string, e.g. "United States"
  language  DataForSEO language_code string, e.g. "en" or "zh-TW"
Optional:
  topic     short slug for the run folder; auto-derived from prompt 1 if omitted
```

## Steps

### 1. Run the pipeline

Execute the standalone Python script via Bash. The script handles all of:
- DataForSEO SERP extract for ChatGPT, Claude, Gemini, AIO (one call per prompt per model)
- Firecrawl scrape of pooled cited + non-cited URLs per model
- Google NLP entity analysis + visualization per model
- AIO abort handling: if no `ai_overview` item OR empty cited URL list, AIO downstream is skipped automatically

Command:

```bash
cd "/Users/elva.chen/Desktop/share-obsidian/entity analysis/All Models in One" && \
python3 pipeline.py \
  --prompts "<pipe-separated prompts>" \
  --location "<location_name>" \
  --language "<language_code>" \
  --topic "<slug>"
```

Stream the output. When the script finishes, read `runs/<topic>/run_config.json` to learn the per-model status:
- `ok`         → model completed all steps; report and comparison can use it
- `aborted`    → AIO had no AI Overview; skip its per-model report and exclude from comparison
- `failed`     → SERP step returned nothing; skip it

If **all** models failed, stop and report the error to the user.

### 2. Author per-model copywriting reports

For each model with status `ok`, read:
- `runs/<topic>/<model>/third_step_google_entity_analysis/results/summary.json`
- `runs/<topic>/<model>/third_step_google_entity_analysis/charts/cited_winning_entities.csv`
- `runs/<topic>/<model>/first_step_aio_seo/serp_*.json` (to recover the prompt list)

Write each report to:
`runs/<topic>/<model>/fourth_step_conclusion/report_<model>.md`

Follow the structure and tone defined in `.claude/commands/entity-report-software-en.md`:

> Write the report as a senior content strategist briefing a B2B SaaS copywriting team. Be opinionated and specific — translate data signals into concrete content decisions, not generic SEO advice.

Required sections:
1. **Key Insights** (3–5 bullets) — what the entity patterns reveal about search intent and content format
2. **Must-Write vs. Skip** — entity types with cited coverage lift > 1.05x vs. < 0.95x; call out density-lift outliers (>3x) separately
3. **Specific Entity Vocabulary List** — group named entities by type (skip bare numbers, single letters, generic UI labels); for each group, write one sentence on what content angle this implies
4. **Pre-Submission Checklist** — max 10 items, most important first, each concrete and testable

Tone: English, consultative, direct. Use entity lift data as evidence, not as the headline. Always note the cited / non-cited doc count so the team can calibrate confidence.

### 3. Author the cross-platform comparison

Read the per-model `summary.json` + `cited_winning_entities.csv` for every model with status `ok`. Then write:

`runs/<topic>/cross_platform/comparison_<topic>.md`

Follow the style of `comparison_results/cross_platform_comparison_ecommerce_shipping_tracking_returns.md`. Required structure:

1. **Header** — date, platforms compared, topic, queries (from `run_config.json`), and a per-platform `cited / non-cited` count table
2. **Executive Summary** — the single biggest takeaway and the one cheapest universal win
3. **Universal Signals** — entity types or named-entity vocabulary where lift is positive (or at least neutral) across **all** included platforms; one subsection per signal with a small comparison table and one "What to do" paragraph
4. **Platform-Specific Signals** — one subsection per platform, listing signals that are significant for that platform and absent or negative on the others
5. **Conflict Zone** — signals that pull in opposite directions across platforms, with a one-line resolution
6. **Master Checklist** — write-once-rank-on-all checklist; tag each item with the platforms it serves (e.g. `[Claude]`, `[ChatGPT]`, `[Google AIO]`, or `[All]`)


Handling missing models:
- If AIO status is `aborted`, include a short note at the top of the comparison: "Google AI Overview did not render for this location/language combination, so it is excluded from this comparison."
- Same treatment for any other model with status `failed`.
- The comparison still proceeds with the remaining 2–3 models; do not block on missing models.

## Notes

- Do **not** alter `pipeline.py` based on intermediate findings — it is the unified, frozen pipeline. If the user wants pipeline changes, that is a separate task.
- Each pipeline invocation **wipes** `runs/<topic>/` first to avoid pooling stale data with new results. If the user re-runs the same topic, this is intentional.
- Long-running step: Firecrawl + Google NLP can take 5–15 minutes total depending on URL count. The Bash call should not be cancelled.
- Costs: each invocation makes ~7 DataForSEO calls per prompt (3 LLM + 4 organic), Firecrawl scrapes for ~80–120 URLs per run, and Google NLP calls for the same. Mention this to the user before running if they invoke with many prompts.
