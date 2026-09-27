"""Escaped, shell-free readers for analysis schema 1.

The publisher supplies the stylesheet, deferred analysis.js and (for music)
window.MUSIC_ANALYSIS. Each public function returns exactly one complete main.
No source files are imported, read, executed or modified by these renderers.
"""

from __future__ import annotations

from collections import Counter
from html import escape
import math
import re
from typing import Any
from urllib.parse import urlsplit

__all__ = ["vocabulary_body", "feelings_body", "leetcode_body"]
PAGE_SIZE = 40


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _number(value: Any) -> str:
    return f"{int(value or 0):,}"


def _ratio(value: Any) -> str:
    return "Not available" if value is None else f"{float(value):.3f}"


def _url(value: Any) -> str | None:
    if not isinstance(value, str) or any(ord(char) < 33 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return None


def _link(url: Any, label: Any, css: str = "") -> str:
    safe = _url(url)
    if not safe:
        return f'<span class="source-unavailable">{_e(label)} (source link unavailable)</span>'
    return f'<a href="{_e(safe)}" class="{_e(css)}" rel="noopener noreferrer">{_e(label)}</a>'


def _line_url(song: dict, number: int) -> str | None:
    url = _url(song.get("sourceUrl"))
    if not url:
        return None
    anchor = "lines-" if urlsplit(url).hostname == "bitbucket.org" else "L"
    return f'{url.split("#", 1)[0]}#{anchor}{number}'


def _intro(section: str, title: str, description: str) -> str:
    return f'''<div class="page-intro">
      <p class="eyebrow">{_e(section)} / Source notebook</p>
      <h1>{_e(title)}</h1><p class="lede">{_e(description)}</p>
      <nav class="toolbar" aria-label="Collection navigation">
        <a class="button ghost" href="../index.html">Back to {_e(section)}</a>
        <a class="button ghost" href="../../Mental-Map/index.html">Mental map</a>
      </nav></div>'''


def _metric(label: str, value: str, note: str, identifier: str = "") -> str:
    attribute = f' id="{_e(identifier)}"' if identifier else ""
    return f'''<div class="metric-card"><p class="metric-label"><strong>{_e(label)}</strong></p>
      <p class="metric-value"{attribute}>{_e(value)}</p><p>{_e(note)}</p></div>'''


def _music_metrics(music: dict) -> str:
    summary = music["summary"]
    return '<div class="metric-grid">' + "".join([
        _metric("Word tokens", _number(summary["tokenCount"]), "All observed forms, including stopwords.", "vocab-tokens"),
        _metric("Distinct forms", _number(summary["vocabularySize"]), "Casefold forms; not an estimate of personal vocabulary.", "vocab-types"),
        _metric("Type–token ratio", _ratio(summary["ttr"]), "Distinct forms ÷ tokens; sensitive to text length.", "vocab-ttr"),
        _metric("MATTR · 50", _ratio(summary["mattr"]), "Mean over fixed 50-token windows, never crossing songs.", "vocab-mattr"),
        _metric("Hapax forms", _number(summary["hapaxCount"]), "Forms appearing exactly once in the selected scope.", "vocab-hapax"),
    ]) + "</div>"


def _downloads() -> str:
    return '''<nav class="toolbar analysis-downloads" aria-label="Download music analysis">
      <a class="button ghost" href="../../assets/data/music-frequencies.csv" download>Word frequencies · CSV</a>
      <a class="button ghost" href="../../assets/data/music-songs.csv" download>Song metrics · CSV</a>
      <a class="button ghost" href="../../assets/data/music-lines.csv" download>Line results · CSV</a>
      <a class="button ghost" href="../../assets/data/music-analysis.json" download>Full evidence · JSON (large)</a>
    </nav>'''


def _provenance(url: Any, commit: Any) -> str:
    return f'''<p>{_link(url, "Source repository")} · Revision:
      <code class="source-commit">{_e(commit or "unavailable")}</code>.</p>
      <p>The input is the local working tree. A recorded HEAD commit is provenance, not
      proof of a clean checkout; linked source may differ from the analyzed text.</p>'''


def _music_method(music: dict, feelings: bool = False) -> str:
    source = music["source"]
    counts = source["counts"]
    keys = ["input", "tokenization", "lines", "deduplication", "versionBias"]
    keys += ["emotion", "negation", "ties", "uncertainty", "polarity"] if feelings else ["vocabulary", "mattr"]
    notes = "".join(f'<p>{_e(source["methodology"][key])}</p>' for key in keys if key in source["methodology"])
    return f'''<section class="panel method-note" aria-labelledby="analysis-method-title">
      <h2 id="analysis-method-title">Method, provenance &amp; limits</h2>
      {_provenance(source.get("repoUrl"), source.get("commit"))}
      <p>{_number(counts.get("lyricFiles"))} lyric files → {_number(counts.get("songs"))} retained song versions;
      {_number(counts.get("duplicateFiles"))} normalized duplicate files are aliases, not extra observations.
      <strong>All versions with differing text are kept.</strong> Repeated verses remain counted.</p>
      <details><summary>Read the exact analysis rules</summary>{notes}</details>
      {_downloads()}</section>'''


def _song_options(music: dict) -> str:
    return '<option value="">All song versions · corpus</option>' + "".join(
        f'<option value="{_e(song["id"])}">{_e(song["title"])} · {_e(song["collection"])}</option>'
        for song in music["songs"]
    )


def _pager(prefix: str, count: int, noun: str) -> str:
    status = f"1–{min(PAGE_SIZE, count):,} of {count:,} {noun} · Page 1 of {max(1, math.ceil(count / PAGE_SIZE)):,}" if count else f"0 {noun}"
    return f'''<div class="toolbar pagination" aria-label="{_e(noun.capitalize())} pagination">
      <button class="button ghost" id="{prefix}-previous" type="button" disabled>Previous</button>
      <p id="{prefix}-status" role="status" aria-live="polite" aria-atomic="true">{status}</p>
      <button class="button ghost" id="{prefix}-next" type="button" disabled>Next</button>
    </div>'''


def _bars(rows: list[dict], key: str = "word") -> str:
    maximum = max((row["count"] for row in rows), default=0)
    return "".join(
        f'''<div class="bar-row"><span class="bar-label">{_e(row[key])}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="display:block;width:{100 * row['count'] / maximum if maximum else 0:.2f}%"></span></span>
        <span class="bar-count">{_number(row['count'])}</span></div>'''
        for row in rows
    ) or '<p class="empty-state">No word forms in this scope.</p>'


def vocabulary_body(music: dict) -> str:
    """Return a vocabulary reader; metrics always include all word forms."""
    frequencies = music["frequencies"]
    rows = "".join(
        f'<tr><td>{index}</td><th scope="row">{_e(row["word"])}</th><td>{_number(row["count"])}</td>'
        f'<td>{_number(row["songCount"])}</td><td>{"Yes" if row["isStopword"] else "No"}</td></tr>'
        for index, row in enumerate(frequencies[:PAGE_SIZE], 1)
    ) or '<tr><td colspan="5" class="empty-state">No word forms available.</td></tr>'
    return f'''<main id="main-content" class="collection-page"><div id="vocabulary-app">
      {_intro("Language", "A vocabulary in songs", "Explore the words on the page: repetitions, rare forms and the changing texture of each song version.")}
      <p class="analysis-summary">{_number(len(music['songs']))} retained song versions ·
      {_number(music['source']['counts']['retainedLines'])} lyric lines. These describe this corpus, not a person's language ability.</p>
      <section aria-labelledby="vocab-scope"><h2 id="vocab-scope">Corpus · all song versions</h2>
      {_music_metrics(music)}<p id="vocab-window-note">{_number(music['summary']['mattrWindowCount'])} within-song MATTR windows.</p>
    <div id="vocab-source" class="method-note">Exact normalized copies count once; differing versions remain separate.</div></section>
      <section class="panel" aria-labelledby="vocab-filter-title"><h2 id="vocab-filter-title">Explore word frequencies</h2>
      <fieldset id="vocab-controls" class="toolbar" disabled><legend>Frequency filters</legend>
        <label for="vocab-song">Song version<select id="vocab-song">{_song_options(music)}</select></label>
        <label for="vocab-search">Search word forms<input id="vocab-search" type="search" placeholder="Find a word…" maxlength="200" autocomplete="off"></label>
        <label for="vocab-stopwords"><input id="vocab-stopwords" type="checkbox"> Hide stopwords</label>
        <button id="vocab-reset" class="button ghost" type="button">Reset filters</button>
      </fieldset><p class="method-note">Search and stopword filters affect only the chart and table. Cards use <strong>all word forms</strong> in the selected song or corpus. Song spread counts retained versions, not independent compositions.</p>
      <p id="vocab-data-status" role="status">Interactive filters require the local analysis data and JavaScript.</p></section>
      <section class="panel" aria-labelledby="vocab-chart-title"><h2 id="vocab-chart-title">Top 20 word forms · by occurrence</h2>
        <div id="vocab-chart" class="chart-bars">{_bars(frequencies[:20])}</div></section>
      <section class="panel" aria-labelledby="vocab-table-title"><h2 id="vocab-table-title">Frequency index</h2>
        <div class="table-wrap" role="region" aria-label="Word frequency table" tabindex="0"><table id="vocab-table">
        <caption>Occurrences and song spread; 40 forms per page. Rank is the position in the displayed sort.</caption>
        <thead><tr><th scope="col">Rank</th><th scope="col" data-sort-header="word" aria-sort="none"><button type="button" data-vocab-sort="word" disabled>Word ↕</button></th>
        <th scope="col" data-sort-header="count" aria-sort="descending"><button type="button" data-vocab-sort="count" disabled>Count ↕</button></th>
        <th scope="col" data-sort-header="songCount" aria-sort="none"><button type="button" data-vocab-sort="songCount" disabled>Song spread ↕</button></th><th scope="col">Stopword</th></tr></thead>
        <tbody id="vocab-rows">{rows}</tbody></table></div>{_pager('vocab', len(frequencies), 'word forms')}
      </section><noscript><p class="method-note">Showing the first 40 corpus word forms and top 20 chart. Download the complete CSV or JSON below for the full index.</p></noscript>
      {_music_method(music)}</div></main>'''


def _color(value: Any) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else "#64748b"


def _contrast(color: str) -> str:
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in rgb]
    luminance = sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    return "#000000" if luminance > 0.179 else "#ffffff"


def _point(radius: float, angle: float) -> tuple[float, float]:
    radians = math.radians(angle)
    return 360 + radius * math.cos(radians), 360 + radius * math.sin(radians)


def _sector(inner: float, outer: float, start: float, end: float) -> str:
    a, b, c, d = _point(outer, start), _point(outer, end), _point(inner, end), _point(inner, start)
    large = int(end - start > 180)
    return (f"M {a[0]:.3f},{a[1]:.3f} A {outer},{outer} 0 {large} 1 {b[0]:.3f},{b[1]:.3f} "
            f"L {c[0]:.3f},{c[1]:.3f} A {inner},{inner} 0 {large} 0 {d[0]:.3f},{d[1]:.3f} Z")


def _wheel(emotions: list[dict]) -> str:
    # Original equal-angle layout: geometry is taxonomy, NOT count or confidence.
    sectors = []
    for index, family in enumerate(emotions):
        start = -90 + index * 360 / len(emotions)
        end = -90 + (index + 1) * 360 / len(emotions)
        color = _color(family.get("color"))
        items = [(family["name"], "", 122, 222, start, end)]
        branches = family.get("branches", [])
        items += [
            (branch["label"], branch["label"], 226, 346,
             start + i * (end - start) / len(branches), start + (i + 1) * (end - start) / len(branches))
            for i, branch in enumerate(branches)
        ]
        for label, branch, inner, outer, left, right in items:
            middle = (left + right) / 2
            x, y = _point((inner + outer) / 2, middle)
            rotation = middle if branch else middle + 90
            rotation = (rotation + 180) % 360 - 180
            if rotation > 90:
                rotation -= 180
            elif rotation < -90:
                rotation += 180
            accessible = family["name"] + (f" / {branch}" if branch else "")
            sectors.append(f'''<a href="#feelings-results" role="button" tabindex="{0 if index == 0 and not branch else -1}"
              class="wheel-sector" data-emotion="{_e(family['name'])}" data-branch="{_e(branch)}"
              aria-label="Filter active cues: {_e(accessible)}" aria-pressed="false">
              <title>{_e(accessible)}</title><path d="{_sector(inner, outer, left + 0.35, right - 0.35)}" fill="{color}" stroke="currentColor" stroke-width="0.4"/>
              <text class="wheel-label" x="{x:.3f}" y="{y:.3f}" transform="rotate({rotation:.3f} {x:.3f} {y:.3f})"
              text-anchor="middle" dominant-baseline="middle" font-size="{10 if branch else 13}" fill="{_contrast(color)}" pointer-events="none">{_e(label)}</text></a>''')
    return f'''<svg id="feelings-wheel" class="emotion-wheel" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720"
      width="720" height="720" style="width:100%;height:auto" role="group" aria-labelledby="wheel-title wheel-description">
      <title id="wheel-title">An original map of 12 text-cue families and 48 branches</title>
      <desc id="wheel-description">Equal-sized sectors are categories, not quantities. Select a sector to filter active supporting cues.
      Use arrow keys, Home and End within the wheel, then Enter or Space. The labeled controls below provide the same filters.</desc>
      {''.join(sectors)}<circle cx="360" cy="360" r="110" fill="none" stroke="currentColor"/>
      <text x="360" y="352" text-anchor="middle" fill="currentColor" font-size="22">Text cues</text>
      <text x="360" y="382" text-anchor="middle" fill="currentColor" font-size="14">not a diagnosis</text></svg>'''


def _polarity(line: dict) -> tuple[str, str]:
    value = line.get("polarity", {}).get("compound")
    if value is None:
        return "Unavailable", "not available"
    return ("Positive" if value >= 0.05 else "Negative" if value <= -0.05 else "Neutral"), f"{value:+.3f}"


def _line_card(song: dict, line: dict) -> str:
    identifier = f"line-{song['id']}-{line['number']}"
    polarity, compound = _polarity(line)
    evidence = "".join(
        f'<li class="evidence-chip{" is-negated" if cue["negated"] else ""}">'
        f'{_e(cue["family"])} / {_e(cue["label"])}: “{_e(cue["text"])}” — '
        + (f'negated by {_e(", ".join(item["word"] for item in cue["negators"]))}; excluded (0)' if cue["negated"] else 'active cue (+1)')
        + '</li>' for cue in line.get("evidence", [])
    )
    scores = "; ".join(f'{item["family"]}: {item["score"]}' for item in line.get("emotionScores", []))
    ambiguity = "Multiple active families or tied primary branches; the primary label is a heuristic." if line.get("ambiguous") else "No competing active label recorded; this is not certainty."
    if line.get("tiedEmotions"):
        ambiguity += " Top-family tie: " + ", ".join(line["tiedEmotions"]) + "."
    return f'''<article class="line-card" id="{_e(identifier)}" tabindex="-1" data-line-number="{line['number']}">
      <h3>{_e(song['title'])} · Line {line['number']}</h3><p class="line-meta">{_e(song['collection'])} · {_link(_line_url(song, line['number']), 'Source line ' + str(line['number']))}
      · <a class="line-permalink" href="#{_e(identifier)}">Link to this line</a></p>
      <p class="lyric-text" dir="auto">{_e(line['text'])}</p>
      <p><strong>Heuristic primary:</strong> {_e(line['emotion'])}{' / ' + _e(line['subemotion']) if line.get('subemotion') else ''}
      · VADER polarity: {_e(polarity)} · compound {_e(compound)}</p>
      <p class="method-note">{_e(ambiguity)}</p>
      <details class="line-evidence"><summary>Supporting evidence · {len(line.get('evidence', []))} cue mappings</summary>
        <p>Family occurrence scores (not probabilities): {_e(scores or 'none')}.</p>
        <ul>{evidence}</ul>{'' if evidence else '<p>No lexicon cues matched. Unclassified does not mean neutral feelings.</p>'}
      </details></article>'''


def feelings_body(music: dict) -> str:
    """Return an evidence-first lyric reader with a keyboard-operable SVG wheel."""
    lines = [(song, line) for song in music["songs"] for line in song["lines"]]
    families = music["emotions"]
    primary_counts = Counter(line["emotion"] for _, line in lines)
    active_counts: Counter[str] = Counter()
    for _, line in lines:
        active_counts.update({score["family"] for score in line["emotionScores"] if score["score"] > 0})
    options = '<option value="">All families</option>' + "".join(f'<option>{_e(family["name"])}</option>' for family in families) + '<option>Unclassified</option>'
    legend = "".join(
        f'<button class="button ghost emotion-legend-button" type="button" data-emotion="{_e(family["name"])}" data-branch="" aria-pressed="false" disabled>'
        f'<span class="emotion-swatch" style="background-color:{_color(family.get("color"))}" aria-hidden="true"></span>{_e(family["name"])}</button>'
        for family in families
    )
    chart = [{"word": family["name"], "count": active_counts[family["name"]]} for family in families]
    chart.append({"word": "Unclassified", "count": primary_counts["Unclassified"]})
    return f'''<main id="main-content" class="collection-page"><div id="feelings-app">
      {_intro("Language", "Feelings, read line by line", "Follow textual cues through the songs, then inspect the words behind every label.")}
      <p class="method-note"><strong>Exploratory text heuristics, not mental states or diagnoses.</strong>
      Family names, including “Depressed”, label lexicon cues only. Scores are occurrence counts, never confidence probabilities.
      Sarcasm, narrative voice, quotations and metaphor are not resolved.</p>
      <div class="metric-grid">{_metric('Song versions', _number(len(music['songs'])), 'Differing versions retained.')}
      {_metric('Retained lines', _number(len(lines)), 'Original physical order; blank/header/timestamp-only lines excluded.')}
      {_metric('Unclassified', _number(primary_counts['Unclassified']), 'No active cues, not neutral emotion.')}
      {_metric('Ambiguous lines', _number(sum(bool(line['ambiguous']) for _, line in lines)), 'Multiple active families or tied primary branches.')}</div>
      <section class="panel" aria-labelledby="feelings-filter-title"><h2 id="feelings-filter-title">Choose a reading</h2>
      <fieldset id="feelings-controls" class="toolbar" disabled><legend>Line filters</legend>
        <label for="feelings-song">Song version<select id="feelings-song">{_song_options(music)}</select></label>
        <label for="feelings-search">Search lyric text<input id="feelings-search" type="search" placeholder="Find a phrase…" maxlength="200" autocomplete="off"></label>
        <label for="feelings-family">Cue family<select id="feelings-family">{options}</select></label>
        <label for="feelings-branch">Supporting branch<select id="feelings-branch"><option value="">All branches</option></select></label>
        <label for="feelings-polarity">VADER polarity<select id="feelings-polarity"><option value="">All polarities</option><option value="positive">Positive</option><option value="neutral">Neutral</option><option value="negative">Negative</option></select></label>
        <button id="feelings-reset" class="button ghost" type="button">Reset filters</button>
      </fieldset><p id="feelings-data-status" role="status">Interactive filters require the local analysis data and JavaScript.</p>
      <p class="method-note">Family/branch filters include <strong>any active supporting match</strong>, not only the primary label; negated cues remain visible in evidence but do not match those filters.
      Positive compound ≥ 0.05; negative ≤ −0.05; otherwise neutral. VADER polarity is separate from cue families.</p></section>
      <section class="panel" aria-labelledby="feelings-wheel-heading"><h2 id="feelings-wheel-heading">A map of textual cues</h2>
        <div class="emotion-layout"><div>{_wheel(families)}<p class="method-note">Original equal-angle design, not copied artwork. Sector area is not frequency.
        Arrow keys navigate the wheel; Enter or Space selects. Family buttons and the branch selector offer the same actions.</p></div>
        <div><div id="feelings-legend" class="emotion-legend" role="group" aria-label="Filter by cue family">{legend}
        <button class="button ghost emotion-legend-button" type="button" data-emotion="Unclassified" data-branch="" aria-pressed="false" disabled>Unclassified</button>
        <button class="button ghost emotion-legend-button" type="button" data-emotion="" data-branch="" aria-pressed="true" disabled>All families</button></div>
        <h3>Lines with active cues</h3><p id="feelings-chart-note">{_number(len(lines))} lines in the current selection. A line may support several families; Unclassified has no active family.</p>
        <div id="feelings-chart" class="chart-bars">{_bars(chart)}</div></div></div>
      </section>
      <section id="feelings-timeline-panel" class="panel" aria-labelledby="feelings-timeline-title"><h2 id="feelings-timeline-title">Track timeline</h2>
                <div id="feelings-track-source">Choose one song version to see its physical-line timeline.</div>
        <p class="method-note">Each numbered strip is a retained line, colored by heuristic primary family. The text label is also available on focus.
        Selecting a strip clears other line filters and opens that exact line. Missing numbers are excluded source lines.</p>
                <p id="feelings-timeline-label" class="line-meta" role="status">Use arrow keys, Home and End to move between timeline strips.</p>
        <div id="feelings-timeline" class="line-timeline" role="group" aria-label="Jump to a physical lyric line"></div>
      </section>
      <section class="panel" aria-labelledby="feelings-results-title"><h2 id="feelings-results-title">Line browser</h2>
        <p>Song order follows sorted source paths; lines stay in physical input order. Showing at most 40 line cards at once.</p>
        <p id="feelings-navigation-note" class="method-note" role="status"></p>
        <div id="feelings-results">{''.join(_line_card(song, line) for song, line in lines[:PAGE_SIZE]) or '<p class="empty-state">No retained lyric lines.</p>'}</div>
        {_pager('feelings', len(lines), 'lines')}
      </section><noscript><p class="method-note">Showing the first 40 retained lines in source order. All lines and evidence are available in the downloads below.</p></noscript>
      {_music_method(music, feelings=True)}</div></main>'''


def _routine(item: dict, kind: str) -> str:
    return f'<li class="code-symbol">{_link(item.get("url"), item["name"])} <span class="line-meta">{_e(kind)} · source line {_e(item["line"])}</span></li>'


def leetcode_body(code: dict) -> str:
    """Return a static AST inventory with progressively enhanced local search."""
    modules = []
    for index, module in enumerate(code["modules"]):
        functions = module["functions"]
        classes = module["classes"]
        methods = sum(len(cls["methods"]) for cls in classes)
        names = [item["name"] for item in functions]
        names += [cls["name"] for cls in classes]
        names += [method["name"] for cls in classes for method in cls["methods"]]
        search = " ".join([module["name"], module["path"], module["description"], *module["topics"], *names])
        class_blocks = "".join(
            f'<section class="code-class"><h4>{_link(cls.get("url"), cls["name"])} · class at source line {_e(cls["line"])}</h4>'
            f'<ul>{"".join(_routine(method, "direct method") for method in cls["methods"])}</ul>'
            f'{"<p>No direct methods indexed.</p>" if not cls["methods"] else ""}</section>'
            for cls in classes
        )
        number_theory = '<p class="method-note"><strong>Number-theory exercise:</strong> biggest_prime is primality practice, not necessarily a LeetCode submission.</p>' if module["name"] == "biggest_prime" else ""
        modules.append(f'''<article class="feature-card code-module" data-code-module data-search="{_e(search)}" aria-labelledby="code-module-{index}">
          <h2 id="code-module-{index}">{_e(module['name'])}</h2><p>{_e(module['description'])}</p>
          <p class="line-meta">{_link(module.get('url'), module['path'])}</p>
          <ul class="code-topics">{''.join(f'<li class="evidence-chip">{_e(topic)}</li>' for topic in module['topics'])}</ul>
          {number_theory}<p>{len(functions)} top-level functions · {len(classes)} classes · {methods} direct methods.</p>
          <details class="code-symbols"><summary>Browse indexed symbols in {_e(module['name'])}</summary>
          <h3>Top-level functions</h3><ul>{''.join(_routine(item, 'function') for item in functions)}</ul>
          {'' if functions else '<p>No top-level functions indexed.</p>'}
          <h3>Classes &amp; direct methods</h3>{class_blocks or '<p>No top-level classes indexed.</p>'}</details></article>''')
    return f'''<main id="main-content" class="collection-page"><div id="code-app">
      {_intro("Miscellaneous", "LeetCode & algorithm practice", "A source-linked inventory of Python exercises: inspect the modules, topics and definition sites without running their code.")}
      <div class="metric-grid">{_metric('Python modules', _number(code['moduleCount']), 'Files indexed statically.')}
      {_metric('Top-level functions', _number(code['functionCount']), 'Includes async and repeated definitions.')}
      {_metric('Classes', _number(code['classCount']), 'Immediate top-level class definitions.')}
      {_metric('Direct methods', _number(code['methodCount']), 'Includes constructors, not nested routines.')}
      {_metric('Routine definitions', _number(code['routineCount']), 'Functions + direct methods; NOT problems solved.')}</div>
      <section class="panel" aria-labelledby="code-filter-title"><h2 id="code-filter-title">Find a module or symbol</h2>
        <fieldset id="code-controls" class="toolbar" disabled><legend>Local source-index search</legend>
        <label for="code-search">Search modules, topics, classes and methods<input id="code-search" type="search" placeholder="e.g. tree, hash, prime…" maxlength="200" autocomplete="off" aria-controls="code-modules"></label>
        <button class="button ghost" id="code-reset" type="button">Clear search</button></fieldset>
        <p id="code-status" role="status" aria-live="polite" aria-atomic="true">{_number(code['moduleCount'])} of {_number(code['moduleCount'])} modules. JavaScript enables local filtering; all symbols are available below.</p>
      </section><div id="code-modules" class="card-grid">{''.join(modules)}</div>
    <p id="code-empty" class="empty-state"{'' if not modules else ' hidden style="display:none"'}>No matching modules. Try a shorter module, topic or symbol name.</p>
      <noscript><p class="method-note">All modules and collapsible symbol lists work without JavaScript. Use your browser's Find command to search.</p></noscript>
      <section class="panel method-note" aria-labelledby="code-method-title"><h2 id="code-method-title">What this index does—and does not—count</h2>
        <p>{_e(code['methodology'])}</p><p>No completion, correctness, acceptance, difficulty or solved-problem totals are inferred from these definitions. No full source code is reproduced here.</p>
        {_provenance(code.get('sourceUrl'), code.get('commit'))}
      </section></div></main>'''