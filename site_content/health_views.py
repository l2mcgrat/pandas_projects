"""Sleep and diet dashboards for Gaming & Performance / Health: static SVG, escaped text, no scripts.

Pass load_health(root)[key]; diet_body also takes load_athletics(root) to show which
training sessions sat behind each day's expenditure. The dream reading is presented as
a playful lexicon count over the owner's own journal, never as psychology.
"""

from __future__ import annotations

import json

from .athletics import YARD
from .athletics_views import _chart, _day, _downloads, _e, _hero, _metrics, _num, _section, _table, _ticks, _update_notes
from .health import CALORIES_PER_POUND, DAILY_TARGET_DEFICIT, HIGH_NEAT_NOTE, OCTOBER_BMR

__all__ = ["diet_body", "sleep_body"]


def _signed(value: int | float) -> str:
    return f"{value:+,.0f}"


def _dream_card(night: dict, dream: dict) -> str:
    chips = []
    if dream["emotion"] != "Unclassified":
        chips.append(f'<span class="dream-chip dream-emotion">{_e(dream["emotion"])}'
                     + (f' · {_e(dream["subemotion"])}' if dream["subemotion"] else "") + "</span>")
    compound = dream["polarity"]["compound"]
    tone = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
    chips.append(f'<span class="dream-chip dream-{tone}">VADER {compound:+.2f}</span>')
    chips += [f'<span class="dream-chip">{_e(found["motif"])}</span>' for found in dream["motifs"]]
    return (f'<article class="dream-card"><header><h3>{_e(_day(night["date"]))} · dream {dream["number"]}</h3>'
            f'<span class="dream-hours">{night["hours"]:g} h slept</span></header>'
            f'<p class="dream-text" data-wb-admin-only hidden>{_e(dream["text"])}</p>'
            f'<p class="sports-note" data-wb-admin-locked-msg>🔒 Dream description hidden — Unlock Admin to view.</p>'
            f'<p class="dream-chips">{"".join(chips)}</p></article>')


def sleep_body(data: dict, lead: str = "") -> str:
    nights, summary, motifs = data["nights"], data["summary"], data["motifs"]
    deck = (f"{summary['nights']} nights since {_day(summary['firstDate'])}: duration, dream recall, and a "
            "pattern reading of the dream journal itself.")
    actions = ('<a class="button primary" href="#sleep-dreams-title">Read the dream journal</a>'
               '<a class="button ghost" href="#sleep-reading-title">The motif reading</a>'
               '<a class="button ghost" href="#sleep-update">Add a night ↓</a>')
    art = ('<div class="athletics-split-card" aria-hidden="true">'
           f'<span class="split-Chest"><strong>{summary["averageHours"]:g}</strong>avg hours</span>'
           f'<span class="split-Back"><strong>{summary["dreams"]}</strong>dreams logged</span>'
           f'<span class="split-Shoulders"><strong>{summary["nightsWithDreams"]}/{summary["nights"]}</strong>nights recalled</span></div>')
    metrics = _metrics([
        ("Nights logged", str(summary["nights"]), f"{_day(summary['firstDate'])} → {_day(summary['lastDate'])}"),
        ("Average sleep", f"{summary['averageHours']:g} h", f"Shortest {summary['shortest']:g} h · longest {summary['longest']:g} h"),
        ("Dreams written down", str(summary["dreams"]), f"Across {summary['nightsWithDreams']} nights"),
        ("Recall vs duration", f"{summary['averageHoursWithDreams']:g} h", f"vs {summary['averageHoursWithout']:g} h on nights with none written"),
    ])
    # Duration bars, coloured by whether a dream was written down.
    high = max(12, int(summary["longest"]) + 1)
    step = 760 / len(nights)
    y = lambda v: 290 - v / high * 240
    bars = []
    for index, night in enumerate(nights):
        bx = 90 + index * step
        label = f'{_e(_day(night["date"]))} · {night["hours"]:g} h · ' + (f'{len(night["dreams"])} dream(s)' if night["recall"] else "no dreams written")
        bars.append(f'<rect class="athletics-bar {"series-0" if night["recall"] else "series-3"}" x="{bx + step * .18:.1f}" y="{y(night["hours"]):.1f}" '
                    f'width="{step * .64:.1f}" height="{290 - y(night["hours"]):.1f}"><title>{label}</title></rect>'
                    f'<text x="{bx + step / 2:.1f}" y="{y(night["hours"]) - 8:.1f}" text-anchor="middle">{night["hours"]:g} h</text>'
                    f'<text x="{bx + step / 2:.1f}" y="314" text-anchor="middle">{_e(_day(night["date"]))}</text>')
    avg = y(summary["averageHours"])
    grid = "".join(f'<line class="chart-grid" x1="70" x2="870" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                   f'<text x="60" y="{y(v) + 4:.1f}" text-anchor="end">{v} h</text>' for v in range(0, high + 1, 3))
    mean_line = (f'<line class="sleep-mean" x1="90" x2="850" y1="{avg:.1f}" y2="{avg:.1f}"/>'
                 f'<text class="athletics-label series-1" x="856" y="{avg + 4:.1f}">avg {summary["averageHours"]:g} h</text>')
    chart = _chart("sleep-hours", "Hours slept per night (h)",
                   "Bars show hours slept (h); brighter bars are nights with at least one dream written down. "
                   "The dashed line is the mean. The table below lists every value.", grid + "".join(bars) + mean_line)
    legend = ('<p class="sports-legend"><span class="series-0">■ Dream written down (h)</span>'
              '<span class="series-3">■ No dream written (h)</span><span class="series-1">┄ Mean duration (h)</span></p>')
    sleep_bi = [
        {
            "date": n["date"],
            "hours": n["hours"],
            "recall": n["recall"],
            "dreamCount": len(n["dreams"]),
            "motifs": sorted({m["motif"] for d in n["dreams"] for m in d["motifs"]}),
        }
        for n in nights
    ]
    rows = [[_day(n["date"]), f'{n["hours"]:g} h', len(n["dreams"]) or ("—" if not n.get("noDreamsWritten") else "0 (noted)"),
             " · ".join(sorted({m["motif"] for d in n["dreams"] for m in d["motifs"]})) or "—"] for n in nights]
    cards = "".join(_dream_card(night, dream) for night in nights for dream in night["dreams"])
    motif_rows = [[m["motif"], m["count"], len(m["nights"]), ", ".join(m["cues"][:8]) + ("…" if len(m["cues"]) > 8 else "")] for m in motifs]
    readings = "".join(f'<article class="dream-motif"><h3>{_e(m["motif"])}</h3>'
                       f'<p class="dream-motif-count">{m["count"]} matches over {len(m["nights"])} nights</p>'
                       f'<p>{_e(m["note"])}</p></article>' for m in motifs)
    recall_note = (f"The three dreamless entries (Oct 15–17) averaged {summary['averageHoursWithout']:g} h against "
                   f"{summary['averageHoursWithDreams']:g} h when dreams were written; the two longest nights "
                   f"({summary['longest']:g} h) both produced multi-dream entries. With {summary['nights']} nights, "
                   "that is a curiosity, not a finding.")
    return f'''<main id="main-content" class="collection-page sports-page athletics-page health-page">{lead}
      {_hero("Health / Sleep", "Dream journal", "Sleep in hours,<br>dreams in <em>motifs.</em>", deck, actions, art)}
      <p class="sports-scope">Every logged night, as written. A personal journal read for patterns — not psychoanalysis, therapy or any claim about mental health.</p>{metrics}
      {_section("01", "Duration", "Hours slept, night by night.", "sleep-hours-title", f'<div class="bi-sleep-host" data-bi-sleep="{_e(json.dumps(sleep_bi, separators=(",", ":")))}">' + legend + chart + '</div>')}
      {_section("02", "The journal", "Every dream, as written (Admin-protected).", "sleep-dreams-title",
                '<div class="admin-gate-banner" data-wb-admin-locked-msg>'
                '<div><strong>🔒 Dream descriptions &amp; personal journal entries are Admin-protected</strong>'
                '<p>Sleep duration and aggregate motif counts are public; full written dream descriptions require Admin unlock (stays unlocked for 30 minutes across the site).</p></div>'
                '<button class="button primary" type="button" data-wb-auth-open>🔐 Unlock Admin (30m)</button></div>'
                '<p data-wb-admin-only hidden>Typos and all: the text is untouched. Chips show the feelings-lexicon reading (same lexicon as the lyrics explorer), a VADER polarity score and the motifs matched.</p>'
                + f'<div class="dream-cards" data-wb-admin-only hidden>{cards}</div>'
                + _table("Nights.", ["Date", "Slept", "Dreams", "Motifs matched"], rows, "sleep-table"))}
      {_section("03", "Reading the dreams", "What keeps showing up.", "sleep-reading-title",
                '<p class="sports-note"><strong>For fun, not Freud:</strong> motifs are counted with a fixed word list over the journal, and the notes below are classic '
                'dream-folklore readings of each motif. None of it is clinical, diagnostic or validated. The journal author finds it entertaining; so should you.</p>'
                + f'<div class="dream-motifs">{readings}</div>'
                + _table("Motif matches.", ["Motif", "Matches", "Nights", "Words that matched"], motif_rows)
                + f'<p class="sports-note">{_e(recall_note)}</p>')}
      <section class="sports-section sports-method" aria-labelledby="sleep-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="sleep-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}, read line by line; any unreadable line stops the build.</li>
      <li>Each paragraph under a date is one dream; "No dreams recorded" is kept as a deliberate entry, not a gap.</li>
      <li>Emotion chips reuse the site's custom feelings lexicon and VADER polarity; dreams with no cue stay Unclassified rather than being guessed.</li>
      <li>Motifs count exact word-form matches from a fixed list (shown in the table), so a motif the list misses is simply not counted.</li></ul>
      {_downloads(3, [("health-sleep.json", "Sleep log · JSON"), ("health-sleep-nights.csv", "Nights · CSV"), ("health-sleep-dreams.csv", "Dreams · CSV")])}</section>
      {_update_notes("sleep", data, '<li>Add a date line like <code>10/19/2026</code>, a duration line like <code>7.5hrs</code>, then one paragraph '
                     'per dream (or <code>No dreams recorded</code>).</li>')}
    </main>'''


def _training(athletics: dict) -> dict[str, list[str]]:
    by_date: dict[str, list[str]] = {}
    for item in athletics["swimming"]["sessions"]:
        by_date.setdefault(item["date"], []).append(f'Swim {_num(item["distance"])} {"yd" if item["unit"] == "y" else "m"}')
    for item in athletics["running"]["sessions"]:
        by_date.setdefault(item["date"], []).append(f'Intervals × {item["count"]}')
    for item in athletics["tempo"]["runs"]:
        by_date.setdefault(item["date"], []).append(f'Tempo {item["distanceKm"]:g} km')
    for item in athletics["weightlifting"]["sessions"]:
        by_date.setdefault(item["date"], []).append(f'Lift · {item["splitRaw"]}')
    return by_date


def diet_body(data: dict, athletics: dict, lead: str = "") -> str:
    days, summary, weeks = data["days"], data["summary"], data["weeks"]
    training = _training(athletics)
    deck = (f"{summary['days']} tracked days since {_day(summary['firstDate'])}: an estimated "
            f"{_num(summary['totalDeficit'])} kcal deficit, about {summary['estimatedPounds']:g} lb.")
    actions = ('<a class="button primary" href="#diet-balance-title">The balance chart</a>'
               '<a class="button ghost" href="#diet-log-title">Every meal</a>'
               '<a class="button ghost" href="#diet-update">Add a day ↓</a>')
    art = ('<div class="athletics-split-card" aria-hidden="true">'
           f'<span class="split-Chest"><strong>{_num(summary["averageExpenditure"])}</strong>avg out</span>'
           f'<span class="split-Back"><strong>{_num(summary["averageConsumption"])}</strong>avg in</span>'
           f'<span class="split-Shoulders"><strong>{_signed(-summary["averageDeficit"])}</strong>avg net</span></div>')
    metrics = _metrics([
        ("Days tracked", str(summary["days"]), f"{_day(summary['firstDate'])} → {_day(summary['lastDate'])}"),
        ("Average deficit", f"{_num(summary['averageDeficit'])} kcal", f"{summary['daysOnTarget']} of {summary['days']} days at the {_num(DAILY_TARGET_DEFICIT)} kcal target"),
        ("Estimated loss", f"{summary['estimatedPounds']:g} lb", f"{_num(summary['totalDeficit'])} kcal ÷ {_num(CALORIES_PER_POUND)}"),
        ("Burn above BMR", f"{_num(summary['averageExpenditure'] - OCTOBER_BMR)} kcal", "Training plus high NEAT, daily average"),
    ])
    # Left axis: expenditure/consumption in kcal. Right axis: the daily deficit.
    left_ticks = _ticks(0, max(d["expenditure"] for d in days))
    deficits = [d["deficit"] for d in days] + [DAILY_TARGET_DEFICIT, 0]
    right_ticks = _ticks(min(deficits), max(deficits))
    top, bottom, right = 40, 290, 810
    y = lambda v: bottom - (v - left_ticks[0]) / (left_ticks[-1] - left_ticks[0]) * (bottom - top)
    yr = lambda v: bottom - (v - right_ticks[0]) / (right_ticks[-1] - right_ticks[0]) * (bottom - top)
    x = lambda i: 110 + i * (right - 130) / (len(days) - 1)
    parts = [f'<line class="chart-grid" x1="70" x2="{right}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
             f'<text x="60" y="{y(t) + 4:.1f}" text-anchor="end">{_num(t)}</text>' for t in left_ticks]
    parts += [f'<text class="axis-deficit" x="{right + 8}" y="{yr(t) + 4:.1f}">{_signed(t)}</text>' for t in right_ticks]
    parts.append(f'<text x="60" y="24" text-anchor="end">kcal</text><text class="axis-deficit" x="{right + 8}" y="24">deficit</text>')
    width = min(26, (right - 130) / len(days) * .5)
    for i, d in enumerate(days):
        base, height = (yr(d["deficit"]), yr(0) - yr(d["deficit"])) if d["deficit"] >= 0 else (yr(0), yr(d["deficit"]) - yr(0))
        parts.append(f'<rect class="diet-deficit{"" if d["deficit"] >= 0 else " is-gain"}" x="{x(i) - width / 2:.1f}" y="{base:.1f}" '
                     f'width="{width:.1f}" height="{height:.1f}"><title>{_e(_day(d["date"]))} · {_signed(-d["deficit"])} kcal net</title></rect>')
        parts.append(f'<text x="{x(i):.1f}" y="314" text-anchor="middle">{_e(_day(d["date"]))}</text>')
    parts.append(f'<line class="diet-zero" x1="90" x2="{right}" y1="{yr(0):.1f}" y2="{yr(0):.1f}"/>')
    parts.append(f'<line class="diet-target" x1="90" x2="{right - 60}" y1="{yr(DAILY_TARGET_DEFICIT):.1f}" y2="{yr(DAILY_TARGET_DEFICIT):.1f}"/>'
                 f'<text class="athletics-label diet-target-label" x="856" y="{yr(DAILY_TARGET_DEFICIT) + 4:.1f}">target</text>')
    for key, cls in (("expenditure", "diet-out"), ("consumption", "diet-in")):
        points = " ".join(f"{x(i):.1f},{y(d[key]):.1f}" for i, d in enumerate(days))
        dots = "".join(f'<circle class="athletics-dot" cx="{x(i):.1f}" cy="{y(d[key]):.1f}" r="4">'
                       f'<title>{_e(_day(d["date"]))} · {_num(d[key])} kcal {"out" if key == "expenditure" else "in"}'
                       f'{" · " + _e(d["expenditureNote"]) if key == "expenditure" and d["expenditureNote"] else ""}</title></circle>'
                       for i, d in enumerate(days))
        parts.append(f'<g class="{cls}"><polyline class="athletics-line" points="{points}"/>{dots}</g>')
    chart = _chart("diet-balance", "Energy out, energy in, and the daily deficit",
                   "Lines show estimated expenditure and logged consumption against the left axis in kilocalories. "
                   "Bars show the daily deficit against the right axis, with the zero line and the "
                   f"{DAILY_TARGET_DEFICIT} kcal target marked. The table below lists every value.", "".join(parts))
    legend = ('<p class="sports-legend"><span class="diet-out">― Expenditure (left)</span><span class="diet-in">― Consumption (left)</span>'
              '<span class="diet-deficit-key">▮ Deficit (right)</span><span class="diet-target-label">┄ Target deficit (right)</span></p>')
    week_rows = [[f"Week of {_day(w['weekOf'])}", f"{_num(w['writtenLoss'])} kcal / ~{w['writtenPounds']:g} lb",
                  f"{_num(w['computedLoss'])} kcal", "✓ matches" if abs(w["writtenLoss"] - w["computedLoss"]) <= 10 else "differs"]
                 for w in weeks]
    rows = [[_day(d["date"]), _num(d["expenditure"]) + (f' ({d["expenditureNote"]})' if d["expenditureNote"] else ""),
             _num(d["consumption"]),
             f'{d["mealMacros"]["carbs"]}/{d["mealMacros"]["fat"]}/{d["mealMacros"]["protein"]} g',
             _signed(-d["deficit"]), _signed(-d["writtenNet"]) if d["writtenNet"] is not None else "—",
             " · ".join(training.get(d["date"], [])) or "Rest day"] for d in days]
    meals = [[_day(d["date"]), m["meal"], m["raw"]] for d in days for m in d["meals"]]
    mismatch = summary["netMismatches"]
    mismatch_note = (f'<p class="sports-note">Written values are kept as written. On {", ".join(_day(x) for x in mismatch)} the written '
                     "net differs from expenditure minus consumption by more than rounding; the computed value drives the charts and the "
                     "written one stays in the table.</p>") if mismatch else ""
    return f'''<main id="main-content" class="collection-page sports-page athletics-page health-page">{lead}
      {_hero("Health / Diet", "Calorie ledger", "Energy in,<br>energy <em>out.</em>", deck, actions, art)}
      <p class="sports-scope">Every tracked day, macros as carbs/fat/protein. Estimates by the owner, not medical or nutrition advice.</p>{metrics}
      {_section("01", "The balance", "Out, in, and what was left over.", "diet-balance-title", f'<div class="bi-diet-host" data-bi-diet="{_e(json.dumps(days, separators=(",", ":")))}">' + legend + chart + '</div>' + mismatch_note +
                f'<p class="sports-note">{_e(HIGH_NEAT_NOTE)} The {_num(DAILY_TARGET_DEFICIT)} kcal/day reference line is the conventional one-pound-a-week cut, chosen by the owner.</p>')}
      {_section("02", "Weeks and training", "The written weekly summaries, checked.", "diet-weeks-title",
                _table("Weekly summaries as written in the log, against the computed total of those days.",
                       ["Week", "Written", "Computed", "Check"], week_rows) +
                '<p>The training column below comes straight from the swimming, weightlifting and running logs on this site; expenditure estimates already include it.</p>' +
                _table("Daily ledger; deficit is negative when consumption won.",
                       ["Date", "Out (kcal)", "In (kcal)", "Macros C/F/P", "Net", "Net as written", "Training that day"], rows, "diet-table"))}
      {_section("03", "The meals", "Every plate, as written.", "diet-log-title",
                f'<details><summary>Show all {len(meals)} meal lines</summary>' +
                _table("Meals; macro triples are carbs/fat/protein grams as logged.", ["Date", "Meal", "As written"], meals, "diet-meals-table") + "</details>")}
      <section class="sports-section sports-method" aria-labelledby="diet-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="diet-method-title">How these numbers are made.</h2>
      <ul><li>Source: {_e(data["source"]["path"])}; any unreadable line stops the build.</li>
      <li>Deficit = written expenditure − written consumption. Headlines and net lines that disagree with that arithmetic are flagged, never corrected.</li>
      <li>BMR is the owner's setting of {_num(OCTOBER_BMR)} kcal for October; expenditure notes in parentheses (walks, cold, dancing) are kept with the day.</li>
      <li>Macro sums add the per-meal triples; meals without a triple contribute nothing rather than a guess.</li></ul>
      {_downloads(3, [("health-diet.json", "Diet log · JSON"), ("health-diet-days.csv", "Days · CSV"), ("health-diet-meals.csv", "Meals · CSV")])}</section>
      {_update_notes("diet", data, '<li>Add a date line like <code>10/19/2026</code>, meal lines like <code>Lunch - 76/29/13g Yam Bowl</code> '
                     '(macros are carbs/fat/protein grams), then <code>Total Expenditure - 3400cals</code>, '
                     '<code>Total Consumption - 2800cals - 300/100/150g</code> and <code>Net Expenditure - 600cals loss</code>.</li>')}
    </main>'''
