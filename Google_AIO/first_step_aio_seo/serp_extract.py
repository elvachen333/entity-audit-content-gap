#!/usr/bin/env python3
"""
DataForSEO SERP extractor — pulls AIO cited URLs and top-N organic non-cited URLs.

Usage:
  python3 serp_extract.py "迪士尼門票"
  python3 serp_extract.py "香港迪士尼"

Output:
  - Prints AIO card text + cited URLs to console
  - Prints top-N organic results (deduplicated from AIO) to console
  - Saves full results to serp_<keyword>.json
"""

import sys
import json
import base64
import urllib.request
import re

# ── Editable config ──────────────────────────────────────────────────────────
DATAFORSEO_LOGIN    = "duncan.kuo@kkday.com"
DATAFORSEO_PASSWORD = "890f70af2beb4469"
LOCATION_NAME       = "United States"
LANGUAGE_CODE       = "en-us"
DEVICE              = "desktop"
TOP_N_ORGANIC       = 20               # Max organic non-cited URLs to return
# ─────────────────────────────────────────────────────────────────────────────

API_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"


def fetch_serp(keyword: str) -> dict:
    credentials = base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()
    ).decode()

    payload = json.dumps([{
        "keyword": keyword,
        "location_name": LOCATION_NAME,
        "language_code": LANGUAGE_CODE,
        "device": DEVICE,
        "os": "windows",
        "depth": TOP_N_ORGANIC + 10,   # fetch a few extra to absorb AIO deduplication
    }]).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def extract_aio(items: list) -> tuple:
    """Return (aio_text, aio_url_list) from SERP items.

    DataForSEO AIO structure:
      item["markdown"]            → AIO response text (top-level)
      item["items"][*]["links"]   → inline cited URLs inside the AIO body
      item["references"]          → reference panel (right-side cited sources)
    """
    for item in items:
        if item.get("type", "").lower() != "ai_overview":
            continue

        # ── Text ──────────────────────────────────────────────────────────────
        text = item.get("markdown") or item.get("text") or ""

        # ── Cited URLs ────────────────────────────────────────────────────────
        cited = []
        seen = set()

        def add(url, title="", snippet=""):
            if url and url not in seen:
                seen.add(url)
                cited.append({"url": url, "title": title, "snippet": snippet})

        # 1. Inline links embedded in AIO body paragraphs
        for element in item.get("items") or []:
            for link in element.get("links") or []:
                add(link.get("url", ""), link.get("title", ""))

        # 2. Reference panel (right-side source cards)
        for ref in item.get("references") or []:
            add(ref.get("url", ""), ref.get("title", ""), ref.get("text", ""))

        return text, cited

    return None, []


def extract_organic(items: list, exclude_urls: set) -> list:
    """Return top-N organic results excluding AIO URLs."""
    organic = []
    for item in items:
        if item.get("type") != "organic":
            continue
        url = item.get("url", "")
        if not url or url in exclude_urls:
            continue
        organic.append({
            "rank": item.get("rank_absolute"),
            "url": url,
            "title": item.get("title", ""),
            "description": item.get("description", ""),
        })
        if len(organic) >= TOP_N_ORGANIC:
            break
    return organic


def safe_filename(keyword: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]', '_', keyword)[:60]


def run(keyword: str):
    print(f"\nFetching SERP: {keyword!r}  [{LOCATION_NAME} / {LANGUAGE_CODE}]")
    data = fetch_serp(keyword)

    tasks = data.get("tasks", [])
    if not tasks:
        print("ERROR: No tasks returned.")
        return

    task = tasks[0]
    if task.get("status_code") != 20000:
        print(f"ERROR: {task.get('status_code')} — {task.get('status_message')}")
        return

    result = task["result"][0]
    items = result.get("items") or []

    # Debug: show all types present in this SERP
    types_found = sorted({i.get("type", "?") for i in items})
    print(f"Item types in response: {types_found}")

    aio_text, aio_cited = extract_aio(items)
    aio_url_set = {e["url"] for e in aio_cited}
    organic = extract_organic(items, aio_url_set)

    # ── Print AIO ─────────────────────────────────────────────────────────────
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"AIO CARD — {'FOUND' if aio_text is not None else 'NOT FOUND'}")
    print(sep)
    if aio_text:
        preview = aio_text[:800] + ("…" if len(aio_text) > 800 else "")
        print(f"\n{preview}\n")
        print(f"Cited URLs ({len(aio_cited)}):")
        for i, e in enumerate(aio_cited, 1):
            print(f"  {i:2}. [{e['title']}]  {e['url']}")
            if e.get("snippet"):
                print(f"       {e['snippet'][:120]}…")
    else:
        print("  No AIO card detected for this keyword / locale.")

    # ── Print organic ─────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"TOP {TOP_N_ORGANIC} ORGANIC — NON-CITED (deduped from AIO)")
    print(sep)
    for e in organic:
        print(f"\n  [{e['rank']:2}] {e['title']}")
        print(f"        {e['url']}")
        desc = (e["description"] or "")[:140]
        if desc:
            print(f"        {desc}…")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    output = {
        "keyword": keyword,
        "location": LOCATION_NAME,
        "language": LANGUAGE_CODE,
        "aio": {
            "found": aio_text is not None,
            "response_text": aio_text,
            "cited_urls": aio_cited,
        },
        "non_cited_organic": organic,
        "_raw_item_types": types_found,
    }

    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    out_file = os.path.join(script_dir, f"serp_{safe_filename(keyword)}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved → {out_file}")

    raw_file = os.path.join(raw_dir, f"serp_{safe_filename(keyword)}_raw.json")
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Raw    → {raw_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 serp_extract.py <keyword>")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    run(keyword)


if __name__ == "__main__":
    main()
