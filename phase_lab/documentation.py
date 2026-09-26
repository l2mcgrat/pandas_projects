"""Build offline mathematical HTML, PDF and LaTeX from one versioned source."""

import hashlib
import html
import io
import json
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.mathtext import math_to_image

from .model import MOLECULES, POTENTIALS
from .references import DENSITIES, VAPORIZATION, density_reference


def build_theory(destination):
    source = Path(__file__).parent / "docs" / "theory.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    # Generated registry appendix keeps the explanatory manuscript and tables in sync.
    appendix = {"id": "registry", "title": "15. Parameter and reference registry", "paragraphs": []}
    for name, molecule in MOLECULES.items():
        rho = density_reference(name)
        appendix["paragraphs"].append(
            f"{molecule.label}: mass {molecule.mass_da} Da; illustrative dipole {molecule.dipole_debye} D; "
            f"sigma {molecule.sigma_nm} nm; molecular epsilon {molecule.epsilon_kj_mol} kJ/mol. "
            f"Density anchor {rho['value_g_cm3']} g/cm^3 at {rho['temperature_K']} K; pressure unspecified. "
            f"Source: {rho['citation']}.")
        doc["sources"].append([f"{name}: density ({DENSITIES[name][1]} K)", rho["source"]])
        ref = VAPORIZATION.get(name)
        appendix["paragraphs"].append(
            f"{name}: vaporization enthalpy {ref['value']:.4g} kJ/mol at {ref['temperature_K']} K; "
            f"pressure {ref['pressure_kPa'] if ref['pressure_kPa'] is not None else 'unspecified'} kPa. {ref['citation']}."
            if ref else f"{name}: no vaporization enthalpy value in the curated registry.")
        if ref:
            doc["sources"].append([f"{name}: vaporization enthalpy", ref["source"]])
    appendix["paragraphs"].append("Available Hamiltonians: " + "; ".join(f"{key}: {value}" for key, value in POTENTIALS.items()) + ".")
    doc["sections"].append(appendix)
    destination.mkdir(parents=True, exist_ok=True)
    parts, tex = [], [r"\documentclass[11pt]{article}", r"\usepackage[margin=1in]{geometry}",
                      r"\usepackage{amsmath,amssymb,hyperref}", r"\begin{document}",
                      r"\title{Dipole Atlas: theory and design}\maketitle\tableofcontents"]

    def latex_text(text):
        replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "_": r"\_",
                        "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}", "^": r"\textasciicircum{}"}
        return "".join(replacements.get(char, char) for char in text)

    with plt.rc_context({"font.family": "DejaVu Serif", "mathtext.fontset": "dejavuserif"}), PdfPages(destination / "theory.pdf") as pdf:
        fig, y, page = None, 0., 0

        def new_page():
            nonlocal fig, y, page
            if fig is not None:
                pdf.savefig(fig)
                plt.close(fig)
            page += 1
            fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
            fig.text(.10, .96, f"DIPOLE ATLAS / THEORY & DESIGN / v{doc['version']}", fontsize=8, color="#49707b")
            fig.text(.10, .04, f"Qualitative surrogates · not measured phase boundaries                                      {page}", fontsize=8)
            y = .915

        def paragraph(text, size=10, heading=False):
            nonlocal y
            lines = textwrap.wrap(text, width=72 if heading else 94, break_long_words=True)
            if y - len(lines)*.017 < .09:
                new_page()
            fig.text(.1, y, "\n".join(lines), va="top", fontsize=size, linespacing=1.45,
                     fontweight="bold" if heading else "normal", color="#12313d" if heading else "#17212b")
            y -= len(lines)*.017 + .024

        new_page()
        paragraph(doc["title"], 16, True)
        paragraph(doc["abstract"])
        parts.append(f'<p class="abstract">{html.escape(doc["abstract"])}</p>')
        tex.extend([r"\begin{abstract}", latex_text(doc["abstract"]), r"\end{abstract}"])
        for section in doc["sections"]:
            paragraph(section["title"], 13, True)
            parts.append(f'<section id="{section["id"]}"><h2>{html.escape(section["title"])}</h2>')
            tex.append(r"\section*{" + latex_text(section["title"]) + "}")
            tex.append(r"\addcontentsline{toc}{section}{" + latex_text(section["title"]) + "}")
            for text in section["paragraphs"]:
                paragraph(text)
                parts.append(f"<p>{html.escape(text)}</p>")
                tex.append(latex_text(text) + "\n\n")
            for equation in section.get("equations", []):
                image = io.BytesIO()
                math_to_image("$" + equation + "$", image, format="svg", dpi=150)
                svg = image.getvalue().decode("utf-8")
                svg = svg[svg.index("<svg"):]
                parts.append(f'<div class="equation" role="img" aria-label="{html.escape(equation)}">{svg}</div>')
                if y < .16:
                    new_page()
                fig.text(.12, y, "$" + equation + "$", fontsize=11, va="top")
                y -= .065
                tex.append(r"\[" + equation + r"\]")
            parts.append("</section>")
        parts.append('<section id="sources"><h2>16. Sources and further reading</h2><ol>')
        paragraph("16. Sources and further reading", 13, True)
        tex.append(r"\section*{Sources and further reading}\begin{enumerate}")
        for label, url in doc["sources"]:
            parts.append(f'<li><a href="{html.escape(url)}">{html.escape(label)}</a></li>')
            paragraph(label + "\n" + url, 9)
            tex.append(r"\item " + latex_text(label) + r" \url{" + url + "}")
        parts.append("</ol></section>")
        tex.append(r"\end{enumerate}\end{document}")
        pdf.savefig(fig)
        plt.close(fig)
    toc = "".join(f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for s in doc["sections"])
    page_html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dipole Atlas — theory and design</title><style>
body{{margin:0;background:#edf0ee;color:#142c36;font:18px/1.8 Georgia,serif}}main{{max-width:850px;margin:40px auto;padding:60px;background:#fff;box-shadow:0 12px 60px #17323e15}}a{{color:#126b79}}h1{{font-size:40px;line-height:1.2}}h2{{line-height:1.4;padding-top:30px;border-top:1px solid #c9d5d8}}nav{{font:14px/1.8 system-ui}}.abstract{{font-style:italic;background:#edf5f4;padding:24px}}.equation{{text-align:center;overflow-x:auto;padding:20px 0}}.equation svg{{max-width:100%;height:auto}}section{{scroll-margin-top:24px}}small{{font-family:system-ui;color:#52707c}}@media(max-width:650px){{main{{margin:0;padding:24px}}h1{{font-size:32px}}}}@media print{{main{{box-shadow:none;margin:0;padding:0}}nav{{display:none}}a{{color:inherit}}}}
</style></head><body><main><nav><a href="index.html">← Molecular explorer</a> · <a href="theory.pdf">PDF</a> · <a href="theory.tex" download>LaTeX source</a> · <a href="theory-source.json" download>Document source</a></nav>
<small>METHODS / VERSION {doc['version']} / CLASSICAL MOLECULAR DYNAMICS</small><h1>{html.escape(doc['title'])}</h1><nav aria-label="Contents"><ol>{toc}<li><a href="#sources">16. Sources</a></li></ol></nav>{''.join(parts)}</main></body></html>'''
    (destination / "theory.html").write_text(page_html, encoding="utf-8")
    (destination / "theory.tex").write_text("\n".join(tex), encoding="utf-8")
    (destination / "theory-source.json").write_bytes(source.read_bytes())
    return {"theory_version": doc["version"], "theory_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}