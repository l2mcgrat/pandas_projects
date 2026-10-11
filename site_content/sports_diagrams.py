"""Original, deterministic house-rule diagrams; no records or publishing I/O.

Run from the repository root: python -B -m site_content.sports_diagrams
API: build_sports_diagrams(root) -> list[Path], ordered PNG then SVG per figure.
Only root/tex_images/sports is written. Importing this module writes nothing.
Reproducibility is byte-for-byte within the pinned Matplotlib/NumPy environment;
font/rasterizer/library upgrades can legitimately change rendered bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["DiagramSpec", "DIAGRAMS", "build_sports_diagrams"]

INK = "#183047"
TEAL = "#087f83"
ORANGE = "#b75016"
PAPER = "#fffdf7"
MUTED = "#536775"
PALE = "#e9f3ef"


@dataclass(frozen=True)
class DiagramSpec:
    slug: str
    game: str
    title: str
    subtitle: str


DIAGRAMS = (
    DiagramSpec("format_overview", "format", "FIRST TO FOUR / WINNER CHOOSES NEXT", "Two players · up to seven challenges · play order is not a preset playlist"),
    DiagramSpec("shooting_progression", "shooting", "SHOOTING / WALK THE COURT", "One make per player at a location; advance only when everyone makes"),
    DiagramSpec("shooting_attempts", "shooting", "SHOOTING / FIVE ATTEMPTS", "Five attempts per player, per shot location; mercy is a separate offer"),
    DiagramSpec("shooting_highjump", "shooting", "SHOOTING / HIGH JUMP RULES", "Unlimited offers do not mean an obligation to accept"),
    DiagramSpec("horse_cycle", "horse", "HORSE / SET, REPLICATE, ROTATE", "Announce the shot parameters before shooting; reasonable ambiguity is not a loophole"),
    DiagramSpec("horse_letters", "horse", "HORSE / LETTERS ARE LIVES", "A missed replication adds one letter; E eliminates, unless a mercy is agreed"),
    DiagramSpec("horse_outcomes", "horse", "HORSE / LAST CHANCE, GOOD VIBES", "Setter generosity is encouraged; dinner and costumes remain opt-in"),
    DiagramSpec("one_on_one_scoring", "one-on-one", "1v1 / TWO OUTSIDE, ONE INSIDE", "First to reach or exceed seven; no supplied win-by-two rule"),
    DiagramSpec("one_on_one_possessions", "one-on-one", "1v1 / CHECK, PLAY, RESOLVE", "Agree made-basket possession, clearing and free-throw rebounds before play"),
    DiagramSpec("one_on_one_structures", "one-on-one", "1v1 / MORE PLAYERS, THREE OPTIONS", "Choose one structure before starting; these are not simultaneous rules"),
    DiagramSpec("backboard_airborne", "backboard", "BACKBOARD / REBOUND WITHOUT LANDING", "Backboard contact → catch airborne before ground → release before landing"),
    DiagramSpec("backboard_attempts", "backboard", "BACKBOARD / THREE ATTEMPTS", "Each location uses the same distance progression as Shooting"),
    DiagramSpec("backboard_highjump", "backboard", "BACKBOARD / HIGH JUMP RULES", "The creators both competed in high jump: this is their countback rule"),
    DiagramSpec("three_point_route", "three-point", "3 POINT / FIVE SPOTS, THEN HALF", "Either corner may start the sequence; angles are schematic location labels"),
    DiagramSpec("three_point_assistance", "three-point", "3 POINT / RETURN, DO NOT INTERFERE", "Help is allowed, not required; without help each player self-rebounds"),
    DiagramSpec("three_point_mercy", "three-point", "3 POINT / THE NO-MISS COMEBACK", "Mercy for the otherwise-losing player: remaining shots back-to-back through half court"),
    DiagramSpec("rim_airborne", "rim", "RIM / CONTACT, CATCH, RELEASE", "Rim contact is required; additional backboard contact is allowed"),
    DiagramSpec("rim_attempts", "rim", "RIM / FOUR TRIES + THE BALL CLAUSE", "A setup going in is BALL, not immediately a missed attempt"),
    DiagramSpec("rim_highjump", "rim", "RIM / HIGH JUMP RULES", "Compare actual attempts at the previous successful shot, not invented points"),
    DiagramSpec("bump_queue", "bump", "BUMP / ORDER AND THE FAKEOUT", "Two balls; agree whether RPS chooses the first player or the right to pick"),
    DiagramSpec("bump_chase", "bump", "BUMP / THE CHASE CHANGES ROLES", "First shoots before second; after the opening shot, rebounds may be shot from anywhere"),
    DiagramSpec("bump_tactics", "bump", "BUMP / BALL-TO-BALL ONLY", "Clear court only · never target people · pause for bystanders · reckless contact stops play"),
    DiagramSpec("multiplayer_tiebreak", "multiplayer", "TWO TO SIX / THE HOUSE EXTENSION", "A seven-game multiplayer finish needs an agreed tie process, not a guessed algorithm"),
    DiagramSpec("creator_episode", "creator", "EPISODE / THE NEXT PICK IS THE HOOK", "Proposed 6–10 minute pilot · original footage · permissions and consent first"),
)


def _text(ax: Axes, x: float, y: float, text: str, size: float = 12,
          color: str = INK, ha: str = "center", weight: str = "normal") -> None:
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=color,
            fontweight=weight, linespacing=1.45, zorder=5)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
           color: str = TEAL, curve: float = 0) -> None:
    from matplotlib.patches import FancyArrowPatch

    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16,
                                color=color, linewidth=2,
                                connectionstyle=f"arc3,rad={curve}", zorder=3))


def _box(ax: Axes, x: float, y: float, title: str, body: str,
         width: float = 3.25, height: float = 1.55, color: str = TEAL) -> None:
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                              boxstyle="round,pad=0.08,rounding_size=0.12",
                              facecolor=PALE, edgecolor=color, linewidth=1.4))
    _text(ax, x, y + height * .26, title, 12, color, weight="bold")
    _text(ax, x, y - .20, body, 11)


def _canvas(spec: DiagramSpec) -> tuple[Figure, Axes]:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(12, 7), facecolor=PAPER)
    FigureCanvasAgg(fig)
    ax = fig.add_axes((.035, .04, .93, .92))
    ax.set(xlim=(0, 12), ylim=(0, 7))
    ax.axis("off")
    _text(ax, .1, 6.72, spec.title, 19, ha="left", weight="bold")
    _text(ax, .1, 6.25, spec.subtitle, 11, MUTED, ha="left")
    ax.plot([.1, 11.9], [5.93, 5.93], color=TEAL, linewidth=2)
    _text(ax, .1, .08, "FIRST TO FOUR  /  Original house-rule illustration  /  Schematic, not official court dimensions", 9, MUTED, ha="left")
    return fig, ax


def _flow(ax: Axes, steps: list[tuple[str, str]], note: str) -> None:
    """A reading-order path, not a claim that all branches are mandatory."""
    positions = [(2, 4.9), (6, 4.9), (10, 4.9), (10, 2.75), (6, 2.75), (2, 2.75)]
    for index, ((title, body), (x, y)) in enumerate(zip(steps, positions)):
        _box(ax, x, y, title, body)
        if index:
            px, py = positions[index - 1]
            if y == py:
                sign = 1 if x > px else -1
                _arrow(ax, (px + sign * 1.73, py), (x - sign * 1.73, y))
            else:
                _arrow(ax, (px, py - .88), (x, y + .88))
    _text(ax, 6, 1.0, note, 12)


def _court(ax: Axes, left: float = .8, bottom: float = 1.1,
           width: float = 5, height: float = 4.45) -> None:
    from matplotlib.patches import Arc, Circle, Rectangle

    ax.add_patch(Rectangle((left, bottom), width, height, fill=False, edgecolor=MUTED, linewidth=1.7))
    cx = left + width / 2
    ax.plot([cx - .40, cx + .40], [bottom + .35, bottom + .35], color=INK, linewidth=3)
    ax.add_patch(Circle((cx, bottom + .55), .12, fill=False, edgecolor=ORANGE, linewidth=2))
    ax.add_patch(Rectangle((cx - .8, bottom), 1.6, 1.95, fill=False, edgecolor=MUTED))
    ax.add_patch(Arc((cx, bottom + .55), 4.35, 5.5, theta1=0, theta2=180, color=MUTED, linewidth=1.7))
    ax.plot([left, left + width], [bottom + height - .28] * 2, color=MUTED, linestyle="--")


def _ball(ax: Axes, x: float, y: float, radius: float = .13, color: str = ORANGE) -> None:
    from matplotlib.patches import Circle

    ax.add_patch(Circle((x, y), radius, facecolor=PAPER, edgecolor=color, linewidth=2, zorder=4))
    ax.plot([x - radius, x + radius], [y, y], color=color, linewidth=.8, zorder=4)
    ax.plot([x, x], [y - radius, y + radius], color=color, linewidth=.8, zorder=4)


def _progression(ax: Axes) -> None:
    from matplotlib.patches import Circle, Rectangle

    ax.add_patch(Rectangle((.6, 1.1), 10.8, 3.45, fill=False, edgecolor=MUTED, linewidth=2))
    ax.plot([6, 6], [1.1, 4.55], color=MUTED)
    ax.add_patch(Circle((6, 2.8), .65, fill=False, edgecolor=MUTED))
    ax.plot([.86, .86], [2.4, 3.2], color=INK, linewidth=3)
    _ball(ax, 1.06, 2.8, .10)
    labels = ["Near\nbasket", "Free\nthrow", "3-point\nline", "Near\nlogo edge", "Logo\ncenter", "Half\ncourt", "Far logo\ncenter", "Further\nas agreed"]
    for i, label in enumerate(labels):
        x = 1.35 + i * 1.3
        _text(ax, x, 3.65 if i % 2 == 0 else 1.85, label, 10)
        ax.scatter([x], [2.8], s=225, color=TEAL, zorder=4)
        _text(ax, x, 2.8, str(i + 1), 10, PAPER, weight="bold")
        if i < 7:
            _arrow(ax, (x + .20, 2.8), (x + 1.08, 2.8))
    _text(ax, 6, 5.25, "Agree exact markers on this court before the first attempt.", 13)
    _text(ax, 6, .65, "Numbers indicate sequence, not metres. The source continues with ‘etc.’, not a fixed endpoint.", 11)


def _attempts(ax: Axes, count: int, game: str) -> None:
    _text(ax, 6, 5.22, f"{count} attempts per player at each {game} location", 17, weight="bold")
    for i in range(count):
        x = 6 + (i - (count - 1) / 2) * 1.45
        _ball(ax, x, 4.28, .39)
        _text(ax, x, 4.28, str(i + 1), 14)
    _box(ax, 2.1, 2.5, "MAKE", "Wait for the other player;\nall make → move back.")
    _box(ax, 6, 2.5, "BUDGET USED", "Mercy may be offered;\nreceiver can decline.")
    _box(ax, 9.9, 2.5, "BOTH FAIL", "Agree mutual mercies;\ntypically two, not a cap.")
    _arrow(ax, (4.8, 3.75), (2.1, 3.4))
    _arrow(ax, (6, 3.75), (6, 3.4))
    _arrow(ax, (7.2, 3.75), (9.9, 3.4))
    _text(ax, 6, .95, "No accepted mercies left? HIGH JUMP RULES compares attempts at the previous successful shot.\nUnlimited mercy offers are hospitality, not extra attempts automatically added to the budget.", 11)


def _highjump(ax: Axes) -> None:
    _box(ax, 2, 4.8, "BOTH FAIL", "Agree any mutual amount;\ntwo is typical.")
    _box(ax, 6, 4.8, "HONOR SYSTEM", "Accept a mercy or decline\nif the game feels lost.")
    _box(ax, 10, 4.8, "NO MERCIES LEFT", "HIGH JUMP RULES: previous\nsuccessful shot counts.")
    _arrow(ax, (3.75, 4.8), (4.25, 4.8))
    _arrow(ax, (7.75, 4.8), (8.25, 4.8))
    _text(ax, 3.1, 3.25, "Illustration, not a recorded game", 12, MUTED)
    for y, name, count in [(2.65, "A", 1), (1.95, "B", 3)]:
        _text(ax, 1, y, name, 13, weight="bold")
        for i in range(count):
            _ball(ax, 1.75 + i * .6, y, .19)
        _text(ax, 4.1, y, f"{count} attempt" + ("s" if count > 1 else ""), 12)
    _box(ax, 8.7, 2.5, "FEWER ATTEMPTS WINS", "Example: A wins the countback.\nTied? Compare the shot before,\nback to the first; then SUDDEN DEATH.", width=5, height=1.85)
    _text(ax, 6, .7, "Why HIGH JUMP RULES? Both creators competed in high jump; this is their owner-supplied rule.", 11)


def _letters(ax: Axes) -> None:
    for i, letter in enumerate("HORSE"):
        x = 1.3 + i * 2.35
        _box(ax, x, 4.45, letter, f"Missed replica {i + 1}", width=1.8, height=1.8,
             color=ORANGE if letter == "E" else TEAL)
        if i < 4:
            _arrow(ax, (x + 1, 4.45), (x + 1.35, 4.45))
    _box(ax, 3, 2.1, "MAKE THE REPLICA", "No letter added.\nContinue the agreed rotation.", width=4.8)
    _box(ax, 9, 2.1, "FINAL E", "Generous mercy may be offered.\nOtherwise out; last player wins.", width=4.8)
    _text(ax, 6, .65, "H → HO → HOR → HORS → HORSE. Historical ‘5-x’ strings are not decoded here.", 12)


def _scoring(ax: Axes) -> None:
    _court(ax)
    _text(ax, 3.3, 2.8, "1 POINT", 14, TEAL, weight="bold")
    _text(ax, 3.3, 4.8, "2 POINTS", 14, ORANGE, weight="bold")
    _box(ax, 9, 4.7, "REACH OR EXCEED 7", "A two-point shot can finish at 8.\nWin by two is not specified.", width=5)
    _box(ax, 9, 2.6, "START WITH A CHECK", "Respectful pass back and forth.\nSudden-death shootout\ndetermines the starter.", width=5, height=1.9)
    _text(ax, 6, .55, "More players may agree a higher target. Agree line calls and possession details before play.", 11)


def _structures(ax: Axes) -> None:
    _box(ax, 2, 4.5, "ALTERNATE", "Predetermine an EVEN\nnumber of possessions.", height=1.9)
    _box(ax, 6, 4.5, "KING OF THE HILL", "A new player enters after\npossession changes.", height=1.9)
    _box(ax, 10, 4.5, "FOUR-PLAYER BRACKET", "Two opening pairings;\nagree advancement details.", height=1.9)
    for x, names in [(2, ("A", "B", "A", "B")), (6, ("A/B", "C in", "Next"))]:
        for i, name in enumerate(names):
            px = x - 1.2 + i * (2.4 / (len(names) - 1))
            _text(ax, px, 2.75, name, 11, TEAL, weight="bold")
            if i:
                _arrow(ax, (px - .55, 2.3), (px - .1, 2.3))
    _text(ax, 9.2, 2.9, "A vs B", 11)
    _text(ax, 9.2, 2.0, "C vs D", 11)
    _arrow(ax, (9.9, 2.9), (10.6, 2.5))
    _arrow(ax, (9.9, 2.0), (10.6, 2.5))
    _text(ax, 11, 2.5, "Final", 11)
    _text(ax, 6, .95, "These are the supplied options for extra players, not an invented universal rotation.\nChoose the target, pairings, substitutions and tie handling before starting.", 12)


def _airborne(ax: Axes, rim: bool) -> None:
    ax.plot([.6, 11.4], [1.9, 1.9], color=MUTED, linewidth=2)
    _text(ax, 1.6, 1.55, "Ground", 11, MUTED)
    ax.plot([3, 3], [3.3, 5.3], color=INK, linewidth=5)
    ax.plot([3, 3.75], [3.8, 3.8], color=ORANGE, linewidth=4)
    _text(ax, 2.05, 5.3, "Backboard", 11)
    _text(ax, 4.1, 3.5, "Rim", 11, ORANGE)
    contact = (3.65, 3.85) if rim else (3.05, 4.75)
    _ball(ax, 1.5, 3, .17)
    _arrow(ax, (1.7, 3.1), contact, curve=-.18)
    _ball(ax, *contact, .15)
    _arrow(ax, (contact[0] + .2, contact[1]), (6.1, 3.35), curve=-.18)
    _ball(ax, 6.35, 3.25, .18)
    _text(ax, 6.35, 2.6, "CATCH\nairborne", 12, TEAL, weight="bold")
    _arrow(ax, (6.6, 3.4), (8.8, 4.45), curve=-.18)
    _ball(ax, 9, 4.5, .18)
    _text(ax, 9.8, 3.5, "RELEASE\nbefore landing", 12, TEAL, weight="bold")
    _text(ax, 7.75, 5.3, "Time sequence left → right\n(not the physical flight of the final shot)", 11, MUTED)
    _text(ax, 6, .9, ("Required setup: RIM touch; backboard may also be touched.\nSetup goes in? Apply BALL accounting, not a normal immediate miss." if rim else
                       "Required setup: BACKBOARD touch. Catch before the ball reaches the ground.\nSimulates being covered immediately after a rebound; no defender contact is needed."), 12)


def _route(ax: Axes) -> None:
    from matplotlib.patches import Arc

    center = (3.4, 1.75)
    ax.add_patch(Arc(center, 4.8, 4.8, theta1=0, theta2=180, edgecolor=MUTED, linewidth=2))
    ax.plot([.7, 6.1], [1.3, 1.3], color=MUTED)
    _ball(ax, *center, .13)
    for i, degrees in enumerate((0, 45, 90, 135, 180)):
        angle = math.radians(degrees)
        x, y = center[0] + 2.4 * math.cos(angle), center[1] + 2.4 * math.sin(angle)
        ax.scatter([x], [y], s=270, color=TEAL, zorder=4)
        _text(ax, x, y, str(i + 1), 11, PAPER, weight="bold")
        _text(ax, x, y + .45, f"{degrees}°", 11)
        if i < 4:
            next_angle = math.radians(degrees + 45)
            end = (center[0] + 2.4 * math.cos(next_angle), center[1] + 2.4 * math.sin(next_angle))
            _arrow(ax, (x - .12, y + .05), (end[0] + .13, end[1] - .12), curve=-.16)
    _box(ax, 9.1, 4.8, "1 → 2 → 3 → 4 → 5", "Corner · wing · top\nwing · opposite corner", width=4.9)
    _box(ax, 9.1, 2.5, "6 / HALF COURT", "After the five three-point makes.\nFirst finisher is an interpretation;\nconfirm simultaneous finishes.", width=4.9, height=1.9)
    _arrow(ax, (5.8, 4.5), (6.5, 4.8))
    _arrow(ax, (9.1, 3.9), (9.1, 3.55))
    _text(ax, 6, .55, "Reverse the sequence to start at the other corner. Distances and arc are schematic.", 11)


def _assistance(ax: Axes) -> None:
    _court(ax, left=.75, width=4.5)
    _ball(ax, 2.9, 3.6, .18)
    _text(ax, 2.9, 4.12, "Shooter", 11)
    _text(ax, 4.35, 2.15, "Helper", 11, TEAL)
    _arrow(ax, (4.25, 2.5), (3.1, 3.35))
    _text(ax, 1.65, 2.2, "Return\nonly", 11, TEAL)
    _box(ax, 8.7, 4.75, "OPTIONAL ASSISTANCE", "Return rebounds safely.\nDo not interfere with a shot.", width=5.4)
    _box(ax, 8.7, 2.55, "NO HELPER?", "Self-rebound. Log assistance\nif comparing completion times.\nHelp is never mandatory.", width=5.4, height=1.9)
    _text(ax, 6, .55, "This positioning is illustrative: keep the return lane and all bystanders clear.", 11)


def _rim_attempts(ax: Axes) -> None:
    _text(ax, 2.7, 5.2, "Ordinary budget: FOUR", 15, weight="bold")
    for i in range(4):
        _ball(ax, 1.15 + i, 4.4, .32)
        _text(ax, 1.15 + i, 4.4, str(i + 1), 12)
    _box(ax, 8.75, 4.55, "SETUP GOES IN = BALL", "One BALL does not cost a miss.\nThree consecutive BALLs = one miss.", width=5.3, height=1.8)
    for i in range(3):
        _box(ax, 1.65 + i * 3, 2.25, f"BALL {i + 1}", "No miss yet" if i < 2 else "Count ONE miss", width=2.25, height=1.4)
        if i < 2:
            _arrow(ax, (2.92 + i * 3, 2.25), (3.38 + i * 3, 2.25))
    _text(ax, 10.5, 2.25, "WE DON'T\nHAVE ALL DAY\nGET WORSE\nSKILL ISSUE", 11, ORANGE, weight="bold")
    _text(ax, 6, .65, "Agree BALL streak reset handling before play; the supplied rule does not fully specify it.", 11)


def _chase(ax: Axes) -> None:
    _court(ax, left=.7, width=4.6)
    _ball(ax, 2.4, 4.8, .17)
    _ball(ax, 3.8, 4.8, .17, TEAL)
    _text(ax, 1.7, 5.3, "FIRST", 11, ORANGE)
    _text(ax, 4.3, 5.3, "SECOND", 11, TEAL)
    _arrow(ax, (2.4, 4.5), (2.9, 1.95), ORANGE, curve=.2)
    _arrow(ax, (3.8, 4.5), (3.1, 1.95), TEAL, curve=-.2)
    _box(ax, 8.6, 4.8, "SECOND MAKES FIRST", "First player is eliminated.\nStop targeting their ball/person.", width=5.5)
    _box(ax, 8.6, 2.6, "FIRST MAKES FIRST", "Pass to the next queued player,\nwho becomes second. With two\nremaining, swap roles.", width=5.5, height=1.95)
    _text(ax, 6, .55, "Rebounds: shoot from anywhere. Single-knockout explanation ≠ a definition of logged ‘5-x’ scores.", 11)


def _tactics(ax: Axes) -> None:
    scenarios = [(3, 4.6, "HELD BALL → BALL", "Use your ball, not hands/body."),
                 (9, 4.6, "FLIGHT INTERCEPTION", "Owen is annoyingly good: owner joke."),
                 (3, 2.35, "UP THROUGH THE NET", "Ball rejection only; beware fakeouts."),
                 (9, 2.35, "REDIRECT A LOOSE REBOUND", "Only with a completely clear path.")]
    for x, y, title, body in scenarios:
        _text(ax, x, y + .8, title, 12, TEAL, weight="bold")
        if "NET" in title:
            ax.plot([x - .45, x + .45], [y + .10] * 2, color=MUTED, linewidth=2)
            for offset in (-.4, -.2, .2, .4):
                ax.plot([x + offset, x + offset * .65], [y + .10, y - .16], color=MUTED, linewidth=.8)
            _ball(ax, x, y - .43, .13, TEAL)
            _ball(ax, x, y + .43, .13, ORANGE)
            _arrow(ax, (x, y - .25), (x, y + .25))
            _text(ax, x + 1.35, y, "Upward\nball path", 10, MUTED)
        elif "FLIGHT" in title:
            _ball(ax, x - 1.2, y - .3, .17, TEAL)
            _ball(ax, x + .65, y + .23, .17, ORANGE)
            _arrow(ax, (x - .95, y - .3), (x + .4, y + .18), curve=-.17)
            _arrow(ax, (x + 1.75, y + .48), (x + .9, y + .27), ORANGE)
        elif "REBOUND" in title:
            ax.plot([x - 1.7, x + 1.7], [y - .42] * 2, color=MUTED, linestyle="--", linewidth=1)
            _ball(ax, x, y - .22, .15, ORANGE)
            _ball(ax, x + 1.15, y - .12, .15, TEAL)
            _arrow(ax, (x - 1.4, y + .33), (x - .22, y - .18), ORANGE)
            _arrow(ax, (x + .95, y - .12), (x + .22, y - .22))
            _arrow(ax, (x - .04, y + .01), (x - .35, y + .52), ORANGE)
        else:
            _ball(ax, x - .85, y, .19, TEAL)
            _ball(ax, x + .75, y, .19, ORANGE)
            _arrow(ax, (x - .58, y), (x + .48, y))
        _text(ax, x, y - .67, body, 10.5)
    _text(ax, 6, .62, "NO human targets, including resting/eliminated/on-phone people. Stop and give first aid for contact.\nNo credit cards, passwords or financial access. If safe separation is impossible, skip the tactic.", 11, ORANGE)


def _draw(spec: DiagramSpec, ax: Axes) -> None:
    slug = spec.slug
    if slug.endswith("_highjump"):
        _highjump(ax)
    elif slug == "shooting_progression":
        _progression(ax)
    elif slug in ("shooting_attempts", "backboard_attempts"):
        _attempts(ax, 5 if spec.game == "shooting" else 3, spec.game.title())
    elif slug == "horse_letters":
        _letters(ax)
    elif slug == "one_on_one_scoring":
        _scoring(ax)
    elif slug == "one_on_one_structures":
        _structures(ax)
    elif slug.endswith("_airborne"):
        _airborne(ax, spec.game == "rim")
    elif slug == "three_point_route":
        _route(ax)
    elif slug == "three_point_assistance":
        _assistance(ax)
    elif slug == "rim_attempts":
        _rim_attempts(ax)
    elif slug == "bump_chase":
        _chase(ax)
    elif slug == "bump_tactics":
        _tactics(ax)
    else:
        steps, note = _FLOWS[slug]
        _flow(ax, steps, note)


_FLOWS = {
    "format_overview": ([
        ("AGREE BEFORE PLAY", "Safety · first picker · repeats\nmarkers · unresolved ties"),
        ("PLAY A CHALLENGE", "Shooting / HORSE / 1v1\nBackboard / 3 Point / Rim / Bump"),
        ("RECORD ONE WIN", "L = Liam; O = Owen\nRecord winners in play order."),
        ("FOUR WINS?", "Yes → series ends.\nNo → winner chooses next."),
        ("NEXT PICK", "Previous winner chooses;\nactual choices need logging."),
        ("REPEAT UNTIL CLINCH", "At most seven in two-player play.\nDo not add post-clinch games.")],
        "Observed Shooting openings do not prove a fixed first game. Repeats are unspecified.\nThe next pick is a story hook, not evidence that choosing causes an advantage."),
    "horse_cycle": ([
        ("0 / FIND THE ORDER", "Sudden-death shot-for-shot\nat an agreed distance."),
        ("1 / ANNOUNCE A SET", "Doable trick / distance /\nrebounded jumper; keep it safe."),
        ("2 / SETTER MISSES?", "Next player sets; repeat\nuntil somebody makes."),
        ("3 / SETTER MAKES", "Others replicate the announced\nparameters within reason."),
        ("4 / REPLICA MISSES", "Add a letter of HORSE.\nNo WEASILY WESLEY loopholes."),
        ("5 / E ELIMINATES", "Last player standing wins.\nFinal-E mercy may be offered.")],
        "RUIN THE VIBE shots: no impossible-for-that-player dunks, bystander involvement or illegal acts.\nPost-replication setter rotation is not fully specified; agree it before play."),
    "horse_outcomes": ([
        ("FINAL E AT STAKE", "Setter may generously offer\na mercy attempt."),
        ("ACCEPT OR DECLINE", "No pressure to extend play;\nrespect personal boundaries."),
        ("IF OUT", "Leave the active play area.\nLast remaining player wins."),
        ("HORSE DINNER JOKE", "Most mercies: dinner for others,\nwin or lose; voluntary only."),
        ("BAD VIBES BETTY", "Tiara · purple lipstick · miniskirt\nONLY a mutually agreed opt-in."),
        ("NO COERCION", "Declining is not a penalty.\nNo forced humiliation.")],
        "Shooting has a different dinner convention: usually dinner for loser(s).\nDo not collapse these jokes into a single enforceable obligation."),
    "one_on_one_possessions": ([
        ("START / CHECK", "Sudden-death shootout, then\nrespectful pass back and forth."),
        ("OFFENSIVE FOUL", "Possession changes. Egregious /\nrepeated lesser foul: 1-point FT."),
        ("MAJOR DEFENSIVE", "Free throw. Agree shooter\nand rebound handling first."),
        ("MINOR DEFENSIVE", "IM NOT A BIG OL BABY:\nmay waive a minor call."),
        ("REPEATED MINOR", "Or an extra possession\nafter the turnover."),
        ("PLAY RESTART", "Apply agreed check/clear rules.\nReckless contact stops play.")],
        "These panels classify calls; they do not require fouls in this order.\nYOUR MOM / skill / dating jokes: consensual only; no hate, threats or encouragement of fouls."),
    "three_point_mercy": ([
        ("OTHER PLAYER FINISHES", "First-finisher reading is\noperational; confirm ties."),
        ("MERCY OFFERED", "Otherwise-losing player\nmay attempt the comeback."),
        ("REMAINING SPOTS", "Make each next required shot\nback-to-back, without a miss."),
        ("THROUGH HALF COURT", "The no-miss chain includes\nthe half-court make."),
        ("ALL MADE?", "Yes: ‘reset where previously\nended’; state needs agreement."),
        ("A MISS?", "The no-miss chain fails;\nno automatic reset earned.")],
        "Last two panels are alternative outcomes. Decide the exact reset state BEFORE play.\nOptional timing does not establish fewer shots; assistance and attempts were not standardized."),
    "bump_queue": ([
        ("0 / ROCK-PAPER-SCISSORS", "Winner goes first OR picks first?\nAgree which before starting."),
        ("1 / SET THE LOCATION", "Base it on least-skilled player;\nSKILL ISSUE adjustment by agreement."),
        ("2 / FIRST SHOOTS FIRST", "Obviously. Second waits\nfor the real first release."),
        ("3 / FAKEOUT?", "Second shoots too early:\nretrieve and return to start."),
        ("SILLY BOY", "YOU SHOULDVE BEEN\nPAYING ATTENTION: time lost."),
        ("RETURN TO THE CHASE", "Maintain the active queue;\nno penalties involving people.")],
        "Going first is a disadvantage ‘unless Liam’ is an owner joke, not measured evidence.\nAgree the queue after elimination and ties; do not infer a first-to-five format from ‘5-x’."),
    "multiplayer_tiebreak": ([
        ("2 PLAYERS", "Normal first to four;\na maximum of seven games."),
        ("3–6 PLAYERS", "House extension: most wins\nafter seven if no earlier four."),
        ("EXAMPLE: 3–3–1", "Two leaders tied; third player\nwon one of the seven games."),
        ("LOSING-PLAYER GAMES", "House rule uses games won\nby losing players to break ties."),
        ("MECHANISM UNSPECIFIED", "Agree game selection, eligible\nplayers and repeated ties first."),
        ("LARGER GROUP", "Use brackets with two or three\nper round; max six in a group.")],
        "The 3–3–1 split is an illustration, not a logged series.\nNo unique outcome or complete multiplayer algorithm is claimed."),
    "creator_episode": ([
        ("0:00–0:30 / STAKES", "Scoreboard cold open.\nFour wins ends the series."),
        ("0:30–1:30 / CONTRACT", "Show winner choice, safety\nand one quick rule demonstration."),
        ("1:30–4:00 / EARLY PLAY", "Readable attempts and scores.\nAfter each win: what next?"),
        ("4:00–6:00 / PRESSURE", "If the series stays alive, show\na reversal or mercy decision."),
        ("6:00–9:00 / FINISH", "Show the actual clinch.\nNever manufacture a game seven."),
        ("9:00–10:00 / OPTIONAL", "Debrief, aggregate CSV and\nnext-session invitation.")],
        "Flexible editing windows, not a promise of ten minutes or seven games.\nJesser pilot / Ludwig or Atrioc adaptations: aspirations, no affiliation or endorsement."),
}


def build_sports_diagrams(root: Path | str) -> list[Path]:
    """Render 24 figures (48 assets); return absolute paths in manifest order.

    Uses bundled DejaVu Sans, fixed SVG IDs and no timestamps/randomness.
    Does not read raw records, create CSV/ZIP/PDF, access a network or publish.
    """
    import matplotlib as mpl

    output = Path(root).resolve() / "tex_images" / "sports"
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    with mpl.rc_context({"font.family": "DejaVu Sans", "font.size": 12,
                         "svg.fonttype": "none", "svg.hashsalt": "first-to-four-sports-v1",
                         "text.usetex": False, "path.simplify": False}):
        for spec in DIAGRAMS:
            fig, ax = _canvas(spec)
            try:
                _draw(spec, ax)
                for suffix in ("png", "svg"):
                    path = output / f"{spec.slug}.{suffix}"
                    metadata = ({"Software": "First to Four original diagrams"} if suffix == "png"
                                else {"Date": None, "Creator": "First to Four original diagrams",
                                      "Title": spec.title, "Description": spec.subtitle})
                    fig.savefig(path, format=suffix, dpi=160, facecolor=PAPER, metadata=metadata)
                    paths.append(path)
            finally:
                fig.clear()
    return paths


def main() -> None:
    paths = build_sports_diagrams(Path(__file__).resolve().parents[1])
    print(f"Built {len(DIAGRAMS)} original sports figures ({len(paths)} PNG/SVG assets).")


if __name__ == "__main__":
    main()