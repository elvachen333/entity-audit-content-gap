#!/usr/bin/env python3
"""
Google NLP Entity Analysis — Step 1: extract entities from all .txt files.

Reads all cited_post*.txt from cited_docs/ and non_cited_post*.txt from non_cited_docs/,
calls Google Natural Language API analyzeEntities on each, and saves per-document
JSON results under third_step_google_entity_analysis/results/.

Usage:
  python3 entity_analysis.py

Output:
  results/cited/<filename>.json
  results/non_cited/<filename>.json
  results/summary.json   ← aggregated lift metrics for visualisation
"""

import os
import json
import glob
import re

from google.cloud import language_v1
from google.oauth2 import service_account

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT = os.path.join(BASE_DIR, "service_account.json")
CITED_DIR       = os.path.join(BASE_DIR, "..", "cited_docs")
NON_CITED_DIR   = os.path.join(BASE_DIR, "..", "non_cited_docs")
RESULTS_DIR     = os.path.join(BASE_DIR, "results")
# ─────────────────────────────────────────────────────────────────────────────

# Google NLP entity types we care about (maps API enum → display label)
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


def make_client():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT,
        scopes=["https://www.googleapis.com/auth/cloud-language"],
    )
    return language_v1.LanguageServiceClient(credentials=creds)


def word_count(text: str) -> int:
    return max(len(text.split()), 1)


def analyze_file(client, txt_path: str) -> dict:
    with open(txt_path, encoding="utf-8") as f:
        text = f.read().strip()

    if not text or len(text) < 20:
        print(f"  SKIP (too short): {os.path.basename(txt_path)}")
        return None

    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language="zh-TW",
    )

    try:
        response = client.analyze_entities(
            document=document,
            encoding_type=language_v1.EncodingType.UTF8,
        )
    except Exception as e:
        print(f"  ERROR: {os.path.basename(txt_path)}: {e}")
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
    # Count entities per type
    type_counts = {}
    type_salience = {}
    for e in entities:
        t = e["type"]
        type_counts[t]   = type_counts.get(t, 0) + e["mentions"]
        type_salience[t] = type_salience.get(t, 0.0) + e["salience"]

    return {
        "file":         os.path.basename(txt_path),
        "word_count":   wc,
        "entity_count": len(entities),
        "entities":     entities,
        "type_counts":  type_counts,
        "type_salience": type_salience,
    }


def process_pool(client, txt_glob: str, label: str) -> list:
    files = sorted(glob.glob(txt_glob))
    print(f"\n── {label} pool: {len(files)} files ──────────────────────────")
    results = []
    for path in files:
        print(f"  Analyzing: {os.path.basename(path)}")
        result = analyze_file(client, path)
        if result:
            results.append(result)
    return results


def compute_summary(cited: list, non_cited: list) -> dict:
    """Compute per-entity-type metrics and lift for both pools."""

    def pool_metrics(docs):
        total_words = sum(d["word_count"] for d in docs)
        n = len(docs)
        type_total_mentions = {}
        type_doc_count      = {}   # how many docs have >=1 entity of this type
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

    # Lift = cited_density / non_cited_density (per 1k words)
    all_types = set(list(cited_m) + list(non_cited_m))
    lift = {}
    for t in all_types:
        c_density = cited_m.get(t, {}).get("density_per_1k", 0)
        n_density = non_cited_m.get(t, {}).get("density_per_1k", 0)
        c_coverage = cited_m.get(t, {}).get("coverage_rate", 0)
        n_coverage = non_cited_m.get(t, {}).get("coverage_rate", 0)

        lift[t] = {
            "density_lift":  round(c_density  / n_density  if n_density  > 0 else 0, 4),
            "coverage_lift": round(c_coverage / n_coverage if n_coverage > 0 else 0, 4),
            "cited_density":    c_density,
            "non_cited_density": n_density,
            "cited_coverage":    c_coverage,
            "non_cited_coverage": n_coverage,
        }

    return {
        "cited_metrics":     cited_m,
        "non_cited_metrics": non_cited_m,
        "lift":              lift,
        "cited_doc_count":   len(cited),
        "non_cited_doc_count": len(non_cited),
    }


def top_named_entities_gap(cited: list, non_cited: list, top_n: int = 40) -> list:
    """Find specific entity names with highest lift (cited vs non-cited frequency)."""
    def name_freq(docs):
        freq = {}
        n = len(docs)
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
        if c_rate + n_rate < 0.05:   # skip very rare entities
            continue
        lift = c_rate / n_rate if n_rate > 0 else c_rate * 10
        gaps.append({
            "name":          key[0],
            "type":          key[1],
            "cited_rate":    round(c_rate, 4),
            "non_cited_rate": round(n_rate, 4),
            "lift":          round(lift, 4),
        })

    gaps.sort(key=lambda x: x["lift"], reverse=True)
    return gaps[:top_n]


def main():
    import shutil
    for sub in ("cited", "non_cited"):
        sub_dir = os.path.join(RESULTS_DIR, sub)
        if os.path.exists(sub_dir):
            shutil.rmtree(sub_dir)
        os.makedirs(sub_dir)
    # Also remove stale summary
    summary_path = os.path.join(RESULTS_DIR, "summary.json")
    if os.path.exists(summary_path):
        os.remove(summary_path)
    print("Cleared previous results.")

    print("Initialising Google NLP client…")
    client = make_client()

    cited_results = process_pool(
        client,
        os.path.join(CITED_DIR, "cited_post*.txt"),
        "CITED",
    )
    non_cited_results = process_pool(
        client,
        os.path.join(NON_CITED_DIR, "non_cited_post*.txt"),
        "NON-CITED",
    )

    # Save individual results
    for r in cited_results:
        out = os.path.join(RESULTS_DIR, "cited", r["file"].replace(".txt", ".json"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

    for r in non_cited_results:
        out = os.path.join(RESULTS_DIR, "non_cited", r["file"].replace(".txt", ".json"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

    # Compute and save summary
    summary = compute_summary(cited_results, non_cited_results)
    summary["top_named_entity_gaps"] = top_named_entities_gap(cited_results, non_cited_results)

    summary_path = os.path.join(RESULTS_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nSaved individual results → {RESULTS_DIR}/cited/ & non_cited/")
    print(f"Saved summary            → {summary_path}")
    print(f"\nCited docs analysed:     {len(cited_results)}")
    print(f"Non-cited docs analysed: {len(non_cited_results)}")
    print("\nRun entity_visualize.py next to generate charts.")


if __name__ == "__main__":
    main()
