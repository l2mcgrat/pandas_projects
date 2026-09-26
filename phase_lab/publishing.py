"""Local static-site publishing only; no Git operations or network access."""

import html
import json
from pathlib import Path
import re
import shutil


def viewer_html(run_id, notice, figures, reports_prefix):
    template = (Path(__file__).parent / "web" / "viewer.html").read_text(encoding="utf-8")
    figures = sorted(figures, key=lambda name: (name != "order_fingerprint.png", name))
    images = "\n".join(
        f'<a data-potential="{html.escape(name.split("/")[0] if "/" in name else "all")}" href="{html.escape(reports_prefix + name)}" target="_blank" rel="noopener"><img loading="lazy" '
        f'src="{html.escape(reports_prefix + name)}" alt="{html.escape(name.removesuffix(".png").replace("_", " "))}"></a>'
        for name in figures)
    for key, value in {"RUN_ID": html.escape(run_id), "NOTICE": html.escape(notice), "FIGURES": images,
                       "PDF": html.escape(reports_prefix + "dipole_atlas.pdf")}.items():
        template = template.replace("@@" + key + "@@", value)
    return template


def link_experiments(atlas):
    """Refresh cross-run boundary links without modifying any recorded data."""
    pages = sorted(Path(atlas).glob("*/index.html"))
    entries = []
    for page in pages:
        manifest = page.parent / "metadata.json"
        if manifest.exists():
            metadata = json.loads(manifest.read_text(encoding="utf-8"))
            config = metadata.get("config", {})
            label = f"{config.get('boundary', 'periodic')} / {config.get('ensemble', 'npt').upper()} · {page.parent.name}"
            entries.append((page, label))
    for page in pages:
        links = ' · '.join(f'<a href="../{html.escape(other.parent.name)}/index.html">{html.escape(label)}</a>'
                           for other, label in entries if other != page)
        markup = f'<nav id="experiments" aria-label="Other boundary experiments">Other experiments: {links}</nav>' if links else '<nav id="experiments" aria-label="Other boundary experiments"></nav>'
        content = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r'<nav id="experiments"[^>]*>.*?</nav>', lambda _: markup, content), encoding="utf-8")


def publish_available_runs(root, site_dir):
    """Copy already-rendered runs during a website build; never start MD here."""
    for page in sorted((Path(root) / "media" / "phase_simulations").glob("*/index.html")):
        metadata_path = Path(root) / "records" / "phase_simulations" / page.parent.name / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("status") == "complete":
                publish_run(Path(root), page.parent.name, site_dir)


def physics_landing_page(site_dir):
    """Used by both this publisher and the existing general website builder."""
    atlas = Path(site_dir) / "Physics" / "Dipole-Atlas"
    runs = sorted((p.parent.name for p in atlas.glob("*/index.html")), reverse=True)
    cards = "\n".join(
        f'<a class="run" href="Dipole-Atlas/{html.escape(run)}/index.html"><span>MOLECULAR DYNAMICS / OPENMM</span>'
        f'<h2>Dipole Atlas</h2><p>{html.escape(run)}</p><strong>Explore trajectories & reports ↗</strong></a>' for run in runs)
    if not cards:
        cards = '<p>Simulation runs will appear here after local publication.</p>'
    elif (atlas / "index.html").exists():
        cards = '<a class="run" href="Dipole-Atlas/index.html"><span>START HERE / STABLE LINK</span><h2>Interaction explorer</h2><p>Choose molecule, potential, metric, temperature and pressure.</p><strong>Open the atlas ↗</strong></a>' + cards
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Physics | LiamMs_PandasProjects</title>
<style>body{{margin:0;background:#080f1e;color:#e6edf7;font:17px/1.65 system-ui,sans-serif}}main,header{{max-width:1100px;margin:auto;padding:32px 24px}}a{{color:#65e4d5}}h1{{font-size:clamp(3rem,8vw,6rem);line-height:1.05;letter-spacing:-.06em}}.eyebrow,.run span{{color:#65e4d5;font-size:12px;letter-spacing:.18em}}.intro{{max-width:700px;color:#adbed6}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:22px;margin-top:48px}}.run{{display:block;color:inherit;text-decoration:none;padding:32px;border:1px solid #29405c;border-radius:20px;background:radial-gradient(ellipse at top right,#173f48,transparent 75%),#101d30;transition:transform .2s}}.run:hover{{transform:translateY(-4px)}}.run h2{{font-size:36px;letter-spacing:-.04em}}.run p{{overflow-wrap:anywhere;color:#adbed6}}.run strong{{color:#fbbf24}}footer{{color:#91a5c2;font-size:13px;margin-top:48px}}</style></head>
<body><!-- dipole-atlas-physics-index --><header><a href="../index.html">← LiamMs_PandasProjects</a></header><main>
<p class="eyebrow">THE PHYSICS COLLECTION</p><h1>Small worlds.<br>Emergent patterns.</h1>
<p class="intro">Follow molecular motion, map dipole orientations, and explore how order responds to temperature and pressure. Interactive experiments with downloadable data—not just pictures.</p>
<section class="grid">{cards}</section><footer>These illustrative polar-fluid models are not calibrated material-property predictions. Read each run's methodology and limitations before interpreting its patterns.</footer>
</main></body></html>'''


def publish_run(root, run_id, site_dir):
    records = root / "records" / "phase_simulations" / run_id
    metadata = json.loads((records / "metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "complete":
        raise ValueError("Cannot publish an incomplete run.")
    media = root / "media" / "phase_simulations" / run_id
    reports = root / "reports" / "phase_simulations" / run_id
    target = Path(site_dir) / "Physics" / "Dipole-Atlas" / run_id
    if target.resolve() == media.resolve():
        raise ValueError("Website destination must differ from source media.")
    shutil.copytree(media, target, dirs_exist_ok=True)
    theory_names = ("theory.html", "theory.pdf", "theory.tex", "theory-source.json")
    shutil.copytree(reports, target / "figures", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*theory_names))
    # Theory assets are already copied from media at the viewer root. Avoid a
    # redundant HTML copy whose "back to explorer" link would target figures/.
    for name in theory_names:
        (target / "figures" / name).unlink(missing_ok=True)
    figures = [p.relative_to(reports).as_posix() for p in sorted(reports.rglob("*.png"))]
    (target / "index.html").write_text(viewer_html(run_id, metadata["notice"], figures, "figures/"), encoding="utf-8")
    link_experiments(target.parent)
    # Stable, nondated public URL. One asset copy per immutable run; <base> resolves
    # downloads/scripts into that run without redirecting the browser's address.
    candidates = []
    for manifest in target.parent.glob("*/metadata.json"):
        item = json.loads(manifest.read_text(encoding="utf-8"))
        if item.get("status") == "complete" and (manifest.parent / "index.html").exists():
            cfg = item.get("config", {})
            rank = (cfg.get("ensemble") == "npt", item.get("schema_version", 1), item.get("created_utc", ""))
            candidates.append((rank, manifest.parent))
    if candidates:
        featured = max(candidates, key=lambda item: item[0])[1]
        page = (featured / "index.html").read_text(encoding="utf-8")
        page = page.replace("<head>", f'<head>\n<base href="{html.escape(featured.name)}/">', 1)
        (target.parent / "index.html").write_text(page, encoding="utf-8")
    landing = Path(site_dir) / "Physics" / "index.html"
    existing = landing.read_text(encoding="utf-8") if landing.exists() else ""
    if not existing or "To be Filled with Analysis" in existing or "dipole-atlas-physics-index" in existing:
        landing.write_text(physics_landing_page(site_dir), encoding="utf-8")
    elif f'Dipole-Atlas/{run_id}/index.html' not in existing:
        # Preserve hand-written Physics content; append one link rather than replacing it.
        card = f'<p><a href="Dipole-Atlas/{html.escape(run_id)}/index.html">Dipole Atlas: {html.escape(run_id)}</a></p>'
        landing.write_text(existing.replace("</body>", card + "\n</body>") if "</body>" in existing else existing + card,
                           encoding="utf-8")