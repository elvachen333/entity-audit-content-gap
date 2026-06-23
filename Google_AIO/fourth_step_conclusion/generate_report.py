#!/usr/bin/env python3
"""
Step 4: Copywriting Conclusion Report

Reads summary.json and cited_winning_entities.csv from third_step_google_entity_analysis
and generates a structured Markdown report for the copywriting team:
  - Which entity types to prioritise (coverage & density lift)
  - Specific named entities / topics that appear in cited docs
  - A writing checklist with actionable items

Usage:
  python3 generate_report.py
  python3 generate_report.py --summary /custom/path/summary.json

Output:
  fourth_step_conclusion/copywriting_report_<keyword>.md
"""

import os
import sys
import json
import csv
import re
import argparse
from datetime import date
from collections import defaultdict

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
THIRD_STEP    = os.path.join(BASE_DIR, "..", "third_step_google_entity_analysis")
SUMMARY_PATH  = os.path.join(THIRD_STEP, "results", "summary.json")
CSV_PATH      = os.path.join(THIRD_STEP, "charts", "cited_winning_entities.csv")
OUT_DIR       = BASE_DIR
# ─────────────────────────────────────────────────────────────────────────────

# Human-readable labels for copywriters (Traditional Chinese)
ENTITY_LABELS_ZH = {
    "ADDRESS":       "地址",
    "LOCATION":      "地點／景點",
    "ORGANIZATION":  "機構／品牌",
    "EVENT":         "活動／節目",
    "WORK_OF_ART":   "作品／節目名稱",
    "PERSON":        "人物",
    "DATE":          "日期／時間",
    "PRICE":         "價格資訊",
    "CONSUMER_GOOD": "商品／產品",
    "NUMBER":        "數字／統計",
    "PHONE_NUMBER":  "聯絡電話",
    "OTHER":         "其他關鍵概念",
}

# Writing advice per entity type
ENTITY_ADVICE = {
    "ADDRESS": (
        "在文章中提供確切地址（例如：台北市某區某路某號），"
        "有助 AI 辨識具體地點，提升本地查詢的引用機率。"
    ),
    "LOCATION": (
        "明確點名景點、場館、區域名稱，"
        "避免只用「附近」、「那裡」等模糊字眼。"
    ),
    "ORGANIZATION": (
        "引用官方機構、品牌或主辦單位全名，"
        "讓 AI 能建立可信的組織實體連結。"
    ),
    "EVENT": (
        "說明活動全名、舉辦期間與主題，"
        "季節性或限定活動尤其應具體描述。"
    ),
    "WORK_OF_ART": (
        "提及展覽、節目、電影、書籍等作品的正式名稱，"
        "而非僅以「這個展覽」、「那部電影」帶過。"
    ),
    "PERSON": (
        "點名相關人物（館長、策展人、代言人）能增加內容權威性，"
        "但需確保資訊正確。"
    ),
    "DATE": (
        "加入具體開放日期、活動時段、季節限定時間，"
        "可幫助 AI 判斷內容時效性與相關性。"
    ),
    "PRICE": (
        "列出實際票價、優惠條件與適用年齡，"
        "價格資訊是親子旅遊類查詢的高需求欄位。"
    ),
    "CONSUMER_GOOD": (
        "介紹具體商品名稱（紀念品、餐飲品項、租借設備），"
        "增加產品層級的實體密度。"
    ),
    "NUMBER": (
        "使用具體數字（樓層、容納人數、展品數量、距離），"
        "比模糊描述更容易被 AI 擷取為事實依據。"
    ),
    "PHONE_NUMBER": (
        "提供客服電話或訂票專線，"
        "對實際查詢行動有幫助，但非引用的關鍵因素。"
    ),
    "OTHER": (
        "涵蓋主題概念詞彙（如：親子展覽、互動體驗、STEM），"
        "這些詞彙是 AI 理解文章主題的重要線索。"
    ),
}


def load_summary(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: str) -> list:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def safe_filename(text: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]', '_', text)[:60]


def pct(v):
    return f"{float(v) * 100:.0f}%"


def fmt_lift(v):
    v = float(v)
    arrow = "▲" if v > 1.05 else ("▼" if v < 0.95 else "─")
    return f"{arrow} {v:.2f}x"


# ── Noise filter: skip entities that are unlikely to be actionable ────────────
SKIP_PATTERNS = re.compile(
    r'^(\d+[\d,./\s]*\d*|[a-zA-Z]{1,2}|首頁|官方|各地|方位|理由|貨幣)$'
)

def is_actionable(name: str, etype: str) -> bool:
    """Return False for very generic or noisy entity names."""
    name = name.strip()
    if len(name) <= 1:
        return False
    if SKIP_PATTERNS.match(name) and etype not in ("ADDRESS", "LOCATION", "ORGANIZATION", "EVENT", "PERSON", "WORK_OF_ART"):
        return False
    return True


def build_report(summary: dict, csv_rows: list, keyword: str) -> str:
    c_n  = summary["cited_doc_count"]
    n_n  = summary["non_cited_doc_count"]
    lift = summary["lift"]
    c_m  = summary["cited_metrics"]
    n_m  = summary["non_cited_metrics"]
    gaps = summary.get("top_named_entity_gaps", [])

    # ── Classify entity types ─────────────────────────────────────────────────
    must_have   = []   # coverage_lift > 1.05
    neutral     = []   # 0.95 <= coverage_lift <= 1.05
    avoid       = []   # coverage_lift < 0.95

    for t, v in sorted(lift.items(), key=lambda x: -x[1]["coverage_lift"]):
        cl = v["coverage_lift"]
        dl = v["density_lift"]
        label = ENTITY_LABELS_ZH.get(t, t)
        cc = pct(c_m.get(t, {}).get("coverage_rate", 0))
        nc = pct(n_m.get(t, {}).get("coverage_rate", 0))
        row = (t, label, cl, dl, cc, nc)
        if cl > 1.05:
            must_have.append(row)
        elif cl >= 0.95:
            neutral.append(row)
        else:
            avoid.append(row)

    # ── Group actionable named entities by type ───────────────────────────────
    entities_by_type = defaultdict(list)
    for g in gaps:
        if g["lift"] >= 1.5 and is_actionable(g["name"], g["type"]):
            entities_by_type[g["type"]].append(g)

    # ── Build Markdown ────────────────────────────────────────────────────────
    today = date.today().isoformat()
    lines = []

    lines += [
        f"# 內容撰寫建議報告",
        f"",
        f"**關鍵字：** {keyword}  ",
        f"**分析日期：** {today}  ",
        f"**引用頁面：** {c_n} 篇　**非引用頁面：** {n_n} 篇",
        f"",
        f"---",
        f"",
        f"## 一、核心發現摘要",
        f"",
    ]

    # Summarise must-have types
    if must_have:
        lines.append("被 AI 引用的頁面，在以下實體類型的覆蓋率**顯著高於**未被引用頁面，"
                     "代表撰寫時應優先涵蓋：")
        lines.append("")
        for t, label, cl, dl, cc, nc in must_have:
            lines.append(f"- **{label}**（引用覆蓋率 {cc}，非引用 {nc}，Coverage Lift {cl:.2f}x）")
        lines.append("")

    if avoid:
        lines.append("以下類型在引用頁面中反而較少出現，無需特別堆砌：")
        lines.append("")
        for t, label, cl, dl, cc, nc in avoid:
            lines.append(f"- {label}（Coverage Lift {cl:.2f}x）")
        lines.append("")

    lines += [
        "---",
        "",
        "## 二、實體類型詳細分析",
        "",
        "| 實體類型 | 中文說明 | Coverage Lift | Density Lift | 引用覆蓋率 | 非引用覆蓋率 |",
        "|----------|----------|:-------------:|:------------:|:----------:|:------------:|",
    ]
    for t, label, cl, dl, cc, nc in must_have + neutral + avoid:
        lines.append(f"| `{t}` | {label} | {fmt_lift(cl)} | {fmt_lift(dl)} | {cc} | {nc} |")

    lines += [
        "",
        "> **Coverage Lift > 1.05x** = 引用頁面明顯較多包含此類實體，應主動加入  ",
        "> **Coverage Lift ≈ 1.00x** = 引用與非引用頁面相近，維持正常密度即可  ",
        "> **Coverage Lift < 0.95x** = 引用頁面反而較少，勿過度堆砌  ",
        "",
        "---",
        "",
        "## 三、高優先級撰寫建議（按實體類型）",
        "",
    ]

    priority_types = [row[0] for row in must_have] or list(ENTITY_LABELS_ZH.keys())[:6]
    for t in priority_types:
        label = ENTITY_LABELS_ZH.get(t, t)
        advice = ENTITY_ADVICE.get(t, "")
        entities = entities_by_type.get(t, [])

        lines.append(f"### {label}（`{t}`）")
        lines.append("")
        lines.append(f"**撰寫建議：** {advice}")
        lines.append("")

        if entities:
            lines.append("**引用頁面中出現、非引用頁面罕見的具體詞彙（建議納入文章）：**")
            lines.append("")
            for g in entities[:12]:
                cited_pct  = f"{g['cited_rate'] * 100:.0f}%"
                ncited_pct = f"{g['non_cited_rate'] * 100:.0f}%"
                lines.append(
                    f"- `{g['name']}` — 引用頁出現率 {cited_pct}，非引用 {ncited_pct}，Lift {float(g['lift']):.1f}x"
                )
            lines.append("")
        else:
            lines.append("*（此類型無足夠樣本提供具體詞彙建議）*")
            lines.append("")

    # ── Types not in must_have but have entities ──────────────────────────────
    extra_types = [t for t in entities_by_type if t not in priority_types]
    if extra_types:
        lines += [
            "---",
            "",
            "## 四、其他值得納入的具體詞彙",
            "",
            "以下詞彙雖屬非優先類型，但在引用頁面中明顯高頻，仍建議適度提及：",
            "",
        ]
        for t in extra_types:
            label = ENTITY_LABELS_ZH.get(t, t)
            lines.append(f"**{label}：**")
            for g in entities_by_type[t][:8]:
                cited_pct  = f"{g['cited_rate'] * 100:.0f}%"
                ncited_pct = f"{g['non_cited_rate'] * 100:.0f}%"
                lines.append(
                    f"- `{g['name']}` （引用 {cited_pct} / 非引用 {ncited_pct}，Lift {float(g['lift']):.1f}x）"
                )
            lines.append("")

    # ── Writing checklist ─────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## 五、撰寫檢查清單",
        "",
        "在提交文章前，請確認以下項目：",
        "",
    ]

    checklist = []
    for t, label, cl, dl, cc, nc in must_have:
        advice_short = ENTITY_ADVICE.get(t, "").split("，")[0]
        checklist.append(f"- [ ] **{label}**：{advice_short}")

    # Always-useful checks
    checklist += [
        "- [ ] 文章是否至少包含 **1 個完整地址**（街道門牌）？",
        "- [ ] 是否點名 **官方機構或品牌全稱**（避免只說「官方網站」）？",
        "- [ ] 是否列出 **具體開放時間或活動日期**？",
        "- [ ] 是否包含 **實際票價或費用**（如適用）？",
        "- [ ] 關鍵景點／地點名稱是否使用 **正式全名**（避免縮寫）？",
        "- [ ] 文章是否自然涵蓋了高 Lift 的 **具體詞彙**（見第三節清單）？",
    ]

    lines += checklist
    lines += [
        "",
        "---",
        "",
        "## 六、背景說明",
        "",
        "本報告依據 Google NLP 實體分析結果產生。",
        "「Coverage Lift」= 引用頁面中含有該類實體的比例 ÷ 非引用頁面的比例；",
        "數值 > 1.0 代表被 AI 引用的頁面更常包含此類實體。",
        "",
        f"> 分析樣本：{c_n} 篇 AI 引用頁面 vs {n_n} 篇有機搜尋頁面（{keyword}）",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate copywriting report from entity analysis")
    parser.add_argument("--summary", default=SUMMARY_PATH, help="Path to summary.json")
    parser.add_argument("--csv",     default=CSV_PATH,     help="Path to cited_winning_entities.csv")
    parser.add_argument("--keyword", default="",           help="Keyword label for the report title")
    args = parser.parse_args()

    if not os.path.exists(args.summary):
        print(f"ERROR: summary.json not found at {args.summary}")
        print("Run entity_analysis.py and entity_visualize.py first.")
        sys.exit(1)

    summary  = load_summary(args.summary)
    csv_rows = load_csv(args.csv)

    # Try to infer keyword from the summary path if not provided
    keyword = args.keyword
    if not keyword:
        # Walk up to find the serp_*.json in first_step_aio_seo
        aio_dir = os.path.join(os.path.dirname(args.summary), "..", "..", "first_step_aio_seo")
        serp_files = [f for f in os.listdir(aio_dir) if f.startswith("serp_") and f.endswith(".json")] \
            if os.path.isdir(aio_dir) else []
        if serp_files:
            # Use the most recently modified serp file
            serp_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(aio_dir, f)),
                reverse=True
            )
            with open(os.path.join(aio_dir, serp_files[0]), encoding="utf-8") as f:
                serp_data = json.load(f)
            keyword = serp_data.get("keyword", "")
        if not keyword:
            keyword = "（關鍵字未指定）"

    print(f"Generating report for: {keyword!r}")
    report = build_report(summary, csv_rows, keyword)

    out_file = os.path.join(OUT_DIR, f"copywriting_report_{safe_filename(keyword)}.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Saved → {out_file}")
    print(f"\nReport preview (first 20 lines):")
    for line in report.split("\n")[:20]:
        print(" ", line)


if __name__ == "__main__":
    main()
