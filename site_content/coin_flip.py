"""Parse and render the Mario Coin Flip Decision & Override Lab (Gaming-and-Performance-Log/Coin-Flip).

Tracks every coin flip used to resolve a real-life decision, whether the coin landed
Heads or Tails, and—crucially—whether Liam followed the coin's decision or overrode
it ("Feynman / Gut-Check Revealed Preference"). Syncs with a semi-structured Google Doc
in the Drive ``Logs/`` folder as well as the on-page interactive 3D Mario Coin Flipper.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape
from pathlib import Path
import re

from .athletics_views import _day, _downloads, _e, _metrics, _section, _table, _update_notes

COIN_FLIP_SOURCE = "records/athletics/coin_flip/Coin_Flip_Log.txt"
COIN_FLIP_COPY = "LiamMs_PandasProjects/Gaming-and-Performance-Log/Coin-Flip/Coin_Flip_Log.txt"
COIN_FLIP_ROUTE = "Gaming-and-Performance-Log/Coin-Flip/index.html"

_DAY_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(20\d{2})$")
_FLIP_PIPE_RE = re.compile(
    r"^(.+?)\s*\|\s*Heads:\s*(.+?),\s*Tails:\s*(.+?)\s*\|\s*Landed:\s*(Heads|Tails)\s*\|\s*Action:\s*(Followed|Overrode)(?:\s*->\s*([^|]+?))?(?:\s*\|\s*Category:\s*([^|]+?))?(?:\s*\|\s*Note:\s*(.+))?$",
    re.I,
)


def mario_coin_svg(size: int = 44, extra_class: str = "", uid: str = "1") -> str:
    """Dynamic animated Super Mario Coin SVG with golden bevel, embossed vertical slot, and sparkles."""
    cls = f"mario-coin-svg {extra_class}".strip()
    gold_id = f"mc-gold-grad-{uid}"
    slot_id = f"mc-slot-grad-{uid}"
    return (
        f'<svg class="{_e(cls)}" viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
        '<defs>'
        f'<radialGradient id="{_e(gold_id)}" cx="35%" cy="30%" r="70%">'
        '<stop offset="0%" stop-color="#fff6a9"/>'
        '<stop offset="45%" stop-color="#ffd43b"/>'
        '<stop offset="82%" stop-color="#e59900"/>'
        '<stop offset="100%" stop-color="#9c6300"/>'
        '</radialGradient>'
        f'<linearGradient id="{_e(slot_id)}" x1="0%" y1="0%" x2="100%" y2="0%">'
        '<stop offset="0%" stop-color="#8a5200"/>'
        '<stop offset="50%" stop-color="#fff3a1"/>'
        '<stop offset="100%" stop-color="#b87400"/>'
        '</linearGradient>'
        '</defs>'
        '<g class="mario-coin-spin-group">'
        f'<ellipse cx="32" cy="32" rx="25" ry="27" fill="url(#{_e(gold_id)})" stroke="#fff3a1" stroke-width="2"/>'
        '<ellipse cx="32" cy="32" rx="20" ry="22" fill="none" stroke="#b87400" stroke-width="1.6" stroke-dasharray="3 2"/>'
        f'<rect x="28.5" y="16" width="7" height="32" rx="3.5" fill="url(#{_e(slot_id)})" stroke="#7a4700" stroke-width="1.4"/>'
        '<path d="M19 18c3-4 8-6 13-6" fill="none" stroke="#ffffffcc" stroke-width="2.2" stroke-linecap="round"/>'
        '</g>'
        '<g class="mario-coin-sparkle">'
        '<path d="M10 14l2-5 2 5 5 2-5 2-2 5-2-5-5-2z" fill="#fff9bf"/>'
        '<path d="M53 45l1.5-3.8 1.5 3.8 3.8 1.5-3.8 1.5-1.5 3.8-1.5-3.8-3.8-1.5z" fill="#ffd43b"/>'
        '</g>'
        '</svg>'
    )


def mario_coin_floating_badge_html(prefix: str = "../", summary: dict | None = None) -> str:
    """Clickable dynamic Mario Coin pill rendered on the Gaming & Performance Log hero stage."""
    flips = summary["totalFlips"] if summary else 8
    override_pct = summary["overrideRate"] if summary else 50.0
    return (
        f'<a class="mario-coin-widget-link atlas-hover" href="{_e(prefix)}Gaming-and-Performance-Log/Coin-Flip/index.html" '
        f'title="Open the Mario Coin Flip Decision &amp; Override Lab ({flips} flips logged · {override_pct:g}% override rate)">'
        f'<span class="mario-coin-icon-wrap">{mario_coin_svg(48, "is-spinning", uid="hero-badge")}</span>'
        '<span class="mario-coin-copy">'
        '<span class="mario-coin-kicker">🪙 Mario Coin Decision Lab</span>'
        '<strong>Flip a Coin &amp; Track Overrides ↗</strong>'
        f'<small>{flips} decisions logged · {override_pct:g}% gut-check override rate</small>'
        '</span></a>'
    )


def parse_coin_flip(text: str) -> dict:
    raw_lines = [(idx, ln.strip()) for idx, ln in enumerate(text.replace("\r\n", "\n").splitlines(), 1) if ln.strip()]
    if not raw_lines or raw_lines[0][1] != "Coin Flip Decision Log":
        raise ValueError("Coin Flip log must start with 'Coin Flip Decision Log'.")

    cur_date: str | None = None
    flips: list[dict] = []

    for lineno, line in raw_lines[1:]:
        if m_day := _DAY_RE.fullmatch(line):
            cur_date = date(int(m_day[3]), int(m_day[1]), int(m_day[2])).isoformat()
            continue
        if m_flip := _FLIP_PIPE_RE.fullmatch(line):
            if cur_date is None:
                raise ValueError(f"Line {lineno}: coin flip entry before a date line: {line!r}")
            question = m_flip[1].strip()
            heads_opt = m_flip[2].strip()
            tails_opt = m_flip[3].strip()
            landed = m_flip[4].strip().capitalize()
            action = m_flip[5].strip().capitalize()
            overrode = action == "Overrode"
            coin_choice = heads_opt if landed == "Heads" else tails_opt
            opposite_choice = tails_opt if landed == "Heads" else heads_opt
            final_choice = (m_flip[6] or (opposite_choice if overrode else coin_choice)).strip()
            category = (m_flip[7] or "General").strip()
            note = (m_flip[8] or "").strip()
            flips.append({
                "number": len(flips) + 1,
                "date": cur_date,
                "question": question,
                "headsOption": heads_opt,
                "tailsOption": tails_opt,
                "landed": landed,
                "coinChoice": coin_choice,
                "action": action,
                "overrode": overrode,
                "finalChoice": final_choice,
                "category": category,
                "note": note,
                "rawLine": line,
            })
            continue
        raise ValueError(f"Line {lineno}: unreadable Coin Flip entry {line!r}.")

    if not flips:
        raise ValueError("Coin Flip Decision Log has no recorded flips.")

    total = len(flips)
    heads_count = sum(1 for f in flips if f["landed"] == "Heads")
    tails_count = total - heads_count
    override_count = sum(1 for f in flips if f["overrode"])
    follow_count = total - override_count

    heads_overrides = sum(1 for f in flips if f["landed"] == "Heads" and f["overrode"])
    tails_overrides = sum(1 for f in flips if f["landed"] == "Tails" and f["overrode"])

    by_cat: dict[str, dict] = defaultdict(lambda: {"category": "", "flips": 0, "followed": 0, "overrode": 0, "heads": 0, "tails": 0})
    for f in flips:
        c = by_cat[f["category"]]
        c["category"] = f["category"]
        c["flips"] += 1
        if f["overrode"]:
            c["overrode"] += 1
        else:
            c["followed"] += 1
        if f["landed"] == "Heads":
            c["heads"] += 1
        else:
            c["tails"] += 1

    categories = []
    for cat_name, c in by_cat.items():
        c["overrideRate"] = round(100.0 * c["overrode"] / max(1, c["flips"]), 1)
        categories.append(dict(c))
    categories.sort(key=lambda x: (x["flips"], x["overrode"]), reverse=True)

    dates_sorted = sorted({f["date"] for f in flips})
    return {
        "flips": flips,
        "categories": categories,
        "summary": {
            "totalFlips": total,
            "followedCount": follow_count,
            "overrodeCount": override_count,
            "overrideRate": round(100.0 * override_count / total, 1),
            "followRate": round(100.0 * follow_count / total, 1),
            "headsCount": heads_count,
            "tailsCount": tails_count,
            "headsPct": round(100.0 * heads_count / total, 1),
            "headsOverrides": heads_overrides,
            "tailsOverrides": tails_overrides,
            "firstDate": dates_sorted[0],
            "lastDate": dates_sorted[-1],
            "topCategory": categories[0]["category"] if categories else "General",
        },
    }


def load_coin_flip(root: Path) -> dict:
    src = root / COIN_FLIP_SOURCE
    copy = root / COIN_FLIP_COPY
    text = src.read_text(encoding="utf-8-sig")
    if copy.is_file() and copy.read_text(encoding="utf-8-sig").replace("\r\n", "\n") != text.replace("\r\n", "\n"):
        raise ValueError(f"{COIN_FLIP_COPY} differs from {COIN_FLIP_SOURCE}; sync them before building.")
    parsed = parse_coin_flip(text)
    nonempty = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parsed["source"] = {
        "path": COIN_FLIP_SOURCE,
        "latestEntry": nonempty[-8:],
    }
    return parsed


def coin_flip_rows(data: dict) -> dict[str, list[dict]]:
    return {
        "coin-flip-decisions": [
            {
                "number": f["number"],
                "date": f["date"],
                "question": f["question"],
                "headsOption": f["headsOption"],
                "tailsOption": f["tailsOption"],
                "landed": f["landed"],
                "action": f["action"],
                "finalChoice": f["finalChoice"],
                "category": f["category"],
                "note": f["note"],
            }
            for f in data["flips"]
        ],
        "coin-flip-categories": data["categories"],
    }


def _category_chart_svg(categories: list[dict]) -> str:
    width, height = 900, 320
    left, right, top, bottom = 74, 826, 40, 268
    plot_w, plot_h = right - left, bottom - top
    max_flips = max(1, max(c["flips"] for c in categories))
    step = plot_w / max(1, len(categories))

    parts = [
        '<title id="coin-flip-category-svg-title">Followed vs. Overridden Coin Flips by Decision Category</title>',
        '<desc id="coin-flip-category-svg-desc">Stacked bars showing Followed decisions (teal) and Overridden decisions (gold/coral) per category, with override percentage on the right axis.</desc>',
        f'<text x="{left - 8}" y="22" text-anchor="end" fill="#69d4cf" font-weight="700" font-size="11">▮ Stacked Bars: Followed (Teal) + Overrode (Gold)</text>',
        f'<text x="{right + 8}" y="22" text-anchor="start" fill="#ffd43b" font-weight="700" font-size="11">● Line: Override Rate (%)</text>',
    ]
    for k in range(5):
        f_tick = round(max_flips * k / 4, 1)
        p_tick = round(100 * k / 4)
        ty = bottom - (k / 4) * plot_h
        parts.append(
            f'<line class="chart-grid" x1="{left}" x2="{right}" y1="{ty:.1f}" y2="{ty:.1f}"/>'
            f'<text x="{left - 8}" y="{ty + 4:.1f}" text-anchor="end">{f_tick:g}</text>'
            f'<text x="{right + 8}" y="{ty + 4:.1f}" text-anchor="start" fill="#ffd43b">{p_tick}%</text>'
        )

    line_pts = []
    for idx, c in enumerate(categories):
        cx = left + (idx + 0.5) * step
        bw = min(56.0, max(22.0, step * 0.55))
        bx = cx - bw / 2
        fol_h = (c["followed"] / max_flips) * plot_h
        ovr_h = (c["overrode"] / max_flips) * plot_h
        fy = bottom - fol_h
        oy = fy - ovr_h
        py = bottom - (c["overrideRate"] / 100.0) * plot_h
        line_pts.append((cx, py, c))
        parts.append(
            f'<g><title>{_e(c["category"])}: {c["flips"]} flips ({c["followed"]} followed, {c["overrode"]} overrode · {c["overrideRate"]}%)</title>'
            f'<rect fill="#69d4cf" x="{bx:.1f}" y="{fy:.1f}" width="{bw:.1f}" height="{fol_h:.1f}"/>'
            f'<rect fill="#ffd43b" x="{bx:.1f}" y="{oy:.1f}" width="{bw:.1f}" height="{ovr_h:.1f}"/>'
            f'<text x="{cx:.1f}" y="{max(26.0, oy - 6):.1f}" text-anchor="middle" font-size="10.5" fill="#eeeef7" font-weight="700">{c["followed"]}F / {c["overrode"]}O</text>'
            f'<text x="{cx:.1f}" y="{bottom + 20}" text-anchor="middle" font-size="11">{_e(c["category"])}</text>'
            f'</g>'
        )

    if len(line_pts) > 1:
        poly = " ".join(f"{cx:.1f},{py:.1f}" for cx, py, _ in line_pts)
        parts.append(f'<polyline fill="none" stroke="#ffd43b" stroke-width="2.8" points="{poly}"/>')
    for cx, py, c in line_pts:
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{py:.1f}" r="4.5" fill="#ffd43b" stroke="#0d101b" stroke-width="1.6">'
            f'<title>{_e(c["category"])} Override Rate: {c["overrideRate"]}%</title></circle>'
        )

    return (
        '<figure class="sports-chart athletics-chart">'
        '<figcaption><span class="chart-title">Coin Decisions by Category — Followed vs. Overridden ("Gut-Check" Rate)</span>'
        '<small>Teal = Followed the Coin · Gold = Overrode the Coin · Yellow Line = Override Rate (%)</small></figcaption>'
        f'<svg class="sports-chart" viewBox="0 0 {width} {height}" role="img" aria-labelledby="coin-flip-category-svg-title coin-flip-category-svg-desc">'
        + "".join(parts)
        + "</svg></figure>"
    )


def coin_flip_body(data: dict, lead: str = "") -> str:
    s = data["summary"]
    flips = data["flips"]
    categories = data["categories"]

    deck = (
        f"Every time I flip a coin to resolve a decision—plus every time my gut overrides the coin the moment it lands. "
        f"{s['totalFlips']} flips logged since {_day(s['firstDate'])}: {s['followedCount']} followed ({s['followRate']}%) vs. "
        f"{s['overrodeCount']} overridden ({s['overrideRate']}%)."
    )
    actions = (
        '<a class="button primary" href="#mario-coin-app">🪙 Flip the Mario Coin</a>'
        '<a class="button ghost" href="#coin-flip-analytics-title">Override analytics</a>'
        '<a class="button ghost" href="#coin_flip-update">Sync Google Doc ↓</a>'
    )
    art = (
        '<div class="athletics-split-card mario-coin-hero-card" aria-hidden="true">'
        f'<div style="display:flex;justify-content:center;margin-bottom:6px;">{mario_coin_svg(64, "is-spinning", uid="hero")}</div>'
        f'<span class="split-Chest"><strong>{s["headsCount"]}H · {s["tailsCount"]}T</strong>{s["headsPct"]}% Heads</span>'
        f'<span class="split-Back"><strong>{s["followedCount"]} Followed</strong>{s["followRate"]}% obeyed</span>'
        f'<span class="split-Shoulders"><strong>{s["overrodeCount"]} Overrode</strong>{s["overrideRate"]}% gut override</span></div>'
    )
    metrics = _metrics([
        ("Decisions flipped", str(s["totalFlips"]), f"{_day(s['firstDate'])} → {_day(s['lastDate'])} · {s['headsCount']} Heads, {s['tailsCount']} Tails"),
        ("Override rate (Gut-Check)", f"{s['overrideRate']}%", f"Overrode {s['overrodeCount']} of {s['totalFlips']} flips ({s['followedCount']} followed)"),
        ("Heads vs. Tails fairness", f"{s['headsPct']}% Heads", f"{s['headsOverrides']} overrides on Heads · {s['tailsOverrides']} on Tails"),
        ("Top decision arena", s["topCategory"], "Synced with Google Drive Coin_Flip_Log.txt"),
    ])

    interactive_flipper_html = f'''
    <section class="sports-section" id="mario-coin-app" aria-labelledby="mario-coin-app-title">
      <p class="sports-kicker">01 / Interactive 3D Super Mario Coin Flipper &amp; Override Recorder</p>
      <h2 id="mario-coin-app-title">Flip the coin—then record whether you obeyed it or overrode it.</h2>
      <p class="sports-note">Why track overrides? When you flip a coin between two hard choices, your gut reaction while the coin is in mid-air (or the split-second it lands) often reveals what you actually wanted all along. Flip below, then log whether you <strong>Followed</strong> or <strong>Overrode</strong> the coin!</p>
      <div class="study-reg-card mario-flipper-card" style="padding:20px;margin:14px 0;">
        <div class="wb-form-grid" style="grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;">
          <label class="wb-wide" for="mc-question-input">Decision / Dilemma Question
            <input id="mc-question-input" type="text" placeholder="e.g. Swim 2000m vs. Rest Day, or Order Shawarma vs. Cook Fried Rice" value="Swim 2000m vs. Take a Rest Day">
          </label>
          <label for="mc-heads-input">🌟 Heads Option (Option A)
            <input id="mc-heads-input" type="text" placeholder="e.g. Swim 2000m" value="Swim 2000m">
          </label>
          <label for="mc-tails-input">🍄 Tails Option (Option B)
            <input id="mc-tails-input" type="text" placeholder="e.g. Take a Rest Day" value="Take a Rest Day">
          </label>
          <label for="mc-category-select">Decision Category
            <select id="mc-category-select">
              <option value="Training &amp; Athletics" selected>Training &amp; Athletics</option>
              <option value="Food &amp; Diet">Food &amp; Diet</option>
              <option value="Study &amp; Career">Study &amp; Career</option>
              <option value="Gaming &amp; Smash">Gaming &amp; Smash</option>
              <option value="General &amp; Life">General &amp; Life</option>
            </select>
          </label>
          <label for="mc-note-input">Gut Reaction / Context Note (optional)
            <input id="mc-note-input" type="text" placeholder="Why did you follow or override the coin?">
          </label>
        </div>

        <div class="mario-coin-stage" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 12px;margin:16px 0;border-radius:12px;background:radial-gradient(circle at center, rgba(255,212,59,0.14), rgba(13,16,27,0.92));border:1px solid rgba(255,212,59,0.32);">
          <button type="button" id="mc-coin-stage-btn" class="mario-coin-stage-btn" aria-label="Flip the Mario Coin" style="background:none;border:none;cursor:pointer;padding:10px;transition:transform 0.2s;">
            <div id="mc-coin-3d" class="mario-coin-3d">{mario_coin_svg(112, "is-interactive", uid="stage")}</div>
          </button>
          <div id="mc-flip-readout" style="text-align:center;margin-top:10px;">
            <span class="wb-badge wb-up" id="mc-flip-badge" style="font-size:14px;padding:6px 14px;">🪙 Ready · Click the Mario Coin or button below to flip!</span>
            <p id="mc-flip-detail" style="margin:8px 0 0;color:#e8eaf6;font-size:15px;font-weight:600;">Heads = Swim 2000m · Tails = Take a Rest Day</p>
          </div>
          <div class="wb-form-actions" style="margin-top:14px;justify-content:center;flex-wrap:wrap;gap:10px;">
            <button type="button" class="button primary" id="mc-flip-trigger-btn" style="background:linear-gradient(135deg,#ffd43b,#e59900);color:#0d101b;font-weight:800;border:none;">🪙 Flip Mario Coin! (50 / 50)</button>
            <button type="button" class="button ghost" id="mc-record-follow-btn" disabled>✓ Follow Coin's Decision &amp; Log</button>
            <button type="button" class="button ghost" id="mc-record-override-btn" disabled style="border-color:#ffd43b88;color:#ffd43b;">⚡ Override Coin! (Do the Opposite &amp; Log)</button>
          </div>
          <p id="mc-log-feedback" class="gdoc-sync-status" role="status" aria-live="polite" style="margin-top:10px;text-align:center;">Every recorded flip updates the charts &amp; table below and formats a canonical line for your Google Doc.</p>
        </div>
      </div>
    </section>'''

    cat_rows = [
        [
            c["category"],
            str(c["flips"]),
            f"{c['heads']}H / {c['tails']}T",
            str(c["followed"]),
            str(c["overrode"]),
            f"{c['overrideRate']}%",
        ]
        for c in categories
    ]

    flip_rows = [
        [
            f"#{f['number']} · {_day(f['date'])}",
            f["category"],
            f["question"],
            f"H: {f['headsOption']} / T: {f['tailsOption']}",
            f"{'🌟' if f['landed'] == 'Heads' else '🍄'} {f['landed']} ({f['coinChoice']})",
            f"{'⚡ Overrode' if f['overrode'] else '✓ Followed'} → {f['finalChoice']}",
            f["note"] or "—",
        ]
        for f in reversed(flips)
    ]

    return f'''<main id="main-content" class="sports-page athletics-page">{lead}
      <header class="sports-hero"><div class="sports-hero-copy"><p class="sports-kicker">Gaming &amp; Performance Log · Mario Coin Decision Lab <span>Revealed Preference &amp; Override Telemetry</span></p>
      <h1>Flip the coin.<br>Measure the <em>override.</em></h1><p class="sports-deck">{_e(deck)}</p><div class="toolbar">{actions}</div></div>{art}</header>
      {metrics}
      {interactive_flipper_html}
      {_section("02", "Category breakdown & gut-check override rate", f"{s['totalFlips']} logged coin flips across {len(categories)} decision arenas.", "coin-flip-analytics-title",
                _category_chart_svg(categories)
                + _table("Coin flip outcomes and override rates by category.", ["Category", "Total Flips", "Heads / Tails", "Followed Coin", "Overrode Coin", "Override Rate"], cat_rows, table_id="coin-flip-category-table"))}
      {_section("03", "Every recorded coin flip & override", "Newest first · includes what the coin landed on, whether it was overridden, and the final action taken.", "coin-flip-log-title",
                _table("Complete Coin Flip Decision & Override Log.", ["Flip & Date", "Category", "Dilemma", "Options (Heads / Tails)", "Coin Landed", "Outcome & Final Choice", "Why / Gut Note"], flip_rows, table_id="coin-flip-table"))}
      <section class="sports-section sports-method" aria-labelledby="coin-flip-method-title"><p class="sports-kicker">The evidence desk</p><h2 id="coin-flip-method-title">How the Coin Flip &amp; Override Log works.</h2>
      <ul><li>Source: <code>{_e(data["source"]["path"])}</code>, synced with your Google Drive <code>Logs/</code> folder and the interactive flipper above.</li>
      <li>Grammar: under a <code>M/D/YYYY</code> date line, each flip is written as <code>Question | Heads: Option A, Tails: Option B | Landed: Heads/Tails | Action: Followed/Overrode -&gt; Final Choice | Category: Category | Note: Optional note</code>.</li></ul>
      {_downloads(2, [("coin-flip.json", "Coin Flip log · JSON"), ("coin-flip-decisions.csv", "All decisions · CSV"), ("coin-flip-categories.csv", "Category summary · CSV")])}</section>
      {_update_notes("coin_flip", data, '<li>Add a date line like <code>11/8/2026</code>, then a flip line like <code>Swim vs. Rest | Heads: Swim, Tails: Rest | Landed: Tails | Action: Overrode -&gt; Swim | Category: Training &amp; Athletics | Note: Wanted to swim</code>.</li>', depth=2)}
    </main>'''
