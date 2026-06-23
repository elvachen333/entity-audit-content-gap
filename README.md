# Entity Audit — AI Search Content-Gap Analysis

Compares how different AI search surfaces — **ChatGPT, Claude, Gemini, and Google AI Overviews (AIO)** — cite and describe entities for a given set of prompts, then turns the entity-coverage signal into concrete copywriting guidance. The goal is to find the content gaps that keep a brand from being cited by AI answers.

## How it works

For a topic (a set of prompts in one language/location), the pipeline runs four steps per model:

1. **`first_step_aio_seo`** — SERP extract via DataForSEO LLM endpoints (ChatGPT / Claude / Gemini) and the organic + AI Overview SERP for Google AIO. One call per prompt per model.
2. **`second_step_crawl_blogs`** — Firecrawl scrape of the pooled **cited** and **non-cited** URLs per model.
3. **`third_step_google_entity_analysis`** — Google NLP entity analysis + visualization over cited vs. non-cited documents (entity types, salience, and coverage lift).
4. **`fourth_step_conclusion`** — a per-model copywriting report (`report_<model>.md`) plus a cross-platform comparison.

AIO abort handling: if a SERP response has no `ai_overview` item or an empty cited-URL list, the AIO downstream steps are skipped automatically; other models are unaffected.

## Layout

```
entity analysis/
├── All Models in One/          # unified pipeline (pipeline.py) + runs/<topic>/
│   └── runs/<topic>/
│       ├── run_config.json      # per-model status: ok | aborted | failed
│       ├── chatgpt/ claude/ gemini/ aio/
│       │   ├── first_step_aio_seo/
│       │   ├── second_step_crawl_ blogs/
│       │   ├── third_step_google_entity_analysis/
│       │   └── fourth_step_conclusion/report_<model>.md
│       └── cross_platform/
├── Chatgpt/  Claude/  Google_AIO/   # single-model runs (same 4-step structure)
├── comparison_results/              # cross-platform comparison write-ups
└── .claude/commands/                # all-models-in-one, entity-report, entity-report-software-en
```

## Running a topic

Driven by the `all-models-in-one` Claude Code command, which calls the pipeline:

```bash
cd "All Models in One" && \
python3 pipeline.py \
  --prompts "<prompt 1>|<prompt 2>|<prompt 3>" \
  --location "United States" \   # DataForSEO location_name
  --language "en" \              # DataForSEO language_code
  --topic "<run-folder-slug>"
```

After it finishes, read `runs/<topic>/run_config.json` for per-model status, then author the per-model reports and the cross-platform comparison (see `.claude/commands/entity-report*.md` for the report structure and tone).

## Reports

Each per-model report covers: **Key Insights**, **Must-Write vs. Skip** (entity types by cited coverage-lift), a **Specific Entity Vocabulary List** grouped by entity type, and a **Pre-Submission Checklist**. Cited / non-cited doc counts are always noted so confidence can be calibrated.

## Credentials & secrets

Requires DataForSEO, Firecrawl, and Google Cloud NLP access. Service-account JSON keys and `.env` files are git-ignored and must never be committed.
