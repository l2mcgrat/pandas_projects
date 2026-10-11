"""Curated public career copy, deliberately not a raw LaTeX-to-HTML export.

Facts were read directly from LiamMcGrath_Resume/resume/{experience,education,
projects,honors,technical_skills}.tex. The undated Manufacturing Division / Pillar
Leads scope correction comes from the owner, not a newly inferred appointment.
Only explicitly selected public fields live here; private contact information,
source/template downloads, and certificates belong to neither renderer.

Integration: insert career_body() inside the About page's existing main element;
wrap resume_body() with the publisher shell at depth=2 for About/Resume/index.html.
Load assets/career.css AFTER portfolio.css, using the shell's relative prefix.
The existing portfolio.js handles the single .print-reader button. No filesystem
access, LaTeX compiler, generated PDF, or publishing side effects are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from urllib.parse import urlsplit, urlunsplit

__all__ = ["resume_body", "career_body"]


@dataclass(frozen=True)
class _Entry:
    title: str
    organization: str
    context: str
    dates: str
    highlights: tuple[str, ...] = ()


_NAME = "Liam McGrath"
_TAGLINE = "Manufacturing data systems · ETL & Power BI · Simulation & controls"
_BRIEF = (
    "Builds data-collection systems, ETL pipelines and Power BI reporting for "
    "manufacturing, with experience in process simulation and industrial controls."
)
_CURRENT_SCOPE = (
    "Business intelligence work now supports the Manufacturing Division at Honda, "
    "having previously focused on the Weld Department. Works with the company’s "
    "Pillar Leads, who oversee department-level matters."
)
_SCOPE_NOTE = (
    "The role dates describe the BI Lead position; the division-scope update is undated."
)
_DOCUMENT_NOTE = (
    "This is a curated public HTML résumé. Print / Save PDF creates a browser-formatted "
    "copy, not the original awesome-cv PDF. The original template is preserved privately; "
    "no compiled original PDF is available yet. Private contact details and original "
    "source/template downloads are omitted."
)
_WORK_TERM_NOTE = (
    "Waters in a 1D Carbon Nanotube is available as a privacy-safe public article, "
    "with its scientific content, figures, source bundle and compiled PDF. "
    "This historical report has no verified completion date; administrative and "
    "contact details are excluded."
)
# Public profile URLs already used by the portfolio; no contact-source import.
_PUBLIC_LINKS = (
    ("LinkedIn", "https://www.linkedin.com/in/liam-mcgrath-54a917111/"),
    ("GitHub", "https://github.com/l2mcgrat"),
)

# experience.tex, reordered reverse-chronologically. No numerical savings claims.
_EXPERIENCE = (
    _Entry(
        "Business Intelligence Lead", "Honda of Canada Mfg.", "", "Jan 2023 – Present",
        (
            "Designed data-collection scripts and validated-entry Python/Tkinter interfaces "
            "for quality and safety documentation.",
            "Built ETL workflows that combine and transform data for Power BI reporting; "
            "standardized reporting using solutions developed in Weld and mentored leads "
            "from other departments.",
            "Developed SQL and Excel production-whiteboard reporting for downtime, "
            "throughput and asset state.",
            "Automated file migration to Microsoft SharePoint and routine API-based "
            "data transfers.",
            "Used process simulation to identify efficiency opportunities and estimate "
            "output changes from engineering projects.",
        ),
    ),
    _Entry(
        "Process Engineer", "Honda of Canada Mfg.", "Engineering Group", "Jan 2020 – Jan 2023",
        (
            "Built critical-control-point reporting pipelines and automated A-rank quality "
            "check sheets; collaborated with Production Unit Leaders on scrap and "
            "throughput reports.",
            "Modified tooling, PLC logic and WINCAPS III robot programs to improve processes.",
            "Analyzed scrap and process-point data to assess efficiency changes; "
            "collaborated with an international New Model Group on development cycles.",
        ),
    ),
    _Entry(
        "Simulation Software Developer", "University of Waterloo", "Roy Research Group",
        "Jan 2018 – Sept 2018",
        (
            "Developed Python/MMTK simulations using path-integral Monte Carlo (PIMC) "
            "and path-integral molecular dynamics (PIMD).",
            "Developed C++ potential-energy and gradient calculations and implemented "
            "the MB-pol many-body water potential.",
            "Automated shell-based simulation submission and trajectory analysis; "
            "used parallel processing and Compute Canada research computing.",
        ),
    ),
    _Entry(
        "Research Assistant", "The Woodbridge Group", "Corporate R&D", "Sept 2016 – May 2017",
        (
            "Formulated polyurethane foams and measured physical and chemical properties "
            "for automotive seating, thermal insulation and acoustic insulation.",
            "Studied resin and solid-polyol dispersions using FTIR and viscosity measurements; "
            "presented research results and product-development updates.",
        ),
    ),
)

_EDUCATION = _Entry(
    "Honours Bachelor of Applied Science in Nanotechnology Engineering (Co-op)",
    "University of Waterloo", "", "2014 – 2019",
)
_PROJECT = _Entry(
    "Room-temperature NO2 sensor", "University of Waterloo", "Fourth-year design capstone",
    "Sept 2018 – Apr 2019",
    (
        "Designed and fabricated a portable nitrogen dioxide sensor with professors and "
        "engineering classmates as an educational capstone.",
        "Deposited carbon nanotubes between interdigitated electrodes and electroplated "
        "tellurium to improve sensitivity.",
        "Evaluated dose-response under controlled NO2 concentrations and built "
        "Arduino-interfaced readout circuitry to display concentrations.",
    ),
)
_HONORS = (
    _Entry("NSERC / USRA research grant", "University of Waterloo", "Research under P. N. Roy", "2018"),
    _Entry("President’s Scholarship", "University of Waterloo", "Academic achievement", "2014"),
)

# technical_skills.tex, with application-specific tools evidenced in the entries.
# Linux is an operating system, AWS a cloud platform, Tableau a BI tool, and TeX
# an authoring tool. Listed tools are experience, not proficiency/certification claims.
_SKILLS = (
    ("Programming & query languages", ("Python", "SQL", "VBA", "C++", "Java", "PowerShell")),
    ("Data & business intelligence", ("Power BI", "Tableau", "Excel", "pandas", "NumPy", "pyodbc", "xlwings")),
    ("Operating systems", ("Linux",)),
    ("Cloud & collaboration", ("AWS", "Microsoft SharePoint")),
    ("Simulation & scientific computing", ("PIMC / PIMD", "MMTK", "Molecular dynamics", "Monte Carlo", "COMSOL", "SIMUL8")),
    ("Interfaces & controls", ("Tkinter", "PLC logic", "WINCAPS III", "Arduino")),
    ("Machine learning tools", ("scikit-learn", "TensorFlow", "Keras")),
    ("Scientific authoring & visualization", ("TeX", "Matplotlib", "VMD")),
)


def _profile_links() -> str:
    """Escape public labels/URLs; never print tracking strings or unsafe schemes."""
    links = []
    for label, url in _PUBLIC_LINKS:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.netloc not in {"www.linkedin.com", "github.com"}:
            raise ValueError("Public profiles require an approved HTTPS host.")
        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        print_url = (parts.netloc.removeprefix("www.") + parts.path).rstrip("/")
        links.append(
            f'<li><a href="{escape(clean_url, quote=True)}" rel="noopener noreferrer">'
            f'{escape(label)}<span class="career-print-url" aria-hidden="true">'
            f' · {escape(print_url)}</span></a></li>'
        )
    return '<ul class="career-profile-links" aria-label="Public profiles">' + "".join(links) + '</ul>'


def _entry_header(entry: _Entry) -> str:
    context = f' · {escape(entry.context)}' if entry.context else ""
    return (
        '<div class="career-entry-heading"><div>'
        f'<h3>{escape(entry.title)}</h3>'
        f'<p class="career-organization">{escape(entry.organization)}{context}</p>'
        f'</div><p class="career-dates">{escape(entry.dates)}</p></div>'
    )


def _entry(entry: _Entry, *, current: bool = False, compact: bool = False) -> str:
    scope = (
        f'<div class="career-scope"><p><strong>Current scope</strong> {escape(_CURRENT_SCOPE)}</p>'
        f'<p class="career-scope-note">{escape(_SCOPE_NOTE)}</p></div>'
    ) if current else ""
    highlights = entry.highlights[:2] if compact else entry.highlights
    bullets = (
        '<ul class="career-highlights">' + ''.join(f'<li>{escape(item)}</li>' for item in highlights) + '</ul>'
    ) if highlights else ""
    return '<article class="career-entry">' + _entry_header(entry) + scope + bullets + '</article>'


def _skills() -> str:
    groups = ''.join(
        f'<div class="career-skill-group"><dt>{escape(label)}</dt>'
        '<dd><ul class="career-skill-list">'
        + ''.join(f'<li>{escape(skill)}</li>' for skill in skills)
        + '</ul></dd></div>'
        for label, skills in _SKILLS
    )
    return f'<dl class="career-skills">{groups}</dl>'


def resume_body() -> str:
    """Public HTML résumé body for About/Resume/index.html (publisher depth 2)."""
    experience = ''.join(
        f'<li>{_entry(entry, current=index == 0)}</li>'
        for index, entry in enumerate(_EXPERIENCE)
    )
    honors = ''.join(_entry(entry) for entry in _HONORS)
    return f'''<main id="main-content" class="collection-page resume-page">
    <nav class="career-navigation" aria-label="Résumé navigation"><a href="../index.html">← About Liam</a><a href="../../index.html">The notebook ↗</a></nav>
    <header class="career-masthead"><p class="eyebrow">Public résumé / Engineering &amp; business intelligence</p>
    <h1>{escape(_NAME)}</h1><p class="career-tagline">{escape(_TAGLINE)}</p><p class="lede career-brief">{escape(_BRIEF)}</p>
    {_profile_links()}
    <div class="toolbar career-actions"><button class="button primary print-reader" type="button" aria-describedby="resume-format-note">Print / Save PDF</button><a class="text-link" href="#resume-experience">Explore experience ↓</a></div>
    <p class="career-format-note" id="resume-format-note">{escape(_DOCUMENT_NOTE)}</p></header>
    <section class="career-section" id="resume-experience" aria-labelledby="resume-experience-title"><p class="eyebrow">01 / Professional practice</p><h2 id="resume-experience-title">Experience</h2><ol class="career-timeline">{experience}</ol></section>
    <section class="career-section" id="resume-education" aria-labelledby="resume-education-title"><p class="eyebrow">02 / Foundations</p><h2 id="resume-education-title">Education</h2>{_entry(_EDUCATION)}</section>
    <section class="career-section" id="resume-projects" aria-labelledby="resume-projects-title"><p class="eyebrow">03 / Educational design</p><h2 id="resume-projects-title">Selected project</h2>{_entry(_PROJECT)}</section>
    <section class="career-section" id="resume-skills" aria-labelledby="resume-skills-title"><p class="eyebrow">04 / Working toolkit</p><h2 id="resume-skills-title">Technical skills</h2>{_skills()}</section>
    <section class="career-section" id="resume-honors" aria-labelledby="resume-honors-title"><p class="eyebrow">05 / Academic recognition</p><h2 id="resume-honors-title">Awards</h2><div class="career-awards">{honors}</div></section>
    <aside class="career-publication-note" aria-label="Work-term report"><strong>Work-term report</strong><p>{escape(_WORK_TERM_NOTE)}</p><a class="text-link" href="../../Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations/index.html">Read the work-term report ↗</a></aside>
    </main>'''


def career_body() -> str:
    """Reusable About/index.html fragment; no main, shell, or certificates."""
    earlier = ''.join(
        f'<li><strong>{escape(entry.title)}</strong><span>{escape(entry.organization)}'
        + (f' · {escape(entry.context)}' if entry.context else '')
        + f'</span><span class="career-dates">{escape(entry.dates)}</span></li>'
        for entry in _EXPERIENCE[1:]
    )
    return f'''<section class="about-section career-block" id="career" aria-labelledby="career-title">
    <p class="eyebrow">From the production floor to the model</p><h2 id="career-title">Engineering &amp; business intelligence</h2><p class="lede career-brief">{escape(_BRIEF)}</p>
    <div class="career-current">{_entry(_EXPERIENCE[0], current=True, compact=True)}</div>
    <div class="career-summary-grid"><article class="career-card"><h3>Earlier experience</h3><ul class="career-earlier">{earlier}</ul></article>
    <article class="career-card"><h3>Engineering foundation</h3><p><strong>{escape(_EDUCATION.organization)}</strong></p><p>{escape(_EDUCATION.title)}</p><p class="career-dates">{escape(_EDUCATION.dates)}</p><p>Educational capstone: {escape(_PROJECT.title)} with carbon nanotubes, tellurium and Arduino readout circuitry.</p></article></div>
    <div class="career-documents"><h3>Public résumé &amp; documents</h3><a class="button primary" href="Resume/index.html">Read the public HTML résumé ↗</a><p class="career-format-note">{escape(_DOCUMENT_NOTE)}</p><p class="career-publication-note"><strong>Work-term report</strong> {escape(_WORK_TERM_NOTE)}</p><a class="button ghost" href="../Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations/index.html">Read the work-term report ↗</a></div>
    </section>'''