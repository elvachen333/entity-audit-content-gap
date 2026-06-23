#!/usr/bin/env python3
"""
Firecrawl URL scraper — saves each URL as a markdown file + plain text file.

Usage:
  # Scrape URLs directly
  python3 firecrawl_save_noncited.py <url1> [url2] [url3] ...

  # Read non-cited URLs from a SERP JSON file
  python3 firecrawl_save_noncited.py --from-serp /path/to/serp_keyword.json

  # Convert existing non_cited_post*.md files in current directory to .txt
  python3 firecrawl_save_noncited.py --convert

File naming:
  For KKday product URLs: non_cited_post<product-slug>.md / .txt
  For other URLs:         non_cited_post<last-path-segment>.md / .txt

Example:
  python3 firecrawl_save_noncited.py https://www.kkday.com/zh-hk/product/19252
  python3 firecrawl_save_noncited.py --from-serp ../first_step_aio_seo/serp_台灣親子遊.json
"""

import sys
import json
import re
import os
import glob
import subprocess

import markdown
from bs4 import BeautifulSoup

API_KEY  = "fc-8fd99fd386384002913a4656d2011f3c"
OUT_DIR  = "/Users/elva.chen/Desktop/share-obsidian/entity analysis/Google_AIO/non_cited_docs"


def clean_url(url: str) -> str:
    """Strip #:~:text= fragments and ?srsltid= / other tracking params."""
    url = re.sub(r'#:~:text=.*$', '', url)
    url = re.sub(r'\?srsltid=[^&]*(&|$)', '?', url)
    url = re.sub(r'\?$', '', url)
    return url.rstrip("/")


def url_to_filename(url: str) -> str:
    """Derive a non_cited_post<suffix>.md filename from a URL."""
    url = clean_url(url)
    match = re.search(r'/product/([^?#]+)', url)
    if match:
        suffix = match.group(1)
    else:
        suffix = url.split("/")[-1] or url.split("/")[-2]
    suffix = re.sub(r'[<>:"/\\|?*]', '_', suffix)[:80]
    return f"non_cited_post{suffix}.md"


def md_to_plaintext(md_content: str) -> str:
    """Convert Markdown to clean plain text (Markdown → HTML → strip tags)."""
    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, "html.parser")
    # Separate block elements with newlines so sentences don't merge
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        tag.insert_after("\n")
    text = soup.get_text(separator="\n")
    # Collapse 3+ consecutive blank lines into 2
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def scrape(url: str):
    """Call the Firecrawl API and return markdown content, or None on failure."""
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


def convert_existing():
    """Convert all non_cited_post*.md in the current directory to .txt."""
    md_files = sorted(glob.glob("non_cited_post*.md"))
    if not md_files:
        print("No non_cited_post*.md files found in current directory.")
        return
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
        print("Usage: python3 firecrawl_save.py <url1> [url2] ...\n"
              "       python3 firecrawl_save.py --convert")
        sys.exit(1)

    if sys.argv[1] == "--convert":
        convert_existing()
        return

    if sys.argv[1] == "--from-serp":
        if len(sys.argv) < 3:
            print("Usage: python3 firecrawl_save_noncited.py --from-serp <serp_json_path>")
            sys.exit(1)
        with open(sys.argv[2], encoding="utf-8") as f:
            serp = json.load(f)
        urls = [e["url"] for e in serp.get("non_cited_organic", [])]
        print(f"Loaded {len(urls)} non-cited URLs from {sys.argv[2]}")
    else:
        urls = sys.argv[1:]

    import shutil
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    print(f"Cleared previous non-cited docs in {OUT_DIR}")
    seen = set()
    for raw_url in urls:
        url = clean_url(raw_url)
        if url in seen:
            print(f"  Duplicate (skipped): {url}")
            continue
        seen.add(url)

        filename = os.path.join(OUT_DIR, url_to_filename(url))
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

    print("\nDone.")


if __name__ == "__main__":
    main()
