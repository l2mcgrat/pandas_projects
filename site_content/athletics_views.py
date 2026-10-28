"""Running, swimming and weightlifting dashboards: static SVG charts, escaped text, no scripts.

Each body is the <main> for a hosted destination at depth 3, styled by sports.css
plus athletics.css. Pass load_athletics(root)[key]; lead is the atlas location bar.
Charts are complete without JavaScript, and every chart has a table equivalent.
"""

from __future__ import annotations

from datetime import date
from html import escape
import json
import math
from typing import Any

from .athletics import REP_TARGETS, clock

__all__ = ["running_body", "swimming_body", "weightlifting_body"]

SERIES = 4


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _day(iso: str) -> str:
    value = date.fromisoformat(iso)
    return f"{value:%b} {value.day}"


def _num(value: float) -> str:
    return f"{value:,.0f}"


KPI_DEFINITIONS: dict[str, str] = {
    # Macroeconomics · AI Iceberg Index (ST-01)
    "Visible tip (surface)": "Direct AI & software adoption in ICT, cloud, and computing payrolls (W_surface / W ≈ 2.2% of national wage bill).",
    "Submerged Iceberg": "Skills-centered cognitive, administrative, financial, and analytical task exposure inside traditional non-tech sectors (W_submerged / W ≈ 11.7%).",
    "Combined exposure": "Total share of North American wage value where frontier AI models overlap occupational tasks (s_surface + s_submerged = 13.9%; 86.1% human moat).",
    "Hidden multiplier": "The Iceberg Ratio Λ = s_submerged / s_surface (11.7% / 2.2% = 5.32×), measuring how much hidden non-tech exposure exceeds visible software roles.",
    # Public Policy · 2026 Alberta Referendum (ST-02)
    "Question 10 · Remain": "Official Elections Alberta ballot share voting Option 1 (Remain in Canada, 74.95%) vs. Option 2 (commence binding separation referendum, 25.05%).",
    "Q1–Q5 · Immigration & ID": "Five non-constitutional provincial policy questions on immigration caps, residency waits, fees, and voter ID — all 5 passed (52.3%–59.8% For).",
    "Q6–Q9 · Constitutional": "Four federal constitutional amendment questions (judiciary, Senate abolition, fiscal opt-out, paramountcy) — all 4 were rejected (46.8%–49.8% For).",
    "True independence core": "Share of the total electorate whose primary stated motivation is full separation (~18%), since 68% of Option 2 voters sought leverage or a vote.",
    # Microeconomics · Gas Price Collusion (ST-06)
    "Oligopoly ex-tax spread": "Pre-tax retail & distribution markup M = P_pump − P_TGP − Tax in concentrated 3–5 firm oligopolies (24–28 c/L vs. 12 c/L competitive benchmark).",
    "AI pricing duopoly boost": "Causal margin expansion (+28%) estimated by Assad et al. (2024, JPE) when both local German stations adopt algorithmic repricing software.",
    "Focal signaling boost": "Retail margin expansion (+75%, +2.4–3.5 c/L) after BP used focal-point price leadership in Perth to end Edgeworth cycles (Byrne & de Roos 2019, AER).",
    "Rockets vs. Feathers": "Asymmetric Error Correction half-life: +10 c/L wholesale jumps pass through in ~1 day (Rocket), while −10 c/L drops decay over ~9–24 days (Feather).",
    # Chemistry · Sodium Battery Technology (ST-05)
    "Crustal abundance": "Earth's upper-crustal elemental concentration ratio: Sodium (23,600 ppm) vs. Lithium (20 ppm) = 1,180× higher geological abundance.",
    "Ionic volume ratio": "Six-coordinate Shannon octahedral volume ratio (r_Na+ / r_Li+)^3 = (1.02 Å / 0.76 Å)^3 ≈ 2.42×, explaining why Na+ requires hard carbon instead of graphite.",
    "Cell cost floor (BatPaC)": "Pack/cell manufacturing cost floor modeled in ANL BatPaC v5.1 ($41–$49/kWh for Na-ion using Al collectors on both electrodes vs. $68/kWh for LFP).",
    "Sub-zero retention (−20 °C)": "Available discharge capacity at −20 °C relative to 25 °C: Na-ion retains 88%–92% due to lower Stokes desolvation energy vs. 64% for LFP.",
    # Emerging Industries · AI Cost & Compute Economics (ST-08)
    "Inference deflation (2023→26)": "Cumulative reduction in unit token price ($/1M blended tokens) for GPT-4-equivalent or higher reasoning accuracy: from $36.00/1M (Mar 2023) to $0.18/1M (Gemini 3.8 Flash, 200×) and $3.50/1M (Gemini 4 Argon High Thinking, 10.3×).",
    "Gemini 4 Argon blended": "Blended API inference price ($3.50/1M tokens at 3:1 input/output ratio: $1.25/1M input, $10.00/1M output) achieving 89.2% MMLU-Pro / GPQA accuracy.",
    "DeepSeek / Flash floor": "Sub-$0.50/1M token frontier inference tier enabled by Sparse MoE (37B active of 671B), Multi-head Latent Attention (MLA 75% KV-cache reduction), and hardware distillation.",
    "Cascade routing savings": "Enterprise TCO reduction (80.6% savings: $0.68/1M vs. $3.50/1M) achieved by routing 85% of routine traffic to Gemini 3.8 Flash and 15% of complex proofs to Gemini 4 Argon High Thinking.",
    # Macroeconomics · Taxes on Generations Over Time Periods (ST-09)
    "Peak tax-bearing cohort (Gen X)": "Population-normalized real annual total tax burden (income, payroll, GST/HST, property, fuel/carbon, and sin excise) per capita for Generation X (ages 45–60) in constant 2024 CAD ($31,420/yr vs. $12,840 rewards).",
    "Senior fiscal reward ratio (65+)": "Ratio of total real per-capita public benefits received (OAS/GIS, CPP/QPP, and CIHI age-weighted healthcare Social Transfers in Kind) to total direct and indirect taxes paid by cohorts aged 65+ (2.31×).",
    "Commute fuel & carbon peak": "Mean one-way commute duration (28.4 mins) and annual per-capita road-fuel excise plus carbon levy expenditure ($780/cap) for Millennial commuters pushed into outer suburban rings (81.6% auto share).",
    "Gen Z vaping excise share": "Share of total national federal and provincial vaping excise duty paid by Generation Z (ages 15–28, 64.2% share / $168 per capita), driven by 19.7% prevalence at ages 20–24 vs. <1.5% for Boomers.",
    # Athletics & Health Dashboards
    "Sessions logged": "Total validated training sessions parsed from the plain-text log file in records/athletics/.",
    "Best interval": "Fastest single 0.95 km I1 neighbourhood loop recorded across all interval sessions.",
    "Latest average": "Mean loop time in the most recent interval session, compared against Session 1.",
    "Latest spread": "Pacing consistency metric: slowest interval minus fastest interval in the latest session.",
    "Total distance": "Cumulative swim distance across all logged sessions, converted to metres (1 yd = 0.9144 m).",
    "Average session": "Mean swim distance per session in metres.",
    "Best week": "Highest Monday–Sunday weekly swim volume in metres.",
    "Working sets": "Total logged resistance sets excluding warmups and dropsets.",
    "Loaded volume": "Total mechanical tonnage: Σ (reps × weight in lbs) across loaded exercises.",
    "Exercises": "Distinct lift names tracked in the weightlifting log.",
    "Nights logged": "Total consecutive or logged sleep dates in Sleep_and_Dream_Log.txt.",
    "Average sleep": "Mean nightly sleep duration in hours across the log window.",
    "Dreams written down": "Total distinct dream paragraphs recorded across all logged nights.",
    "Recall vs duration": "Mean sleep hours on nights with ≥1 written dream vs. nights marked 'No dreams recorded'.",
    "Days tracked": "Total full-day nutrition & expenditure entries in Diet_and_Calorie_Tracking.txt.",
    "Average deficit": "Mean daily net energy balance (Total Expenditure − Total Consumption) vs. the 500 kcal/day target.",
    "Estimated loss": "Cumulative caloric deficit divided by 3,500 kcal per pound of tissue equivalent.",
    "Burn above BMR": "Mean daily active energy expenditure above the 1,850 kcal basal metabolic rate (training + NEAT).",
}


def _metrics(
    items: list[tuple[str, ...]],
    *,
    with_tooltips: bool = False,
    mm_href: str = "",
    mm_label: str = "",
) -> str:
    if not with_tooltips:
        return '<div class="sports-metrics" aria-label="Logged totals">' + "".join(
            f'<div class="sports-metric"><span>{_e(item[0])}</span><strong>{_e(item[1])}</strong><small>{_e(item[2])}</small></div>'
            for item in items
        ) + "</div>"
    cards = []
    for item in items:
        label, value, note = item[0], item[1], item[2]
        defn = item[3] if len(item) > 3 and item[3] else KPI_DEFINITIONS.get(
            label,
            f"{label}: {note}. Empirical parameter computed from the study's primary dataset.",
        )
        item_mm_href = item[4] if len(item) > 4 and item[4] else mm_href
        item_mm_label = item[5] if len(item) > 5 and item[5] else mm_label
        mm_html = (
            f'<a class="kpi-tip-mm" href="{_e(item_mm_href)}">🧠 Mental Map: {_e(item_mm_label or "Open Section")} ↗</a>'
            if item_mm_href else ""
        )
        cards.append(
            f'<div class="sports-metric kpi-card" data-kpi-card tabindex="0" role="button" aria-expanded="false" '
            f'aria-label="{_e(label)}: {_e(value)}. Tap or hover for definition.">'
            f'<span class="kpi-head"><span>{_e(label)}</span><em class="kpi-info-badge" aria-hidden="true" title="Tap or hover for metric definition">ⓘ</em></span>'
            f'<strong>{_e(value)}</strong><small>{_e(note)}</small>'
            f'<div class="kpi-tooltip" role="tooltip">'
            f'<div class="kpi-tip-title">{_e(label)} · Definition</div>'
            f'<p class="kpi-tip-desc">{_e(defn)}</p>'
            f'{mm_html}'
            f'</div></div>'
        )
    return '<div class="sports-metrics" aria-label="Key study metrics (hover or tap any card for definition &amp; Mental Map link)">' + "".join(cards) + "</div>"


def _downloads(depth: int, files: list[tuple[str, str]]) -> str:
    prefix = "../" * depth + "assets/data/"
    links = "".join(f'<a class="button {"primary" if i == 0 else "ghost"}" href="{prefix}{_e(name)}" download>{_e(label)}</a>'
                    for i, (name, label) in enumerate(files))
    return f'<nav class="toolbar sports-downloads" aria-label="Downloads">{links}</nav>'


def _hero(kicker: str, badge: str, title: str, deck: str, actions: str, art: str) -> str:
    return (f'<header class="sports-hero"><div class="sports-hero-copy"><p class="sports-kicker">{_e(kicker)} <span>{_e(badge)}</span></p>'
            f'<h1>{title}</h1><p class="sports-deck">{_e(deck)}</p><div class="toolbar">{actions}</div></div>{art}</header>')


def _axis(top: float, bottom: float, low: float, high: float, labels, unit: str) -> str:
    rows = []
    for value in labels:
        y = bottom - (value - low) / (high - low) * (bottom - top)
        rows.append(f'<line class="chart-grid" x1="70" x2="870" y1="{y:.1f}" y2="{y:.1f}"/>'
                    f'<text x="60" y="{y + 4:.1f}" text-anchor="end">{_e(unit(value))}</text>')
    return "".join(rows)


def _chart(chart_id: str, title: str, desc: str, inner: str, height: int = 330) -> str:
    return (f'<div class="sports-chart-wrap" role="region" aria-label="{_e(title)}" tabindex="0">'
            f'<svg viewBox="0 0 900 {height}" class="sports-chart" role="img" aria-labelledby="{chart_id}-svg-title {chart_id}-svg-desc">'
            f'<title id="{chart_id}-svg-title">{_e(title)}</title><desc id="{chart_id}-svg-desc">{_e(desc)}</desc>{inner}</svg></div>')


def _table(caption: str, head: list[str], rows: list[list[Any]], table_id: str = "") -> str:
    ident = f' id="{table_id}"' if table_id else ""
    body = "".join("<tr>" + "".join((f'<th scope="row">{_e(cell)}</th>' if i == 0 else f"<td>{_e(cell)}</td>")
                                    for i, cell in enumerate(row)) + "</tr>" for row in rows)
    return (f'<div class="sports-table-wrap" role="region" aria-label="{_e(caption)}" tabindex="0"><table{ident}><caption>{_e(caption)}</caption>'
            f'<thead><tr>{"".join(f"<th scope=col>{_e(h)}</th>" for h in head)}</tr></thead><tbody>{body}</tbody></table></div>')


def _section(number: str, kicker: str, title: str, ident: str, content: str) -> str:
    return (f'<section class="sports-section" aria-labelledby="{ident}"><p class="sports-kicker">{_e(number)} / {_e(kicker)}</p>'
            f'<h2 id="{ident}">{_e(title)}</h2>{content}</section>')


def running_body(data: dict, lead: str = "", tempo: dict | None = None) -> str:
    sessions, summary, route = data["sessions"], data["summary"], data["routes"]["I1"]
    first, last = sessions[0], sessions[-1]
    best = summary["bestInterval"]
    deck = (f"Interval training for pace and VO₂ max on I1, a {route['distanceKm']} km neighbourhood loop. "
            f"{summary['sessions']} sessions logged since {_day(summary['firstDate'])}.")
    actions = ('<a class="button primary" href="Overview/index.html">Read the overview <span aria-hidden="true">↗</span></a>'
               '<a class="button ghost" href="#running-history">Best times, 2013–2017</a>'
               '<a class="button ghost" href="#running-update">Add a session ↓</a>')
    art = ('<figure class="athletics-route"><img src="../../../assets/documents/athletics-running/interval_track_1.png" '
           f'alt="Map of the I1 interval loop, about {route["distanceKm"]} km, drawn over residential streets." loading="lazy" decoding="async">'
           '<figcaption>I1 route, 0.95 km per loop. Start marker and coordinates removed.</figcaption></figure>')
    metrics = _metrics([
        ("Sessions logged", str(summary["sessions"]), f"{summary['intervals']} intervals in total"),
        ("Best interval", clock(best["seconds"]), f"{_day(best['date'])} · {clock(best['seconds'] / route['distanceKm'])} per km"),
        ("Latest average", clock(last["average"]), f"{summary['averageChange']:+.0f} s vs the first session ({summary['averageChangePercent']:+.1f}%)"),
        ("Latest spread", f"{summary['latestSpread']} s", "Slowest minus fastest interval"),
    ])
    times = [i["seconds"] for s in sessions for i in s["intervals"]]
    low, high = (min(times) // 15) * 15 - 5, -(-max(times) // 15) * 15 + 5
    count = max(s["count"] for s in sessions)
    x = lambda n: 110 + (n - 1) * 700 / max(1, count - 1)
    y = lambda v: 290 - (v - low) / (high - low) * 250
    lines = []
    for index, item in enumerate(sessions):
        cls = f"series-{index % SERIES}"
        points = " ".join(f"{x(i['number']):.1f},{y(i['seconds']):.1f}" for i in item["intervals"])
        dots = "".join(f'<circle class="athletics-dot" cx="{x(i["number"]):.1f}" cy="{y(i["seconds"]):.1f}" r="5"><title>{_e(_day(item["date"]))} · interval {i["number"]} · {_e(i["raw"])}</title></circle>'
                       for i in item["intervals"])
        end = item["intervals"][-1]
        lines.append(f'<g class="{cls}"><polyline class="athletics-line" points="{points}"/>{dots}'
                     f'<text class="athletics-label" x="{x(end["number"]) + 12:.1f}" y="{y(end["seconds"]) + 4:.1f}">{_e(_day(item["date"]))}</text></g>')
    grid = _axis(40, 290, low, high, range(int(low) + 5, int(high), 15), clock)
    ticks = "".join(f'<text x="{x(n):.1f}" y="314" text-anchor="middle">Interval {n}</text>' for n in range(1, count + 1))
    chart = _chart("running-intervals", "Every interval in every session",
                   f"Lines join the intervals of one session; time per {route['distanceKm']} km loop, lower is faster. "
                   "The table below lists every value.", grid + ticks + "".join(lines))
    legend = '<p class="sports-legend">' + "".join(f'<span class="series-{i % SERIES}">● {_e(_day(s["date"]))}</span>' for i, s in enumerate(sessions)) + "<span>Lower is faster.</span></p>"
    # Averages over time: a range bar from fastest to slowest interval with the mean marked.
    sx = lambda i: 110 + i * 700 / max(1, len(sessions) - 1)
    bars = []
    for index, item in enumerate(sessions):
        cx = sx(index)
        bars.append(f'<g class="series-{index % SERIES}"><line class="athletics-range" x1="{cx:.1f}" x2="{cx:.1f}" y1="{y(item["best"]):.1f}" y2="{y(item["worst"]):.1f}"/>'
                    f'<circle class="athletics-dot" cx="{cx:.1f}" cy="{y(item["average"]):.1f}" r="8"><title>{_e(_day(item["date"]))} average {clock(item["average"])}</title></circle>'
                    f'<text class="athletics-label" x="{cx + 14:.1f}" y="{y(item["average"]) + 4:.1f}">{clock(item["average"])}</text></g>'
                    f'<text x="{cx:.1f}" y="314" text-anchor="middle">{_e(_day(item["date"]))}</text>')
    averages = _chart("running-averages", "Session averages with fastest-to-slowest range",
                      "Each column is one session: the line spans its fastest and slowest interval and the dot marks the computed mean.",
                      _axis(40, 290, low, high, range(int(low) + 5, int(high), 15), clock) + "".join(bars))
    rows = [[_day(s["date"]), s["route"], " · ".join(i["raw"] for i in s["intervals"]), clock(s["average"]),
             s["recordedAverage"]["raw"] if s["recordedAverage"] else "— (none written)", clock(s["best"]),
             f'{s["spread"]:g} s', f'{s["fade"]:+g} s', clock(s["pacePerKm"])]
            for s in sessions]
    mismatch = summary["recordedAverageMismatches"]
    note = (f'<p class="sports-note">Recorded averages are kept as written. On {", ".join(_day(d) for d in mismatch)} the written average '
            "differs from the mean of the listed intervals by more than rounding.</p>") if mismatch else ""
    if summary["unwrittenAverages"]:
        note += (f'<p class="sports-note">No average was written for {", ".join(_day(d) for d in summary["unwrittenAverages"])}; '
                 "the computed mean stands alone there.</p>")
    history = data["history"]
    history_rows = [[row["year"], row["session"], row["best"], clock(row["pacePerKm"]) + " /km"] for row in history]
    history_rows.append([summary["lastDate"][:4], "I1 loop (0.95 km)", clock(best["seconds"]), clock(best["seconds"] / route["distanceKm"]) + " /km"])
    pattern = ("Every session finished faster than it started." if all(s["fade"] < 0 for s in sessions)
               else "How each session unfolded, interval by interval.")
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Running", "I1 · interval log", "Faster loops.<br>Same <em>route.</em>", deck, actions, art)}
      <p class="sports-scope">Every logged session · {_e(_day(summary["firstDate"]))} → {_e(_day(summary["lastDate"]))}, {summary["firstDate"][:4]}. Descriptive, not a training plan.</p>{metrics}
      {_section("01", "Every interval", pattern, "running-intervals-title", f'<div class="bi-running-host" data-bi-running="{_e(json.dumps({"sessions": sessions, "tempo": (tempo or {}).get("runs", [])}, separators=(",", ":")))}">' + legend + chart + '</div>' +
                '<p class="sports-note">Fade is last interval minus first; a negative fade means the session finished faster than it started.</p>')}
      {_section("02", "Session averages", f"{clock(first['average'])} to {clock(last['average'])} in {summary['sessions']} sessions.", "running-averages-title", averages + note)}
      {_section("03", "The log", "Every interval, as written.", "running-log-title",
                _table("Running sessions; times are minutes:seconds per loop.", ["Date", "Route", "Intervals", "Mean", "Written average", "Fastest", "Spread", "Fade", "Pace /km"], rows, "running-table"))}
      {_tempo_section(tempo) if tempo else ""}
      <section class="sports-section" id="running-history" aria-labelledby="running-history-title"><p class="sports-kicker">05 / Then and now</p><h2 id="running-history-title">Best times from 2013 and 2017.</h2>
      <p>Rough estimates recalled from the major training blocks; earlier logs were lost. Track repeats and a neighbourhood loop are different efforts, so compare paces loosely.</p>
      {_table("Best repeat time per session type, with pace per kilometre.", ["Year", "Session", "Best repeat", "Pace"], history_rows)}</section>
      <section class="sports-section sports-method" aria-labelledby="running-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="running-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}, read line by line; any unreadable line stops the build.</li>
      <li>Pace assumes each interval is one {route["distanceKm"]} km loop of I1 ({_e(route["distanceSource"])}).</li>
      <li>Means are computed from the listed intervals; written averages are shown beside them, never replaced.</li></ul>
      {_downloads(3, [("athletics-running.json", "Running log · JSON"), ("athletics-running-intervals.csv", "Intervals · CSV"), ("athletics-running-sessions.csv", "Sessions · CSV"), ("athletics-running-tempo.csv", "Tempo runs · CSV")])}</section>
      {_update_notes("running", data, '<li>Add a block per session: a line like <code>I1 - (10/6/2026) - 4 Intervals</code>, then one <code>m:ss</code> or <code>m:ss.s</code> time per line, '
                     'then optionally <code>Avg: m:ss</code>. The interval count must match the times listed; the written average is kept beside the computed mean.</li>'
                     '<li>Tempo runs go in <code>records/athletics/running/Tempo_Run_Log.txt</code>: a <code>(10/12/2026)</code> line, '
                     'a <code>Tempo Run - 5.8km (Route Name)</code> line, the total time like <code>33:23.81</code>, then the pace line like <code>5:45.5 min/km - 2.89m/s</code>.</li>')}
    </main>'''


def _tempo_section(tempo: dict) -> str:
    runs, summary = tempo["runs"], tempo["summary"]
    rows = [[_day(r["date"]), r["route"], f'{r["distanceKm"]:g} km', r["timeRaw"], clock(r["paceSeconds"]) + " /km",
             f'{r["speed"]:g} m/s', r["writtenPace"]["raw"]] for r in runs]
    chips = "".join(f'<li class="series-{i % SERIES}">{_e(_day(r["date"]))} · {_e(r["route"])} · {r["distanceKm"]:g} km @ {clock(r["paceSeconds"])}/km</li>'
                    for i, r in enumerate(runs))
    # Build static dual-metric SVG chart for Tempo Runs (Pace /km bars + Speed m/s line)
    step = 760 / max(1, len(runs))
    max_pace = max(360, int(max(r["paceSeconds"] for r in runs)) + 20)
    y_p = lambda v: 290 - (v / max_pace) * 235
    bars = []
    for idx, r in enumerate(runs):
        bx = 90 + idx * step
        bars.append(
            f'<rect class="athletics-bar series-1" x="{bx + step * .18:.1f}" y="{y_p(r["paceSeconds"]):.1f}" width="{step * .64:.1f}" height="{290 - y_p(r["paceSeconds"]):.1f}">'
            f'<title>{_e(_day(r["date"]))} · {_e(r["route"])} · {r["distanceKm"]:g} km · {clock(r["paceSeconds"])}/km ({r["speed"]:g} m/s)</title></rect>'
            f'<text x="{bx + step / 2:.1f}" y="{y_p(r["paceSeconds"]) - 8:.1f}" text-anchor="middle">{clock(r["paceSeconds"])}/km ({r["speed"]:g} m/s)</text>'
            f'<text x="{bx + step / 2:.1f}" y="314" text-anchor="middle">{_e(_day(r["date"]))}</text>'
        )
    grid = _axis(55, 290, 0, max_pace, range(0, max_pace + 1, 90), lambda v: f"{clock(v)}/km")
    tempo_chart = _chart(
        "running-tempo-chart",
        "Tempo run pace (/km) and speed (m/s) progression",
        "Bars show computed pace per kilometre (lower is faster) and speed in metres per second across logged continuous tempo runs.",
        grid + "".join(bars),
    )
    note = ("Pace and speed are computed from the written time and distance; the written pace line is kept beside them"
            + (" and matches" if not summary["paceMismatches"] else f" and differs on {', '.join(_day(d) for d in summary['paceMismatches'])}") + ". "
            "Route distances and names are as written; the route map stays unpublished because it shows the start point.")
    return (f'<section class="sports-section" id="running-tempo" aria-labelledby="running-tempo-title"><p class="sports-kicker">04 / Tempo runs</p>'
            f'<h2 id="running-tempo-title">Continuous runs, {summary["kilometres"]:g} km so far.</h2>'
            f'<ol class="athletics-chips" id="tempo-chips-list" aria-label="Tempo runs">{chips}</ol>'
            f'<div class="bi-tempo-host" data-bi-tempo="{_e(json.dumps(runs, separators=(",", ":")))}">{tempo_chart}</div>'
            + _table("Tempo runs; time as written, pace computed.", ["Date", "Route", "Distance", "Time", "Pace", "Speed", "Pace as written"], rows, "tempo-table")
            + f'<p class="sports-note">{_e(note)}</p></section>')


def swimming_body(data: dict, lead: str = "") -> str:
    sessions, summary, weeks = data["sessions"], data["summary"], data["weeks"]
    deck = (f"Low-impact distance work, logged since {_day(summary['firstDate'])}: "
            f"{_num(summary['meters'])} m over {summary['sessions']} sessions.")
    actions = ('<a class="button primary" href="Overview/index.html">Read the overview <span aria-hidden="true">↗</span></a>'
               '<a class="button ghost" href="#swimming-bests">High-school bests</a>'
               '<a class="button ghost" href="#swimming-update">Add a session ↓</a>')
    strokes = sessions[-1]["strokes"]
    art = ('<div class="athletics-lanes" aria-hidden="true">' + "".join(f'<span class="lane series-{i % SERIES}">{_e(stroke)}</span>' for i, stroke in enumerate(strokes)) + "</div>")
    metrics = _metrics([
        ("Sessions logged", str(summary["sessions"]), f"About every {summary['averageGapDays']} days"),
        ("Total distance", f"{_num(summary['meters'])} m", f"{_day(summary['firstDate'])} → {_day(summary['lastDate'])}"),
        ("Average session", f"{_num(summary['average'])} m", f"Longest {_num(summary['longest'])} m"),
        ("Best week", f"{_num(max(w['meters'] for w in weeks))} m", "Weeks start on Monday"),
    ])
    top = max(s["meters"] for s in sessions)
    high = -(-top // 500) * 500
    total = sessions[-1]["cumulativeMeters"]
    step = 760 / len(sessions)
    y = lambda v: 290 - v / high * 240
    yc = lambda v: 290 - v / total * 240
    bars, line = [], []
    for index, item in enumerate(sessions):
        bx = 90 + index * step
        bars.append(f'<rect class="athletics-bar series-0" x="{bx + step * .18:.1f}" y="{y(item["meters"]):.1f}" width="{step * .64:.1f}" height="{290 - y(item["meters"]):.1f}"><title>{_e(_day(item["date"]))} · {_num(item["meters"])} m</title></rect>'
                    f'<text x="{bx + step / 2:.1f}" y="{y(item["meters"]) - 8:.1f}" text-anchor="middle">{_num(item["meters"])}</text>'
                    f'<text x="{bx + step / 2:.1f}" y="314" text-anchor="middle">{_e(_day(item["date"]))}</text>')
        line.append(f"{bx + step / 2:.1f},{yc(item['cumulativeMeters']):.1f}")
    grid = _axis(50, 290, 0, high, range(0, int(high) + 1, 500), lambda v: f"{v:,} m")
    cumulative = (f'<polyline class="athletics-line series-1" points="{" ".join(line)}"/>'
                  f'<text class="athletics-label series-1" x="870" y="{yc(total) - 10:.1f}" text-anchor="end">{_num(total)} m in total</text>')
    chart = _chart("swimming-sessions", "Distance per session and running total",
                   "Bars show metres per session against the left axis. The line climbs to the running total on its own scale.", grid + "".join(bars) + cumulative)
    legend = '<p class="sports-legend"><span class="series-0">■ Session distance</span><span class="series-1">― Running total (own scale)</span></p>'
    rows = [[_day(s["date"]), f'{_num(s["distance"])} {"yd" if s["unit"] == "y" else "m"}', f'{_num(s["meters"])} m',
             s["orderRaw"], f'{_num(s["cumulativeMeters"])} m'] for s in sessions]
    week_rows = [[f"Week of {_day(w['weekOf'])}", f"{_num(w['meters'])} m"] for w in weeks]
    bests = [[b["event"], f'{b["liam"]:.2f} s', f'{b["owen"]:.2f} s', "Liam" if b["liam"] < b["owen"] else "Owen"] for b in data["bests"]]
    chips = "".join(f'<li class="series-{i % SERIES}">{i + 1}. {_e(stroke)}</li>' for i, stroke in enumerate(strokes))
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Swimming", "Distance log", "Lengths add<br>up to <em>kilometres.</em>", deck, actions, art)}
      <p class="sports-scope">Every logged session. Total distance only, for now: set times start once a pool-safe watch arrives.</p>{metrics}
      {_section("01", "Distance", "Every session, and where the total stands.", "swimming-distance-title", f'<div class="bi-swimming-host" data-bi-swimming="{_e(json.dumps(sessions, separators=(",", ":")))}">' + legend + chart + '</div>')}
      {_section("02", "Stroke order", "Each set swims all four strokes.", "swimming-strokes-title",
                f'<ol class="athletics-chips" aria-label="Stroke order as logged">{chips}</ol><p class="sports-note">Order as logged: {_e(sessions[-1]["orderRaw"])}. Strokes are swum as evenly as possible to balance the muscle groups.</p>'
                + _table("Weekly totals.", ["Week", "Distance"], week_rows))}
      {_section("03", "The log", "Every session, as written.", "swimming-log-title",
                _table("Swimming sessions.", ["Date", "As written", "In metres", "Sets and strokes", "Running total"], rows, "swimming-table") +
                (f'<p class="sports-note">Most sessions are logged in yards ({summary["yardSessions"]} of {summary["sessions"]}); the charts and totals convert to metres at 0.9144 m per yard. '
                 'Set distances inside a yard-day description share the day\'s unit even when suffixed “m”.</p>') +
                ((f'<p class="sports-note">On {", ".join(_day(d) for d in summary["setMismatches"])} the listed sets do not add up to the written total; '
                  'the written total drives the charts and the set list stays as written.</p>') if summary["setMismatches"] else ""))}
      <section class="sports-section" id="swimming-bests" aria-labelledby="swimming-bests-title"><p class="sports-kicker">04 / The old rivalry</p><h2 id="swimming-bests-title">High-school bests: Liam and Owen.</h2>
      <p>Best times from high-school racing, recalled rather than taken from a results sheet.</p>
      {_table("50 m best times; lower is faster.", ["Event", "Liam", "Owen", "Faster"], bests)}
      <aside class="sports-pending"><span class="sports-kicker">Next / Planned sets</span><h2>Timed sets, once the watch arrives.</h2>
      <p>5 × 50 m, 10 × 50 m and 5 × 100 m, each repeat inside a set window (for example 48 s per 50 m), with the remaining time as rest. No set times have been recorded yet.</p></aside></section>
      <section class="sports-section sports-method" aria-labelledby="swimming-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="swimming-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}; each line's sets × set distance must equal its total, or the build stops.</li>
      <li>Weeks run Monday to Sunday. The running total is the sum of logged sessions only.</li></ul>
      {_downloads(3, [("athletics-swimming.json", "Swimming log · JSON"), ("athletics-swimming-sessions.csv", "Sessions · CSV")])}</section>
      {_update_notes("swimming", data, '<li>Add one line per session, oldest first: <code>(10/6/2026) - 2000m - 5x400 of Fly-Back_Breast-Free</code>. '
                     'Sets × set distance must equal the total, and the stroke order is separated by - or _.</li>')}
    </main>'''


# Lines on the weight axis of each exercise chart: (point key, css class, legend label).
LIFT_LINES = (("value", "lift-top", "Heaviest set"), *((f"best{t}", f"lift-{t}", f"Heaviest for {t}+ reps") for t in REP_TARGETS))


def _ticks(low: float, high: float) -> list[float]:
    """At most five evenly spaced, round tick values covering low..high."""
    raw = ((high - low) or max(abs(high), 1)) / 3
    steps = (1, 2, 2.5, 5, 10, 15, 20, 25, 50, 100, 200, 250, 500, 1000, 1500, 2000, 2500, 5000, 10000)
    step = next(s for s in steps if s >= raw)
    start, end = max(0, math.floor(low / step) * step), math.ceil(high / step) * step
    end = end if end > start else start + step
    return [start + k * step for k in range(round((end - start) / step) + 1)]


def _weight(value: float | None, assisted: bool) -> str:
    return "—" if value is None else f"{value:g} lb" + (" assist" if assisted else "")


def _muscle_group(name: str) -> str:
    low = name.lower()
    if any(k in low for k in ("squat", "lunge", "calf", "hamstring", "quad", "leg press", "leg extension", "leg curl")):
        return "Legs"
    if any(k in low for k in ("crunch", "situp", "sit-up", "leg raise", "ab ")):
        return "Abs"
    if any(k in low for k in ("curl", "bicep", "hammer")):
        return "Biceps"
    if any(k in low for k in ("tricep", "dip", "rope extension", "bar extension", "cable extension", "overhead extension")):
        return "Triceps"
    if any(k in low for k in ("shoulder", "delt", "lateral raise", "raises")):
        return "Shoulders"
    if any(k in low for k in ("pullup", "pull-up", "pulldown", "pull down", "row", "lat ", "back extension", "deadlift")):
        return "Back"
    return "Chest"


def _progress(entry: dict) -> str:
    """One exercise: weight lines on the left axis, reps at the heaviest set as bars on the right axis."""
    points = entry["points"]
    assisted = entry["kind"] == "assisted"
    weights = [p[key] for p in points for key, _, _ in LIFT_LINES if p[key] is not None]
    wticks = _ticks(min(weights), max(weights))
    rmax = max(5, math.ceil(max(p["reps"] for p in points) / 5) * 5)
    rticks = range(0, rmax + 1, 5 if rmax <= 15 else 10)
    left, right, top, bottom = 46, 294, 26, 150
    x = lambda i: (left + right) / 2 if len(points) == 1 else left + 26 + i * (right - left - 52) / (len(points) - 1)
    y = lambda v: bottom - (v - wticks[0]) / (wticks[-1] - wticks[0]) * (bottom - top)
    yr = lambda r: bottom - r / rmax * (bottom - top)
    width = min(24, (right - left) / len(points) * .4)
    parts = [f'<line class="chart-grid" x1="{left}" x2="{right}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
             f'<text x="{left - 6}" y="{y(t) + 3.5:.1f}" text-anchor="end">{t:g}</text>' for t in wticks]
    parts += [f'<text class="axis-reps" x="{right + 6}" y="{yr(r) + 3.5:.1f}">{r}</text>' for r in rticks]
    parts.append(f'<text x="{left - 6}" y="12" text-anchor="end">lb</text><text class="axis-reps" x="{right + 6}" y="12">reps</text>')
    for i, p in enumerate(points):
        parts.append(f'<rect class="lift-reps" x="{x(i) - width / 2:.1f}" y="{yr(p["reps"]):.1f}" width="{width:.1f}" height="{bottom - yr(p["reps"]):.1f}">'
                     f'<title>{_e(_day(p["date"]))} · {p["reps"]} reps at the heaviest set</title></rect>'
                     f'<text x="{x(i):.1f}" y="168" text-anchor="middle">{_e(_day(p["date"]))}</text>')
    for key, cls, label in LIFT_LINES:
        runs, run = [], []
        for i, p in enumerate(points):  # A session with no qualifying set breaks the line.
            if p[key] is None:
                if run:
                    runs.append(run)
                run = []
            else:
                run.append((x(i), y(p[key]), p))
        runs += [run] if run else []
        lines = "".join(f'<polyline class="athletics-line" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b, _ in r)}"/>' for r in runs if len(r) > 1)
        dots = "".join(f'<circle class="athletics-dot" cx="{a:.1f}" cy="{b:.1f}" r="3.5"><title>{_e(_day(p["date"]))} · {_e(label.lower())}: '
                       f'{_e(_weight(p[key], assisted))}</title></circle>' for r in runs for a, b, p in r)
        labels = "".join(f'<text x="{a:.1f}" y="{b - 9:.1f}" text-anchor="middle">{p[key]:g}</text>' for r in runs for a, b, p in r) if key == "value" else ""
        parts.append(f'<g class="{cls}">{lines}{dots}{labels}</g>')
    if assisted:
        badge = '<span class="athletics-badge">Assist weight · lower means less help</span>'
    else:
        change = entry.get("change", 0)
        badge = f'<span class="athletics-badge {"up" if change > 0 else "flat"}">{change:+g} lb top set</span>'
    last = points[-1]
    summary = (f'Latest, {_day(last["date"])}: heaviest {_weight(last["value"], assisted)} × {last["reps"]}; '
               + "; ".join(f"{t}+ reps {_weight(last[f'best{t}'], assisted)}" for t in REP_TARGETS))
    e1rm = [p["e1rm"] for p in points if p.get("e1rm")]
    extra = f'<small>{_e(summary)}.</small>' + (f'<small>Estimated 1RM, latest: {e1rm[-1]:g} lb</small>' if e1rm else "")
    label = (f'{entry["name"]}, {len(points)} sessions. Left axis: {"assistance" if assisted else "weight"} in pounds for the heaviest set and the heaviest '
             f'for 10+ and 12+ reps. Right axis: reps at the heaviest set. {summary}.')
    m_grp = _muscle_group(entry["name"])
    return (f'<article class="athletics-multiple" data-muscle-group="{_e(m_grp)}" data-exercise-name="{_e(entry["name"])}" '
            f'data-exercise-kind="{_e(entry["kind"])}" data-exercise-points="{_e(json.dumps(points, separators=(",", ":")))}">'
            f'<div class="multiple-head"><h3>{_e(entry["name"])}</h3><span class="muscle-pill muscle-{_e(m_grp.lower())}">{_e(m_grp)}</span></div>{badge}'
            f'<svg class="athletics-spark" viewBox="0 0 340 176" role="img" aria-label="{_e(label)}">{"".join(parts)}</svg>{extra}</article>')


def _update_notes(key: str, data: dict, steps: str) -> str:
    """Owner notes + non-Admin 0-token Google Doc / Logs refresh & on-site quick-add panel."""
    source = data["source"]
    last_date = data.get("summary", {}).get("lastDate", "2026-10-18")
    default_url = (
        "https://docs.google.com/document/d/1mboHEkA2jzHEbJY0mcuXbP-N_cWfyaN-LiN2z8xueq0/edit"
        if key == "weightlifting"
        else "https://docs.google.com/document/d/1kaKlOi_fPPrxHyCwf-G3nP93TkC-aPLT5Y-7b776Pmo/edit"
        if key in ("running", "tempo")
        else ""
    )
    sample_placeholder = {
        "diet": "10/28/2026\nBreakfast - 3/1/28g Protein Powder, Large Regular Coffee 20/7/1g, 81/3/3g 3 Bananas\nLunch - 84/30/24g Fried Rice (2/3 Tupperware)\nDinner - 37/20/50g Pulled Ham on a Bun, 2/20/60g Chicken Parmesan, 19/4/3g Roasted Potato Wedges\nSnacks - Nothing\nTotal Expenditure - 2800cals\nTotal Consumption - 2425cals - 246/85/169g\nNet Expenditure - 375cal loss",
        "weightlifting": "10/28/2026 - Back & Bis\nAssisted Pullups; 12x90lbs, 10x75lbs, 8x60lbs\nBarbell Curls; 15x50lbs, 12x60lbs, 8x70lbs",
        "swimming": "(10/28/2026) - 2000m - 5x400 of Fly-Back_Breast-Free",
        "running": "I1 - (10/28/2026) - 4 Intervals\n3:42.0\n3:39.5\n3:36.2\n3:33.8\nAvg: 3:37.9",
        "tempo": "(10/28/2026)\nTempo Run - 4.6km (House to Vape Store & Back)\n21:10.00\n4:36.1 min/km - 3.62m/s",
        "sleep": "10/28/2026\n7.5hrs\nNo dreams recorded",
    }.get(key, "")
    return (f'<section class="sports-section athletics-update" id="{key}-update" aria-labelledby="{key}-update-title">'
            f'<p class="sports-kicker">Google Drive Logs Sync &amp; Direct On-Site Editor · No Terminal Required</p>'
            f'<h2 id="{key}-update-title">Refresh from Google Docs or add an entry directly from the site.</h2>'
            f'<div class="gdoc-sync-box" data-gdoc-sync="{_e(key)}" data-gdoc-last-date="{_e(last_date)}" data-gdoc-default-url="{_e(default_url)}" data-gdoc-repo-path="{_e(source["path"])}">'
            f'<div class="gdoc-sync-head">'
            f'<div><strong>🔄 Live Google Drive / Docs Sync &amp; On-Site Publisher (<code>{_e(source["path"])}</code>)</strong>'
            f'<small class="gdoc-sync-sub">Currently built through <strong>{_e(last_date)}</strong> · Uses <strong>0 API tokens</strong> to validate, update charts &amp; tables live, and commit to GitHub.</small></div>'
            f'<div class="wb-form-actions">'
            f'<button class="button primary gdoc-refresh-btn" type="button" data-gdoc-refresh-btn="{_e(key)}">↻ Check &amp; Refresh Log Now (0 Tokens)</button>'
            f'<button class="button ghost" type="button" data-gdoc-commit-btn="{_e(key)}">☁️ Commit &amp; Publish Log to GitHub</button>'
            f'<a class="button ghost" href="../../../Updates/index.html">All Doc Updates Hub ↗</a>'
            f'</div>'
            f'</div>'
            f'<div class="gdoc-sync-controls">'
            f'<label for="gdoc-url-{_e(key)}">Option A — Google Doc share URL or ID for <code>{_e(key)}</code> inside your Google Drive <code>Logs/</code> folder (saved across devices):</label>'
            f'<div class="gdoc-sync-row">'
            f'<input id="gdoc-url-{_e(key)}" type="url" value="{_e(default_url)}" placeholder="Paste https://docs.google.com/document/d/... link from your Drive Logs folder (Anyone with link: Viewer)">'
            f'<button class="button ghost" type="button" data-gdoc-save-btn="{_e(key)}">Save Link</button>'
            f'</div>'
            f'<details class="gdoc-quick-add" style="margin-top:10px;">'
            f'<summary style="cursor:pointer;color:#9ddacf;font-weight:600;">➕ Option B — Paste or Type a New Entry Directly on the Site (0 Tokens · Updates Charts, Tables &amp; GitHub)</summary>'
            f'<div style="margin-top:8px;display:grid;gap:8px;">'
            f'<textarea id="gdoc-append-text-{_e(key)}" rows="6" style="width:100%;font-family:monospace;font-size:13px;padding:10px;border-radius:8px;background:#0d101b;color:#eeeef7;border:1px solid rgba(157,218,207,0.3);" placeholder="{_e(sample_placeholder)}"></textarea>'
            f'<div class="wb-form-actions">'
            f'<button class="button primary" type="button" data-gdoc-append-btn="{_e(key)}">⚡ Append Entry, Update Charts &amp; Publish from Site (0 Tokens)</button>'
            f'</div></div></details>'
            f'<p class="gdoc-sync-status" id="gdoc-status-{_e(key)}" role="status" aria-live="polite">'
            f'Ready · Click "Check &amp; Refresh Log Now" to pull from Google Docs, or open Option B above to paste a new entry directly on the site.'
            f'</p>'
            f'</div></div>'
            f'<ol><li><strong>Do it 100% from the site (Phone or Desktop):</strong> Either paste your Google Doc share link in <strong>Option A</strong> above and click <strong>↻ Check &amp; Refresh Log Now (0 Tokens)</strong>, OR open <strong>➕ Option B</strong> above, paste your new entry, and click <strong>⚡ Append Entry, Update Charts &amp; Publish from Site</strong>. Both immediately apply the <strong>0-token regex formatter</strong>, redraw the interactive PowerBI charts, KPI cards, and tables on this page, relay across your devices, and commit to GitHub (when your GitHub PAT is saved in <strong>🔐 Unlock Admin</strong>).</li>'
            f'{steps}'
            f'<li>Canonical repo file: <code>{_e(source["path"])}</code> in plain text (.txt) (also mirrored under <code>LiamMs_PandasProjects/Gaming-and-Performance-Log/</code>; both copies are updated together when you click <strong>☁️ Commit &amp; Publish Log to GitHub</strong>).</li>'
            '<li>Optional local CLI sync: If you are in VS Code, you can also run <code>python -B -m site_content.log_sync ; python -B -m site_content.build --also-local</code> and push <code>liammspandasprojects</code>.</li></ol>'
            f'<p>The latest entry, as written:</p>'
            + (f'<p class="sports-note" data-wb-admin-locked-msg>🔒 Latest written dream/journal entry is Admin-protected — Unlock Admin to view.</p>'
               f'<pre class="athletics-entry" id="gdoc-preview-{_e(key)}" data-wb-admin-only hidden>{_e(chr(10).join(source["latestEntry"]))}</pre>'
               if key == "sleep"
               else f'<pre class="athletics-entry" id="gdoc-preview-{_e(key)}">{_e(chr(10).join(source["latestEntry"]))}</pre>')
            + '<p class="sports-note">An older copy under LiamMs_PandasProjects/Gaming-and-Performance-Log/ is checked too: '
            'if it differs from the file above, the build stops instead of skipping the edit.</p></section>')


def weightlifting_body(data: dict, lead: str = "") -> str:
    sessions, summary = data["sessions"], data["summary"]
    deck = (f"Push, pull and shoulder days since {_day(summary['firstDate'])}: {summary['sessions']} sessions, "
            f"{summary['sets']} working sets (dropsets excluded).")
    actions = ('<a class="button primary" href="Overview/index.html">Read the overview <span aria-hidden="true">↗</span></a>'
               '<a class="button ghost" href="#lifting-peaks">Past peaks</a>'
               '<a class="button ghost" href="#weightlifting-update">Add a session ↓</a>')
    splits = summary["splits"]
    art = ('<div class="athletics-split-card" aria-hidden="true">' + "".join(
        f'<span class="split-{name}"><strong>{count}</strong>{_e(name)} days</span>' for name, count in splits.items()) + "</div>")
    metrics = _metrics([
        ("Sessions logged", str(summary["sessions"]), f"{_day(summary['firstDate'])} → {_day(summary['lastDate'])}"),
        ("Working sets", str(summary["sets"]), f"{_num(summary['reps'])} reps"),
        ("Loaded volume", f"{_num(summary['volume'])} lb", "Reps × weight, loaded lifts only"),
        ("Exercises", str(summary["exercises"]), "Names kept as logged"),
    ])
    high = -(-max(s["volume"] for s in sessions) // 5000) * 5000
    step = 760 / len(sessions)
    y = lambda v: 290 - v / high * 240
    bars = []
    for index, item in enumerate(sessions):
        bx = 90 + index * step
        bars.append(f'<rect class="athletics-bar split-{item["split"]}" x="{bx + step * .16:.1f}" y="{y(item["volume"]):.1f}" width="{step * .68:.1f}" height="{290 - y(item["volume"]):.1f}"><title>{_e(_day(item["date"]))} · {_e(item["splitRaw"])} · {_num(item["volume"])} lb</title></rect>'
                    f'<text x="{bx + step / 2:.1f}" y="{y(item["volume"]) - 8:.1f}" text-anchor="middle">{item["volume"] / 1000:.1f}k lb</text>'
                    f'<text x="{bx + step / 2:.1f}" y="314" text-anchor="middle">{_e(_day(item["date"]))}</text>')
    grid = _axis(50, 290, 0, high, range(0, int(high) + 1, 5000), lambda v: f"{v / 1000:g}k lb")
    chart = _chart("lifting-volume", "Loaded volume per session (lb), coloured by split",
                   "Bars show reps times weight (lb) for loaded lifts in each session. Bodyweight and assisted sets add no volume.", grid + "".join(bars))
    legend = '<p class="sports-legend">' + "".join(f'<span class="split-{name}">■ {name}</span>' for name in splits) + "<span>Bodyweight and assisted sets count no volume (0 lb).</span></p>"
    lifting_bi_wrap = f'<div class="bi-lifting-host" id="bi-lifting-host" data-bi-lifting="{_e(json.dumps(sessions, separators=(",", ":")))}">{legend}{chart}</div>'
    tracked = [entry for entry in data["exercises"] if entry["kind"] in ("loaded", "assisted") and len(entry["points"]) > 1]
    multiples = '<div class="athletics-multiples" id="lifting-multiples-grid">' + "".join(_progress(entry) for entry in tracked) + "</div>"
    lift_legend = ('<p class="sports-legend">' + "".join(f'<span class="{cls}">{mark} {_e(label)} (left axis, lb)</span>'
                                                         for (_, cls, label), mark in zip(LIFT_LINES, ("―", "╌", "┈")))
                   + '<span class="lift-reps-key">▮ Reps at the heaviest set (right axis)</span></p>')
    value_rows = [[e["name"], _day(p["date"]), _weight(p["value"], e["kind"] == "assisted"), p["reps"],
                   *(_weight(p[f"best{t}"], e["kind"] == "assisted") for t in REP_TARGETS)] for e in tracked for p in e["points"]]
    values = (f'<details><summary>Show the values behind these charts</summary>'
              + _table("Per exercise and session: heaviest set, its reps, and the heaviest weight lifted for at least 10 and 12 reps.",
                       ["Exercise", "Date", "Heaviest set", "Reps", *(f"{t}+ reps" for t in REP_TARGETS)], value_rows, "lifting-progress-table")
              + "</details>")
    rows = [[_day(s["date"]), s["splitRaw"], e["name"],
             ", ".join(f'{x["reps"]}×{x["weight"]:g}' for x in e["sets"]) or "— nothing written",
             e["kind"] + (" · excluded: " + ", ".join(f'{t["raw"]} ({t["reason"]})' for t in e["excludedSets"]) if e["excludedSets"] else "")]
            for s in sessions for e in s["exercises"]]
    peaks = [[p["peak"], p["lift"], f'{p["weightLbs"]} lb' + (f' × {p["reps"]}' if p["reps"] else "")] for p in data["peaks"]]
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Weightlifting", "Training log", "Heavier sets,<br>one <em>week</em> at a time.", deck, actions, art)}
      <p class="sports-scope">Every logged working set. Descriptive, not a programme or a strength rating.</p>{metrics}
      {_section("01", "Volume", "How much work each session moved.", "lifting-volume-title", lifting_bi_wrap)}
      {_section("02", "Progress by exercise", "Top sets and rep targets, session by session.", "lifting-progress-title",
                '<p>Every exercise logged more than once. The left axis is weight: the heaviest set, plus the heaviest weight managed for at least 10 reps '
                'and for at least 12 reps. The bars, on the right axis, count the reps done at the heaviest set. Assisted lifts plot the least assistance '
                'instead, so lower is better. A line breaks where a session had no set reaching 10 or 12 reps.</p>' + lift_legend + multiples + values +
                '<p class="sports-note">Estimated one-rep maximums use the Epley formula (weight × (1 + reps ÷ 30)) on the best set; they are rough for high-rep sets and were not tested.</p>')}
      <section class="sports-section" aria-labelledby="lifting-log-title"><p class="sports-kicker">03 / The log</p><h2 id="lifting-log-title">Every set, as written.</h2>
      <details><summary>Show all {summary["sets"]} working sets</summary>{_table("Weightlifting log; sets are reps × pounds.", ["Date", "Split", "Exercise", "Sets", "Kind"], rows, "lifting-table")}</details></section>
      <section class="sports-section" id="lifting-peaks" aria-labelledby="lifting-peaks-title"><p class="sports-kicker">04 / Past peaks</p><h2 id="lifting-peaks-title">The numbers to beat.</h2>
      <p>Recalled peaks since 2012, not part of the current log.</p>{_table("Past peaks.", ["When", "Lift", "Weight"], peaks)}</section>
      <section class="sports-section sports-method" aria-labelledby="lifting-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="lifting-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}; dropsets are excluded in the log itself.</li>
      <li>Exercise names are shown with spelling fixed (for example Dumbell → Dumbbell); the raw names stay in the downloads. Differently named lifts are never merged.</li>
      <li>Assisted lifts record the machine's assistance, so lower numbers mean more bodyweight lifted.</li></ul>
      {_downloads(3, [("athletics-weightlifting.json", "Lifting log · JSON"), ("athletics-weightlifting-sets.csv", "Sets · CSV"), ("athletics-weightlifting-sessions.csv", "Sessions · CSV"), ("athletics-weightlifting-progress.csv", "Progress · CSV")])}</section>
      {_update_notes("weightlifting", data, '<li>Start each day with a line like <code>10/6/2026 - Chest &amp; Abs</code>; the first word is the split (Chest, Back, Delts or Shoulders). '
                     'Below it, one line per exercise: <code>Exercise Name; 12x95lbs, 10x115lbs, 8x125lbs</code>, sets as reps x pounds. '
                     'Write 0lbs for bodyweight sets and keep Assisted in the name for assisted machines. A ; or : after the name both work.</li>')}
    </main>'''
