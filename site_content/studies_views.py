"""Views for the Macroeconomics AI Iceberg study and the 2026 Alberta Referendum study."""

from __future__ import annotations

from html import escape
import json
from typing import Any

from .athletics_views import _chart, _downloads, _hero, _metrics, _num, _section, _table

__all__ = ["ai_cost_study_body", "alberta_study_body", "gas_study_body", "gen_tax_study_body", "macro_study_body", "sodium_study_body"]


def _e(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _safe_attr_json(value: Any) -> str:
    return escape(json.dumps(value, separators=(",", ":")), quote=True)


def _inspector_param_card(label: str, val_id: str, val_str: str, defn: str, mm_href: str, mm_label: str) -> str:
    """Render an interactive parameter box inside a Study Inspector with hover/tap definition & Mental Map link."""
    return (
        f'<div class="study-param-card" data-kpi-card tabindex="0" role="button" aria-expanded="false" '
        f'aria-label="{_e(label)}: {_e(val_str)}. Tap or hover for definition.">'
        f'<span class="kpi-head"><span>{_e(label)}</span><em class="kpi-info-badge" aria-hidden="true">ⓘ</em></span>'
        f'<strong id="{_e(val_id)}">{_e(val_str)}</strong>'
        f'<div class="kpi-tooltip" role="tooltip">'
        f'<div class="kpi-tip-title">{_e(label)} · Parameter Definition</div>'
        f'<p class="kpi-tip-desc">{_e(defn)}</p>'
        f'<a class="kpi-tip-mm" href="{_e(mm_href)}">🧠 Mental Map: {_e(mm_label)} ↗</a>'
        f'</div></div>'
    )


def _inspector_attr_row(label: str, val_id: str, val_str: str, defn: str, mm_href: str, mm_label: str) -> str:
    """Render an interactive structural attribute row inside a Study Inspector with hover/tap definition & Mental Map link."""
    return (
        f'<div class="study-sector-row study-attr-row" data-kpi-card tabindex="0" role="button" aria-expanded="false" '
        f'aria-label="{_e(label)}: {_e(val_str)}. Tap or hover for definition.">'
        f'<span>{_e(label)} <em class="kpi-info-badge" aria-hidden="true">ⓘ</em></span>'
        f'<strong id="{_e(val_id)}" style="grid-column: span 2; text-align:right;">{_e(val_str)}</strong>'
        f'<div class="kpi-tooltip" role="tooltip">'
        f'<div class="kpi-tip-title">{_e(label)} · Attribute Definition</div>'
        f'<p class="kpi-tip-desc">{_e(defn)}</p>'
        f'<a class="kpi-tip-mm" href="{_e(mm_href)}">🧠 Mental Map: {_e(mm_label)} ↗</a>'
        f'</div></div>'
    )


def _macro_iceberg_svg(industries: list[dict[str, Any]]) -> str:
    """Horizontal stacked bar chart: visible surface AI exposure vs. submerged Iceberg exposure by NAICS industry."""
    ordered = sorted(industries, key=lambda s: s["surfacePct"] + s["submergedPct"], reverse=True)
    height = 70 + len(ordered) * 32
    max_pct = 50.0
    left, width = 265.0, 420.0
    parts = []
    for tick in range(0, 51, 10):
        tx = left + tick / max_pct * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="32" y2="{height - 28}"/>'
            f'<text x="{tx:.1f}" y="22" text-anchor="middle">{tick}%</text>'
        )
    for idx, sec in enumerate(ordered):
        y = 40 + idx * 32
        w_surf = sec["surfacePct"] / max_pct * width
        w_sub = sec["submergedPct"] / max_pct * width
        total = sec["surfacePct"] + sec["submergedPct"]
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(sec["name"])}</text>'
            f'<rect class="study-bar-surface" x="{left:.1f}" y="{y:.1f}" width="{w_surf:.1f}" height="20">'
            f'<title>{_e(sec["name"])} · visible surface AI exposure: {sec["surfacePct"]}%</title></rect>'
            f'<rect class="study-bar-submerged" x="{left + w_surf:.1f}" y="{y:.1f}" width="{w_sub:.1f}" height="20">'
            f'<title>{_e(sec["name"])} · submerged Iceberg skill exposure: {sec["submergedPct"]}%</title></rect>'
            f'<text class="athletics-label" x="{left + w_surf + w_sub + 8:.1f}" y="{y + 15:.1f}">{total:.1f}% ({sec["submergedPct"]:.1f}% sub.)</text>'
        )
    return _chart(
        "macro-iceberg-bars",
        "Visible tip vs. submerged Iceberg AI wage exposure across 12 NAICS sectors",
        "Each row shows the share of industry wage value in visible tech/AI adoption (cyan) plus submerged administrative, analytical, and cognitive skill exposure (amber).",
        "".join(parts),
        height=height,
    )


def _macro_roles_svg(industries: list[dict[str, Any]], role_families: list[dict[str, Any]]) -> str:
    """100% stacked horizontal bars showing internal occupational role breakdown inside each industry."""
    height = 70 + len(industries) * 32
    left, width = 265.0, 580.0
    parts = []
    for tick in range(0, 101, 20):
        tx = left + tick / 100.0 * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="32" y2="{height - 28}"/>'
            f'<text x="{tx:.1f}" y="22" text-anchor="middle">{tick}%</text>'
        )
    for idx, sec in enumerate(industries):
        y = 40 + idx * 32
        cursor = left
        parts.append(f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(sec["name"])}</text>')
        for fam_idx, fam in enumerate(role_families):
            share = sec["roles"][fam["key"]]
            seg_w = share / 100.0 * width
            parts.append(
                f'<rect class="role-seg role-{fam_idx}" x="{cursor:.1f}" y="{y:.1f}" width="{seg_w:.1f}" height="20">'
                f'<title>{_e(sec["name"])} · {_e(fam["label"])}: {share}%</title></rect>'
            )
            if share >= 12:
                parts.append(f'<text class="role-seg-label" x="{cursor + seg_w / 2:.1f}" y="{y + 14:.1f}" text-anchor="middle">{share}%</text>')
            cursor += seg_w
    return _chart(
        "macro-role-composition",
        "Occupational role breakdown inside each major industry (100% of sector employment)",
        "Stacked bars split each NAICS industry into six role families: Analytical/Tech, Administrative/Clerical, Management, Sales, Skilled Trades, and Hands-On Care/Field Ops.",
        "".join(parts),
        height=height,
    )


def _macro_region_map_svg(regions: list[dict[str, Any]]) -> str:
    """Interactive + static SVG map of 12 North American regional economies."""
    outline = (
        '<rect x="20" y="16" width="860" height="428" rx="10" class="study-map-bg"/>'
        '<path class="study-map-land" d="M110 85 L360 75 L590 95 L790 120 L830 205 L765 320 L685 405 L535 395 L410 420 L270 375 L135 340 L105 210 Z"/>'
        '<line class="study-map-border" x1="125" y1="182" x2="775" y2="182"/>'
        '<text class="study-map-caption" x="48" y="46">CANADA · Provincial economic corridors</text>'
        '<text class="study-map-caption" x="48" y="424">UNITED STATES · Regional economic belts (click any node to inspect)</text>'
    )
    nodes = []
    for idx, reg in enumerate(regions):
        total = round(reg["surfacePct"] + reg["submergedPct"], 1)
        radius = 16 + min(12, round(reg["workersMillions"] * 0.45))
        active = " is-selected" if idx == 0 else ""
        nodes.append(
            f'<g class="study-map-node{active}" tabindex="0" role="button" data-region-node="{_e(reg["id"])}" '
            f'aria-label="{_e(reg["name"])}: {total}% combined AI exposure ({reg["submergedPct"]}% submerged)">'
            f'<circle class="study-map-halo" cx="{reg["x"]}" cy="{reg["y"]}" r="{radius + 7}"/>'
            f'<circle class="study-map-pin" cx="{reg["x"]}" cy="{reg["y"]}" r="{radius}"/>'
            f'<text class="study-map-code" x="{reg["x"]}" y="{reg["y"] + 4}" text-anchor="middle">{_e(reg["id"])}</text>'
            f'<text class="study-map-pct" x="{reg["x"]}" y="{reg["y"] + radius + 16}" text-anchor="middle">{total}%</text>'
            f'</g>'
        )
    return _chart(
        "macro-region-map",
        "North American regional economies: combined AI wage exposure and sector structure",
        "Twelve regional economies across Canada and the United States positioned schematically. Node size reflects workforce scale; percentage label shows combined surface plus submerged AI exposure.",
        outline + "".join(nodes),
        height=460,
    )


def macro_study_body(data: dict[str, Any], lead: str = "") -> str:
    """Render the Macroeconomics AI Iceberg & Sector Role Breakdown study."""
    s = data["summary"]
    industries = data["industries"]
    regions = data["regions"]
    roles = data["roleFamilies"]
    first_reg = regions[0]

    deck = (
        f"What AI actually touches when you look beneath Silicon Valley: modeling {s['workersMillions']}M workers, "
        f"{s['occupations']} occupations, and {s['skills']:,} skills across {s['industries']} major industries and "
        f"{s['regions']} North American regional economies."
    )
    actions = (
        '<a class="button primary" href="Paper/index.html">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#macro-map-title">Interactive economy map</a>'
        '<a class="button ghost" href="../../../Workbench/index.html">Workbench queue ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["surfacePct"]}%</strong>visible tip (${s["surfaceBillions"]}B)</span>'
        f'<span class="split-Chest"><strong>{s["submergedPct"]}%</strong>submerged (${s["submergedBillions"]}B)</span>'
        f'<span class="split-Shoulders"><strong>{s["submergedToSurfaceRatio"]}×</strong>hidden vs. visible</span></div>'
    )
    mm_macro = "../../../Mental-Map/index.html#sec:economic-growth"
    mm_macro_lbl = "§ 2.3.1 Macroeconomics / Economic Growth"
    metrics = _metrics([
        ("Visible tip (surface)", f"{s['surfacePct']}% of wages", f"~${s['surfaceBillions']}B in direct software, computing & IT roles"),
        ("Submerged Iceberg", f"{s['submergedPct']}% of wages", f"~${s['submergedBillions']:,}B in routine cognitive, admin & analytical tasks"),
        ("Combined exposure", f"{s['combinedPct']}% of wages", "86.1% stays anchored in physical, clinical & licensed human work"),
        ("Hidden multiplier", f"{s['submergedToSurfaceRatio']}× larger", "Why GDP tech share badly understates regional AI disruption"),
    ], with_tooltips=True, mm_href=mm_macro, mm_label=mm_macro_lbl)

    iceberg_legend = (
        '<p class="sports-legend">'
        '<span class="study-key-surface">■ Visible tip (direct tech/computing adoption)</span>'
        '<span class="study-key-submerged">■ Submerged Iceberg (skills-centered cognitive/admin exposure)</span></p>'
    )
    role_legend = '<p class="sports-legend">' + "".join(
        f'<span class="role-key-{i}">■ {_e(f["label"])} ({f["surfacePct"] + f["submergedPct"]:.1f}% AI task overlap)</span>'
        for i, f in enumerate(roles)
    ) + "</p>"

    ind_rows = [
        [
            f'{sec["code"]} · {sec["name"]}',
            f'{sec["employmentShare"]:.1f}%',
            f'{sec["gdpShare"]:.1f}%',
            f'${_num(sec["medianWage"])}',
            f'{sec["surfacePct"]:.1f}%',
            f'{sec["submergedPct"]:.1f}%',
            f'{sec["surfacePct"] + sec["submergedPct"]:.1f}%',
            sec["aiWipeoutRisk"],
            sec["humanMoat"],
        ]
        for sec in industries
    ]
    role_rows = [
        [
            sec["name"],
            *(f'{sec["roles"][f["key"]]}%' for f in roles),
        ]
        for sec in industries
    ]

    reg_buttons = "".join(
        f'<button class="wb-bucket-chip{" is-active" if i == 0 else ""}" type="button" data-region-btn="{_e(r["id"])}">{_e(r["id"])} · {_e(r["name"].split(" (")[0])}</button>'
        for i, r in enumerate(regions)
    )
    first_bars = "".join(
        f'<div class="study-sector-row"><span>{_e(k)}</span><div class="study-sector-track"><div class="study-sector-fill" style="width:{v * 3}%"></div></div><strong>{v}%</strong></div>'
        for k, v in first_reg["sectors"].items()
    )
    inspector = f'''<div class="study-map-layout" data-regions="{_safe_attr_json(regions)}">
      <div class="study-map-col">
        <div class="wb-bucket-bar" role="group" aria-label="Select a regional economy">{reg_buttons}</div>
        {_macro_region_map_svg(regions)}
      </div>
      <aside class="study-inspector" id="macro-region-inspector" aria-live="polite">
        <p class="eyebrow" id="reg-country">{_e(first_reg["country"])} · Regional Economy Inspector (hover / tap parameters)</p>
        <h3 id="reg-name">{_e(first_reg["name"])}</h3>
        <div class="study-reg-kpis">
          {_inspector_param_card("GDP", "reg-gdp", f"${_num(first_reg['gdpBillions'])}B", "Annual regional Gross Domestic Product in billions of USD (BEA / Statistics Canada provincial accounts).", mm_macro, mm_macro_lbl)}
          {_inspector_param_card("Workforce", "reg-workers", f"{first_reg['workersMillions']:.1f}M", "Total employed civilian labor force in millions across all NAICS industries in the region.", mm_macro, mm_macro_lbl)}
          {_inspector_param_card("Visible tip", "reg-surf", f"{first_reg['surfacePct']:.1f}%", "Share of regional wage bill in direct software, cloud, and computing occupations (the visible tip of the AI Iceberg).", mm_macro, mm_macro_lbl)}
          {_inspector_param_card("Submerged", "reg-sub", f"{first_reg['submergedPct']:.1f}%", "Share of regional wage bill in routine administrative, financial, clerical, and analytical tasks inside non-tech sectors.", mm_macro, mm_macro_lbl)}
        </div>
        <h4>Sector composition (% of regional GDP)</h4>
        <div class="study-sector-bars" id="reg-sectors">{first_bars}</div>
        <p class="sports-note" id="reg-sig">{_e(first_reg["signature"])}</p>
      </aside>
    </div>'''

    reg_rows = [
        [
            f'{r["id"]} · {r["name"]}', r["country"], f'${_num(r["gdpBillions"])}B',
            f'{r["workersMillions"]:.1f}M', f'{r["surfacePct"]:.1f}%', f'{r["submergedPct"]:.1f}%',
            f'{r["surfacePct"] + r["submergedPct"]:.1f}%',
            ", ".join(f"{k} {v}%" for k, v in r["sectors"].items()),
        ]
        for r in regions
    ]

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {_hero("Macroeconomics / Economic Growth", "Study 01 · AI & Labor", "Above the water,<br>and <em>beneath</em> it.", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-01 · Grounded in the MIT / Oak Ridge National Laboratory Project Iceberg skill-exposure framework and North American NAICS occupational matrices.</p>
      {_section("01", "The Iceberg split", "Why visible tech jobs are only 2.2% of the story — and 11.7% sits underwater.", "macro-iceberg-title",
                '<p>Headlines track AI through software engineers and data centers — the <strong>2.2%</strong> visible tip. '
                'Project Iceberg maps 32,000+ occupational skills across 923 occupations and finds <strong>11.7%</strong> of total wage value '
                '(~$1.2 trillion) in submerged cognitive, administrative, financial, and analytical tasks inside non-tech industries.</p>'
                + iceberg_legend + _macro_iceberg_svg(industries)
                + metrics
                + _table("NAICS sectors ranked by AI wage exposure, showing the tasks most vulnerable to automation and the human moat.",
                         ["Sector", "Jobs %", "GDP %", "Median wage", "Visible %", "Submerged %", "Total %", "High wipeout-risk tasks", "Durable human moat"],
                         ind_rows, "macro-industry-table"))}
      {_section("02", "Inside the industries", "How the six occupational role families divide every sector.", "macro-roles-title",
                '<p>An industry is not a single job. Manufacturing is 54% skilled trades and plant operators (low AI overlap), '
                'but 25% analytical engineering and clerical procurement/scheduling (high submerged overlap). Healthcare is 56% hands-on clinical care, '
                'yet 18% administrative billing, coding, and intake.</p>'
                + role_legend + _macro_roles_svg(industries, roles)
                + _table("Occupational role breakdown (% of sector workforce).",
                         ["Sector", *(f["label"] for f in roles)], role_rows, "macro-roles-table"))}
      {_section("03", "Interactive economy map", "Click any North American region to inspect its sector mix and Iceberg ratio.", "macro-map-title",
                '<p>Select a province or US region on the map or buttons below to compare its GDP sector composition against its visible and submerged AI exposure.</p>'
                + inspector
                + _table("North American regional economies.",
                         ["Region", "Country", "GDP (USD)", "Workers", "Visible %", "Submerged %", "Combined %", "Sector mix"],
                         reg_rows, "macro-region-table"))}
      <section class="sports-section sports-method" aria-labelledby="macro-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="macro-method-title">Sources, LaTeX paper, and downloads.</h2>
        <ul>
          <li><strong>Framework:</strong> MIT &amp; Oak Ridge National Laboratory (ORNL), <em>The Iceberg Index: Measuring Skills-centered Exposure in the AI Economy</em> (151M workers, 923 occupations, 32,000+ skills).</li>
          <li><strong>Sector &amp; role matrices:</strong> Synthesized from BLS Occupational Employment and Wage Statistics (OEWS), BEA GDP-by-Industry, and Statistics Canada Labour Force Survey NAICS tables.</li>
          <li><strong>Dedicated LaTeX paper:</strong> Read or download the compiled article at <a href="Paper/index.html">Economic Growth: The AI Iceberg Paper &amp; PDF ↗</a>.</li>
        </ul>
        {_downloads(3, [
            ("studies-macro.json", "Macro Iceberg study · JSON"),
            ("studies-macro-industries.csv", "12 NAICS industries · CSV"),
            ("studies-macro-regions.csv", "12 Regional economies · CSV"),
        ])}
      </section>
    </main>'''


# ---- Study 2 View: October 19, 2026 Alberta Referendum -------------------------------

def _alberta_questions_svg(questions: list[dict[str, Any]]) -> str:
    """Diverging 100% bar chart of all 10 ballot questions with the 50% majority line."""
    height = 75 + len(questions) * 34
    left, width = 310.0, 520.0
    mid = left + width / 2
    parts = [
        f'<line class="diet-target" x1="{mid:.1f}" x2="{mid:.1f}" y1="30" y2="{height - 24}"/>'
        f'<text class="athletics-label diet-target-label" x="{mid:.1f}" y="20" text-anchor="middle">50% majority threshold</text>'
    ]
    for tick in (0, 25, 50, 75, 100):
        tx = left + tick / 100.0 * width
        parts.append(f'<text x="{tx:.1f}" y="{height - 8}" text-anchor="middle">{tick}%</text>')
    for idx, q in enumerate(questions):
        y = 36 + idx * 34
        w_for = q["forPct"] / 100.0 * width
        w_against = q["againstPct"] / 100.0 * width
        cls = "ab-q-remain" if q["number"] == 10 else ("ab-q-pass" if q["forPct"] > 50 else "ab-q-fail")
        label_for = "Remain" if q["number"] == 10 else "For"
        label_ag = "Referendum" if q["number"] == 10 else "Against"
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">Q{q["number"]} · {_e(q["shortTitle"][:36])}</text>'
            f'<rect class="{cls}" x="{left:.1f}" y="{y:.1f}" width="{w_for:.1f}" height="21">'
            f'<title>Q{q["number"]} {label_for}: {q["forPct"]:.2f}% ({_num(q["forVotes"])} votes)</title></rect>'
            f'<rect class="ab-q-against" x="{left + w_for:.1f}" y="{y:.1f}" width="{w_against:.1f}" height="21">'
            f'<title>Q{q["number"]} {label_ag}: {q["againstPct"]:.2f}% ({_num(q["againstVotes"])} votes)</title></rect>'
            f'<text class="role-seg-label" x="{left + 8:.1f}" y="{y + 15:.1f}">{label_for} {q["forPct"]:.1f}%</text>'
            f'<text class="role-seg-label" x="{left + width - 8:.1f}" y="{y + 15:.1f}" text-anchor="end">{label_ag} {q["againstPct"]:.1f}%</text>'
        )
    return _chart(
        "alberta-ballot-questions",
        "All 10 October 19, 2026 Alberta Referendum questions: For/Remain vs. Against/Referendum",
        "Horizontal 100% bars for Questions 1 to 10. Questions 1 to 5 (non-constitutional immigration and voter ID) passed; Questions 6 to 9 (constitutional amendments) failed; Question 10 voted 74.95% Remain.",
        "".join(parts),
        height=height,
    )


def _alberta_demographics_svg(demographics: list[dict[str, Any]]) -> str:
    """Horizontal stacked bars comparing Question 10 Remain vs. Option 2 across demographic groups."""
    height = 70 + len(demographics) * 32
    left, width = 275.0, 440.0
    parts = []
    for tick in range(0, 101, 25):
        tx = left + tick / 100.0 * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">{tick}%</text>'
        )
    for idx, row in enumerate(demographics):
        y = 38 + idx * 32
        w_rem = row["remainPct"] / 100.0 * width
        w_opt = row["option2Pct"] / 100.0 * width
        w_oth = row["otherPct"] / 100.0 * width
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(row["group"])}</text>'
            f'<rect class="ab-q-remain" x="{left:.1f}" y="{y:.1f}" width="{w_rem:.1f}" height="20">'
            f'<title>{_e(row["group"])} · Remain in Canada: {row["remainPct"]:g}%</title></rect>'
            f'<rect class="study-bar-submerged" x="{left + w_rem:.1f}" y="{y:.1f}" width="{w_opt:.1f}" height="20">'
            f'<title>{_e(row["group"])} · Option 2 (separation referendum process): {row["option2Pct"]:g}%</title></rect>'
            f'<rect class="ab-q-undecided" x="{left + w_rem + w_opt:.1f}" y="{y:.1f}" width="{w_oth:.1f}" height="20">'
            f'<title>{_e(row["group"])} · Undecided / skip: {row["otherPct"]:g}%</title></rect>'
            f'<text class="role-seg-label" x="{left + 8:.1f}" y="{y + 14:.1f}">{row["remainPct"]:g}% Remain</text>'
            f'<text class="athletics-label" x="{left + w_rem + w_opt + w_oth + 8:.1f}" y="{y + 14:.1f}">{row["option2Pct"]:g}% Opt 2</text>'
        )
    return _chart(
        "alberta-demographic-splits",
        "Question 10 demographic breakdown: Remain vs. Option 2 by region, party, age, and ballot channel",
        "Stacked bars compare Remain in Canada (green/cyan), Option 2 separation process (amber), and undecided/skip (muted) across 14 demographic slices.",
        "".join(parts),
        height=height,
    )


def alberta_study_body(data: dict[str, Any], lead: str = "") -> str:
    """Render the October 19, 2026 Alberta Referendum & Demographic Vote Anatomy study."""
    s = data["summary"]
    questions = data["questions"]
    demographics = data["demographics"]
    motives = data["motives"]

    deck = (
        f"On October 19, 2026, Albertans cast {_num(s['q10TotalVotes'])} ballots across 10 questions — "
        f"passing all 5 immigration & voter-ID proposals, rejecting all 4 constitutional amendments, "
        f"and voting {s['q10RemainPct']}% to {s['q10Option2Pct']}% to remain in Canada."
    )
    actions = (
        '<a class="button primary" href="Paper/index.html">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#alberta-demographics-title">Demographic breakdown</a>'
        '<a class="button ghost" href="../../../Workbench/index.html">Workbench queue ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["q10RemainPct"]}%</strong>Remain (Q10)</span>'
        f'<span class="split-Chest"><strong>5 / 5</strong>Q1–Q5 passed</span>'
        f'<span class="split-Shoulders"><strong>0 / 4</strong>Q6–Q9 passed</span></div>'
    )
    metrics = _metrics([
        ("Question 10 · Remain", f"{s['q10RemainPct']}%", f"{_num(s['q10RemainVotes'])} votes vs. {_num(s['q10Option2Votes'])} ({s['q10Option2Pct']}%)"),
        ("Q1–Q5 · Immigration & ID", "5 of 5 passed", "52.3% to 59.8% For (non-binding provincial bills)"),
        ("Q6–Q9 · Constitutional", "0 of 4 passed", "46.8% to 49.8% For — voters balked at constitutional fights"),
        ("True independence core", f"~{s['directIndependencePct']:g}% of voters", "Only 32% of Option 2 voters cite independence as primary goal"),
    ], with_tooltips=True, mm_href="../../../Mental-Map/index.html#sec:public-policy", mm_label="§ 2.1.5 Law & Policy / Public Policy")

    q_rows = [
        [
            f'Q{q["number"]}', q["category"], q["shortTitle"],
            f'{_num(q["forVotes"])} ({q["forPct"]:.2f}%)',
            f'{_num(q["againstVotes"])} ({q["againstPct"]:.2f}%)',
            _num(q["forVotes"] + q["againstVotes"]),
            q["outcome"],
        ]
        for q in questions
    ]

    dims = ["All", "Region", "Provincial Party", "2025 Federal Vote", "Age & Turnout", "Voting Channel"]
    dim_chips = '<div class="wb-bucket-bar" role="group" aria-label="Filter demographics">' + "".join(
        f'<button class="wb-bucket-chip{" is-active" if i == 0 else ""}" type="button" data-ab-dim="{_e(d)}">{_e(d)}</button>'
        for i, d in enumerate(dims)
    ) + "</div>"

    demo_tbody = "".join(
        f'<tr data-ab-row="{_e(d["dimension"])}"><th scope="row">{_e(d["group"])}</th>'
        f'<td>{_e(d["dimension"])}</td><td><strong>{d["remainPct"]:g}%</strong></td>'
        f'<td>{d["option2Pct"]:g}%</td><td>{d["otherPct"]:g}%</td>'
        f'<td>{_e(d["turnoutOrShare"])}</td><td>{_e(d["source"])}</td></tr>'
        for d in demographics
    )
    demo_table = (
        '<div class="sports-table-wrap" role="region" aria-label="Demographic breakdown on Question 10" tabindex="0">'
        '<table id="alberta-demographics-table"><caption>Question 10 vote intention &amp; exit-poll demographics</caption>'
        '<thead><tr><th scope="col">Demographic group</th><th scope="col">Dimension</th>'
        '<th scope="col">Remain %</th><th scope="col">Option 2 %</th><th scope="col">Undecided %</th>'
        '<th scope="col">Turnout / identity note</th><th scope="col">Source</th></tr></thead>'
        f'<tbody id="ab-demo-body">{demo_tbody}</tbody></table></div>'
    )

    motive_rows = [
        ["Remain in Canada (74.95%)", m["reason"], f'{m["pct"]}%'] for m in motives["remain"]
    ] + [
        ["Option 2 · Referendum process (25.05%)", m["reason"], f'{m["pct"]}%'] for m in motives["option2"]
    ]

    mm_ab = "../../../Mental-Map/index.html#sec:public-policy"
    mm_ab_lbl = "§ 2.1.5 Law & Policy / Public Policy"
    ab_inspector = (
        '<aside class="study-inspector" style="margin: 14px 0 18px;" aria-label="Referendum Parameter Inspector">'
        '<p class="eyebrow">Referendum Threshold &amp; Coalition Parameter Inspector (hover / tap parameters)</p>'
        '<h3>October 19, 2026 Ballot Structure &amp; Effective Separatism Core</h3>'
        '<div class="study-reg-kpis">'
        + _inspector_param_card("Majority Threshold τ*", "ab-tau", "50.0% + 1", "Simple majority threshold required under the Alberta Referendum Act for non-constitutional provincial policy questions (Q1–Q5 all cleared τ*).", mm_ab, mm_ab_lbl)
        + _inspector_param_card("Constitutional Hurdle", "ab-const", "38/50 + 7/10", "Section 38(1) Constitution Act, 1982 amendment formula requiring Parliament plus 7 provinces representing ≥50% of population (Q6–Q9 all failed even the provincial 50% bar).", mm_ab, mm_ab_lbl)
        + _inspector_param_card("Leverage Share λ", "ab-lev", "68.0% of Opt 2", "Share of Option 2 voters who voted to gain fiscal bargaining leverage or a direct vote rather than actual separation from Canada.", mm_ab, mm_ab_lbl)
        + _inspector_param_card("True Exit Core s*", "ab-core", "18.0% overall", "Effective province-wide share desiring full independence: s* ≈ Option 2 share (25.05%) × direct exit share + undecided lean (~18%).", mm_ab, mm_ab_lbl)
        + '</div></aside>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {_hero("Law & Policy / Public Policy", "Study 02 · Referendum Anatomy", "Three ballots<br>in <em>one.</em>", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-02 · Official Elections Alberta ballot counts (Oct 19, 2026) paired with Abacus Data (n=1,021) and Research Co. pre-vote (n=811) &amp; exit-poll (n=601) demographic cross-tabs.</p>
      {_section("01", "The 10-question split", "Voters said yes to provincial immigration & ID rules, no to constitutional amendments, and 3-to-1 to stay in Canada.", "alberta-questions-title",
                '<p>The October 19, 2026 ballot was not a single referendum: it bundled three distinct propositions, and the electorate split them surgically. '
                'Every non-constitutional immigration and voter-ID question passed (52.3%–59.8%); every constitutional amendment failed just below 50% (46.8%–49.8%); '
                'and Question 10 rejected commencing a binding separation referendum by nearly fifty points (74.95% to 25.05%).</p>'
                + '<p class="sports-legend"><span class="study-key-surface">■ Q10 Remain (74.95%)</span><span class="ab-key-pass">■ Q1–Q5 Passed (&gt;50%)</span>'
                '<span class="study-key-submerged">■ Q6–Q9 Failed (&lt;50%)</span><span class="ab-key-against">■ Against / Option 2</span></p>'
                + _alberta_questions_svg(questions)
                + metrics
                + ab_inspector
                + _table("Official Elections Alberta results across all 10 ballot questions.",
                         ["Q#", "Block", "Question", "For / Remain", "Against / Option 2", "Total ballots", "Result"],
                         q_rows, "alberta-questions-table"))}
      {_section("02", "How each demographic voted", "Region, party coalition, age, turnout, and early mail ballots.", "alberta-demographics-title",
                '<p>Remain won every region of the province — including Rural Alberta (57% Remain vs. 35% Option 2) — while Edmonton (77%) and Calgary (75%) anchored the 3-to-1 margin. '
                'The sharpest fracture ran straight through the governing United Conservative Party: UCP supporters split 52% Option 2 to 44% Remain, whereas NDP voters backed Remain 93% to 4%.</p>'
                + _alberta_demographics_svg(demographics)
                + dim_chips + demo_table)}
      {_section("03", "Inside the two coalitions", "Why a 25% Option 2 vote is ~18% actual separatism — and why Option 2 voters were the most optimistic.", "alberta-coalitions-title",
                '<p>Abacus Data and Research Co. exit polling show that neither camp was monolithic:</p>'
                '<ul>'
                '<li><strong>Leverage vs. Exit inside Option 2:</strong> Only 32% of Option 2 voters named independence as their main reason; '
                '23% wanted a better fiscal deal inside Canada, 22% believed Albertans deserved a direct vote, and 19% wanted to send Ottawa a message. '
                'Asked directly about an independent Alberta, support sits at ~18% province-wide.</li>'
                '<li><strong>The 47-point Canadian identity gap:</strong> 76% of Remain voters feel strongly attached to Canada (and 51% to Alberta); '
                'among Option 2 voters, only 21% feel strongly attached to Canada versus 68% to Alberta. Still, 65% of all referendum voters call themselves '
                '“Canadians first, Albertans second” (versus 22% “Albertans first”).</li>'
                '<li><strong>The age &amp; optimism twist:</strong> Voters 60+ turned out at 85% (vs. 38% under 30) and held equal 71% attachment to both Canada and Alberta. '
                'Meanwhile, 18–34 voters were most open to US statehood (21% vs. 6% among 55+), and Option 2 voters were <em>more</em> likely than Remain voters '
                'to say Alberta\'s best days are ahead (59% vs. 44%).</li>'
                '</ul>'
                + _table("Primary voter motivation inside the Remain and Option 2 coalitions (Abacus Data Oct 2026).",
                         ["Coalition", "Primary stated motivation", "Share of coalition"], motive_rows, "alberta-motives-table"))}
      <section class="sports-section sports-method" aria-labelledby="alberta-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="alberta-method-title">Sources, LaTeX paper, and downloads.</h2>
        <ul>
          <li><strong>Ballot counts:</strong> Elections Alberta official October 19, 2026 referendum count (Questions 1–9 at 97%–97.6% reporting; Question 10 at 99.98% reporting, 2,070,634 ballots).</li>
          <li><strong>Demographic cross-tabs:</strong> Abacus Data Alberta survey (Oct 7–13, 2026, n=1,021, MoE ±3.1%), Research Co. final pre-referendum survey (Oct 16–18, 2026, n=811, MoE ±3.6%), and Research Co. provincial exit poll (Oct 19–20, 2026, n=601 referendum voters, MoE ±4.0%).</li>
          <li><strong>Dedicated LaTeX paper:</strong> Read or download the compiled article at <a href="Paper/index.html">Public Policy: 2026 Alberta Referendum Paper &amp; PDF ↗</a>.</li>
        </ul>
        {_downloads(3, [
            ("studies-alberta.json", "Alberta referendum study · JSON"),
            ("studies-alberta-questions.csv", "10 Ballot questions · CSV"),
            ("studies-alberta-demographics.csv", "Demographic cross-tabs · CSV"),
        ])}
      </section>
    </main>'''


# ---- Study 3 View: ST-06 Gas Price Collusion & Oligopoly Supergames -------------------

def _gas_country_svg(countries: list[dict[str, Any]]) -> str:
    """Stacked horizontal bar chart decomposing retail pump price into Wholesale TGP, Sovereign Tax, and Ex-Tax Retail Markup."""
    ordered = sorted(countries, key=lambda c: c["markupUsdL"], reverse=True)
    height = 74 + len(ordered) * 34
    max_usd = 2.60
    left, width = 275.0, 415.0
    parts = []
    for tick_tenths in range(0, 27, 5):
        val = tick_tenths / 10.0
        tx = left + val / max_usd * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="32" y2="{height - 28}"/>'
            f'<text x="{tx:.1f}" y="22" text-anchor="middle">${val:.2f}/L</text>'
        )
    for idx, row in enumerate(ordered):
        y = 40 + idx * 34
        w_wh = row["wholesaleUsdL"] / max_usd * width
        w_mk = row["markupUsdL"] / max_usd * width
        w_tx = row["taxUsdL"] / max_usd * width
        label = row["country"].split(" (")[0]
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(row["code"])} · {_e(label)} (CR4 {row["cr4Pct"]}%)</text>'
            f'<rect class="study-bar-surface" x="{left:.1f}" y="{y:.1f}" width="{w_wh:.1f}" height="21">'
            f'<title>{_e(row["country"])} · Wholesale Rack/TGP: ${row["wholesaleUsdL"]:.2f}/L</title></rect>'
            f'<rect class="study-bar-submerged" x="{left + w_wh:.1f}" y="{y:.1f}" width="{w_mk:.1f}" height="21">'
            f'<title>{_e(row["country"])} · Ex-Tax Retail Oligopoly Markup: ${row["markupUsdL"]:.2f}/L ({row["markupUsdL"]*100:.0f} c/L)</title></rect>'
            f'<rect class="ab-q-against" x="{left + w_wh + w_mk:.1f}" y="{y:.1f}" width="{w_tx:.1f}" height="21">'
            f'<title>{_e(row["country"])} · Sovereign Tax Wedge (Excise + Carbon + VAT): ${row["taxUsdL"]:.2f}/L</title></rect>'
            f'<text class="athletics-label" x="{left + w_wh + w_mk + w_tx + 8:.1f}" y="{y + 15:.1f}">${row["pumpUsdL"]:.2f}/L ({row["markupUsdL"]*100:.0f}c markup)</text>'
        )
    return _chart(
        "gas-country-decomposition",
        "Cross-country pump price decomposition ($ USD/L): Wholesale TGP vs. Ex-Tax Oligopoly Markup vs. Tax Wedge",
        "Countries ranked by Ex-Tax Retail & Distribution Markup (amber). High European headline pump prices are 55%–62% sovereign tax (purple), but concentrated 3-to-5 firm oligopolies (DE, UK, AU, CL, CA) extract 24–28 c/L ex-tax markups vs. 12 c/L in unconcentrated US big-box markets.",
        "".join(parts),
        height=height,
    )


def _gas_rockets_feathers_svg(pass_through: list[dict[str, Any]]) -> str:
    """Athletics-style trajectory chart of Asymmetric Pass-Through (Rockets & Feathers) and Edgeworth Cycles."""
    height = 330
    left, right, top, bottom = 68.0, 855.0, 34.0, 286.0
    width = right - left
    plot_h = bottom - top
    parts = []
    for pct in (0, 25, 50, 75, 100):
        y = bottom - (pct / 100.0) * plot_h
        parts.append(
            f'<line class="chart-grid" x1="{left:.1f}" x2="{right:.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
            f'<text x="{left - 10:.1f}" y="{y + 4:.1f}" text-anchor="end">{pct}%</text>'
        )
    for d in (0, 3, 7, 14, 21, 28):
        x = left + (d / 28.0) * width
        parts.append(
            f'<line class="chart-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top:.1f}" y2="{bottom:.1f}"/>'
            f'<text x="{x:.1f}" y="{bottom + 20:.1f}" text-anchor="middle">Day {d}</text>'
        )

    def pt_xy(day: float, pct: float) -> tuple[float, float]:
        return left + (day / 28.0) * width, bottom - (pct / 100.0) * plot_h

    rocket_pts = [pt_xy(r["day"], r["rocketPassPct"]) for r in pass_through]
    feather_pts = [pt_xy(r["day"], r["featherPassPct"]) for r in pass_through]
    edge_pts = [pt_xy(r["day"], r["edgeworthMarginCpl"] * 4.0) for r in pass_through]
    coll_pts = [pt_xy(r["day"], r["collusiveMarginCpl"] * 4.0) for r in pass_through]

    poly_coords = rocket_pts + list(reversed(feather_pts))
    wedge_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly_coords)
    parts.append(f'<polygon points="{wedge_str}" fill="#f7ab6524" stroke="none"/>')

    r_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in rocket_pts)
    f_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in feather_pts)
    e_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in edge_pts)
    c_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in coll_pts)

    parts.append(f'<polyline fill="none" stroke="#f28b82" stroke-width="3" points="{r_line}"/>')
    parts.append(f'<polyline fill="none" stroke="#69d4cf" stroke-width="3" points="{f_line}"/>')
    parts.append(f'<polyline fill="none" stroke="#bba1ff" stroke-width="2" stroke-dasharray="5 4" points="{e_line}"/>')
    parts.append(f'<polyline fill="none" stroke="#8fe0a8" stroke-width="2.2" stroke-dasharray="2 3" points="{c_line}"/>')

    for r, (rx, ry), (fx, fy) in zip(pass_through, rocket_pts, feather_pts):
        parts.append(
            f'<circle cx="{rx:.1f}" cy="{ry:.1f}" r="4" fill="#f28b82">'
            f'<title>Day {r["day"]} · Rocket upward pass-through: {r["rocketPassPct"]:g}%</title></circle>'
            f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="4" fill="#69d4cf">'
            f'<title>Day {r["day"]} · Feather downward pass-through: {r["featherPassPct"]:g}% (Edgeworth margin: {r["edgeworthMarginCpl"]} c/L vs Collusive: {r["collusiveMarginCpl"]} c/L)</title></circle>'
        )
    parts.append(
        '<text class="athletics-label" x="215" y="64">Rocket (+10 c/L wholesale jump: 93% passed in 3 days)</text>'
        '<text class="athletics-label" x="380" y="195">Feather (-10 c/L wholesale drop: slow 24-day decay = tacit rent wedge)</text>'
    )
    return _chart(
        "gas-rockets-feathers-cycles",
        "Asymmetric pass-through ('Rockets & Feathers') and Edgeworth sawtooth cycles over 28 days",
        "Coral curve tracks cumulative retail pass-through of a +10 c/L wholesale shock (Rocket); cyan curve tracks pass-through of a -10 c/L drop (Feather). Dashed purple sawtooth shows competitive Edgeworth price cycles vs. green sticky focal-point collusion.",
        "".join(parts),
        height=height,
    )


def _gas_supergame_svg(industries: list[dict[str, Any]]) -> str:
    """Comparison bar chart of Effective Discount Factor (delta) vs. Critical Collusion Threshold (delta* = 1 - 1/N)."""
    height = 74 + len(industries) * 36
    left, width = 280.0, 390.0
    parts = []
    for tick in (0, 25, 50, 75, 100):
        val = tick / 100.0
        tx = left + val * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">δ = {val:.2f}</text>'
        )
    for idx, ind in enumerate(industries):
        y = 38 + idx * 36
        w_eff = ind["deltaEff"] * width
        x_star = left + ind["deltaStar"] * width
        collusive = ind["deltaEff"] >= ind["deltaStar"]
        bar_cls = "study-bar-submerged" if collusive else "study-bar-surface"
        verdict = f'SPNE ({ind["slack"]:+.2f})' if collusive else f'Comp. ({ind["slack"]:+.2f})'
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(ind["industry"][:34])}</text>'
            f'<rect class="{bar_cls}" x="{left:.1f}" y="{y:.1f}" width="{w_eff:.1f}" height="20">'
            f'<title>{_e(ind["industry"])} · Effective δ = {ind["deltaEff"]:.2f} vs Critical δ* = {ind["deltaStar"]:.2f} ({_e(ind["equilibrium"])})</title></rect>'
            f'<line class="diet-target" x1="{x_star:.1f}" x2="{x_star:.1f}" y1="{y - 3:.1f}" y2="{y + 23:.1f}"/>'
            f'<circle cx="{x_star:.1f}" cy="{y + 10:.1f}" r="4.5" fill="#ffffff" stroke="#0d101b" stroke-width="1.5">'
            f'<title>Critical threshold δ* = 1 - 1/N = {ind["deltaStar"]:.2f} (N = {ind["firmsN"]:g})</title></circle>'
            f'<text class="athletics-label" x="{left + max(w_eff, ind["deltaStar"] * width) + 8:.1f}" y="{y + 15:.1f}">δ={ind["deltaEff"]:.2f} / δ*={ind["deltaStar"]:.2f} · {verdict}</text>'
        )
    return _chart(
        "gas-supergame-industries",
        "Repeated Bertrand supergame incentive-compatibility: Effective δ vs. critical threshold δ* = 1 − 1/N",
        "Bars show effective discount factor δ = exp(−rT) (amber = Collusive SPNE where δ ≥ δ*; cyan = Competitive Bertrand where δ < δ*). White markers indicate each industry's critical threshold δ* = 1 − 1/N.",
        "".join(parts),
        height=height,
    )


def gas_study_body(data: dict[str, Any], lead: str = "", *, is_subtab: bool = False) -> str:
    """Render ST-06: Gas Price Collusion, Asymmetric Pass-Through, and Oligopoly Supergames in Game Theory."""
    s = data["summary"]
    countries = data["countries"]
    pass_through = data["passThrough"]
    industries = data["industries"]
    first_ind = industries[0]
    up_root = "../../../../" if is_subtab else "../../../"
    paper_href = "../Paper/index.html" if is_subtab else "Paper/index.html"
    overview_href = "../index.html" if is_subtab else "index.html"
    subtab_href = "index.html" if is_subtab else "Gas-Price-Collusion/index.html"

    deck = (
        f"Decomposing retail pump prices across {s['countriesAnalyzed']} countries into crude/wholesale rack cost, sovereign tax wedges, "
        f"and ex-tax oligopoly markups — and modeling why street-sign transparency, inelastic market demand, and AI pricing sustain tacit collusion."
    )
    actions = (
        f'<a class="button primary" href="{paper_href}">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#gas-supergame-title">Supergame industry model</a>'
        f'<a class="button ghost" href="{up_root}Mental-Map/index.html#sec:game-theory">Mental Map § 2.2.4 ↗</a>'
        f'<a class="button ghost" href="{up_root}Workbench/index.html">Workbench (ST-06) ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["oligopolyMarkupCpl"]}</strong>oligopoly ex-tax spread</span>'
        f'<span class="split-Chest"><strong>+{s["aiDuopolyMarginBoostPct"]}%</strong>AI duopoly margin jump</span>'
        f'<span class="split-Shoulders"><strong>r = {s["cr4MarkupCorrelation"]}</strong>CR4 vs. markup</span></div>'
    )
    tab_bar = (
        '<nav class="wb-bucket-bar" aria-label="Game Theory destination tabs" style="margin: 14px 0 6px;">'
        f'<a class="wb-bucket-chip{" is-active" if not is_subtab else ""}" href="{overview_href}">📊 Game Theory · Gas Price Collusion Dashboard</a>'
        f'<a class="wb-bucket-chip{" is-active" if is_subtab else ""}" href="{subtab_href}">⛽ Gas Price Collusion Tab (ST-06)</a>'
        f'<a class="wb-bucket-chip" href="{paper_href}">📄 Compiled LaTeX Paper &amp; PDF</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Mental-Map/index.html#sec:game-theory">🧠 Mental Map § 2.2.4</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Workbench/index.html">🗄️ Workbench Queue</a>'
        '</nav>'
    )
    mm_gas = f"{up_root}Mental-Map/index.html#sec:game-theory"
    mm_gas_lbl = "§ 2.2.4 Microeconomics / Game Theory"
    metrics = _metrics([
        ("Oligopoly ex-tax spread", s["oligopolyMarkupCpl"], f"vs. {s['competitiveMarkupCpl']} in unconcentrated US big-box markets (r = {s['cr4MarkupCorrelation']})"),
        ("AI pricing duopoly boost", f"+{s['aiDuopolyMarginBoostPct']}% margin", "German MTS-K station panel when both local rivals adopt AI pricing (Assad et al. 2024)"),
        ("Focal signaling boost", f"+{s['focalSignalingBoostPct']}% margin", "Perth FuelWatch after BP ended Edgeworth price cycles (Byrne & de Roos 2019)"),
        ("Rockets vs. Feathers", f"{s['rocketHalfLifeDays']}d vs. {s['featherHalfLifeDays']}d half-life", f"-{s['stationSwitchElasticityPct']}% station volume for a 2 c/L unilateral price gap"),
    ], with_tooltips=True, mm_href=mm_gas, mm_label=mm_gas_lbl)

    country_rows = [
        [
            f'{c["code"]} · {c["country"]}',
            f'${c["pumpUsdL"]:.2f}/L',
            f'${c["wholesaleUsdL"]:.2f}/L',
            f'${c["taxUsdL"]:.2f}/L ({c["taxUsdL"]/c["pumpUsdL"]*100:.0f}%)',
            f'${c["markupUsdL"]:.2f}/L ({c["markupUsdL"]*100:.0f} c/L)',
            f'{c["lernerExTaxPct"]:.1f}%',
            f'{c["cr4Pct"]}% (HHI {c["hhi"]})',
            c["dominantFirms"],
            c["regime"],
        ]
        for c in countries
    ]

    ind_chips = "".join(
        f'<button class="wb-bucket-chip{" is-active" if i == 0 else ""}" type="button" data-gas-ind-btn="{_e(ind["id"])}">{_e(ind["id"])} · {_e(ind["industry"].split(" (")[0])}</button>'
        for i, ind in enumerate(industries)
    )
    inspector = f'''<div class="study-map-layout" data-gas-industries="{_safe_attr_json(industries)}">
      <div class="study-map-col">
        <div class="wb-bucket-bar" role="group" aria-label="Select an industry supergame">{ind_chips}</div>
        {_gas_supergame_svg(industries)}
      </div>
      <aside class="study-inspector" id="gas-supergame-inspector" aria-live="polite">
        <p class="eyebrow" id="gas-ind-eq">{_e(first_ind["equilibrium"])} · Repeated Bertrand Inspector (hover / tap parameters)</p>
        <h3 id="gas-ind-name">{_e(first_ind["industry"])}</h3>
        <div class="study-reg-kpis">
          {_inspector_param_card("Effective δ", "gas-ind-deff", f"{first_ind['deltaEff']:.2f}", "Effective discount factor δ = exp(−rT) measuring patience and retaliation speed. Because street signs and AI pricing detect cuts in seconds (T → 0), δ approaches 1.0.", mm_gas, mm_gas_lbl)}
          {_inspector_param_card("Critical δ*", "gas-ind-dstar", f"{first_ind['deltaStar']:.2f}", "Critical defection threshold δ* = (π_deviate − π_collude) / (π_deviate − π_punish) ≈ 1 − 1/N. Tacit collusion is a Subgame Perfect Nash Equilibrium (SPNE) if and only if Effective δ ≥ Critical δ*.", mm_gas, mm_gas_lbl)}
          {_inspector_param_card("Local Firms N", "gas-ind-n", f"{first_ind['firmsN']:g}", "Effective number of symmetric competing firms in the local pricing cluster (N ≈ 1/HHI). Fewer competitors lower δ* = 1 − 1/N, making tacit coordination much easier to sustain.", mm_gas, mm_gas_lbl)}
          {_inspector_param_card("Detection Lag T", "gas-ind-lag", f"{first_ind['detectionLagHours']:g} hr", "Hours required for rival firms to detect a price cut and match it. Instant street-sign/API transparency shrinks T → 0, eliminating the temporary volume gain from cheating.", mm_gas, mm_gas_lbl)}
        </div>
        <h4>Structural Game-Theory Attributes (hover / tap for definition)</h4>
        <div class="study-sector-bars">
          {_inspector_attr_row("Product homogeneity", "gas-ind-homog", first_ind["homogeneity"], "Physical substitutability across rivals. Standardized 87-octane fuel is chemically identical, so a 2 c/L gap shifts 36% of station volume—making punishment price wars devastating (π_punish → 0).", mm_gas, mm_gas_lbl)}
          {_inspector_attr_row("Price transparency", "gas-ind-vis", first_ind["priceVisibility"], "Observability of rival transaction prices. Public street signs and mandatory government portals allow zero-lag monitoring, whereas secret B2B NDA discounts prevent tacit coordination.", mm_gas, mm_gas_lbl)}
        </div>
        <p class="sports-note" id="gas-ind-why">{_e(first_ind["whyMechanism"])}</p>
      </aside>
    </div>'''

    ind_rows = [
        [
            ind["industry"],
            f'{ind["firmsN"]:g}',
            f'{ind["detectionLagHours"]:g} hr',
            f'{ind["deltaStar"]:.2f}',
            f'{ind["deltaEff"]:.2f}',
            f'{ind["slack"]:+.2f}',
            ind["homogeneity"],
            ind["priceVisibility"],
            ind["equilibrium"],
        ]
        for ind in industries
    ]

    pandas_box = (
        '<details class="wb-schema-details" open>'
        '<summary>🐍 View reproducible Pandas analysis script (<code>gas_price_collusion_pandas.py</code>)</summary>'
        f'<pre class="wb-bars" style="padding:14px; border:1px solid #69d4cf44; border-radius:8px; background:#080b14; overflow-x:auto;"><code>{_e(data["pandasScript"])}</code></pre>'
        '</details>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {tab_bar}
      {_hero("Microeconomics / Game Theory", "Study ST-06 · Gemini 4 Argon + Pandas", "Why gas prices<br><em>feather</em> down.", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-06 · Generated with <strong>{_e(data["model"])}</strong> · Grounded in IEA Energy Prices &amp; Taxes, German MTS-K (Assad et al. 2024, <em>JPE</em>), Western Australia FuelWatch (Byrne &amp; de Roos 2019, <em>AER</em>), UK CMA Road Fuel Reports (2023–2025), Canadian Cartel Records (Clark &amp; Houde 2013/2014), and Chilean CNE (Luco 2019, <em>AEJ: Microeconomics</em>).</p>
      {_section("01", "Pump price decomposition", "Separating sovereign fuel taxes from oligopoly ex-tax retail markups across 12 countries.", "gas-country-title",
                '<p>Raw international pump comparisons confuse fiscal taxation with corporate pricing power. In Denmark ($2.35/L) and the Netherlands ($2.26/L), '
                'excise, carbon, and VAT taxes account for over 60% of the retail price. However, once we strip out taxes and wholesale Terminal Gate Prices (TGP) using Pandas, '
                'a stark industrial-organization pattern emerges: countries where 3 to 5 vertically integrated refiner-marketers or supermarket chains control 65%–89% of stations '
                '(Germany, the UK, Australia, Chile, and Canada) sustain ex-tax retail markups of <strong>24 to 28 cents/L</strong> — more than double the <strong>12 cents/L</strong> '
                'spread in unconcentrated US markets anchored by high-volume maverick discounters (Costco, QuikTrip, Wawa).</p>'
                + '<p class="sports-legend"><span class="study-key-surface">■ Wholesale Crude &amp; Refining TGP ($/L)</span>'
                '<span class="study-key-submerged">■ Ex-Tax Retail &amp; Oligopoly Markup Spread ($/L)</span>'
                '<span class="ab-key-against">■ Sovereign Tax Wedge (Excise + Carbon + VAT)</span></p>'
                + _gas_country_svg(countries)
                + metrics
                + _table("Cross-country gasoline price decomposition ($ USD/L), Top-4 firm concentration (CR4), HHI, and empirical collusion regime.",
                         ["Country", "Pump $/L", "Wholesale TGP", "Tax wedge", "Ex-tax markup", "Ex-tax Lerner %", "CR4 / HHI", "Dominant firms", "Empirical regime"],
                         country_rows, "gas-country-table"))}
      {_section("02", "Rockets, feathers & Edgeworth cycles", "How tacit focal points and AI pricing replace price wars with asymmetric pass-through.", "gas-cycles-title",
                '<p>In an oligopoly without an explicit cartel ring, firms coordinate dynamically through two signature price trajectories:</p>'
                '<ul>'
                '<li><strong>Asymmetric Pass-Through ("Rockets &amp; Feathers"):</strong> When wholesale crude/TGP jumps by +10 c/L, stations pass through 93% of the hike within 3 days '
                'so no firm is left selling below replacement cost. When wholesale cost drops by −10 c/L, stations hold their posted street signs flat and let retail prices feather down '
                'over 21–28 days — because any unilateral price cut risks being misread by rivals as a defection, triggering a price war.</li>'
                '<li><strong>From Edgeworth Sawtooth Wars to AI Sticky Margins:</strong> In competitive markets, stations undercut by 0.2–0.5 c/L daily until margins hit zero, '
                'followed by a coordinated 10–12 c/L relenting jump led by a major brand (purple dashed curve). Byrne &amp; de Roos (2019) proved that BP used focal-point signaling '
                'in Perth to transition stations to a flat collusive margin (+75% profit jump, green curve), while Assad et al. (2024) showed that AI pricing algorithms in Germany '
                'raised duopoly margins by +28% by punishing undercutting in seconds.</li>'
                '</ul>'
                + _gas_rockets_feathers_svg(pass_through))}
      {_section("03", "Game theory: why gas colludes and other industries don't", "Repeated Bertrand supergames: comparing effective δ = exp(−rT) against critical threshold δ* = 1 − 1/N.", "gas-supergame-title",
                '<p>In a one-shot Bertrand game with homogeneous 87-octane fuel, price collapses to marginal cost \\((P = MC)\\). '
                'In an infinitely repeated supergame, tacit collusion is sustainable as a Subgame Perfect Nash Equilibrium (SPNE) if and only if '
                'the effective discount factor \\(\\delta = e^{-rT}\\) exceeds the critical defection threshold \\(\\delta^* = \\frac{\\pi^{\\text{deviate}} - \\pi^{\\text{collude}}}{\\pi^{\\text{deviate}} - \\pi^{\\text{punish}}} \\approx 1 - \\frac{1}{N}\\). '
                'Click any industry below to inspect why retail fuel, cement, and 3-carrier telecom sit deep inside the collusive zone while B2B SaaS, custom manufacturing, and aircraft procurement cannot sustain tacit collusion:</p>'
                + inspector
                + _table("Repeated Bertrand supergame parameters across 10 benchmark industries.",
                         ["Industry", "Local N", "Detection lag T", "Critical δ*", "Effective δ", "Collusive slack (δ − δ*)", "Product homogeneity", "Price visibility", "Equilibrium outcome"],
                         ind_rows, "gas-industry-table")
                + pandas_box)}
      <section class="sports-section sports-method" aria-labelledby="gas-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="gas-method-title">Sources, LaTeX paper, Pandas script, and downloads.</h2>
        <ul>
          <li><strong>Peer-reviewed econometric benchmarks:</strong> Assad, Clark, Ershov &amp; Xu (2024, <em>Journal of Political Economy</em>) on German MTS-K algorithmic pricing; Byrne &amp; de Roos (2019, <em>American Economic Review</em>) on Western Australia FuelWatch focal-point signaling; Clark &amp; Houde (2013 <em>RESTud</em>, 2014 <em>AEJ: Economic Policy</em>) on Canadian retail gasoline cartels; Luco (2019, <em>AEJ: Microeconomics</em>) on Chilean mandatory price disclosure.</li>
          <li><strong>Official data feeds:</strong> IEA Energy Prices and Taxes Database, UK Competition and Markets Authority (CMA) Road Fuel Monitoring Reports (2023–2025), and Natural Resources Canada (NRCan) Daily Pump Price Survey.</li>
          <li><strong>Dedicated LaTeX paper &amp; Mental Map integration:</strong> Read the compiled paper at <a href="{paper_href}">Game Theory: Gas Price Collusion Paper &amp; PDF ↗</a> and see the integrated notes in <a href="{up_root}Mental-Map/index.html#sec:game-theory">Mental Map § 2.2.4 Game Theory ↗</a>.</li>
        </ul>
        {_downloads(4 if is_subtab else 3, [
            ("studies-gas.json", "Gas Price Collusion study · JSON"),
            ("studies-gas-countries.csv", "12 Country price decompositions · CSV"),
            ("studies-gas-pass-through.csv", "28-Day Rockets & Feathers ECM · CSV"),
            ("studies-gas-industries.csv", "10 Industry supergame thresholds · CSV"),
        ])}
      </section>
    </main>'''


# ---- Study 4 View: ST-05 Sodium Battery Technology vs. Lithium-Ion -------------------

def _sodium_density_cost_svg(chemistries: list[dict[str, Any]]) -> str:
    """Horizontal comparison chart of Gravimetric Energy Density (Wh/kg) and Cell Cost ($/kWh) across 6 SIB & LIB chemistries."""
    height = 76 + len(chemistries) * 36
    max_wh = 320.0
    left, width = 285.0, 410.0
    parts = []
    for tick in range(0, 301, 50):
        tx = left + tick / max_wh * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">{tick} Wh/kg</text>'
        )
    for idx, c in enumerate(chemistries):
        y = 38 + idx * 36
        w_grav = c["gravWhKg"] / max_wh * width
        w_cost = c["cellCostUsdKwh"] / max_wh * width
        is_na = c["id"].startswith("SIB")
        cls = "study-bar-surface" if is_na else "study-bar-submerged"
        short_lbl = c["chemistry"].split(" (")[0]
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(short_lbl)}</text>'
            f'<rect class="{cls}" x="{left:.1f}" y="{y:.1f}" width="{w_grav:.1f}" height="21">'
            f'<title>{_e(c["chemistry"])} · {c["gravWhKg"]} Wh/kg ({c["volWhL"]} Wh/L) · ${c["cellCostUsdKwh"]}/kWh · {c["cycleLife"]:,} cycles</title></rect>'
            f'<circle cx="{left + w_cost:.1f}" cy="{y + 10.5:.1f}" r="5" fill="#ffffff" stroke="#0d101b" stroke-width="1.6">'
            f'<title>Pack/Cell Cost Floor: ${c["cellCostUsdKwh"]}/kWh</title></circle>'
            f'<text class="athletics-label" x="{left + w_grav + 8:.1f}" y="{y + 15:.1f}">{c["gravWhKg"]} Wh/kg · ${c["cellCostUsdKwh"]}/kWh ({c["cycleLife"]//1000}k cyc)</text>'
        )
    return _chart(
        "sodium-chemistry-comparison",
        "Sodium-Ion (SIB) vs. Lithium-Ion (LIB): Gravimetric energy density (Wh/kg) and cell cost floor ($/kWh)",
        "Cyan bars represent Sodium-Ion chemistries (Prussian White, Layered Oxide, Polyanionic NFPP); amber bars represent Lithium-Ion chemistries (LFP, LMFP, NMC-811). White markers show ANL BatPaC cell cost ($/kWh).",
        "".join(parts),
        height=height,
    )


def _sodium_temp_svg(temp_curve: list[dict[str, Any]]) -> str:
    """Athletics-style trajectory chart of Sub-Zero Discharge Capacity Retention (-40°C to +45°C)."""
    height = 320
    left, right, top, bottom = 70.0, 855.0, 34.0, 276.0
    width = right - left
    plot_h = bottom - top
    parts = []
    for pct in (25, 50, 75, 100):
        y = bottom - (pct / 100.0) * plot_h
        parts.append(
            f'<line class="chart-grid" x1="{left:.1f}" x2="{right:.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
            f'<text x="{left - 10:.1f}" y="{y + 4:.1f}" text-anchor="end">{pct}%</text>'
        )
    for t in temp_curve:
        x = left + ((t["tempC"] + 40.0) / 85.0) * width
        parts.append(
            f'<line class="chart-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top:.1f}" y2="{bottom:.1f}"/>'
            f'<text x="{x:.1f}" y="{bottom + 20:.1f}" text-anchor="middle">{t["tempC"]:+d}°C</text>'
        )

    def xy(temp_c: float, pct: float) -> tuple[float, float]:
        return left + ((temp_c + 40.0) / 85.0) * width, bottom - (pct / 100.0) * plot_h

    sib_pts = [xy(t["tempC"], t["sibRetentionPct"]) for t in temp_curve]
    lfp_pts = [xy(t["tempC"], t["lfpRetentionPct"]) for t in temp_curve]
    nmc_pts = [xy(t["tempC"], t["nmcRetentionPct"]) for t in temp_curve]

    parts.append(f'<polyline fill="none" stroke="#69d4cf" stroke-width="3.2" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in sib_pts)}"/>')
    parts.append(f'<polyline fill="none" stroke="#f7ab65" stroke-width="2.8" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in lfp_pts)}"/>')
    parts.append(f'<polyline fill="none" stroke="#bba1ff" stroke-width="2.2" stroke-dasharray="5 4" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in nmc_pts)}"/>')

    for t, (sx, sy), (lx, ly) in zip(temp_curve, sib_pts, lfp_pts):
        parts.append(
            f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="4.5" fill="#69d4cf"><title>{t["tempC"]:+d}°C · Na-Ion (SIB) capacity retention: {t["sibRetentionPct"]:g}%</title></circle>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="#f7ab65"><title>{t["tempC"]:+d}°C · Li-Ion LFP capacity retention: {t["lfpRetentionPct"]:g}%</title></circle>'
        )
    parts.append(
        '<text class="athletics-label" x="235" y="62">Na-Ion Prussian White / NFPP (92% retention at −20°C; 76% at −40°C)</text>'
        '<text class="athletics-label" x="255" y="175">Li-Ion LFP (64% at −20°C; 28% at −40°C — winter grid derating)</text>'
    )
    return _chart(
        "sodium-subzero-retention",
        "Sub-zero discharge capacity retention (−40°C to +45°C): why Na+ lower desolvation energy prevents winter blackouts",
        "Because Na+ has a 25%–30% lower charge-density desolvation barrier than Li+, Sodium-Ion cells retain 92% capacity at −20°C and 76% at −40°C compared with 64% and 28% for LFP.",
        "".join(parts),
        height=height,
    )


def sodium_study_body(data: dict[str, Any], lead: str = "", *, is_subtab: bool = False) -> str:
    """Render ST-05: Sodium Battery Technology in Science-and-Engineering/Chemistry/Electrochemistry."""
    s = data["summary"]
    chemistries = data["chemistries"]
    temp_curve = data["tempCurve"]
    up_root = "../../../../" if is_subtab else "../../../"
    paper_href = "../Paper/index.html" if is_subtab else "Paper/index.html"
    overview_href = "../index.html" if is_subtab else "index.html"
    subtab_href = "index.html" if is_subtab else "Sodium-Battery-Technology/index.html"

    deck = (
        f"Moving one row down Group 1 of the periodic table from Lithium (Z=3, r=0.76 Å) to Sodium (Z=11, r=1.02 Å): "
        f"how {s['crustalAbundanceRatio']} higher crustal abundance, dual aluminum current collectors, and lower desolvation barriers enable {s['sibCellCostUsdKwh']} grid storage."
    )
    actions = (
        f'<a class="button primary" href="{paper_href}">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#sodium-temp-title">Winter grid resilience</a>'
        f'<a class="button ghost" href="{up_root}Mental-Map/index.html#sec:electrochemistry">Mental Map § 1.3.3 ↗</a>'
        f'<a class="button ghost" href="{up_root}Workbench/index.html">Workbench (ST-05) ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["crustalAbundanceRatio"]}</strong>Na vs. Li abundance</span>'
        f'<span class="split-Chest"><strong>{s["sibCellCostUsdKwh"]}</strong>BatPaC cell floor</span>'
        f'<span class="split-Shoulders"><strong>{s["minus20CRetentionSibPct"]}%</strong>−20 °C retention</span></div>'
    )
    tab_bar = (
        '<nav class="wb-bucket-bar" aria-label="Electrochemistry destination tabs" style="margin: 14px 0 6px;">'
        f'<a class="wb-bucket-chip{" is-active" if not is_subtab else ""}" href="{overview_href}">⚡ Electrochemistry · Sodium Battery Dashboard</a>'
        f'<a class="wb-bucket-chip{" is-active" if is_subtab else ""}" href="{subtab_href}">🔋 Sodium Battery Technology Tab (ST-05)</a>'
        f'<a class="wb-bucket-chip" href="{paper_href}">📄 Compiled LaTeX Paper &amp; PDF</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Mental-Map/index.html#sec:electrochemistry">🧠 Mental Map § 1.3.3</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Workbench/index.html">🗄️ Workbench Queue</a>'
        '</nav>'
    )
    mm_sod = f"{up_root}Mental-Map/index.html#sec:electrochemistry"
    mm_sod_lbl = "§ 1.3.3 Chemistry / Electrochemistry"
    metrics = _metrics([
        ("Crustal abundance", s["crustalAbundanceRatio"], f"Na {s['naPpm']:,} ppm vs. Li {s['liPpm']} ppm (soda ash vs. brine/spodumene)"),
        ("Ionic volume ratio", f"{s['ionicVolumeRatio']}× larger", f"r(Na+) = {s['ionicRadiusNa']} Å vs. r(Li+) = {s['ionicRadiusLi']} Å → hard carbon anode"),
        ("Cell cost floor (BatPaC)", s["sibCellCostUsdKwh"], f"vs. {s['lfpCellCostUsdKwh']} for LFP (Al foil on both anode & cathode)"),
        ("Sub-zero retention (−20 °C)", f"{s['minus20CRetentionSibPct']}% capacity", f"vs. {s['minus20CRetentionLfpPct']}% for LFP — critical for polar-vortex grid peaks"),
    ], with_tooltips=True, mm_href=mm_sod, mm_label=mm_sod_lbl)

    chem_rows = [
        [
            c["chemistry"], c["ion"], c["cathode"], c["anode"],
            f'{c["gravWhKg"]} Wh/kg', f'{c["volWhL"]} Wh/L',
            f'${c["cellCostUsdKwh"]}/kWh', f'{c["cycleLife"]:,}',
            f'{c["tempRetMinus20Pct"]}%', c["zeroVoltSafe"],
        ]
        for c in chemistries
    ]

    pandas_box = (
        '<details class="wb-schema-details" open>'
        '<summary>🐍 View reproducible Pandas analysis script (<code>sodium_battery_pandas.py</code>)</summary>'
        f'<pre class="wb-bars" style="padding:14px; border:1px solid #69d4cf44; border-radius:8px; background:#080b14; overflow-x:auto;"><code>{_e(data["pandasScript"])}</code></pre>'
        '</details>'
    )

    sodium_inspector = (
        '<aside class="study-inspector" style="margin: 14px 0 18px;" aria-label="Electrochemical Parameter Inspector">'
        '<p class="eyebrow">Periodic Table &amp; Intercalation Parameter Inspector (hover / tap parameters)</p>'
        '<h3>Group 1 Alkali Charge Carrier &amp; Grid BESS Parameters</h3>'
        '<div class="study-reg-kpis">'
        + _inspector_param_card("Standard Potential E°", "sod-e0", "−2.71 V vs −3.04 V", "Standard reduction potential vs. SHE: Na+/Na (−2.71 V) sits 0.33 V above Li+/Li (−3.04 V), preventing Na plating dendrites during fast cold charging.", mm_sod, mm_sod_lbl)
        + _inspector_param_card("Faraday Specific Cap.", "sod-qth", "1,166 vs 3,861 mAh/g", "Theoretical metal specific capacity Q_th = nF / (3.6 M), driven by atomic weight M_Na = 22.99 g/mol vs. M_Li = 6.94 g/mol.", mm_sod, mm_sod_lbl)
        + _inspector_param_card("Desolvation Barrier Ea", "sod-ea", "−28% lower for Na+", "Lower surface charge density q/(4πr²) on Na+ (r = 1.02 Å) weakens solvent binding, enabling 88%–92% discharge retention at −20 °C.", mm_sod, mm_sod_lbl)
        + _inspector_param_card("Anode Foil Collector", "sod-foil", "Dual Al (0 V safe)", "Because Na does not alloy with Al at 0 V, SIBs replace expensive Copper anode foil with Aluminum on both electrodes and ship safely shorted at 0.0 V.", mm_sod, mm_sod_lbl)
        + '</div>'
        '<h4>Structural &amp; Grid BESS Attribute Scores (hover / tap for definition)</h4>'
        '<div class="study-sector-bars">'
        + _inspector_attr_row("−20 °C Polar-Vortex Retention", "sod-attr-cold", "92% (SIB) vs 64% (LFP)", "Usable discharge energy at −20 °C without burning auxiliary HVAC battery-heating power during winter grid peaks.", mm_sod, mm_sod_lbl)
        + _inspector_attr_row("Supply-Chain Geopolitical Independence", "sod-attr-geo", "96% (Soda Ash Na2CO3)", "Abundant domestic trona / soda ash precursor (23,600 ppm crustal Na) with zero Cobalt, Nickel, or Copper foil dependency.", mm_sod, mm_sod_lbl)
        + '</div></aside>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {tab_bar}
      {_hero("Chemistry / Electrochemistry", "Study ST-05 · Gemini 4 Argon + Pandas", "Period 3 power,<br>built for the <em>grid.</em>", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-05 · Generated on Mobile &amp; promoted to canonical site · Grounded in Argonne National Laboratory BatPaC v5.1 (2025), NREL Annual Technology Baseline (ATB), USGS Mineral Commodity Summaries (2025–2026), IEA Global EV &amp; Battery Outlook, and LBNL Materials Project.</p>
      {_section("01", "Periodic table origins", "Why moving from Period 2 (Li, Z=3) to Period 3 (Na, Z=11) changes everything.", "sodium-periodic-title",
                '<p class="sports-legend"><span class="study-key-surface">■ Sodium-Ion (SIB: Prussian White, Layered Oxide, Polyanionic NFPP)</span>'
                '<span class="study-key-submerged">■ Lithium-Ion (LIB: LFP, LMFP, NMC-811)</span>'
                '<span class="ab-key-against">● White marker = Cell manufacturing cost floor ($/kWh)</span></p>'
                + _sodium_density_cost_svg(chemistries)
                + metrics
                + sodium_inspector
                + '<p>Every engineering trade-off between sodium-ion (SIB) and lithium-ion (LIB) batteries follows directly from adding a closed \\(n=2\\) neon core shell '
                '\\((1s^2 2s^2 2p^6)\\) when moving down Group 1 from Lithium \\(([\\text{He}]2s^1,\\; M_{\\text{Li}}=6.94\\text{ g/mol})\\) to Sodium \\(([\\text{Ne}]3s^1,\\; M_{\\text{Na}}=22.99\\text{ g/mol})\\):</p>'
                '<ul>'
                '<li><strong>Shannon Octahedral Radius &amp; Hard Carbon Intercalation:</strong> The 6-coordinate ionic radius expands from \\(r_{\\text{Li}^+} = 0.76\\text{ \\AA}\\) to \\(r_{\\text{Na}^+} = 1.02\\text{ \\AA}\\) '
                '(a \\((1.02/0.76)^3 \\approx 2.42\\times\\) ionic volume expansion). Because \\(\\text{Na}^+\\)-graphite binary staging compounds are thermodynamically unstable above ~35 mAh/g due to π-d orbital repulsion, '
                'SIBs replace graphite with disordered <strong>hard carbon</strong> (turbostratic nanodomains + closed nanopores delivering 300–350 mAh/g).</li>'
                '<li><strong>Aluminum Foil on Both Electrodes &amp; 0 V Transport Safety:</strong> Unlike \\(\\text{Li}\\), which alloys with Aluminum at low potentials (~0.3 V vs. \\(\\text{Li/Li}^+\\)) and forces LIBs to use expensive, heavy Copper foil on the anode, '
                '\\(\\text{Na}\\) forms no binary alloy with \\(\\text{Al}\\). SIBs use inexpensive Aluminum current collectors on <em>both</em> cathode and anode — cutting current-collector cost by ~70% and allowing cells to be shipped and stored completely shorted at <strong>0.0 V</strong> with zero copper dissolution or thermal runaway hazard.</li>'
                '<li><strong>Standard Potential &amp; Energy Density Ceiling:</strong> By Faraday\'s law \\(Q_{\\text{th}} = nF / (3.6 M)\\), metal specific capacity drops from 3,861 mAh/g (Li) to 1,166 mAh/g (Na) and \\(E^\\circ\\) shifts from \\(-3.04\\text{ V}\\) to \\(-2.71\\text{ V}\\) vs. SHE, '
                'placing practical SIB cells at 135–165 Wh/kg versus 190 Wh/kg for LFP and 275 Wh/kg for NMC-811.</li>'
                '</ul>'
                + _table("Electrochemical and technoeconomic comparison of 6 commercial Sodium-Ion and Lithium-Ion cell architectures.",
                         ["Chemistry", "Charge carrier", "Cathode host", "Anode & collector", "Grav. Wh/kg", "Vol. Wh/L", "Cell $/kWh", "Cycle life", "−20°C ret.", "0 V transport"],
                         chem_rows, "sodium-chemistry-table"))}
      {_section("02", "Preventing massive grid blackouts", "Why lower Stokes desolvation energy makes Na-ion the ideal polar-vortex and Dunkelflaute BESS.", "sodium-temp-title",
                '<p>Why does a larger ion move <em>faster</em> across the electrolyte interface in extreme cold? Because \\(\\text{Na}^+\\) has a larger crystallographic radius (1.02 Å vs. 0.76 Å), '
                'its surface electrostatic charge density \\(q / (4\\pi r^2)\\) is <strong>44% lower</strong> than \\(\\text{Li}^+\\). That weaker electric field binds carbonate/ether solvent molecules '
                'less tightly, reducing the interfacial desolvation activation barrier \\(E_a^{\\text{desolv}}\\) by 25%–30% and yielding a smaller Stokes solvated radius in solution.</p>'
                '<p>During winter polar-vortex blackout emergencies (such as the 2021 Texas ERCOT freeze or Canadian prairie cold snaps at −20 °C to −35 °C), LFP grid batteries suffer severe charge-transfer impedance spikes and lose 36%–72% of their usable capacity unless they burn auxiliary HVAC heating power. '
                'Polyanionic (NFPP) and Prussian White sodium-ion grid banks retain <strong>88%–92% capacity at −20 °C</strong>, achieve 8,000–10,000 cycles, and eliminate lithium supply bottlenecks for 4-to-12 hour utility peak shaving and synthetic inertia.</p>'
                + _sodium_temp_svg(temp_curve)
                + pandas_box)}
      <section class="sports-section sports-method" aria-labelledby="sodium-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="sodium-method-title">Sources, LaTeX paper, Pandas script, and downloads.</h2>
        <ul>
          <li><strong>Technoeconomic &amp; cell models:</strong> Argonne National Laboratory (ANL) <em>BatPaC v5.1 Battery Manufacturing Cost Model</em> (2025) and NREL <em>Annual Technology Baseline (ATB) Utility-Scale Battery Storage</em>.</li>
          <li><strong>Geological &amp; materials benchmarks:</strong> USGS <em>Mineral Commodity Summaries: Lithium &amp; Soda Ash</em> (2025–2026), IEA <em>Global EV &amp; Battery Outlook</em>, and Lawrence Berkeley National Laboratory (LBNL) <em>Materials Project Electrochemical Database</em>.</li>
          <li><strong>Dedicated LaTeX paper &amp; Mental Map integration:</strong> Read the compiled paper at <a href="{paper_href}">Electrochemistry: Sodium Battery Paper &amp; PDF ↗</a> and see the integrated notes in <a href="{up_root}Mental-Map/index.html#sec:electrochemistry">Mental Map § 1.3.3 Electrochemistry ↗</a>.</li>
        </ul>
        {_downloads(4 if is_subtab else 3, [
            ("studies-sodium.json", "Sodium Battery study · JSON"),
            ("studies-sodium-chemistries.csv", "6 SIB vs. LIB chemistries · CSV"),
            ("studies-sodium-temp-curve.csv", "Sub-zero retention curve · CSV"),
        ])}
      </section>
    </main>'''


# ---- Study 5 View: ST-08 AI Cost & Compute Economics (Emerging Industries / AI) ------

def _ai_cost_models_svg(models: list[dict[str, Any]]) -> str:
    """Horizontal comparison chart of Blended Inference Cost ($/1M tokens), Training Capex ($M), and Reasoning Score (%)."""
    height = 76 + len(models) * 36
    max_usd = 40.0
    left, width = 285.0, 395.0
    parts = []
    for tick in (0, 10, 20, 30, 40):
        tx = left + (tick / max_usd) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">${tick}/1M tok</text>'
        )
    for idx, m in enumerate(models):
        y = 38 + idx * 36
        w_cost = max(3.0, (m["blendedUsdM"] / max_usd) * width)
        w_score = (m["benchmarkPct"] / 100.0) * width
        is_efficient = m["blendedUsdM"] <= 4.50
        cls = "study-bar-surface" if is_efficient else "study-bar-submerged"
        short_lbl = m["model"].split(" (")[0]
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(short_lbl)}</text>'
            f'<rect class="{cls}" x="{left:.1f}" y="{y:.1f}" width="{w_cost:.1f}" height="21">'
            f'<title>{_e(m["model"])} · Blended: ${m["blendedUsdM"]:.2f}/1M tokens (${m["inputUsdM"]:.2f} in / ${m["outputUsdM"]:.2f} out) · Capex: ${m["trainCapexUsdM"]:g}M · {m["energyWhQuery"]:.2f} Wh/query · Score: {m["benchmarkPct"]:.1f}%</title></rect>'
            f'<circle cx="{left + w_score:.1f}" cy="{y + 10.5:.1f}" r="4.8" fill="#ffffff" stroke="#0d101b" stroke-width="1.6">'
            f'<title>MMLU-Pro / GPQA Reasoning Accuracy: {m["benchmarkPct"]:.1f}%</title></circle>'
            f'<text class="athletics-label" x="{left + max(w_cost, w_score) + 10:.1f}" y="{y + 15:.1f}">${m["blendedUsdM"]:.2f}/1M · {m["benchmarkPct"]:.1f}% ({m["energyWhQuery"]:.2f} Wh)</text>'
        )
    return _chart(
        "ai-cost-models-chart",
        "AI inference deflation (2023–2026): Blended price ($/1M tokens) vs. reasoning accuracy (%) & energy (Wh/query)",
        "Bars show blended API token cost ($/1M tokens, 3:1 input/output); white circles mark MMLU-Pro/GPQA accuracy (% of chart width). Cyan bars highlight sub-$4.50/1M Sparse MoE & distilled tiers.",
        "".join(parts),
        height=height,
    )


def _ai_cost_layers_svg(layers: list[dict[str, Any]]) -> str:
    """Horizontal bar chart of AI infrastructure cost-impact share (%) vs. hardware bottleneck severity (%)."""
    height = 76 + len(layers) * 36
    left, width = 285.0, 395.0
    parts = []
    for tick in (0, 25, 50, 75, 100):
        tx = left + (tick / 100.0) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">{tick}%</text>'
        )
    for idx, lyr in enumerate(layers):
        y = 38 + idx * 36
        w_share = (lyr["costSharePct"] / 100.0) * width
        x_bot = left + (lyr["bottleneckScore"] / 100.0) * width
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(lyr["layer"][:34])}</text>'
            f'<rect class="study-bar-surface" x="{left:.1f}" y="{y:.1f}" width="{w_share:.1f}" height="20">'
            f'<title>{_e(lyr["layer"])} · Cost Leverage Share: {lyr["costSharePct"]}% · Bottleneck Score: {lyr["bottleneckScore"]}% ({_e(lyr["metricVal"])})</title></rect>'
            f'<circle cx="{x_bot:.1f}" cy="{y + 10:.1f}" r="4.5" fill="#f7ab65" stroke="#0d101b" stroke-width="1.5">'
            f'<title>Supply/Hardware Bottleneck Severity: {lyr["bottleneckScore"]}%</title></circle>'
            f'<text class="athletics-label" x="{left + max(w_share, (lyr["bottleneckScore"]/100.0)*width) + 10:.1f}" y="{y + 15:.1f}">{_e(lyr["metricVal"])} ({lyr["costSharePct"]}%)</text>'
        )
    return _chart(
        "ai-cost-layers-chart",
        "AI compute & infrastructure layers: Cost leverage (%) vs. supply bottleneck severity (● amber marker)",
        "Compares the six structural drivers of AI economics across memory bandwidth (HBM3e), Sparse MoE/MLA compression, test-time reasoning tokens, pre-training capex, baseload power, and cascade routing.",
        "".join(parts),
        height=height,
    )


def ai_cost_study_body(data: dict[str, Any], lead: str = "", *, is_subtab: bool = False) -> str:
    """Render ST-08: AI Cost & Compute Economics in Business-and-Economics/Emerging-Industries/Artificial-Intelligence."""
    s = data["summary"]
    models = data["models"]
    layers = data["layers"]
    first_lyr = layers[0]
    up_root = "../../../../" if is_subtab else "../../../"
    paper_href = "../Paper/index.html" if is_subtab else "Paper/index.html"
    overview_href = "../index.html" if is_subtab else "index.html"
    subtab_href = "index.html" if is_subtab else "AI-Cost-Study/index.html"

    deck = (
        f"Between 2023 and 2026, frontier-equivalent LLM token inference deflated by {s['inferenceDeflationMultiple']} "
        f"(from {s['gpt4BaselineUsdM']} to {s['flashBlendedUsdM']}–{s['argonBlendedUsdM']}) while pre-training cluster capex climbed past $130M–$1B+."
    )
    actions = (
        f'<a class="button primary" href="{paper_href}">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#ai-cost-layers-title">6-Layer Cost Inspector</a>'
        f'<a class="button ghost" href="{up_root}Mental-Map/index.html#sec:emerging-industries-artificial-intelligence">Mental Map § 2.5.1 ↗</a>'
        f'<a class="button ghost" href="{up_root}Workbench/index.html">Workbench (ST-08) ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["inferenceDeflationMultiple"]}</strong>inference deflation</span>'
        f'<span class="split-Chest"><strong>{s["argonBlendedUsdM"]}</strong>Argon High Thinking</span>'
        f'<span class="split-Shoulders"><strong>{s["cascadeSavingsPct"]}%</strong>cascade savings</span></div>'
    )
    tab_bar = (
        '<nav class="wb-bucket-bar" aria-label="Artificial Intelligence destination tabs" style="margin: 14px 0 6px;">'
        f'<a class="wb-bucket-chip{" is-active" if not is_subtab else ""}" href="{overview_href}">🤖 Emerging Industries: AI · Cost &amp; Compute Dashboard</a>'
        f'<a class="wb-bucket-chip{" is-active" if is_subtab else ""}" href="{subtab_href}">📉 AI Cost &amp; Compute Study Tab (ST-08)</a>'
        f'<a class="wb-bucket-chip" href="{paper_href}">📄 Compiled LaTeX Paper &amp; PDF</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Mental-Map/index.html#sec:emerging-industries-artificial-intelligence">🧠 Mental Map § 2.5.1</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Workbench/index.html">🗄️ Workbench Queue</a>'
        '</nav>'
    )
    mm_ai = f"{up_root}Mental-Map/index.html#sec:emerging-industries-artificial-intelligence"
    mm_ai_lbl = "§ 2.5.1 Emerging Industries / Artificial Intelligence"
    metrics = _metrics([
        ("Inference deflation (2023→26)", s["inferenceDeflationMultiple"], f"From {s['gpt4BaselineUsdM']} (2023 GPT-4) down to {s['flashBlendedUsdM']} (Gemini 3.8 Flash)"),
        ("Gemini 4 Argon blended", s["argonBlendedUsdM"], "$1.25/1M input · $10.00/1M output · 89.2% reasoning benchmark"),
        ("DeepSeek / Flash floor", f"{s['deepseekBlendedUsdM']} / {s['flashBlendedUsdM']}", "Sparse MoE (37B active of 671B) + Multi-head Latent Attention (MLA)"),
        ("Cascade routing savings", f"{s['cascadeSavingsPct']}% TCO cut", "85% Gemini 3.8 Flash + 15% Gemini 4 Argon High Thinking ($0.68/1M)"),
    ], with_tooltips=True, mm_href=mm_ai, mm_label=mm_ai_lbl)

    ai_inspector = (
        '<aside class="study-inspector" style="margin: 14px 0 18px;" aria-label="AI Compute Parameter Inspector">'
        '<p class="eyebrow">Roofline &amp; Scaling Law Parameter Inspector (hover / tap parameters)</p>'
        '<h3>Chinchilla Pre-Training vs. HBM3e Memory-Bandwidth Decoding</h3>'
        '<div class="study-reg-kpis">'
        + _inspector_param_card("Active Sparsity Ratio", "ai-param-moe", "37B / 671B (5.5%)", "Fraction of total Mixture-of-Experts parameters activated per token forward pass, cutting compute FLOPs per token by ~18×.", mm_ai, mm_ai_lbl)
        + _inspector_param_card("MLA KV-Cache Compression", "ai-param-mla", "−75% to −88% HBM", "Low-rank latent projection of attention Key-Value tensors (d_c ≤ n_h d_h), eliminating the HBM3e memory-bandwidth wall on long contexts.", mm_ai, mm_ai_lbl)
        + _inspector_param_card("Jevons Thinking Multiplier", "ai-param-jevons", "5×–15× tokens/query", "Test-time compute search trees multiply internal reasoning tokens per query as per-token prices fall—raising total compute demand.", mm_ai, mm_ai_lbl)
        + _inspector_param_card("Query Energy Footprint", "ai-param-wh", s["energyPerQueryWh"], "Electrical energy consumed per 1,000-token inference query including data-center cooling PUE (1.12–1.20).", mm_ai, mm_ai_lbl)
        + '</div>'
        '<h4>Infrastructure Cost &amp; Bottleneck Attributes (hover / tap for definition)</h4>'
        '<div class="study-sector-bars">'
        + _inspector_attr_row("HBM3e Memory Bandwidth Bound", "ai-attr-hbm", f"{first_lyr['bottleneckScore']}% (Bytes/FLOP)", "Autoregressive decoding latency is governed by HBM3e memory bandwidth (TB/s) rather than peak tensor-core FLOP/s.", mm_ai, mm_ai_lbl)
        + _inspector_attr_row("Hardware Driver", "ai-attr-drv", first_lyr["hardwareDriver"], "Primary silicon and algorithmic lever governing unit token cost in the selected layer.", mm_ai, mm_ai_lbl)
        + '</div></aside>'
    )

    model_rows = [
        [
            m["model"], m["architecture"],
            f'${m["inputUsdM"]:.2f}/1M', f'${m["outputUsdM"]:.2f}/1M', f'${m["blendedUsdM"]:.2f}/1M',
            f'{36.0 / m["blendedUsdM"]:.1f}×',
            f'{m["trainFlopsE24"]:g}×10²⁴', f'${m["trainCapexUsdM"]:g}M',
            f'{m["energyWhQuery"]:.2f} Wh', f'{m["benchmarkPct"]:.1f}%', m["regime"],
        ]
        for m in models
    ]
    layer_rows = [
        [
            l["layer"], l["metricVal"], f'{l["costSharePct"]}%', f'{l["bottleneckScore"]}%',
            l["deflationRate"], l["hardwareDriver"], l["mechanism"],
        ]
        for l in layers
    ]

    pandas_box = (
        '<details class="wb-schema-details" open>'
        '<summary>🐍 View reproducible Pandas analysis script (<code>ai_cost_economics_pandas.py</code>)</summary>'
        f'<pre class="wb-bars" style="padding:14px; border:1px solid #69d4cf44; border-radius:8px; background:#080b14; overflow-x:auto;"><code>{_e(data["pandasScript"])}</code></pre>'
        '</details>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {tab_bar}
      {_hero("Emerging Industries / Artificial Intelligence", "Study ST-08 · Gemini 4 Argon + Pandas", "200× cheaper tokens,<br><em>billion-dollar</em> clusters.", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-08 · Generated on Mobile &amp; promoted to canonical site · Grounded in Epoch AI Compute &amp; Price Trends (2023–2026), Artificial Analysis API Benchmarks, Stanford HAI AI Index, and Google AI Studio / OpenAI / Anthropic / DeepSeek Technical Reports.</p>
      {_section("01", "Inference deflation vs. frontier capex", "Why marginal token prices fell 10×–200× in three years while pre-training cluster costs exploded.", "ai-cost-models-title",
                '<p class="sports-legend"><span class="study-key-surface">■ Sparse MoE, Distilled &amp; Open-Weight Tiers (≤$4.50 / 1M tokens)</span>'
                '<span class="study-key-submerged">■ Legacy / Dense Frontier Reference Tiers ($27–$36 / 1M tokens)</span>'
                '<span class="ab-key-against">● White marker = MMLU-Pro / GPQA Reasoning Accuracy (%)</span></p>'
                + _ai_cost_models_svg(models)
                + metrics
                + ai_inspector
                + '<p>Modern AI unit economics obey a sharp <strong>two-part tariff</strong>. On the marginal side, algorithmic innovations — Sparse Mixture-of-Experts (routing 37B active parameters out of 671B), '
                'Multi-head Latent Attention (compressing KV-cache memory traffic by 75%–88%), and FP8/INT4 quantization — combined with custom inference silicon (TPU v6e, Blackwell B200) have driven the price of GPT-4-level intelligence down by <strong>~68%–85% per year</strong>. '
                'On the fixed-cost side, pre-training a frontier base model requires 100,000+ interconnected accelerators and 100–500 MW of baseload data-center power ($130M to $1B+ per run).</p>'
                + _table("Frontier, open-weight cloud, and local quantized AI model economics (2023–2026).",
                         ["Model tier", "Architecture", "Input $/1M", "Output $/1M", "Blended $/1M", "Deflation vs 2023", "Train FLOPs", "Train Capex", "Energy / query", "Score %", "Economic regime"],
                         model_rows, "ai-cost-models-table"))}
      {_section("02", "The 6-layer AI cost stack & Jevons Paradox", "Memory bandwidth walls, test-time reasoning token multipliers, and enterprise cascade routing.", "ai-cost-layers-title",
                '<p>Why hasn\'t a 99% drop in per-token pricing caused hyperscaler AI revenue to collapse? Because of <strong>Jevons Paradox</strong>: '
                'test-time reasoning models (Gemini 4 Argon High Thinking, OpenAI o3, DeepSeek-R1) generate 5,000 to 32,000 internal chain-of-thought tokens per query to solve multi-step engineering, coding, and mathematical proofs. '
                'For production workloads, pairing a fast distilled router (85% of traffic on <strong>Gemini 3.8 Flash</strong> at $0.18/1M) with a deep reasoning escalation tier (15% on <strong>Gemini 4 Argon High Thinking</strong> at $3.50/1M) achieves an <strong>80.6% reduction in total monthly spend</strong> ($0.68/1M blended) without sacrificing frontier accuracy.</p>'
                + _ai_cost_layers_svg(layers)
                + _table("Six structural layers governing AI compute cost, HBM3e hardware bottlenecks, and enterprise TCO.",
                         ["Infrastructure layer", "Key benchmark", "Cost leverage %", "Bottleneck %", "Annual shift", "Hardware / algorithmic driver", "Structural mechanism"],
                         layer_rows, "ai-cost-layers-table")
                + pandas_box)}
      <section class="sports-section sports-method" aria-labelledby="ai-cost-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="ai-cost-method-title">Sources, LaTeX paper, Pandas script, and downloads.</h2>
        <ul>
          <li><strong>Compute &amp; pricing series:</strong> Epoch AI <em>LLM Inference Price Trends &amp; Training Compute Database</em> (2023–2026), Artificial Analysis <em>Independent LLM API Latency &amp; Price Benchmarks</em>, and Stanford HAI <em>AI Index Report</em>.</li>
          <li><strong>Architecture &amp; hardware reports:</strong> Google DeepMind <em>Gemini 4 Argon &amp; TPU v6e Technical Report</em>, DeepSeek-AI <em>DeepSeek-V3 / R1 Multi-head Latent Attention &amp; Auxiliary-Loss-Free MoE</em>, and SemiAnalysis <em>HBM3e &amp; CoWoS Supply Chain Model</em>.</li>
          <li><strong>Dedicated LaTeX paper &amp; Mental Map integration:</strong> Read the compiled paper at <a href="{paper_href}">Emerging Industries: AI Cost &amp; Compute Paper &amp; PDF ↗</a> and see the integrated notes in <a href="{up_root}Mental-Map/index.html#sec:emerging-industries-artificial-intelligence">Mental Map § 2.5.1 Artificial Intelligence ↗</a>.</li>
        </ul>
        {_downloads(4 if is_subtab else 3, [
            ("studies-ai-cost.json", "AI Cost & Compute study · JSON"),
            ("studies-ai-cost-models.csv", "8 Model cost & capex benchmarks · CSV"),
            ("studies-ai-cost-layers.csv", "6 Infrastructure cost layers · CSV"),
        ])}
      </section>
    </main>'''


# ---- Study 6 View: ST-09 Taxes on Generations Over Time Periods (Multi-Plot) ---------

def _gen_tax_burden_rewards_svg(cohorts: list[dict[str, Any]]) -> str:
    """Plot 1: Real Per-Capita Tax Burden vs. Fiscal Rewards (Cash + Healthcare/Education STiK) in 2024 CAD/capita."""
    height = 78 + len(cohorts) * 38
    max_cad = 36000.0
    left, width = 285.0, 395.0
    parts = []
    for tick in (0, 9000, 18000, 27000, 36000):
        tx = left + (tick / max_cad) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">${tick // 1000}k/cap</text>'
        )
    for idx, c in enumerate(cohorts):
        y = 38 + idx * 38
        w_tax = (c["totalTaxCad"] / max_cad) * width
        w_rew = (c["totalRewardCad"] / max_cad) * width
        short_lbl = c["cohort"].replace("Baseline", "Era")
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(short_lbl)}</text>'
            f'<rect class="study-bar-submerged" x="{left:.1f}" y="{y:.1f}" width="{w_tax:.1f}" height="12">'
            f'<title>{_e(c["cohort"])} · Real Gross Taxes Paid: ${_num(c["totalTaxCad"])}/capita (2024 CAD)</title></rect>'
            f'<rect class="study-bar-surface" x="{left:.1f}" y="{y + 13:.1f}" width="{w_rew:.1f}" height="12">'
            f'<title>{_e(c["cohort"])} · Real Fiscal Rewards Received (Cash + Health/Education STiK): ${_num(c["totalRewardCad"])}/capita (Ratio {c["rewardRatio"]:.2f}×)</title></rect>'
            f'<text class="athletics-label" x="{left + max(w_tax, w_rew) + 8:.1f}" y="{y + 16:.1f}">${_num(c["totalTaxCad"])} tax vs ${_num(c["totalRewardCad"])} reward ({c["rewardRatio"]:.2f}×)</text>'
        )
    return _chart(
        "gen-tax-burden-rewards-chart",
        "Plot 1 · Real Per-Capita Tax Burden vs. Fiscal Rewards by Generation & Historical Era (2024 CAD/capita)",
        "Amber top bars show real population-normalized gross taxes paid per capita; cyan bottom bars show real cash + healthcare/education transfers received per capita (StatCan DHEA, SHS & CIHI, 1985–2025).",
        "".join(parts),
        height=height,
    )


def _gen_tax_mix_svg(cohorts: list[dict[str, Any]]) -> str:
    """Plot 2: Stacked Tax Instrument Composition (Income/Payroll, Sales, Property, Fuel/Carbon, Alcohol & Vape Excise)."""
    height = 78 + len(cohorts) * 36
    max_cad = 32000.0
    left, width = 285.0, 395.0
    parts = []
    for tick in (0, 8000, 16000, 24000, 32000):
        tx = left + (tick / max_cad) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">${tick // 1000}k/cap</text>'
        )
    for idx, c in enumerate(cohorts):
        y = 38 + idx * 36
        w_inc = (c["incomePayrollCad"] / max_cad) * width
        w_sal = (c["salesTaxCad"] / max_cad) * width
        w_prp = (c["propertyTaxCad"] / max_cad) * width
        w_exc = ((c["fuelCarbonCad"] + c["alcoholTaxCad"] + c["vapeTaxCad"]) / max_cad) * width
        x1 = left + w_inc
        x2 = x1 + w_sal
        x3 = x2 + w_prp
        short_lbl = c["cohort"].replace("Baseline", "Era")
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(short_lbl)}</text>'
            f'<rect fill="#bba1ff" x="{left:.1f}" y="{y:.1f}" width="{w_inc:.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Income &amp; Payroll (PIT + CPP/EI): ${_num(c["incomePayrollCad"])}/cap</title></rect>'
            f'<rect fill="#69d4cf" x="{x1:.1f}" y="{y:.1f}" width="{w_sal:.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Sales Tax (GST/HST/PST): ${_num(c["salesTaxCad"])}/cap</title></rect>'
            f'<rect fill="#f7ab65" x="{x2:.1f}" y="{y:.1f}" width="{w_prp:.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Municipal Property Tax: ${_num(c["propertyTaxCad"])}/cap ({c["homeownerPct"]:g}% homeowner rate)</title></rect>'
            f'<rect fill="#f28b82" x="{x3:.1f}" y="{y:.1f}" width="{max(3.0, w_exc):.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Fuel/Carbon (${c["fuelCarbonCad"]}) + Alcohol (${c["alcoholTaxCad"]}) + Vape (${c["vapeTaxCad"]})</title></rect>'
            f'<text class="athletics-label" x="{x3 + max(3.0, w_exc) + 8:.1f}" y="{y + 15:.1f}">PIT ${_num(c["incomePayrollCad"])} · Sales ${_num(c["salesTaxCad"])} · Prop ${_num(c["propertyTaxCad"])}</text>'
        )
    return _chart(
        "gen-tax-mix-chart",
        "Plot 2 · Tax Instrument Breakdown Across Generations & Time Periods (Income/Payroll, Sales, Property & Sin/Fuel Excise)",
        "Stacked bars decompose per-capita tax payments into Income & Payroll (violet), Sales GST/HST (cyan), Property Tax (amber), and Fuel/Carbon + Alcohol + Vape Excise (coral).",
        "".join(parts),
        height=height,
    )


def _gen_commute_excise_svg(cohorts: list[dict[str, Any]]) -> str:
    """Plot 3: Average One-Way Commute Duration (mins) & Fuel/Carbon Tax vs. Youth Vape Excise & Property Tax Incidence."""
    height = 78 + len(cohorts) * 36
    max_fuel = 1000.0
    left, width = 285.0, 395.0
    parts = []
    for tick in (0, 250, 500, 750, 1000):
        tx = left + (tick / max_fuel) * width
        parts.append(
            f'<line class="chart-grid" x1="{tx:.1f}" x2="{tx:.1f}" y1="30" y2="{height - 26}"/>'
            f'<text x="{tx:.1f}" y="20" text-anchor="middle">${tick}/cap</text>'
        )
    for idx, c in enumerate(cohorts):
        y = 38 + idx * 36
        w_fuel = (c["fuelCarbonCad"] / max_fuel) * width
        w_vape = (c["vapeTaxCad"] / max_fuel) * width
        x_comm = left + (c["commuteMins"] / 35.0) * width
        short_lbl = c["cohort"].replace("Baseline", "Era")
        parts.append(
            f'<text x="{left - 10:.1f}" y="{y + 15:.1f}" text-anchor="end">{_e(short_lbl)}</text>'
            f'<rect fill="#69d4cf" x="{left:.1f}" y="{y:.1f}" width="{w_fuel:.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Gross Fuel &amp; Carbon Tax: ${c["fuelCarbonCad"]}/cap ({c["commuteMins"]:.1f} min 1-way commute, {c["autoSharePct"]:.1f}% auto share)</title></rect>'
            f'<rect fill="#f28b82" x="{left + w_fuel:.1f}" y="{y:.1f}" width="{max(0.0, w_vape):.1f}" height="20">'
            f'<title>{_e(c["cohort"])} · Vaping Excise Duty: ${c["vapeTaxCad"]}/cap ({c["vapePrevPct"]:.1f}% prevalence)</title></rect>'
            f'<circle cx="{x_comm:.1f}" cy="{y + 10:.1f}" r="5" fill="#ffffff" stroke="#0d101b" stroke-width="1.6">'
            f'<title>Average One-Way Commute Duration: {c["commuteMins"]:.1f} mins ({c["autoSharePct"]:.1f}% private vehicle share)</title></circle>'
            f'<text class="athletics-label" x="{left + w_fuel + w_vape + 8:.1f}" y="{y + 15:.1f}">{c["commuteMins"]:.1f}m commute → ${c["fuelCarbonCad"]} CO2/fuel + ${c["vapeTaxCad"]} vape</text>'
        )
    return _chart(
        "gen-tax-commute-excise-chart",
        "Plot 3 · Average Commute Duration (● mins) Driving Fuel & Carbon Tax ($/cap) + Youth Vaping Excise ($/cap)",
        "Cyan bars show annual per-capita road-fuel excise and carbon tax; coral extensions show vaping excise duty ($168/cap on Gen Z); white markers plot mean one-way commute duration (peaking at 28.4 mins for Millennials).",
        "".join(parts),
        height=height,
    )


def gen_tax_study_body(data: dict[str, Any], lead: str = "", *, is_subtab: bool = False) -> str:
    """Render ST-09: Taxes on Generations Over Time Periods in Business-and-Economics/Macroeconomics/Fiscal-Policy."""
    s = data["summary"]
    cohorts = data["cohorts"]
    up_root = "../../../../" if is_subtab else "../../../"
    paper_href = "../Paper/index.html" if is_subtab else "Paper/index.html"
    overview_href = "../index.html" if is_subtab else "index.html"
    subtab_href = "index.html" if is_subtab else "Taxes-on-Generations/index.html"

    deck = (
        f"In constant 2024 Canadian dollars normalized for cohort population size (1985–2025), prime-working-age Gen X ({s['peakTaxCohort']}) "
        f"and Millennials ($26,890/yr, 28.4 min commute) fund the fiscal base while 65+ seniors receive {s['seniorRewardRatio']} in pensions and healthcare."
    )
    actions = (
        f'<a class="button primary" href="{paper_href}">Read the LaTeX paper &amp; PDF <span aria-hidden="true">↗</span></a>'
        '<a class="button ghost" href="#gen-tax-mix-title">Plot 2: Tax Mix Over Time</a>'
        '<a class="button ghost" href="#gen-tax-commute-title">Plot 3: Commute &amp; Vape Tax</a>'
        f'<a class="button ghost" href="{up_root}Mental-Map/index.html#sec:fiscal-policy">Mental Map § 2.3.3 ↗</a>'
        f'<a class="button ghost" href="{up_root}Workbench/index.html">Workbench (ST-09) ↗</a>'
    )
    art = (
        '<div class="athletics-split-card" aria-hidden="true">'
        f'<span class="split-Back"><strong>{s["peakTaxCohort"]}</strong>Gen X peak tax</span>'
        f'<span class="split-Chest"><strong>{s["seniorRewardRatio"]}</strong>65+ reward ratio</span>'
        f'<span class="split-Shoulders"><strong>28.4m</strong>Millennial commute</span></div>'
    )
    tab_bar = (
        '<nav class="wb-bucket-bar" aria-label="Fiscal Policy destination tabs" style="margin: 14px 0 6px;">'
        f'<a class="wb-bucket-chip{" is-active" if not is_subtab else ""}" href="{overview_href}">🏛️ Fiscal Policy · Generational Tax Dashboard</a>'
        f'<a class="wb-bucket-chip{" is-active" if is_subtab else ""}" href="{subtab_href}">📊 Taxes on Generations Study Tab (ST-09)</a>'
        f'<a class="wb-bucket-chip" href="{paper_href}">📄 Compiled LaTeX Paper &amp; PDF</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Mental-Map/index.html#sec:fiscal-policy">🧠 Mental Map § 2.3.3</a>'
        f'<a class="wb-bucket-chip" href="{up_root}Workbench/index.html">🗄️ Workbench Queue</a>'
        '</nav>'
    )
    mm_fp = f"{up_root}Mental-Map/index.html#sec:fiscal-policy"
    mm_fp_lbl = "§ 2.3.3 Macroeconomics / Fiscal Policy"
    metrics = _metrics([
        ("Peak tax-bearing cohort (Gen X)", s["peakTaxCohort"], "Net fiscal deficit −$18,580/capita (Reward Ratio 0.41×)"),
        ("Senior fiscal reward ratio (65+)", s["seniorRewardRatio"], "$29,140 transfers + health STiK vs. $12,610 taxes paid/capita"),
        ("Commute fuel & carbon peak", s["millennialCommuteTax"], "Millennials (29–44) longest 1-way commute & gross fuel/CO2 tax"),
        ("Gen Z vaping excise share", s["genZVapeShare"], "19.7% prevalence (ages 20–24) vs. <1.5% for Boomers"),
    ], with_tooltips=True, mm_href=mm_fp, mm_label=mm_fp_lbl)

    gen_inspector = (
        '<aside class="study-inspector" style="margin: 14px 0 18px;" aria-label="Generational Fiscal Incidence Parameter Inspector">'
        '<p class="eyebrow">Generational Fiscal Incidence &amp; Behavioral Micro-Model Inspector (hover / tap parameters)</p>'
        '<h3>Auerbach-Kotlikoff Generational Accounting &amp; Micro-Excise Elasticities</h3>'
        '<div class="study-reg-kpis">'
        + _inspector_param_card("Aging Fiscal Shift β_65+", "gt-param-beta", "+$468.40 / 1% pop", "Panel OLS fixed-effects estimate of the additional real annual net tax burden imposed on prime working-age adults (25–54) per 1 percentage-point increase in the 65+ population share.", mm_fp, mm_fp_lbl)
        + _inspector_param_card("Commute Carbon Elasticity γ", "gt-param-gamma", "1.34 (p = 0.0003)", "Elasticity of gross household fuel and carbon tax expenditure with respect to cohort mean one-way commute duration across Canadian CMAs.", mm_fp, mm_fp_lbl)
        + _inspector_param_card("Vape Excise Youth Skew CI", "gt-param-vape", "−0.54 (64.2% Gen Z)", "Age-ranked concentration index of federal/provincial vaping excise duty payments; negative values below −0.45 indicate severe concentration on cohorts under age 30.", mm_fp, mm_fp_lbl)
        + _inspector_param_card("Senior Health STiK Multiplier", "gt-param-hlth", "3.68× (65+) / 6.49× (80+)", "Ratio of CIHI per-capita public healthcare expenditure for seniors aged 65+ ($14,042) and 80+ ($24,800) relative to the working-age baseline of $3,818/capita.", mm_fp, mm_fp_lbl)
        + '</div>'
        '<h4>Structural Incidence &amp; Behavioral Attribute Scores (hover / tap for definition)</h4>'
        '<div class="study-sector-bars">'
        + _inspector_attr_row("Prime-Age Income & Payroll Tax Concentration", "gt-attr-pit", "79% (Ages 29–60)", "Share of aggregate national personal income tax and CPP/EI payroll contributions funded by Millennials and Gen X after normalizing for population share.", mm_fp, mm_fp_lbl)
        + _inspector_attr_row("Exurban Auto Commute Exposure (Ages 30–54)", "gt-attr-comm", "83% Auto Share (28.4m)", "Weighted share of employed Millennials and Gen X commuting via private vehicle from outer suburban rings, driving peak gross fuel and carbon tax incidence.", mm_fp, mm_fp_lbl)
        + _inspector_attr_row("Boomer Homeownership & Property Tax Share", "gt-attr-prop", "76% ($2,640/cap)", "Homeownership rate among Baby Boomer households, resulting in the highest gross per-capita municipal property tax outflow alongside the lowest tax-to-equity ratio.", mm_fp, mm_fp_lbl)
        + _inspector_attr_row("Life-Cycle Fiscal Asymmetry (2025 vs 1990)", "gt-attr-asym", "88% (+$7,040/cap)", "Expansion of the real young-adult net fiscal deficit between the 1990 Boomer baseline (ages 26–44) and the 2025 Millennial baseline (ages 29–44).", mm_fp, mm_fp_lbl)
        + '</div></aside>'
    )

    cohort_rows = [
        [
            c["cohort"],
            f'${_num(c["totalTaxCad"])} (${_num(c["incomePayrollCad"])} PIT/CPP | ${_num(c["salesTaxCad"])} Sales | ${_num(c["propertyTaxCad"])} Prop)',
            f'${_num(c["totalRewardCad"])}',
            f'{c["netIncidenceCad"]:+,d} / cap ({c["rewardRatio"]:.2f}×)',
            f'{c["commuteMins"]:.1f} min ({c["autoSharePct"]:.1f}% auto)',
            f'${c["fuelCarbonCad"]} fuel/CO2 · ${c["alcoholTaxCad"]} alc · ${c["vapeTaxCad"]} vape',
            c["driverNote"],
        ]
        for c in cohorts
    ]

    pandas_box = (
        '<details class="wb-schema-details" open>'
        '<summary>🐍 View reproducible Pandas analysis script (<code>generational_taxes_pandas.py</code>)</summary>'
        f'<pre class="wb-bars" style="padding:14px; border:1px solid #69d4cf44; border-radius:8px; background:#080b14; overflow-x:auto;"><code>{_e(data["pandasScript"])}</code></pre>'
        '</details>'
    )

    return f'''<main id="main-content" class="collection-page sports-page athletics-page study-page">{lead}
      {tab_bar}
      {_hero("Macroeconomics / Fiscal Policy", "Study ST-09 · Gemini 4 Argon + Pandas", "Who pays the bill,<br>and who gets <em>rewarded.</em>", deck, actions, art)}
      <p class="sports-scope">Workbench Study ST-09 · Executed on Mobile via <strong>{_e(data["model"])}</strong> &amp; promoted to canonical multi-plot dashboard · Grounded in Statistics Canada DHEA (Tables 36-10-0587-01 &amp; 36-10-0588-01), Survey of Household Spending (SHS), Census/LFS Commuting Supplements, CTNS Vaping &amp; Nicotine Survey, CIHI National Health Expenditure Database (1975–2025), and PBO Carbon &amp; Excise Reports.</p>
      {_section("01", "Real tax burden vs. fiscal rewards", "Population-normalized per-capita taxes paid vs. cash and healthcare/education transfers received (2024 CAD).", "gen-tax-burden-title",
                '<p class="sports-legend"><span class="study-key-submerged">■ Real Gross Taxes Paid per Capita (2024 CAD)</span>'
                '<span class="study-key-surface">■ Real Fiscal Rewards Received per Capita (OAS/CPP/CCB + Healthcare &amp; Education STiK)</span></p>'
                + _gen_tax_burden_rewards_svg(cohorts)
                + metrics
                + gen_inspector
                + '<p>To eliminate demographic bulge bias and inflation distortion, every cohort is normalized by its population count \\(N_{g,t}\\) and deflated to constant 2024 Canadian dollars. '
                'Prime-working-age <strong>Generation X (ages 45–60)</strong> and <strong>Millennials (ages 29–44)</strong> carry net fiscal burdens of <strong>−$18,580/capita</strong> (\\(\\Lambda = 0.41\\times\\)) and <strong>−$13,440/capita</strong> (\\(\\Lambda = 0.50\\times\\)), '
                'whereas <strong>Baby Boomers (61–79)</strong> and the <strong>Silent Generation (80+)</strong> receive net fiscal rewards of <strong>+$13,330/capita</strong> (\\(\\Lambda = 1.94\\times\\)) and <strong>+$24,440/capita</strong> (\\(\\Lambda = 3.68\\times\\)) driven by OAS/GIS, CPP payouts, and age-weighted CIHI healthcare Social Transfers in Kind ($14,042 to $24,800/capita).</p>'
                + _table("Population-normalized real annual tax burden, public transfer rewards, commute duration, and excise incidence across 8 generational cohorts (2024 CAD).",
                         ["Generation / Era", "Gross Tax / Cap (Breakdown)", "Fiscal Rewards / Cap", "Net Incidence (Ratio)", "Mean 1-Way Commute", "Fuel/CO2, Alcohol & Vape Tax", "Key Structural Driver"],
                         cohort_rows, "gen-tax-cohorts-table"))}
      {_section("02", "Tax instrument mix over time (1985–2025)", "How income/payroll, sales (GST/HST), property tax, and sin/carbon excise shifted across eras.", "gen-tax-mix-title",
                '<p>Comparing <strong>Millennials in 2025 (ages 29–44)</strong> against <strong>Baby Boomers at the exact same life-cycle stage in 1990 (ages 26–44)</strong> reveals a <strong>+$7,040/capita (+35.5%) increase in real tax burden</strong>. '
                'In 1990, the combined employer-employee CPP payroll rate was 4.4% under a 5.8 : 1 worker-to-retiree support ratio, and neither the federal carbon levy nor vaping excise existed. '
                'In 2025, Millennials pay an 11.9%–13.9% enhanced CPP1/CPP2 payroll rate under a 3.4 : 1 support ratio, alongside higher shelter-driven property and sales taxes. '
                'Meanwhile, <strong>Baby Boomers (76% homeownership)</strong> pay the highest absolute municipal property tax ($2,640/capita), though it represents just 0.38% of their accumulated home equity versus 1.15% for leveraged young buyers.</p>'
                + '<p class="sports-legend"><span style="color:#bba1ff;font-weight:700;">■ Income &amp; Payroll Tax (PIT + CPP/EI)</span>'
                '<span style="color:#69d4cf;font-weight:700;">■ Sales Tax (GST/HST/PST)</span>'
                '<span style="color:#f7ab65;font-weight:700;">■ Municipal Property Tax</span>'
                '<span style="color:#f28b82;font-weight:700;">■ Fuel/Carbon, Alcohol &amp; Vape Excise</span></p>'
                + _gen_tax_mix_svg(cohorts))}
      {_section("03", "Commute times, carbon/fuel tax & youth vape excise", "Why exurban housing geometry taxes Millennial/Gen X commuters while vaping excise targets Gen Z.", "gen-tax-commute-title",
                '<p>Indirect excise taxes exhibit the sharpest generational divergence in the entire tax code:</p>'
                '<ul>'
                '<li><strong>Average Commute Duration &amp; Fuel/Carbon Tax (Millennials &amp; Gen X):</strong> Priced out of transit-dense urban cores by high home price-to-income ratios, Millennials (ages 29–44) and Gen X (ages 45–60) log the longest one-way commutes in Canada at <strong>28.4 minutes</strong> (81.6% private auto share) and <strong>27.6 minutes</strong> (84.8% auto share), compared with 21.8 minutes for Boomers at the same age in 1990. With a commute-to-carbon elasticity of \\(\\gamma = 1.34\\), Millennials and Gen X pay <strong>$780 to $815/capita</strong> in gross road-fuel excise and carbon levies (and remain net payers of −$145 to −$185/capita even after quarterly Canada Carbon Rebates, whereas non-commuting seniors receive a +$115 to +$140 net rebate windfall).</li>'
                '<li><strong>Vaping Excise Duty (Gen Z Concentration):</strong> Introduced in October 2022 ($1 per 2 mL) and hiked +12% in July 2024 with provincial harmonization (doubling to $2/2 mL in ON, QC, AB, BC), vaping excise falls <strong>64.2% on Generation Z</strong> ($168/capita, where 30-day prevalence is 19.7% at ages 20–24 versus &lt;1.5% among Boomers, concentration index \\(CI = -0.54\\)).</li>'
                '</ul>'
                + '<p class="sports-legend"><span style="color:#69d4cf;font-weight:700;">■ Annual Road-Fuel &amp; Carbon Tax ($/capita)</span>'
                '<span style="color:#f28b82;font-weight:700;">■ Annual Vaping Excise Duty ($/capita)</span>'
                '<span class="ab-key-against">● White marker = Mean One-Way Commute Duration (mins)</span></p>'
                + _gen_commute_excise_svg(cohorts)
                + pandas_box)}
      <section class="sports-section sports-method" aria-labelledby="gen-tax-method-title">
        <p class="sports-kicker">The evidence desk</p>
        <h2 id="gen-tax-method-title">Sources, LaTeX paper, Pandas script, and downloads.</h2>
        <ul>
          <li><strong>National accounts &amp; household surveys:</strong> Statistics Canada <em>Distributions of Household Economic Accounts (DHEA, Tables 36-10-0587-01 &amp; 36-10-0588-01, 1999–2025)</em>, <em>Survey of Household Spending by Age of Reference Person (SHS, Table 11-10-0227-01)</em>, and <em>Census / Labour Force Survey Commuting Reference Tables (98-10-0458-01)</em>.</li>
          <li><strong>Health &amp; excise microdata:</strong> CIHI <em>National Health Expenditure Database (NHEX 1975–2025)</em>, Health Canada <em>Canadian Tobacco and Nicotine Survey (CTNS 2022–2024)</em>, and Parliamentary Budget Officer (PBO) <em>Distributional Carbon Pricing &amp; Fiscal Sustainability Reports</em>.</li>
          <li><strong>Dedicated LaTeX paper &amp; Mental Map integration:</strong> Read the compiled paper at <a href="{paper_href}">Fiscal Policy: Taxes on Generations Paper &amp; PDF ↗</a> and see the integrated notes in <a href="{up_root}Mental-Map/index.html#sec:fiscal-policy">Mental Map § 2.3.3 Fiscal Policy ↗</a>.</li>
        </ul>
        {_downloads(4 if is_subtab else 3, [
            ("studies-gen-tax.json", "Generational Taxes study · JSON"),
            ("studies-gen-tax-cohorts.csv", "8 Generational & Historical Cohorts · CSV"),
        ])}
      </section>
    </main>'''


