# Copywriting Strategy Report — Claude

**Query:** 迪士尼遊輪票去哪裡買最便宜？ ("Where to buy Disney Cruise tickets cheapest?")
**Platform:** Claude (claude-sonnet-4-0, web_search)
**Locale:** Hong Kong / zh-hk
**Sample:** 8 cited pages vs 18 non-cited pages

---

## 1. Key Insights

- **Claude rewards booking-mechanics literacy — specifically the "guarantee" category codes.** `ogt`, `igt`, and `vgt` (Oceanview Guarantee, Inside Guarantee, Verandah Guarantee — Disney Cruise Line's cheapest cabin-booking categories) appear across 37–50% of cited pages and **zero** non-cited pages. No other AI platform surfaces booking-jargon vocabulary this sharply. An article that doesn't explain these three codes is missing the single most distinguishing signal for Claude citation.
- **Pricing density is the strongest category signal.** PRICE density lift is **2.52x** (the one density-lift outlier above 2x in this dataset) while coverage lift is near parity. Translation: both cited and non-cited pages mention prices, but cited pages mention them ~2.5× more often per 1,000 words. Claude rewards *pricing saturation*, not just a pricing table in a sidebar.
- **Specific sailing years beat evergreen framing.** `2026` appears in 88% of cited pages vs 11% of non-cited (7.88x lift). `april 2026`, `summer 2026`, `may 15`, `2027` are all cited-only. This is the strongest single-entity signal in the Claude pool after pricing.
- **Name every ship in the fleet.** `disney cruise line` (5x CONSUMER_GOOD, cited-only), plus `disney wonder`, `disney wish`, `disney dream`, `disney adventure`, `disney treasure` all appear only in cited pages. `disney` organisation entity is in **100% of cited** pages vs 22% non-cited (4.5x lift) — literally no cited page omits the Disney brand name.
- **Total-cost breakdown matters.** `port expenses`, `taxes`, `fees` each appear at 4.5x lift (25% cited vs 5.6% non-cited). Unlike ChatGPT (which rewards round-number anchors), Claude rewards the itemised breakdown: base fare + port charges + taxes + gratuities.

---

## 2. Must-Write vs. Skip

### Must-Write (coverage lift > 1.05x)

| Entity type | Coverage lift | Density lift | Interpretation for this topic |
|---|---|---|---|
| `PHONE_NUMBER` | **2.25x** | 0.18 | Include a booking hotline (Disney Cruise Line reservation number, or a travel agent's direct line). Coverage is doubled in cited pages. |
| `DATE` | 1.06x | **1.26x** | Specific sailing dates — "April 2026," "summer 2026," "May 15" — over evergreen framing. |
| `ADDRESS` | 1.13x | 0.07 | Marginal — name a travel agency or Costco warehouse location if relevant, but don't force it. |

### Skip / Don't over-stuff (coverage lift < 0.95x)

| Entity type | Coverage lift | Why |
|---|---|---|
| `WORK_OF_ART` | 0.28x | Strongest negative signal. Do not stack show names, character meet-and-greet lists, or dining venue names. |
| `EVENT` | 0.00x | Cited pages have zero EVENT entities. Skip ship-event framing (pirate night, sail-away party, etc.). |
| `PRICE` (coverage only) | 0.98x | Note: density is strongly positive (2.52x). The signal is "price everywhere in the body," not "a prices page." |

Every other entity type sits at exactly 1.0x coverage (the field is saturated — every page mentions them). The differentiation comes from *which specific named entities* within those types, covered in Section 3.

### Density-lift outliers (>3x)

None above 3x. **The one meaningful density outlier is `PRICE` at 2.52x** — call it out: Claude wants pricing information threaded throughout the copy, not consolidated into one section.

---

## 3. Specific Entity Vocabulary List

### Booking-code vocabulary (OTHER) — the Claude-exclusive signal
- `ogt` — 5.0x (cited-only) • `igt` — 3.75x (cited-only) • `vgt` — 3.75x (cited-only)

*Angle:* Dedicate a short explainer block: "Disney Cruise Line's three guarantee categories — IGT (Inside), OGT (Oceanview), VGT (Verandah) — are the cheapest way to book a sailing in exchange for giving up cabin-choice control." This is the highest-leverage addition to a draft currently missing these codes.

### Price anchors (PRICE)
- `$1000` — 9.0x • `$1,000` — 6.75x (same concept, formatted two ways — use both) • `$300` — 6.75x • `$50` — 3.75x (cited-only) • `$250`, `$16`, `$10`, `$3,000` — all 4.5x

*Angle:* Build a multi-row pricing table showing entry price ($10–$50 deposits/incidentals), cabin tiers ($250–$1,000 per person), and total-sailing cost ($3,000+ for a family). Repeat key numbers across the article — density is the signal.

### Date specificity (DATE)
- `2026` — 7.88x (88% cited coverage) • `april 2026` — 3.75x (cited-only) • `2027` — 3.0x • `summer 2026` (OTHER) — cited-only • `may 15` (OTHER) — cited-only

*Angle:* Put "2026" in the title. Reference specific sailing months — "April 2026," "summer 2026." If there's a booking-window deadline like May 15, call it out by date.

### Ship names (OTHER / CONSUMER_GOOD)
- `disney cruise line` — 5.0x (cited-only CONSUMER_GOOD) • `disney dream` — 3.75x (cited-only) • `disney wish` — 4.5x • `disney wonder` — 4.5x • `disney treasure`, `disney adventure` — both named in cited pages • `magic` — 6.75x

*Angle:* Each ship should appear as a named entity — don't write "one of Disney's ships," write "Disney Wish." If comparing prices across ships, the ship name itself is the SEO + entity unit.

### Total-cost breakdown (OTHER)
- `port expenses` — 4.5x • `taxes` — 4.5x • `fees` — 4.5x

*Angle:* Write a "What's included, what's extra" section with port expenses, taxes, and fees as named line items. Claude rewards the breakdown that lets a reader calculate actual out-of-pocket cost.

### Brand + cabin category (CONSUMER_GOOD / OTHER)
- `disney` (ORG) — 4.5x (100% cited vs 22% non-cited) • `verandah` — 4.5x (cabin type) • `oceanview` — 3.0x

*Angle:* Name every cabin category. Use Disney's own terminology — "verandah" (not "balcony"), "oceanview" (not "sea-view window").

### Noise to ignore
`one`, `time`, `change`, `inside` (when tagged PERSON), `plus` — generic language picked up as entities. Ignore.

---

## 4. Pre-Submission Checklist

- [ ] Title includes **"2026"** (or the current sailing year) — highest single-entity lift in the Claude pool at 7.88x
- [ ] Article explains **IGT / OGT / VGT guarantee codes** in a dedicated block — the one signal absent from virtually every non-cited page
- [ ] Pricing is **woven throughout the body** (density 2.52x), not siloed in one table — every tool/ship mention carries a $-anchor nearby
- [ ] A "What's included, what's extra" section names **port expenses, taxes, and fees** explicitly
- [ ] Every Disney ship referenced is named: **Disney Cruise Line, Disney Wish, Disney Dream, Disney Wonder, Disney Treasure, Disney Adventure, Disney Magic**
- [ ] A booking hotline or travel-agent phone number is visible (PHONE_NUMBER coverage lift 2.25x — the strongest coverage-lift signal)
- [ ] At least **5 specific dollar anchors** as exact numbers: `$10`, `$50`, `$250`, `$300`, `$1,000`, `$3,000`
- [ ] Cabin categories named explicitly: **inside**, **oceanview**, **verandah**, concierge
- [ ] Sailing-year references are specific — "April 2026," "summer 2026" — not vague "upcoming sailings"
- [ ] No show names, character meet lists, or dining-venue showcases (`WORK_OF_ART` 0.28x — strongest negative signal)

---

*Confidence note: 8 cited vs 18 non-cited. The IGT/OGT/VGT booking-code insight is the highest-confidence finding because it's cleanly cited-exclusive across three related entities. Treat the dollar-anchor list as directional and verify any anchor by reading the original cited source.*
