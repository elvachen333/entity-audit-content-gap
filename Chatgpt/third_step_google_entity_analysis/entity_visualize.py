#!/usr/bin/env python3
"""
Google NLP Entity Analysis — Step 2: generate all charts from summary.json.

Usage:
  python3 entity_visualize.py

Outputs (saved to charts/ subfolder):
  1. entity_lift_bar.png         — lift per entity type (like Gauge Image 1)
  2. coverage_rate_bar.png       — % pages with each entity type, cited vs non-cited
  3. entity_distribution_pie.png — share of entity types in each pool
  4. top_entities_gap.png        — named entity lift gap (top 20)
  5. salience_comparison.png     — avg salience per entity type, cited vs non-cited
  6. density_scatter.png         — cited vs non-cited density bubble chart
"""

import os
import json
import glob
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = ["PingFang HK", "Heiti TC", "Arial Unicode MS", "DejaVu Sans"]
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR  = os.path.join(BASE_DIR, "results")
CHARTS_DIR   = os.path.join(BASE_DIR, "charts")
SUMMARY_PATH = os.path.join(RESULTS_DIR, "summary.json")


def _detect_keyword() -> str:
    """Read keyword from the most recently modified serp_*.json in first_step_aio_seo/."""
    serp_dir = os.path.join(BASE_DIR, "..", "first_step_aio_seo")
    pattern  = os.path.join(serp_dir, "serp_*.json")
    files    = [f for f in glob.glob(pattern) if not f.endswith("_raw.json")]
    if not files:
        return ""
    latest = max(files, key=os.path.getmtime)
    try:
        with open(latest, encoding="utf-8") as f:
            return json.load(f).get("keyword", "")
    except Exception:
        return ""


KEYWORD = _detect_keyword() or "（關鍵字未知）"

# Dark theme matching reference images
DARK_BG   = "#0d1117"
PANEL_BG  = "#161b22"
GOLD      = "#f5a623"
TEAL      = "#4ec9c9"
TEXT      = "#e0e0e0"
GRIDLINE  = "#2a2a3a"
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


def dark_fig(w=14, h=7):
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


def load_summary():
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Shared lift bar drawing helper ───────────────────────────────────────────
def _draw_lift_bar(summary, lift_key, title, ylabel, filename):
    lift   = summary["lift"]
    types  = [t for t in ENTITY_ORDER if t in lift]
    values = [lift[t].get(lift_key, 0) for t in types]
    labels = [ENTITY_LABELS.get(t, t) for t in types]

    paired = sorted(zip(values, labels, types), reverse=True)
    values, labels, types = zip(*paired) if paired else ([], [], [])

    fig, ax = dark_fig(14, 7)
    colors = [GOLD if v >= 1.0 else TEAL for v in values]
    bars = ax.bar(labels, [v - 1.0 for v in values], color=colors,
                  width=0.6, zorder=3)
    ax.axhline(0, color=TEXT, linewidth=1.0, zorder=4)

    for bar, v in zip(bars, values):
        ypos = bar.get_height() + 0.005 if v >= 1.0 else bar.get_height() - 0.02
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                f"{v:.2f}x", ha="center", va="bottom" if v >= 1.0 else "top",
                color=TEXT, fontsize=9, fontweight="bold")

    ax.set_title(title, color=TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Entity type", color=TEXT, fontsize=10)
    ax.set_ylabel(ylabel, color=TEXT, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x+1:.2f}x"))

    pos_patch = mpatches.Patch(color=GOLD, label="Positive lift (>1.0x)")
    neg_patch = mpatches.Patch(color=TEAL, label="Negative lift (<1.0x)")
    ax.legend(handles=[pos_patch, neg_patch], facecolor=PANEL_BG,
              labelcolor=TEXT, fontsize=9, framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 1: Entity Density Lift Bar ─────────────────────────────────────────
def chart_lift_bar(summary):
    _draw_lift_bar(
        summary,
        lift_key  = "density_lift",
        title     = f"Entity Density Lift — Cited vs Non-Cited  [{KEYWORD}]\n(mentions per 1,000 words: cited ÷ non-cited)",
        ylabel    = "Lift vs. non-cited pages\n(density ratio)",
        filename  = "1_entity_density_lift_bar.png",
    )


# ── Chart 1b: Entity Coverage Lift Bar ───────────────────────────────────────
def chart_coverage_lift_bar(summary):
    _draw_lift_bar(
        summary,
        lift_key  = "coverage_lift",
        title     = f"Entity Coverage Lift — Cited vs Non-Cited  [{KEYWORD}]\n(% pages containing entity type: cited ÷ non-cited)",
        ylabel    = "Lift vs. non-cited pages\n(coverage ratio)",
        filename  = "1b_entity_coverage_lift_bar.png",
    )


# ── Chart 2: Coverage Rate Comparison Bar ────────────────────────────────────
def chart_coverage_rate(summary):
    c_m  = summary["cited_metrics"]
    n_m  = summary["non_cited_metrics"]
    types = [t for t in ENTITY_ORDER if t in c_m or t in n_m]
    labels = [ENTITY_LABELS.get(t, t) for t in types]

    c_vals = [c_m.get(t, {}).get("coverage_rate", 0) * 100 for t in types]
    n_vals = [n_m.get(t, {}).get("coverage_rate", 0) * 100 for t in types]

    x = np.arange(len(types))
    w = 0.38
    fig, ax = dark_fig(14, 7)
    ax.bar(x - w/2, c_vals, w, label="Cited",     color=GOLD,  zorder=3, alpha=0.9)
    ax.bar(x + w/2, n_vals, w, label="Non-cited", color=TEAL,  zorder=3, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TEXT, fontsize=9)
    ax.set_ylabel("% of pages containing entity type", color=TEXT, fontsize=10)
    ax.set_title(f"Entity Coverage Rate — Cited vs Non-Cited  [{KEYWORD}]",
                 color=TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "2_coverage_rate_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 3: Entity Distribution Pie ────────────────────────────────────────
def chart_distribution_pie(summary):
    c_m = summary["cited_metrics"]
    n_m = summary["non_cited_metrics"]

    def get_shares(metrics):
        total = sum(v.get("total_mentions", 0) for v in metrics.values())
        if total == 0:
            return {}, 0
        return {t: v.get("total_mentions", 0) / total * 100
                for t, v in metrics.items()
                if v.get("total_mentions", 0) > 0}, total

    c_shares, c_total = get_shares(c_m)
    n_shares, n_total = get_shares(n_m)

    palette = plt.cm.get_cmap("tab20", 12)
    colors  = [palette(i) for i in range(12)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor=DARK_BG)
    for ax, shares, label, total in [
        (axes[0], c_shares, "Cited",     c_total),
        (axes[1], n_shares, "Non-Cited", n_total),
    ]:
        ax.set_facecolor(PANEL_BG)
        if not shares:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", color=TEXT)
            continue
        sorted_shares = sorted(shares.items(), key=lambda x: x[1], reverse=True)
        labels_pie = [ENTITY_LABELS.get(t, t).replace("\n", " ")
                      for t, _ in sorted_shares]
        vals_pie   = [v for _, v in sorted_shares]
        wedges, texts, autotexts = ax.pie(
            vals_pie,
            labels=labels_pie,
            autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
            colors=colors[:len(vals_pie)],
            startangle=140,
            textprops={"color": TEXT, "fontsize": 8},
        )
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(DARK_BG)
        ax.set_title(f"{label} Pool — Entity Distribution\n(n={total} mentions)",
                     color=TEXT, fontsize=11, fontweight="bold")

    plt.suptitle(f"Entity Type Distribution  [{KEYWORD}]",
                 color=TEXT, fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "3_entity_distribution_pie.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 4: Top Named Entities Gap ─────────────────────────────────────────
def chart_top_entities_gap(summary, top_n=40):
    gaps = summary.get("top_named_entity_gaps", [])[:top_n]
    if not gaps:
        print("  SKIP: no named entity gap data.")
        return

    df = pd.DataFrame(gaps)
    df = df.sort_values("lift", ascending=True)

    fig, ax = dark_fig(13, max(6, len(df) * 0.38))
    colors = [GOLD if row["lift"] >= 1.0 else TEAL for _, row in df.iterrows()]
    bars = ax.barh(df["name"] + "  [" + df["type"] + "]",
                   df["lift"], color=colors, height=0.7, zorder=3)
    ax.axvline(1.0, color=TEXT, linewidth=1.0, linestyle="--", zorder=4)

    for bar, v in zip(bars, df["lift"]):
        ax.text(v + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{v:.2f}x", va="center", color=TEXT, fontsize=8)

    ax.set_xlabel("Lift (cited frequency / non-cited frequency)", color=TEXT, fontsize=10)
    ax.set_title(f"Top Named Entities Gap — Cited vs Non-Cited  [{KEYWORD}]",
                 color=TEXT, fontsize=12, fontweight="bold", pad=12)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "4_top_entities_gap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 5: Avg Salience Comparison ────────────────────────────────────────
def chart_salience(summary):
    c_m = summary["cited_metrics"]
    n_m = summary["non_cited_metrics"]
    types = [t for t in ENTITY_ORDER if t in c_m or t in n_m]
    labels = [ENTITY_LABELS.get(t, t) for t in types]

    c_sal = [c_m.get(t, {}).get("avg_salience", 0) for t in types]
    n_sal = [n_m.get(t, {}).get("avg_salience", 0) for t in types]

    x = np.arange(len(types))
    w = 0.38
    fig, ax = dark_fig(14, 7)
    ax.bar(x - w/2, c_sal, w, label="Cited",     color=GOLD,  zorder=3, alpha=0.9)
    ax.bar(x + w/2, n_sal, w, label="Non-cited", color=TEAL,  zorder=3, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TEXT, fontsize=9)
    ax.set_ylabel("Avg salience score (0–1, higher = more central to doc)",
                  color=TEXT, fontsize=10)
    ax.set_title(f"Avg Entity Salience — Cited vs Non-Cited  [{KEYWORD}]",
                 color=TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, fontsize=10)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "5_salience_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 6: Density Scatter ─────────────────────────────────────────────────
def chart_density_scatter(summary):
    lift   = summary["lift"]
    c_m    = summary["cited_metrics"]
    n_m    = summary["non_cited_metrics"]
    types  = [t for t in ENTITY_ORDER if t in lift]

    c_dens = [c_m.get(t, {}).get("density_per_1k", 0) for t in types]
    n_dens = [n_m.get(t, {}).get("density_per_1k", 0) for t in types]
    lifts  = [lift[t]["density_lift"] for t in types]
    labels = [ENTITY_LABELS.get(t, t).replace("\n", " ") for t in types]

    sizes  = [max(40, l * 120) for l in lifts]
    colors = [GOLD if l >= 1.0 else TEAL for l in lifts]

    fig, ax = dark_fig(11, 8)
    sc = ax.scatter(n_dens, c_dens, s=sizes, c=colors, alpha=0.85, zorder=3)

    # Diagonal = no lift
    all_vals = c_dens + n_dens
    mx = max(all_vals) * 1.15 if all_vals else 1
    ax.plot([0, mx], [0, mx], "--", color=GRIDLINE, linewidth=1, zorder=2,
            label="No lift (1.0x)")

    for x, y, lbl in zip(n_dens, c_dens, labels):
        ax.annotate(lbl, (x, y), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color=TEXT)

    ax.set_xlabel("Non-cited density (entities per 1,000 words)", color=TEXT, fontsize=10)
    ax.set_ylabel("Cited density (entities per 1,000 words)", color=TEXT, fontsize=10)
    ax.set_title(f"Entity Density — Cited vs Non-Cited  [{KEYWORD}]\n"
                 f"(bubble size ∝ lift ratio)", color=TEXT, fontsize=12,
                 fontweight="bold", pad=12)
    ax.legend(facecolor=PANEL_BG, labelcolor=TEXT, fontsize=9)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "6_density_scatter.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── Chart 7: Coverage Lift Heatmap (keyword cluster view) ───────────────────
def chart_cluster_heatmap(summary):
    """One-row heatmap per keyword — mirrors Gauge Image 2.
    Currently single keyword; will grow as more keywords are added.
    """
    lift  = summary["lift"]
    types = [t for t in ENTITY_ORDER if t in lift]
    labels = [ENTITY_LABELS.get(t, t).replace("\n", " ") for t in types]
    values = [[lift[t]["coverage_lift"] for t in types]]

    df = pd.DataFrame(values, index=[KEYWORD], columns=labels)

    fig, ax = plt.subplots(figsize=(14, max(3, len(df) * 1.1)),
                           facecolor=DARK_BG)
    ax.set_facecolor(PANEL_BG)

    sns.heatmap(
        df,
        ax=ax,
        annot=True,
        fmt=".2f",
        cmap=sns.diverging_palette(220, 40, as_cmap=True),
        center=1.0,
        linewidths=0.5,
        linecolor=DARK_BG,
        annot_kws={"size": 10, "color": TEXT},
        cbar_kws={"label": "Coverage lift"},
    )
    ax.set_title(
        f"Entity Coverage Lift by Keyword Cluster  [{KEYWORD}]\n"
        f"(cited coverage rate / non-cited coverage rate)",
        color=TEXT, fontsize=12, fontweight="bold", pad=12,
    )
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.set_ylabel("Keyword cluster", color=TEXT)

    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(colors=TEXT, labelsize=8)
    cbar.set_label("Coverage lift", color=TEXT)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "7_cluster_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"  Saved: {path}")


# ── CSV: Cited-winning entity detail ─────────────────────────────────────────
def export_coverage_gap_csv(summary):
    """
    For every entity TYPE where cited coverage rate > non-cited coverage rate,
    export all specific named entities of that type with full detail:
    entity_type, entity_name, cited_doc_count, non_cited_doc_count,
    cited_coverage_rate, non_cited_coverage_rate, coverage_lift,
    cited_total_mentions, non_cited_total_mentions,
    avg_salience_cited, avg_salience_non_cited
    Sorted by entity_type (coverage lift desc), then entity name coverage desc.
    """
    c_m = summary["cited_metrics"]
    n_m = summary["non_cited_metrics"]
    c_n = summary["cited_doc_count"]
    n_n = summary["non_cited_doc_count"]

    # Entity types where cited coverage > non-cited coverage
    winning_types = {
        t for t in c_m
        if c_m[t].get("coverage_rate", 0) > n_m.get(t, {}).get("coverage_rate", 0)
    }

    # Load individual doc results
    def load_pool_docs(subdir):
        docs = []
        pattern = os.path.join(RESULTS_DIR, subdir, "*.json")
        for path in sorted(glob.glob(pattern)):
            with open(path, encoding="utf-8") as f:
                docs.append(json.load(f))
        return docs

    cited_docs     = load_pool_docs("cited")
    non_cited_docs = load_pool_docs("non_cited")

    # Aggregate per named entity (name + type key)
    def aggregate(docs):
        stats = {}   # key=(name, type) → {doc_count, total_mentions, total_salience}
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
                # Count all mentions regardless of seen
                if key in stats:
                    stats[key]["total_mentions"] += e["mentions"]
        return stats

    c_stats = aggregate(cited_docs)
    n_stats = aggregate(non_cited_docs)

    # Build rows — only for winning entity types
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
        print("  CSV: no rows matched (no winning entity types found).")
        return

    # Sort: entity_type by type-level coverage lift desc, then named entity coverage lift desc
    type_lift = {
        t: round(c_m[t]["coverage_rate"] / n_m.get(t, {}).get("coverage_rate", 0.0001), 4)
        for t in winning_types
    }
    df = pd.DataFrame(rows)
    df["_type_lift"] = df["entity_type"].map(type_lift)
    df = df.sort_values(["_type_lift", "coverage_lift", "cited_doc_count"],
                        ascending=[False, False, False])
    df = df.drop(columns=["_type_lift"])

    out_path = os.path.join(CHARTS_DIR, "cited_winning_entities.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  Saved: {out_path}  ({len(df)} rows, {df['entity_type'].nunique()} entity types)")


def main():
    if not os.path.exists(SUMMARY_PATH):
        print(f"ERROR: {SUMMARY_PATH} not found. Run entity_analysis.py first.")
        return

    import shutil
    if os.path.exists(CHARTS_DIR):
        shutil.rmtree(CHARTS_DIR)
    os.makedirs(CHARTS_DIR)
    summary = load_summary()

    print(f"Generating charts → {CHARTS_DIR}/\n")
    chart_coverage_lift_bar(summary)
    chart_coverage_rate(summary)
    chart_top_entities_gap(summary)
    export_coverage_gap_csv(summary)

    print(f"\nAll outputs saved to {CHARTS_DIR}/")
    print("""
Outputs generated:
  1b_entity_coverage_lift_bar.png  — Coverage lift per entity type (% pages containing)
  2_coverage_rate_bar.png          — Absolute coverage % cited vs non-cited
  4_top_entities_gap.png           — Specific named entities with highest lift
  cited_winning_entities.csv       — Full entity detail for cited-winning types
""")


if __name__ == "__main__":
    main()
