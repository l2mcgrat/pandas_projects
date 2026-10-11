"""Reorganize the merged Mental Map to follow the website: 6 fields, 36 topics, 216 destinations.

A one-time, reviewable migration. ``python -B -m site_content.restructure`` reports;
``--write`` replaces mental_map.tex (from then on the hand-edited canonical notebook)
and writes notebook_sources/restructure-manifest.json. It refuses to overwrite a
mental_map.tex edited after the last restructure unless --force is given.
The input is the reproducible merge archived in notebook_sources/merged/.

Every earlier block keeps its prose, math, labels and images. A block either
merges into a destination (its heading becomes the outline heading) or becomes a
child heading beneath one; deeper headings move down with it, at most to level 5.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
import re

from .atlas import NODES, ROOT as ATLAS_ROOT, Node, parent, slug

ROOT = Path(__file__).resolve().parents[1]
MERGED = ROOT / "notebook_sources" / "merged" / "mental_map.merged.tex"
OUTPUT = ROOT / "mental_map.tex"
MANIFEST = ROOT / "notebook_sources" / "restructure-manifest.json"
COMMANDS = ("section", "subsection", "subsubsection", "subsubsubsection", "subparagraph")
HEADING = re.compile(r"\\(section|subsection|subsubsection|subsubsubsection)(\*?)\{(.*)\}\s*")
ANY_HEADING = re.compile(r"(?m)^\\(?:sub)*section\*?\{")
LABEL = re.compile(r"\s*\\label\{([^{}]+)\}\s*")
# Assembly-era signposts that no longer describe what follows them.
TRANSITION = r"\textit{Historical notes follow; read alongside the editorial corrections.}"
CHAPTER_MARK = "% BEGIN MERGED CHAPTER:"
FRONT, BACK = "front", "back"
MERGE, CHILD, DROP = "merge", "child", "drop"

SE, BE, CE, SP, LP = ("Science-and-Engineering", "Business-and-Economics", "Career-and-Education",
                      "Sports-and-Entertainment", "Language-and-Programming")
PHYS = f"{SE}/Physics"
FAV = f"{CE}/Educational-Favourites"
PHYS_ADD = ("Physics", "Conservation, fields, and physical models across scales -- study additions")
CHEM_ADD = ("Chemistry", "Chemical balance, molecular structure, and measurement -- study additions")
NANO_ADD = ("Nanotechnology", "Nanodevices, photonics, and engineered interfaces -- study additions")
ML = "Machine Learning/Data Science/Artificial Intelligence"
JOBS = "Job Related Endeavors"
GAPS = "Things I understand at a High Level, but I don't understand at a Low enough Level"

# Earlier heading path -> (atlas node path, FRONT or BACK; mode). Unlisted headings move with their parent.
PLACE: dict[tuple[str, ...], tuple[str, str]] = {
    ("Introductory Summary",): (FRONT, MERGE),
    ("Philosophy",): (FRONT, CHILD),
    ("Sciences",): (SE, MERGE),
    ("Sciences", "Formal Sciences (Basically Math, Computer Science)"): (f"{LP}/Learning-Progress/Formal-Sciences", MERGE),
    ("Sciences", "Natural Sciences"): (f"{LP}/Learning-Progress/Natural-Sciences", MERGE),
    ("Sciences", "Social Sciences"): (f"{LP}/Learning-Progress/Social-Sciences", MERGE),
    ("Math",): (f"{SE}/Mathematics", MERGE),
    ("Math", "Linear structure, numerical reasoning, and uncertainty -- study additions"): (f"{SE}/Mathematics/Linear-Algebra", CHILD),
    ("Math", "Calculus"): (f"{SE}/Mathematics/Calculus-and-Vectors", MERGE),
    ("Math", "Linear Algebra"): (f"{SE}/Mathematics/Linear-Algebra", MERGE),
    ("Math", "Probability and Statistics"): (f"{SE}/Mathematics/Probability-and-Statistics", MERGE),
    ("Physics",): (PHYS, MERGE),
    PHYS_ADD: (f"{PHYS}/Classical-Mechanics", CHILD),
    (*PHYS_ADD, "Waves and optics"): (f"{PHYS}/Optics", CHILD),
    (*PHYS_ADD, "Maxwell fields, circuits, and carriers"): (f"{PHYS}/Electromagnetism", CHILD),
    (*PHYS_ADD, "Quantum states, ensembles, and relativity bridges"): (f"{PHYS}/Quantum-Mechanics", CHILD),
    ("Physics", "Classical Mechanics"): (f"{PHYS}/Classical-Mechanics", MERGE),
    ("Physics", "Continuum Mechanics"): (f"{FAV}/Continuum-Mechanics", MERGE),
    ("Physics", "Electromagnetism"): (f"{PHYS}/Electromagnetism", MERGE),
    ("Physics", "Quantum Mechanics"): (f"{PHYS}/Quantum-Mechanics", MERGE),
    ("Physics", "Statistical Thermodynamics"): (f"{PHYS}/Thermodynamics", MERGE),
    ("Physics", "Solid State Physics"): (f"{FAV}/Semiconductor-Physics", CHILD),
    ("Physics", "Relativity"): (f"{PHYS}/General-and-Special-Relativity", MERGE),
    ("Physics", "Theory of Everything"): (f"{PHYS}/General-and-Special-Relativity", CHILD),
    ("Physics", "Perturbed linear rotor -- companion draft"): (f"{PHYS}/Thermodynamics", CHILD),
    ("Chemistry",): (f"{SE}/Chemistry", MERGE),
    CHEM_ADD: (f"{SE}/Chemistry/Physical-Chemistry", CHILD),
    (*CHEM_ADD, "Polymers and biochemical function"): (f"{SE}/Chemistry/Materials-Chemistry", CHILD),
    (*CHEM_ADD, "Characterization, uncertainty, and safety"): (f"{SE}/Chemistry/Analytical-Chemistry", CHILD),
    ("Biology",): (f"{SE}/Biology", MERGE),
    ("Biology", "Cell Biology"): (f"{SE}/Biology/Cellular-Biology", MERGE),
    ("Biology", "Human Body"): (f"{SE}/Biology/Neuroscience", CHILD),
    ("Psychology",): (f"{SE}/Psychology", MERGE),
    ("Psychology", "The Big 5"): (f"{SE}/Psychology/Personality-Psychology", CHILD),
    ("Psychology", "Theory of Multiple Intelligence's"): (f"{SE}/Psychology/Developmental-Psychology", CHILD),
    ("Psychology", "Cognitive Science"): (f"{SE}/Psychology/Cognitive-Psychology", CHILD),
    ("Computation",): (f"{SE}/Computer-Science", MERGE),
    ("Computation", "Self-taught DSA and LeetCode problem-solving patterns -- study additions"): (f"{SE}/Computer-Science/Data-Structures-and-Algorithms", CHILD),
    ("Computation", "Fundamentals of Computation"): (f"{SE}/Computer-Science/Computer-Architecture", CHILD),
    ("Computation", "LINUX"): (f"{SE}/Computer-Science/Operating-Systems", MERGE),
    ("Computation", "python"): (f"{SE}/Computer-Science/Programming-Languages", CHILD),
    ("Computation", "C++"): (f"{SE}/Computer-Science/Programming-Languages", CHILD),
    ("Computation", "Other Peoples Programs"): (f"{SE}/Computer-Science/Simulations", MERGE),
    ("Computation", "Other Peoples Programs", "Coop Project Using MMTK"): (f"{CE}/Job-Experiences/Quantum-Molecular-Dynamics-Simulations", MERGE),
    (ML,): (f"{SE}/Computer-Science/Artificial-Intelligence", MERGE),
    (ML, "Machine Learning"): (f"{SE}/Computer-Science/Artificial-Intelligence", MERGE),
    (ML, "Artificial Intelligence"): (f"{SE}/Computer-Science/Artificial-Intelligence", MERGE),
    (ML, "Artificial Intelligence", "Natural Language Processing"): (f"{LP}/Linguistics/Mathematical-Linguistics", MERGE),
    (ML, "Artificial Intelligence", "AI Business Reports"): (f"{BE}/Emerging-Industries/Artificial-Intelligence", CHILD),
    ("Nanotechnology",): (FAV, MERGE),
    NANO_ADD: (f"{FAV}/Nanofabrication", CHILD),
    (*NANO_ADD, "From energy bands to a p--n junction"): (f"{FAV}/Semiconductor-Physics", CHILD),
    (*NANO_ADD, "Photonics and confinement"): (f"{PHYS}/Optics", CHILD),
    (*NANO_ADD, "Surfaces and electrochemical energy"): (f"{SE}/Chemistry/Electrochemistry", CHILD),
    ("Nanotechnology", "Nanoelectronics"): (f"{FAV}/Integrated-Circuits", MERGE),
    ("Engineering",): (f"{PHYS}/Classical-Mechanics", DROP),
    ("Engineering", "Completed SYDE 352: feedback analysis and controller design -- study additions"): (f"{PHYS}/Classical-Mechanics", CHILD),
    ("Business",): (BE, MERGE),
    ("Economics",): (BE, MERGE),
    ("Economics", "Macroeconomics"): (f"{BE}/Macroeconomics", MERGE),
    ("Economics", "Microeconomics"): (f"{BE}/Microeconomics", MERGE),
    ("Economics", "Industries"): (f"{BE}/Macroeconomics/Development-Economics", MERGE),
    ("History",): (f"{LP}/Learning-Progress/Economics-and-History", MERGE),
    ("Sociology",): (f"{LP}/Learning-Progress/Social-Sciences", CHILD),
    ("Theology",): (f"{LP}/Rap/Seven-Deadly-Sins", MERGE),
    ("Theology", "Seven Deadly Sins/Heavenly Virtues"): (f"{LP}/Rap/Seven-Deadly-Sins", MERGE),
    (JOBS,): (CE, MERGE),
    (JOBS, "Data Scientist/Analyst Type Positions"): (f"{CE}/Career-Paths/Liam", MERGE),
    (JOBS, "Chemical, Material, Nanotechnology Engineering Type Jobs"): (f"{CE}/Job-Experiences/Materials-Engineer", CHILD),
    (JOBS, "Service/Retail Type Work"): (f"{CE}/Job-Experiences/Lifeguarding-Days", CHILD),
    (JOBS, "Employment"): (f"{CE}/Job-Experiences", MERGE),
    (GAPS,): (f"{LP}/Learning-Progress/Natural-Sciences", CHILD),
    (GAPS, "Physics"): (f"{LP}/Learning-Progress/Natural-Sciences", DROP),
    (GAPS, "Physics", "PN Junctions"): (f"{FAV}/Semiconductor-Physics", CHILD),
    ("YouTube Videos",): (f"{SP}/YouTube", MERGE),
    ("Imported image archive",): (BACK, CHILD),
}

# Destinations whose notes live elsewhere get a cross-reference instead of a blank.
SEE_ALSO = {
    f"{FAV}/Statistical-Thermodynamics": (f"{PHYS}/Thermodynamics",),
    f"{FAV}/Vector-Calculus": (f"{SE}/Mathematics/Calculus-and-Vectors",),
    f"{LP}/LeetCode": (f"{SE}/Computer-Science/Data-Structures-and-Algorithms",),
    f"{LP}/Text-Analysis": (f"{LP}/Linguistics/Mathematical-Linguistics",),
    f"{LP}/Coding-Projects/Simulations": (f"{SE}/Computer-Science/Simulations",),
}

FRONT_TEXT = r"""\textit{Reorganized on 4 October 2026 to follow the website.}

The six numbered sections match the six fields of the website, in the order of the home hexagon. Each has six subsections (the topics), and each subsection has six subsubsections (the destinations): 216 places for notes. Numbers match the site, so 1.2.2 is Science \& Engineering, Physics, Quantum Mechanics.

Earlier writing was moved, not rewritten. Each block now sits under the destination it fits best, and its own headings moved down a level; where a heading was folded into a destination, a short note names the earlier heading. Destinations without notes yet say so. A comment beginning \texttt{\% atlas:} sits above every outline heading: keep those comments and their labels so each hexagon on the website can link to its section."""

PLACEHOLDER = r"\textit{Open for notes: this destination is outlined on the website and ready for its first entry.}"


@dataclass
class Block:
    level: int
    title: str
    star: bool
    path: tuple[str, ...]
    order: int
    body: list[str] = field(default_factory=list)
    children: list["Block"] = field(default_factory=list)


@dataclass
class Slot:
    bodies: list[tuple[int, list[str]]] = field(default_factory=list)
    items: list[tuple[int, list[str]]] = field(default_factory=list)
    label: str | None = None


def parse(text: str) -> tuple[str, list[str], list[Block], list[Block]]:
    """Split the document body into a heading tree; returns preamble, intro, roots, all blocks."""
    preamble, rest = text.split("\\begin{document}", 1)
    body = rest.rsplit("\\end{document}", 1)[0]
    roots: list[Block] = []
    blocks: list[Block] = []
    stack: list[Block] = []
    intro: list[str] = []
    for line in body.split("\n"):
        match = HEADING.fullmatch(line)
        if not match:
            (stack[-1].body if stack else intro).append(line)
            continue
        level = COMMANDS.index(match[1]) + 1
        while stack and stack[-1].level >= level:
            stack.pop()
        block = Block(level, match[3], bool(match[2]), (stack[-1].path if stack else ()) + (match[3],), len(blocks))
        (stack[-1].children if stack else roots).append(block)
        blocks.append(block)
        stack.append(block)
    if len(blocks) != len(ANY_HEADING.findall(body)):
        raise ValueError("A heading shares its line with other text; restructure cannot place it safely.")
    return preamble, intro, roots, blocks


def active(lines: list[str]) -> str:
    """Text that renders: no comments, page breaks or whitespace."""
    text = re.sub(r"(?<!\\)%[^\n]*", "", "\n".join(lines))
    return re.sub(r"\\(?:newpage|clearpage)\b|\s+", "", text)


def clean(lines: list[str]) -> list[str]:
    kept = [line for line in lines if not line.startswith(CHAPTER_MARK) and line.strip() != TRANSITION]
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    return kept


def escape(text: str) -> str:
    return text.replace("&", r"\&").replace("%", r"\%")


def heading(level: int, title: str, star: bool = False) -> str:
    if not 1 <= level <= len(COMMANDS):
        raise ValueError(f"Heading {title!r} would land at level {level}; give it its own placement.")
    return f"\\{COMMANDS[level - 1]}{'*' if star else ''}{{{title}}}"


def render(block: Block, level: int, star: bool) -> list[str]:
    lines = [heading(level, block.title, star or block.star), *clean(block.body)]
    for child in block.children:
        if child.path not in PLACE:
            lines += ["", *render(child, level + child.level - block.level, star)]
    return lines


def _similar(old: str, new: str) -> bool:
    a, b = (" ".join(re.findall(r"[a-z0-9]+", value.lower().replace("&", " and "))) for value in (old, new))
    return a in b or b in a


def place(blocks: list[Block]) -> tuple[dict[str, Slot], list[dict]]:
    slots: dict[str, Slot] = {}
    log = []
    for block in blocks:
        if block.path not in PLACE:
            continue
        target, mode = PLACE[block.path]
        matter = target in (FRONT, BACK)
        node = None if matter else NODES[target]
        base = {FRONT: 1, BACK: 0}[target] if matter else node.depth
        slot = slots.setdefault(target, Slot())
        loose = [child for child in block.children if child.path not in PLACE]
        if mode == DROP:
            if active(block.body) or loose:
                raise ValueError(f"{block.path} is dropped but still has content of its own.")
        elif mode == CHILD:
            if node is not None and node.depth != 3:
                raise ValueError(f"{block.path} can only become a child of a destination.")
            slot.items.append((block.order, render(block, base + 1, matter)))
        else:
            body = clean(block.body)
            if body and (label := LABEL.fullmatch(body[0])):
                if slot.label:
                    raise ValueError(f"{target} would receive two heading labels.")
                slot.label, body = label[1], body[1:]
            if node is not None and (active(body) or loose) and not _similar(block.title, node.title):
                body = [rf"\textit{{From the earlier heading ``{block.title}''.}}", "", *body]
            slot.bodies.append((block.order, body))
            for child in loose:
                if node is not None and node.depth < 3:
                    raise ValueError(f"{child.path} needs its own placement below {target}.")
                slot.items.append((child.order, render(child, base + child.level - block.level, matter)))
        log.append({"from": " > ".join(block.path), "to": target, "mode": mode})
    return slots, log


def node_ids(slots: dict[str, Slot]) -> dict[str, str]:
    bases = {key: slug(node.title).lower() for key, node in NODES.items() if node.depth}
    counts = Counter(bases.values())
    ids = {}
    for key, base in bases.items():
        if key in slots and slots[key].label:
            ids[key] = slots[key].label
            continue
        if counts[base] > 1:
            base = slug(parent(NODES[key]).title).lower() + "-" + base
        ids[key] = "sec:" + base
    if len(set(ids.values())) != len(ids):
        raise ValueError("Outline heading labels must be unique.")
    return ids


def is_open(node: Node, slot: Slot) -> bool:
    return node.depth == 3 and not slot.items and not any(active(body) for _, body in slot.bodies)


def _emit(node: Node, slots: dict[str, Slot], ids: dict[str, str]) -> list[str]:
    slot = slots.get(node.key, Slot())
    lines = [f"% atlas: {node.path}", heading(node.depth, escape(node.title)) + f"\\label{{{ids[node.key]}}}"]
    if node.tagline:
        lines.append(rf"\textit{{{escape(node.tagline)}}}")
    bodies = [body for _, body in sorted(slot.bodies)]
    if is_open(node, slot):
        lines.append(PLACEHOLDER)
    if node.key in SEE_ALSO:
        refs = ", ".join(rf"Section~\ref{{{ids[key]}}}" for key in SEE_ALSO[node.key])
        lines += ["", rf"\textit{{Related notes: {refs}.}}"]
    for body in bodies:
        if body:
            lines += ["", *body]
    if node.depth < 3:
        if slot.items:
            raise ValueError(f"{node.key} cannot hold loose headings above its destinations.")
        for child in node.children:
            lines += ["", *_emit(child, slots, ids)]
    else:
        for _, item in sorted(slot.items):
            lines += ["", *item]
    return lines


def restructure(text: str) -> tuple[str, dict]:
    preamble, intro, roots, blocks = parse(text)
    if active(intro) != r"\maketitle\tableofcontents":
        raise ValueError("Unexpected content before the first section.")
    paths = Counter(block.path for block in blocks)
    if (repeated := [path for path, count in paths.items() if count > 1 and path in PLACE]):
        raise ValueError(f"Ambiguous placement paths: {repeated}")
    if (stale := sorted(set(PLACE) - set(paths))):
        raise ValueError(f"Placements name headings that no longer exist: {stale}")
    if (loose := [block.path for block in roots if block.path not in PLACE]):
        raise ValueError(f"Top-level sections without a placement: {loose}")
    slots, log = place(blocks)
    ids = node_ids(slots)
    out = [preamble.rstrip("\n"), "", r"\begin{document}", r"\maketitle", r"\tableofcontents", "",
           r"\section*{About this notebook}\label{about-this-notebook}", FRONT_TEXT]
    front = slots.get(FRONT, Slot())
    for _, body in sorted(front.bodies):
        if body:
            out += ["", *body]
    for _, item in sorted(front.items):
        out += ["", *item]
    for item in ATLAS_ROOT.children:
        out += ["", *_emit(item, slots, ids)]
    for _, item in sorted(slots.get(BACK, Slot()).items):
        out += ["", *item]
    output = "\n".join(out) + "\n\n\\end{document}\n"
    leaves = [node for node in NODES.values() if node.depth == 3]
    open_count = sum(is_open(node, slots.get(node.key, Slot())) for node in leaves)
    manifest = {
        "schemaVersion": 1,
        "input": {"path": MERGED.relative_to(ROOT).as_posix(), "sha256": sha256(text.encode("utf-8")).hexdigest()},
        "outline": {"fields": 6, "topics": 36, "destinations": len(leaves)},
        "destinationsWithNotes": len(leaves) - open_count, "openDestinations": open_count,
        "placements": log, "labels": ids,
        "policy": "Prose, math, labels and images moved unchanged; merged headings are named in a short note; "
                  "two assembly signposts (chapter comments and 'Historical notes follow') were removed.",
        "outputSha256": sha256(output.encode("utf-8")).hexdigest(),
    }
    return output, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Replace mental_map.tex and the restructure manifest")
    parser.add_argument("--force", action="store_true", help="Overwrite even if mental_map.tex was edited since")
    args = parser.parse_args()
    output, manifest = restructure(MERGED.read_text(encoding="utf-8"))
    print(f"Restructured notebook: {len(output.splitlines())} lines; "
          f"{manifest['destinationsWithNotes']} destinations with notes, {manifest['openDestinations']} open.")
    if not args.write:
        return
    current = sha256(OUTPUT.read_bytes()).hexdigest() if OUTPUT.exists() else ""
    previous = json.loads(MANIFEST.read_text(encoding="utf-8"))["outputSha256"] if MANIFEST.exists() else manifest["input"]["sha256"]
    if current and current != previous and not args.force:
        raise SystemExit("mental_map.tex has edits made after the last restructure; rerun with --force to discard them.")
    OUTPUT.write_text(output, encoding="utf-8", newline="\n")
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.name} and {MANIFEST.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
