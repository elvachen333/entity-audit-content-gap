#!/usr/bin/env python3
"""
Retry steps 1–3 for a single model against an existing run folder.

Use this when the full pipeline ran but one model failed (e.g. DataForSEO
upstream rate-limit for Gemini). It does NOT wipe the run folder — only the
named model's subfolder gets overwritten.

Usage:
  python3 retry_model.py --topic disney_cruise_tickets_hk --model gemini

The model argument must be one of: chatgpt, claude, gemini, aio.
Prompts / location / language are read back from the run's run_config.json.
"""

import argparse
import json
import os
import shutil
import sys

import pipeline


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--model", required=True, choices=pipeline.MODELS)
    args = p.parse_args()

    run_dir = os.path.join(pipeline.RUNS_DIR, args.topic)
    config_path = os.path.join(run_dir, "run_config.json")
    if not os.path.exists(config_path):
        sys.exit(f"ERROR: run folder not found: {run_dir}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    prompts  = config["prompts"]
    location = config["location"]
    language = config["language"]
    keyword_label = " | ".join(prompts) if len(prompts) > 1 else prompts[0]

    model_dir = os.path.join(run_dir, args.model)
    # Reset only this model's subfolder
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir)
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

    pipeline.update_run_config(run_dir, args.model, status="pending",
                               reason=None, prompt_count=None,
                               cited_doc_count=None, non_cited_doc_count=None)

    print(f"Retrying {args.model.upper()} for topic={args.topic!r}")
    print(f"  prompts : {prompts}")
    print(f"  location: {location}  language: {language}")

    # Step 1
    serp_outputs = []
    for prompt in prompts:
        out = pipeline.run_serp_for_model(args.model, prompt, location, language, model_dir)
        if out:
            serp_outputs.append(out)

    # AIO abort check (mirrors pipeline.run_pipeline logic)
    if args.model == "aio":
        total_cited = sum(len(s["aio"]["cited_urls"]) for s in serp_outputs)
        has_aio_item = any(s["aio"]["found"] for s in serp_outputs)
        if not has_aio_item or total_cited == 0:
            print("\n  AIO ABORTED — no AI Overview rendered.")
            pipeline.update_run_config(run_dir, args.model, status="aborted",
                                       reason="No ai_overview item or empty cited URL list",
                                       prompt_count=len(serp_outputs))
            return

    if not serp_outputs:
        print(f"\n  {args.model.upper()}: SERP still returned nothing — leaving as failed.")
        pipeline.update_run_config(run_dir, args.model, status="failed",
                                   reason="No SERP output")
        return

    pipeline.update_run_config(run_dir, args.model, status="serp_done",
                               prompt_count=len(serp_outputs))

    # Step 2
    print(f"\n  Firecrawl crawling pooled URLs…")
    pipeline.crawl_for_model(model_dir, serp_outputs)
    pipeline.update_run_config(run_dir, args.model, status="crawl_done")

    # Step 3a
    print(f"\n  Google NLP entity analysis…")
    summary = pipeline.entity_analysis_for_model(model_dir, language)
    pipeline.update_run_config(run_dir, args.model,
                               status="analysis_done",
                               cited_doc_count=summary["cited_doc_count"],
                               non_cited_doc_count=summary["non_cited_doc_count"])

    # Step 3b
    print(f"\n  Visualization…")
    pipeline.visualize_for_model(model_dir, summary, keyword_label)
    pipeline.update_run_config(run_dir, args.model, status="ok")

    print(f"\n{args.model.upper()} retry complete.")
    print(f"  cited_doc_count     = {summary['cited_doc_count']}")
    print(f"  non_cited_doc_count = {summary['non_cited_doc_count']}")


if __name__ == "__main__":
    main()
