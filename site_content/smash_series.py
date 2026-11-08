"""Parse and render the 1v1 Smash Series Log (Gaming-and-Performance-Log/Smash-Bros/1v1-History).

Follows the bracket notation ``Character vs. Opponent - (stock_diff, percentage)`` and the
scoring rules from ``next_smash_mains_discovery.py`` (with ``max_percentage = 200.0`` and
matchup multipliers from ``matchup_chart.csv``).
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import date
from html import escape
from pathlib import Path
import re
from statistics import mean

from .athletics_views import _day, _downloads, _e, _metrics, _num, _section, _table, _update_notes

SMASH_SERIES_GDOC_ID = "1nD1anwy7vaR_V9K9LuIkL5CmEcPqMO7rog3yTbX_U9g"


def _signed(val: float) -> str:
    return f"+{val:g}" if val >= 0 else f"{val:g}"
SMASH_SERIES_SOURCE = "records/athletics/smash/Smash_Series_Log.txt"
SMASH_SERIES_COPY = "LiamMs_PandasProjects/Gaming-and-Performance-Log/Smash-Bros/1v1-History/Smash_Series_Log.txt"
MAX_PERCENTAGE = 200.0

_DAY_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(20\d{2})(?:\s*-\s*(.+))?$")
_SERIES_RE = re.compile(r"^Series\s+(\d+)$", re.I)
_MATCH_RE = re.compile(
    r"^(.+?)\s+vs\.?\s+(.+?)\s*-\s*\(\s*([+-]?\d+)\s*,\s*(\d+(?:\.\d+)?)\s*\)$",
    re.I,
)

CHARACTER_ALIASES = {
    "Bowser Jr.": "Bowser Jr",
    "Pac-Man": "PacMan",
    "R.O.B.": "ROB",
}


def canonical_character_name(raw: str) -> str:
    cleaned = raw.strip().rstrip(".")
    return CHARACTER_ALIASES.get(cleaned, cleaned)


def fighter_slug(name: str) -> str:
    clean = canonical_character_name(name).replace("&", "and")
    return "-".join(re.findall(r"[A-Za-z0-9]+", clean))


def load_matchup_table(root: Path) -> dict[tuple[str, str], float]:
    path = root / "matchup_chart.csv"
    if not path.is_file():
        return {}
    table: dict[tuple[str, str], float] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            char = str(row.get("Character") or "").strip().lower()
            if not char:
                continue
            for col, val in row.items():
                if not col or col == "Character":
                    continue
                try:
                    table[(char, col.strip().lower())] = float(val)
                except (TypeError, ValueError):
                    continue
    return table


def score_1v1_match(
    character: str,
    opponent: str,
    stock_diff: int,
    percentage: float,
    matchup_table: dict[tuple[str, str], float] | None = None,
    cap: float = MAX_PERCENTAGE,
) -> tuple[float, float, float]:
    """Return (base_score, matchup_multiplier, adjusted_score) per Next_Smash_Mains_Discovery."""
    if stock_diff > 0:
        base_score = stock_diff + max(0.0, cap - percentage) / cap
    elif stock_diff < 0:
        base_score = 1.0 + stock_diff + min(1.0, percentage / cap)
    else:
        return 0.0, 1.0, 0.0

    mult = 1.0
    if matchup_table:
        m_val = matchup_table.get((character.lower(), opponent.lower()))
        if m_val is not None:
            mult = 1.0 - (m_val / 20.0)
    adjusted = base_score * mult
    return round(base_score, 3), round(mult, 3), round(adjusted, 3)


def parse_smash_series(text: str, matchup_table: dict[tuple[str, str], float] | None = None) -> dict:
    raw_lines = [(idx, ln.strip()) for idx, ln in enumerate(text.replace("\r\n", "\n").splitlines(), 1) if ln.strip()]
    if not raw_lines or raw_lines[0][1] != "Smash Series Log":
        raise ValueError("Smash Series Log must start with 'Smash Series Log'.")

    cur_date: str | None = None
    cur_friend = "Owen"
    cur_series_num: int | None = None
    current_series: dict | None = None
    series_list: list[dict] = []
    all_matches: list[dict] = []

    for lineno, line in raw_lines[1:]:
        if m_day := _DAY_RE.fullmatch(line):
            cur_date = date(int(m_day[3]), int(m_day[1]), int(m_day[2])).isoformat()
            cur_friend = (m_day[4] or "Owen").strip()
            cur_series_num = None
            current_series = None
            continue
        if m_ser := _SERIES_RE.fullmatch(line):
            if cur_date is None:
                raise ValueError(f"Line {lineno}: Series header before a date line.")
            cur_series_num = int(m_ser[1])
            current_series = {
                "id": f"{cur_date}-S{cur_series_num}",
                "date": cur_date,
                "friend": cur_friend,
                "seriesNumber": cur_series_num,
                "matches": [],
            }
            series_list.append(current_series)
            continue
        if m_mat := _MATCH_RE.fullmatch(line):
            if current_series is None or cur_date is None or cur_series_num is None:
                raise ValueError(f"Line {lineno}: match entry outside a dated Series block: {line!r}")
            char_raw, opp_raw = m_mat[1].strip(), m_mat[2].strip()
            char_name = canonical_character_name(char_raw)
            opp_name = canonical_character_name(opp_raw)
            stock_diff = int(m_mat[3])
            pct = float(m_mat[4])
            if stock_diff == 0:
                raise ValueError(f"Line {lineno}: stock_diff cannot be 0 in a completed 1v1 match: {line!r}")
            base_sc, mult, adj_sc = score_1v1_match(char_name, opp_name, stock_diff, pct, matchup_table)
            game_num = len(current_series["matches"]) + 1
            match_obj = {
                "date": cur_date,
                "friend": cur_friend,
                "seriesId": current_series["id"],
                "seriesNumber": cur_series_num,
                "gameNumber": game_num,
                "character": char_name,
                "characterRaw": char_raw,
                "characterSlug": fighter_slug(char_name),
                "opponent": opp_name,
                "opponentRaw": opp_raw,
                "opponentSlug": fighter_slug(opp_name),
                "stockDiff": stock_diff,
                "percentage": int(pct) if pct == int(pct) else pct,
                "won": stock_diff > 0,
                "baseScore": base_sc,
                "matchupMultiplier": mult,
                "adjustedScore": adj_sc,
                "rawLine": line,
            }
            current_series["matches"].append(match_obj)
            all_matches.append(match_obj)
            continue
        raise ValueError(f"Line {lineno}: unreadable Smash Series entry {line!r}.")

    if not all_matches:
        raise ValueError("Smash Series Log has no recorded matches.")

    series_wins = 0
    series_losses = 0
    series_ties = 0
    for ser in series_list:
        ms = ser["matches"]
        w = sum(1 for m in ms if m["won"])
        l = len(ms) - w
        net_stocks = sum(m["stockDiff"] for m in ms)
        tot_base = round(sum(m["baseScore"] for m in ms), 2)
        tot_adj = round(sum(m["adjustedScore"] for m in ms), 2)
        if w > l:
            outcome = "Won"
            series_wins += 1
        elif w < l:
            outcome = "Lost"
            series_losses += 1
        else:
            outcome = "Tied"
            series_ties += 1
        # Compute best character streak inside this series
        best_streak_char = ""
        best_streak_len = 0
        cur_c = ""
        cur_s = 0
        for m in ms:
            if m["won"]:
                if m["character"] == cur_c:
                    cur_s += 1
                else:
                    cur_c = m["character"]
                    cur_s = 1
                if cur_s > best_streak_len:
                    best_streak_len = cur_s
                    best_streak_char = cur_c
            else:
                cur_c = ""
                cur_s = 0
        ser.update(
            games=len(ms),
            wins=w,
            losses=l,
            outcome=outcome,
            netStocks=net_stocks,
            baseScore=tot_base,
            adjustedScore=tot_adj,
            mvpCharacter=best_streak_char or ms[0]["character"],
            mvpStreak=best_streak_len,
        )

    # Aggregate Liam's fighters
    by_char: dict[str, list[dict]] = defaultdict(list)
    for m in all_matches:
        by_char[m["character"]].append(m)

    fighters: list[dict] = []
    for char_name, ms in by_char.items():
        w = sum(1 for m in ms if m["won"])
        l = len(ms) - w
        # Longest consecutive win streak for this character
        max_streak = 0
        cur_streak = 0
        for m in ms:
            if m["won"]:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 0
        fighters.append({
            "character": char_name,
            "slug": fighter_slug(char_name),
            "games": len(ms),
            "wins": w,
            "losses": l,
            "winRate": round(100.0 * w / len(ms), 1),
            "netStocks": sum(m["stockDiff"] for m in ms),
            "avgDamage": round(mean(m["percentage"] for m in ms), 1),
            "baseScore": round(sum(m["baseScore"] for m in ms), 2),
            "adjustedScore": round(sum(m["adjustedScore"] for m in ms), 2),
            "scorePerGame": round(sum(m["adjustedScore"] for m in ms) / len(ms), 2),
            "bestStreak": max_streak,
        })
    fighters.sort(key=lambda f: (f["adjustedScore"], f["wins"], f["netStocks"]), reverse=True)

    # Aggregate Opponent (Owen's) fighters
    by_opp: dict[str, list[dict]] = defaultdict(list)
    for m in all_matches:
        by_opp[m["opponent"]].append(m)

    opponents: list[dict] = []
    for opp_name, ms in by_opp.items():
        liam_w = sum(1 for m in ms if m["won"])
        opp_w = len(ms) - liam_w
        opponents.append({
            "opponent": opp_name,
            "slug": fighter_slug(opp_name),
            "games": len(ms),
            "liamWins": liam_w,
            "opponentWins": opp_w,
            "liamWinRate": round(100.0 * liam_w / len(ms), 1),
            "netStocksVsOpponent": sum(m["stockDiff"] for m in ms),
            "avgAdjustedScore": round(sum(m["adjustedScore"] for m in ms) / len(ms), 2),
        })
    opponents.sort(key=lambda o: (o["games"], o["opponentWins"]), reverse=True)

    total_wins = sum(1 for m in all_matches if m["won"])
    total_losses = len(all_matches) - total_wins
    dates_sorted = sorted({m["date"] for m in all_matches})

    return {
        "series": series_list,
        "matches": all_matches,
        "fighters": fighters,
        "opponents": opponents,
        "summary": {
            "matches": len(all_matches),
            "wins": total_wins,
            "losses": total_losses,
            "winRate": round(100.0 * total_wins / len(all_matches), 1),
            "seriesCount": len(series_list),
            "seriesWins": series_wins,
            "seriesLosses": series_losses,
            "seriesTies": series_ties,
            "datesCount": len(dates_sorted),
            "firstDate": dates_sorted[0],
            "lastDate": dates_sorted[-1],
            "netStocks": sum(m["stockDiff"] for m in all_matches),
            "totalBaseScore": round(sum(m["baseScore"] for m in all_matches), 2),
            "totalAdjustedScore": round(sum(m["adjustedScore"] for m in all_matches), 2),
            "avgScorePerMatch": round(sum(m["adjustedScore"] for m in all_matches) / len(all_matches), 2),
            "uniqueFightersPlayed": len(fighters),
            "uniqueOpponentsFaced": len(opponents),
        },
    }


def load_smash_series(root: Path) -> dict:
    src = root / SMASH_SERIES_SOURCE
    copy = root / SMASH_SERIES_COPY
    text = src.read_text(encoding="utf-8-sig")
    if copy.is_file() and copy.read_text(encoding="utf-8-sig").replace("\r\n", "\n") != text.replace("\r\n", "\n"):
        raise ValueError(f"{SMASH_SERIES_COPY} differs from {SMASH_SERIES_SOURCE}; sync them before building.")
    matchup_table = load_matchup_table(root)
    parsed = parse_smash_series(text, matchup_table)
    nonempty = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parsed["source"] = {
        "path": SMASH_SERIES_SOURCE,
        "latestEntry": nonempty[-14:],
    }
    return parsed


def smash_series_rows(data: dict) -> dict[str, list[dict]]:
    return {
        "smash-1v1-matches": [
            {
                "date": m["date"],
                "friend": m["friend"],
                "seriesNumber": m["seriesNumber"],
                "gameNumber": m["gameNumber"],
                "character": m["character"],
                "opponent": m["opponent"],
                "stockDiff": m["stockDiff"],
                "percentage": m["percentage"],
                "baseScore": m["baseScore"],
                "matchupMultiplier": m["matchupMultiplier"],
                "adjustedScore": m["adjustedScore"],
            }
            for m in data["matches"]
        ],
        "smash-1v1-fighters": data["fighters"],
        "smash-1v1-series": [
            {k: v for k, v in s.items() if k != "matches"}
            for s in data["series"]
        ],
    }


def _series_chart_svg(series_list: list[dict]) -> str:
    width, height = 920, 340
    left, right, top, bottom = 74, 846, 40, 275
    plot_w, plot_h = right - left, bottom - top
    max_games = max(1, max(s["games"] for s in series_list))
    max_score = max(1.0, max(s["adjustedScore"] for s in series_list))
    step = plot_w / max(1, len(series_list))

    parts = [
        '<title id="smash-series-svg-title">1v1 Series outcomes, win/loss splits, and Next_Smash_Mains_Discovery series scores</title>',
        '<desc id="smash-series-svg-desc">Stacked green win bars and coral loss bars per Series on the left axis, with total matchup-adjusted Next_Smash_Mains_Discovery score on the right axis.</desc>',
        f'<text x="{left - 8}" y="22" text-anchor="end" fill="#69d4cf" font-weight="700" font-size="11">▮ Stacked Bars: Wins &amp; Losses (Games)</text>',
        f'<text x="{right + 8}" y="22" text-anchor="start" fill="#f7ab65" font-weight="700" font-size="11">● Line: Series Score (Adj. Pts)</text>',
    ]
    for k in range(5):
        g_tick = round(max_games * k / 4, 1)
        s_tick = round(max_score * k / 4, 1)
        ty = bottom - (k / 4) * plot_h
        parts.append(
            f'<line class="chart-grid" x1="{left}" x2="{right}" y1="{ty:.1f}" y2="{ty:.1f}"/>'
            f'<text x="{left - 8}" y="{ty + 4:.1f}" text-anchor="end">{g_tick:g}</text>'
            f'<text x="{right + 8}" y="{ty + 4:.1f}" text-anchor="start" fill="#f7ab65">{s_tick:g} pts</text>'
        )

    line_pts: list[tuple[float, float, dict]] = []
    for idx, ser in enumerate(series_list):
        cx = left + (idx + 0.5) * step
        bw = min(46.0, max(18.0, step * 0.58))
        bx = cx - bw / 2
        w_h = (ser["wins"] / max_games) * plot_h
        l_h = (ser["losses"] / max_games) * plot_h
        wy = bottom - w_h
        ly = wy - l_h
        sy = bottom - (ser["adjustedScore"] / max_score) * plot_h
        line_pts.append((cx, sy, ser))
        short_lbl = f"{_day(ser['date'])} S{ser['seriesNumber']}"
        tip = (
            f"{_day(ser['date'])} · Series {ser['seriesNumber']} vs. {ser['friend']}: "
            f"{ser['wins']}–{ser['losses']} ({ser['outcome']}, {_signed(ser['netStocks'])} stocks, "
            f"{ser['adjustedScore']:.2f} pts, MVP {ser['mvpCharacter']})"
        )
        parts.append(
            f'<g><title>{_e(tip)}</title>'
            f'<rect fill="#69d4cf" x="{bx:.1f}" y="{wy:.1f}" width="{bw:.1f}" height="{w_h:.1f}"/>'
            f'<rect fill="#f28b82" x="{bx:.1f}" y="{ly:.1f}" width="{bw:.1f}" height="{l_h:.1f}"/>'
            f'<text x="{cx:.1f}" y="{max(28.0, ly - 6):.1f}" text-anchor="middle" font-size="10" fill="#eeeef7" font-weight="700">{ser["wins"]}–{ser["losses"]}</text>'
            f'<text x="{cx:.1f}" y="{bottom + 18}" text-anchor="end" transform="rotate(-24, {cx:.1f}, {bottom + 18})" font-size="10.5">{_e(short_lbl)}</text>'
            f'</g>'
        )

    if len(line_pts) > 1:
        poly = " ".join(f"{cx:.1f},{sy:.1f}" for cx, sy, _ in line_pts)
        parts.append(f'<polyline fill="none" stroke="#f7ab65" stroke-width="2.8" points="{poly}"/>')
    for cx, sy, ser in line_pts:
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{sy:.1f}" r="4.5" fill="#f7ab65" stroke="#0d101b" stroke-width="1.6">'
            f'<title>{_e(_day(ser["date"]))} S{ser["seriesNumber"]}: {ser["adjustedScore"]:.2f} matchup-adjusted pts</title></circle>'
        )

    return (
        '<figure class="sports-chart athletics-chart">'
        '<figcaption><span class="chart-title">1v1 Series Progression — Win/Loss Record &amp; Matchup-Adjusted Score per Series</span>'
        '<small>Teal = Games Won · Coral = Games Lost · Amber Line = Cumulative Next_Smash_Mains_Discovery Score per Series</small></figcaption>'
        f'<svg class="sports-chart" viewBox="0 0 {width} {height}" role="img" aria-labelledby="smash-series-svg-title smash-series-svg-desc">'
        + "".join(parts)
        + "</svg></figure>"
    )


def _fighter_leaderboard_svg(fighters: list[dict]) -> str:
    height = 76 + len(fighters) * 32
    left = 235
    width = 430
    max_val = max(1.0, max(max(f["adjustedScore"], f["baseScore"]) for f in fighters))
    parts = [
        '<title id="smash-fighters-svg-title">Liam 1v1 Fighter Leaderboard by Next_Smash_Mains_Discovery Adjusted Score</title>',
        '<desc id="smash-fighters-svg-desc">Horizontal bars ranking all characters played in 1v1 Series by total matchup-adjusted score, win-loss record, and best streak.</desc>',
    ]
    for i in range(5):
        tv = round(max_val * i / 4, 1)
        tx = left + (i / 4) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 24}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">{tv:g} pts</text>'
        )
    for idx, f in enumerate(fighters):
        y = 38 + idx * 32
        adj = max(0.0, f["adjustedScore"])
        w_bar = (adj / max_val) * width
        lbl = f"{f['character']} ({f['wins']}–{f['losses']})"
        note = f"{f['adjustedScore']:.2f} pts ({f['scorePerGame']:+.2f}/gm · {_signed(f['netStocks'])} stocks · streak {f['bestStreak']})"
        parts.append(
            f'<text x="{left - 10}" y="{y + 15}" text-anchor="end">{_e(lbl)}</text>'
            f'<rect fill="#69d4cf" x="{left}" y="{y}" width="{w_bar:.1f}" height="20">'
            f'<title>{_e(f["character"])}: {_e(note)}</title></rect>'
            f'<text class="athletics-label" x="{left + w_bar + 8:.1f}" y="{y + 15}">{_e(note)}</text>'
        )
    return (
        '<figure class="sports-chart athletics-chart">'
        '<figcaption><span class="chart-title">Liam\'s 1v1 Fighter Leaderboard (Next_Smash_Mains_Discovery Scoring)</span>'
        '<small>Ranked by cumulative matchup-adjusted points across all 11 Series · includes Win–Loss record, net stocks &amp; longest King-of-the-Hill win streak</small></figcaption>'
        f'<svg class="sports-chart" viewBox="0 0 920 {height}" role="img" aria-labelledby="smash-fighters-svg-title smash-fighters-svg-desc">'
        + "".join(parts)
        + "</svg></figure>"
    )


def smash_series_body(data: dict, lead: str = "") -> str:
    s = data["summary"]
    series_list = data["series"]
    fighters = data["fighters"]
    opponents = data["opponents"]
    matches = data["matches"]

    deck = (
        f"{s['matches']} recorded 1v1 games across {s['seriesCount']} King-of-the-Hill Series ({_day(s['firstDate'])} → {_day(s['lastDate'])}): "
        f"{s['wins']}–{s['losses']} ({s['winRate']}%) match record, {_signed(s['netStocks'])} net stocks, and {s['totalAdjustedScore']:.2f} Next_Smash_Mains_Discovery points."
    )
    actions = (
        '<a class="button primary" href="#smash-series-progression-title">Series progression</a>'
        '<a class="button ghost" href="#smash-fighter-leaderboard-title">Fighter leaderboard</a>'
        '<a class="button ghost" href="../../../Smash/index.html">Smash Mains Discovery ↗</a>'
        '<a class="button ghost" href="#smash_series-update">Sync Google Doc ↓</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Chest"><strong>{s["wins"]}–{s["losses"]}</strong>1v1 games ({s["winRate"]}%)</span>'
        f'<span class="split-Back"><strong>{s["seriesWins"]}–{s["seriesLosses"]}–{s["seriesTies"]}</strong>Series W–L–T</span>'
        f'<span class="split-Shoulders"><strong>{_signed(s["netStocks"])}</strong>net stocks</span></div>'
    )
    metrics = _metrics([
        ("1v1 Match record", f"{s['wins']}–{s['losses']} ({s['winRate']}%)", f"{s['matches']} games across {s['datesCount']} match days vs. Owen"),
        ("Series record", f"{s['seriesWins']}–{s['seriesLosses']}–{s['seriesTies']}", f"{s['seriesWins']} Series wins, {s['seriesTies']} tie (11/1 S1, +7 net stocks)"),
        ("Next Smash Mains score", f"{s['totalAdjustedScore']:.2f} pts", f"{s['avgScorePerMatch']:.2f} adj. pts/game (base {s['totalBaseScore']:.2f} pts)"),
        ("Roster breadth", f"{s['uniqueFightersPlayed']} fighters", f"Against {s['uniqueOpponentsFaced']} opponent fighters · top streak: Ridley (7–0)"),
    ])

    series_rows = [
        [
            f"{_day(ser['date'])} · Series {ser['seriesNumber']}",
            ser["friend"],
            f"{ser['wins']}–{ser['losses']} ({ser['outcome']})",
            f"{_signed(ser['netStocks'])} stocks",
            f"{ser['baseScore']:.2f}",
            f"{ser['adjustedScore']:.2f}",
            f"{ser['mvpCharacter']} ({ser['mvpStreak']}W streak)",
        ]
        for ser in series_list
    ]

    fighter_rows = [
        [
            escape(f["character"]),
            f"{f['wins']}–{f['losses']}",
            f"{f['winRate']}%",
            _signed(f["netStocks"]),
            f"{f['avgDamage']}%",
            f"{f['bestStreak']}W",
            f"{f['baseScore']:.2f}",
            f"{f['adjustedScore']:.2f}",
            f"{f['scorePerGame']:+.2f}",
        ]
        for f in fighters
    ]

    opp_rows = [
        [
            escape(o["opponent"]),
            str(o["games"]),
            f"{o['liamWins']}–{o['opponentWins']}",
            f"{o['liamWinRate']}%",
            _signed(o["netStocksVsOpponent"]),
            f"{o['avgAdjustedScore']:+.2f} pts",
        ]
        for o in opponents
    ]

    match_rows = [
        [
            f"{_day(m['date'])} · S{m['seriesNumber']}.G{m['gameNumber']}",
            m["character"],
            m["opponent"],
            f"({_signed(m['stockDiff'])}, {m['percentage']}%)",
            "Win" if m["won"] else "Loss",
            f"{m['baseScore']:+.3f}",
            f"{m['matchupMultiplier']:.3f}×",
            f"{m['adjustedScore']:+.3f}",
        ]
        for m in matches
    ]

    formula_card = (
        '<article class="study-reg-card" style="margin: 14px 0 18px;">'
        '<div class="study-reg-head"><div><span class="sports-kicker">Bracket Notation &amp; Next_Smash_Mains_Discovery Scoring Engine</span>'
        '<h3>How <code>Character vs. Opponent - (stocks, damage%)</code> is Scored</h3></div>'
        '<span class="wb-badge wb-up">Matchup-Adjusted · Cap = 200%</span></div>'
        '<p style="color:#c5cbe0;margin:6px 0 10px;">Every 1v1 game follows King-of-the-Hill (winner stays on) and records the signed stock differential and ending damage percentage <code>(stock_diff, percentage)</code>:</p>'
        '<div class="study-reg-kpis">'
        '<div><span>Win Formula (<code>stock_diff &gt; 0</code>)</span><strong><code>stock_diff + max(0, 200 − %)/200</code></strong></div>'
        '<div><span>Loss Formula (<code>stock_diff &lt; 0</code>)</span><strong><code>1 + stock_diff + min(1, %/200)</code></strong></div>'
        '<div><span>Matchup Multiplier</span><strong><code>1 − (Matchup_Value / 20)</code></strong></div>'
        '<div><span>Adjusted Match Score</span><strong><code>Base_Score × Matchup_Multiplier</code></strong></div>'
        '</div></article>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      <header class="sports-hero"><div class="sports-hero-copy"><p class="sports-kicker">Smash Bros · 1v1 Series History <span>vs. Owen · King-of-the-Hill</span></p>
      <h1>Winner stays on.<br>Every stock <em>scored.</em></h1><p class="sports-deck">{_e(deck)}</p><div class="toolbar">{actions}</div></div>{art}</header>
      {metrics}
      {formula_card}
      {_section("01", "Series-by-series progression", f"{s['seriesCount']} King-of-the-Hill Series ({s['seriesWins']}W–{s['seriesLosses']}L–{s['seriesTies']}T).", "smash-series-progression-title",
                _series_chart_svg(series_list)
                + _table("Every recorded 1v1 Series.", ["Series", "Opponent", "Games (W–L)", "Net Stocks", "Base Score", "Adj. Score", "Series MVP Streak"], series_rows, table_id="smash-series-table"))}
      {_section("02", "Fighter leaderboard", f"{len(fighters)} fighters played by Liam, ranked by Next_Smash_Mains_Discovery matchup-adjusted score.", "smash-fighter-leaderboard-title",
                _fighter_leaderboard_svg(fighters)
                + _table("Fighter performance across all 1v1 Series.", ["Fighter", "W–L", "Win %", "Net Stocks", "Avg End %", "Best Streak", "Base Pts", "Adj. Pts", "Adj. Pts / Game"], fighter_rows, table_id="smash-fighters-table"))}
      {_section("03", "Opponent counter-pick & boss breakdown", f"How Owen's {len(opponents)} fighters fared across {s['matches']} games.", "smash-opponents-breakdown-title",
                _table("Record against each opponent fighter.", ["Opponent Fighter (Owen)", "Games Faced", "Liam W–L", "Liam Win %", "Net Stocks", "Avg Adj. Score"], opp_rows, table_id="smash-opponents-table"))}
      {_section("04", "Complete 1v1 match log", f"All {s['matches']} games in chronological order with bracket notation and Next_Smash_Mains_Discovery scores.", "smash-matches-log-title",
                f'<details class="sports-log-details" open><summary>Show all {s["matches"]} recorded 1v1 games</summary>'
                + _table("Every 1v1 game.", ["Series & Game", "Liam Fighter", "Owen Fighter", "Bracket (Stocks, %)", "Result", "Base Score", "Matchup Mult.", "Adj. Score"], match_rows, table_id="smash-matches-table")
                + "</details>")}
      <section class="sports-section sports-method" aria-labelledby="smash-series-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="smash-series-method-title">How these numbers are made.</h2>
      <ul><li>Source: <code>{_e(data["source"]["path"])}</code>, synced directly from Google Docs (<code>1nD1anwy7vaR_V9K9LuIkL5CmEcPqMO7rog3yTbX_U9g</code>).</li>
      <li>Bracket notation <code>(stock_diff, percentage)</code> is scored with the exact <code>Round._score_match</code> formula from <code>next_smash_mains_discovery.py</code> and <code>matchup_chart.csv</code>.</li></ul>
      {_downloads(3, [("smash-1v1-series.json", "1v1 Series log · JSON"), ("smash-1v1-matches.csv", "All 113 matches · CSV"), ("smash-1v1-fighters.csv", "Fighter leaderboard · CSV")])}</section>
      {_update_notes("smash_series", data, '<li>Add a date line like <code>11/8/2026 - Owen</code>, a <code>Series 1</code> line, then match lines like <code>Ridley vs. Hero - (2, 115)</code>.</li>')}
    </main>'''
