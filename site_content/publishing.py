"""Add the portfolio without rebuilding Smash records or running simulations."""

from __future__ import annotations

import csv
from html import escape
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

from .analysis import analyze_code, analyze_music, music_rows
from .athletics import athletics_rows, load_athletics
from .athletics_views import running_body, swimming_body, weightlifting_body
from .atlas import ANCHORS, NODES, ROOT, walk
from .atlas_tree import atlas_schema_script, atlas_tree_body
from .atlas_views import (AI_COST_PAPER, AI_COST_STUDY, AI_COST_TAB, ALBERTA_PAPER, ALBERTA_STUDY, ALGORITHMS, ATLAS, CHANGE_LOG, COMPLETION, CONTROL, DASHBOARD, DATABASE_LEAVES, DIET,
                          FEELINGS, GAS_PAPER, GAS_STUDY, GAS_TAB, GEN_TAX_PAPER, GEN_TAX_STUDY, GEN_TAX_TAB, GUIDE, HOSTED, LEETCODE, LEETCODE_LEAVES, MACRO_PAPER, MACRO_STUDY, NBA, PITCH,
                          PREDICTIONS, QUANTUM, RAP_LEAVES, REMINDERS, REPORT, RULES, RUNNING, SLEEP, SODIUM_PAPER, SODIUM_STUDY, SODIUM_TAB, SWIMMING, TRAFFIC, UFC, UPCOMING, UPDATES, VOCABULARY,
                          WEIGHTLIFTING, WORKBENCH, branch_body, branch_stage, home_hero, leaf_body, prefix, premade_body, strip)
from .basketball import export_rows, load_basketball
from .career import career_body, resume_body
from .catalog import leetcode_catalog, rap_catalog
from .catalog_views import leetcode_content, rap_content
from .health import health_rows, load_health
from .health_views import diet_body, sleep_body
from .studies import load_studies, studies_rows
from .studies_views import ai_cost_study_body, alberta_study_body, gas_study_body, gen_tax_study_body, macro_study_body, sodium_study_body
from .workbench import load_workbench, workbench_rows
from .workbench_views import auth_dialog_html, completion_dashboard_body, database_leaf_content, reminders_dashboard_body, traffic_dashboard_body, updates_dashboard_body, workbench_body
from .creators import FIRST_SECTION_ID, creators_html, scroll_cue_html
from .icons import icon_svg, icons_css, require_complete
from .latex import convert_document
from .pdf import copy_verified_pdf
from .sports_views import basketball_body, sports_body
from .views import feelings_body, leetcode_body, vocabulary_body
from .work_report import prepare_report, report_result

HERE = Path(__file__).parent
# Earlier public URLs keep working: each becomes a small forwarding page.
REDIRECTS = {
    "Gaming/index.html": "Gaming-and-Performance-Log/index.html",
    "Economics/index.html": "Business-and-Economics/index.html",
    "Business/index.html": "Business-and-Economics/index.html",
    "Physics/index.html": "Science-and-Engineering/Physics/index.html",
    "Language/index.html": "Language-and-Programming/index.html",
    "Miscellaneous/index.html": ATLAS,
    "Sports/index.html": "Sports-and-Entertainment/Series-Hub/index.html",
    "Physics/Quantum-Mechanics/index.html": QUANTUM,
    "Physics/Control-Systems/index.html": CONTROL,
    "Miscellaneous/Algorithms/index.html": ALGORITHMS,
    "Miscellaneous/LeetCode/index.html": LEETCODE,
    "Language/Vocabulary/index.html": VOCABULARY,
    "Language/Feelings/index.html": FEELINGS,
    "Sports/Basketball-Series/index.html": DASHBOARD,
    "Sports/Rules/index.html": RULES,
    "Sports/Creator-Pitch/index.html": PITCH,
    "About/Work-Term-Report/index.html": REPORT,
    **{f"Sports-and-Entertainment/NBA-Analytics/{leaf}index.html": f"Sports-and-Entertainment/Sports-Analytics/{leaf}index.html"
       for leaf in ("", "Player-Rankings/", "Metric-Overview/", "Statistics/", "Predictions-and-Results/",
                    "Conditioning/", "Shenanigans/")},
}
EMAIL = "l2mcgrat@uwaterloo.ca"
COPYRIGHT = "© 2026 Liam McGrath. All rights reserved."
LICENSE_TEXT = f"""Copyright (c) 2026 Liam McGrath. All rights reserved.

This repository and the website published from it (liammspandasprojects.org),
including its text, notes, data, analyses, documents, images, icons, designs and
source code, belong to Liam McGrath unless a different owner is noted below.

No license is granted. You may view this material on the website, and on GitHub as
GitHub's Terms of Service allow, but you may not copy, clone for reuse, modify,
republish, distribute, sell or make derivative works from any part of it without
prior written permission from Liam McGrath.

Third-party material keeps its own terms and is not covered by this notice:
- MathJax, in assets/vendor/mathjax, is distributed under the Apache License 2.0;
  its license file is included beside it.
- Names, links and descriptions of other creators refer to their own work and imply
  no affiliation. Owen Paget's photo is used with his permission and may not be reused.
- Super Smash Bros. character names and icons, and any third-party icon sets, belong
  to their respective owners and appear here for commentary and analysis.
- Map screenshots credit the mapping service they were made with.

To ask for permission, email {EMAIL}.
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def safe_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _up(route: str) -> str:
    return "../" * route.count("/")


def _lead(route: str, label: str = "") -> str:
    """Atlas location bar for a page hosted at, or attached below, a destination."""
    key = route.removesuffix("/index.html")
    if key in NODES:
        return strip(NODES[key])
    above, _, name = key.rpartition("/")
    return strip(NODES[above], label or name.replace("-", " ").capitalize()) if above in NODES else ""


def _with_lead(body: str, lead: str) -> str:
    return re.sub(r"<main\b[^>]*>", lambda match: match[0] + lead, body, count=1)


def redirect_html(route: str, target: str) -> str:
    href = escape(_up(route) + target, quote=True)
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Moved | Liam McGrath</title>'
            f'<link rel="canonical" href="{href}"><script src="{_up(route)}assets/redirect.js"></script>'
            f'<meta http-equiv="refresh" content="0; url={href}"><meta name="robots" content="noindex"></head>'
            f'<body><p>This page has moved to <a href="{href}">its new home in the site atlas</a>.</p></body></html>\n')


def header(prefix: str) -> str:
    ic_map = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><circle cx="12" cy="4" r="1.8"/><circle cx="19" cy="8" r="1.8"/><circle cx="19" cy="16" r="1.8"/><circle cx="12" cy="20" r="1.8"/><circle cx="5" cy="16" r="1.8"/><circle cx="5" cy="8" r="1.8"/><path d="M12 5.8v3M17.4 9l-2.6 1.5M17.4 15l-2.6-1.5M12 18.2v-3M6.6 15l2.6-1.5M6.6 9l2.6 1.5"/></svg>'
    ic_atlas = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2.5 20.2 7.2 20.2 16.8 12 21.5 3.8 16.8 3.8 7.2"/><circle cx="12" cy="12" r="2.6"/><path d="M12 2.5v6.9M20.2 7.2l-6 3.5M20.2 16.8l-6-3.5M12 21.5v-6.9M3.8 16.8l6-3.5M3.8 7.2l6 3.5"/></svg>'
    ic_wb = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="5.5" rx="7.5" ry="2.8"/><path d="M4.5 5.5v6.2c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8V5.5"/><path d="M4.5 11.7v6.2c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8v-6.2"/></svg>'
    ic_cre = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.6 5.4 6 .9-4.3 4.2 1 6-5.3-2.8-5.3 2.8 1-6L3.4 9.3l6-.9z"/></svg>'
    ic_smash = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3.4 13.8h17.2M8.6 3.4v17.2"/></svg>'
    ic_comp = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5h16"/><rect x="5.5" y="11" width="3.2" height="6.5" rx=".8"/><rect x="10.4" y="7.5" width="3.2" height="10" rx=".8"/><rect x="15.3" y="4.5" width="3.2" height="13" rx=".8"/></svg>'
    ic_traffic = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><ellipse cx="12" cy="12" rx="3.8" ry="8.5"/><path d="M3.8 12h16.4M5.2 7.8h13.6M5.2 16.2h13.6"/></svg>'
    ic_rem = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
    ic_upd = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 11a8.1 8.1 0 0 0-15.5-2m-.5-4v4h4"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"/></svg>'
    ic_admin = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.5" y="10.5" width="15" height="10" rx="2.4"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/><circle cx="12" cy="15.5" r="1.4"/></svg>'
    ic_pwd = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8" cy="15" r="4"/><path d="M10.8 12.2L19 4m-1.5 1.5l2.5 2.5m-5 1l2 2"/></svg>'
    ic_about = '<svg class="nav-sym" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8.2" r="3.6"/><path d="M5.5 19.5c1.4-3.4 4-5.2 6.5-5.2s5.1 1.8 6.5 5.2"/></svg>'
    return f'''<header class="site-header">
      <a class="brand" href="{prefix}index.html" aria-label="Liam McGrath home"><span class="brand-mark" aria-hidden="true">LM</span><span>LIAM McGRATH<small>AN OPEN NOTEBOOK</small></span></a>
    <nav aria-label="Primary navigation" class="top-symbol-bar"><a class="top-sym-tile" href="{prefix}Mental-Map/index.html">{ic_map}<span class="symbol-caption">Mental Map</span></a><a class="top-sym-tile" href="{prefix}{ATLAS}">{ic_atlas}<span class="symbol-caption">Site Atlas</span></a><a class="top-sym-tile" href="{prefix}{WORKBENCH}">{ic_wb}<span class="symbol-caption">Workbench</span></a><a class="top-sym-tile" href="{prefix}{UPDATES}">{ic_upd}<span class="symbol-caption">Doc Updates</span></a><a class="top-sym-tile" href="{prefix}index.html#{FIRST_SECTION_ID}">{ic_cre}<span class="symbol-caption">Creators</span></a><a class="top-sym-tile" href="{prefix}Smash/index.html">{ic_smash}<span class="symbol-caption">Smash</span></a><a class="top-sym-tile is-admin-tile" href="{prefix}{COMPLETION}" data-wb-admin-only hidden>{ic_comp}<span class="symbol-caption">Map &amp; Site %</span></a><a class="top-sym-tile is-admin-tile" href="{prefix}{TRAFFIC}" data-wb-admin-only hidden>{ic_traffic}<span class="symbol-caption">IP &amp; Traffic</span></a><a class="top-sym-tile is-admin-tile" href="{prefix}{REMINDERS}" data-wb-admin-only hidden>{ic_rem}<span class="symbol-caption">Reminders</span></a><button class="top-sym-tile is-admin-tile" type="button" data-wb-password-open data-wb-admin-only hidden>{ic_pwd}<span class="symbol-caption">Passwords</span></button><button class="top-sym-tile" type="button" data-wb-auth-open>{ic_admin}<span class="symbol-caption">Unlock Admin</span></button><a class="top-sym-tile" href="{prefix}About/index.html">{ic_about}<span class="symbol-caption">About Me</span></a></nav>
    </header>'''


def footer(prefix: str) -> str:
    return (f'<footer class="site-footer"><a href="{prefix}index.html">Liam McGrath · An open notebook</a><span>Ideas are better connected.</span>'
            f'<a href="{prefix}About/index.html">About &amp; documents ↗</a>'
            f'<p class="site-copyright">{COPYRIGHT} No part of this site or its source may be copied or republished without permission. '
            f'<a href="{prefix}LICENSE.txt">License</a></p></footer>')


def shell(title: str, body: str, depth: int = 0, data_file: str | None = None,
          brand_text: str = "", *, math: bool = False, music: bool = False,
          analysis: bool = False, sports: bool = False, styles: tuple[str, ...] = (),
          scripts: tuple[str, ...] = ()) -> str:
    prefix = "../" * depth
    # Retain this argument for the existing generator's public function signature.
    del brand_text
    data = f'<script src="{prefix}{data_file}"></script>' if data_file else ""
    if music:
        data += f'<script defer src="{prefix}assets/data/music-analysis.js"></script>'
    if analysis:
        data += f'<script defer src="{prefix}assets/analysis.js"></script>'
    if sports:
        data += f'<script defer src="{prefix}assets/sports.js"></script>'
    data += ''.join(f'<script defer src="{prefix}{script}"></script>' for script in scripts)
    sports_css = f'<link rel="stylesheet" href="{prefix}assets/sports.css">' if sports else ''
    sports_css += ''.join(f'<link rel="stylesheet" href="{prefix}{style}">' for style in styles)
    maths = (f'<script defer src="{prefix}assets/math-config.js"></script><script defer id="MathJax-script" src="{prefix}assets/vendor/mathjax/tex-chtml.js"></script>') if math else ""
    if 'id="main-content"' not in body:
        body = body.replace("<main", '<main id="main-content"', 1)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Liam McGrath’s connected notebook of science, language, data analysis and creative projects.">
<meta name="theme-color" content="#0d101b"><title>{escape(title)} | Liam McGrath</title>
<link rel="icon" href="{prefix}assets/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/styles.css"><link rel="stylesheet" href="{prefix}assets/portfolio.css"><link rel="stylesheet" href="{prefix}assets/career.css"><link rel="stylesheet" href="{prefix}assets/atlas-icons.css">
{sports_css}{maths}</head><body><a class="skip-link" href="#main-content">Skip to content</a>{header(prefix)}{body}
{footer(prefix)}
{data}<script src="{prefix}assets/site.js"></script><script defer src="{prefix}assets/portfolio.js"></script>
</body></html>'''


def home_html() -> str:
    body = (f'<main id="main-content" class="home-landing home-snap">{home_hero({}, scroll_cue_html(FIRST_SECTION_ID))}'
            f'{creators_html()}{auth_dialog_html()}</main>')
    return shell("Ideas, connected", body, styles=("assets/creators.css",), scripts=("assets/creators.js", "assets/workbench.js"))


def atlas_page(node, mental: dict[str, str], available) -> str:
    """A field or topic hexagon page, or an outlined destination page."""
    body = leaf_body(node, available) if not node.children else branch_body(node, mental, available)
    return shell(node.title, body, node.depth)


def about_html() -> str:
    credentials = [
        ('2019 · AUGUST', 'Deep Learning Specialization', 'Coursera', 'TWNRBDRXJDVR', 'https://www.coursera.org/account/accomplishments/specialization/TWNRBDRXJDVR'),
        ('2019 · JUNE', 'Improving Deep Neural Networks: Hyperparameter tuning, Regularization and Optimization', 'Coursera', 'BE2WTX8S2GL4', 'https://www.coursera.org/account/accomplishments/verify/BE2WTX8S2GL4'),
        ('2019 · NOVEMBER', 'Lean Six Sigma White Belt Certification', 'Six Sigma Management Institute by Dr. Mikel J. Harry', '', ''),
    ]
    items = ''.join(f'<article class="credential"><span class="eyebrow">{date}</span><h3>{title}</h3><p>{issuer}</p>' + (f'<a href="{url}" rel="noopener noreferrer">View credential ↗</a><small>Credential ID: {identifier}</small>' if url else '') + '</article>' for date, title, issuer, identifier, url in credentials)
    return shell('About me', f'''<main id="main-content" class="collection-page"><section class="about-intro"><div class="monogram" aria-hidden="true">L<span>M</span></div><div><p class="eyebrow">Engineer. Learner. Maker.</p><h1>Hi, I’m Liam.</h1><p class="lede">This is where I connect what I learn—from mathematical models and machine learning to music, language and the logic of games.</p><p>BASc in Nanotechnology Engineering<br><strong>University of Waterloo</strong></p><div class="toolbar"><a class="button primary" href="../Mental-Map/index.html">Explore my Mental Map ↗</a><a class="button ghost" href="https://www.linkedin.com/in/liam-mcgrath-54a917111/" rel="noopener noreferrer">LinkedIn ↗</a><a class="text-link" href="https://github.com/l2mcgrat">GitHub ↗</a></div></div></section>
    <section class="about-section"><p class="eyebrow">Learning, with a paper trail</p><h2>Licenses &amp; certifications</h2><p class="lede">A foundation in neural networks and process improvement.</p><div class="credential-grid">{items}</div><p class="method-note">Education and credentials transcribed from the supplied LinkedIn screenshot. Credential links use the displayed IDs; availability has not been independently verified.</p></section>
    {career_body()}</main>''', 1)


def document_html(result: dict, title: str, depth: int, topic_links: str, download: str, *,
                  pdf: str | None = None, lead: str = '', tools: str = '', after: str = '', sidebar: str = '',
                  data_file: str | None = None, scripts: tuple[str, ...] = (),
                  byline: str = 'By Liam McGrath · A living document, not a finished textbook.',
                  note: str = 'Section links stay in this document. Blue topic links open separate readers. Historical writing, editorial corrections and AI-assisted study additions are distinguished in the text. Numbering follows this reader’s order; historical claims still need review.') -> str:
    pdf_link = (f'<a class="button primary" href="{escape(pdf)}" download>Compiled article · PDF ↓</a>'
                if pdf else '')
    body = result['body']
    # Add visibly separate editorial links, never change the authored prose.
    if title == 'Mental Map':
        topics = {
            ANCHORS.get('Science-and-Engineering/Physics/Quantum-Mechanics', 'quantum-mechanics'): (QUANTUM, 'Open the dedicated quantum-mechanics notebook', 'A focused reader with its own contents and source download.'),
            'study-control': (CONTROL, 'Open the illustrated control-systems reader', 'A focused reader with its own contents and source download.'),
            'study-computation': (ALGORITHMS, 'Open the illustrated algorithms reader', 'A focused reader with its own contents and source download.'),
        }
        # Fields and topics link back to their hexagons; live destinations to their pages.
        for node in walk(ROOT):
            if node.path not in ANCHORS or ANCHORS[node.path] in topics:
                continue
            if 1 <= node.depth <= 2:
                topics[ANCHORS[node.path]] = (node.url, f'Explore {node.title} in the site atlas',
                                              'Six linked destinations, each with its own animated hexagon.')
            elif node.path in HOSTED:
                topics[ANCHORS[node.path]] = (node.url, f'Open the {node.title} page', 'A live reader or dashboard for this destination.')
        for heading in result['headings']:
            if heading['id'] in topics:
                url, label, small = topics[heading['id']]
                pattern = f'(id="{re.escape(heading["id"])}"[^>]*>.*?</h[1-6]>)'
                body = re.sub(pattern, lambda m: m[1] + f'<aside class="topic-callout"><span>Go deeper ↗</span><a href="../{escape(url)}">{escape(label)}</a><small>{small}</small></aside>', body, count=1, flags=re.S)
    return shell(title, f'''<main id="main-content" class="document-page">{lead}<div class="reader-top"><div><p class="eyebrow">The connected notebook / LaTeX edition</p><h1>{escape(title)}</h1><p>{escape(byline)}</p></div><div class="toolbar">{pdf_link}<a class="button ghost" href="{escape(download)}" download>Source + images · ZIP ↓</a><button class="button ghost print-reader" type="button">Print / Save PDF</button>{tools}</div></div>
    <div class="reader-layout"><aside class="reader-sidebar">{sidebar}<details class="contents-panel" open><summary>Contents <span>{len(result['headings'])} headings</span></summary><label class="toc-search-label" for="toc-search">Find a section<input id="toc-search" type="search" placeholder="Search the contents…"></label><div id="reader-toc">{result['toc']}</div><p id="toc-empty" hidden>No matching sections.</p></details></aside>
    <div class="reader-column"><nav class="topic-links" aria-label="Deeper topic pages"><strong>Follow a thread ↗</strong>{topic_links}</nav><p class="reader-note">{escape(note)}</p><p class="math-status" role="status">Typesetting equations locally…</p><article class="tex-paper">{body}</article><noscript><p>JavaScript is required for equation typesetting. The contents, text and images remain available; download the LaTeX source for the original formulas.</p></noscript><a class="back-top" href="#main-content">Back to the top ↑</a></div></div>{after}</main>''', depth, data_file, math=True, scripts=scripts)


def request_dialog() -> str:
    """Mental Map change requests: the form drafts an email; nothing is sent or stored by the site."""
    return f'''<dialog class="request-dialog" id="request-change" aria-labelledby="request-title" data-email="{EMAIL}">
      <form class="request-form" method="dialog" id="request-form"><p class="eyebrow">Mental Map · Suggest an edit</p><h2 id="request-title">Request a change</h2>
      <p class="request-intro">Choose where the change belongs, paste your text or .tex, then press Create email. Your email app opens with everything filled in, addressed to Liam; this website does not send or store anything.</p>
      <div class="request-grid"><label for="request-name">Name<input id="request-name" name="name" required maxlength="120" autocomplete="name"></label>
      <label for="request-date">Date<input id="request-date" name="date" type="date" required></label>
      <label for="request-section">Section<select id="request-section" name="section" required></select></label>
      <label for="request-subsection">Subsection<select id="request-subsection" name="subsection" required disabled></select></label>
      <label class="request-wide" for="request-subsubsection">Subsubsection<select id="request-subsubsection" name="subsubsection" disabled></select></label></div>
      <label for="request-content">Content <small>Paste text or .tex content here</small><textarea id="request-content" name="content" rows="9" required maxlength="20000"></textarea></label>
      <p class="request-status" id="request-status" role="status" aria-live="polite"></p>
      <div class="request-actions"><button class="button ghost" type="button" data-request-close>Cancel</button><button class="button primary" type="submit">Create email ✉</button></div></form></dialog>'''


def reader_html(root: Path, site: Path, source: str, name: str, title: str, route: str, related: str, *,
                images: str = 'tex_images', pdf_key: str | None = None, byline: str | None = None, note: str | None = None) -> str:
    """A standalone article read in the site's reader, attached to an atlas page."""
    up = _up(route)
    path = root / source
    assets = site / 'assets' / 'documents' / name
    url = f'{up}assets/documents/{name}'
    result = convert_document(path, root / images, assets, url, source_root=root)
    source_zip(path, assets)
    pdf = copy_verified_pdf(root, pdf_key, assets) if pdf_key else None
    options = {key: value for key, value in (('byline', byline), ('note', note)) if value}
    return document_html(result, title, route.count('/'), related, url + '/source-bundle.zip',
                         pdf=url + '/' + pdf if pdf else None, lead=_lead(route), **options)


def _qm_anchor() -> str:
    return ANCHORS.get('Science-and-Engineering/Physics/Quantum-Mechanics', 'quantum-mechanics')


def quantum_html(root: Path, site: Path, route: str = QUANTUM) -> str:
    up = _up(route)
    source = root / 'Quantum_Mechanics.tex'
    if not source.exists():
        source = root / 'quantum_mechanics.tex'  # Backward-compatible fixture/import name.
    if source.exists():
        assets = site / 'assets' / 'documents' / 'quantum-mechanics'
        images = root / 'tex_images' / 'quantum_mechanics'
        result = convert_document(source, images if images.exists() else source.parent, assets, up + 'assets/documents/quantum-mechanics')
        source_zip(source, assets)
        return document_html(result, 'Quantum mechanics', route.count('/'),
                             f'<a href="{up}Mental-Map/index.html#{_qm_anchor()}">Mental Map ↗</a><a href="../index.html">Physics ↗</a>'
                             f'<a href="{up}{REPORT}">Work-term report ↗</a>',
                             up + 'assets/documents/quantum-mechanics/source-bundle.zip', lead=_lead(route))
    return shell('Quantum mechanics', f'''<main id="main-content" class="collection-page">{_lead(route)}<section class="quantum-intro"><div><p class="eyebrow">Featured notebook / Physics</p><h1>A world written<br>in wavefunctions.</h1><p class="lede">A dedicated home for analytical solutions of the Schrödinger equation—and the mathematics that makes them possible.</p><span class="badge">Full LaTeX manuscript coming next</span><div class="toolbar"><a class="button primary" href="{up}Mental-Map/index.html#{_qm_anchor()}">Read the Mental Map outline ↗</a><a class="button ghost" href="../index.html">More physics →</a></div></div><div class="quantum-art" aria-hidden="true">{icon_svg('Science-and-Engineering/Physics', 'is-playing')}<span>ψ</span><small>THE QUANTUM NOTEBOOK</small></div></section>
    <section class="panel"><h2>From an outline to a deeper study</h2><p>The Mental Map currently provides headings for position, mass, momentum and energy. This dedicated page is ready for the separate quantum-mechanics manuscript, with a linked contents list and LaTeX equation numbering.</p><p class="method-note">No solutions have been added or claimed on your behalf. The exact scope of analytically solvable models will follow the manuscript, rather than claiming an exhaustive list.</p></section></main>''', route.count('/'))


def study_html(root: Path, site: Path, name: str, title: str, anchor: str, route: str, related: str) -> str:
    """Focused views of the same unmodified fragments included in Mental Map."""
    up = _up(route)
    source = root / 'notebook_sources' / 'additions' / f'{name}.tex'
    assets = site / 'assets' / 'documents' / name
    # References are root-prefixed for the canonical notebook/source bundles.
    # Resolve those paths against the repository, still confined to image_dir,
    # rather than copying/rebasing the authored fragment.
    result = convert_document(source, root / 'tex_images' / 'mental_map', assets,
                              f'{up}assets/documents/{name}', source_root=root)
    source_zip(source, assets)
    return document_html(result, title, route.count('/'),
                         f'<a href="{up}Mental-Map/index.html#{anchor}">Mental Map ↗</a>{related}',
                         f'{up}assets/documents/{name}/source-bundle.zip', lead=_lead(route))


def sports_document_html(root: Path, site: Path, key: str, route: str) -> str:
    documents = {
        'basketball-rules': ('basketball_rules.tex', 'First to Four · House rules',
                            'Owner-supplied house rules · Illustrated public edition',
                            'Seven challenges, with three diagrams per game. Safety and consent take priority; operational interpretations and unresolved mechanics are explicitly marked.'),
        'creator-pitch': ('creator_pitch.tex', 'First to Four · Creator pitch',
                         'Original pilot proposal · Draft, not sent',
                         'A proposed basketball and sports-data pilot, not a commissioned production. Jesser, Ludwig and Atrioc are aspirational recipients only; no affiliation or endorsement is implied.'),
    }
    filename, title, byline, note = documents[key]
    source = root / 'notebook_sources' / 'sports' / filename
    assets = site / 'assets' / 'documents' / key
    url = f'{_up(route)}assets/documents/{key}'
    result = convert_document(source, root / 'tex_images' / 'sports', assets, url, source_root=root)
    source_zip(source, assets)
    pdf = copy_verified_pdf(root, key, assets)
    return document_html(result, title, route.count('/'),
                         '<a href="../index.html">Series Hub ↗</a>'
                         '<a href="../Analytics/index.html">Basketball analytics ↗</a>'
                         '<a href="../Rules/index.html">House rules ↗</a>'
                         '<a href="../Creator-Petition/index.html">Creator pitch ↗</a>',
                         url + '/source-bundle.zip', pdf=url + '/' + pdf if pdf else None,
                         byline=byline, note=note, lead=_lead(route))


def work_report_html(root: Path, site: Path, route: str = REPORT) -> str:
    up = _up(route)
    assets = site / 'assets' / 'documents' / 'work-term-report'
    url = up + 'assets/documents/work-term-report'
    result = report_result(root, assets, url)
    source_zip(prepare_report(root), assets)
    # This audit contains transformations and whole-input hashes, never removed
    # administrative values or the original class/contact-bearing preamble.
    write(assets / 'edition-manifest.json', safe_json(result['report_manifest']))
    pdf = copy_verified_pdf(root, 'work-term-report', assets)
    return document_html(result, 'Waters in a 1D Carbon Nanotube', route.count('/'),
                         f'<a href="{up}About/index.html">About Liam ↗</a>'
                         f'<a href="{up}About/Resume/index.html">Public résumé ↗</a>'
                         f'<a href="{up}Science-and-Engineering/Physics/index.html">Physics ↗</a>'
                         f'<a href="{url}/edition-manifest.json" download>Edition audit · JSON ↓</a>',
                         url + '/source-bundle.zip', pdf=url + '/' + pdf if pdf else None, lead=_lead(route),
                         byline='Liam McGrath · Historical 3B Nanotechnology Engineering work-term report · Completion date unverified',
                         note='Privacy-safe public article, not the original ECE template. Scientific text, equations, figures, appendices and references are retained. Administrative/contact details are excluded; ambiguous historical references are marked for review. The compiled PDF uses article pagination; its successful compilation is not a new scientific validation.')


def source_zip(source: Path, assets: Path) -> None:
    """Recreate the original relative figure paths beside its unchanged source."""
    manifest = assets / 'source-images.json'
    images = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else [
        {'asset': path.relative_to(assets).as_posix(), 'archive': path.relative_to(assets).as_posix()}
        for path in sorted(assets.rglob('*')) if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.avif'}
    ]
    with zipfile.ZipFile(assets / 'source-bundle.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(source, source.name)
        seen = {source.name}
        for image in images:
            path = (assets / image['asset']).resolve()
            archive = Path(image['archive'])
            if not path.is_relative_to(assets.resolve()) or archive.is_absolute() or '..' in archive.parts:
                raise ValueError('Unsafe source image archive path')
            if archive.as_posix() not in seen:
                bundle.write(path, archive.as_posix())
                seen.add(archive.as_posix())


def load_analysis(root: Path, name: str, function, repo: Path) -> dict:
    snapshot = root / 'records' / 'site_content' / f'{name}.json'
    if repo.is_dir():
        result = function(repo)
        write(snapshot, safe_json(result))
    elif snapshot.exists():
        print(f'{name}: local repository missing; using saved analysis snapshot {snapshot.name}')
        result = json.loads(snapshot.read_text(encoding='utf-8'))
        if isinstance(result.get('source', {}).get('methodology'), dict):
            result['source']['methodology']['input'] = 'Saved analysis snapshot: the source repository was unavailable for this build. Metrics and labels have not been recomputed.'
        elif 'methodology' in result:
            result['methodology'] = 'Saved analysis snapshot; source repository unavailable at build time. ' + result['methodology']
    else:
        raise FileNotFoundError(f'{repo.name} is missing and no {name} snapshot exists. Supply a local repository path.')
    return result


def csv_text(rows: list[dict]) -> str:
    if not rows:
        return ''
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        # Keep JSON lossless; protect spreadsheet users from lyric/formula cells.
        writer.writerow({key: ("'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else value) for key, value in row.items()})
    return output.getvalue()


def upgrade_existing_pages(site: Path) -> None:
    """Only refresh shared chrome; preserve pre-existing Smash HTML/data edits."""
    for page in site.rglob('*.html'):
        if '.git' in page.parts:
            continue
        content = page.read_text(encoding='utf-8')
        if not re.search(r'href="[^"]*assets/styles\.css"', content):
            continue
        depth = len(page.relative_to(site).parts) - 1
        prefix = '../' * depth
        if 'assets/portfolio.css' not in content:
            content = content.replace('</head>', f'<link rel="stylesheet" href="{prefix}assets/portfolio.css">\n</head>', 1)
        if 'assets/portfolio.js' not in content:
            content = content.replace('</body>', f'<script defer src="{prefix}assets/portfolio.js"></script>\n</body>', 1)
        content = re.sub(r'<header\b[^>]*\bclass=[\'"][^\'"]*\bsite-header\b[^\'"]*[\'"][^>]*>.*?</header>', lambda _: header(prefix), content, count=1, flags=re.S)
        content, footers = re.subn(r'<footer\b[^>]*\bclass=[\'"][^\'"]*\bsite-footer\b[^\'"]*[\'"][^>]*>.*?</footer>', lambda _: footer(prefix), content, count=1, flags=re.S)
        if not footers:
            content = content.replace('</body>', footer(prefix) + '\n</body>', 1)
        main = re.search(r'<main\b[^>]*>', content)
        main_id = re.search(r'\bid=[\'"]([^\'"]+)[\'"]', main[0]) if main else None
        target = main_id[1] if main_id else 'main-content'
        if main and not main_id:
            content = content[:main.start()] + main[0].replace('<main', '<main id="main-content"', 1) + content[main.end():]
        if 'class="skip-link"' not in content:
            content = re.sub(r'<body\b[^>]*>', lambda m: m[0] + f'<a class="skip-link" href="#{escape(target)}">Skip to content</a>', content, count=1)
        if content != page.read_text(encoding='utf-8'):
            write(page, content)


def publish_portfolio(root: Path, site: Path, music: dict | None = None, code: dict | None = None,
                      leetcode: dict | None = None, rap: dict | None = None) -> dict:
    root, site = root.resolve(), site.resolve()
    assets = site / 'assets'
    vendor = HERE / 'node_modules' / 'mathjax' / 'es5'
    fallback_vendor = root / 'LiamMs_PandasProjects' / 'assets' / 'vendor' / 'mathjax'
    if not vendor.exists():
        if fallback_vendor.exists():
            vendor = fallback_vendor
        else:
            raise FileNotFoundError('Local MathJax is missing. Install the dependencies in site_content with npm ci before building.')
    if music is None:
        music = load_analysis(root, 'music-analysis', analyze_music, root.parent / 'music_work')
    if code is None:
        code = load_analysis(root, 'code-analysis', analyze_code, root.parent / 'leetcode_problems')
    if leetcode is None:
        leetcode = load_analysis(root, 'leetcode-catalog', leetcode_catalog, root.parent / 'leetcode_problems')
    if rap is None:
        rap = load_analysis(root, 'rap-catalog', rap_catalog, root.parent / 'music_work')
    for asset in (HERE / 'web').iterdir():
        if asset.is_file():
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, assets / asset.name)
    shutil.copytree(HERE / 'web' / 'creators', assets / 'creators', dirs_exist_ok=True)
    write(site / 'LICENSE.txt', LICENSE_TEXT)
    if vendor.resolve() != (assets / 'vendor' / 'mathjax').resolve():
        shutil.copytree(vendor, assets / 'vendor' / 'mathjax', dirs_exist_ok=True)
    mathjax_license = HERE / 'node_modules' / 'mathjax' / 'LICENSE'
    if mathjax_license.is_file():
        shutil.copy2(mathjax_license, assets / 'vendor' / 'mathjax' / 'LICENSE')
    write(assets / 'data' / 'music-analysis.json', safe_json(music))
    write(assets / 'data' / 'music-analysis.js', 'window.MUSIC_ANALYSIS=' + safe_json(music) + ';')
    write(assets / 'data' / 'code-analysis.json', safe_json(code))
    for name, rows in music_rows(music).items():
        write(assets / 'data' / f'music-{name}.csv', csv_text(rows))
    basketball = load_basketball(root)
    # The public-shortname source is validated first, then distributed unchanged
    # in meaning. Unknown score/time fields are not coerced to points or zeroes.
    raw_basketball = json.loads((root / 'records/basketball/series.json').read_text(encoding='utf-8'))
    write(assets / 'data/basketball-source.json', safe_json(raw_basketball))
    basketball['sourceDownloadAvailable'] = True
    write(assets / 'data/basketball-analysis.json', safe_json(basketball))
    write(assets / 'data/basketball-analysis.js', 'window.BASKETBALL_ANALYSIS=' + safe_json(basketball) + ';')
    for name, rows in export_rows(basketball).items():
        write(assets / 'data' / f'basketball-{name}.csv', csv_text(rows))
    athletics = load_athletics(root)
    for key, data in athletics.items():
        write(assets / 'data' / f'athletics-{key}.json', safe_json(data))
    for name, rows in athletics_rows(athletics).items():
        write(assets / 'data' / f'athletics-{name}.csv', csv_text(rows))
    health = load_health(root)
    for key, data in health.items():
        write(assets / 'data' / f'health-{key}.json', safe_json(data))
    for name, rows in health_rows(health).items():
        write(assets / 'data' / f'health-{name}.csv', csv_text(rows))
    workbench = load_workbench(root)
    write(assets / 'data' / 'workbench.json', safe_json(workbench))
    for name, rows in workbench_rows(workbench).items():
        write(assets / 'data' / f'workbench-{name}.csv', csv_text(rows))
    studies = load_studies()
    for key, data in studies.items():
        write(assets / 'data' / f'studies-{key.replace("_", "-")}.json', safe_json(data))
    for name, rows in studies_rows(studies).items():
        write(assets / 'data' / f'studies-{name}.csv', csv_text(rows))
    if 'gas' in studies and 'pandasScript' in studies['gas']:
        write(assets / 'data' / 'gas_price_collusion_pandas.py', studies['gas']['pandasScript'])
    if 'sodium' in studies and 'pandasScript' in studies['sodium']:
        write(assets / 'data' / 'sodium_battery_pandas.py', studies['sodium']['pandasScript'])
    if 'ai_cost' in studies and 'pandasScript' in studies['ai_cost']:
        write(assets / 'data' / 'ai_cost_economics_pandas.py', studies['ai_cost']['pandasScript'])
    if 'gen_tax' in studies and 'pandasScript' in studies['gen_tax']:
        write(assets / 'data' / 'generational_taxes_pandas.py', studies['gen_tax']['pandasScript'])
    pub_studies_path = root / 'records' / 'workbench' / 'published_studies.json'
    if pub_studies_path.is_file():
        pub_studies_data = json.loads(pub_studies_path.read_text(encoding='utf-8'))
    else:
        pub_studies_data = {"version": 1, "runs": {}, "entries": {}, "deleted": []}
    write(assets / 'data' / 'live-cloud-studies.json', safe_json(pub_studies_data))
    result = convert_document(root / 'mental_map.tex', root / 'tex_images' / 'mental_map', assets / 'documents' / 'mental-map', '../assets/documents/mental-map')
    source_zip(root / 'mental_map.tex', assets / 'documents' / 'mental-map')
    mental = {heading['id']: heading['title'] for heading in result['headings']}
    missing = sorted(set(ANCHORS.values()) - set(mental))
    unmarked = sorted(node.key for node in NODES.values() if node.depth and node.path not in ANCHORS)
    if missing or unmarked:
        raise ValueError(f'Every atlas page needs its Mental Map heading; missing ids {missing[:5]}, '
                         f'pages without a "% atlas:" marker {unmarked[:5]}')
    require_complete()
    write(assets / 'atlas-icons.css', icons_css())
    write(assets / 'data' / 'atlas-schema.js', atlas_schema_script())
    links = ''.join(f'<a href="../{url}">{label} ↗</a>' for label, url in [
        ('Site atlas', ATLAS), ('Workbench', WORKBENCH), ('How to add notes · guide', GUIDE), ('Quantum mechanics', QUANTUM),
        ('Control systems', CONTROL), ('Algorithms', ALGORITHMS), ('Vocabulary', VOCABULARY), ('Feelings explorer', FEELINGS),
        ('Change log', CHANGE_LOG)])
    request = (f'<a class="button ghost" href="mailto:{EMAIL}?subject=Mental%20Map%20change%20request" data-request-open>'
               'Request a change ✉</a>')

    def available(item) -> bool:
        return not item.legacy or (site / item.legacy).is_file()

    pages = {
        'index.html': home_html(), 'About/index.html': about_html(),
        'About/Resume/index.html': shell('Public résumé', resume_body(), 2),
        'Mental-Map/index.html': document_html(result, 'Mental Map', 1, links, '../assets/documents/mental-map/source-bundle.zip',
                                               tools=request, after=request_dialog(), data_file='assets/data/atlas-schema.js',
                                               sidebar=(f'<a class="request-side" href="mailto:{EMAIL}?subject=Mental%20Map%20change%20request" '
                                                        'data-request-open>Suggest a change to this section ✉</a>'),
                                               scripts=('assets/request-change.js',)),
        ATLAS: shell('Site atlas', atlas_tree_body(), 1, 'assets/data/atlas-schema.js',
                     styles=('assets/atlas-tree.css',), scripts=('assets/atlas-tree.js',)),
        WORKBENCH: shell('Notebook Workbench', workbench_body(workbench, '../'), 1,
                         styles=('assets/sports.css', 'assets/athletics.css', 'assets/workbench.css'),
                         scripts=('assets/workbench.js',)),
        UPDATES: shell('Google Docs & Site Integration Hub', updates_dashboard_body(root, athletics, health, '../'), 1,
                       styles=('assets/sports.css', 'assets/athletics.css', 'assets/workbench.css'),
                       scripts=('assets/workbench.js',)),
        COMPLETION: shell('Map & Site % Reflection', completion_dashboard_body(root, '../'), 1,
                          styles=('assets/sports.css', 'assets/athletics.css', 'assets/workbench.css'),
                          scripts=('assets/workbench.js',)),
        TRAFFIC: shell('IP & Traffic Reflection', traffic_dashboard_body(workbench, '../'), 1,
                       styles=('assets/sports.css', 'assets/athletics.css', 'assets/workbench.css'),
                       scripts=('assets/workbench.js',)),
        REMINDERS: shell('Reminders · REABS (Random Extra Additional Bullshit)', reminders_dashboard_body(workbench, '../'), 1,
                         styles=('assets/sports.css', 'assets/athletics.css', 'assets/workbench.css'),
                         scripts=('assets/workbench.js',)),
    }
    pages.update({node.url: atlas_page(node, mental, available) for node in walk(ROOT) if node.depth})
    for path in LEETCODE_LEAVES + RAP_LEAVES:
        node = NODES[path]
        render, catalog = (leetcode_content, leetcode) if path in LEETCODE_LEAVES else (rap_content, rap)
        lede, content = render(path.rsplit('/', 1)[1], catalog, prefix(node))
        pages[node.url] = shell(node.title, leaf_body(node, available, content, lede), node.depth, styles=('assets/catalog.css',))
    for path in DATABASE_LEAVES:
        node = NODES[path]
        lede, content = database_leaf_content(path.rsplit('/', 1)[1], workbench, prefix(node))
        pages[node.url] = shell(node.title, leaf_body(node, available, content, lede), node.depth,
                                styles=('assets/catalog.css',))
    series = NODES['Sports-and-Entertainment/Series-Hub']
    hosted = {
        QUANTUM: quantum_html(root, site),
        ALGORITHMS: study_html(root, site, 'computation', 'Data structures & algorithms', 'study-computation', ALGORITHMS,
                               f'<a href="../../../{LEETCODE}">Practice source index ↗</a>'),
        CONTROL: study_html(root, site, 'control', 'Control systems', 'study-control', CONTROL,
                            '<a href="../index.html">Classical mechanics ↗</a>'),
        REPORT: work_report_html(root, site),
        RULES: sports_document_html(root, site, 'basketball-rules', RULES),
        PITCH: sports_document_html(root, site, 'creator-pitch', PITCH),
        DASHBOARD: shell('First to Four · Basketball series', basketball_body(basketball, _lead(DASHBOARD)), 3,
                         'assets/data/basketball-analysis.js', sports=True),
        series.url: shell(series.title, sports_body(basketball, branch_stage(series, mental, available)), 2,
                          'assets/data/basketball-analysis.js', sports=True),
        VOCABULARY: shell('Vocabulary explorer', _with_lead(vocabulary_body(music, section='Text Analysis', root='../../../'), _lead(VOCABULARY)),
                          3, music=True, analysis=True),
        FEELINGS: shell('Feelings explorer', _with_lead(feelings_body(music, section='Text Analysis', root='../../../'), _lead(FEELINGS)),
                        3, music=True, analysis=True),
        LEETCODE: shell('LeetCode & algorithms', _with_lead(leetcode_body(code, section='LeetCode', root='../../../'), _lead(LEETCODE)),
                        3, analysis=True),
        GUIDE: reader_html(root, site, 'notebook_sources/guides/mental_map_guide.tex', 'mental-map-guide',
                           'Adding notes to the Mental Map', GUIDE,
                           '<a href="../index.html">Mental Map ↗</a><a href="../../Science-and-Engineering/index.html">Science &amp; Engineering ↗</a>',
                           pdf_key='mental-map-guide', byline='Liam McGrath · A how-to for filling the 216 destinations',
                           note='Steps for moving notes from a Gemini chat log into the right subsubsection, checking them and publishing both repositories.'),
        CHANGE_LOG: reader_html(root, site, 'notebook_sources/website/change_log.tex', 'website-change-log', 'Website change log', CHANGE_LOG,
                                '<a href="../index.html">Website Changes ↗</a><a href="../Upcoming-Changes/index.html">Upcoming changes ↗</a>',
                                byline='Liam McGrath · Requested and implemented changes, newest first',
                                note='Each date lists what was requested and what was built. Planned work is in Upcoming Changes.'),
        UPCOMING: reader_html(root, site, 'notebook_sources/website/upcoming_changes.tex', 'website-upcoming', 'Upcoming website changes', UPCOMING,
                              '<a href="../index.html">Website Changes ↗</a><a href="../Change-Log/index.html">Change log ↗</a>',
                              byline='Liam McGrath · Planned work and the change-request database plan',
                              note='Requests are grouped by the date they were made; finished items move to the change log.'),
        UFC: shell('UFC predictions vs. outcomes', premade_body(
            NODES[PREDICTIONS], 'UFC predictions vs. outcomes', 'Sports Analytics · Premade tab',
            'Fight picks recorded before each event, then checked against the results.',
            ('Log each pick before the event: fighters, predicted winner, method and confidence.',
             'Add the official result after the event, without editing the original pick.',
             'Score the picks over time: hit rate, plus a calibration check of the stated confidence.'), _lead(UFC, 'UFC predictions vs. outcomes')), 4),
        NBA: shell('NBA predictions vs. outcomes', premade_body(
            NODES[PREDICTIONS], 'NBA predictions vs. outcomes', 'Sports Analytics · Premade tab',
            'Game and season predictions recorded in advance, then scored against what happened.',
            ('Log each prediction before tip-off or the season start, with the reasoning and confidence.',
             'Add the final score or standing once it is official, without editing the original call.',
             'Score the record over time, by game and by season-long call.'), _lead(NBA, 'NBA predictions vs. outcomes')), 4),
    }
    for key, route, body in (('running', RUNNING, running_body), ('swimming', SWIMMING, swimming_body),
                             ('weightlifting', WEIGHTLIFTING, weightlifting_body)):
        node = NODES[route.removesuffix('/index.html')]
        rendered = (running_body(athletics[key], _lead(route), athletics['tempo']) if key == 'running'
                    else body(athletics[key], _lead(route)))
        hosted[route] = shell(f'{node.title} log', rendered, 3,
                              styles=('assets/sports.css', 'assets/athletics.css'))
        overview = route.replace('index.html', 'Overview/index.html')
        hosted[overview] = reader_html(root, site, f'notebook_sources/athletics/{key}.tex', f'athletics-{key}', f'{node.title}: overview', overview,
                                       f'<a href="../index.html">{node.title} dashboard ↗</a><a href="../../index.html">Athletics ↗</a>',
                                       images='tex_images/athletics', byline='Liam McGrath · Training overview',
                                       note='History and context for the logged training. The dashboard holds every logged value.')
    hosted[SLEEP] = shell('Sleep & dream log', sleep_body(health['sleep'], _lead(SLEEP)), 3,
                          styles=('assets/sports.css', 'assets/athletics.css', 'assets/health.css'))
    hosted[DIET] = shell('Diet & calorie tracking', diet_body(health['diet'], athletics, _lead(DIET)), 3,
                         styles=('assets/sports.css', 'assets/athletics.css', 'assets/health.css'))
    hosted[MACRO_STUDY] = shell('Economic Growth · The AI Iceberg Index', macro_study_body(studies['macro'], _lead(MACRO_STUDY)), 3,
                                styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
                                scripts=('assets/studies.js',))
    hosted[MACRO_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/macro_ai_iceberg.tex', 'macro-ai-iceberg',
        'Above and Beneath the Surface: The AI Iceberg Index', MACRO_PAPER,
        '<a href="../index.html">Interactive Iceberg study ↗</a><a href="../../index.html">Macroeconomics ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='macro-ai-iceberg',
        byline='Liam McGrath · Macroeconomics & labor-exposure study',
        note='Formal decomposition of visible vs. submerged AI skill exposure across 12 NAICS sectors and 12 regional economies.',
    )
    hosted[ALBERTA_STUDY] = shell('Public Policy · 2026 Alberta Referendum', alberta_study_body(studies['alberta'], _lead(ALBERTA_STUDY)), 3,
                                  styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
                                  scripts=('assets/studies.js',))
    hosted[ALBERTA_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/alberta_referendum_2026.tex', 'alberta-referendum-2026',
        'Three Ballots in One: The 2026 Alberta Referendum', ALBERTA_PAPER,
        '<a href="../index.html">Interactive Referendum study ↗</a><a href="../../index.html">Law &amp; Policy ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='alberta-referendum-2026',
        byline='Liam McGrath · Constitutional & demographic voting study',
        note='All 10 October 19, 2026 ballot questions, ballot roll-off, demographic cross-tabs, and coalition motivation analysis.',
    )
    hosted[GAS_STUDY] = shell(
        'Game Theory · Gas Price Collusion & Oligopoly Supergames',
        gas_study_body(studies['gas'], _lead(GAS_STUDY), is_subtab=False), 3, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[GAS_TAB] = shell(
        'Gas Price Collusion · Game Theory Study Tab',
        gas_study_body(studies['gas'], _lead(GAS_TAB, 'Gas Price Collusion'), is_subtab=True), 4, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[GAS_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/gas_price_collusion.tex', 'gas-price-collusion',
        'Why Gas Prices Feather Down: Oligopoly Supergames & Algorithmic Pricing', GAS_PAPER,
        '<a href="../index.html">Interactive Game Theory dashboard ↗</a><a href="../Gas-Price-Collusion/index.html">Gas Price Collusion tab ↗</a><a href="../../index.html">Microeconomics ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='gas-price-collusion',
        byline='Liam McGrath · Microeconomics & Game Theory study (Gemini 4 Argon + Pandas)',
        note='Cross-country retail fuel price decomposition, Rockets & Feathers asymmetric ECM, and repeated Bertrand supergame SPNE thresholds.',
    )
    hosted[SODIUM_STUDY] = shell(
        'Electrochemistry · Sodium Battery Technology & Grid Storage',
        sodium_study_body(studies['sodium'], _lead(SODIUM_STUDY), is_subtab=False), 3, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[SODIUM_TAB] = shell(
        'Sodium Battery Technology · Electrochemistry Study Tab',
        sodium_study_body(studies['sodium'], _lead(SODIUM_TAB, 'Sodium Battery Technology'), is_subtab=True), 4, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[SODIUM_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/sodium_battery_technology.tex', 'sodium-battery-technology',
        'Period 3 Power: Periodic Table Electrochemistry & Grid-Scale Sodium-Ion Batteries', SODIUM_PAPER,
        '<a href="../index.html">Interactive Electrochemistry dashboard ↗</a><a href="../Sodium-Battery-Technology/index.html">Sodium Battery tab ↗</a><a href="../../index.html">Chemistry ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='sodium-battery-technology',
        byline='Liam McGrath · Electrochemistry & energy-storage study (Gemini 4 Argon + Pandas)',
        note='Periodic table origins of Na-ion vs. Li-ion, hard carbon nanopore intercalation, dual Al current collectors, and winter blackout BESS resilience.',
    )
    hosted[AI_COST_STUDY] = shell(
        'Artificial Intelligence · AI Cost & Compute Economics',
        ai_cost_study_body(studies['ai_cost'], _lead(AI_COST_STUDY), is_subtab=False), 3, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[AI_COST_TAB] = shell(
        'AI Cost & Compute Economics · Emerging Industries Study Tab',
        ai_cost_study_body(studies['ai_cost'], _lead(AI_COST_TAB, 'AI Cost & Compute Study'), is_subtab=True), 4, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[AI_COST_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/ai_cost_economics.tex', 'ai-cost-economics',
        'AI Cost & Compute Economics: Token Inference Deflation vs. Frontier Training Capex', AI_COST_PAPER,
        '<a href="../index.html">Interactive AI Cost dashboard ↗</a><a href="../AI-Cost-Study/index.html">AI Cost Study tab ↗</a><a href="../../index.html">Emerging Industries ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='ai-cost-economics',
        byline='Liam McGrath · Emerging Industries & AI Economics study (Gemini 4 Argon + Pandas)',
        note='Chinchilla pre-training scaling vs. HBM3e memory-bandwidth decoding, Sparse MoE + MLA KV-cache compression, Jevons Paradox in reasoning tokens, and enterprise cascade routing.',
    )
    hosted[GEN_TAX_STUDY] = shell(
        'Fiscal Policy · Taxes on Generations Over Time Periods',
        gen_tax_study_body(studies['gen_tax'], _lead(GEN_TAX_STUDY), is_subtab=False), 3, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[GEN_TAX_TAB] = shell(
        'Taxes on Generations Over Time Periods · Fiscal Policy Study Tab',
        gen_tax_study_body(studies['gen_tax'], _lead(GEN_TAX_TAB, 'Taxes on Generations'), is_subtab=True), 4, math=True,
        styles=('assets/sports.css', 'assets/athletics.css', 'assets/studies.css'),
        scripts=('assets/studies.js',),
    )
    hosted[GEN_TAX_PAPER] = reader_html(
        root, site, 'notebook_sources/studies/generational_taxes.tex', 'generational-taxes',
        'Taxes on Generations Over Time Periods: Real Tax Burden, Fiscal Rewards, Commutes & Excise', GEN_TAX_PAPER,
        '<a href="../index.html">Interactive Fiscal Policy dashboard ↗</a><a href="../Taxes-on-Generations/index.html">Taxes on Generations tab ↗</a><a href="../../index.html">Macroeconomics ↗</a><a href="../../../../Workbench/index.html">Workbench ↗</a>',
        images='tex_images/studies', pdf_key='generational-taxes',
        byline='Liam McGrath · Macroeconomics & Fiscal Policy study (Gemini 4 Argon + Pandas · 20,079 tokens)',
        note='Population-normalized real generational accounting (1985–2025), exurban commute carbon elasticity, youth vaping excise concentration, and senior healthcare STiK multipliers.',
    )
    pages.update(hosted)
    for path, content in pages.items():
        write(site / path, content)
    for path, target in REDIRECTS.items():
        write(site / path, redirect_html(path, target))
    upgrade_existing_pages(site)
    manifest = {'pages': list(pages), 'redirects': list(REDIRECTS), 'atlasNodes': len(NODES),
                'document': {key: result[key] for key in ('equation_count', 'image_count', 'warnings')},
                'music': music['summary'], 'codeModules': code['moduleCount'], 'basketball': basketball['summary'],
                'leetcodeEntries': len(leetcode['problems']), 'rapSongs': len(rap['songs'])}
    write(assets / 'data' / 'portfolio-build.json', safe_json(manifest))
    print(f'Portfolio generated: {site} · {len(pages)} pages · {len(REDIRECTS)} redirects · {len(result["headings"])} document headings')
    return manifest