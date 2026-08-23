# Smash Analytics — Change Log

Changes are grouped by session. File paths are relative to `pandas_projects/` unless prefixed with `site:` (meaning `LiamMs_PandasProjects/`).

---

## Session — 2026-07-19

### Site — Separate opponent profile pages
- `generate_liamms_site.py`: Added `opponent_character_page()` function
  - Generates `site:Smash/Opponents/{slug}/index.html` for every character with at least one opponent appearance
  - Layout: purple `🛡 As Opponent — Rank #N` badge, opponent-focused KPIs (Opp Rank, Total NT, Win Rate, W/L, Appearances, Avg NT, Fighter Rank), NT Per Appearance chart, NT by Round chart, Appearances Log
  - "View Fighter Profile" button links back to `site:Smash/{slug}/index.html`
  - Depth 3 asset paths (`../../../`)
- `generate_liamms_site.py`: Opponent index tiles and leaderboard now link to `./King-K-Rool/index.html` (new page) instead of `../King-K-Rool/index.html` (character page)
- `generate_liamms_site.py`: Removed duplicate `opponent_tile()` definition
- `generate_liamms_site.py`: CSS — added `.opp-page-badge`, `.opp-hero-metrics` (purple KPI values), `.opp-card-page` variant
- `generate_liamms_site.py`: Character profile pages retain full opponent section unchanged

### Site — Opponent bar chart labels
- `generate_liamms_site.py` (`site.js`): NT Score Per Appearance chart labels changed from truncated `"Round 1\nM1\nvs King K"` to full character name (`a.against`)

### Data — Round 5 current scores print
- `next_smash_mains_discovery.py`: After `round_5_summary` is built (some Round 5 matches played), a second score window "Round 5 current scores (post-match)" is printed alongside the existing "Round 5 entry scores" — shows post-match accumulated scores for all Round 5 participants

---

## Session — 2026-07-18 (pre-compaction work, landed in `21319d3`)

### Site — Round toggle on main Smash page
- `generate_liamms_site.py`: Added round-selector bar (`<div class="round-selector-bar">`) with `.round-pill` pills above the overview grid
- `generate_liamms_site.py` (`site.js`): `renderSmashRound(roundLabel, chars)` — clicking a round pill updates the leaderboard with cumulative scores up to that round and redraws the top-16 score spread chart
- `generate_liamms_site.py` (`site.js`): `ROUND_ORDER` constant for canonical ordering of rounds/eliminations
- `generate_liamms_site.py` (`site.js`): `allRounds(chars)` now sorted by `ROUND_ORDER` (was interleaving rounds and eliminations incorrectly)
- `generate_liamms_site.py`: CSS — `.round-pill`, `.round-pill.active`, `.round-pill:hover`

### Site — Opponent Rank Atlas page
- `generate_liamms_site.py`: Added `opp_rank_atlas_page(opponents)` function → `site:Smash/Opponents/Rank-Atlas/index.html`
- `generate_liamms_site.py` (`site.js`): `drawOppRankAtlas(canvas, opps, highlightNames)` — trajectory chart for opponent ranks across rounds
- `generate_liamms_site.py` (`main()`): Computes `opp_cumul` (cumulative NT per round per opponent) and `opp_rank_at` (rank at each round), attaches as `oppRanks: [{roundLabel, round, rank}]` to each opponent leader entry

### Site — Score spread / overview chart fixes
- Score spread chart: removed scroll, capped at top 16, legend hidden (`hideLegend: true`)
- `generate_liamms_site.py` (`site.js`): `drawBarChart` accepts `opts.hideLegend`

---

## Session — earlier (landed in `0ae80cc`)

### Site — Opponent section on character profile pages
- `generate_liamms_site.py`: Character profile pages gained "As Opponent" section: KPI bar (appearances, W/L, win rate, total NT, avg NT), NT Per Appearance bar chart (`drawCustomBarChart`, green=won / red=loss), NT by Round chart, Appearances Log

### Site — Opponents index page
- `generate_liamms_site.py`: Added `opponents_page()` → `site:Smash/Opponents/index.html`
  - Page toggle bar (⚔ Fighters / 🛡 As Opponents)
  - Opponent leaderboard ranked by total NT score
  - Top-16 NT score chart
  - Character grid with opponent rank and NT score

### Site — `drawCustomBarChart` JS function
- `generate_liamms_site.py` (`site.js`): Added `drawCustomBarChart(canvas, labels, values, colors, title, yLabel)` — custom bar chart with per-bar color (used for win/loss colouring on opponent charts)

### Site — Character profile page layout redesign
- All chart panels switched to `wide` (full-width, `grid-column: 1 / -1`)
- Canvas sizes 1400×380
- `.profile-chart-grid`: 2-column grid; wide panels span both columns
- `.fighter-model-img`: `height: min(100vh, 1100px); max-width: min(92vw, 1800px); opacity: .70`
- Stronger gradient overlay on fighter card pages

### Site — Page toggle infrastructure
- CSS: `.page-toggle-bar`, `.toggle-pill`, `.toggle-pill.active` (cyan), `.toggle-pill:not(.active)` (muted)

---

## Push history

| Commit | Content | Status |
|--------|---------|--------|
| `0ae80cc` | Opponent page, charts, character page redesign | ✅ Live on GitHub Pages |
| `21319d3` | Round toggle, Opponent Atlas, allRounds fix | ❌ Blocked — connection resets on push |
| `068f503` | Separate opponent pages, label fix, opponent pages | ❌ Blocked — connection resets on push |

> **Push issue:** Both HTTPS (HTTP 408) and SSH (TCP reset) connections are dropped before GitHub acknowledges receipt of ~180MB packs. The data uploads fully but confirmation is lost. Workaround: retry until it lands, or resolve network-level issue (NAT/firewall timeout on large TCP transfers).
