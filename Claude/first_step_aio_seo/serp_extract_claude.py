#!/usr/bin/env python3
"""
DataForSEO Claude SERP extractor — pulls Claude cited URLs and top-N organic non-cited URLs.

Makes two API calls:
  1. ai_optimization/claude/llm_responses/live  →  Claude answer + cited sources
  2. serp/google/organic/live/advanced          →  organic SERP (deduplicated)

Output JSON is intentionally identical in structure to serp_extract.py so all
downstream scripts (firecrawl_save_cited.py, entity_analysis.py, etc.) work unchanged.

Usage:
  python3 serp_extract_claude.py "top shopify shipping software"
  python3 serp_extract_claude.py "best delivery notification email tools"

Output:
  - Prints Claude response text + cited URLs to console
  - Prints top-N organic results (deduplicated from Claude citations) to console
  - Saves full results to serp_<keyword>.json
"""

import sys
import json
import base64
import urllib.request
import re
import os

# ── Editable config ──────────────────────────────────────────────────────────
DATAFORSEO_LOGIN    = "duncan.kuo@kkday.com"
DATAFORSEO_PASSWORD = "890f70af2beb4469"
LOCATION_NAME       = "United States"
LANGUAGE_CODE       = "en"
DEVICE              = "desktop"
TOP_N_ORGANIC       = 20
CLAUDE_MODEL        = "claude-sonnet-4-0"
# ─────────────────────────────────────────────────────────────────────────────

CLAUDE_API_URL  = "https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/live"
ORGANIC_API_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"


def _auth_header() -> str:
    return "Basic " + base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()
    ).decode()


def _post(url: str, payload: list) -> dict:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
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


def fetch_claude(keyword: str) -> dict:
    """Call Claude llm_responses with web_search enabled."""
    return _post(CLAUDE_API_URL, [{
        "user_prompt":    keyword,
        "model_name":     CLAUDE_MODEL,
        "web_search":     True,
        "force_web_search": True,
        "system_message": "Please respond in English.",
    }])


def fetch_organic(keyword: str) -> dict:
    """Call Google organic SERP to get non-cited candidates."""
    return _post(ORGANIC_API_URL, [{
        "keyword":       keyword,
        "location_name": LOCATION_NAME,
        "language_code": LANGUAGE_CODE,
        "device":        DEVICE,
        "os":            "windows",
        "depth":         TOP_N_ORGANIC + 10,
    }])


def extract_claude(items: list) -> tuple:
    """Return (response_text, cited_url_list) from Claude llm_responses items.

    DataForSEO Claude response structure:
      item["type"] == "message"
      item["sections"][*]["text"]          → answer text segments
      item["sections"][*]["annotations"]   → inline citation objects with url/title
      item["references"]                   → deduplicated source list
    """
    for item in items:
        if item.get("type", "").lower() != "message":
            continue

        text_parts = [s["text"] for s in (item.get("sections") or []) if s.get("text")]
        text = "\n\n".join(text_parts) or item.get("text") or item.get("markdown") or ""

        cited = []
        seen  = set()

        def add(url, title="", snippet=""):
            if url and url not in seen:
                seen.add(url)
                cited.append({"url": url, "title": title, "snippet": snippet})

        # 1. Inline annotations inside each section
        for section in item.get("sections") or []:
            for ann in section.get("annotations") or []:
                add(ann.get("url", ""), ann.get("title", ""))

        # 2. Top-level references panel
        for ref in item.get("references") or []:
            add(ref.get("url", ""), ref.get("title", ""), ref.get("text", ""))

        return text, cited

    return None, []


def extract_organic(items: list, exclude_urls: set) -> list:
    """Return top-N organic results, deduplicating any URLs already cited by Claude."""
    excluded_normalised = {_normalise(u) for u in exclude_urls}

    organic = []
    for item in items:
        if item.get("type") != "organic":
            continue
        url = item.get("url", "")
        if not url:
            continue
        if _normalise(url) in excluded_normalised:
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


def _normalise(url: str) -> str:
    """Strip scheme, www prefix, and trailing slash for dedup comparison."""
    u = re.sub(r"^https?://", "", url.lower().strip())
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def _check_task(data: dict, label: str):
    tasks = data.get("tasks", [])
    if not tasks:
        print(f"ERROR [{label}]: No tasks returned.")
        return None
    task = tasks[0]
    if task.get("status_code") != 20000:
        print(f"ERROR [{label}]: {task.get('status_code')} — {task.get('status_message')}")
        return None
    result = (task.get("result") or [{}])[0]
    return result.get("items") or []


def safe_filename(keyword: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]', '_', keyword)[:60]


def run(keyword: str):
    print(f"\nKeyword: {keyword!r}  [{LOCATION_NAME} / {LANGUAGE_CODE}]")

    # ── 1. Claude answer + cited sources ─────────────────────────────────────
    print(f"  Calling Claude llm_responses (model={CLAUDE_MODEL}, web_search=True)…")
    claude_data  = fetch_claude(keyword)
    claude_items = _check_task(claude_data, "Claude")
    if claude_items is None:
        return

    claude_types = sorted({i.get("type", "?") for i in claude_items})
    print(f"  Claude item types: {claude_types}")

    claude_text, claude_cited = extract_claude(claude_items)
    cited_url_set = {e["url"] for e in claude_cited}

    # ── 2. Google organic SERP ────────────────────────────────────────────────
    print(f"  Calling Google organic SERP…")
    organic_data  = fetch_organic(keyword)
    organic_items = _check_task(organic_data, "Organic")
    if organic_items is None:
        return

    organic = extract_organic(organic_items, cited_url_set)

    # ── Print Claude answer ───────────────────────────────────────────────────
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"CLAUDE ANSWER — {'FOUND' if claude_text is not None else 'NOT FOUND'}")
    print(sep)
    if claude_text:
        preview = claude_text[:800] + ("…" if len(claude_text) > 800 else "")
        print(f"\n{preview}\n")
        print(f"Cited URLs ({len(claude_cited)}):")
        for i, e in enumerate(claude_cited, 1):
            print(f"  {i:2}. [{e['title']}]  {e['url']}")
            if e.get("snippet"):
                print(f"       {e['snippet'][:120]}…")
    else:
        print("  No Claude answer detected for this keyword.")

    # ── Print organic ─────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"TOP {TOP_N_ORGANIC} ORGANIC — NON-CITED (deduped from Claude citations)")
    print(sep)
    for e in organic:
        print(f"\n  [{e['rank']:2}] {e['title']}")
        print(f"        {e['url']}")
        desc = (e["description"] or "")[:140]
        if desc:
            print(f"        {desc}…")

    # ── Save JSON — same structure as serp_extract.py for pipeline compatibility
    output = {
        "keyword":  keyword,
        "model":    CLAUDE_MODEL,
        "location": LOCATION_NAME,
        "language": LANGUAGE_CODE,
        "aio": {                         # key kept as "aio" for downstream compatibility
            "found":         claude_text is not None,
            "response_text": claude_text,
            "cited_urls":    claude_cited,
        },
        "non_cited_organic":  organic,
        "_claude_item_types": claude_types,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir    = os.path.join(script_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    out_file = os.path.join(script_dir, f"serp_{safe_filename(keyword)}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved → {out_file}")

    raw_claude = os.path.join(raw_dir, f"serp_{safe_filename(keyword)}_raw_claude.json")
    with open(raw_claude, "w", encoding="utf-8") as f:
        json.dump(claude_data, f, ensure_ascii=False, indent=2)

    raw_organic = os.path.join(raw_dir, f"serp_{safe_filename(keyword)}_raw_organic.json")
    with open(raw_organic, "w", encoding="utf-8") as f:
        json.dump(organic_data, f, ensure_ascii=False, indent=2)
    print(f"Raw    → {raw_dir}/")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 serp_extract_claude.py <keyword>")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    run(keyword)


if __name__ == "__main__":
    main()
