#!/usr/bin/env python3
"""
All Models in One — unified pipeline for steps 1-3 across ChatGPT, Claude,
Gemini, and Google AIO.

This script is a self-contained orchestrator that copies the per-model logic
from the original scripts (no business logic altered):

  Step 1 — SERP extract  (DataForSEO LLM endpoints + organic SERP)
    ChatGPT  : ai_optimization/chat_gpt/llm_responses/live   + organic
    Claude   : ai_optimization/claude/llm_responses/live     + organic
    Gemini   : ai_optimization/gemini/llm_responses/live     + organic
    AIO      : serp/google/organic/live/advanced  (AIO + organic in one call)

  Step 2 — Firecrawl crawl  (cited + non-cited pools per model)
  Step 3 — Google NLP entity analysis + visualization

For Google AIO: if the SERP response contains no `ai_overview` item OR the
cited URL list is empty, AIO downstream steps are skipped. Other models are
unaffected.

CLI:
  python3 pipeline.py \\
    --prompts "prompt1|prompt2|prompt3" \\
    --location "United States" \\
    --language "en" \\
    --topic "ecommerce_shipping_tracking_returns"

Format hints:
  --prompts   pipe-separated list of prompts on the same topic
  --location  DataForSEO location_name, e.g. "United States", "Taiwan", "Japan"
  --language  DataForSEO language_code, e.g. "en", "zh-TW", "ja"
  --topic     short slug used as the run folder name (optional;
              auto-derived from the first prompt when omitted)

Output layout (created fresh; existing folder of same topic slug is wiped):
  runs/<topic>/
    run_config.json
    chatgpt/  claude/  gemini/  aio/
      first_step_aio_seo/
        serp_<prompt>.json + raw/
      cited_docs/
      non_cited_docs/
      third_step_google_entity_analysis/
        results/   (cited/, non_cited/, summary.json)
        charts/    (PNGs + cited_winning_entities.csv)
      fourth_step_conclusion/   (placeholder for skill-authored report)
    cross_platform/             (placeholder for skill-authored comparison)
"""

import argparse
import base64
import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime

# ── Editable config (copied from original scripts) ───────────────────────────
DATAFORSEO_LOGIN    = "duncan.kuo@kkday.com"
DATAFORSEO_PASSWORD = "890f70af2beb4469"
FIRECRAWL_API_KEY   = "fc-080ace888c37493792b569c2ece3910f"

DEVICE              = "desktop"
TOP_N_ORGANIC       = 20

CHATGPT_MODEL       = "gpt-4.1"
CLAUDE_MODEL        = "claude-sonnet-4-0"
GEMINI_MODEL        = "gemini-2.5-flash"

CHATGPT_API_URL = "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live"
CLAUDE_API_URL  = "https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/live"
GEMINI_API_URL  = "https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live"
ORGANIC_API_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT = os.path.join(BASE_DIR, "service_account.json")
RUNS_DIR        = os.path.join(BASE_DIR, "runs")

MODELS = ["chatgpt", "claude", "gemini", "aio"]

# Google NLP entity types (display labels) — from original entity_analysis.py
ENTITY_TYPES = {
    "DATE":          "DATE",
    "PHONE_NUMBER":  "PHONE",
    "ADDRESS":       "ADDRESS",
    "NUMBER":        "NUMBER",
    "LOCATION":      "LOCATION",
    "ORGANIZATION":  "ORG",
    "CONSUMER_GOOD": "CONSUMER GOOD",
    "EVENT":         "EVENT",
    "PRICE":         "PRICE",
    "PERSON":        "PERSON",
    "WORK_OF_ART":   "WORK OF ART",
    "OTHER":         "OTHER",
}


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────
def _auth_header() -> str:
    return "Basic " + base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()
    ).decode()


def _post(url: str, payload: list) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": _auth_header(),
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _check_task(data: dict, label: str):
    tasks = data.get("tasks", [])
    if not tasks:
        print(f"  ERROR [{label}]: No tasks returned.")
        return None
    task = tasks[0]
    if task.get("status_code") != 20000:
        print(f"  ERROR [{label}]: {task.get('status_code')} — {task.get('status_message')}")
        return None
    result = (task.get("result") or [{}])[0]
    return result.get("items") or []


def _normalise(url: str) -> str:
    """Strip scheme, www prefix, and trailing slash for dedup comparison."""
    u = re.sub(r"^https?://", "", url.lower().strip())
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def safe_filename(text: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]', '_', text)[:60]


def slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()
    return s[:50] or "topic"


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — SERP extract per model
# (Per-model functions copied from the original serp_extract_*.py scripts,
#  parameterised on location/language. JSON output structure is preserved.)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_chatgpt(keyword: str) -> dict:
    return _post(CHATGPT_API_URL, [{
        "user_prompt":      keyword,
        "model_name":       CHATGPT_MODEL,
        "web_search":       True,
        "force_web_search": True,
        "system_message":   "Please respond in English.",
    }])


def fetch_claude(keyword: str) -> dict:
    return _post(CLAUDE_API_URL, [{
        "user_prompt":      keyword,
        "model_name":       CLAUDE_MODEL,
        "web_search":       True,
        "force_web_search": True,
        "system_message":   "Please respond in English.",
    }])


def fetch_gemini(keyword: str) -> dict:
    return _post(GEMINI_API_URL, [{
        "user_prompt":    keyword,
        "model_name":     GEMINI_MODEL,
        "web_search":     True,
        "system_message": "Please respond in English.",
    }])


def fetch_organic(keyword: str, location: str, language: str) -> dict:
    return _post(ORGANIC_API_URL, [{
        "keyword":       keyword,
        "location_name": location,
        "language_code": language,
        "device":        DEVICE,
        "os":            "windows",
        "depth":         TOP_N_ORGANIC + 10,
    }])


def extract_llm_message(items: list) -> tuple:
    """Shared extractor for ChatGPT / Claude / Gemini llm_responses items.

    Identical structure across all three: type=='message' with sections that
    hold text + annotations and a top-level references panel.
    """
    for item in items:
        if item.get("type", "").lower() != "message":
            continue

        text_parts = [s["text"] for s in (item.get("sections") or []) if s.get("text")]
        text = "\n\n".join(text_parts) or item.get("text") or item.get("markdown") or ""

        cited = []
        seen = set()

        def add(url, title="", snippet=""):
            if url and url not in seen:
                seen.add(url)
                cited.append({"url": url, "title": title, "snippet": snippet})

        for section in item.get("sections") or []:
            for ann in section.get("annotations") or []:
                add(ann.get("url", ""), ann.get("title", ""))

        for ref in item.get("references") or []:
            add(ref.get("url", ""), ref.get("title", ""), ref.get("text", ""))

        return text, cited

    return None, []


def extract_aio(items: list) -> tuple:
    """Extract AIO text + cited URLs from organic SERP items.

    Mirrors Google_AIO/first_step_aio_seo/serp_extract.py:extract_aio.
    """
    for item in items:
        if item.get("type", "").lower() != "ai_overview":
            continue

        text = item.get("markdown") or item.get("text") or ""

        cited = []
        seen = set()

        def add(url, title="", snippet=""):
            if url and url not in seen:
                seen.add(url)
                cited.append({"url": url, "title": title, "snippet": snippet})

        for element in item.get("items") or []:
            for link in element.get("links") or []:
                add(link.get("url", ""), link.get("title", ""))

        for ref in item.get("references") or []:
            add(ref.get("url", ""), ref.get("title", ""), ref.get("text", ""))

        return text, cited

    return None, []


def extract_organic_dedup(items: list, exclude_urls: set, normalise: bool) -> list:
    """Top-N organic results, optionally normalising URLs for dedup match."""
    if normalise:
        excluded = {_normalise(u) for u in exclude_urls}
    else:
        excluded = set(exclude_urls)

    organic = []
    for item in items:
        if item.get("type") != "organic":
            continue
        url = item.get("url", "")
        if not url:
            continue
        key = _normalise(url) if normalise else url
        if key in excluded:
            continue
        organic.append({
            "rank":        item.get("rank_absolute"),
            "url":         url,
            "title":       item.get("title", ""),
            "description": item.get("description", ""),
        })
        if len(organic) >= TOP_N_ORGANIC:
            break
    return organic


def run_serp_for_model(model: str, keyword: str, location: str, language: str,
                       model_dir: str) -> dict:
    """Run step-1 SERP extract for one (model, prompt) and write JSON.

    Returns the saved output dict (with 'aio' key for downstream compatibility),
    or None on failure.
    """
    print(f"\n  [{model.upper()}] keyword={keyword!r}")
    first_step_dir = os.path.join(model_dir, "first_step_aio_seo")
    raw_dir        = os.path.join(first_step_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    safe_kw = safe_filename(keyword)

    if model == "aio":
        print(f"    Calling Google organic SERP (with AIO)…")
        organic_data  = fetch_organic(keyword, location, language)
        organic_items = _check_task(organic_data, "Organic+AIO")
        if organic_items is None:
            return None
        types_found = sorted({i.get("type", "?") for i in organic_items})
        print(f"    Item types: {types_found}")

        aio_text, aio_cited = extract_aio(organic_items)
        aio_url_set = {e["url"] for e in aio_cited}
        organic = extract_organic_dedup(organic_items, aio_url_set, normalise=False)

        output = {
            "keyword":  keyword,
            "model":    "aio",
            "location": location,
            "language": language,
            "aio": {
                "found":         aio_text is not None,
                "response_text": aio_text,
                "cited_urls":    aio_cited,
            },
            "non_cited_organic":  organic,
            "_raw_item_types":    types_found,
        }

        raw_files = {
            f"serp_{safe_kw}_raw.json": organic_data,
        }

    else:
        # ChatGPT / Claude / Gemini
        if model == "chatgpt":
            llm_data = fetch_chatgpt(keyword)
            llm_label = "ChatGPT"
            llm_model = CHATGPT_MODEL
            types_key = "_chatgpt_item_types"
            raw_llm_name = f"serp_{safe_kw}_raw_chatgpt.json"
        elif model == "claude":
            llm_data = fetch_claude(keyword)
            llm_label = "Claude"
            llm_model = CLAUDE_MODEL
            types_key = "_claude_item_types"
            raw_llm_name = f"serp_{safe_kw}_raw_claude.json"
        else:  # gemini
            llm_data = fetch_gemini(keyword)
            llm_label = "Gemini"
            llm_model = GEMINI_MODEL
            types_key = "_gemini_item_types"
            raw_llm_name = f"serp_{safe_kw}_raw_gemini.json"

        print(f"    Calling {llm_label} llm_responses (model={llm_model})…")
        llm_items = _check_task(llm_data, llm_label)
        if llm_items is None:
            return None

        types_found = sorted({i.get("type", "?") for i in llm_items})
        print(f"    {llm_label} item types: {types_found}")

        text, cited = extract_llm_message(llm_items)
        cited_url_set = {e["url"] for e in cited}

        print(f"    Calling Google organic SERP…")
        organic_data  = fetch_organic(keyword, location, language)
        organic_items = _check_task(organic_data, "Organic")
        if organic_items is None:
            return None

        organic = extract_organic_dedup(organic_items, cited_url_set, normalise=True)

        output = {
            "keyword":  keyword,
            "model":    llm_model,
            "location": location,
            "language": language,
            "aio": {
                "found":         text is not None,
                "response_text": text,
                "cited_urls":    cited,
            },
            "non_cited_organic": organic,
            types_key:           types_found,
        }

        raw_files = {
            raw_llm_name:                 llm_data,
            f"serp_{safe_kw}_raw_organic.json": organic_data,
        }

    # ── Save outputs ─────────────────────────────────────────────────────────
    out_file = os.path.join(first_step_dir, f"serp_{safe_kw}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved → {out_file}")
    print(f"    Cited URLs: {len(output['aio']['cited_urls'])}  Non-cited: {len(output['non_cited_organic'])}")

    for name, payload in raw_files.items():
        with open(os.path.join(raw_dir, name), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    return output


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Firecrawl crawl (copied from firecrawl_save_all.py)
# ─────────────────────────────────────────────────────────────────────────────
def clean_url(url: str) -> str:
    url = re.sub(r'#:~:text=.*$', '', url)
    url = re.sub(r'\?srsltid=[^&]*(&|$)', '?', url)
    url = re.sub(r'\?$', '', url)
    return url.rstrip("/")


def url_to_filename(url: str, prefix: str) -> str:
    url = clean_url(url)
    match = re.search(r'/product/([^?#]+)', url)
    if match:
        suffix = match.group(1)
    else:
        suffix = url.split("/")[-1] or url.split("/")[-2]
    suffix = re.sub(r'[<>:"/\\|?*]', '_', suffix)[:80]
    return f"{prefix}{suffix}.md"


def md_to_plaintext(md_content: str) -> str:
    import markdown
    from bs4 import BeautifulSoup
    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        tag.insert_after("\n")
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def firecrawl_scrape(url: str):
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST", "https://api.firecrawl.dev/v1/scrape",
            "-H", f"Authorization: Bearer {FIRECRAWL_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"url": url, "formats": ["markdown"]}),
        ],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"      ERROR: invalid JSON response for {url}")
        return None

    if data.get("success") and data.get("data", {}).get("markdown"):
        return data["data"]["markdown"]

    print(f"      ERROR: {str(data)[:200]}")
    return None


def scrape_pool(urls: list, out_dir: str, prefix: str, label: str):
    """Scrape a list of URLs into out_dir using the given filename prefix."""
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n    {label} pool ({len(urls)} URLs) → {out_dir}")

    seen = set()
    for raw_url in urls:
        url = clean_url(raw_url)
        if url in seen:
            print(f"      Duplicate (skipped): {url}")
            continue
        seen.add(url)

        filename     = os.path.join(out_dir, url_to_filename(url, prefix))
        txt_filename = filename[:-3] + ".txt"
        print(f"      Scraping: {url}")
        content = firecrawl_scrape(url)
        if content:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            plain = md_to_plaintext(content)
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(plain)
            print(f"        Saved ({len(plain):,} chars)")
        else:
            print(f"        Skipped")


def crawl_for_model(model_dir: str, serp_outputs: list):
    """Pool cited + non-cited URLs across all prompts and crawl them."""
    cited_dir     = os.path.join(model_dir, "cited_docs")
    non_cited_dir = os.path.join(model_dir, "non_cited_docs")

    cited_urls = []
    non_cited_urls = []
    for serp in serp_outputs:
        cited_urls     += [e["url"] for e in serp.get("aio", {}).get("cited_urls", [])]
        non_cited_urls += [e["url"] for e in serp.get("non_cited_organic", [])]

    print(f"\n  Pooled {len(cited_urls)} cited + {len(non_cited_urls)} non-cited URLs across {len(serp_outputs)} prompt(s)")
    scrape_pool(cited_urls,     cited_dir,     "cited_post",     "CITED")
    scrape_pool(non_cited_urls, non_cited_dir, "non_cited_post", "NON-CITED")


# ─────────────────────────────────────────────────────────────────────────────
# Step 3a — Google NLP entity analysis
# (Logic copied from entity_analysis.py; language is parameterised so the
#  same script works across en / zh-TW / ja / etc.)
# ─────────────────────────────────────────────────────────────────────────────
def nlp_language(code: str) -> str:
    """Map a DataForSEO language_code to a Google NLP language hint."""
    c = code.strip().lower()
    if c in ("zh-tw", "zh-hant", "zh-hant-tw"):
        return "zh-TW"
    if c in ("zh-cn", "zh-hans", "zh"):
        return "zh"
    return c.split("-")[0]


def make_nlp_client():
    from google.cloud import language_v1
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT,
        scopes=["https://www.googleapis.com/auth/cloud-language"],
    )
    return language_v1.LanguageServiceClient(credentials=creds)


def word_count(text: str) -> int:
    return max(len(text.split()), 1)


def analyze_file(client, txt_path: str, language: str) -> dict:
    from google.cloud import language_v1

    with open(txt_path, encoding="utf-8") as f:
        text = f.read().strip()

    if not text or len(text) < 20:
        print(f"      SKIP (too short): {os.path.basename(txt_path)}")
        return None

    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language=language,
    )

    try:
        response = client.analyze_entities(
            document=document,
            encoding_type=language_v1.EncodingType.UTF8,
        )
    except Exception as e:
        print(f"      ERROR: {os.path.basename(txt_path)}: {e}")
        return None

    entities = []
    for ent in response.entities:
        type_name = language_v1.Entity.Type(ent.type_).name
        entities.append({
            "name":     ent.name,
            "type":     type_name,
            "salience": round(ent.salience, 6),
            "mentions": len(ent.mentions),
        })

    wc = word_count(text)
    type_counts = {}
    type_salience = {}
    for e in entities:
        t = e["type"]
        type_counts[t]   = type_counts.get(t, 0) + e["mentions"]
        type_salience[t] = type_salience.get(t, 0.0) + e["salience"]

    return {
        "file":          os.path.basename(txt_path),
        "word_count":    wc,
        "entity_count":  len(entities),
        "entities":      entities,
        "type_counts":   type_counts,
        "type_salience": type_salience,
    }


def process_pool(client, txt_glob: str, label: str, language: str) -> list:
    files = sorted(glob.glob(txt_glob))
    print(f"\n    {label} pool: {len(files)} files")
    results = []
    for path in files:
        print(f"      Analyzing: {os.path.basename(path)}")
        result = analyze_file(client, path, language)
        if result:
            results.append(result)
    return results


def compute_summary(cited: list, non_cited: list) -> dict:
    def pool_metrics(docs):
        total_words = sum(d["word_count"] for d in docs) or 1
        n = max(len(docs), 1)
        type_total_mentions = {}
        type_doc_count      = {}
        type_total_salience = {}

        for doc in docs:
            for t, cnt in doc["type_counts"].items():
                type_total_mentions[t] = type_total_mentions.get(t, 0) + cnt
                type_doc_count[t]      = type_doc_count.get(t, 0) + 1
            for t, sal in doc["type_salience"].items():
                type_total_salience[t] = type_total_salience.get(t, 0.0) + sal

        metrics = {}
        for t in set(list(type_total_mentions) + list(type_doc_count)):
            mentions = type_total_mentions.get(t, 0)
            metrics[t] = {
                "total_mentions":  mentions,
                "density_per_1k":  round(mentions / total_words * 1000, 4),
                "coverage_rate":   round(type_doc_count.get(t, 0) / n, 4),
                "avg_salience":    round(type_total_salience.get(t, 0) / type_doc_count.get(t, 1), 6),
            }
        return metrics

    cited_m     = pool_metrics(cited)
    non_cited_m = pool_metrics(non_cited)

    all_types = set(list(cited_m) + list(non_cited_m))
    lift = {}
    for t in all_types:
        c_density  = cited_m.get(t, {}).get("density_per_1k", 0)
        n_density  = non_cited_m.get(t, {}).get("density_per_1k", 0)
        c_coverage = cited_m.get(t, {}).get("coverage_rate", 0)
        n_coverage = non_cited_m.get(t, {}).get("coverage_rate", 0)

        lift[t] = {
            "density_lift":      round(c_density  / n_density  if n_density  > 0 else 0, 4),
            "coverage_lift":     round(c_coverage / n_coverage if n_coverage > 0 else 0, 4),
            "cited_density":     c_density,
            "non_cited_density": n_density,
            "cited_coverage":    c_coverage,
            "non_cited_coverage": n_coverage,
        }

    return {
        "cited_metrics":       cited_m,
        "non_cited_metrics":   non_cited_m,
        "lift":                lift,
        "cited_doc_count":     len(cited),
        "non_cited_doc_count": len(non_cited),
    }


def top_named_entities_gap(cited: list, non_cited: list, top_n: int = 40) -> list:
    def name_freq(docs):
        freq = {}
        n = max(len(docs), 1)
        for doc in docs:
            seen = set()
            for e in doc["entities"]:
                key = (e["name"].lower(), e["type"])
                if key not in seen:
                    seen.add(key)
                    freq[key] = freq.get(key, 0) + 1
        return freq, n

    c_freq, c_n = name_freq(cited)
    n_freq, n_n = name_freq(non_cited)
    all_keys = set(list(c_freq) + list(n_freq))

    gaps = []
    for key in all_keys:
        c_rate = c_freq.get(key, 0) / c_n
        n_rate = n_freq.get(key, 0) / n_n
        if c_rate + n_rate < 0.05:
            continue
        lift = c_rate / n_rate if n_rate > 0 else c_rate * 10
        gaps.append({
            "name":           key[0],
            "type":           key[1],
            "cited_rate":     round(c_rate, 4),
            "non_cited_rate": round(n_rate, 4),
            "lift":           round(lift, 4),
        })

    gaps.sort(key=lambda x: x["lift"], reverse=True)
    return gaps[:top_n]


def entity_analysis_for_model(model_dir: str, language: str):
    """Run NLP entity analysis on the cited / non-cited TXT pools."""
    cited_dir     = os.path.join(model_dir, "cited_docs")
    non_cited_dir = os.path.join(model_dir, "non_cited_docs")
    results_dir   = os.path.join(model_dir, "third_step_google_entity_analysis", "results")

    for sub in ("cited", "non_cited"):
        os.makedirs(os.path.join(results_dir, sub), exist_ok=True)

    nlp_lang = nlp_language(language)
    print(f"    NLP language hint: {nlp_lang}")
    print("    Initialising Google NLP client…")
    client = make_nlp_client()

    cited_results     = process_pool(client, os.path.join(cited_dir,     "cited_post*.txt"),     "CITED",     nlp_lang)
    non_cited_results = process_pool(client, os.path.join(non_cited_dir, "non_cited_post*.txt"), "NON-CITED", nlp_lang)

    for r in cited_results:
        out = os.path.join(results_dir, "cited", r["file"].replace(".txt", ".json"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

    for r in non_cited_results:
        out = os.path.join(results_dir, "non_cited", r["file"].replace(".txt", ".json"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

    summary = compute_summary(cited_results, non_cited_results)
    summary["top_named_entity_gaps"] = top_named_entities_gap(cited_results, non_cited_results)
    summary_path = os.path.join(results_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"    Cited analysed: {len(cited_results)}  Non-cited analysed: {len(non_cited_results)}")
    print(f"    Saved summary → {summary_path}")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Step 3b — Visualization
# (Logic copied from entity_visualize.py; only the run paths and KEYWORD label
#  are parameterised. Same 4 outputs as the original main().)
# ─────────────────────────────────────────────────────────────────────────────
ENTITY_ORDER = [
    "DATE", "PHONE_NUMBER", "ADDRESS", "NUMBER",
    "LOCATION", "ORGANIZATION", "CONSUMER_GOOD",
    "EVENT", "PRICE", "PERSON", "WORK_OF_ART",
]
ENTITY_LABELS = {
    "DATE": "DATE", "PHONE_NUMBER": "PHONE", "ADDRESS": "ADDRESS",
    "NUMBER": "NUMBER", "LOCATION": "LOCATION", "ORGANIZATION": "ORG",
    "CONSUMER_GOOD": "CONSUMER\nGOOD", "EVENT": "EVENT", "PRICE": "PRICE",
    "PERSON": "PERSON", "WORK_OF_ART": "WORK\nOF ART",
}

DARK_BG  = "#0d1117"
PANEL_BG = "#161b22"
GOLD     = "#f5a623"
TEAL     = "#4ec9c9"
TEXT     = "#e0e0e0"
GRIDLINE = "#2a2a3a"


def _dark_fig(plt, w=14, h=7):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRIDLINE)
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.6, zorder=0)
    return fig, ax


def chart_coverage_lift_bar(plt, mpatches, mticker, summary, charts_dir, keyword):
    lift   = summary["lift"]
    types  = [t for t in ENTITY_ORDER if t in lift]
    values = [lift[t].get("coverage_lift", 0) for t in types]
    labels = [ENTITY_LABELS.get(t, t) for t in types]

    paired = sorted(zip(values, labels, types), reverse=True)
    if paired:
        values, labels, types = zip(*paired)
    else:
        values, labels, types = [], [], []

    fig, ax = _dark_fig(plt, 14, 7)
    colors = [GOLD if v >= 1.0 else TEAL for v in values]
    bars = ax.bar(labels, [v - 1.0 for v in values], color=colors, width=0.6, zorder=3)
    ax.axhline(0, color=TEXT, linewidth=1.0, zorder=4)

    for bar, v in zip(bars, values):
        ypos = bar.get_height() + 0.005 if v >= 1.0 else bar.get_height() - 0.02
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                f"{v:.2f}x", ha="center", va="bottom" if v >= 1.0 else "top",
                color=TEXT, fontsize=9, fontweight="bold")

    ax.set_title(
        f"Entity Coverage Lift — Cited vs Non-Cited  [{keyword}]\n"
        f"(% pages containing entity type: cited ÷ non-cited)",
        color=TEXT, fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlabel("Entity type", color=TEXT, fontsize=10)
    ax.set_ylabel("Lift vs. non-cited pages\n(coverage ratio)", color=TEXT, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x+1:.2f}x"))

    pos_patch = mpatches.Patch(color=GOLD, label="Positive lift (>1.0x)")
    neg_patch = mpatches.Patch(color=TEAL, label="Negative lift (<1.0x)")
    ax.legend(handles=[pos_patch, neg_patch], facecolor=PANEL_BG,
              labelcolor=TEXT, fontsize=9, framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(charts_dir, "1b_entity_coverage_lift_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"      Saved: {path}")


def chart_coverage_rate(plt, mticker, summary, charts_dir, keyword):
    import numpy as np
    c_m  = summary["cited_metrics"]
    n_m  = summary["non_cited_metrics"]
    types = [t for t in ENTITY_ORDER if t in c_m or t in n_m]
    labels = [ENTITY_LABELS.get(t, t) for t in types]

    c_vals = [c_m.get(t, {}).get("coverage_rate", 0) * 100 for t in types]
    n_vals = [n_m.get(t, {}).get("coverage_rate", 0) * 100 for t in types]

    x = np.arange(len(types))
    w = 0.38
    fig, ax = _dark_fig(plt, 14, 7)
    ax.bar(x - w/2, c_vals, w, label="Cited",     color=GOLD, zorder=3, alpha=0.9)
    ax.bar(x + w/2, n_vals, w, label="Non-cited", color=TEAL, zorder=3, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TEXT, fontsize=9)
    ax.set_ylabel("% of pages containing entity type", color=TEXT, fontsize=10)
    ax.set_title(f"Entity Coverage Rate — Cited vs Non-Cited  [{keyword}]",
                 color=TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    plt.tight_layout()
    path = os.path.join(charts_dir, "2_coverage_rate_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"      Saved: {path}")


def chart_top_entities_gap(plt, summary, charts_dir, keyword, top_n=40):
    import pandas as pd
    gaps = summary.get("top_named_entity_gaps", [])[:top_n]
    if not gaps:
        print("      SKIP: no named entity gap data.")
        return

    df = pd.DataFrame(gaps).sort_values("lift", ascending=True)

    fig, ax = _dark_fig(plt, 13, max(6, len(df) * 0.38))
    colors = [GOLD if row["lift"] >= 1.0 else TEAL for _, row in df.iterrows()]
    bars = ax.barh(df["name"] + "  [" + df["type"] + "]",
                   df["lift"], color=colors, height=0.7, zorder=3)
    ax.axvline(1.0, color=TEXT, linewidth=1.0, linestyle="--", zorder=4)

    for bar, v in zip(bars, df["lift"]):
        ax.text(v + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}x", va="center", color=TEXT, fontsize=8)

    ax.set_xlabel("Lift (cited frequency / non-cited frequency)", color=TEXT, fontsize=10)
    ax.set_title(f"Top Named Entities Gap — Cited vs Non-Cited  [{keyword}]",
                 color=TEXT, fontsize=12, fontweight="bold", pad=12)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    path = os.path.join(charts_dir, "4_top_entities_gap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"      Saved: {path}")


def export_coverage_gap_csv(summary, results_dir, charts_dir):
    import pandas as pd
    c_m = summary["cited_metrics"]
    n_m = summary["non_cited_metrics"]
    c_n = max(summary["cited_doc_count"], 1)
    n_n = max(summary["non_cited_doc_count"], 1)

    winning_types = {
        t for t in c_m
        if c_m[t].get("coverage_rate", 0) > n_m.get(t, {}).get("coverage_rate", 0)
    }

    def load_pool_docs(subdir):
        docs = []
        for path in sorted(glob.glob(os.path.join(results_dir, subdir, "*.json"))):
            with open(path, encoding="utf-8") as f:
                docs.append(json.load(f))
        return docs

    cited_docs     = load_pool_docs("cited")
    non_cited_docs = load_pool_docs("non_cited")

    def aggregate(docs):
        stats = {}
        for doc in docs:
            seen = set()
            for e in doc["entities"]:
                key = (e["name"], e["type"])
                if key not in seen:
                    seen.add(key)
                    if key not in stats:
                        stats[key] = {"doc_count": 0, "total_mentions": 0, "total_salience": 0.0}
                    stats[key]["doc_count"]      += 1
                    stats[key]["total_salience"] += e["salience"]
                if key in stats:
                    stats[key]["total_mentions"] += e["mentions"]
        return stats

    c_stats = aggregate(cited_docs)
    n_stats = aggregate(non_cited_docs)

    all_keys = set(list(c_stats.keys()) + list(n_stats.keys()))
    rows = []
    for (name, etype) in all_keys:
        if etype not in winning_types:
            continue
        c = c_stats.get((name, etype), {"doc_count": 0, "total_mentions": 0, "total_salience": 0.0})
        n = n_stats.get((name, etype), {"doc_count": 0, "total_mentions": 0, "total_salience": 0.0})

        c_cov  = round(c["doc_count"] / c_n, 4)
        n_cov  = round(n["doc_count"] / n_n, 4)
        c_lift = round(c_cov / n_cov if n_cov > 0 else c_cov * 10, 4)
        c_sal  = round(c["total_salience"] / c["doc_count"], 6) if c["doc_count"] > 0 else 0.0
        n_sal  = round(n["total_salience"] / n["doc_count"], 6) if n["doc_count"] > 0 else 0.0

        rows.append({
            "entity_type":              etype,
            "entity_name":              name,
            "cited_doc_count":          c["doc_count"],
            "non_cited_doc_count":      n["doc_count"],
            "cited_coverage_rate":      c_cov,
            "non_cited_coverage_rate":  n_cov,
            "coverage_lift":            c_lift,
            "cited_total_mentions":     c["total_mentions"],
            "non_cited_total_mentions": n["total_mentions"],
            "avg_salience_cited":       c_sal,
            "avg_salience_non_cited":   n_sal,
        })

    if not rows:
        print("      CSV: no rows matched (no winning entity types found).")
        return

    type_lift = {
        t: round(c_m[t]["coverage_rate"] / max(n_m.get(t, {}).get("coverage_rate", 0.0001), 0.0001), 4)
        for t in winning_types
    }
    df = pd.DataFrame(rows)
    df["_type_lift"] = df["entity_type"].map(type_lift)
    df = df.sort_values(["_type_lift", "coverage_lift", "cited_doc_count"],
                        ascending=[False, False, False])
    df = df.drop(columns=["_type_lift"])

    out_path = os.path.join(charts_dir, "cited_winning_entities.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"      Saved: {out_path}  ({len(df)} rows, {df['entity_type'].nunique()} entity types)")


def visualize_for_model(model_dir: str, summary: dict, keyword_label: str):
    """Generate the same charts + CSV the original entity_visualize.main() produces."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["font.family"] = ["PingFang HK", "Heiti TC", "Arial Unicode MS", "DejaVu Sans"]
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker

    results_dir = os.path.join(model_dir, "third_step_google_entity_analysis", "results")
    charts_dir  = os.path.join(model_dir, "third_step_google_entity_analysis", "charts")
    if os.path.exists(charts_dir):
        shutil.rmtree(charts_dir)
    os.makedirs(charts_dir)

    print(f"    Generating charts → {charts_dir}/")
    chart_coverage_lift_bar(plt, mpatches, mticker, summary, charts_dir, keyword_label)
    chart_coverage_rate(plt, mticker, summary, charts_dir, keyword_label)
    chart_top_entities_gap(plt, summary, charts_dir, keyword_label)
    export_coverage_gap_csv(summary, results_dir, charts_dir)


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────
def init_run_folder(topic: str, prompts: list, location: str, language: str) -> str:
    run_dir = os.path.join(RUNS_DIR, topic)
    if os.path.exists(run_dir):
        print(f"Wiping existing run folder: {run_dir}")
        shutil.rmtree(run_dir)
    os.makedirs(run_dir)

    for model in MODELS:
        model_dir = os.path.join(run_dir, model)
        for sub in (
            "first_step_aio_seo/raw",
            "cited_docs",
            "non_cited_docs",
            "third_step_google_entity_analysis/results/cited",
            "third_step_google_entity_analysis/results/non_cited",
            "third_step_google_entity_analysis/charts",
            "fourth_step_conclusion",
        ):
            os.makedirs(os.path.join(model_dir, sub), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "cross_platform"), exist_ok=True)

    config = {
        "topic":     topic,
        "prompts":   prompts,
        "location":  location,
        "language":  language,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "models":    {m: {"status": "pending"} for m in MODELS},
    }
    with open(os.path.join(run_dir, "run_config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return run_dir


def update_run_config(run_dir: str, model: str, **fields):
    path = os.path.join(run_dir, "run_config.json")
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    config["models"][model].update(fields)
    config["updated_at"] = datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def run_pipeline(prompts: list, location: str, language: str, topic: str):
    print(f"\n{'═' * 72}")
    print(f"All Models in One — pipeline")
    print(f"  Topic    : {topic}")
    print(f"  Prompts  : {len(prompts)}")
    for i, p in enumerate(prompts, 1):
        print(f"    {i}. {p}")
    print(f"  Location : {location}")
    print(f"  Language : {language}")
    print(f"{'═' * 72}")

    run_dir = init_run_folder(topic, prompts, location, language)
    print(f"Run folder: {run_dir}")

    keyword_label = " | ".join(prompts) if len(prompts) > 1 else prompts[0]

    for model in MODELS:
        print(f"\n{'─' * 72}")
        print(f"MODEL: {model.upper()}")
        print(f"{'─' * 72}")
        model_dir = os.path.join(run_dir, model)

        # Step 1: SERP for each prompt
        serp_outputs = []
        for prompt in prompts:
            out = run_serp_for_model(model, prompt, location, language, model_dir)
            if out:
                serp_outputs.append(out)

        # AIO abort check
        if model == "aio":
            total_cited = sum(len(s["aio"]["cited_urls"]) for s in serp_outputs)
            has_aio_item = any(s["aio"]["found"] for s in serp_outputs)
            if not has_aio_item or total_cited == 0:
                print(f"\n  AIO ABORTED — no AI Overview rendered for the given location/language.")
                print(f"  Skipping Firecrawl + entity analysis for AIO. Other models continue.")
                update_run_config(run_dir, model, status="aborted",
                                  reason="No ai_overview item or empty cited URL list",
                                  prompt_count=len(serp_outputs))
                continue

        if not serp_outputs:
            print(f"\n  {model.upper()}: SERP step returned nothing — skipping downstream.")
            update_run_config(run_dir, model, status="failed", reason="No SERP output")
            continue

        update_run_config(run_dir, model, status="serp_done", prompt_count=len(serp_outputs))

        # Step 2: Firecrawl
        print(f"\n  Firecrawl crawling pooled URLs…")
        crawl_for_model(model_dir, serp_outputs)
        update_run_config(run_dir, model, status="crawl_done")

        # Step 3a: Entity analysis
        print(f"\n  Google NLP entity analysis…")
        summary = entity_analysis_for_model(model_dir, language)
        update_run_config(run_dir, model,
                          status="analysis_done",
                          cited_doc_count=summary["cited_doc_count"],
                          non_cited_doc_count=summary["non_cited_doc_count"])

        # Step 3b: Visualization
        print(f"\n  Visualization…")
        visualize_for_model(model_dir, summary, keyword_label)
        update_run_config(run_dir, model, status="ok")

    # Final status
    print(f"\n{'═' * 72}")
    print(f"Pipeline complete. Run folder: {run_dir}")
    with open(os.path.join(run_dir, "run_config.json"), encoding="utf-8") as f:
        config = json.load(f)
    print(f"Per-model status:")
    for m in MODELS:
        s = config["models"][m].get("status", "?")
        extra = ""
        if s == "ok":
            extra = f"  ({config['models'][m].get('cited_doc_count', 0)} cited / {config['models'][m].get('non_cited_doc_count', 0)} non-cited)"
        elif s == "aborted":
            extra = f"  ({config['models'][m].get('reason', '')})"
        print(f"  {m:8s} → {s}{extra}")
    print(f"{'═' * 72}")
    print(f"\nNext step: invoke the /all-models-in-one skill (or read the model")
    print(f"summaries directly) to author per-model reports and the cross-platform")
    print(f"comparison under {run_dir}/")


def parse_args():
    p = argparse.ArgumentParser(
        description="All Models in One — run SERP + crawl + entity analysis "
                    "for ChatGPT, Claude, Gemini, and Google AIO in a single pass.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Format hints:
  --prompts   pipe-separated, e.g. "What is X?|Compare Y and Z|Best W tools"
  --location  DataForSEO location_name string. Examples:
                "United States", "United Kingdom", "Taiwan", "Japan",
                "Germany", "France", "Canada", "Australia"
  --language  DataForSEO language_code. Examples:
                "en"     English
                "en-us"  US English (used by Google organic SERP)
                "zh-TW"  Traditional Chinese
                "ja"     Japanese
                "de"     German
  --topic     short slug, e.g. "ecommerce_returns".
              Optional; auto-derived from the first prompt if omitted.

Example:
  python3 pipeline.py \\
    --prompts "Best Shopify shipping apps|Top package tracking tools" \\
    --location "United States" --language "en" \\
    --topic "shipping_tracking"
""",
    )
    p.add_argument("--prompts",  required=True,
                   help="Pipe-separated list of prompts on the same topic")
    p.add_argument("--location", required=True,
                   help='DataForSEO location_name, e.g. "United States"')
    p.add_argument("--language", required=True,
                   help='DataForSEO language_code, e.g. "en" or "zh-TW"')
    p.add_argument("--topic",    default="",
                   help="Short slug for the run folder (auto-derived if omitted)")
    return p.parse_args()


def main():
    args = parse_args()
    prompts = [p.strip() for p in args.prompts.split("|") if p.strip()]
    if not prompts:
        sys.exit("ERROR: --prompts is empty after parsing on '|'.")

    topic = args.topic.strip() or slugify(prompts[0])
    run_pipeline(prompts, args.location.strip(), args.language.strip(), topic)


if __name__ == "__main__":
    main()
