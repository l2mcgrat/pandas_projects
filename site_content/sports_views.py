"""Escaped, offline Sports bodies; no shell, I/O, analysis or source mutation.

The parent loads web/sports.css after portfolio.css, and deferred web/sports.js
after assets/data/basketball-analysis.js (window.BASKETBALL_ANALYSIS). Routes:
Sports-and-Entertainment/Series-Hub/index.html (depth 2) and its Analytics
destination (depth 3).
Pass the enriched basketball.analyze_series result, not the raw log. Optional
raw-source downloads are opt-in with data['sourceDownloadAvailable'] = True;
the parent must publish assets/data/basketball-source.json before opting in.
All charts and evidence remain available without JavaScript. No inline scripts.
"""

from __future__ import annotations

from html import escape
import math
from typing import Any
from urllib.parse import urlencode

__all__ = ["sports_body", "basketball_body", "sports_net_svg"]

CHALLENGES = (
    ("shooting", "Shooting"), ("bump", "Bump"), ("horse", "HORSE"),
    ("backboard", "Backboard"), ("three-point", "3 Point"),
    ("rim", "Rim"), ("one-on-one", "1v1"),
)
CSV_TABLES = (
    "summary", "series", "rounds", "challenges", "transitions", "byPicker",
    "conditionalNextChallenge", "transitionMatrix", "trajectories",
    "seriesLengths", "comebacks", "timing",
)
_NAMES = {"L": "Liam", "O": "Owen"}
_LABELS = dict(CHALLENGES)


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _obj(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _rows(value: Any) -> list[dict]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _n(value: Any) -> int:
    return int(value) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else 0


def _pct(numerator: Any, denominator: Any) -> str:
    return f"{100 * _n(numerator) / _n(denominator):.1f}%" if _n(denominator) else "—"


def _width(numerator: Any, denominator: Any) -> str:
    return f"{min(100, 100 * _n(numerator) / _n(denominator)):.3f}" if _n(denominator) else "0"


def _duration(seconds: Any) -> str:
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        return "Not recorded"
    minutes, remainder = divmod(int(seconds), 60)
    return f"{minutes}:{remainder:02d}"


def _player(value: Any) -> str:
    return value if isinstance(value, str) and value in _NAMES else "unknown"


def _name(value: Any) -> str:
    return _NAMES.get(_player(value), "Unrecorded")


def _label(value: Any) -> str:
    return _LABELS.get(str(value), str(value or "Unrecorded challenge"))


def _series_url(item: dict, base: str = "index.html", number: int | None = None) -> str:
    query = urlencode({"series": str(item.get("id", "")),
                       "round": _n(item.get("roundCount")) if number is None else number})
    return _e(f"{base}?{query}#play-by-play")


def _default_series(data: dict) -> dict:
    series = _rows(data.get("series"))
    return next((row for row in series if row.get("id") == "2026-09-10-1"),
                next((row for row in series if row.get("decider")), series[0] if series else {}))


def _legend() -> str:
    return '<p class="sports-legend"><span class="player-L">● L / Liam</span><span class="player-O">■ O / Owen</span><span>Labels and shapes accompany colour.</span></p>'


def sports_net_svg() -> str:
    """Original, ID-free net + ball artwork, also reusable by the parent map."""
    return '''<svg class="sports-net sports-net-art" viewBox="0 0 320 280" role="img" aria-label="Original basketball and woven net illustration">
      <title>A ball, a rim, a possibility</title><desc>An original line drawing of a basketball above a woven net. Decorative motion plays only on request, never a recorded shot.</desc>
      <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path class="net-board" d="M54 136V30H266V136M122 118V83H198V118"/>
        <g class="net-weave"><path d="M81 142L110 239Q160 261 210 239L239 142M103 146L126 245M126 149L145 250M149 150L163 251M173 150L184 247M197 148L204 241M219 145L221 200"/>
        <path d="M85 156L130 186L187 158L228 191M95 190L139 218L216 175M105 223L149 246L209 211M91 177L172 222L219 197M115 147L193 193L226 174M148 150L219 191M178 149L232 165M116 235L189 195L228 217M100 207L182 164"/></g>
        <ellipse class="net-rim" cx="160" cy="139" rx="81" ry="12" stroke-width="5"/>
        <g class="net-ball"><circle cx="160" cy="65" r="29"/><path d="M131 65H189M160 36V94M140 44Q170 65 140 86M180 44Q150 65 180 86"/></g>
      </g></svg>'''


def _scoreboard(data: dict) -> str:
    summary = _obj(data.get("summary"))
    wins = _obj(summary.get("seriesWins"))
    rounds = _obj(summary.get("challengeWins"))
    total = _n(summary.get("seriesCount"))
    return f'''<div class="sports-scoreboard" aria-label="Series wins in the supplied log">
      <p class="sports-kicker">First to four <span>Series ledger</span></p>
      <div class="sports-score"><div class="player-L"><span>L / Liam</span><strong>{_n(wins.get('L'))}</strong></div>
      <span class="score-divider" aria-hidden="true">:</span><div class="player-O"><span>O / Owen</span><strong>{_n(wins.get('O'))}</strong></div></div>
      <div class="sports-stack score-stripe" aria-hidden="true"><span class="fill-L" style="width:{_width(wins.get('L'), total)}%"></span><span class="fill-O" style="width:{_width(wins.get('O'), total)}%"></span></div>
      <p>{total} completed series · Round wins <strong class="player-L">L {_n(rounds.get('L'))}</strong> / <strong class="player-O">O {_n(rounds.get('O'))}</strong></p>
    </div>'''


def _metrics(data: dict) -> str:
    summary = _obj(data.get("summary"))
    streak = _obj(summary.get("currStreak"))
    best = _obj(_obj(data.get("timing")).get("bestOverall"))
    metrics = (
        ("series", _n(summary.get("seriesCount")), "Completed series", "First to four round wins"),
        ("rounds", _n(summary.get("challengeCount")), "Challenges played", "Rounds, not shot attempts"),
        ("streak", _n(streak.get("length")), "Series win streak", f"{_name(streak.get('player'))} · end of this log only"),
        ("best", _duration(best.get("seconds")), "Best listed 3 Point time", f"{_name(best.get('winner'))} · winner completion time"),
    )
    return '<div class="sports-metrics" aria-label="Entire supplied log">' + "".join(
        f'<div class="sports-metric"><span>{_e(label)}</span><strong id="sports-metric-{key}">{_e(value)}</strong><small>{_e(note)}</small></div>'
        for key, value, label, note in metrics
    ) + '</div>'


def _story(data: dict, base: str) -> str:
    selected = _default_series(data)
    if not selected:
        return '<p class="sports-empty">No completed series have been supplied. The rules and source readers remain available.</p>'
    summary = _obj(data.get("summary"))
    wins = _obj(summary.get("seriesWins"))
    intro = (f"Liam leads the supplied series ledger {_n(wins.get('L'))}–{_n(wins.get('O'))}. "
             if _n(wins.get("L")) > _n(wins.get("O")) else "Every completed series has a round-by-round record. ")
    description = ("A deciding seventh round brought this one to the wire." if selected.get("decider")
                   else "Trace a completed series from its opening round to the clinch.")
    return f'''<p class="sports-story">{_e(intro)}{_e(description)} Seven challenge types; one first-to-four finish. The notes, not a prediction, tell the story.</p>
      <a class="button primary" href="{_series_url(selected, base)}">{'Game 7' if selected.get('decider') else 'Series'} · {_e(selected.get('date'))} / session {_n(selected.get('session'))} <span aria-hidden="true">↗</span></a>'''


def _downloads(data: dict, depth: int) -> str:
    prefix = "../" * depth + "assets/data/"
    raw = (f'<a class="button ghost" href="{prefix}basketball-source.json" download>Raw source · JSON</a>'
           if data.get("sourceDownloadAvailable") is True else '')
    tables = ''.join(f'<li><a href="{prefix}basketball-{key}.csv" download>{key} · CSV</a></li>' for key in CSV_TABLES)
    return f'''<div class="sports-downloads"><nav class="toolbar" aria-label="Basketball evidence downloads">
      <a class="button primary" href="{prefix}basketball-analysis.json" download>Source &amp; analysis · JSON</a>
      <a class="button ghost" href="{prefix}basketball-rounds.csv" download>Round log · CSV</a>{raw}</nav>
      <details><summary>All 12 analysis tables · CSV downloads</summary><ul class="sports-download-list">{tables}</ul></details>
      <p class="sports-note">The analysis JSON includes preserved source games. Raw strings and timing statuses remain in the exports.</p></div>'''


def sports_body(data: dict, lead: str = "") -> str:
    """Return the Series Hub main (Sports-and-Entertainment/Series-Hub, depth 2); lead precedes the hub."""
    data = _obj(data)
    return f'''<main id="main-content" class="collection-page sports-page sports-hub">{lead}
      <header class="sports-hero"><div class="sports-hero-copy"><p class="sports-kicker">The sports notebook <span>01 / Court series</span></p>
      <h1>Meet at<br>the <em>court.</em></h1><p class="sports-deck">Small games. Long stories.<br>A record of the rounds, the rules, and what comes next.</p>
      {_story(data, 'Analytics/index.html')}</div>
      <div class="sports-art"><span class="sports-art-label">FIELD NOTES / NO. 01</span>{sports_net_svg()}
        <button class="button ghost" type="button" id="sports-net-boop" disabled>Boop the net <span aria-hidden="true">↗</span></button>
        <p class="sports-note">Original illustration · motion on request, not game footage.</p></div></header>
      {_metrics(data)}
      <section class="sports-section" aria-labelledby="sports-collections"><p class="sports-kicker">The playbook</p><h2 id="sports-collections">From house rules to hard numbers.</h2>
      <div class="sports-cards"><a class="sports-card sports-card-featured" href="Analytics/index.html"><span class="sports-kicker">01 / Court series</span>
      <h3>First to four.</h3><p>The Liam / Owen ledger. Challenge splits, next-round choices, and every recorded finish.</p>{_scoreboard(data)}<span class="sports-card-link">Explore the series <span aria-hidden="true">↗</span></span></a>
      <a class="sports-card" href="Rules/index.html"><span class="sports-kicker">02 / House rules</span><div class="sports-card-number" aria-hidden="true">4</div>
      <h3>The rules reader.</h3><p>How the series works. Read the authored rules and access source documents through the reader.</p><span class="sports-card-link">Open the playbook <span aria-hidden="true">↗</span></span></a>
      <a class="sports-card" href="Creator-Petition/index.html"><span class="sports-kicker">03 / Creator notebook</span><div class="sports-card-number" aria-hidden="true">↗</div>
      <h3>A creator pitch.</h3><p>An authored concept, separate from the results. Original diagrams; no borrowed highlights or branding.</p><span class="sports-card-link">Read the concept <span aria-hidden="true">↗</span></span></a></div></section>
      <aside class="sports-pending"><span class="sports-kicker">Next season / Pending</span><h2>Team basketball, when there is a record.</h2>
      <p>Future team and next-season basketball analysis is pending. No team results, fixtures, or projections are included in this two-player log.</p></aside>
      <section class="sports-section" aria-labelledby="sports-hub-evidence"><h2 id="sports-hub-evidence">Keep the evidence in view.</h2>
      <p>Descriptive results from the supplied log, not ability ratings. Dates and same-day sessions follow the source; no live clock or tracking is implied by the section badges.</p>{_downloads(data, 2)}</section>
    </main>'''


def _series_grid(data: dict) -> str:
    series = _rows(data.get("series"))
    rows = []
    for item in series:
        rounds = _rows(item.get("rounds"))
        chips = ''.join(f'<span class="round-chip fill-{_player(row.get("winner"))}" title="Round {_n(row.get("number"))}: {_e(_label(row.get("challenge")))}">{_e(_player(row.get("winner")))}</span>' for row in rounds[:7])
        chips += '<span class="round-chip unused" aria-hidden="true">·</span>' * max(0, 7 - len(rounds))
        wins = _obj(item.get("challengeWins"))
        rows.append(f'''<tr data-series-id="{_e(item.get('id'))}" data-winner="{_player(item.get('winner'))}">
          <th scope="row"><a class="sports-series-link" href="{_series_url(item)}" data-select-series="{_e(item.get('id'))}">{_e(item.get('date'))}<span>Session {_n(item.get('session'))} ↗</span></a></th>
          <td><span class="round-sequence" aria-label="Winner order {_e(item.get('order'))}">{chips}</span><code>{_e(item.get('order'))}</code></td>
          <td><strong class="player-{_player(item.get('winner'))}">{_e(_name(item.get('winner')))}</strong><br><span class="sports-tabular">L {_n(wins.get('L'))} – O {_n(wins.get('O'))}</span></td>
        </tr>''')
    return f'''<section class="sports-section" id="series-log" aria-labelledby="series-log-title"><p class="sports-kicker">01 / Every finish</p><h2 id="series-log-title">A season of small turning points.</h2>
      <p>Select a date to inspect that series. Each letter is a challenge winner, left to right; seven slots maximum. Dots after the clinch are not extra rounds.</p>{_legend()}
      <fieldset class="sports-controls" id="sports-log-controls" disabled><legend>Filter the series log only</legend>
      <label for="sports-log-winner">Series winner<select id="sports-log-winner"><option value="">All winners</option><option value="L">L / Liam</option><option value="O">O / Owen</option></select></label>
      <label for="sports-log-search">Date or winner-order code<input id="sports-log-search" type="search" maxlength="100" placeholder="2026-09-10 or OLLOLOL" autocomplete="off"></label>
      <button class="button ghost" id="sports-log-reset" type="button">Reset log</button></fieldset>
      <p class="sports-note">Filters affect this log only. All overview metrics and other charts always describe all {_n(_obj(data.get('summary')).get('seriesCount'))} series.</p>
      <p id="sports-log-status" role="status">Showing {len(series)} of {len(series)} series · log only.</p>
      <div class="sports-table-wrap" role="region" aria-label="Chronological series sequence" tabindex="0"><table id="sports-series-table">
      <caption>All supplied series in chronological order; same-day session numbers follow source entry order, not start times.</caption>
      <thead><tr><th scope="col">Date / session</th><th scope="col">Round winner sequence · L / O</th><th scope="col">Series result</th></tr></thead>
      <tbody>{''.join(rows) or '<tr><td colspan="3">No completed series supplied.</td></tr>'}</tbody></table></div></section>'''


def _challenge_chart(data: dict) -> str:
    challenges = {str(row.get("id")): row for row in _rows(data.get("challenges"))}
    bars = []
    for key, label in CHALLENGES:
        row = challenges.get(key, {})
        count = _n(row.get("winRateDenominator", row.get("played")))
        wins = _obj(row.get("wins"))
        bars.append(f'''<div class="sports-challenge" data-challenge="{key}"><div class="sports-bar-heading"><h3>{_e(row.get('label', label))}</h3><span>{count} played rounds</span></div>
          <div class="sports-stack" aria-hidden="true"><span class="fill-L" style="width:{_width(wins.get('L'), count)}%"></span><span class="fill-O" style="width:{_width(wins.get('O'), count)}%"></span></div>
          <div class="sports-bar-values"><span class="player-L">L {_n(wins.get('L'))}/{count} · {_pct(wins.get('L'), count)}</span><span class="player-O">O {_n(wins.get('O'))}/{count} · {_pct(wins.get('O'), count)}</span></div></div>''')
    return f'''<section class="sports-section" aria-labelledby="challenge-title"><p class="sports-kicker">02 / The challenge split</p><h2 id="challenge-title">Seven ways to win a round.</h2>
      <p>Observed challenge wins ÷ rounds played in that challenge. These percentages are not ability estimates. Repeated challenges, if present, count each played round.</p>{_legend()}
      <figure class="sports-bars" id="sports-challenge-chart">{''.join(bars)}<figcaption>Every bar has its own played-round denominator; an unplayed challenge has no percentage.</figcaption></figure></section>'''


def _matrix(data: dict) -> str:
    matrix = _obj(data.get("transitionMatrix"))
    counts = matrix.get("counts", [])
    order = matrix.get("challengeOrder", [key for key, _ in CHALLENGES])
    order = order if isinstance(order, list) and len(order) == 7 else [key for key, _ in CHALLENGES]
    safe = [[_n(counts[i][j]) if isinstance(counts, list) and i < len(counts) and isinstance(counts[i], list) and j < len(counts[i]) else 0 for j in range(7)] for i in range(7)]
    maximum = max((max(row) for row in safe), default=0)
    rows = ''.join('<tr><th scope="row">' + _e(_label(order[i])) + '</th>' + ''.join(
        f'<td style="background-color:rgb(247 171 101 / {0.06 + 0.40 * count / maximum if maximum else 0.06:.3f})">{count}</td>' for count in row) + '</tr>' for i, row in enumerate(safe))
    return f'''<div class="sports-table-wrap" role="region" aria-label="Challenge transition heatmap" tabindex="0"><table class="sports-matrix" id="sports-transition-matrix">
      <caption id="sports-matrix-caption">All inferred pickers · {sum(map(sum, safe))} within-series transitions. Rows = previous challenge; columns = next challenge. Cells are counts, not rates.</caption>
      <thead><tr><th scope="col">Previous ↓ / Next →</th>{''.join(f'<th scope="col">{_e(_label(key))}</th>' for key in order)}</tr></thead><tbody>{rows}</tbody></table></div>'''


def _conditional_rows(data: dict) -> str:
    return ''.join(f'''<tr data-picker="{_player(row.get('player'))}"><th scope="row">{_e(_name(row.get('player')))} / {_e(_label(row.get('nextChallenge')))}</th>
      <td>{_n(row.get('countPicks'))}/{_n(row.get('pickerTotal'))} · {_pct(row.get('countPicks'), row.get('pickerTotal'))}</td>
      <td>{_n(row.get('countWins'))}/{_n(row.get('countPicks'))} · {_pct(row.get('countWins'), row.get('countPicks'))}</td>
      <td>{_n(row.get('countLosses'))}</td></tr>''' for row in _rows(data.get('conditionalNextChallenge'))) or '<tr><td colspan="4">No inferred choices supplied.</td></tr>'


def _picker_chart(data: dict) -> str:
    transitions = _obj(_obj(data.get("summary")).get("transitions"))
    total, held, switched = (_n(transitions.get(key)) for key in ("total", "retentions", "switches"))
    pickers = {str(row.get("player")): row for row in _rows(data.get("byPicker"))}
    bars = []
    for player in ("L", "O"):
        row = pickers.get(player, {})
        denominator, holds = _n(row.get("denominator")), _n(row.get("holds"))
        bars.append(f'''<div class="sports-picker-card"><h3 class="player-{player}">{player} / {_NAMES[player]}</h3><p class="sports-picker-number">{holds}<span> / {denominator} holds</span></p>
          <div class="sports-stack" aria-hidden="true"><span class="fill-{player}" style="width:{_width(holds, denominator)}%"></span><span class="fill-switch" style="width:{_width(row.get('losses'), denominator)}%"></span></div>
          <p>{_pct(holds, denominator)} observed hold rate · {_n(row.get('losses'))} next-round losses.</p></div>''')
    return f'''<section class="sports-section" id="picker-patterns" aria-labelledby="picker-title"><p class="sports-kicker">03 / Who picks next?</p><h2 id="picker-title">A choice follows a win. Not a guarantee.</h2>
      <p><strong>Inferred picker / next-round winner.</strong> Under winner-picks-next, the previous winner is the inferred picker, not an independently recorded decision-maker. Round one has no recorded picker; there is no next choice after the clinch.</p>
      <div class="sports-picker-grid">{''.join(bars)}</div><figure class="sports-composition"><h3>All within-series transitions</h3>
      <div class="sports-stack" aria-hidden="true"><span class="fill-hold" style="width:{_width(held, total)}%"></span><span class="fill-switch" style="width:{_width(switched, total)}%"></span></div>
      <figcaption><strong>{held}/{total} holds · {_pct(held, total)}</strong> / <strong>{switched}/{total} switches · {_pct(switched, total)}</strong>. A hold repeats the winner; a switch changes the winner. No cross-series transitions.</figcaption></figure>
      <p class="sports-note">Small, selected samples; no causal picking advantage, best-choice recommendation, or implied 50% random baseline. The two player hold rates condition on different inferred pickers.</p>
      <h3>Which challenge followed which?</h3><fieldset class="sports-controls" id="sports-picker-controls" disabled><legend>Filter the matrix and next-choice table only</legend>
      <label for="sports-picker-filter">Inferred picker<select id="sports-picker-filter"><option value="">All inferred pickers</option><option value="L">L / Liam</option><option value="O">O / Owen</option></select></label></fieldset>
      <p id="sports-picker-status" role="status">Matrix and choice table: all inferred pickers. Hold cards above always show the full log.</p>{_matrix(data)}
      <details class="sports-choice-details" open><summary>Next-choice frequency and observed holds · keep the denominators separate</summary>
      <div class="sports-table-wrap" role="region" aria-label="Conditional next challenge choices" tabindex="0"><table id="sports-choice-table">
      <caption>Choice share = choices / all that player's inferred picks. Hold rate = next-round wins / those choices. A dash means an undefined rate, not zero.</caption>
      <thead><tr><th scope="col">Inferred picker / next challenge</th><th scope="col">Choice share · count/n</th><th scope="col">Observed holds · wins/n</th><th scope="col">Losses</th></tr></thead><tbody>{_conditional_rows(data)}</tbody></table></div></details></section>'''


def _timing_chart(data: dict) -> str:
    timing = _obj(data.get("timing"))
    entries = _rows(timing.get("entries"))
    valid = [row for row in entries if row.get("status") == "valid" and type(row.get("seconds")) in (int, float) and math.isfinite(row["seconds"]) and row["seconds"] >= 0]
    maximum = max(60, math.ceil(max((_n(row.get("seconds")) for row in valid), default=0) / 60) * 60)
    best = _obj(timing.get("bestOverall"))
    points, ticks, table_rows, missing = [], [], [], []
    for index, row in enumerate(entries):
        x = 65 + index * 760 / max(1, len(entries) - 1)
        ticks.append(f'<text x="{x:.2f}" y="291" text-anchor="middle">{index + 1}</text>')
        context = f"{row.get('date', '')} / S{_n(row.get('session'))}"
        status = row.get("status", "missing")
        if row in valid:
            y = 250 - 205 * _n(row.get("seconds")) / maximum
            player = _player(row.get("winner"))
            is_best = row.get("seriesId") == best.get("seriesId") and row.get("round") == best.get("round")
            shape = (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6"/>' if player == 'L' else f'<rect x="{x - 6:.2f}" y="{y - 6:.2f}" width="12" height="12"/>')
            points.append(f'<g class="timing-point player-{player}"><title>{_e(context)} · {_e(_name(player))} · {_n(row.get("seconds"))} seconds</title>{shape}</g>')
            if is_best:
                points.append(f'<circle class="sports-best-ring" cx="{x:.2f}" cy="{y:.2f}" r="12"/><text class="sports-best-label" x="{x:.2f}" y="{y - 22:.2f}" text-anchor="middle">Best {_e(_duration(row.get("seconds")))}</text>')
        else:
            text = {"pending": "TBD · pending", "not-recorded": "N/A · not recorded", "missing": "Time absent · played", "not-played": "3 Point not played"}.get(str(status), "Time unavailable")
            missing.append(f'<li><strong>{_e(text)}</strong><span>{_e(context)} · entry {index + 1}</span></li>')
        table_rows.append(f'<tr><th scope="row">{index + 1} · {_e(context)}</th><td>{_e(_name(row.get("winner"))) if row.get("played") else "—"}</td><td>{_e(row.get("raw")) or "Absent"}</td><td>{_n(row.get("seconds")) if row in valid else "—"}</td><td>{_e(status)}</td><td>{_e(row.get("note")) or "—"}</td></tr>')
    for step in range(6):
        seconds = maximum * step / 5
        y = 250 - 205 * step / 5
        ticks.append(f'<line class="chart-grid" x1="55" x2="847" y1="{y:.2f}" y2="{y:.2f}"/><text x="44" y="{y + 4:.2f}" text-anchor="end">{seconds:g}</text>')
    by_player = _obj(timing.get("bestByPlayer"))
    bests = ' / '.join(f'{_NAMES[player]}: {_duration(_obj(by_player.get(player)).get("seconds"))}' for player in ('L', 'O'))
    courts = [_e(f"{row.get('date')} / S{_n(row.get('session'))}: {row.get('court') or 'court unrecorded'}; rim {row.get('rimHeightInches') if row.get('rimHeightInches') is not None else 'unrecorded'} inches") for row in _rows(data.get('series')) if row.get('court') is not None or row.get('rimHeightInches') is not None]
    return f'''<section class="sports-section" aria-labelledby="timing-title"><p class="sports-kicker">04 / Against the clock</p><h2 id="timing-title">Only the times that were written down.</h2>
      <p><strong>{_n(timing.get('validCount'))} recorded times / {_n(timing.get('played'))} played 3 Point rounds.</strong> Listed winner completion times, in seconds; lower is faster. Not shot accuracy. Best listed by player: {_e(bests)}.</p>{_legend()}
    <figure id="sports-timing-chart"><div class="sports-chart-wrap" role="region" aria-label="Scrollable timing plot" tabindex="0"><svg viewBox="0 0 900 325" class="sports-chart" role="img" aria-labelledby="timing-svg-title timing-svg-desc">
      <title id="timing-svg-title">Chronological 3 Point winner completion times</title><desc id="timing-svg-desc">{len(valid)} recorded durations. Y axis: seconds. X axis: chronological entry number, evenly spaced, not elapsed time. Liam circles; Owen squares. Missing and unplayed entries are not plotted. Full values follow in the timing table.</desc>
    <text x="55" y="20">Seconds</text>{''.join(ticks)}{''.join(points)}<text x="450" y="318" text-anchor="middle">Chronological entry / same-day source order →</text></svg></div>
    <figcaption>No connecting lines; no invented zeroes. X-axis entry numbers map to dates and sessions in the table. No measured session start times. On narrow screens, scroll the plot horizontally or read the timing table.</figcaption></figure>
      <aside class="sports-missing"><h3>Off the plot, still in the record.</h3><ul>{''.join(missing) or '<li>No missing or unplayed timing entries.</li>'}</ul></aside>
      <p class="sports-note">Rebounding assistance is unknown / not standardized; attempts and losing-player times are unavailable. Court metadata is never carried forward. Recorded metadata: {'; '.join(courts) or 'none'}. All other courts and rim heights are unrecorded.</p>
      <details><summary>Timing evidence · all recorded, missing and unplayed entries</summary><div class="sports-table-wrap" role="region" aria-label="3 Point timing source table" tabindex="0"><table id="sports-timing-table">
      <caption>Raw time, numeric seconds and status are separate. TBD, N/A and absent played times are missing durations; not-played means the challenge did not occur.</caption>
      <thead><tr><th scope="col">Entry / date / session</th><th scope="col">Winner</th><th scope="col">Raw time</th><th scope="col">Seconds</th><th scope="col">Status</th><th scope="col">Note</th></tr></thead><tbody>{''.join(table_rows) or '<tr><td colspan="6">No timing entries supplied.</td></tr>'}</tbody></table></div></details></section>'''


def _trajectory(item: dict) -> str:
    count = max(1, _n(item.get("roundCount")))
    points = _rows(item.get("trajectory"))
    grid, lines, marks = [], [], []
    for score in range(5):
        y = 246 - score * 48
        grid.append(f'<line class="chart-grid" x1="55" x2="835" y1="{y}" y2="{y}"/><text x="40" y="{y + 4}" text-anchor="end">{score}</text>')
    for number in range(_n(item.get("roundCount")) + 1):
        grid.append(f'<text x="{55 + number * 780 / count:.2f}" y="273" text-anchor="middle">{number}</text>')
    for player in ('L', 'O'):
        coords = ' '.join(f'{55 + _n(point.get("round")) * 780 / count:.2f},{246 - min(4, _n(point.get(player))) * 48}' for point in points)
        lines.append(f'<polyline class="trajectory-line player-{player}" points="{coords}"/>')
        for point in points:
            x, y = 55 + _n(point.get('round')) * 780 / count, 246 - min(4, _n(point.get(player))) * 48
            marks.append(f'<circle class="trajectory-dot player-L" cx="{x:.2f}" cy="{y}" r="5"/>' if player == 'L' else f'<rect class="trajectory-dot player-O" x="{x - 5:.2f}" y="{y - 5}" width="10" height="10"/>')
        marker = 835 if item else 55
        return f'''<div class="sports-chart-wrap" role="region" aria-label="Scrollable selected-series trajectory" tabindex="0"><svg viewBox="0 0 900 315" class="sports-chart" id="sports-trajectory" role="img" aria-labelledby="trajectory-title trajectory-desc">
      <title id="trajectory-title">Selected series cumulative round wins</title><desc id="trajectory-desc">{_e(item.get('date'))}, session {_n(item.get('session'))}. Round zero through {_n(item.get('roundCount'))}. L / Liam circles and solid line; O / Owen squares and dashed line. The series ends at the first four wins.</desc>
      <text x="55" y="25">Round wins / first to 4</text>{''.join(grid)}<g id="sports-trajectory-lines">{''.join(lines + marks)}</g>
            <line id="sports-round-marker" class="round-marker" x1="{marker}" x2="{marker}" y1="45" y2="253"/><text x="450" y="305" text-anchor="middle">Round →</text></svg></div>'''


def _round_details(item: dict) -> str:
    rows = []
    for row in _rows(item.get('rounds')):
        number = _n(row.get('number'))
        wins = _obj(row.get('cumulativeWins'))
        time = _obj(row.get('time'))
        picker = (f"{_name(row.get('inferredPicker'))} (inferred from previous winner)" if row.get('inferredPicker') else "Unrecorded · opening round")
        time_text = (f"{time.get('raw') if time.get('raw') is not None else 'Absent'} · {time.get('status', 'missing')}" if row.get('challenge') == 'three-point' else 'Not applicable')
        rows.append(f'''<li id="sports-round-{number}"{' aria-current="step"' if number == _n(item.get('roundCount')) else ''}>
          <span class="sports-round-number">{number:02}</span><div><h3>{_e(_label(row.get('challenge')))} <span class="player-{_player(row.get('winner'))}">{_e(_player(row.get('winner')))} / {_e(_name(row.get('winner')))} wins</span></h3>
          <p>Series score: L {_n(wins.get('L'))} – O {_n(wins.get('O'))}. Picker: {_e(picker)}.</p>
          <p>Raw score: <strong>{_e(row.get('scoreRaw')) or 'Not recorded'}</strong> · Raw time: <strong>{_e(time_text)}</strong></p>
          <p>Note: {_e(row.get('note')) or 'None recorded'}</p></div></li>''')
    return ''.join(rows) or '<li>No rounds supplied.</li>'


def _play_by_play(data: dict) -> str:
    selected = _default_series(data)
    series = _rows(data.get('series'))
    wins = _obj(selected.get('challengeWins'))
    count = _n(selected.get('roundCount'))
    options = ''.join(f'<option value="{_e(row.get("id"))}"{" selected" if row is selected else ""}>{_e(row.get("date"))} / session {_n(row.get("session"))} · {_e(row.get("order"))}</option>' for row in series)
    return f'''<section class="sports-section sports-replay" id="play-by-play" tabindex="-1" aria-labelledby="play-title"><p class="sports-kicker">05 / Inside one series</p><h2 id="play-title">Every round leaves a mark.</h2>
      <p>A source-log walkthrough, not video or live tracking. The scoreboard here changes with the selected round; global metrics above never change.</p>
      <fieldset class="sports-controls" id="sports-series-controls" disabled><legend>Choose a completed series</legend><label for="sports-series-select">Series<select id="sports-series-select">{options or '<option>No series available</option>'}</select></label></fieldset>
      <h3 id="sports-selected-title">{_e(selected.get('date')) or 'No series supplied'} / session {_n(selected.get('session'))}</h3>
      <p id="sports-series-note" class="sports-note">Series note: {_e(selected.get('note')) or 'None recorded'}</p>
      <p class="sports-local-score" id="sports-round-score" role="status" aria-live="polite" aria-atomic="true">Round {count} of {count} · L {_n(wins.get('L'))} – O {_n(wins.get('O'))}{' · Final' if selected else ''}</p>
    {_legend()}{_trajectory(selected)}<p class="sports-note">On narrow screens, scroll the plot horizontally. The source log below gives every cumulative score in text.</p>
      <fieldset class="sports-controls sports-scrubber" id="sports-round-controls" disabled><legend>Move through recorded rounds</legend>
      <button class="button ghost" id="sports-round-prev" type="button">Previous round</button><label for="sports-round-range">Recorded round<input id="sports-round-range" type="range" min="0" max="{count}" value="{count}" step="1" aria-valuetext="Round {count} of {count}"></label>
      <button class="button ghost" id="sports-round-next" type="button" disabled>Next round</button></fieldset>
      <p id="sports-round-context">{'Final recorded round; first to four ends the series.' if selected else 'No completed series to inspect.'}</p>
      <h3>What happened · source round log</h3><p class="sports-note">All rounds stay readable while scrubbing. The selected round is outlined. Raw HORSE / Bump scores have unconfirmed orientation; they are not interpreted as points or letters.</p>
      <ol class="sports-round-list" id="sports-round-list">{_round_details(selected)}</ol></section>'''


def basketball_body(data: dict, lead: str = "") -> str:
    """Return the dashboard main at Sports-and-Entertainment/Series-Hub/Analytics (depth 3)."""
    data = _obj(data)
    source = _obj(data.get('source'))
    caveats = data.get('caveats', [])
    caveats = caveats if isinstance(caveats, list) else []
    return f'''<main id="main-content" class="collection-page sports-page basketball-page" data-sports-dashboard>{lead}
      <nav class="sports-breadcrumbs" aria-label="Sports navigation"><a href="../index.html">Series Hub</a><span aria-hidden="true">/</span><span aria-current="page">Basketball series</span><a href="../Rules/index.html">Rules reader ↗</a><a href="../Creator-Petition/index.html">Creator pitch ↗</a></nav>
      <header class="sports-hero"><div class="sports-hero-copy"><p class="sports-kicker">01 / Court series <span>Completed records</span></p>
      <h1>First to <em>four.</em><br>Every round counts.</h1><p class="sports-deck">Liam &amp; Owen / the court notebook</p>{_story(data, 'index.html')}</div>{_scoreboard(data)}</header>
      <p class="sports-scope">Entire supplied log · {_e(_obj(data.get('summary')).get('firstDate')) or 'No start date'} → {_e(_obj(data.get('summary')).get('lastDate')) or 'No end date'}. Descriptive, not predictive.</p>{_metrics(data)}
      <nav class="sports-jump-links" aria-label="Dashboard sections"><a href="#series-log">Series sequence</a><a href="#challenge-title">Challenge splits</a><a href="#picker-patterns">Picker patterns</a><a href="#timing-title">3 Point times</a><a href="#play-by-play">Round walkthrough</a><a href="#sports-sources">Sources</a></nav>
      <p class="sports-note" id="sports-data-status" role="status">Static charts and complete evidence are shown. Interactive controls require JavaScript and the local analysis data.</p>
      {_series_grid(data)}{_challenge_chart(data)}{_picker_chart(data)}{_timing_chart(data)}{_play_by_play(data)}
      <section class="sports-section sports-method" id="sports-sources" aria-labelledby="sports-sources-title"><p class="sports-kicker">The evidence desk</p><h2 id="sports-sources-title">The record, with its limits attached.</h2>
      <p>Source heading: {_e(source.get('sourceTitle')) or 'Not supplied'}. {_e(_obj(data.get('provenance')).get('source'))}</p><p>{_e(source.get('chronology'))}</p>
      <ul>{''.join(f'<li>{_e(note)}</li>' for note in caveats) or '<li>No completed-series analysis supplied. No results or rates are inferred.</li>'}</ul>
      <p><a href="../Rules/index.html">Read the rules and source documents</a> · <a href="../Creator-Petition/index.html">Read the creator pitch</a>. No mercy totals, dinner obligations, or future results are inferred.</p>{_downloads(data, 3)}</section>
      <noscript><p class="sports-note">JavaScript is off. All series, challenge splits, transition counts, timing evidence and the default series walkthrough remain readable. Download the full source-preserving JSON for any other series.</p></noscript>
    </main>'''