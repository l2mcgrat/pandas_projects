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
from .latex import convert_document
from .views import feelings_body, leetcode_body, vocabulary_body

HERE = Path(__file__).parent
CATEGORIES = ["Gaming", "Economics", "Business", "Physics", "Language", "Miscellaneous"]
DESCRIPTIONS = {
    "Gaming": "Competition, measured.", "Economics": "Systems of exchange.",
    "Business": "From process to insight.", "Physics": "Models of the world.",
    "Language": "Words, rhythm & meaning.", "Miscellaneous": "Room for curiosity.",
}
ICONS = {
    "Gaming": '<path d="M18 22h28l6 21c1 5-4 8-8 4l-6-6H26l-6 6c-4 4-9 1-8-4Z"/><path d="M23 27v12m-6-6h12"/><circle cx="41" cy="29" r="2"/><circle cx="46" cy="35" r="2"/>',
    "Economics": '<path d="M12 48h40M16 41V30m10 11V24m11 17V19m11 22V10"/><path class="icon-draw" d="m12 25 13-9 11 3L51 7"/>',
    "Business": '<rect x="12" y="20" width="40" height="30" rx="5"/><path d="M24 20v-7h16v7M12 32q20 12 40 0M28 35h8"/>',
    "Physics": '<g class="icon-orbit"><ellipse cx="32" cy="32" rx="25" ry="10"/><ellipse cx="32" cy="32" rx="25" ry="10" transform="rotate(60 32 32)"/><ellipse cx="32" cy="32" rx="25" ry="10" transform="rotate(120 32 32)"/></g><circle cx="32" cy="32" r="4"/>',
    "Language": '<path d="M14 14h36v28H29L17 51v-9h-3Z"/><path class="icon-wave" d="M22 27v6m7-12v18m7-16v12m7-9v6"/>',
    "Miscellaneous": '<path class="icon-orbit" d="m32 8 7 17 17 7-17 7-7 17-7-17-17-7 17-7Z"/><circle cx="32" cy="32" r="5"/>',
    "Mental Map": '<path d="M32 32 12 19m20 13 20-13M32 32v23m0-23V9M32 32 12 46m20-14 20 14"/><circle cx="32" cy="32" r="7"/><circle cx="12" cy="19" r="4"/><circle cx="52" cy="19" r="4"/><circle cx="12" cy="46" r="4"/><circle cx="52" cy="46" r="4"/><circle cx="32" cy="9" r="4"/><circle cx="32" cy="55" r="4"/>',
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def safe_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def icon(name: str) -> str:
    return f'<svg class="topic-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'


def header(prefix: str) -> str:
    return f'''<header class="site-header">
      <a class="brand" href="{prefix}index.html" aria-label="Liam McGrath home"><span class="brand-mark" aria-hidden="true">LM</span><span>LIAM McGRATH<small>AN OPEN NOTEBOOK</small></span></a>
      <nav aria-label="Primary navigation"><a href="{prefix}Mental-Map/index.html">Mental Map</a><a href="{prefix}Language/index.html">Language</a><a href="{prefix}Smash/index.html">Smash</a><a href="{prefix}About/index.html">About me <span aria-hidden="true">↗</span></a></nav>
    </header>'''


def shell(title: str, body: str, depth: int = 0, data_file: str | None = None,
          brand_text: str = "", *, math: bool = False, music: bool = False,
          analysis: bool = False) -> str:
    prefix = "../" * depth
    # Retain this argument for the existing generator's public function signature.
    del brand_text
    data = f'<script src="{prefix}{data_file}"></script>' if data_file else ""
    if music:
        data += f'<script defer src="{prefix}assets/data/music-analysis.js"></script>'
    if analysis:
        data += f'<script defer src="{prefix}assets/analysis.js"></script>'
    maths = (f'<script defer src="{prefix}assets/math-config.js"></script><script defer id="MathJax-script" src="{prefix}assets/vendor/mathjax/tex-chtml.js"></script>') if math else ""
    if 'id="main-content"' not in body:
        body = body.replace("<main", '<main id="main-content"', 1)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Liam McGrath’s connected notebook of science, language, data analysis and creative projects.">
<meta name="theme-color" content="#0d101b"><title>{escape(title)} | Liam McGrath</title>
<link rel="icon" href="{prefix}assets/mark.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/styles.css"><link rel="stylesheet" href="{prefix}assets/portfolio.css">
{maths}</head><body><a class="skip-link" href="#main-content">Skip to content</a>{header(prefix)}{body}
<footer class="site-footer"><a href="{prefix}index.html">Liam McGrath · An open notebook</a><span>Ideas are better connected.</span><a href="{prefix}About/index.html">About &amp; documents ↗</a></footer>
{data}<script src="{prefix}assets/site.js"></script><script defer src="{prefix}assets/portfolio.js"></script>
</body></html>'''


def card(url: str, eyebrow: str, title: str, description: str, symbol: str = "") -> str:
    art = icon(symbol) if symbol in ICONS else '<span class="card-arrow" aria-hidden="true">↗</span>'
    return f'<a class="feature-card" href="{escape(url)}">{art}<span class="eyebrow">{escape(eyebrow)}</span><h3>{escape(title)}</h3><p>{escape(description)}</p><span class="card-link">Explore <span aria-hidden="true">↗</span></span></a>'


def home_html() -> str:
    nodes = "".join(f'<a class="hex-node node-{name.lower()}" data-topic="{name.lower()}" href="{name}/index.html"><span class="hex-inner">{icon(name)}<strong>{name}</strong></span></a>' for name in CATEGORIES)
    # Same centres as the CSS percentages; every spoke terminates at a real link.
    points = [(300, 78), (492, 189), (492, 411), (300, 522), (108, 411), (108, 189)]
    spokes = "".join(f'<path class="map-spoke spoke-{name.lower()}" d="M300 300 L{x} {y}"/>' for name, (x, y) in zip(CATEGORIES, points))
    return shell("Ideas, connected", f'''<main id="main-content" class="home-landing">
    <section class="home-stage"><div class="home-copy"><p class="eyebrow"><span class="status-dot"></span> The personal atlas of Liam McGrath</p>
      <h1>Curiosity.<br>Patterns.<br><em>Connections.</em></h1>
      <p class="home-description">A living notebook at the intersection of science, data and the things that make us human.</p>
      <div class="home-actions"><a class="button primary" href="Mental-Map/index.html">Enter the Mental Map <span aria-hidden="true">↗</span></a><a class="text-link" href="About/index.html">A little about me →</a></div>
      <div class="home-caption"><span>01 — EXPLORE THE CONNECTIONS</span><p>Six fields. One ever-growing map.</p></div></div>
      <div class="map-column"><nav class="hex-map" aria-label="Connected fields of exploration"><div class="hex-frame" aria-hidden="true"></div>
        <svg class="map-connections" viewBox="0 0 600 600" aria-hidden="true"><path class="map-perimeter" d="M300 78 492 189 492 411 300 522 108 411 108 189Z"/>{spokes}<circle class="map-ring" cx="300" cy="300" r="103"/></svg>
        {nodes}<a class="hex-node node-mental-map" data-topic="mental-map" href="Mental-Map/index.html"><span class="hex-inner">{icon('Mental Map')}<small>THE CONNECTING THREAD</small><strong>Mental Map</strong><span class="map-enter">Open notebook ↗</span></span></a>
      </nav><p class="map-hint" id="map-hint" aria-live="polite">Follow a thread. See where it leads.</p></div>
    </section><section class="home-discover" aria-labelledby="discover-title"><div class="section-heading"><div><p class="eyebrow">A few places to begin</p><h2 id="discover-title">Inside the notebook</h2></div><a class="text-link" href="Mental-Map/index.html">See the full map ↗</a></div>
    <div class="card-grid">{card('Physics/Quantum-Mechanics/index.html', 'Featured / Physics', 'The quantum notebook', 'A home for analytical solutions, mathematical detail and the questions behind them.', 'Physics')}
    {card('Language/Vocabulary/index.html', 'Language / Original writing', 'A vocabulary in songs', 'Explore repetitions, rare words and the breadth of a growing lyric archive.', 'Language')}
    {card('Miscellaneous/LeetCode/index.html', 'Miscellaneous / Practice', 'Thinking in algorithms', 'Arrays, hash tables and trees. A small, open record of working through problems.', 'Miscellaneous')}</div></section></main>''')


def collection_html(label: str, site: Path) -> str:
    title = {"Physics": "From first principles.", "Language": "Words have a world inside.", "Gaming": "Play. Measure. Understand.", "Economics": "How systems exchange value.", "Business": "Better questions. Better decisions.", "Miscellaneous": "Follow the interesting bits."}[label]
    cards = []
    if label == "Language":
        cards = [card('Vocabulary/index.html', '01 / Lexical diversity', 'Vocabulary explorer', 'Search word frequencies, compare song versions and explore MATTR-50.', 'Language'), card('Feelings/index.html', '02 / Text & emotion', 'The feelings explorer', 'An interactive wheel, a line-by-line reader, and the evidence behind each suggestion.', 'Mental Map')]
    elif label == "Miscellaneous":
        cards = [card('LeetCode/index.html', '01 / Coding practice', 'LeetCode & algorithms', 'A starting collection, not a complete count of problems solved.', 'Miscellaneous')]
    elif label == "Gaming":
        cards = [card('../Smash/index.html', '01 / Tournament analytics', 'Super Smash Bros.', 'Fighter profiles, rankings, round histories and comparative analysis.', 'Gaming')]
    elif label == "Physics":
        cards = [card('Quantum-Mechanics/index.html', 'Featured / Analytical physics', 'Quantum mechanics', 'A dedicated mathematical notebook. The full source document is next.', 'Physics')]
        atlas = site / "Physics" / "Dipole-Atlas"
        if (atlas / "index.html").exists():
            cards.append(card('Dipole-Atlas/index.html', 'Interactive / Molecular dynamics', 'Dipole Atlas', 'Explore qualitative molecular models, trajectories and downloadable experiments.', 'Mental Map'))
        for run in sorted(atlas.glob('*/index.html')):
            cards.append(card(f'Dipole-Atlas/{run.parent.name}/index.html', 'Experiment archive', run.parent.name.replace('_', ' '), 'Recorded trajectories, methodology and model limitations.'))
    else:
        anchor = "economics" if label == "Economics" else "business"
        cards = [card(f'../Mental-Map/index.html#{anchor}', 'From the Mental Map', f'{label} notes', 'The original notebook is the starting point. More focused studies can grow from here.', label)]
        if label == "Business":
            cards.append(card('../About/index.html', 'Background / Learning', 'About Liam', 'Engineering education and a foundation in deep learning and process improvement.'))
    return shell(label, f'''<main id="main-content" class="collection-page"><div class="page-intro"><a class="crumb" href="../index.html">← The atlas</a><p class="eyebrow">The {label.lower()} collection</p><h1>{title}</h1><p class="lede">{DESCRIPTIONS[label]} A part of the larger <a href="../Mental-Map/index.html">Mental Map</a>.</p></div><div class="card-grid">{''.join(cards)}</div></main>''', 1)


def about_html() -> str:
    credentials = [
        ('2019 · AUGUST', 'Deep Learning Specialization', 'Coursera', 'TWNRBDRXJDVR', 'https://www.coursera.org/account/accomplishments/specialization/TWNRBDRXJDVR'),
        ('2019 · JUNE', 'Improving Deep Neural Networks: Hyperparameter tuning, Regularization and Optimization', 'Coursera', 'BE2WTX8S2GL4', 'https://www.coursera.org/account/accomplishments/verify/BE2WTX8S2GL4'),
        ('2019 · NOVEMBER', 'Lean Six Sigma White Belt Certification', 'Six Sigma Management Institute by Dr. Mikel J. Harry', '', ''),
    ]
    items = ''.join(f'<article class="credential"><span class="eyebrow">{date}</span><h3>{title}</h3><p>{issuer}</p>' + (f'<a href="{url}" rel="noopener noreferrer">View credential ↗</a><small>Credential ID: {identifier}</small>' if url else '') + '</article>' for date, title, issuer, identifier, url in credentials)
    return shell('About me', f'''<main id="main-content" class="collection-page"><section class="about-intro"><div class="monogram" aria-hidden="true">L<span>M</span></div><div><p class="eyebrow">Engineer. Learner. Maker.</p><h1>Hi, I’m Liam.</h1><p class="lede">This is where I connect what I learn—from mathematical models and machine learning to music, language and the logic of games.</p><p>BASc in Nanotechnology Engineering<br><strong>University of Waterloo</strong></p><div class="toolbar"><a class="button primary" href="../Mental-Map/index.html">Explore my Mental Map ↗</a><a class="button ghost" href="https://www.linkedin.com/in/liam-mcgrath-54a917111/" rel="noopener noreferrer">LinkedIn ↗</a><a class="text-link" href="https://github.com/l2mcgrat">GitHub ↗</a></div></div></section>
    <section class="about-section"><p class="eyebrow">Learning, with a paper trail</p><h2>Licenses &amp; certifications</h2><p class="lede">A foundation in neural networks and process improvement.</p><div class="credential-grid">{items}</div><p class="method-note">Education and credentials transcribed from the supplied LinkedIn screenshot. Credential links use the displayed IDs; availability has not been independently verified.</p></section>
    <section class="about-section"><p class="eyebrow">A growing archive</p><h2>Work &amp; documents</h2><div class="card-grid"><article class="pending-card"><span class="badge">Coming next</span><h3>Engineering &amp; business intelligence</h3><p>Process Engineering and Business Intelligence Lead work at Honda of Canada Manufacturing will be added here after the professional details are supplied.</p></article><article class="pending-card"><span class="badge">Awaiting documents</span><h3>Résumé &amp; work-term report</h3><p>Space reserved for the résumé and third–fourth year work-term report. No downloads have been published yet.</p></article></div></section></main>''', 1)


def document_html(result: dict, title: str, depth: int, topic_links: str, download: str) -> str:
    root = '../' * depth
    body = result['body']
    # Add visibly separate editorial links, never change the authored prose.
    if title == 'Mental Map':
        for heading in result['headings']:
            if heading['title'] == 'Quantum Mechanics':
                pattern = f'(id="{re.escape(heading["id"])}"[^>]*>.*?</h[1-6]>)'
                body = re.sub(pattern, lambda m: m[1] + '<aside class="topic-callout"><span>Go deeper ↗</span><a href="../Physics/Quantum-Mechanics/index.html">Open the dedicated quantum-mechanics notebook</a><small>The original headings below are still an outline.</small></aside>', body, count=1, flags=re.S)
    return shell(title, f'''<main id="main-content" class="document-page"><div class="reader-top"><div><p class="eyebrow">The connected notebook / LaTeX edition</p><h1>{title}</h1><p>By Liam McGrath · A living document, not a finished textbook.</p></div><div class="toolbar"><a class="button ghost" href="{download}" download>Source + images · ZIP ↓</a><button class="button ghost print-reader" type="button">Print / Save PDF</button></div></div>
    <div class="reader-layout"><aside class="reader-sidebar"><details class="contents-panel" open><summary>Contents <span>{len(result['headings'])} headings</span></summary><label class="toc-search-label" for="toc-search">Find a section<input id="toc-search" type="search" placeholder="Search the contents…"></label><div id="reader-toc">{result['toc']}</div><p id="toc-empty" hidden>No matching sections.</p></details></aside>
    <div class="reader-column"><nav class="topic-links" aria-label="Deeper topic pages"><strong>Follow a thread ↗</strong>{topic_links}</nav><p class="reader-note">Section links stay in this document. Blue topic links above open separate pages. Original outline-only sections are retained; these are historical notes, not reviewed reference material.</p><p class="math-status" role="status">Typesetting equations locally…</p><article class="tex-paper">{body}</article><noscript><p>JavaScript is required for equation typesetting. The contents, text and images remain available; download the LaTeX source for the original formulas.</p></noscript><a class="back-top" href="#main-content">Back to the top ↑</a></div></div></main>''', depth, math=True)


def quantum_html(root: Path, site: Path) -> str:
    source = root / 'quantum_mechanics.tex'
    if source.exists():
        assets = site / 'assets' / 'documents' / 'quantum-mechanics'
        images = root / 'tex_images' / 'quantum_mechanics'
        result = convert_document(source, images if images.exists() else source.parent, assets, '../../assets/documents/quantum-mechanics')
        source_zip(source, assets)
        return document_html(result, 'Quantum mechanics', 2, '<a href="../../Mental-Map/index.html#quantum-mechanics">Mental Map ↗</a><a href="../index.html">Physics collection ↗</a>', '../../assets/documents/quantum-mechanics/source-bundle.zip')
    return shell('Quantum mechanics', f'''<main id="main-content" class="collection-page"><section class="quantum-intro"><div><p class="eyebrow">Featured notebook / Physics</p><h1>A world written<br>in wavefunctions.</h1><p class="lede">A dedicated home for analytical solutions of the Schrödinger equation—and the mathematics that makes them possible.</p><span class="badge">Full LaTeX manuscript coming next</span><div class="toolbar"><a class="button primary" href="../../Mental-Map/index.html#quantum-mechanics">Read the Mental Map outline ↗</a><a class="button ghost" href="../index.html">More physics →</a></div></div><div class="quantum-art" aria-hidden="true">{icon('Physics')}<span>ψ</span><small>THE QUANTUM NOTEBOOK</small></div></section>
    <section class="panel"><h2>From an outline to a deeper study</h2><p>The Mental Map currently provides headings for position, mass, momentum and energy. This dedicated page is ready for the separate quantum-mechanics manuscript, with a linked contents list and LaTeX equation numbering.</p><p class="method-note">No solutions have been added or claimed on your behalf. The exact scope of analytically solvable models will follow the manuscript, rather than claiming an exhaustive list.</p></section></main>''', 2)


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
        main = re.search(r'<main\b[^>]*>', content)
        main_id = re.search(r'\bid=[\'"]([^\'"]+)[\'"]', main[0]) if main else None
        target = main_id[1] if main_id else 'main-content'
        if main and not main_id:
            content = content[:main.start()] + main[0].replace('<main', '<main id="main-content"', 1) + content[main.end():]
        if 'class="skip-link"' not in content:
            content = re.sub(r'<body\b[^>]*>', lambda m: m[0] + f'<a class="skip-link" href="#{escape(target)}">Skip to content</a>', content, count=1)
        if content != page.read_text(encoding='utf-8'):
            write(page, content)


def publish_portfolio(root: Path, site: Path, music: dict | None = None, code: dict | None = None) -> dict:
    root, site = root.resolve(), site.resolve()
    assets = site / 'assets'
    vendor = HERE / 'node_modules' / 'mathjax' / 'es5'
    if not vendor.exists():
        raise FileNotFoundError('Local MathJax is missing. Install the dependencies in site_content with npm ci before building.')
    if music is None:
        music = load_analysis(root, 'music-analysis', analyze_music, root.parent / 'music_work')
    if code is None:
        code = load_analysis(root, 'code-analysis', analyze_code, root.parent / 'leetcode_problems')
    for asset in (HERE / 'web').iterdir():
        if asset.is_file():
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, assets / asset.name)
    shutil.copytree(vendor, assets / 'vendor' / 'mathjax', dirs_exist_ok=True)
    shutil.copy2(HERE / 'node_modules' / 'mathjax' / 'LICENSE', assets / 'vendor' / 'mathjax' / 'LICENSE')
    write(assets / 'data' / 'music-analysis.json', safe_json(music))
    write(assets / 'data' / 'music-analysis.js', 'window.MUSIC_ANALYSIS=' + safe_json(music) + ';')
    write(assets / 'data' / 'code-analysis.json', safe_json(code))
    for name, rows in music_rows(music).items():
        write(assets / 'data' / f'music-{name}.csv', csv_text(rows))
    result = convert_document(root / 'mental_map.tex', root / 'tex_images' / 'mental_map', assets / 'documents' / 'mental-map', '../assets/documents/mental-map')
    source_zip(root / 'mental_map.tex', assets / 'documents' / 'mental-map')
    links = ''.join(f'<a href="../{url}">{label} ↗</a>' for label, url in [('Quantum mechanics', 'Physics/Quantum-Mechanics/index.html'), ('Vocabulary', 'Language/Vocabulary/index.html'), ('Feelings explorer', 'Language/Feelings/index.html'), ('Algorithms', 'Miscellaneous/LeetCode/index.html')])
    pages = {
        'index.html': home_html(), 'About/index.html': about_html(),
        'Mental-Map/index.html': document_html(result, 'Mental Map', 1, links, '../assets/documents/mental-map/source-bundle.zip'),
        'Physics/Quantum-Mechanics/index.html': quantum_html(root, site),
        'Language/Vocabulary/index.html': shell('Vocabulary explorer', vocabulary_body(music), 2, music=True, analysis=True),
        'Language/Feelings/index.html': shell('Feelings explorer', feelings_body(music), 2, music=True, analysis=True),
        'Miscellaneous/LeetCode/index.html': shell('LeetCode & algorithms', leetcode_body(code), 2, analysis=True),
    }
    pages.update({f'{name}/index.html': collection_html(name, site) for name in CATEGORIES})
    for path, content in pages.items():
        write(site / path, content)
    upgrade_existing_pages(site)
    manifest = {'pages': list(pages), 'document': {key: result[key] for key in ('equation_count', 'image_count', 'warnings')}, 'music': music['summary'], 'codeModules': code['moduleCount']}
    write(assets / 'data' / 'portfolio-build.json', safe_json(manifest))
    print(f'Portfolio generated: {site} · {len(pages)} pages · {len(result["headings"])} document headings')
    return manifest