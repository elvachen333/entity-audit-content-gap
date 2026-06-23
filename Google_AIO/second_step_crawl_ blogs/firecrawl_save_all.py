#!/usr/bin/env python3
"""
Firecrawl URL scraper — scrapes BOTH cited and non-cited URLs in one run.

Usage:
  # Read both pools from a SERP JSON file (most common)
  python3 firecrawl_save_all.py --from-serp /path/to/serp_keyword.json

  # Convert existing *.md files in both output dirs to .txt
  python3 firecrawl_save_all.py --convert

File naming:
  cited_docs/     cited_post<suffix>.md / .txt
  non_cited_docs/ non_cited_post<suffix>.md / .txt

Example:
  python3 firecrawl_save_all.py --from-serp ../first_step_aio_seo/serp_台灣親子遊.json
"""

import sys
import json
import re
import os
import glob
import subprocess
import markdown
from bs4 import BeautifulSoup

API_KEY      = "fc-8fd99fd386384002913a4656d2011f3c"
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITED_DIR    = os.path.join(BASE_DIR, "cited_docs")
NON_CITED_DIR = os.path.join(BASE_DIR, "non_cited_docs")


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
    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        tag.insert_after("\n")
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def scrape(url: str):
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST", "https://api.firecrawl.dev/v1/scrape",
            "-H", f"Authorization: Bearer {API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"url": url, "formats": ["markdown"]}),
        ],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR: invalid JSON response for {url}")
        return None

    if data.get("success") and data.get("data", {}).get("markdown"):
        return data["data"]["markdown"]

    print(f"  ERROR: {data}")
    return None


def scrape_pool(urls: list, out_dir: str, prefix: str, label: str):
    """Scrape a list of URLs into out_dir using the given filename prefix."""
    os.makedirs(out_dir, exist_ok=True)
    print(f"\nSaving to: {out_dir}")
    print(f"── {label} ({len(urls)} URLs) ──────────────────────────────────")

    seen = set()
    for raw_url in urls:
        url = clean_url(raw_url)
        if url in seen:
            print(f"  Duplicate (skipped): {url}")
            continue
        seen.add(url)

        filename     = os.path.join(out_dir, url_to_filename(url, prefix))
        txt_filename = filename[:-3] + ".txt"
        print(f"Scraping: {url}")
        content = scrape(url)
        if content:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Saved:   {filename} ({len(content):,} chars)")
            plain = md_to_plaintext(content)
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(plain)
            print(f"  Saved:   {txt_filename} ({len(plain):,} chars)")
        else:
            print(f"  Skipped: {url}")


def convert_existing():
    """Convert all cited_post*.md and non_cited_post*.md to .txt."""
    for out_dir, pattern in [
        (CITED_DIR,     "cited_post*.md"),
        (NON_CITED_DIR, "non_cited_post*.md"),
    ]:
        md_files = sorted(glob.glob(os.path.join(out_dir, pattern)))
        if not md_files:
            print(f"No {pattern} files found in {out_dir}")
            continue
        for md_path in md_files:
            txt_path = md_path[:-3] + ".txt"
            with open(md_path, encoding="utf-8") as f:
                md_content = f.read()
            plain = md_to_plaintext(md_content)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(plain)
            print(f"  Converted: {md_path} → {txt_path} ({len(plain):,} chars)")
    print("\nDone.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 firecrawl_save_all.py --from-serp <serp_json_path>\n"
              "       python3 firecrawl_save_all.py --convert")
        sys.exit(1)

    if sys.argv[1] == "--convert":
        convert_existing()
        return

    if sys.argv[1] == "--from-serp":
        if len(sys.argv) < 3:
            print("Usage: python3 firecrawl_save_all.py --from-serp <serp_json_path>")
            sys.exit(1)
        with open(sys.argv[2], encoding="utf-8") as f:
            serp = json.load(f)

        cited_urls     = [e["url"] for e in serp.get("aio", {}).get("cited_urls", [])]
        non_cited_urls = [e["url"] for e in serp.get("non_cited_organic", [])]
        print(f"Loaded {len(cited_urls)} cited + {len(non_cited_urls)} non-cited URLs"
              f" from {sys.argv[2]}")

        scrape_pool(cited_urls,     CITED_DIR,     "cited_post",     "CITED")
        scrape_pool(non_cited_urls, NON_CITED_DIR, "non_cited_post", "NON-CITED")
    else:
        print("ERROR: unknown argument. Use --from-serp or --convert.")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
