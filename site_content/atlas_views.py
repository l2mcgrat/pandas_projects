"""Hexagon field/topic pages, destination pages and the home hero, all from atlas.py."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from html import escape

from .atlas import NODES, ROOT, Node, anchor, lineage, parent
from .icons import icon_svg

TONES = ("science", "business", "career", "sports", "gaming", "language")
POINTS = {"top": (300, 78), "upper-left": (108, 189), "upper-right": (492, 189),
          "lower-left": (108, 411), "bottom": (300, 522), "lower-right": (492, 411)}

QUANTUM = "Science-and-Engineering/Physics/Quantum-Mechanics/index.html"
CONTROL = "Science-and-Engineering/Physics/Classical-Mechanics/Control-Systems/index.html"
ALGORITHMS = "Science-and-Engineering/Computer-Science/Data-Structures-and-Algorithms/index.html"
REPORT = "Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations/index.html"
RULES = "Sports-and-Entertainment/Series-Hub/Rules/index.html"
DASHBOARD = "Sports-and-Entertainment/Series-Hub/Analytics/index.html"
PITCH = "Sports-and-Entertainment/Series-Hub/Creator-Petition/index.html"
FEELINGS = "Language-and-Programming/Text-Analysis/Sentiment/index.html"
VOCABULARY = "Language-and-Programming/Text-Analysis/Word-Frequency/index.html"
LEETCODE = "Language-and-Programming/LeetCode/Source-Index/index.html"
ATLAS = "Atlas/index.html"
WORKBENCH = "Workbench/index.html"
UPDATES = "Updates/index.html"
COMPLETION = "Completion/index.html"
TRAFFIC = "Traffic/index.html"
MENTAL_MAP = "Mental-Map/index.html"
GUIDE = "Mental-Map/Guide/index.html"
MACRO_STUDY = "Business-and-Economics/Macroeconomics/Economic-Growth/index.html"
MACRO_PAPER = "Business-and-Economics/Macroeconomics/Economic-Growth/Paper/index.html"
ALBERTA_STUDY = "Business-and-Economics/Law-and-Policy/Public-Policy/index.html"
ALBERTA_PAPER = "Business-and-Economics/Law-and-Policy/Public-Policy/Paper/index.html"
GAS_STUDY = "Business-and-Economics/Microeconomics/Game-Theory/index.html"
GAS_TAB = "Business-and-Economics/Microeconomics/Game-Theory/Gas-Price-Collusion/index.html"
GAS_PAPER = "Business-and-Economics/Microeconomics/Game-Theory/Paper/index.html"
SODIUM_STUDY = "Science-and-Engineering/Chemistry/Electrochemistry/index.html"
SODIUM_TAB = "Science-and-Engineering/Chemistry/Electrochemistry/Sodium-Battery-Technology/index.html"
SODIUM_PAPER = "Science-and-Engineering/Chemistry/Electrochemistry/Paper/index.html"
AI_COST_STUDY = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/index.html"
AI_COST_TAB = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/AI-Cost-Study/index.html"
AI_COST_PAPER = "Business-and-Economics/Emerging-Industries/Artificial-Intelligence/Paper/index.html"
GEN_TAX_STUDY = "Business-and-Economics/Macroeconomics/Fiscal-Policy/index.html"
GEN_TAX_TAB = "Business-and-Economics/Macroeconomics/Fiscal-Policy/Taxes-on-Generations/index.html"
GEN_TAX_PAPER = "Business-and-Economics/Macroeconomics/Fiscal-Policy/Paper/index.html"
_ATHLETICS = "Gaming-and-Performance-Log/Athletics"
RUNNING = f"{_ATHLETICS}/Running/index.html"
SWIMMING = f"{_ATHLETICS}/Swimming/index.html"
WEIGHTLIFTING = f"{_ATHLETICS}/Weightlifting/index.html"
_HEALTH = "Gaming-and-Performance-Log/Health"
SLEEP = f"{_HEALTH}/Sleep/index.html"
DIET = f"{_HEALTH}/Diet/index.html"
_WEBSITE = "Language-and-Programming/Coding-Projects/Website-Changes"
CHANGE_LOG = f"{_WEBSITE}/Change-Log/index.html"
UPCOMING = f"{_WEBSITE}/Upcoming-Changes/index.html"
PREDICTIONS = "Sports-and-Entertainment/Sports-Analytics/Predictions-and-Results"
UFC = f"{PREDICTIONS}/UFC-Predictions-vs-Outcomes/index.html"
NBA = f"{PREDICTIONS}/NBA-Predictions-vs-Outcomes/index.html"
# Destinations whose own page is an existing reader or explorer.
LEETCODE_LEAVES = tuple(f"Language-and-Programming/LeetCode/{leaf}" for leaf in (
    "Lists-and-Arrays", "Trees-and-Tries", "Graphs", "Dynamic-Programming", "Recursion", "Hard-Problems"))
RAP_LEAVES = tuple(f"Language-and-Programming/Rap/{leaf}" for leaf in (
    "Seven-Deadly-Sins", "Homewood-and-Trafalgar", "Made-in-Abyss", "Vagabond", "NanoFtheAbove", "Future-Projects"))
DATABASE_LEAVES = (
    "Language-and-Programming/Coding-Projects/Database-Exploration",
    "Language-and-Programming/Coding-Projects/Relational-Database-Development",
)
# Dynamic Programming renders its selection rule but has no solutions yet, so it is not "Live".
HOSTED = frozenset(route.removesuffix("/index.html") for route in (
    QUANTUM, ALGORITHMS, REPORT, RULES, DASHBOARD, PITCH, FEELINGS, VOCABULARY, RUNNING, SWIMMING, WEIGHTLIFTING,
    SLEEP, DIET, MACRO_STUDY, ALBERTA_STUDY, GAS_STUDY, SODIUM_STUDY, AI_COST_STUDY, GEN_TAX_STUDY)) | frozenset(
    path for path in LEETCODE_LEAVES + RAP_LEAVES + DATABASE_LEAVES if not path.endswith("Dynamic-Programming"))


@dataclass(frozen=True)
class Feature:
    href: str
    eyebrow: str
    title: str
    text: str
    icon: str
    legacy: str = ""
    date: str = ""  # when the item was added or last substantially updated


_QM = Feature(QUANTUM, "Reader · Analytical physics", "The hydrogen manuscript",
              "Quantum mechanics with a corrected derivation and normalized wavefunctions.", "Science-and-Engineering/Physics/Quantum-Mechanics",
              date="2026-09-26")
_CONTROL = Feature(CONTROL, "SYDE 352 · Illustrated review", "Feedback & control systems",
                   "State space, Routh–Hurwitz, root locus, Bode, Nyquist and compensation.", "Science-and-Engineering/Physics/Classical-Mechanics",
                   date="2026-09-27")
_DSA = Feature(ALGORITHMS, "Illustrated study notes", "Data structures & algorithms",
               "Invariants, complexity, graphs and dynamic programming.", "Science-and-Engineering/Computer-Science/Data-Structures-and-Algorithms",
               date="2026-09-27")
_DIPOLE = Feature("Physics/Dipole-Atlas/index.html", "Interactive · Molecular dynamics", "Dipole Atlas",
                  "Qualitative order/disorder simulations, trajectories and downloads.", "Science-and-Engineering/Physics/Thermodynamics",
                  "Physics/Dipole-Atlas/index.html", date="2026-09-25")
_REPORT = Feature(REPORT, "Research · Work-term report", "Waters in a 1D Carbon Nanotube",
                  "Path-integral simulations of water in a nanotube, with PDF and source.", "Career-and-Education/Job-Experiences/Quantum-Molecular-Dynamics-Simulations",
                  date="2026-09-27")
_RESUME = Feature("About/Resume/index.html#resume-experience", "Public résumé · Experience", "Engineering & business intelligence",
                  "Honda process engineering and BI, Roy-group simulation and Woodbridge R&D.", "Career-and-Education/Job-Experiences",
                  date="2026-09-27")
_PROJECTS = Feature("About/Resume/index.html#resume-projects", "Public résumé · Capstone", "Room-temperature NO2 sensor",
                    "Carbon nanotubes, tellurium and Arduino readout in a fourth-year design project.", "Career-and-Education/Projects/KUBO-NO2-Sensor",
                    date="2026-09-27")
_ABOUT = Feature("About/index.html", "About Liam", "Education & credentials", "Nanotechnology Engineering, certifications and career summary.",
                 "Career-and-Education", date="2026-09-26")
_DASH = Feature(DASHBOARD, "First to Four · Analytics", "The basketball series dashboard",
                "Thirteen series, challenge splits, inferred picks and a round-by-round scrubber.", "Sports-and-Entertainment/Series-Hub/Analytics",
                date="2026-09-27")
_RULES = Feature(RULES, "First to Four · House rules", "Illustrated rules", "Seven challenges with three diagrams each, plus PDF and source.",
                 "Sports-and-Entertainment/Series-Hub/Rules", date="2026-10-04")
_PITCH = Feature(PITCH, "First to Four · Proposal", "Creator pitch", "A draft pilot proposal; unaffiliated and not sent.",
                 "Sports-and-Entertainment/Series-Hub/Creator-Petition", date="2026-09-27")
_VOCAB = Feature(VOCABULARY, "Text analysis · Lexical diversity", "Vocabulary explorer",
                 "Word frequencies, song versions and MATTR-50 across the lyric archive.", "Language-and-Programming/Text-Analysis/Word-Frequency",
                 date="2026-09-26")
_FEEL = Feature(FEELINGS, "Text analysis · Cues", "Feelings explorer",
                "An interactive wheel and a line-by-line reader with evidence for every label.", "Language-and-Programming/Text-Analysis/Sentiment",
                date="2026-09-26")
_LEET = Feature(LEETCODE, "Practice · Source index", "LeetCode source index",
                "Modules, topics and definition sites; not a count of problems solved.", "Language-and-Programming/LeetCode", date="2026-09-26")
_SMASH = Feature("Smash/index.html", "Analytics · Smash Bros", "Smash mains discovery",
                 "Fighter profiles, rankings and round histories.", "Gaming-and-Performance-Log/Smash-Bros", "Smash/index.html", date="2026-09-20")
_RANK = Feature("Smash/Rank-Atlas/index.html", "Smash · Rankings", "Rank atlas", "Rank trajectories across rounds.",
                "Gaming-and-Performance-Log/Smash-Bros/Player-Statistics", "Smash/Rank-Atlas/index.html", date="2026-09-20")
_SCORE = Feature("Smash/Score-Atlas/index.html", "Smash · Scores", "Score atlas", "Score movement across every recorded round.",
                 "Gaming-and-Performance-Log/Smash-Bros/Highlights", "Smash/Score-Atlas/index.html", date="2026-09-20")
_OPPONENTS = Feature("Smash/Opponents/index.html", "Smash · Opponents", "Opponent profiles", "How characters fared as opponents.",
                     "Gaming-and-Performance-Log/Smash-Bros/Character-Origins", "Smash/Opponents/index.html", date="2026-09-20")
_MAP = Feature(MENTAL_MAP, "The connecting thread", "Mental Map", "The notebook behind every field, now in the site's 6 × 6 × 6 outline.",
               "root", date="2026-10-04")
_GUIDE = Feature(GUIDE, "Guide · PDF", "Adding notes to the Mental Map", "From a Gemini chat log to the right subsubsection, checked and built.",
                 "Career-and-Education/Projects/Mental-Map", date="2026-10-04")
_ATLAS = Feature(ATLAS, "Site atlas", "Every page at a glance", "The radial tree of all 259 nodes.",
                 "Language-and-Programming/Coding-Projects/Website-Changes", date="2026-10-04")
_WORKBENCH = Feature(WORKBENCH, "Database · 4 tables", "Notebook Workbench",
                     "Study queue, wishlist to-dos, spontaneous rap bars by bucket, and a browser voice-note studio.",
                     "Language-and-Programming/Coding-Projects/Relational-Database-Development", date="2026-10-25")
_ICEBERG = Feature(MACRO_STUDY, "Macroeconomics · Study 01", "The AI Iceberg Index & sector roles",
                   "2.2% visible tech adoption vs. 11.7% submerged skill exposure across 12 NAICS industries and 12 regional economies.",
                   "Business-and-Economics/Macroeconomics/Economic-Growth", date="2026-10-25")
_ICEBERG_PAPER = Feature(MACRO_PAPER, "LaTeX paper · PDF", "Above and Beneath the Surface",
                         "Formal decomposition of the Iceberg Index, sector role matrices, and regional multipliers.",
                         "Business-and-Economics/Macroeconomics", date="2026-10-25")
_ALBERTA = Feature(ALBERTA_STUDY, "Public Policy · Study 02", "2026 Alberta Referendum anatomy",
                   "All 10 October 19 ballot questions and how region, party coalition, age, and identity split the vote.",
                   "Business-and-Economics/Law-and-Policy/Public-Policy", date="2026-10-25")
_ALBERTA_PAPER = Feature(ALBERTA_PAPER, "LaTeX paper · PDF", "Three Ballots in One",
                         "Ballot roll-off, demographic decomposition, and why 25% Option 2 equals ~18% direct separatism.",
                         "Business-and-Economics/Law-and-Policy", date="2026-10-25")
_GAS = Feature(GAS_STUDY, "Game Theory · Study ST-06", "Gas Price Collusion & oligopoly supergames",
               "Cross-country pump price decomposition, Rockets & Feathers ECM, and repeated Bertrand SPNE thresholds.",
               "Business-and-Economics/Microeconomics/Game-Theory", date="2026-10-25")
_GAS_PAPER = Feature(GAS_PAPER, "LaTeX paper · PDF", "Why Gas Prices Feather Down",
                     "Repeated Bertrand supergames, German MTS-K AI pricing, Perth FuelWatch signaling, and Pandas code.",
                     "Business-and-Economics/Microeconomics", date="2026-10-25")
_SODIUM = Feature(SODIUM_STUDY, "Electrochemistry · Study ST-05", "Sodium Battery Technology & grid storage",
                  "Period 2 vs. Period 3 electrochemistry, hard carbon intercalation, dual Al collectors, and −20°C grid retention.",
                  "Science-and-Engineering/Chemistry/Electrochemistry", date="2026-10-25")
_SODIUM_PAPER = Feature(SODIUM_PAPER, "LaTeX paper · PDF", "Period 3 Power: Sodium-Ion Batteries",
                        "Faraday capacity, Shannon radius, Stokes desolvation kinetics, and ANL BatPaC cost floors.",
                        "Science-and-Engineering/Chemistry", date="2026-10-25")
_AI_COST = Feature(AI_COST_STUDY, "Emerging Industries · Study ST-08", "AI Cost & Compute Economics",
                   "200× token inference deflation vs. $130M–$1B+ training clusters, Sparse MoE + MLA KV-cache, and cascade routing.",
                   "Business-and-Economics/Emerging-Industries/Artificial-Intelligence", date="2026-10-26")
_AI_COST_PAPER = Feature(AI_COST_PAPER, "LaTeX paper · PDF", "AI Cost & Compute Economics",
                         "Chinchilla scaling, HBM3e memory-bandwidth roofline, Jevons Paradox in reasoning tokens, and Pandas code.",
                         "Business-and-Economics/Emerging-Industries", date="2026-10-26")
_GEN_TAX = Feature(GEN_TAX_STUDY, "Fiscal Policy · Study ST-09", "Taxes on Generations Over Time Periods",
                   "Real population-normalized tax burden vs. fiscal rewards (1985–2025), 28.4m exurban commute carbon tax, youth vape excise & property tax.",
                   "Business-and-Economics/Macroeconomics/Fiscal-Policy", date="2026-10-27")
_GEN_TAX_PAPER = Feature(GEN_TAX_PAPER, "LaTeX paper · PDF", "Taxes on Generations Over Time Periods",
                         "Auerbach-Kotlikoff generational accounting, commute carbon elasticity, vaping excise concentration, and Pandas code.",
                         "Business-and-Economics/Macroeconomics", date="2026-10-27")
_CHANGES = Feature(CHANGE_LOG, "Reader · Dated", "Change log", "Every request and what was built, newest first.",
                   "Language-and-Programming/Coding-Projects/Website-Changes", date="2026-10-25")
_UPCOMING = Feature(UPCOMING, "Reader · Dated", "Upcoming changes", "Planned work by request date, and the change-request database plan.",
                    "Language-and-Programming/Coding-Projects/Relational-Database-Development", date="2026-10-25")
_DATABASE = Feature(UPCOMING + "#database-plan", "Plan · Nine steps", "Change requests in a database",
                    "From the Mental Map's email form to an insert-only table, with validation and spam checks.",
                    "Language-and-Programming/Coding-Projects/Database-Exploration", date="2026-10-04")
_RUN = Feature(RUNNING, "Athletics · Intervals", "Running dashboard", "Every I1 interval, session averages, and the new tempo runs.",
               f"{_ATHLETICS}/Running", date="2026-10-18")
_SWIM = Feature(SWIMMING, "Athletics · Distance", "Swimming dashboard", "Distance per session in yards and metres, the running total and high-school bests.",
                f"{_ATHLETICS}/Swimming", date="2026-10-18")
_LIFT = Feature(WEIGHTLIFTING, "Athletics · Strength", "Weightlifting dashboard",
                "Volume per session; for every exercise, the top set, the heaviest for 10 and 12 reps, and the reps.",
                f"{_ATHLETICS}/Weightlifting", date="2026-10-18")
_SLEEP = Feature(SLEEP, "Health · Journal", "Sleep & dream log", "Hours per night, every dream as written, and a playful motif reading.",
                 f"{_HEALTH}/Sleep", date="2026-10-18")
_DIET = Feature(DIET, "Health · Ledger", "Diet & calorie tracking", "Energy in and out on one chart, with the daily deficit against its target.",
                f"{_HEALTH}/Diet", date="2026-10-18")
_UFC = Feature(UFC, "Premade tab · UFC", "UFC predictions vs. outcomes", "A place to log fight predictions before the event and results after.",
               f"{PREDICTIONS}", date="2026-10-04")
_NBA = Feature(NBA, "Premade tab · NBA", "NBA predictions vs. outcomes", "A place to log game and season predictions, then score them.",
               f"{PREDICTIONS}", date="2026-10-04")

_LEETCODE_LEAVES = {path: (_LEET,) for path in LEETCODE_LEAVES}
_RAP_LEAVES = {path: (_VOCAB, _FEEL) for path in RAP_LEAVES}
FEATURES: dict[str, tuple[Feature, ...]] = {
    "Science-and-Engineering": (_SODIUM, _QM, _CONTROL, _DSA, _DIPOLE),
    "Science-and-Engineering/Chemistry": (_SODIUM, _SODIUM_PAPER),
    "Science-and-Engineering/Physics": (_QM, _CONTROL, _DIPOLE, _REPORT),
    "Science-and-Engineering/Physics/Classical-Mechanics": (_CONTROL,),
    "Science-and-Engineering/Physics/Thermodynamics": (_DIPOLE,),
    "Science-and-Engineering/Computer-Science": (_DSA, _LEET, _REPORT),
    "Science-and-Engineering/Computer-Science/Simulations": (_DIPOLE, _REPORT),
    "Business-and-Economics": (_GEN_TAX, _AI_COST, _GAS, _ICEBERG, _ALBERTA, _GEN_TAX_PAPER, _AI_COST_PAPER, _GAS_PAPER, _ICEBERG_PAPER, _ALBERTA_PAPER),
    "Business-and-Economics/Microeconomics": (_GAS, _GAS_PAPER),
    "Business-and-Economics/Microeconomics/Market-Structures": (_GAS, _GAS_PAPER),
    "Business-and-Economics/Macroeconomics": (_GEN_TAX, _GEN_TAX_PAPER, _ICEBERG, _ICEBERG_PAPER, _ALBERTA),
    "Business-and-Economics/Macroeconomics/Fiscal-Policy": (_GEN_TAX, _GEN_TAX_PAPER, _ICEBERG),
    "Business-and-Economics/Law-and-Policy": (_ALBERTA, _ALBERTA_PAPER),
    "Business-and-Economics/Emerging-Industries": (_AI_COST, _AI_COST_PAPER, _ICEBERG, _ICEBERG_PAPER),
    "Business-and-Economics/Emerging-Industries/Artificial-Intelligence": (_AI_COST, _AI_COST_PAPER, _ICEBERG),
    "Business-and-Economics/Best-Practices-and-Success-Stories/Honda": (_RESUME,),
    "Career-and-Education": (_ABOUT, _RESUME, _REPORT),
    "Career-and-Education/Job-Experiences": (_RESUME, _REPORT),
    "Career-and-Education/Job-Experiences/Process-Engineering": (_RESUME,),
    "Career-and-Education/Job-Experiences/Business-Intelligence": (_RESUME,),
    "Career-and-Education/Job-Experiences/Corporate-Research-and-Development": (_RESUME,),
    "Career-and-Education/Projects": (_PROJECTS, _MAP, _SMASH, _DASH),
    "Career-and-Education/Projects/KUBO-NO2-Sensor": (_PROJECTS,),
    "Career-and-Education/Projects/Pandas-Projects": (_GAS, _ICEBERG, _ALBERTA, _SMASH, _DASH, _VOCAB),
    "Career-and-Education/Projects/Mental-Map": (_MAP, _GUIDE),
    "Sports-and-Entertainment": (_DASH, _RULES, _PITCH),
    "Sports-and-Entertainment/Series-Hub/History": (Feature(DASHBOARD + "#series-log", "Analytics · Every finish", "The series log",
                                                            "All thirteen series in order, with winner sequences.", "Sports-and-Entertainment/Series-Hub/History",
                                                            date="2026-10-04"),),
    "Sports-and-Entertainment/Series-Hub/Records": (Feature(DASHBOARD + "#timing-title", "Analytics · 3 Point times", "Recorded times",
                                                            "Listed completion times, with missing values kept missing.", "Sports-and-Entertainment/Series-Hub/Records",
                                                            date="2026-10-04"),),
    "Sports-and-Entertainment/Sports-Analytics": (_UFC, _NBA),
    PREDICTIONS: (_UFC, _NBA),
    "Gaming-and-Performance-Log": (_SMASH, _RUN, _LIFT, _SLEEP),
    "Gaming-and-Performance-Log/Smash-Bros": (_SMASH, _RANK, _SCORE, _OPPONENTS),
    "Gaming-and-Performance-Log/Smash-Bros/New-Smash-Mains": (_SMASH,),
    "Gaming-and-Performance-Log/Smash-Bros/Next-Smash-Mains": (_SMASH,),
    "Gaming-and-Performance-Log/Smash-Bros/Player-Statistics": (_RANK, _SCORE),
    _ATHLETICS: (_RUN, _SWIM, _LIFT),
    _HEALTH: (_SLEEP, _DIET),
    f"{_HEALTH}/Analytics": (_SLEEP, _DIET),
    f"{_HEALTH}/Mentality": (_SLEEP,),
    "Language-and-Programming": (_WORKBENCH, _VOCAB, _FEEL, _LEET),
    "Language-and-Programming/Rap": (_WORKBENCH, _VOCAB, _FEEL),
    "Language-and-Programming/Learning-Progress": (_WORKBENCH, _ICEBERG, _ALBERTA),
    "Language-and-Programming/Text-Analysis": (_VOCAB, _FEEL),
    "Language-and-Programming/Text-Analysis/Lexicon": (_VOCAB, _FEEL),
    "Language-and-Programming/LeetCode": (_LEET, _DSA),
    **_LEETCODE_LEAVES,
    **_RAP_LEAVES,
    "Language-and-Programming/Coding-Projects": (_WORKBENCH, _CHANGES, _UPCOMING, _SMASH, _DASH),
    "Language-and-Programming/Coding-Projects/Simulations": (_DIPOLE,),
    "Language-and-Programming/Coding-Projects/Database-Exploration": (_WORKBENCH, _DATABASE),
    "Language-and-Programming/Coding-Projects/Relational-Database-Development": (_WORKBENCH, _DATABASE),
    "Language-and-Programming/Coding-Projects/Website-Changes": (_WORKBENCH, _CHANGES, _UPCOMING, _DATABASE, _ATLAS),
}


def _validate() -> None:
    unknown = {key for key in FEATURES if key not in NODES}
    unknown |= {item.icon for items in FEATURES.values() for item in items if item.icon not in NODES}
    if unknown:
        raise ValueError(f"Features reference unknown atlas nodes: {sorted(unknown)}")
    for item in {item for items in FEATURES.values() for item in items}:
        Date.fromisoformat(item.date)  # Every card shows the date it was added.


_validate()


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def prefix(node: Node) -> str:
    return "../" * node.depth


def tone(node: Node) -> str:
    return TONES[lineage(node)[1].index] if node.depth else "home"


def mental_href(node: Node, root: str) -> str:
    target = anchor(node)
    return root + MENTAL_MAP + (f"#{target}" if target else "")


def _hint(node: Node) -> str:
    if node.tagline:
        return f"{node.title} — {node.tagline}"
    return f"{node.title} — {'open the reader' if node.path in HOSTED else 'an outlined destination'}."


def hex_map(node: Node, mental: dict[str, str], label: str) -> str:
    """Six children around a Mental Map centre; every spoke ends at a real link."""
    root = prefix(node)
    spokes = "".join(f'<path class="map-spoke spoke-{child.position}" d="M300 300 L{POINTS[child.position][0]} {POINTS[child.position][1]}"/>'
                     for child in node.children)
    # --n (longest word) lets CSS shrink labels like "Electromagnetism" instead of splitting them.
    nodes = "".join(
        f'<a class="hex-node atlas-hover pos-{child.position} tone-{tone(child)}" data-topic="{child.position}" '
        f'data-hint="{_e(_hint(child))}" href="{_e(root + child.url)}"><span class="hex-inner">{icon_svg(child.key)}'
        f'<strong style="--n:{max(len(word) for word in child.title.split())}">{_e(child.title)}</strong></span></a>'
        for child in node.children)
    section = mental.get(anchor(node), "")
    sub = "The connecting thread" if not node.depth else (f"§ {section}" if section else "Open the notebook")
    centre = (f'<a class="hex-node atlas-hover node-mental-map" data-topic="center" '
              f'data-hint="{_e("Mental Map — " + (section or "the thread connecting every field") + ".")}" '
              f'href="{_e(mental_href(node, root))}"><span class="hex-inner">{icon_svg("root")}<small>{_e(sub)}</small>'
              '<strong>Mental Map</strong></span></a>')
    return (f'<nav class="hex-map" aria-label="{_e(label)}"><div class="hex-frame" aria-hidden="true"></div>'
            '<svg class="map-connections" viewBox="0 0 600 600" aria-hidden="true">'
            f'<path class="map-perimeter" d="M300 78 492 189 492 411 300 522 108 411 108 189Z"/>{spokes}'
            f'<circle class="map-ring" cx="300" cy="300" r="103"/></svg>{nodes}{centre}</nav>'
            '<p class="map-hint" id="map-hint" aria-live="polite">Follow a thread. See where it leads.</p>')


def crumbs(node: Node, extra: str = "") -> str:
    """Breadcrumbs for a node page, or for an attached page one level below it."""
    root = prefix(node) + ("../" if extra else "")
    chain = lineage(node)
    linked = chain if extra else chain[:-1]
    items = [f'<li><a href="{_e(root + item.url)}">{"Home" if not item.depth else _e(item.title)}</a></li>' for item in linked]
    items.append(f'<li aria-current="page">{_e(extra or chain[-1].title)}</li>')
    return f'<nav class="atlas-crumbs" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>'


def strip(node: Node, extra: str = "") -> str:
    """Location bar inserted at the top of hosted readers and explorers."""
    position = "Attached reader" if extra else f"Destination {node.index + 1} of 6"
    return (f'<div class="atlas-strip tone-{tone(node)}"><span class="atlas-strip-icon atlas-hover">{icon_svg(node.key)}</span>'
            f'{crumbs(node, extra)}<span class="atlas-strip-meta">{_e(position)}</span></div>')


def _date(value: str) -> str:
    day = Date.fromisoformat(value)
    return f'<time datetime="{day.isoformat()}">{day:%b} {day.day}, {day.year}</time>'


def features(node: Node, available) -> str:
    items = [item for item in FEATURES.get(node.path, ()) if available(item)]
    if not items:
        return ""
    root = prefix(node)
    cards = "".join(
        f'<a class="atlas-feature atlas-hover" href="{_e(root + item.href)}">{icon_svg(item.icon)}'
        f'<span class="atlas-feature-meta"><span class="eyebrow">{_e(item.eyebrow)}</span>{_date(item.date)}</span>'
        f'<h3>{_e(item.title)}</h3><p>{_e(item.text)}</p><span class="card-link">Open <span aria-hidden="true">↗</span></span></a>'
        for item in items)
    return (f'<section class="atlas-features" aria-labelledby="features-{_e(node.key.replace("/", "-"))}">'
            f'<h2 id="features-{_e(node.key.replace("/", "-"))}">Already in this {"field" if node.depth == 1 else "branch" if node.depth == 2 else "destination"}</h2>'
            f'<div class="atlas-feature-grid">{cards}</div></section>')


def _status(child: Node) -> str:
    if child.children:
        return f"{len(child.children)} destinations"
    return "Live" if child.path in HOSTED else ("Related links" if child.path in FEATURES else "Outlined")


def _siblings(node: Node) -> str:
    above = parent(node)
    if above is None:
        return ""
    root = prefix(node)
    links = []
    for item in above.children:
        current = ' aria-current="page"' if item is node else ''
        links.append(f'<li><a class="atlas-hover" href="{_e(root + item.url)}"{current}>{icon_svg(item.key)}<span>{_e(item.title)}</span></a></li>')
    return (f'<nav class="atlas-siblings" aria-label="{_e("More in " + above.title)}"><p class="eyebrow">More in {_e(above.title)}</p>'
            f'<ol>{"".join(links)}</ol></nav>')


def branch_stage(node: Node, mental: dict[str, str], available) -> str:
    """Breadcrumbs, copy and hexagon for a field (depth 1) or topic (depth 2)."""
    root = prefix(node)
    chain = lineage(node)
    eyebrow = (f"Field {node.index + 1:02d} of 06" if node.depth == 1
               else f"{chain[1].title} · Topic {node.index + 1} of 6")
    listing = "".join(
        f'<li><a class="atlas-hover" href="{_e(root + child.url)}">{icon_svg(child.key)}<span><strong>{_e(child.title)}</strong>'
        f'<small>{_e(child.tagline or _status(child))}</small></span></a></li>' for child in node.children)
    return f'''{crumbs(node)}<section class="atlas-stage tone-{tone(node)}"><div class="atlas-copy"><p class="eyebrow"><span class="status-dot"></span> {_e(eyebrow)}</p>
      <h1>{_e(node.title)}</h1><p class="lede">{_e(node.tagline)}</p>
      <div class="home-actions"><a class="button primary" href="{_e(mental_href(node, root))}">Open in the Mental Map <span aria-hidden="true">↗</span></a>
      <a class="text-link" href="{_e(root + ATLAS)}">See the full site atlas →</a></div>
      <ol class="atlas-children" aria-label="{_e("Inside " + node.title)}">{listing}</ol></div>
      <div class="map-column">{hex_map(node, mental, node.title + " · six paths")}</div></section>{features(node, available)}'''


def branch_body(node: Node, mental: dict[str, str], available) -> str:
    return f'<main id="main-content" class="atlas-page tone-{tone(node)}">{branch_stage(node, mental, available)}{_siblings(node)}</main>'


def leaf_body(node: Node, available, content: str = "", lede: str = "") -> str:
    """An outlined destination: ready for its first study, linked to related work.

    content (trusted markup) fills a destination that already has entries; lede replaces
    the outlined-destination sentence and is escaped.
    """
    root = prefix(node)
    chain = lineage(node)
    lede = lede or f"An outlined destination in {chain[2].title}. Its first study is being prepared; the related notes below are already open."
    return f'''<main id="main-content" class="atlas-page atlas-leaf tone-{tone(node)}">{crumbs(node)}
    <header class="leaf-hero"><div class="leaf-icon is-playing">{icon_svg(node.key)}</div><div>
      <p class="eyebrow">{_e(chain[1].title)} / {_e(chain[2].title)} · Destination {node.index + 1} of 6</p>
      <h1>{_e(node.title)}</h1>
      <p class="lede">{_e(lede)}</p>
      <div class="home-actions"><a class="button primary" href="{_e(root + chain[2].url)}">Back to {_e(chain[2].title)}</a>
      <a class="button ghost" href="{_e(mental_href(node, root))}">Related Mental Map notes <span aria-hidden="true">↗</span></a>
      <a class="text-link" href="{_e(root + ATLAS)}">Site atlas →</a></div></div></header>
    {content}{features(node, available)}{_siblings(node)}</main>'''


def premade_body(node: Node, name: str, eyebrow: str, text: str, plan: tuple[str, ...], lead: str) -> str:
    """A page attached below a destination, made ready before its content exists."""
    steps = "".join(f"<li>{_e(step)}</li>" for step in plan)
    return f'''<main id="main-content" class="atlas-page atlas-leaf tone-{tone(node)}">{lead}
    <header class="leaf-hero"><div class="leaf-icon is-playing">{icon_svg(node.key)}</div><div>
      <p class="eyebrow">{_e(eyebrow)}</p><h1>{_e(name)}</h1><p class="lede">{_e(text)}</p>
      <div class="home-actions"><a class="button primary" href="../index.html">Back to {_e(node.title)}</a>
      <a class="text-link" href="{_e(prefix(node) + '../' + ATLAS)}">Site atlas →</a></div></div></header>
    <section class="atlas-features" aria-labelledby="premade-plan"><h2 id="premade-plan">Ready for its first entries</h2>
      <ol class="premade-plan">{steps}</ol></section></main>'''


def home_hero(mental: dict[str, str], cue: str) -> str:
    return f'''<section class="home-stage snap-section" id="home-atlas" aria-labelledby="home-title"><div class="home-copy">
      <p class="eyebrow"><span class="status-dot"></span> The personal atlas of Liam McGrath</p>
      <h1 id="home-title">Curiosity.<br>Patterns.<br><em>Connections.</em></h1>
      <p class="home-description">A living notebook at the intersection of science, data and the things that make us human — built on <strong>Theory, Application, and Study</strong>.</p>
      <div class="home-actions"><a class="button primary" href="{MENTAL_MAP}">Enter the Mental Map <span aria-hidden="true">↗</span></a>
      <a class="button ghost" href="{WORKBENCH}">Open the Workbench <span aria-hidden="true">↗</span></a></div>
      <div class="home-caption"><span>01 — EXPLORE THE CONNECTIONS</span><p>Six fields. Thirty-six paths. 216 destinations.</p></div></div>
      <div class="map-column">{hex_map(ROOT, mental, "Six fields of exploration")}</div>{cue}</section>'''
