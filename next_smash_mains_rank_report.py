# next_smash_mains_rank_report.py
# Tournament-wide rank analytics: average rank and related trajectory statistics.

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import statistics
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

from next_smash_mains_profiles import (
    CharacterProfile,
    LABEL_TO_ROUND,
    ROUND_DISPLAY,
    build_profiles,
)

GOOD = "#2ca02c"
BAD = "#d62728"
WARNING = "#bcbd22"
NEUTRAL = "#4e79a7"
ACCENT = "#f28e2b"

# Characters ranked at or above this are still in the active Round 7 field.
ACTIVE_CUTOFF = 40


def _ordered_labels(profiles: dict[str, CharacterProfile]) -> list[str]:
    labels = {label for p in profiles.values() for label in p.ranks_by_round}
    return sorted(labels, key=lambda l: LABEL_TO_ROUND.get(l, 99))


def _display(label: str) -> str:
    return ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 99), label)


def _barh_page(pdf: PdfPages, rows: list[tuple[str, float]], title: str, xlabel: str,
               color, value_fmt: str = "{:.2f}", note: str | None = None) -> None:
    if not rows:
        return
    names = [r[0] for r in rows][::-1]
    values = [r[1] for r in rows][::-1]
    colors = [color(v) for v in values] if callable(color) else color

    fig, ax = plt.subplots(figsize=(12, max(6, 0.32 * len(names) + 2)))
    bars = ax.barh(names, values, color=colors, edgecolor="black", linewidth=0.4)
    span = (max(values) - min(min(values), 0)) or 1
    for bar, value in zip(bars, values):
        offset = span * 0.01
        ax.text(bar.get_width() + (offset if value >= 0 else -offset),
                bar.get_y() + bar.get_height() / 2,
                value_fmt.format(value),
                va="center", ha="left" if value >= 0 else "right", fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=13)
    ax.margins(x=0.12)
    ax.grid(axis="x", alpha=0.25)
    if note:
        ax.annotate(note, xy=(0.5, -0.06), xycoords="axes fraction",
                    ha="center", va="top", fontsize=8, style="italic")
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_average_rank(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    rows = sorted(
        ((p.name, p.average_rank) for p in profiles.values() if p.ranks_by_round),
        key=lambda r: r[1],
    )[:30]
    _barh_page(
        pdf, rows,
        "Average Rank Across All Rounds (lower is better) — Top 30",
        "Average rank",
        color=NEUTRAL,
        note="Averaged over the rounds each character actually competed in.",
    )


def _page_rank_vs_average(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    """Current rank minus average rank: who is peaking vs who is fading."""
    entries = [
        (p.name, p.average_rank - p.current_rank, p.average_rank, p.current_rank)
        for p in profiles.values()
        if p.ranks_by_round and p.current_rank
    ]
    entries.sort(key=lambda e: e[1], reverse=True)
    top = entries[:15]
    bottom = entries[-15:]

    fig, axes = plt.subplots(1, 2, figsize=(15, 9))
    for ax, data, title, color in (
        (axes[0], top, "Peaking Now\n(current rank far better than career average)", GOOD),
        (axes[1], bottom[::-1], "Fading\n(current rank far worse than career average)", BAD),
    ):
        names = [f"{d[0]}  ({d[2]:.1f} → {d[3]})" for d in data][::-1]
        values = [abs(d[1]) for d in data][::-1]
        ax.barh(names, values, color=color, edgecolor="black", linewidth=0.4)
        for i, v in enumerate(values):
            ax.text(v + max(values) * 0.01, i, f"{v:.1f}", va="center", fontsize=8)
        ax.set_xlabel("Rank places moved vs average")
        ax.set_title(title, fontsize=11)
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle("Career Average vs Current Standing", fontsize=14)
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_volatility(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    entries = [
        (p.name, statistics.pstdev(list(p.ranks_by_round.values())))
        for p in profiles.values()
        if len(p.ranks_by_round) >= 3
    ]
    entries.sort(key=lambda e: e[1], reverse=True)
    _barh_page(
        pdf, entries[:20],
        "Most Volatile Careers — Standard Deviation of Rank",
        "Rank standard deviation",
        color=ACCENT,
        note="High values mean the character swung wildly between rounds. Minimum 3 rounds played.",
    )
    _barh_page(
        pdf, entries[-20:][::-1],
        "Most Consistent Careers — Standard Deviation of Rank",
        "Rank standard deviation",
        color=NEUTRAL,
        note="Low values mean the character held a steady position all tournament.",
    )


def _page_trajectories(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    labels = _ordered_labels(profiles)
    leaders = sorted(
        (p for p in profiles.values() if p.current_rank),
        key=lambda p: p.current_rank,
    )[:10]

    fig, ax = plt.subplots(figsize=(13, 8))
    for profile in leaders:
        xs, ys = [], []
        for idx, label in enumerate(labels):
            if label in profile.ranks_by_round:
                xs.append(idx)
                ys.append(profile.ranks_by_round[label])
        if xs:
            ax.plot(xs, ys, marker="o", linewidth=1.8, markersize=4, label=profile.name)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([_display(l) for l in labels], rotation=45, ha="right")
    ax.invert_yaxis()
    ax.set_ylabel("Rank")
    ax.set_title("Rank Trajectory of the Current Top 10", fontsize=13)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2, loc="lower left")
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_peak_and_floor(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    active = sorted(
        (p for p in profiles.values() if p.current_rank and p.current_rank <= ACTIVE_CUTOFF and p.ranks_by_round),
        key=lambda p: p.current_rank,
    )
    if not active:
        return

    fig, ax = plt.subplots(figsize=(13, max(7, 0.3 * len(active) + 2)))
    for i, profile in enumerate(active):
        ranks = list(profile.ranks_by_round.values())
        best, worst = min(ranks), max(ranks)
        ax.plot([best, worst], [i, i], color="#bbbbbb", linewidth=2, zorder=1)
        ax.scatter([best], [i], color=GOOD, s=28, zorder=3)
        ax.scatter([worst], [i], color=BAD, s=28, zorder=3)
        ax.scatter([profile.current_rank], [i], color="black", marker="|", s=90, zorder=4)

    ax.set_yticks(range(len(active)))
    ax.set_yticklabels([p.name for p in active], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Rank")
    ax.set_title(
        "Round 7 Field: Career Best (green), Career Worst (red), Current (black tick)",
        fontsize=13,
    )
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _page_elimination_survival(pdf: PdfPages, profiles: dict[str, CharacterProfile],
                               elimination_counts: dict[str, int]) -> None:
    xs, ys, names = [], [], []
    for profile in profiles.values():
        if not profile.current_rank:
            continue
        xs.append(elimination_counts.get(profile.name, 0))
        ys.append(profile.current_rank)
        names.append(profile.name)

    fig, ax = plt.subplots(figsize=(13, 8))
    colors = [GOOD if y <= ACTIVE_CUTOFF else "#999999" for y in ys]
    ax.scatter(xs, ys, c=colors, s=45, edgecolor="black", linewidth=0.4, zorder=3)
    for x, y, name in zip(xs, ys, names):
        if x >= 3 or y <= 12:
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 0), fontsize=7)

    ax.axhline(ACTIVE_CUTOFF + 0.5, color=BAD, linestyle="--", linewidth=1)
    ax.invert_yaxis()
    ax.set_xlabel("Elimination rounds appeared in")
    ax.set_ylabel("Current rank")
    ax.set_title("Elimination Appearances vs Current Standing", fontsize=13)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _elimination_status_page(
    pdf: PdfPages,
    profiles: dict[str, CharacterProfile],
    label: str,
    cumulative_counts: dict[str, int],
    elimination_participants: set[str],
    rank_bands: list[tuple[int, str]] | None,
) -> None:
    round_number = LABEL_TO_ROUND.get(label, 99)
    ranked_characters: list[tuple[int, str]] = []
    for profile in profiles.values():
        prior_ranks = [
            (LABEL_TO_ROUND.get(round_label, 99), rank)
            for round_label, rank in profile.ranks_by_round.items()
            if LABEL_TO_ROUND.get(round_label, 99) <= round_number
        ]
        if prior_ranks:
            ranked_characters.append((max(prior_ranks)[1], profile.name))
    ranked_characters.sort()

    count_groups: dict[int, list[tuple[str, str]]] = {}
    for rank, character in ranked_characters:
        if rank_bands:
            arrow_color = "#000000"
            for max_rank, color in rank_bands:
                if rank <= max_rank:
                    arrow_color = color
                    break
            if arrow_color == WARNING:
                status = "Currently in Elimination"
            elif arrow_color in {BAD, "#000000"}:
                status = "Eliminated"
            else:
                status = "Not in Elimination"
        elif character in elimination_participants:
            status = "Currently in Elimination"
        else:
            status = "Not in Elimination"
        status_color = {
            "Not in Elimination": GOOD,
            "Currently in Elimination": WARNING,
            "Eliminated": BAD,
        }[status]
        count = cumulative_counts.get(character, 0)
        count_groups.setdefault(count, []).append((character, status_color))

    row_lines: list[tuple[int, list[tuple[str, str]]]] = []
    for count, characters in sorted(count_groups.items()):
        for index in range(0, len(characters), 4):
            row_lines.append((count, characters[index:index + 4]))

    row_height = 0.042
    fig_height = max(8, 2.4 + len(row_lines) * 0.62)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    left, right = 0.015, 0.985
    count_column = 0.17
    top = 0.92
    bottom = 0.07
    available_height = top - bottom
    line_height = available_height / (len(row_lines) + 1)

    ax.add_patch(plt.Rectangle((left, top - line_height), right - left, line_height, fill=False, linewidth=1.2))
    ax.plot([count_column, count_column], [bottom, top], color="black", linewidth=1.2)
    ax.text((left + count_column) / 2, top - line_height / 2, "Elimination Count", ha="center", va="center", weight="bold")
    ax.text((count_column + right) / 2, top - line_height / 2, "Characters", ha="center", va="center", weight="bold")

    previous_count: int | None = None
    for line_index, (count, characters) in enumerate(row_lines, start=1):
        y_top = top - line_height * line_index
        y_bottom = y_top - line_height
        ax.add_patch(plt.Rectangle((left, y_bottom), right - left, line_height, fill=False, linewidth=0.8))
        if count != previous_count:
            count_label = f"{count} Elimination" if count == 1 else f"{count} Eliminations"
            ax.text((left + count_column) / 2, y_bottom + line_height / 2, count_label, ha="center", va="center")
        previous_count = count

        slot_width = (right - count_column) / 4
        for slot, (character, color) in enumerate(characters):
            x = count_column + slot_width * (slot + 0.5)
            ax.text(x, y_bottom + line_height / 2, character, color=color, ha="center", va="center", fontsize=9)

    status_colors = {
        "Not in Elimination": GOOD,
        "Currently in Elimination": WARNING,
        "Eliminated": BAD,
    }
    ax.set_title(f"{_display(label)}: Elimination History", fontsize=14)
    legend_x = [0.31, 0.5, 0.69]
    for x, (status, color) in zip(legend_x, status_colors.items()):
        ax.text(x, 0.025, status, color=color, ha="center", fontsize=9, weight="bold")
    plt.tight_layout(rect=[0.01, 0.02, 0.99, 0.96])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def generate_elimination_history_report(
    profiles: dict[str, CharacterProfile],
    output_dir: Path,
    elimination_round_participants: dict[str, set[str]],
    status_bands_by_round: dict[str, list[tuple[int, str]]],
    filename: str = "elimination_history_by_round.pdf",
) -> Path:
    output_path = output_dir / filename
    cumulative_counts: dict[str, int] = {character: 0 for character in profiles}
    with PdfPages(output_path) as pdf:
        for label in _ordered_labels(profiles):
            participants = elimination_round_participants.get(label, set())
            for character in participants:
                cumulative_counts[character] = cumulative_counts.get(character, 0) + 1
            _elimination_status_page(
                pdf,
                profiles,
                label,
                cumulative_counts,
                participants,
                status_bands_by_round.get(label),
            )
    print(f"Elimination history report saved: {output_path}")
    return output_path


def _page_overperformance(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    entries = [
        (p.name, p.avg_overperformance)
        for p in profiles.values()
        if len(p.matches) >= 6
    ]
    entries.sort(key=lambda e: e[1], reverse=True)
    rows = entries[:15] + entries[-15:]
    _barh_page(
        pdf, rows,
        "Matchup Chart: Biggest Over- and Under-Performers",
        "Average stock diff above / below matchup prediction",
        color=lambda v: GOOD if v >= 0 else BAD,
        note="Minimum 6 matches played. Positive means the character beat what the matchup chart expected.",
    )


def _page_rescoring_losses(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    entries = [
        (p.name, sum(p.lost_score_per_rescoring.values()))
        for p in profiles.values()
        if p.lost_score_per_rescoring
    ]
    entries.sort(key=lambda e: e[1], reverse=True)
    _barh_page(
        pdf, entries[:25],
        "Most Score Removed by Inter-Round Reductions",
        "Total score removed",
        color=BAD,
        note="Cumulative points stripped by every score-reduction step the character passed through.",
    )


def _page_efficiency(pdf: PdfPages, profiles: dict[str, CharacterProfile]) -> None:
    data = [p for p in profiles.values() if len(p.matches) >= 6 and p.current_rank]
    if not data:
        return

    xs = [p.win_rate * 100 for p in data]
    ys = [p.avg_points_per_match for p in data]
    colors = [GOOD if p.current_rank <= ACTIVE_CUTOFF else "#999999" for p in data]

    fig, ax = plt.subplots(figsize=(13, 8))
    ax.scatter(xs, ys, c=colors, s=45, edgecolor="black", linewidth=0.4, zorder=3)
    ranked = sorted(range(len(data)), key=lambda i: ys[i], reverse=True)[:12]
    for i in ranked:
        ax.annotate(data[i].name, (xs[i], ys[i]), textcoords="offset points",
                    xytext=(6, 0), fontsize=7)
    ax.set_xlabel("Win rate (%)")
    ax.set_ylabel("Average score per match")
    ax.set_title("Win Rate vs Scoring Output (green = still in the Round 7 field)", fontsize=13)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def generate_rank_report(
    records_dir: Path,
    output_dir: Path,
    matchup_df: pd.DataFrame,
    elimination_counts: dict[str, int] | None = None,
    elimination_round_participants: dict[str, set[str]] | None = None,
    status_bands_by_round: dict[str, list[tuple[int, str]]] | None = None,
    filename: str = "average_rank_report.pdf",
) -> Path:
    """Build the multi-page rank analytics PDF."""
    profiles = build_profiles(records_dir=records_dir, matchup_df=matchup_df)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    with PdfPages(output_path) as pdf:
        _page_average_rank(pdf, profiles)
        _page_rank_vs_average(pdf, profiles)
        _page_volatility(pdf, profiles)
        _page_trajectories(pdf, profiles)
        _page_peak_and_floor(pdf, profiles)
        if elimination_counts:
            _page_elimination_survival(pdf, profiles, elimination_counts)
        _page_overperformance(pdf, profiles)
        _page_rescoring_losses(pdf, profiles)
        _page_efficiency(pdf, profiles)

    if elimination_round_participants is not None and status_bands_by_round is not None:
        generate_elimination_history_report(
            profiles,
            output_dir,
            elimination_round_participants,
            status_bands_by_round,
        )

    print(f"Rank analytics report saved: {output_path}")
    return output_path
