"""Snap-scrolling "respected creators" showcase that follows the home-page hero.

API: creators_html() -> str returns sibling <section class="creator-section
snap-section"> fragments (no <main>); scroll_cue_html(target_id) -> str returns
the hero's indicator link; FIRST_SECTION_ID is the first rendered section id.
Home page only (depth 0): <main class="home-landing home-snap">, hero section
class="home-stage snap-section" containing scroll_cue_html(FIRST_SECTION_ID),
then creators_html(); shell(..., styles=("assets/creators.css",),
scripts=("assets/creators.js",)). No inline scripts, styles or handlers.
Friends render only once BOTH consent=True and a validated https url are set;
until then neither their section nor their name appears anywhere in the output.
Public-figure blurbs are starter text grounded in their own sites (Liam rewrites
them) and imply no affiliation, endorsement or personal relationship.
Every rendered URL must be https on the creator's own domain(s) and never a
store, merch, donation, membership, sponsorship or ticket page; violations raise.
Previews are original SVG art; set `image` (assets/creators/<slug>.<ext>) only
for a consented photo or screenshot to replace it.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import math
import re
from typing import Callable
from urllib.parse import urlsplit

__all__ = [
    "CLOSING_ID", "CREATORS", "Creator", "FIRST_SECTION_ID", "Highlight", "TOP_ID",
    "creators_html", "scroll_cue_html", "section_id", "visible_creators",
]

TOP_ID = "main-content"
CLOSING_ID = "creator-more"
THEMES = ("violet", "azure", "ember", "jade", "rose")
MAX_HIGHLIGHTS = 5
# URL tokens (split on non-alphanumerics) starting with these are never linked.
BLOCKED_TERMS = (
    "store", "merch", "shop", "donat", "patreon", "sponsor", "member", "ticket",
    "support", "checkout", "subscribe", "buy",
)
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ANCHOR = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_IMAGE = re.compile(r"assets/creators/[a-z0-9]+(?:-[a-z0-9]+)*\.(?:avif|webp|png|jpe?g)")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_UNSAFE_URL_CHARS = frozenset('<>"\'`\\{}|^')


@dataclass(frozen=True)
class Highlight:
    label: str
    description: str
    url: str | None  # None: a project that is not live yet, shown without a link
    symbol: str
    source: str | None  # page on which this exact link was found (audit trail, not rendered)


@dataclass(frozen=True)
class Creator:
    key: str
    name: str
    url: str | None = None
    domains: tuple[str, ...] = ()
    public_figure: bool = False
    consent: bool = False
    eyebrow: str = ""
    tagline: str = ""
    blurb: str = ""
    highlights: tuple[Highlight, ...] = ()
    art: str = "orbit"
    theme: str = "violet"
    image: str | None = None
    verified: str = ""  # date the links were last checked against the live site


_3B1B = "https://www.3blue1brown.com/"
_COMPLEXLY = "https://complexly.org/"
_WHAT_TO_EAT = "https://wwhattoeat.com/"
_SMALL_SHOTS = "https://www.smallshots.ca/"

CREATORS: tuple[Creator, ...] = (
    Creator(
        key="owen", name="Owen Paget", url=_WHAT_TO_EAT, domains=("wwhattoeat.com", "www.wwhattoeat.com"),
        consent=True, eyebrow="Builder, friend and rival", tagline="Small tools for everyday questions.",
        blurb=("Owen Paget builds web tools for everyday questions. His first live site, What to Eat, turns "
               "dinner indecision into a trip around the world: pick a meal, hover over a country to preview its "
               "dishes, or let it surprise you. A creator hub and a stock-monitoring tool are next. Owen is also "
               "Liam's longtime rival, from high-school swimming to the First to Four basketball series."),
        highlights=(
            Highlight("What to Eat",
                      "A world map of recipes: choose breakfast, lunch or dinner, hover over a country to preview "
                      "its dishes, or press Surprise me.",
                      _WHAT_TO_EAT, "globe", _WHAT_TO_EAT),
            Highlight("Creator Hub", "A home for creators and their work.", None, "hub", None),
            Highlight("Stock Monitoring", "A tool for keeping an eye on the markets.", None, "chart", None),
        ),
        theme="ember", image="assets/creators/owen.webp", verified="2026-10-04",
    ),
    Creator(key="camille", name="Camille", url=None, consent=False, theme="rose"),
    Creator(
        key="asha", name="Asha", url=_SMALL_SHOTS, domains=("www.smallshots.ca", "smallshots.ca"),
        consent=True, eyebrow="Photography, close up and far out", tagline="Shots of things that are small, and things that make me feel small.",
        blurb=("Asha's Small Shots looks in two directions. Up close: bubbles and CDs, plants and foods, "
               "animals and insects. Far out: skies, road trips and long exposures, the things that make her feel small."),
        highlights=(
            Highlight("Small Things", "Close-ups in four sets: Bubbles & CDs, Plants & Foods, Animals & Insects, and Everything Else.",
                      "https://www.smallshots.ca/smallthings", "camera", _SMALL_SHOTS),
            Highlight("Things That Make Me Feel Small", "Wide views in three sets: Sky, Road Trips and Long Exposure.",
                      "https://www.smallshots.ca/things-that-make-me-feel-small", "globe", _SMALL_SHOTS),
            Highlight("Long Exposure", "Light and motion gathered over seconds into a single frame.",
                      "https://www.smallshots.ca/things-that-make-me-feel-small/project-two-ky966-n329z-nnx53-feazs-ajmse-jf5w2",
                      "spark", "https://www.smallshots.ca/things-that-make-me-feel-small"),
            Highlight("Road Trips", "Places seen along the way.",
                      "https://www.smallshots.ca/things-that-make-me-feel-small/project-four-l3zw3-dk9py-xcmem-llk7k-cnfna-p6ycj",
                      "signpost", "https://www.smallshots.ca/things-that-make-me-feel-small"),
        ),
        theme="jade", verified="2026-10-05",
    ),
    Creator(
        key="3blue1brown", name="3Blue1Brown", url=_3B1B,
        domains=("www.3blue1brown.com", "3blue1brown.com"), public_figure=True,
        eyebrow="Mathematics, made visible", tagline="Math, explained visually.",
        blurb=("Grant Sanderson’s 3Blue1Brown explains math visually. Some lessons build the "
               "foundations a STEM undergraduate needs; others are playful explorations of "
               "puzzles and beautiful problems. The site adds written and interactive versions "
               "of many videos, guided by the idea that loving math begins with deep understanding."),
        highlights=(
            Highlight("About the channel",
                      "Why it exists, who makes it, and answers to common questions, from the "
                      "animation tools to advice for new math creators.",
                      "https://www.3blue1brown.com/about", "compass", _3B1B),
            Highlight("Extras",
                      "Manim, the open-source animation library behind the videos, plus podcast "
                      "conversations, talks and collaborations.",
                      "https://www.3blue1brown.com/extras", "spark", _3B1B),
            Highlight("Summer of Math Exposition",
                      "The 2021 open invitation for anyone to publish a math explainer, which "
                      "drew more than 1,300 entries.",
                      "https://www.3blue1brown.com/blog/some1", "quill",
                      "https://www.3blue1brown.com/extras"),
            Highlight("Recommendations",
                      "Other places online to practise and explore math: problem collections, "
                      "interactive articles and fellow channels.",
                      "https://www.3blue1brown.com/blog/recommendations", "signpost",
                      "https://www.3blue1brown.com/extras"),
        ),
        art="fourier", theme="azure", verified="2026-10-03",
    ),
    Creator(
        key="complexly", name="Complexly", url=_COMPLEXLY,
        domains=("complexly.org", "www.complexly.org"), public_figure=True,
        eyebrow="Education, science & curiosity", tagline="Trustworthy learning, free for everyone.",
        blurb=("Founded in 2012 by Hank and John Green, Complexly is a nonprofit making trustworthy "
               "educational media that inspires curiosity and lowers barriers to knowledge-building. "
               "Its shows include Crash Course, SciShow, PBS Eons and Bizarre Beasts, each shaped by "
               "researchers, writers, hosts, artists and fact checkers."),
        highlights=(
            Highlight("Crash Course",
                      "Free, fast-paced courses (more than 50 so far) that accompany high-school "
                      "and college classes from the humanities to the sciences.",
                      "https://complexly.org/ourshow/crashcourse/", "book", _COMPLEXLY),
            Highlight("SciShow",
                      "Explores the unexpected, covering scientific topics in a fun, accessible way.",
                      "https://complexly.org/ourshow/scishow/", "flask", _COMPLEXLY),
            Highlight("Crash Course Creator Lab",
                      "A free, four-unit media-literacy project that takes high-school students "
                      "from research and scripting to a fact-checked video.",
                      "https://complexly.org/crash-course-creator-lab/", "camera", _COMPLEXLY),
            Highlight("All shows",
                      "The full directory, from PBS Eons and Journey to the Microcosmos to "
                      "The Art Assignment and Ours Poetica.",
                      "https://complexly.org/our-shows/", "grid", _COMPLEXLY),
            Highlight("Mission & values",
                      "Why Complexly exists: inquiry, narrative and accuracy, and the belief that "
                      "education is a human right.",
                      "https://complexly.org/about/", "beacon", _COMPLEXLY),
        ),
        art="constellation", theme="ember", verified="2026-10-03",
    ),
)


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _f(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def section_id(creator: Creator) -> str:
    return f"creator-{creator.key}"


def _host(url: str) -> str:
    return urlsplit(url).hostname or ""


def _site_label(url: str) -> str:
    host = _host(url)
    return host[4:] if host.startswith("www.") else host


def _checked_url(url: object, allowed: tuple[str, ...], what: str) -> str:
    if (not isinstance(url, str) or not url
            or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 or ch in _UNSAFE_URL_CHARS for ch in url)):
        raise ValueError(f"{what}: unsafe or empty URL {url!r}")
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme != "https" or parts.netloc != host or host not in allowed:
        raise ValueError(f"{what}: {url!r} must be https on {', '.join(allowed)}")
    if any(token.startswith(BLOCKED_TERMS) for token in re.split(r"[^a-z0-9]+", url.lower())):
        raise ValueError(f"{what}: {url!r} looks like a store, donation, membership or ticket link")
    return url


def _validate(creator: Creator) -> None:
    what = f"creator {creator.key!r}"
    if not isinstance(creator.name, str) or not creator.name.strip():
        raise ValueError(f"{what}: name is required")
    if creator.theme not in THEMES:
        raise ValueError(f"{what}: unknown theme {creator.theme!r}")
    if creator.art not in _ARTS:
        raise ValueError(f"{what}: unknown art {creator.art!r}")
    if creator.image is not None and not (isinstance(creator.image, str) and _IMAGE.fullmatch(creator.image)):
        raise ValueError(f"{what}: image must be a local assets/creators/<slug>.<ext> path")
    if creator.verified and not _DATE.fullmatch(creator.verified):
        raise ValueError(f"{what}: verified must be YYYY-MM-DD")
    allowed = tuple(domain.lower() for domain in creator.domains) or (_host(creator.url or ""),)
    _checked_url(creator.url, allowed, what)
    if len(creator.highlights) > MAX_HIGHLIGHTS:
        raise ValueError(f"{what}: at most {MAX_HIGHLIGHTS} highlights fit the layout")
    for item in creator.highlights:
        if not item.label.strip() or not item.description.strip():
            raise ValueError(f"{what}: highlights need a label and description")
        if item.symbol not in _SYMBOLS:
            raise ValueError(f"{what}: unknown symbol {item.symbol!r}")
        if item.url is None and item.source is None:
            continue
        _checked_url(item.url, allowed, f"{what} highlight {item.label!r}")
        _checked_url(item.source, allowed, f"{what} highlight source {item.label!r}")


def visible_creators() -> tuple[Creator, ...]:
    """Public figures with a url, and friends with consent=True and a url, all validated."""
    keys = [creator.key for creator in CREATORS]
    for key in keys:
        if not isinstance(key, str) or not _SLUG.fullmatch(key) or f"creator-{key}" == CLOSING_ID:
            raise ValueError(f"invalid creator key {key!r}")
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate creator keys")
    shown = tuple(creator for creator in CREATORS
                  if creator.url is not None and (creator.public_figure or creator.consent is True))
    for creator in shown:
        _validate(creator)
    return shown


# ---- Original preview artwork (no logos, characters, photos or screenshots) ----

def _svg_open(kind: str) -> str:
    return (f'<svg class="creator-art-svg creator-art-{kind}" viewBox="0 0 640 480" '
            'preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">')


def _fourier_art(uid: str, creator: Creator) -> str:
    """Epicycles whose rotation rates (1, -2, 4) trace the precomputed curve exactly."""
    del creator
    cx, cy = 320.0, 214.0
    radii, freqs = (92.0, 40.0, 20.0), (1, -2, 4)
    points = []
    for step in range(240):
        theta = 2 * math.pi * step / 240
        points.append((cx + sum(r * math.cos(n * theta) for r, n in zip(radii, freqs)),
                       cy + sum(r * math.sin(n * theta) for r, n in zip(radii, freqs))))
    curve = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points) + "Z"
    grid = "".join(f"M0 {y}H640" for y in range(14, 480, 40)) + "".join(f"M{x} 0V480" for x in range(0, 641, 40))
    near, far = [], []
    for gx in range(20, 640, 40):
        for gy in range(14, 480, 40):
            dx, dy = gx - cx, gy - cy
            distance = math.hypot(dx, dy)
            if distance < 46:
                continue
            vx, vy = -dy - 0.35 * dx, dx - 0.35 * dy
            scale = 8 / math.hypot(vx, vy)
            vx, vy = vx * scale, vy * scale
            angle = math.atan2(vy, vx)
            tip = (gx + vx, gy + vy)
            heads = [(tip[0] - 4.5 * math.cos(angle + side), tip[1] - 4.5 * math.sin(angle + side)) for side in (0.5, -0.5)]
            (near if distance < 200 else far).append(
                f"M{gx - vx:.1f} {gy - vy:.1f}L{tip[0]:.1f} {tip[1]:.1f}"
                f"M{heads[0][0]:.1f} {heads[0][1]:.1f}L{tip[0]:.1f} {tip[1]:.1f}L{heads[1][0]:.1f} {heads[1][1]:.1f}")
    r1, r2, r3 = (_f(r) for r in radii)
    return (
        f'{_svg_open("fourier")}<defs><radialGradient id="{uid}-bg" cx="50%" cy="44%" r="70%">'
        '<stop offset="0" stop-color="#1c3560"/><stop offset=".55" stop-color="#0f1a33"/><stop offset="1" stop-color="#0a0e1b"/></radialGradient>'
        f'<filter id="{uid}-soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7"/></filter></defs>'
        f'<rect width="640" height="480" fill="url(#{uid}-bg)"/>'
        f'<path class="creator-fourier-grid" d="{grid}"/><path class="creator-fourier-axis" d="M0 {_f(cy)}H640M{_f(cx)} 0V480"/>'
        f'<path class="creator-fourier-field creator-fourier-far" d="{"".join(far)}"/>'
        f'<path class="creator-fourier-field" d="{"".join(near)}"/>'
        f'<path class="creator-fourier-halo" filter="url(#{uid}-soft)" d="{curve}"/>'
        f'<path class="creator-fourier-curve" pathLength="1" d="{curve}"/>'
        f'<g transform="translate({_f(cx)} {_f(cy)})"><circle class="creator-epi-orbit" r="{r1}"/>'
        f'<g class="creator-epi creator-epi-1"><line class="creator-epi-arm" x2="{r1}"/><g transform="translate({r1} 0)">'
        f'<circle class="creator-epi-orbit" r="{r2}"/><circle class="creator-epi-joint" r="3"/>'
        f'<g class="creator-epi creator-epi-2"><line class="creator-epi-arm" x2="{r2}"/><g transform="translate({r2} 0)">'
        f'<circle class="creator-epi-orbit" r="{r3}"/><circle class="creator-epi-joint" r="2.5"/>'
        f'<g class="creator-epi creator-epi-3"><line class="creator-epi-arm" x2="{r3}"/>'
        f'<circle class="creator-epi-pen-glow" cx="{r3}" r="11"/><circle class="creator-epi-pen" cx="{r3}" r="4.5"/>'
        '</g></g></g></g></g><circle class="creator-epi-joint" r="4"/></g></svg>'
    )


_NET_NODES = (
    (150, 118, 4.0, "HISTORY"), (250, 84, 3.0, ""), (372, 76, 5.0, "LITERATURE"),
    (482, 120, 3.5, ""), (522, 222, 4.5, "ASTRONOMY"), (478, 320, 3.0, ""),
    (382, 372, 5.0, "DEEP TIME"), (262, 362, 3.5, ""), (160, 312, 4.5, "CHEMISTRY"),
    (122, 214, 3.0, ""), (238, 160, 3.0, "PSYCHOLOGY"), (404, 160, 3.0, "ART"),
    (414, 274, 3.0, "BIOLOGY"), (230, 276, 3.0, "PHILOSOPHY"),
)
_NET_EDGES = tuple((i, (i + 1) % 10) for i in range(10)) + (
    (0, 10), (2, 11), (4, 12), (8, 13), (10, 11), (11, 12), (12, 13), (13, 10),
)


def _constellation_art(uid: str, creator: Creator) -> str:
    """A curiosity constellation of subjects orbiting a hand-built question mark."""
    del creator
    cx, cy = 320.0, 218.0
    edges = "".join(f"M{_NET_NODES[a][0]} {_NET_NODES[a][1]}L{_NET_NODES[b][0]} {_NET_NODES[b][1]}" for a, b in _NET_EDGES)
    spokes = []
    for x, y, _, _ in _NET_NODES[10:]:
        angle = math.atan2(y - cy, x - cx)
        spokes.append(f"M{x} {y}L{cx + 64 * math.cos(angle):.1f} {cy + 64 * math.sin(angle):.1f}")
    stars, labels = [], []
    for index, (x, y, radius, label) in enumerate(_NET_NODES):
        stars.append(f'<circle class="creator-net-star creator-twinkle-{index % 3}" cx="{x}" cy="{y}" r="{_f(radius)}"/>')
        if label:
            right = x < cx
            labels.append(f'<text class="creator-net-label" x="{x + 11 if right else x - 11}" y="{y + 4}" '
                          f'text-anchor="{"start" if right else "end"}">{label}</text>')
    return (
        f'{_svg_open("constellation")}<defs><radialGradient id="{uid}-bg" cx="50%" cy="46%" r="72%">'
        '<stop offset="0" stop-color="#3a2416"/><stop offset=".5" stop-color="#1b1622"/><stop offset="1" stop-color="#0c0e1a"/></radialGradient>'
        f'<radialGradient id="{uid}-core" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f6b36e" stop-opacity=".42"/>'
        '<stop offset="1" stop-color="#f6b36e" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="640" height="480" fill="url(#{uid}-bg)"/>'
        f'<g transform="translate({_f(cx)} {_f(cy)})"><g class="creator-net-orbit">'
        '<ellipse class="creator-net-ring" rx="250" ry="92" transform="rotate(-16)"/>'
        '<ellipse class="creator-net-ring creator-net-ring-alt" rx="200" ry="150" transform="rotate(24)"/>'
        '<circle class="creator-net-moon" cx="250" cy="0" r="3.5" transform="rotate(-16)"/></g></g>'
        f'<path class="creator-net-edge" d="{edges}"/><path class="creator-net-edge creator-net-spoke" d="{"".join(spokes)}"/>'
        f'{"".join(stars)}{"".join(labels)}'
        f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="96" fill="url(#{uid}-core)"/>'
        f'<circle class="creator-net-halo" cx="{_f(cx)}" cy="{_f(cy)}" r="58"/>'
        '<path class="creator-net-question" d="M297 199a24 24 0 1 1 34 21c-7 4-11 9-11 17v5"/>'
        '<circle class="creator-net-dot" cx="320" cy="260" r="6"/></svg>'
    )


def _orbit_art(uid: str, creator: Creator) -> str:
    """Neutral placeholder for future friends who have not supplied an image."""
    return (
        f'{_svg_open("orbit")}<defs><radialGradient id="{uid}-bg" cx="50%" cy="45%" r="70%">'
        '<stop offset="0" stop-color="#2e2350"/><stop offset=".6" stop-color="#151830"/><stop offset="1" stop-color="#0b0e1a"/></radialGradient></defs>'
        f'<rect width="640" height="480" fill="url(#{uid}-bg)"/><g transform="translate(320 214)">'
        '<circle class="creator-orbit-ring" r="70"/><circle class="creator-orbit-ring" r="120"/><circle class="creator-orbit-ring" r="170"/>'
        '<g class="creator-orbit-spin"><circle class="creator-orbit-moon" cx="120" r="6"/></g>'
        '<g class="creator-orbit-spin creator-orbit-spin-slow"><circle class="creator-orbit-moon" cx="-170" r="4"/></g>'
        f'<text class="creator-orbit-initial" y="30" text-anchor="middle">{_e(creator.name[:1])}</text></g></svg>'
    )


_ARTS: dict[str, Callable[[str, Creator], str]] = {
    "fourier": _fourier_art, "constellation": _constellation_art, "orbit": _orbit_art,
}

# ---- Highlight symbols (original 24px line icons) ----

_SYMBOLS = {
    "compass": '<circle cx="12" cy="12" r="9"/><g class="creator-sym-spin"><path d="m12 5.5 2.2 6.5-2.2 6.5-2.2-6.5Z"/>'
               '<path class="creator-sym-fill" d="m12 5.5 2.2 6.5H9.8Z"/></g><circle cx="12" cy="12" r=".8"/>',
    "spark": '<path class="creator-sym-pulse" d="M12 3.5c.8 4.4 2.1 5.7 6.5 6.5-4.4.8-5.7 2.1-6.5 6.5-.8-4.4-2.1-5.7-6.5-6.5 4.4-.8 5.7-2.1 6.5-6.5Z"/>'
             '<path class="creator-sym-twinkle" d="M18.5 16v4m-2-2h4M5.5 4v2.5m-1.25-1.25h2.5"/>',
    "quill": '<g class="creator-sym-nudge"><path d="M19.5 4.5c-6 .5-10.5 4.5-12 11l-1 4 4-1c6.5-1.5 10.5-6 11-12Z"/>'
             '<path d="M6.5 19.5 14 12"/></g><path class="creator-sym-draw" pathLength="1" d="M3.5 21.5h9"/>',
    "signpost": '<path class="creator-sym-draw" pathLength="1" d="M5 20.5v-6a4 4 0 0 1 4-4h10"/><path class="creator-sym-nudge" d="m16 7.5 3 3-3 3"/>'
                '<path class="creator-sym-draw" pathLength="1" d="M5 14.5V3.5"/><circle cx="5" cy="20.5" r="1"/>',
    "book": '<path d="M3.5 6.5c3-1.3 5.8-1.1 8.5.8v12c-2.7-1.9-5.5-2.1-8.5-.8Z"/>'
            '<path class="creator-sym-nudge" d="M20.5 6.5c-3-1.3-5.8-1.1-8.5.8v12c2.7-1.9 5.5-2.1 8.5-.8Z"/>'
            '<path class="creator-sym-draw" pathLength="1" d="M6 10.5c1.4-.4 2.8-.2 4 .5M6 13.5c1.4-.4 2.8-.2 4 .5"/>',
    "flask": '<path d="M9.5 3.5h5M10.5 3.5v5.2L5.2 18a1.8 1.8 0 0 0 1.6 2.5h10.4a1.8 1.8 0 0 0 1.6-2.5l-5.3-9.3V3.5"/>'
             '<path d="M7.4 14.5h9.2"/><g class="creator-sym-rise"><circle cx="10.5" cy="17.4" r=".9"/>'
             '<circle cx="13.7" cy="16.6" r=".6"/><circle cx="12.1" cy="12.2" r=".6"/></g>',
    "camera": '<rect x="3" y="7" width="12.5" height="10" rx="2.2"/><path class="creator-sym-nudge" d="m15.5 10.5 5-3v9l-5-3"/>'
              '<circle class="creator-sym-pulse creator-sym-fill" cx="7" cy="10.5" r="1.2"/>',
    "grid": '<g class="creator-sym-dots">' + "".join(
        f'<circle cx="{x}" cy="{y}" r="1.7"/>' for y in (6, 12, 18) for x in (6, 12, 18)) + '</g>',
    "beacon": '<path d="M9 21h6l-1.2-11h-3.6Z"/><path d="M9.5 10h5M10.5 10V7h3v3"/>'
              '<path class="creator-sym-pulse" d="M4 5.5 8 7.5M20 5.5l-4 2M12 2v2.5"/>',
    "arrow": '<path class="creator-sym-nudge" d="M7 17 17 7M9 7h8v8"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><g class="creator-sym-spin"><path d="M12 3c-3.2 3-3.2 15 0 18M12 3c3.2 3 3.2 15 0 18"/></g>'
             '<path d="M3.6 9h16.8M3.6 15h16.8"/>',
    "hub": '<circle cx="12" cy="12" r="2.6"/><path d="m10.1 10.1-3.4-3.4m6.6 3.4 3.4-3.4m-6.6 6.6-3.4 3.4m6.6-3.4 3.4 3.4"/>'
           '<g class="creator-sym-pulse"><circle cx="5.4" cy="5.4" r="1.8"/><circle cx="18.6" cy="5.4" r="1.8"/>'
           '<circle cx="5.4" cy="18.6" r="1.8"/><circle cx="18.6" cy="18.6" r="1.8"/></g>',
    "chart": '<path d="M4 4v16h16"/><path class="creator-sym-draw" pathLength="1" d="m7.5 15 3.5-4 3 2.6 4.8-5.6"/>'
             '<path class="creator-sym-nudge" d="M15.6 8h3.2v3.2"/>',
}


def _symbol(name: str) -> str:
    return ('<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{_SYMBOLS[name]}</svg>')


# ---- Rendering ----

def _preview(creator: Creator, sid: str, site: str) -> str:
    if creator.image:
        art = f'<img class="creator-image" src="{_e(creator.image)}" alt="" loading="lazy" decoding="async">'
    else:
        art = _ARTS[creator.art](f"{sid}-art", creator)
    return (
        f'<a class="creator-preview" href="{_e(creator.url)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="creator-art">{art}</span><span class="creator-preview-label">'
        f'<span class="creator-preview-name">{_e(creator.name)}</span>'
        f'<span class="creator-preview-visit">Visit {_e(site)} <span class="creator-arrow" aria-hidden="true">↗</span></span>'
        '</span><span class="creator-sr"> (opens in a new tab)</span></a>'
    )


def _highlight(item: Highlight, sid: str, index: int, site: str) -> str:
    description_id = f"{sid}-highlight-{index}"
    if item.url is None:
        return (
            f'<li class="creator-highlight is-pending"><div class="creator-highlight-text">'
            f'<h3 class="creator-highlight-label">{_e(item.label)} <span class="creator-soon">Coming soon</span></h3>'
            f'<p class="creator-highlight-description" id="{description_id}">{_e(item.description)}</p></div>'
            f'<span class="creator-symbol is-pending" aria-hidden="true">{_symbol(item.symbol)}</span></li>'
        )
    return (
        f'<li class="creator-highlight"><div class="creator-highlight-text">'
        f'<h3 class="creator-highlight-label">{_e(item.label)}</h3>'
        f'<p class="creator-highlight-description" id="{description_id}">{_e(item.description)}</p></div>'
        f'<a class="creator-symbol" href="{_e(item.url)}" target="_blank" rel="noopener noreferrer" '
        f'aria-label="Open {_e(item.label)} on {_e(site)} (opens in a new tab)" aria-describedby="{description_id}">'
        f'{_symbol(item.symbol)}</a></li>'
    )


def _section(creator: Creator, number: int, total: int, next_id: str, next_label: str) -> str:
    sid = section_id(creator)
    site = _site_label(creator.url or "")
    eyebrow = f'<span class="creator-eyebrow-text">{_e(creator.eyebrow)}</span>' if creator.eyebrow else ""
    parts = [
        f'<section class="creator-section snap-section creator-theme-{creator.theme}" id="{sid}" aria-labelledby="{sid}-title">',
        '<div class="creator-inner">', _preview(creator, sid, site), '<div class="creator-copy">',
        f'<p class="creator-eyebrow"><span class="creator-count"><span class="creator-sr">Respected creator </span>{number:02d}'
        f'<span class="creator-sr"> of</span><span aria-hidden="true"> /</span> {total:02d}</span>{eyebrow}</p>',
        f'<h2 class="creator-title" id="{sid}-title">{_e(creator.name)}</h2>',
    ]
    if creator.tagline:
        parts.append(f'<p class="creator-tagline">{_e(creator.tagline)}</p>')
    if creator.blurb:
        parts.append(f'<p class="creator-blurb">{_e(creator.blurb)}</p>')
    if creator.highlights:
        rows = "".join(_highlight(item, sid, index, site) for index, item in enumerate(creator.highlights, 1))
        parts.append(f'<ul class="creator-highlights" aria-label="Valued sections of {_e(site)}">{rows}</ul>')
    if creator.public_figure:
        checked = f"; links checked {creator.verified}" if creator.verified else ""
        note = (f"Starter notes drawn from {_e(site)}{_e(checked)}. An independent appreciation, "
                f"not affiliated with or endorsed by {_e(creator.name)}.")
    else:
        note = f"Shared with {_e(creator.name)}’s permission."
    parts.append(
        f'<div class="creator-meta"><p class="creator-note">{note}</p>'
        f'<a class="creator-next" href="#{next_id}">{_e(next_label)} <span aria-hidden="true">↓</span></a></div>'
        '</div></div></section>'
    )
    return "".join(parts)


def _closing() -> str:
    dots = "".join(f'<circle class="creator-closing-dot creator-twinkle-{i % 3}" cx="{_f(60 + 46 * math.cos(i * 1.2566))}" '
                   f'cy="{_f(60 + 46 * math.sin(i * 1.2566))}" r="3"/>' for i in range(5))
    return (
        f'<section class="creator-section creator-closing snap-section" id="{CLOSING_ID}" aria-labelledby="{CLOSING_ID}-title">'
        '<div class="creator-closing-inner"><svg class="creator-closing-art" viewBox="0 0 120 120" aria-hidden="true" focusable="false">'
        '<circle class="creator-closing-ring" cx="60" cy="60" r="46"/><circle class="creator-closing-ring" cx="60" cy="60" r="28"/>'
        f'<g class="creator-closing-spin">{dots}</g>'
        '<path class="creator-closing-spark" d="M60 46c1 7 3 9 10 10-7 1-9 3-10 10-1-7-3-9-10-10 7-1 9-3 10-10Z"/></svg>'
        '<p class="creator-eyebrow"><span class="creator-eyebrow-text">The list keeps growing</span></p>'
        f'<h2 class="creator-title" id="{CLOSING_ID}-title">More respected creators are on the way</h2>'
        '<p class="creator-blurb">Friends, collaborators and creators whose work shaped this notebook will join here. '
        'Personal sites appear only once their makers have said yes.</p>'
        f'<a class="creator-top" href="#{TOP_ID}">Back to top <span aria-hidden="true">↑</span></a></div></section>'
    )


def creators_html() -> str:
    shown = visible_creators()
    sections = []
    for number, creator in enumerate(shown, 1):
        following = shown[number] if number < len(shown) else None
        next_id = section_id(following) if following else CLOSING_ID
        next_label = f"Next: {following.name}" if following else "More on the way"
        sections.append(_section(creator, number, len(shown), next_id, next_label))
    return "".join(sections) + _closing()


def scroll_cue_html(target_id: str) -> str:
    if not isinstance(target_id, str) or not _ANCHOR.fullmatch(target_id):
        raise ValueError(f"invalid scroll-cue target {target_id!r}")
    return (
        f'<a class="scroll-cue" href="#{target_id}"><span class="scroll-cue-label">Scroll to see other respected creators</span>'
        '<span class="scroll-cue-chevron" aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" focusable="false">'
        '<path class="scroll-cue-chev" d="m6 5 6 6 6-6"/><path class="scroll-cue-chev scroll-cue-chev-late" d="m6 12 6 6 6-6"/>'
        '</svg></span></a>'
    )


def _first_section_id() -> str:
    shown = visible_creators()
    return section_id(shown[0]) if shown else CLOSING_ID


FIRST_SECTION_ID = _first_section_id()
