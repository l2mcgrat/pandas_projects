"""The six-way site outline behind every hexagon, route, icon and radial tree."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import re

POSITIONS = ("top", "upper-left", "upper-right", "lower-left", "bottom", "lower-right")

# (title, tagline, ((topic, tagline, (six destinations)), ...)); order = POSITIONS.
OUTLINE = (
    ("Science & Engineering", "Models, measurements and machines.", (
        ("Mathematics", "The language underneath every model.",
         ("Calculus & Vectors", "Probability & Statistics", "Linear Algebra", "Number Theory", "Set Theory", "Abstract Algebra")),
        ("Physics", "Models of the world, from orbits to orbitals.",
         ("Classical Mechanics", "Quantum Mechanics", "General & Special Relativity", "Electromagnetism", "Optics", "Thermodynamics")),
        ("Chemistry", "Bonds, reactions and the materials they make.",
         ("Organic Chemistry", "Inorganic Chemistry", "Electrochemistry", "Physical Chemistry", "Analytical Chemistry", "Materials Chemistry")),
        ("Biology", "Living systems, from molecules to minds.",
         ("Quantum Biology", "Biochemistry", "Genetics", "Cellular Biology", "Neuroscience", "Evolutionary Biology")),
        ("Psychology", "How minds perceive, decide and grow.",
         ("Biological Psychology", "Cognitive Psychology", "Personality Psychology", "Developmental Psychology", "Clinical Psychology", "Social Psychology")),
        ("Computer Science", "Computation, abstraction and machines that learn.",
         ("Artificial Intelligence", "Simulations", "Data Structures and Algorithms", "Computer Architecture", "Operating Systems", "Programming Languages")),
    )),
    ("Business & Economics", "Systems of exchange and decision.", (
        ("Law and Policy", "The rules that shape markets and societies.",
         ("Constitutional Law", "Corporate Law", "Criminal Law", "International Law", "Public Policy", "Regulatory Frameworks")),
        ("Microeconomics", "Choices, incentives and the markets they create.",
         ("Consumer Theory", "Producer Theory", "Market Structures", "Game Theory", "Behavioral Economics", "Information Economics")),
        ("Macroeconomics", "Growth, money and whole economies in motion.",
         ("Economic Growth", "Monetary Policy", "Fiscal Policy", "International Trade", "Business Cycles", "Development Economics")),
        ("Key Performance Indicators", "Measuring what matters in an organization.",
         ("Profitability Metrics", "Liquidity Metrics", "Efficiency Metrics", "Growth Metrics", "Customer Metrics", "Operational Metrics")),
        ("Emerging Industries", "Where new technology meets new markets.",
         ("Artificial Intelligence", "Biotechnology", "Renewable Energy", "Space Industry", "Robotics & Automation", "Quantum Technologies")),
        ("Best Practices & Success Stories", "Lessons from companies worth studying.",
         ("Honda", "Costco", "Berkshire Hathaway", "Microsoft", "NVIDIA", "Amazon")),
    )),
    ("Career & Education", "Where I have worked, learned and am heading.", (
        ("Job Experiences", "From simulation research to manufacturing analytics.",
         ("Quantum Molecular Dynamics Simulations", "Process Engineering", "Business Intelligence", "Corporate Research and Development", "Materials Engineer", "Lifeguarding Days")),
        ("Educational Favourites", "Courses that changed how I see the world.",
         ("Statistical Thermodynamics", "Continuum Mechanics", "Vector Calculus", "Nanofabrication", "Integrated Circuits", "Semiconductor Physics")),
        ("Waterloo Highlights", "The people and moments behind the degree.",
         ("Varsity Cheerleading", "Shenanigans", "Relationships", "Adventures and Highlights", "Academic Excellence", "Little Things")),
        ("Projects", "Things built, measured and shipped.",
         ("KUBO - NO2 Sensor", "Pandas Projects", "WebDev Consulting", "Raspberry Pi", "Mental Map", "Future Plans")),
        ("Future Planning", "Where the next chapters are heading.",
         ("E-Learning", "Europe Migration", "Networking and Connections", "Creative Endeavours", "New Age Promotion", "Roadmap to Logan")),
        ("Career Paths", "Different routes, compared side by side.",
         ("Logan", "Amar", "Rhema", "Owen", "Liam", "Calena")),
    )),
    ("Sports & Entertainment", "Court stories, screens and shows.", (
        ("Anime and Manga", "Studios, authors and the craft of animation.",
         ("SeriesGraph Top 50", "Anime Studios", "Legendary Authors", "Production Process", "Sakuga and Artstyles", "Upcoming Greatness")),
        ("Western Productions", "Film, television and the stories behind them.",
         ("SeriesGraph Top 50", "Adult Animation", "Comedians", "Production Process", "History of Film", "Controversies")),
        ("Big Brother & Survivor", "Strategy, social games and unforgettable seasons.",
         ("All Time Greats", "Starter Seasons", "Roadmaps to Victory", "Greatest Moments", "Predictions and Analytics", "Controversies")),
        ("YouTube", "Creators who teach, document and analyze.",
         ("Educational", "Parasocial", "Documentary", "Data Analytics", "History", "Personal")),
        ("Series Hub", "First to four: rules, records and analytics.",
         ("Videos", "Rules", "Analytics", "History", "Records", "Creator Petition")),
        ("Sports Analytics", "Predictions, metrics and outcomes across sports.",
         ("Player Rankings", "Metric Overview", "Statistics", "Predictions and Results", "Conditioning", "Shenanigans")),
    )),
    ("Gaming & Performance Log", "Competition, practice and progress, measured.", (
        ("Smash Bros", "Mains, mechanics and match analytics.",
         ("New Smash Mains", "Next Smash Mains", "Mechanics History", "Player Statistics", "Character Origins", "Highlights")),
        ("Steam", "A library of favourites, genres and achievements.",
         ("Favourites", "Achievements History", "Combat-Platformers", "Strategy", "History", "Shopping Cart")),
        ("Nintendo", "Consoles, classics and what comes next.",
         ("All-Time Greats", "Mario Sports", "Console Comparison", "Controversy", "History", "Upcoming Greats")),
        ("Athletics", "Running, swimming, lifting and training logs.",
         ("Running", "Swimming", "Weightlifting", "Training Schedule", "History", "Future Events")),
        ("Memory", "Techniques and tests for remembering more.",
         ("Names and Places", "Scientific Concepts", "Techniques", "Meditation Study", "Quiz Analytics", "Information Theory")),
        ("Health", "Sleep, diet and the habits behind performance.",
         ("Sleep", "Diet", "Mentality", "Information Consumption", "Analytics", "Struggles and Setbacks")),
    )),
    ("Language & Programming", "Words, rhythm, code and meaning.", (
        ("Rap", "Original projects, verses and themes.",
         ("Seven Deadly Sins", "Homewood & Trafalgar", "Made in Abyss", "Vagabond", "NanoFtheAbove", "Future Projects")),
        ("Linguistics", "How language means, changes and is learned.",
         ("Semantics", "Etymology", "Morphology", "Mathematical Linguistics", "Applied Linguistics", "Second Language Acquisition")),
        ("Text Analysis", "Measuring words, sentiment and style.",
         ("Sentiment", "Word Frequency", "Speech Patterns", "Lexicon", "Themes", "Journal Psychoanalysis")),
        ("LeetCode", "Patterns for solving problems in code.",
         ("Lists and Arrays", "Trees and Tries", "Graphs", "Dynamic Programming", "Recursion", "Hard Problems")),
        ("Learning Progress", "A record of what I am studying and why.",
         ("Formal Sciences", "Natural Sciences", "Social Sciences", "Business & Finance", "Economics & History", "Coursera & LeetCode")),
        ("Coding Projects", "Databases, simulations, websites and more.",
         ("Database Exploration", "Simulations", "WebDev Consulting", "Relational Database Development", "Miscellaneous", "Website Changes")),
    )),
)

# Each outline heading in mental_map.tex is preceded by "% atlas: <node path>".
MARKER = re.compile(r"^% atlas: (\S+)\r?\n\\(?:sub){0,2}section\{.*\}\\label\{([^{}]+)\}", re.M)


def mental_map_anchors(source: Path = Path(__file__).resolve().parents[1] / "mental_map.tex") -> dict[str, str]:
    """Node path -> Mental Map heading id, read from the notebook's own markers."""
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    return dict(MARKER.findall(text))


ANCHORS = mental_map_anchors()


@dataclass(frozen=True)
class Node:
    title: str
    path: str
    depth: int
    index: int
    tagline: str = ""
    children: tuple["Node", ...] = ()

    @property
    def key(self) -> str:
        return self.path or "root"

    @property
    def url(self) -> str:
        return f"{self.path}/index.html" if self.path else "index.html"

    @property
    def position(self) -> str:
        return POSITIONS[self.index] if self.depth else "center"

    @property
    def parent_path(self) -> str | None:
        return None if not self.depth else self.path.rpartition("/")[0]


def slug(title: str) -> str:
    return "-".join(re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", title.replace("&", " and ")))


def _build() -> Node:
    fields = []
    for i, (title, tagline, topics) in enumerate(OUTLINE):
        field = slug(title)
        subtopics = []
        for j, (topic, topic_tagline, leaves) in enumerate(topics):
            branch = f"{field}/{slug(topic)}"
            subtopics.append(Node(topic, branch, 2, j, topic_tagline, tuple(
                Node(leaf, f"{branch}/{slug(leaf)}", 3, k) for k, leaf in enumerate(leaves))))
        fields.append(Node(title, field, 1, i, tagline, tuple(subtopics)))
    return Node("Liam McGrath", "", 0, 0, "Curiosity. Patterns. Connections.", tuple(fields))


def walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from walk(child)


ROOT = _build()
NODES = {node.key: node for node in walk(ROOT)}


def _validate() -> None:
    if len(NODES) != 259:
        raise ValueError("The atlas must contain exactly 259 unique nodes.")
    for node in NODES.values():
        if node.depth < 3 and len(node.children) != 6:
            raise ValueError(f"{node.key} must have exactly six children.")
    if sum(node.depth == 3 for node in NODES.values()) != 216:
        raise ValueError("The atlas must contain exactly 216 destinations.")
    unknown = set(ANCHORS) - set(NODES)
    if unknown:
        raise ValueError(f"Mental Map anchors reference unknown nodes: {sorted(unknown)}")


_validate()


def parent(node: Node) -> Node | None:
    return None if node.parent_path is None else NODES[node.parent_path or "root"]


def lineage(node: Node) -> list[Node]:
    """Root first, ending with the node itself."""
    chain = [node]
    while (above := parent(chain[0])) is not None:
        chain.insert(0, above)
    return chain


def anchor(node: Node) -> str:
    for item in reversed(lineage(node)):
        if item.path in ANCHORS:
            return ANCHORS[item.path]
    return ""


def schema(node: Node = ROOT) -> dict:
    """Nested titles, path segments and Mental Map anchors; the browser computes the layout."""
    return {"t": node.title, "s": node.path.rpartition("/")[2], "a": ANCHORS.get(node.path, ""),
            "c": [schema(child) for child in node.children]}
