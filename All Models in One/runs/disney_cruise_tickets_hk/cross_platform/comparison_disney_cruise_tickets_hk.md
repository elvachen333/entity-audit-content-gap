# Cross-Platform AI Citation Analysis — Disney Cruise Tickets (Hong Kong)

**Date:** 2026-04-21
**Platforms analysed:** ChatGPT (GPT-4.1) · Claude (Sonnet 4.0)
**Topic:** Cheapest way to buy Disney Cruise tickets
**Query:** 迪士尼遊輪票去哪裡買最便宜？ ("Where to buy Disney Cruise tickets cheapest?")
**Locale:** Hong Kong / zh-hk

> **Google AI Overview** did not render for this location/language combination, so it is excluded from this comparison.
> **Google Gemini** was rate-limited upstream by DataForSEO (`3rd Party API Service Unavailable`) and produced no SERP. It is also excluded. Retrying Gemini after 10–20 minutes may succeed.

| Platform | Cited pages | Non-cited pages |
|----------|:-----------:|:---------------:|
| ChatGPT GPT-4.1 | 7 | 15 |
| Claude Sonnet 4.0 | 8 | 18 |

---

## Executive Summary

ChatGPT and Claude agree that **naming the ships, the year, and specific dollar amounts** is non-negotiable. They disagree sharply on article depth: ChatGPT rewards a thin, transactional piece (cited pages are ~3–6× less entity-dense than non-cited); Claude rewards the depth *inside* the pricing section specifically, not breadth.

The single most efficient write-once-rank-on-both addition: **put "2026" in the title and thread 5–6 specific dollar anchors throughout the body**. Both platforms treat this as the strongest single signal.

The biggest strategic split: **booking-mechanics jargon** (IGT / OGT / VGT) is a Claude-exclusive winner and absent from ChatGPT's signal set. Including it helps Claude; it doesn't hurt ChatGPT. Include it.

---

## 1. Universal Signals — Do This for Both Platforms

### 1.1 "2026" in the title (strongest universal signal)

| Entity | ChatGPT lift | Claude lift |
|---|:---:|:---:|
| `2026` | 3.21x | **7.88x** (88% cited coverage) |
| `2025` | 3.21x | — |
| `april 2026` / `summer 2026` / `may 15` | — | all cited-only |

**What to do:** Put a specific year in the H1. Reference at least one specific sailing month or date window in the body. Claude cares more than ChatGPT, but neither platform penalises it — this is the cheapest universal win.

### 1.2 Name every Disney ship explicitly

| Ship entity | ChatGPT lift | Claude lift |
|---|:---:|:---:|
| `magic` (Disney Magic) | **8.57x** | 6.75x |
| `disney treasure` | 4.29x (cited-only) | cited-only |
| `disney wonder` | 2.86x (cited-only) | 4.5x |
| `disney fantasy` | 2.86x (cited-only) | — |
| `disney wish` | — | 4.5x |
| `disney dream` | — | 3.75x (cited-only) |
| `disney adventure` | — | 4.5x |
| `disney cruise line` (CONSUMER_GOOD) | — | **5.0x** (cited-only) |

**What to do:** Write a dedicated paragraph or row per ship, naming each: Disney Magic, Disney Wonder, Disney Fantasy, Disney Dream, Disney Wish, Disney Treasure, Disney Adventure. The ship name itself is the entity unit — "one of Disney's ships" or "the fleet" does not score. Claude additionally expects "Disney Cruise Line" as a full brand phrase.

### 1.3 Specific dollar anchors — not ranges

| Anchor | ChatGPT lift | Claude lift |
|---|:---:|:---:|
| `$50` | 4.29x (cited-only) | 3.75x (cited-only) |
| `$100` | 4.29x (cited-only) | — |
| `$200` | 6.43x | — |
| `$250` | — | 4.5x |
| `$300` | — | 6.75x |
| `$500` | **5.71x** (cited-only) | — |
| `$1,000` / `$1000` | — | **9.0x** / 6.75x |
| `$2,000` | 2.86x (cited-only) | — |
| `$2,500` | 4.29x | — |
| `$3,000` | 4.29x | 4.5x |
| `$4,000` | **6.43x** | — |

**What to do:** Build a pricing table with these as cell values — **not** ranges like "$500–$1,000." ChatGPT spreads across a wider anchor set ($50 → $4,000); Claude concentrates on $1,000 and $300. Include both spreads in a "Savings benchmarks" table and in per-ship pricing callouts. Do not use approximate phrasing.

### 1.4 Name Disney as the brand in every section

| Signal | ChatGPT | Claude |
|---|:---:|:---:|
| `disney` (ORGANIZATION) | 5.36x (71% cited vs 13% non-cited) | **4.5x** (100% cited vs 22% non-cited) |

**What to do:** Do not replace "Disney" with pronouns or shortened forms. Every major section should name the Disney brand explicitly, not just in the title.

### 1.5 Cabin-category vocabulary

| Term | ChatGPT | Claude |
|---|:---:|:---:|
| `inside` (stateroom) | 4.29x (OTHER/CONSUMER_GOOD) | 4.5x (PERSON tag — noise — but signal is present) |
| `oceanview` | — | 3.0x |
| `verandah` | — | 4.5x |

**What to do:** Use Disney's own cabin terminology — "inside," "oceanview," "verandah" — and have at least one of them per booking-tier section. Both platforms reward the vocabulary; Claude rewards a wider spread.

---

## 2. Platform-Specific Signals — Tune Per Platform

### 2.1 Claude-exclusive signals

These signals are significant for Claude and absent from ChatGPT's data.

| Signal | Claude lift | Other |
|---|:---:|:---:|
| **IGT / OGT / VGT guarantee codes** | 3.75x – 5.0x (all cited-only) | Not in ChatGPT signals |
| **Price density across the body** | 2.52x density lift (outlier) | ChatGPT density lift < 1.0x |
| **`port expenses` / `taxes` / `fees`** (itemised total-cost breakdown) | 4.5x each | Not in ChatGPT signals |
| **PHONE_NUMBER coverage** | 2.25x | 1.07x (marginal on ChatGPT) |
| **`april 2026` / `summer 2026` / `may 15`** (specific sailing dates) | cited-only | Only year-level signal on ChatGPT |

**What to do for Claude:** Add a dedicated "Guarantee booking codes explained" block covering IGT, OGT, and VGT. Include a "What's included vs what's extra" section with port expenses, taxes, and fees as named line items. Show a booking hotline. Thread pricing *throughout* the article rather than siloing in a pricing table.

### 2.2 ChatGPT-exclusive signals

These signals are significant for ChatGPT and absent from Claude's data.

| Signal | ChatGPT lift | Other |
|---|:---:|:---:|
| **`costco`** (named reseller) | 2.86x (cited-only) | Not in Claude signals |
| **`wi-fi`** (onboard add-on) | 4.29x (cited-only) | Not in Claude signals |
| **`access`** (premium/concierge access) | 4.29x | Not in Claude signals |
| **`december 2024`** (specific booking window) | 2.86x (cited-only) | Year-level only on Claude |
| **Shorter article length** | Cited pages 3–6× lower entity density than non-cited | Not directional on Claude |

**What to do for ChatGPT:** Name Costco Travel as the reseller channel for cheap tickets — not generic "third-party sites." Include onboard-cost line items like Wi-Fi packages and premium "access" (concierge, character breakfasts). Keep total article length short (600–900 words) rather than a 2,000-word guide.

---

## 3. The Conflict Zone — Signals That Pull in Opposite Directions

| Signal | ChatGPT wants | Claude wants | Resolution |
|---|:---:|:---:|:---:|
| Article length / entity density | **Thin** (3–6× lower density than non-cited) | Price density **2.52x above** non-cited | Keep non-price sections short (ship names, booking channels, cabins each as one-liners) but saturate the pricing section with repeated dollar anchors. |
| LOCATION coverage | Negative (0.71x) | Neutral (1.0x) | Omit dedicated port-of-call / destination sections. Mention ports only as "departure: Miami" one-liners. |
| `WORK_OF_ART` / `EVENT` | Strongly negative (0.39x / 0.00x) | Strongly negative (0.28x / 0.00x) | **Both agree** to skip — no show lists, dining venues, character meet-and-greets, or sailing-event narratives. (Not actually a conflict — listed here because it is the one case where both platforms *penalise* the same thing.) |
| PRICE coverage vs density | Negative coverage (0.82x), negative density | Near-parity coverage, **strongly positive density (2.52x)** | Don't add a dedicated "prices" page. Instead, repeat the same 5–6 dollar anchors throughout the body — this satisfies Claude's density demand without triggering ChatGPT's coverage penalty for over-stuffing. |

---

## 4. Master Checklist — Write Once, Rank on Both

Items are tagged with the platform(s) they serve. `[All]` = both ChatGPT and Claude.

### Structure
- [ ] Title includes **"2026"** (or the current sailing year) `[All]`
- [ ] Article is **short to medium length** — closer to 900 words than 2,000 `[ChatGPT]`
- [ ] Pricing is **woven throughout the body**, not siloed in one table `[Claude]`

### Booking-mechanics coverage
- [ ] Dedicated explainer for **IGT / OGT / VGT guarantee codes** `[Claude]`
- [ ] **Costco Travel** named as a booking channel `[ChatGPT]`
- [ ] Booking **hotline or travel-agent phone** number visible `[Claude]`
- [ ] A specific booking-window cue — "book by December 2024," "for April 2026 sailings" `[All]`

### Pricing (the repeat-me-throughout list)
- [ ] Price anchors as **exact dollar amounts**, not ranges: `$50`, `$100`, `$200`, `$300`, `$500`, `$1,000`, `$3,000` `[All]`
- [ ] A total-cost breakdown section naming **port expenses, taxes, fees** `[Claude]`

### Ships — name each one
- [ ] **Disney Magic, Disney Wonder, Disney Fantasy, Disney Dream, Disney Wish, Disney Treasure, Disney Adventure** each named by ship name `[All]`
- [ ] Full brand phrase **"Disney Cruise Line"** used in the intro and at least one section heading `[Claude]`

### Cabins and onboard
- [ ] Cabin categories named: **inside, oceanview, verandah, concierge** `[All]`
- [ ] Onboard add-ons named: **Wi-Fi**, **premium access** (concierge, character breakfasts) `[ChatGPT]`

### What to Avoid
- [ ] ❌ No **show names, character meet-and-greets, or dining-venue tours** (`WORK_OF_ART` is the strongest negative signal on both platforms) `[All]`
- [ ] ❌ No dedicated **ports / destinations / itinerary** section (`LOCATION` penalty on ChatGPT) `[ChatGPT]`
- [ ] ❌ No sailing-event narratives (pirate night, sail-away) — `EVENT` coverage is **zero** in cited pages on both platforms `[All]`
- [ ] ❌ No approximate price phrasing ("around $500," "up to ~$1,000") — use exact numbers `[All]`
- [ ] ❌ No "one of Disney's ships" — always use the specific ship name `[All]`
