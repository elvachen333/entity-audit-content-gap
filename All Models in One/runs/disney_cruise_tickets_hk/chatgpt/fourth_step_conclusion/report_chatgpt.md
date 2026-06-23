# Copywriting Strategy Report — ChatGPT

**Query:** 迪士尼遊輪票去哪裡買最便宜？ ("Where to buy Disney Cruise tickets cheapest?")
**Platform:** ChatGPT (GPT-4.1, web_search)
**Locale:** Hong Kong / zh-hk
**Sample:** 7 cited pages vs 15 non-cited pages

---

## 1. Key Insights

- **ChatGPT cites the thin, price-forward article — not the deep travel guide.** Cited pages have dramatically lower absolute entity density across almost every type (NUMBER 46 vs 304 per 1k words, CONSUMER_GOOD 27 vs 68, PERSON 5 vs 121). The non-cited pool is stuffed with named people and places typical of long-form travel blogs. ChatGPT is rewarding short, transactional "here's how to save money" content, not comprehensive 2,000-word reviews.
- **Pricing is the signal, but it's about specific dollar anchors — not total cost transparency.** PRICE coverage is actually slightly lower in cited pages (0.71 vs 0.87), but the *specific* price points winning with ChatGPT are concrete round-number anchors: `$4,000`, `$3,000`, `$2,500`, `$2,000`, `$500`, `$200`, `$100`, `$50` — all with 4–6x lift. These are the "starting at" and "save up to" numbers, not itemised breakdowns.
- **Name the ships, not the destinations.** The `disney` organisation entity has 5.36x lift (71% cited vs 13% non-cited). Specific ship names — `disney treasure`, `disney wonder`, `disney fantasy` — all appear in cited pages and never in non-cited. Destinations, ports, and itinerary details (LOCATION, WORK_OF_ART) are both low-density *and* low-coverage in cited pages, signalling ChatGPT prefers product-level naming over trip-narrative.
- **Costco is a named-authority entity for this query.** `costco` appears at 28.6% cited vs 0% non-cited (2.86x lift). For the "cheapest Disney cruise" query, ChatGPT specifically surfaces content that names resellers and loyalty channels — Costco, AAA, military/teacher discounts.
- **Year references carry disproportionate weight.** `2025` and `2026` each have 3.21x lift. `december 2024` is cited-only. The pattern: articles tied to a specific sailing year rank; evergreen "how to save on Disney cruises" articles don't.

---

## 2. Must-Write vs. Skip

### Must-Write (coverage lift > 1.05x)

| Entity type | Coverage lift | Interpretation for this topic |
|---|---|---|
| `PHONE_NUMBER` | 1.07x | Minor — only relevant if embedding a booking hotline (Disney Cruise Line 1-800 number). Don't force it. |
| `ADDRESS` | 1.07x | Marginal. If mentioning a Costco warehouse or travel agency office, include the street address. |

Note: the only coverage-lift signals above 1.05x are marginal. **The real "must-write" story is in the named entity list in Section 3** — specific prices, specific ship names, and Costco — not in entity-type categories.

### Skip / Don't over-stuff (coverage lift < 0.95x)

| Entity type | Coverage lift | Why |
|---|---|---|
| `LOCATION` | 0.71x | Port lists, city itineraries, and Caribbean/Bahamas destination details are over-represented in *non-cited* pages. ChatGPT penalises travel-guide framing. |
| `PRICE` | 0.82x | Surprising but consistent with insight #2 — broad price coverage (every fee, tax, gratuity) is *less* rewarded than a handful of anchor dollar amounts. |
| `CONSUMER_GOOD` | 0.86x | Don't stack every onboard amenity and dining venue. Name only the ships. |
| `NUMBER` / `DATE` / `ORGANIZATION` / `PERSON` | all ~0.86x | Long-form travel blogs pack these; ChatGPT ranks terser "how to save" articles instead. |
| `WORK_OF_ART` | 0.39x | Don't list character meet-and-greets, show names, or themed restaurants. This is the strongest negative signal. |
| `EVENT` | 0.00x | Cited pages have zero EVENT entities. Skip sailing-itinerary event framing entirely. |

### Density-lift outliers (>3x)

None. Every density lift is below 1.0x, confirming the "cited = shorter, leaner article" insight.

---

## 3. Specific Entity Vocabulary List

Group the winning named entities by angle. Use these as exact-match anchors in the article.

### Price anchors (PRICE)
- `$500` — 5.71x lift (cited-only) • `$4,000` — 6.43x • `$200` — 6.43x • `$100` — 4.29x (cited-only) • `$50` — 4.29x (cited-only) • `$3,000` — 4.29x • `$2,500` — 4.29x • `$2,000` — 2.86x (cited-only)

*Angle:* ChatGPT rewards a **clear $-range spread**, from entry-level ($50–$500 savings opportunities) to aspirational totals ($2,000–$4,000 per sailing). Build a "what you'll pay" table with these specific anchors as cell values, not approximate ranges.

### Ship names (OTHER / CONSUMER_GOOD)
- `disney treasure` — 4.29x (cited-only) • `disney wonder` — 2.86x (cited-only) • `disney fantasy` — 2.86x (cited-only) • `magic` — 8.57x (Disney Magic, the ship)

*Angle:* Dedicate a short line to each ship name, even if the article's angle is about buying tickets cheaply. The ship name is the entity; the tip about booking it is the copy.

### Brand / reseller authority (ORGANIZATION)
- `disney` — 5.36x (71% cited vs 13% non-cited) • `costco` — 2.86x (cited-only)

*Angle:* Every piece of pricing advice should be framed against a named booking channel. Disney Cruise Line direct booking is the baseline; Costco Travel is the named-alternative authority. Don't just say "third-party sites" — name Costco explicitly.

### Time references (DATE)
- `2025` — 3.21x • `2026` — 3.21x • `december 2024` — 2.86x (cited-only)

*Angle:* Put a year in the title (e.g. "2026 Disney Cruise Deals"). Reference the current sailing calendar year and the next one. ChatGPT ranks time-stamped content over evergreen pieces for this transactional query.

### Product / value terms (OTHER / CONSUMER_GOOD)
- `access` — 4.29x (premium access, concierge access) • `wi-fi` — 4.29x • `inside` — 4.29x (inside stateroom) • `day` — 4.29x (day-of / booking windows)

*Angle:* Name cabin categories (inside / outside / verandah / concierge) and onboard add-ons (Wi-Fi packages, drink packages) as discrete line items. The cheap-tickets angle is as much about what you skip as what you pay.

### Noise to ignore
`read more`, `sign up`, `disclaimer`, `related articles`, `home`, `however`, `instead`, `related` — these are CMS-chrome artefacts from the scraped pages. Their high lift reflects that cited pages share a similar travel-blog template, not a content signal.

---

## 4. Pre-Submission Checklist

- [ ] Title includes a **specific year** — "2026" or "2025" — not just "Disney Cruise Deals"
- [ ] Article explicitly names **Costco Travel** as a booking channel (not "third-party sites")
- [ ] Every Disney ship the article mentions is named by ship name: **Disney Treasure, Disney Wonder, Disney Fantasy, Disney Magic, Disney Wish, Disney Dream**
- [ ] At least **6 specific dollar anchors** appear as exact numbers: $50, $100, $200, $500, $1,000, $2,000+ tier
- [ ] A price-savings table lists **specific "Save up to $X"** or "Starting at $X" rows — not ranges like "$500–$1,000"
- [ ] No multi-paragraph ship amenity / character-meet / show descriptions (`WORK_OF_ART` is the strongest negative signal)
- [ ] No dedicated destinations or port-of-call section (`LOCATION` is the second-strongest negative signal)
- [ ] Cabin categories named explicitly: **inside stateroom**, **outside**, **verandah**, **concierge**
- [ ] At least one **booking-timing cue**: "book by December 2024," "for 2026 sailings," "30-day window"
- [ ] Keep total article length short — cited pages have ~3–6x lower entity density than non-cited, so prefer a 600–900-word transactional article over a 2,000-word guide

---

*Confidence note: 7 cited vs 15 non-cited — a small sample. Treat the high-lift named entities as directional rather than statistically definitive, and validate the short-article hypothesis by comparing word counts of the scraped cited docs before committing to the structure.*
