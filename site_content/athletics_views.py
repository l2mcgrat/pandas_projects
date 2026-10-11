"""Running, swimming and weightlifting dashboards: static SVG charts, escaped text, no scripts.

Each body is the <main> for a hosted destination at depth 3, styled by sports.css
plus athletics.css. Pass load_athletics(root)[key]; lead is the atlas location bar.
Charts are complete without JavaScript, and every chart has a table equivalent.
"""

from __future__ import annotations

from datetime import date
from html import escape
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


def _metrics(items: list[tuple[str, str, str]]) -> str:
    return '<div class="sports-metrics" aria-label="Logged totals">' + "".join(
        f'<div class="sports-metric"><span>{_e(label)}</span><strong>{_e(value)}</strong><small>{_e(note)}</small></div>'
        for label, value, note in items) + "</div>"


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


def running_body(data: dict, lead: str = "") -> str:
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
             s["recordedAverage"]["raw"], clock(s["best"]), f'{s["spread"]} s', f'{s["fade"]:+d} s', clock(s["pacePerKm"])]
            for s in sessions]
    mismatch = summary["recordedAverageMismatches"]
    note = (f'<p class="sports-note">Recorded averages are kept as written. On {", ".join(_day(d) for d in mismatch)} the written average '
            "differs from the mean of the listed intervals by more than rounding.</p>") if mismatch else ""
    history = data["history"]
    history_rows = [[row["year"], row["session"], row["best"], clock(row["pacePerKm"]) + " /km"] for row in history]
    history_rows.append([summary["lastDate"][:4], "I1 loop (0.95 km)", clock(best["seconds"]), clock(best["seconds"] / route["distanceKm"]) + " /km"])
    pattern = ("Every session finished faster than it started." if all(s["fade"] < 0 for s in sessions)
               else "How each session unfolded, interval by interval.")
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Running", "I1 · interval log", "Faster loops.<br>Same <em>route.</em>", deck, actions, art)}
      <p class="sports-scope">Every logged session · {_e(_day(summary["firstDate"]))} → {_e(_day(summary["lastDate"]))}, {summary["firstDate"][:4]}. Descriptive, not a training plan.</p>{metrics}
      {_section("01", "Every interval", pattern, "running-intervals-title", legend + chart +
                '<p class="sports-note">Fade is last interval minus first; a negative fade means the session finished faster than it started.</p>')}
      {_section("02", "Session averages", f"{clock(first['average'])} to {clock(last['average'])} in {summary['sessions']} sessions.", "running-averages-title", averages + note)}
      {_section("03", "The log", "Every interval, as written.", "running-log-title",
                _table("Running sessions; times are minutes:seconds per loop.", ["Date", "Route", "Intervals", "Mean", "Written average", "Fastest", "Spread", "Fade", "Pace /km"], rows, "running-table"))}
      <section class="sports-section" id="running-history" aria-labelledby="running-history-title"><p class="sports-kicker">04 / Then and now</p><h2 id="running-history-title">Best times from 2013 and 2017.</h2>
      <p>Rough estimates recalled from the major training blocks; earlier logs were lost. Track repeats and a neighbourhood loop are different efforts, so compare paces loosely.</p>
      {_table("Best repeat time per session type, with pace per kilometre.", ["Year", "Session", "Best repeat", "Pace"], history_rows)}</section>
      <section class="sports-section sports-method" aria-labelledby="running-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="running-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}, read line by line; any unreadable line stops the build.</li>
      <li>Pace assumes each interval is one {route["distanceKm"]} km loop of I1 ({_e(route["distanceSource"])}).</li>
      <li>Means are computed from the listed intervals; written averages are shown beside them, never replaced.</li></ul>
      {_downloads(3, [("athletics-running.json", "Running log · JSON"), ("athletics-running-intervals.csv", "Intervals · CSV"), ("athletics-running-sessions.csv", "Sessions · CSV")])}</section>
      {_update_notes("running", data, '<li>Add a block per session: a line like <code>I1 - (10/6/2026) - 4 Intervals</code>, then one <code>m:ss</code> time per line, '
                     'then <code>Avg: m:ss</code>. The interval count must match the times listed; the written average is kept beside the computed mean.</li>')}
    </main>'''


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
    rows = [[_day(s["date"]), f'{_num(s["meters"])} m', f'{s["sets"]} × {s["setMeters"]} m', s["orderRaw"], f'{_num(s["cumulativeMeters"])} m'] for s in sessions]
    week_rows = [[f"Week of {_day(w['weekOf'])}", f"{_num(w['meters'])} m"] for w in weeks]
    bests = [[b["event"], f'{b["liam"]:.2f} s', f'{b["owen"]:.2f} s', "Liam" if b["liam"] < b["owen"] else "Owen"] for b in data["bests"]]
    chips = "".join(f'<li class="series-{i % SERIES}">{i + 1}. {_e(stroke)}</li>' for i, stroke in enumerate(strokes))
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Swimming", "Distance log", "Lengths add<br>up to <em>kilometres.</em>", deck, actions, art)}
      <p class="sports-scope">Every logged session. Total distance only, for now: set times start once a pool-safe watch arrives.</p>{metrics}
      {_section("01", "Distance", "Every session, and where the total stands.", "swimming-distance-title", legend + chart)}
      {_section("02", "Stroke order", "Each set swims all four strokes.", "swimming-strokes-title",
                f'<ol class="athletics-chips" aria-label="Stroke order as logged">{chips}</ol><p class="sports-note">Order as logged: {_e(sessions[-1]["orderRaw"])}. Strokes are swum as evenly as possible to balance the muscle groups.</p>'
                + _table("Weekly totals.", ["Week", "Distance"], week_rows))}
      {_section("03", "The log", "Every session, as written.", "swimming-log-title",
                _table("Swimming sessions.", ["Date", "Distance", "Sets", "Stroke order", "Running total"], rows, "swimming-table"))}
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
    step = next(s for s in (1, 2, 2.5, 5, 10, 15, 20, 25, 50, 100, 200, 250, 500, 1000) if s >= raw)
    start, end = max(0, math.floor(low / step) * step), math.ceil(high / step) * step
    end = end if end > start else start + step
    return [start + k * step for k in range(round((end - start) / step) + 1)]


def _weight(value: float | None, assisted: bool) -> str:
    return "—" if value is None else f"{value:g} lb" + (" assist" if assisted else "")


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
    return (f'<article class="athletics-multiple"><h3>{_e(entry["name"])}</h3>{badge}'
            f'<svg class="athletics-spark" viewBox="0 0 340 176" role="img" aria-label="{_e(label)}">{"".join(parts)}</svg>{extra}</article>')


def _update_notes(key: str, data: dict, steps: str) -> str:
    """Owner notes: where the log lives, the line format, and how to rebuild."""
    source = data["source"]
    return (f'<section class="sports-section athletics-update" id="{key}-update" aria-labelledby="{key}-update-title">'
            f'<p class="sports-kicker">Owner notes / Adding data</p><h2 id="{key}-update-title">Add a session.</h2>'
            f'<ol><li>Open <code>{_e(source["path"])}</code> in the pandas_projects folder. It is plain text (.txt). '
            'The CSV and JSON files on this page are exports made from it at every build; editing them changes nothing.</li>'
            f'{steps}<li>Rebuild from pandas_projects with <code>python -B -m site_content.build --also-local</code>. '
            'Any line the build cannot read stops it with the line number.</li>'
            '<li>Publish by committing and pushing the liammspandasprojects repository.</li></ol>'
            f'<p>The latest entry, as written:</p><pre class="athletics-entry">{_e(chr(10).join(source["latestEntry"]))}</pre>'
            f'<p class="sports-note">An older copy at LiamMs_PandasProjects/Gaming-and-Performance-Log/Athletics/ is checked too: '
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
                    f'<text x="{bx + step / 2:.1f}" y="{y(item["volume"]) - 8:.1f}" text-anchor="middle">{item["volume"] / 1000:.1f}k</text>'
                    f'<text x="{bx + step / 2:.1f}" y="314" text-anchor="middle">{_e(_day(item["date"]))}</text>')
    grid = _axis(50, 290, 0, high, range(0, int(high) + 1, 5000), lambda v: f"{v / 1000:g}k")
    chart = _chart("lifting-volume", "Loaded volume per session, coloured by split",
                   "Bars show reps times weight for loaded lifts in each session. Bodyweight and assisted sets add no volume.", grid + "".join(bars))
    legend = '<p class="sports-legend">' + "".join(f'<span class="split-{name}">■ {name}</span>' for name in splits) + "<span>Bodyweight and assisted sets count no volume.</span></p>"
    tracked = [entry for entry in data["exercises"] if entry["kind"] in ("loaded", "assisted") and len(entry["points"]) > 1]
    multiples = '<div class="athletics-multiples">' + "".join(_progress(entry) for entry in tracked) + "</div>"
    lift_legend = ('<p class="sports-legend">' + "".join(f'<span class="{cls}">{mark} {_e(label)} (left axis, lb)</span>'
                                                         for (_, cls, label), mark in zip(LIFT_LINES, ("―", "╌", "┈")))
                   + '<span class="lift-reps-key">▮ Reps at the heaviest set (right axis)</span></p>')
    value_rows = [[e["name"], _day(p["date"]), _weight(p["value"], e["kind"] == "assisted"), p["reps"],
                   *(_weight(p[f"best{t}"], e["kind"] == "assisted") for t in REP_TARGETS)] for e in tracked for p in e["points"]]
    values = (f'<details><summary>Show the values behind these charts</summary>'
              + _table("Per exercise and session: heaviest set, its reps, and the heaviest weight lifted for at least 10 and 12 reps.",
                       ["Exercise", "Date", "Heaviest set", "Reps", *(f"{t}+ reps" for t in REP_TARGETS)], value_rows, "lifting-progress-table")
              + "</details>")
    rows = [[_day(s["date"]), s["splitRaw"], e["name"], ", ".join(f'{x["reps"]}×{x["weight"]:g}' for x in e["sets"]), e["kind"]]
            for s in sessions for e in s["exercises"]]
    peaks = [[p["peak"], p["lift"], f'{p["weightLbs"]} lb' + (f' × {p["reps"]}' if p["reps"] else "")] for p in data["peaks"]]
    return f'''<main id="main-content" class="collection-page sports-page athletics-page">{lead}
      {_hero("Athletics / Weightlifting", "Training log", "Heavier sets,<br>one <em>week</em> at a time.", deck, actions, art)}
      <p class="sports-scope">Every logged working set. Descriptive, not a programme or a strength rating.</p>{metrics}
      {_section("01", "Volume", "How much work each session moved.", "lifting-volume-title", legend + chart)}
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
