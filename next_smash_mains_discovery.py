# New_Smash_Gods__Discovery_Training (Object-Oriented Rewrite)

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from typing import Callable

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
REPORTS_ROOT_DIR = ROOT / "reports"
RECORDS_ROOT_DIR = ROOT / "records"

RANKING_CHANGES_DIR = REPORTS_ROOT_DIR / "next_smash_mains_ranking_changes"
REPORTS_DIR = REPORTS_ROOT_DIR / "next_smash_mains_reports"
RECORDS_DIR = RECORDS_ROOT_DIR / "next_smash_mains_records"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RANKING_CHANGES_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR.mkdir(parents=True, exist_ok=True)

# Maps internal sequential round number → semantic filename prefix and display name.
# Pattern: Round 1, Round 2, Elimination 1, Round 3, Elimination 2, Round 4, ...
ROUND_LABEL: dict[int, str] = {
    1: "round_1",
    2: "round_2",
    3: "elimination_1",
    4: "round_3",
    5: "elimination_2",
    6: "round_4",
}
ROUND_DISPLAY: dict[int, str] = {
    1: "Round 1",
    2: "Round 2",
    3: "Elimination 1",
    4: "Round 3",
    5: "Elimination 2",
    6: "Round 4",
}
LABEL_TO_ROUND: dict[str, int] = {v: k for k, v in ROUND_LABEL.items()}

MATCHUP_PATH = ROOT / "matchup_chart.csv"
MATCHUP_DF = pd.read_csv(MATCHUP_PATH) if MATCHUP_PATH.exists() else pd.DataFrame()
ANALYSIS_SCRIPT_PATH = ROOT / "next_smash_mains_analysis.py"


def regenerate_analysis_outputs() -> None:
    if not ANALYSIS_SCRIPT_PATH.exists():
        print(f"Analysis script not found; skipped regeneration: {ANALYSIS_SCRIPT_PATH}")
        return
    try:
        subprocess.run([sys.executable, str(ANALYSIS_SCRIPT_PATH)], check=True)
        print("Analysis outputs regenerated.")
    except subprocess.CalledProcessError as exc:
        print(f"Analysis regeneration failed with exit code {exc.returncode}.")

def apply_score_reduction(scores: dict[str, float]) -> dict[str, float]:
    """Reduce all scores to score^(2/3), applied entering/exiting elimination rounds."""
    return {char: round(score ** (2 / 3), 3) for char, score in scores.items()}

def apply_selective_score_reduction(scores: dict[str, float], target_characters: set[str], exponent: float) -> dict[str, float]:
    """Reduce only selected character scores to score^exponent."""
    return {
        char: round(score ** exponent, 3) if char in target_characters else score
        for char, score in scores.items()
    }

def placeholder_only_characters(matches_by_character: dict[str, list[MatchResult]]) -> list[str]:
    return [
        character
        for character, matches in matches_by_character.items()
        if matches and all(match.opponent == "Link" and match.stock_diff == 0 and match.percentage == 0 for match in matches)
    ]

def print_placeholder_only_characters(round_label: str, matches_by_character: dict[str, list[MatchResult]]) -> None:
    characters = placeholder_only_characters(matches_by_character)
    print(f"{round_label} placeholder-only characters: {characters}")

def placeholder_elimination_matches(characters: list[str]) -> dict[str, list[MatchResult]]:
    return {
        character: [
            MatchResult(character, "Link", 1, 0, 0),
            MatchResult(character, "Link", 2, 0, 0),
            MatchResult(character, "Link", 3, 0, 0),
        ]
        for character in characters
    }

def rank_window_characters(scores: dict[str, float], start_rank: int, end_rank: int) -> list[str]:
    ranked_characters = [
        character for character, _score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    return ranked_characters[start_rank - 1:end_rank]

def build_elimination_2_matches(round_3_scores: dict[str, float]) -> dict[str, list[MatchResult]]:
    return placeholder_elimination_matches(
        rank_window_characters(round_3_scores, ELIMINATION_2_RANK_START, ELIMINATION_2_RANK_END)
    )

def build_round_4_matches(round_3_scores: dict[str, float], elimination_2_scores: dict[str, float]) -> dict[str, list[MatchResult]]:
    top_56 = rank_window_characters(round_3_scores, 1, 56)
    top_8 = rank_window_characters(elimination_2_scores, 1, 8)
    ordered_characters = top_56 + [character for character in top_8 if character not in top_56]
    return placeholder_elimination_matches(ordered_characters)

def placeholder_round_matches(character: str) -> list[MatchResult]:
    return [
        MatchResult(character, "Mario", 1, 0, 0),
        MatchResult(character, "Mario", 2, 0, 0),
        MatchResult(character, "Mario", 3, 0, 0),
    ]

def bar_generator(value_map: dict, x_axis: str, y_axis: str, title: str, pdf: PdfPages) -> None:
    keys = list(value_map.keys())
    values = list(value_map.values())
    plt.figure(figsize=(11, 6))
    bars = plt.bar(keys, values, color="skyblue", edgecolor="black")
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.2f}", ha="center", va="bottom")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    pdf.savefig()
    plt.close()

def histogram_generator(character_dict: dict[str, float], x_axis: str, y_axis: str, title: str, pdf: PdfPages) -> None:
    values = list(character_dict.values())
    if not values:
        return
    plt.figure(figsize=(11, 6))
    plt.hist(values, bins=24, edgecolor="black", color="#9ecae1")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

def distribution_generator(character_dict: dict[str, float], x_axis: str, y_axis: str, title: str, pdf: PdfPages) -> None:
    values = list(character_dict.values())
    if len(values) < 2:
        return
    plt.figure(figsize=(11, 6))
    sns.kdeplot(values, fill=True, color="skyblue", linewidth=2)
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

def table_generator(category_to_characters: dict[str, list[str]], title: str, pdf: PdfPages) -> None:
    table_data = []
    row_heights: list[float] = []
    for category, chars in category_to_characters.items():
        chunks = [", ".join(chars[i:i + 5]) for i in range(0, len(chars), 5)] or [""]
        category_col = "\n".join([category] + [""] * (len(chunks) - 1))
        table_data.append([category_col, "\n".join(chunks)])
        row_heights.append(max(0.06, 0.04 * len(chunks)))
    fig_height = max(10, 1.6 + sum(0.75 * h for h in row_heights) * 10)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=table_data,
        colLabels=["Category", "Characters"],
        cellLoc="center",
        colWidths=[0.14, 0.86],
        loc="upper center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.35)
    header_height = 0.06
    for col in range(2):
        table[(0, col)].set_height(header_height)
    for row_index, row_height in enumerate(row_heights, start=1):
        for col in range(2):
            table[(row_index, col)].set_height(row_height)
    ax.set_title(title)
    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.97])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

@dataclass
class MatchResult:
    character: str
    opponent: str
    match_number: int
    stock_diff: int
    percentage: float

    @property
    def won(self) -> bool:
        return self.stock_diff > 0

    @property
    def lost(self) -> bool:
        return self.stock_diff < 0

    @property
    def is_placeholder(self) -> bool:
        return self.stock_diff == 0 and self.percentage == 0

@dataclass
class RoundScoringRule:
    round_number: int
    max_percentage: float
    early_round_limit: int = 3
    early_multiplier_fn: Callable[[int], float] = lambda _m: 1.0
    use_matchup_multiplier: bool = True
    late_match_division: bool = True

    def stage_multiplier(self, match_number: int) -> float:
        return self.early_multiplier_fn(match_number) if match_number <= self.early_round_limit else 1.0
@dataclass
class RoundSummary:
    round_number: int
    scores: dict[str, float]
    win_loses: dict[str, list]
    characters_played: set[str]
    all_characters: set[str]
    losses_received: dict[str, int]

@dataclass
class Round:
    round_number: int
    matches_by_character: dict[str, list[MatchResult]]
    scoring_rule: RoundScoringRule
    matchup_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def from_dataframe(cls, round_number: int, df: pd.DataFrame, scoring_rule: RoundScoringRule, matchup_df: pd.DataFrame) -> "Round":
        matches_by_character: dict[str, list[MatchResult]] = defaultdict(list)
        required_cols = {"Character", "Opponent", "Round", "Stock Diff", "Percentage"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Round {round_number}: missing required columns: {sorted(missing)}")
        for row in df.itertuples(index=False):
            match = MatchResult(
                character=str(getattr(row, "Character")),
                opponent=str(getattr(row, "Opponent")),
                match_number=int(getattr(row, "Round")),
                stock_diff=int(getattr(row, "Stock_Diff") if hasattr(row, "Stock_Diff") else getattr(row, "_5")),
                percentage=float(getattr(row, "Percentage")),
            )
            matches_by_character[match.character].append(match)
        for character in matches_by_character:
            matches_by_character[character].sort(key=lambda m: m.match_number)
        return cls(round_number=round_number, matches_by_character=dict(matches_by_character), scoring_rule=scoring_rule, matchup_df=matchup_df)

    def _matchup_multiplier(self, character: str, opponent: str, stock_diff: int) -> float:
        if stock_diff == 0 or self.matchup_df.empty or not self.scoring_rule.use_matchup_multiplier:
            return 1.0
        character_key = character.lower()
        opponent_key = opponent.lower()
        if "Character" not in self.matchup_df.columns or opponent_key not in self.matchup_df.columns:
            return 1.0
        row = self.matchup_df[self.matchup_df["Character"].astype(str).str.lower() == character_key]
        if row.empty:
            return 1.0
        try:
            matchup_value = float(row[opponent_key].iloc[0])
            return 1 - matchup_value / 20
        except Exception:
            return 1.0

    def _score_match(self, match: MatchResult) -> float:
        cap = self.scoring_rule.max_percentage
        if match.won:
            base_score = match.stock_diff + max(0.0, cap - match.percentage) / cap
        elif match.lost:
            base_score = 1 + match.stock_diff + min(1.0, match.percentage / cap)
        else:
            return 0.0
        score = base_score
        score *= self.scoring_rule.stage_multiplier(match.match_number)
        score *= self._matchup_multiplier(match.character, match.opponent, match.stock_diff)
        if self.scoring_rule.late_match_division and match.match_number > self.scoring_rule.early_round_limit:
            score /= match.match_number
        return score

    def calculate_with_records(self, previous_scores: dict[str, float], loss_counter: dict[str, int]) -> tuple[RoundSummary, pd.DataFrame]:
        scores = dict(previous_scores)
        win_loses = {
            "Lost Round 1": [0, 0.0, []],
            "Lost Round 2": [0, 0.0, []],
            "Lost Round 3": [0, 0.0, []],
            "Lost Round 4": [0, 0.0, []],
            "Lost Round 5": [0, 0.0, []],
            "Won Round 3": [0, 0.0, []],
            "Won Round 4": [0, 0.0, []],
            "Won Tourney": [0, 0.0, []],
        }
        characters_played = set()
        all_characters = set()
        record_rows: list[dict[str, object]] = []
        for character, matches in self.matches_by_character.items():
            characters_played.add(character)
            running_score = scores.get(character, 0.0)
            last_real_match: MatchResult | None = None
            for match in matches:
                all_characters.add(match.opponent)
                if match.is_placeholder:
                    continue
                last_real_match = match
                match_score = self._score_match(match)
                running_score += match_score
                matchup_multiplier = self._matchup_multiplier(match.character, match.opponent, match.stock_diff)
                record_rows.append(
                    {
                        "Character": character,
                        "Opponent": match.opponent,
                        "Round": match.match_number,
                        "Win": int(match.won),
                        "Loss": int(match.lost),
                        "Stock Diff": match.stock_diff,
                        "Percentage": match.percentage,
                        "Score": round(match_score, 3),
                        "Matchup": round(matchup_multiplier, 3),
                        "Accumulated_Sum": round(running_score, 3),
                    }
                )
                if match.lost:
                    loss_counter[match.opponent] += 1
            if last_real_match is not None:
                if last_real_match.lost:
                    result_key = f"Lost Round {last_real_match.match_number}"
                elif last_real_match.match_number >= 5:
                    result_key = "Won Tourney"
                elif last_real_match.match_number == 4:
                    result_key = "Won Round 4"
                else:
                    result_key = "Won Round 3"
                if result_key in win_loses:
                    win_loses[result_key][0] += 1
                    win_loses[result_key][1] += running_score
                    win_loses[result_key][2].append(character)
            scores[character] = round(running_score, 3)
        summary = RoundSummary(
            round_number=self.round_number,
            scores=scores,
            win_loses=win_loses,
            characters_played=characters_played,
            all_characters=all_characters,
            losses_received=dict(loss_counter),
        )
        records_df = pd.DataFrame(
            record_rows,
            columns=["Character", "Opponent", "Round", "Win", "Loss", "Stock Diff", "Percentage", "Score", "Matchup", "Accumulated_Sum"],
        )
        return summary, records_df

    def calculate(self, previous_scores: dict[str, float], loss_counter: dict[str, int]) -> RoundSummary:
        summary, _records_df = self.calculate_with_records(previous_scores, loss_counter)
        return summary


class TournamentManager:
    def __init__(self, records_dir: Path, reports_dir: Path, ranking_changes_dir: Path, matchup_df: pd.DataFrame):
        self.records_dir = records_dir
        self.reports_dir = reports_dir
        self.ranking_changes_dir = ranking_changes_dir
        self.matchup_df = matchup_df
        self.elimination_rounds = {3, 5, 8, 10, 12, 14, 16, 18, 20, 22}
        self.rules = self._build_round_rules()

    @staticmethod
    def _build_round_rules() -> dict[int, RoundScoringRule]:
        rules: dict[int, RoundScoringRule] = {}
        rules[1] = ROUND_1_RULE
        rules[2] = ROUND_2_RULE
        rules[3] = ELIMINATION_1_RULE
        rules[4] = ROUND_3_RULE
        rules[5] = ROUND_4_RULE
        for r in range(6, 51):
            rules[r] = RoundScoringRule(round_number=r, max_percentage=175, early_multiplier_fn=lambda _m: 1.0)
        return rules

    def _round_files(self) -> list[tuple[int, Path]]:
        files = []
        for f in self.records_dir.glob("*_records.csv"):
            label = f.stem.removesuffix("_records")
            number = LABEL_TO_ROUND.get(label)
            if number is not None:
                files.append((number, f))
        return sorted(files, key=lambda x: x[0])

    @staticmethod
    def _score_to_ranks(scores: dict[str, float]) -> dict[str, int]:
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return {character: i + 1 for i, (character, _) in enumerate(ordered)}

    @staticmethod
    def _rank_group(rank: int) -> str:
        if rank <= 32:
            return "Top 32"
        if rank <= 64:
            return "Top 64"
        return "Bottom 65+"

    @staticmethod
    def _overlay_rank_change_scorecards(ax: plt.Axes, changes: list[tuple], limit: int = 15) -> None:
        rises = sorted([entry for entry in changes if entry[3] > 0], key=lambda entry: entry[3], reverse=True)[:limit]
        drops = sorted([entry for entry in changes if entry[3] < 0], key=lambda entry: entry[3])[:limit]

        if rises:
            rises_lines = [f"+{delta:>2}  {character}" for character, _i_rank, _f_rank, delta, *_rest in rises]
        else:
            rises_lines = ["No positive rank movement"]

        if drops:
            drops_lines = [f"{delta:>3}  {character}" for character, _i_rank, _f_rank, delta, *_rest in drops]
        else:
            drops_lines = ["No negative rank movement"]

        top_text = f"Top {limit} Rises\n" + "\n".join(rises_lines)
        bottom_text = f"Top {limit} Drops\n" + "\n".join(drops_lines)

        ax.text(
            0.5,
            0.985,
            top_text,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=9,
            color="#064e3b",
            zorder=50,
            bbox={"boxstyle": "round,pad=0.55", "facecolor": "#ecfdf5", "edgecolor": "#10b981", "alpha": 0.96},
            clip_on=False,
        )
        ax.text(
            0.5,
            0.015,
            bottom_text,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=9,
            color="#7f1d1d",
            zorder=50,
            bbox={"boxstyle": "round,pad=0.55", "facecolor": "#fef2f2", "edgecolor": "#ef4444", "alpha": 0.96},
            clip_on=False,
        )

    def _ranking_changes_colored(self, initial_scores: dict[str, float], final_scores: dict[str, float], round_number: int, eliminated_characters: set[str]) -> None:
        initial_ranks = self._score_to_ranks(initial_scores)
        final_ranks = self._score_to_ranks(final_scores)
        all_chars = sorted(set(initial_ranks) | set(final_ranks))
        changes = []
        for c in all_chars:
            if c not in initial_ranks or c not in final_ranks:
                continue
            i_rank = initial_ranks[c]
            f_rank = final_ranks[c]
            delta = i_rank - f_rank
            i_group = self._rank_group(i_rank)
            f_group = self._rank_group(f_rank)
            if c in eliminated_characters:
                color = "#d62728" if round_number in self.elimination_rounds else "#ff7f0e"
            elif f_group != i_group:
                color = "#2ca02c" if f_rank < i_rank else "#9467bd"
            else:
                color = "#1f77b4" if delta > 0 else ("#7f7f7f" if delta == 0 else "#8c564b")
            changes.append((c, i_rank, f_rank, delta, color))
        if not changes:
            return
        changes.sort(key=lambda x: x[1])
        fig, ax = plt.subplots(figsize=(14, 10))
        for c, i_rank, f_rank, delta, color in changes:
            ax.plot([0, 1], [i_rank, f_rank], marker="o", color=color, alpha=0.75, linewidth=1.8)
            if abs(delta) >= 10:
                ax.text(1.02, f_rank, c, fontsize=7, va="center")
        self._overlay_rank_change_scorecards(ax, changes)
        ax.set_xticks([0, 1])
        display = ROUND_DISPLAY.get(round_number, f"Round {round_number}")
        ax.set_xticklabels(["Previous Round", display])
        ax.invert_yaxis()
        ax.set_ylabel("Rank")
        ax.set_title(f"{display}: Ranking Changes")
        ax.grid(axis="y", alpha=0.2)
        plt.tight_layout()
        label = ROUND_LABEL.get(round_number, f"round_{round_number}")
        filename = self.ranking_changes_dir / f"{label}_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig)
        plt.close(fig)

    def _ranking_changes_elimination(self, initial_scores: dict[str, float], final_scores: dict[str, float], round_number: int) -> None:
        """Generate elimination ranking changes with fixed top 64.

        Ranks 1-64 are locked and shown as grey arrows. Only initial ranks 65+
        are re-ordered based on final scores among that subset.
        """
        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        initial_ranks = self._score_to_ranks(initial_scores)
        if not initial_ranks:
            return

        ordered_initial = [c for c, _rank in sorted(initial_ranks.items(), key=lambda x: x[1])]
        bottom_characters = [c for c in ordered_initial if initial_ranks[c] >= 65]
        if not bottom_characters:
            return

        bottom_sorted_by_final = sorted(bottom_characters, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)
        display_final_ranks = {c: 65 + i for i, c in enumerate(bottom_sorted_by_final)}

        changes = []
        for c in ordered_initial:
            i_rank = initial_ranks[c]
            if i_rank <= 64:
                f_rank = i_rank
                color = "#7f7f7f"  # grey
            else:
                f_rank = display_final_ranks[c]
                if f_rank <= 72:
                    color = "#2ca02c"  # green
                elif f_rank <= 80:
                    color = "#bcbd22"  # yellow
                else:
                    color = "#d62728"  # red
            delta = i_rank - f_rank
            changes.append((c, i_rank, f_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for c, i_rank, f_rank, _delta, color in changes:
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
            ax.annotate(
                "",
                xy=(1, f_rank),
                xycoords="data",
                xytext=(0, i_rank),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", lw=2, color=color),
            )

            self._overlay_rank_change_scorecards(ax, changes, limit=5)

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Elimination 1: Rank 86 to 64 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "elimination_1_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_elimination_2(self, initial_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        """Generate Elimination 2 ranking changes with fixed top 56 and fixed Elimination 2 band 57-80."""

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 56:
                return "#7f7f7f"  # grey
            if rank <= 64:
                return "#2ca02c"  # green
            if rank <= 72:
                return "#bcbd22"  # yellow
            if rank <= 80:
                return "#d62728"  # red
            return "#000000"      # black

        initial_ranks = self._score_to_ranks(initial_scores)
        if not initial_ranks:
            return

        ordered_initial = [c for c, _rank in sorted(initial_ranks.items(), key=lambda x: x[1])]
        locked_top = [c for c in ordered_initial if initial_ranks[c] <= 56]
        elimination_2_characters = [c for c in ordered_initial if c in ELIMINATION_2_MATCHES]
        other_bottom = [c for c in ordered_initial if c not in locked_top and c not in ELIMINATION_2_MATCHES]

        elimination_2_sorted = sorted(elimination_2_characters, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)
        other_bottom_sorted = sorted(other_bottom, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)

        display_final_ranks: dict[str, int] = {}
        for idx, character in enumerate(elimination_2_sorted):
            display_final_ranks[character] = 57 + idx

        next_rank = 57 + len(elimination_2_sorted)
        for idx, character in enumerate(other_bottom_sorted):
            display_final_ranks[character] = next_rank + idx

        changes = []
        for character in ordered_initial:
            initial_rank = initial_ranks[character]
            if character in locked_top:
                final_rank = initial_rank
            else:
                final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
            ax.annotate(
                "",
                xy=(1, final_rank),
                xycoords="data",
                xytext=(0, initial_rank),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", lw=2, color=color),
            )

        self._overlay_rank_change_scorecards(ax, changes, limit=5)

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Elimination 2: Rank 86 to 57 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "elimination_2_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_black_arrows(self, seed_order: list[str], final_scores: dict[str, float], round_number: int = 1) -> None:
        """Generate Round 1 ranking changes with black arrows only (no color coding).
        
        seed_order: List of character names in seed/bracket order (1st seed, 2nd seed, etc.)
        final_scores: Dictionary of character names to their final round scores.
        """
        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"
        
        seed_ranks = {character: i + 1 for i, character in enumerate(seed_order)}
        final_ranks = self._score_to_ranks(final_scores)
        
        all_chars = sorted(set(seed_ranks) | set(final_ranks))
        changes = []
        for c in all_chars:
            if c not in seed_ranks or c not in final_ranks:
                continue
            i_rank = seed_ranks[c]
            f_rank = final_ranks[c]
            delta = i_rank - f_rank
            changes.append((c, i_rank, f_rank, delta))
        
        if not changes:
            return
        
        changes.sort(key=lambda x: x[1])
        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))
        
        for c, i_rank, f_rank, delta in changes:
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
            ax.annotate(
                "",
                xy=(1, f_rank),
                xycoords="data",
                xytext=(0, i_rank),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", lw=2, color="black"),
            )

            self._overlay_rank_change_scorecards(ax, changes)
        
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        display = ROUND_DISPLAY.get(round_number, f"Round {round_number}")
        ax.set_title(f"{display}: Rank 86 to 1 Rank Changes", fontsize=14)
        
        plt.tight_layout()
        label = ROUND_LABEL.get(round_number, f"round_{round_number}")
        filename = self.ranking_changes_dir / f"{label}_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_round_3(self, previous_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        """Generate Round 3 changes chart with rank-band colors."""
        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        initial_ranks = self._score_to_ranks(previous_scores)
        final_ranks = self._score_to_ranks(final_scores)
        all_chars = sorted(set(initial_ranks) | set(final_ranks))
        changes = []
        for c in all_chars:
            if c not in initial_ranks or c not in final_ranks:
                continue
            i_rank = initial_ranks[c]
            f_rank = final_ranks[c]
            delta = i_rank - f_rank
            if f_rank <= 48:
                color = "#2ca02c"  # green
            elif f_rank <= 72:
                color = "#bcbd22"  # yellow
            elif f_rank <= 80:
                color = "#d62728"  # red
            else:
                color = "#000000"  # black
            changes.append((c, i_rank, f_rank, delta, color))

        if not changes:
            return

        changes.sort(key=lambda x: x[1])
        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for c, i_rank, f_rank, _delta, color in changes:
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
            ax.annotate(
                "",
                xy=(1, f_rank),
                xycoords="data",
                xytext=(0, i_rank),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", lw=2, color=color),
            )

            self._overlay_rank_change_scorecards(ax, changes)

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Round 3 Ranking Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "round_3_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_round_4(self, previous_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        """Generate Round 4 ranking changes using elimination-style arrows and rank bands."""
        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 48:
                return "#2ca02c"  # green
            if rank <= 72:
                return "#bcbd22"  # yellow
            if rank <= 80:
                return "#d62728"  # red
            return "#000000"      # black

        initial_ranks = self._score_to_ranks(previous_scores)
        if not initial_ranks:
            return

        ordered_initial = [c for c, _rank in sorted(initial_ranks.items(), key=lambda x: x[1])]
        final_sorted = sorted(ordered_initial, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)
        display_final_ranks = {character: idx + 1 for idx, character in enumerate(final_sorted)}

        changes = []
        for character in ordered_initial:
            initial_rank = initial_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        changes.sort(key=lambda x: x[1])
        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
            ax.annotate(
                "",
                xy=(1, final_rank),
                xycoords="data",
                xytext=(0, initial_rank),
                textcoords="data",
                arrowprops=dict(arrowstyle="->", lw=2, color=color),
            )

        self._overlay_rank_change_scorecards(ax, changes, limit=15)

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Round 4 Ranking Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "round_4_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def _round_report(summary: RoundSummary, output_pdf: Path) -> None:
        win_loss_totals = {k: v[0] for k, v in summary.win_loses.items()}
        win_loss_averages = {k: round(v[1] / (v[0] if v[0] else 1), 3) for k, v in summary.win_loses.items()}
        win_loss_characters = {k: v[2] for k, v in summary.win_loses.items()}
        display = ROUND_DISPLAY.get(summary.round_number, f"Round {summary.round_number}")
        with PdfPages(output_pdf) as pdf:
            bar_generator(win_loss_totals, "Category", "Count", f"{display}: Win/Loss Totals", pdf)
            bar_generator(win_loss_averages, "Category", "Average Score", f"{display}: Win/Loss Average Scores", pdf)
            table_generator(win_loss_characters, f"{display}: End-Scenario Characters", pdf)
            histogram_generator(summary.scores, "Score", "Frequency", f"{display}: Score Distribution", pdf)
            distribution_generator(summary.scores, "Score", "Density", f"{display}: Score Density", pdf)

    def bootstrap_round_from_matches(
        self,
        round_number: int,
        matches_by_character: dict[str, list[MatchResult]],
        previous_scores: dict[str, float] | None = None,
    ) -> RoundSummary:
        rule = self.rules.get(round_number, RoundScoringRule(round_number=round_number, max_percentage=175))
        round_engine = Round(
            round_number=round_number,
            matches_by_character=matches_by_character,
            scoring_rule=rule,
            matchup_df=self.matchup_df,
        )
        summary, records_df = round_engine.calculate_with_records(previous_scores or {}, defaultdict(int))
        label = ROUND_LABEL.get(round_number, f"round_{round_number}")
        records_path = self.records_dir / f"{label}_records.csv"
        records_df.to_csv(records_path, index=False)
        return summary

    def run(self, start_round: int | None = None, end_round: int | None = None) -> dict[str, float]:
        files = self._round_files()
        if not files:
            raise FileNotFoundError("No files matched records/round_*_records.csv")
        if start_round is not None:
            files = [x for x in files if x[0] >= start_round]
        if end_round is not None:
            files = [x for x in files if x[0] <= end_round]
        cumulative_scores: dict[str, float] = {}
        round_history: dict[int, dict[str, float]] = {}
        loss_counter: dict[str, int] = defaultdict(int)
        for round_number, csv_path in files:
            df = pd.read_csv(csv_path)
            rule = self.rules.get(round_number, RoundScoringRule(round_number=round_number, max_percentage=175))
            round_engine = Round.from_dataframe(round_number, df, rule, self.matchup_df)
            if round_number == 3 and cumulative_scores:
                cumulative_scores = apply_score_reduction(cumulative_scores)
                previous_scores = dict(cumulative_scores)
            elif round_number == 4 and cumulative_scores:
                elimination_characters = set(ELIMINATION_1_MATCHES.keys())
                cumulative_scores = apply_selective_score_reduction(cumulative_scores, elimination_characters, exponent=0.539555)
                previous_scores = dict(cumulative_scores)
            elif round_number == 5 and cumulative_scores:
                elimination_characters = set(ELIMINATION_2_MATCHES.keys())
                cumulative_scores = apply_selective_score_reduction(
                    cumulative_scores,
                    elimination_characters,
                    exponent=ELIMINATION_2_ENTRY_EXPONENT,
                )
                previous_scores = dict(cumulative_scores)
            elif round_number == 6 and cumulative_scores:
                elimination_characters = set(ELIMINATION_2_MATCHES.keys())
                cumulative_scores = apply_selective_score_reduction(
                    cumulative_scores,
                    elimination_characters,
                    exponent=ROUND_4_SETUP_EXPONENT,
                )
                previous_scores = dict(cumulative_scores)
            else:
                previous_scores = dict(cumulative_scores)
            summary = round_engine.calculate(cumulative_scores, loss_counter)
            cumulative_scores = summary.scores
            round_history[round_number] = dict(cumulative_scores)
            report_path = self.reports_dir / f"{ROUND_LABEL.get(round_number, f'round_{round_number}')}_results.pdf"
            self._round_report(summary, report_path)
            if round_number == 2 and previous_scores:
                seed_order = [character for character, _score in sorted(previous_scores.items(), key=lambda item: item[1], reverse=True)]
                self._ranking_changes_black_arrows(seed_order, cumulative_scores, round_number=round_number)
            elif round_number == 3 and previous_scores:
                self._ranking_changes_elimination(previous_scores, cumulative_scores, round_number=round_number)
            elif round_number == 4 and previous_scores:
                self._ranking_changes_round_3(previous_scores, cumulative_scores)
            elif round_number == 6 and previous_scores:
                # Round 4 (semantic) ranking changes are generated in main() using ROUND_4_MATCHES.
                pass
            elif round_number == 5 and previous_scores:
                self._ranking_changes_elimination_2(previous_scores, cumulative_scores)
            elif previous_scores:
                eliminated = set(previous_scores) - set(cumulative_scores)
                self._ranking_changes_colored(previous_scores, cumulative_scores, round_number, eliminated)
        if not round_history:
            return {}
        with PdfPages(self.reports_dir / "all_rounds_histogram_evolution.pdf") as pdf:
            for rn in sorted(round_history):
                display = ROUND_DISPLAY.get(rn, f"Round {rn}")
                histogram_generator(round_history[rn], "Score", "Frequency", f"{display}: Score Distribution", pdf)
        with PdfPages(self.reports_dir / "all_rounds_distribution_evolution.pdf") as pdf:
            for rn in sorted(round_history):
                display = ROUND_DISPLAY.get(rn, f"Round {rn}")
                distribution_generator(round_history[rn], "Score", "Density", f"{display}: Score Density", pdf)
        final_round = max(round_history)
        final_scores = round_history[final_round]
        final_ranks = self._score_to_ranks(final_scores)
        final_df = pd.DataFrame([{"Character": c, "Score": s, "Rank": final_ranks[c]} for c, s in final_scores.items()]).sort_values("Rank")
        final_df.to_csv(self.records_dir / "overall_ranking_profile.csv", index=False)
        return final_scores

#######################################################
####################### ROUND 1 #######################
#######################################################

ROUND_1_RULE = RoundScoringRule(
    round_number=1,
    max_percentage=200,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1 + (m - 1) / 10,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_1_MATCHES: dict[str, list[MatchResult]] = {
    "Link": [ # 1st Previously
        MatchResult("Link", "Pyra & Mythra", 1, -1, 83),
    ],
    "King Dedede": [ # 2nd Previously
        MatchResult("King Dedede", "Olimar", 1, 2, 116),
        MatchResult("King Dedede", "Yoshi", 2, 1, 0),
        MatchResult("King Dedede", "Wolf", 3, 2, 106),
    ],
    "Dr Mario": [ # 3rd Previously
        MatchResult("Dr Mario", "Pokemon Trainer", 1, 3, 102),
        MatchResult("Dr Mario", "Cloud", 2, 2, 57),
        MatchResult("Dr Mario", "Sonic", 3, 3, 136),
    ],
    "Piranha Plant": [ # 4th Previously
        MatchResult("Piranha Plant", "Kazuya", 1, 2, 0),
        MatchResult("Piranha Plant", "Ness", 2, 2, 0),
        MatchResult("Piranha Plant", "Shulk", 3, 1, 53),
        MatchResult("Piranha Plant", "Pyra & Mythra", 4, 3, 141),
    ],
    "Chrom": [ # 5th Previously
        MatchResult("Chrom", "Corrin", 1, 2, 93),
        MatchResult("Chrom", "Bayonetta", 2, 2, 85),
        MatchResult("Chrom", "Simon", 3, 3, 97),
    ],
    "Banjo & Kazooie": [ # 6th Previously
        MatchResult("Banjo & Kazooie", "Wii Fit Trainer", 1, 1, 0),
        MatchResult("Banjo & Kazooie", "Inkling", 2, 3, 180),
        MatchResult("Banjo & Kazooie", "Hero", 3, 1, 8),
    ],
    "Zelda": [ # 7th Previously
        MatchResult("Zelda", "Greninja", 1, 2, 0),
        MatchResult("Zelda", "Lucario", 2, 2, 25),
        MatchResult("Zelda", "Ganondorf", 3, 3, 76),
    ],
    "Young Link": [ # 8th Previously
        MatchResult("Young Link", "Snake", 1, 2, 23),
        MatchResult("Young Link", "Bowser", 2, 2, 91),
        MatchResult("Young Link", "Joker", 3, 2, 108),
    ],
    "Ice Climbers": [ # 9th Previously
        MatchResult("Ice Climbers", "Snake", 1, 2, 106),
        MatchResult("Ice Climbers", "Olimar", 2, 2, 65),
        MatchResult("Ice Climbers", "Wii Fit Trainer", 3, 2, 11),
    ],
    "Yoshi": [ # 10th Previously
        MatchResult("Yoshi", "Mario", 1, 2, 137),
        MatchResult("Yoshi", "Byleth", 2, 1, 22),
        MatchResult("Yoshi", "Ness", 3, 3, 169),
    ],
    "Kirby": [ # 11th Previously
        MatchResult("Kirby", "Palutena", 1, 2, 11),
        MatchResult("Kirby", "Bowser", 2, 2, 40),
        MatchResult("Kirby", "Mewtwo", 3, 1, 26),
    ],
    "Ike": [ # 12th Previously
        MatchResult("Ike", "Daisy", 1, 1, 25),
        MatchResult("Ike", "Lucario", 2, 2, 110),
        MatchResult("Ike", "Link", 3, 1, 35),
    ],
    "Hero": [ # 13th Previously
        MatchResult("Hero", "Chrom", 1, 2, 93),
        MatchResult("Hero", "Peach", 2, 2, 107),
        MatchResult("Hero", "Sonic", 3, 2, 122),
    ],
    "Mii Gunner": [ # 14th Previously
        MatchResult("Mii Gunner", "Pac Man", 1, 2, 128),
        MatchResult("Mii Gunner", "Daisy", 2, 2, 37),
        MatchResult("Mii Gunner", "Mr Game & Watch", 3, 2, 57),
        MatchResult("Mii Gunner", "King Dedede", 5, 1, 48),
    ],
    "Mewtwo": [ # 15th Previously
        MatchResult("Mewtwo", "Terry", 1, -1, 13),
    ],
    "Bowser Jr": [ # 16th Previously
        MatchResult("Bowser Jr", "Ryu", 1, 2, 58),
        MatchResult("Bowser Jr", "Steve", 2, 2, 88),
        MatchResult("Bowser Jr", "King Dedede", 3, -1, 75),
    ],
    "Min Min": [ # 17th Previously
        MatchResult("Min Min", "Roy", 1, 2, 77),
        MatchResult("Min Min", "Terry", 2, 3, 98),
        MatchResult("Min Min", "Byleth", 3, 3, 133),
        MatchResult("Min Min", "Banjo & Kazooie", 4, 3, 167),
    ],
    "Ridley": [ # 18th Previously
        MatchResult("Ridley", "Pichu", 1, 1, 88),
        MatchResult("Ridley", "Samus", 2, 2, 59),
        MatchResult("Ridley", "Banjo & Kazooie", 3, -1, 92),
    ],
    "Cloud": [ # 19th Previously
        MatchResult("Cloud", "Sora", 1, 2, 176),
        MatchResult("Cloud", "Corrin", 2, 1, 46),
        MatchResult("Cloud", "Greninja", 3, 2, 32),
        MatchResult("Cloud", "Pac Man", 4, 2, 0),
    ],
    "Falco": [ # 20th Previously
        MatchResult("Falco", "Peach", 1, 1, 0),
        MatchResult("Falco", "Young Link", 2, 2, 47),
        MatchResult("Falco", "Pac Man", 3, -2, 80),
    ],
    "Sora": [ # 21st Previously
        MatchResult("Sora", "Snake", 1, 2, 142),
        MatchResult("Sora", "Yoshi", 2, 2, 33),
        MatchResult("Sora", "Min Min", 3, 1, 0),
    ],
    "Little Mac": [ # 22nd Previously
        MatchResult("Little Mac", "Pikachu", 1, 1, 46),
        MatchResult("Little Mac", "Duck Hunt", 2, 1, 0),
        MatchResult("Little Mac", "Isabellle", 3, 1, 95),
    ],
    "Sephiroth": [ # 23rd Previously
        MatchResult("Sephiroth", "Greninja", 1, 3, 130),
        MatchResult("Sephiroth", "Pit", 2, 3, 122),
        MatchResult("Sephiroth", "Zelda", 3, 2, 115),
    ],
    "Bowser": [ # 24th Previously
        MatchResult("Bowser", "King Dedede", 1, 2, 81),
        MatchResult("Bowser", "King K Rool", 2, 2, 44),
        MatchResult("Bowser", "Samus", 3, 3, 194),
    ],
    "Roy": [ # 25th Previously
        MatchResult("Roy", "Richter", 1, 2, 78),
        MatchResult("Roy", "Lucas", 2, 1, 0),
        MatchResult("Roy", "Wii Fit Trainer", 3, 3, 44),
    ],
    "King K Rool": [ # 26th Previously
        MatchResult("King K Rool", "King K Rool", 1, 2, 35),
        MatchResult("King K Rool", "Fox", 2, 1, 129),
        MatchResult("King K Rool", "Toon Link", 3, 3, 211),
        MatchResult("King K Rool", "Greninja", 4, 3, 101),
    ],
    "Pyra & Mythra": [ # 27th Previously
        MatchResult("Pyra & Mythra", "King Dedede", 1, -1, 62),
    ],
    "Isabelle": [ # 28th Previously
        MatchResult("Isabelle", "Falco", 1, 2, 164),
        MatchResult("Isabelle", "Kazuya", 2, 1, 71),
        MatchResult("Isabelle", "Pikachu", 3, 1, 0),
    ],
    "Dark Pit": [ # 29th Previously
        MatchResult("Dark Pit", "Link", 1, 2, 58),
        MatchResult("Dark Pit", "Inkling", 2, -1, 87),
    ],
    "Sonic": [ # 30th Previously
        MatchResult("Sonic", "Joker", 1, 1, 95),
        MatchResult("Sonic", "Shulk", 2, 1, 93),
        MatchResult("Sonic", "Piranha Plant", 3, -1, 29),
    ],
    "Toon Link": [ # 31st Previously
        MatchResult("Toon Link", "Pac Man", 1, 2, 47),
        MatchResult("Toon Link", "Mr Game & Watch", 2, 3, 104),
        MatchResult("Toon Link", "Isabelle", 3, 1, 0),
        MatchResult("Toon Link", "Piranha Plant", 4, 2, 122),
    ],
    "Donkey Kong": [ # 32nd Previously
        MatchResult("Donkey Kong", "Ken", 1, 3, 243),
        MatchResult("Donkey Kong", "Simon", 2, 1, 0),
        MatchResult("Donkey Kong", "Ganondorf", 3, 2, 116),
        MatchResult("Donkey Kong", "Kirby", 4, 2, 53),
    ],
    "Pokemon Trainer": [ # 33rd Previously
        MatchResult("Pokemon Trainer", "Wii Fit Trainer", 1, 1, 0),
        MatchResult("Pokemon Trainer", "Dark Samus", 2, 3, 129),
        MatchResult("Pokemon Trainer", "Byleth", 3, -1, 86),
    ],
    "Luigi": [ # 34th Previously
        MatchResult("Luigi", "Sheik", 1, 1, 0),
        MatchResult("Luigi", "Cloud", 2, 2, 131),
        MatchResult("Luigi", "Inkling", 3, 1, 51),
        MatchResult("Luigi", "Byleth", 4, 1, 6),
        MatchResult("Luigi", "Sora", 5, 2, 45),
    ],
    "Samus": [ # 35th Previously
        MatchResult("Samus", "Sora", 1, -1, 71),
    ],
    "Meta Knight": [ # 36th Previously
        MatchResult("Meta Knight", "Diddy Kong", 1, 1, 130),
        MatchResult("Meta Knight", "Fox", 2, 1, 48),
        MatchResult("Meta Knight", "Roy", 3, 1, 38),
        MatchResult("Meta Knight", "Sora", 4, -1, 71),
    ],
    "ROB": [ # 37th Previously
        MatchResult("ROB", "Olimar", 1, 1, 16),
        MatchResult("ROB", "Mega Man", 2, -1, 71),
        ],
    "Lucas": [ # 38th Previously
        MatchResult("Lucas", "Rosalina & Luma", 1, 2, 7),
        MatchResult("Lucas", "Banjo & Kazooie", 2, 2, 92),
        MatchResult("Lucas", "Wario", 3, 2, 82),
        MatchResult("Lucas", "Bowser Jr", 4, 2, 121),
        ],
    "Rosalina & Luma": [ # 39th Previously
        MatchResult("Rosalina & Luma", "Pyra & Mythra", 1, -1, 63),
        ],
    "Wii Fit Trainer": [ # 40th Previously
        MatchResult("Wii Fit Trainer", "Kirby", 1, 1, 86),
        MatchResult("Wii Fit Trainer", "Hero", 2, 3, 82),
        MatchResult("Wii Fit Trainer", "Daisy", 3, 2, 31),
        MatchResult("Wii Fit Trainer", "Richter", 4, 1, 42),
        ],
    "Pikachu": [ # 41st Previously
        MatchResult("Pikachu", "Jigglypuff", 1, 2, 149),
        MatchResult("Pikachu", "Inkling", 2, 2, 44),
        MatchResult("Pikachu", "Daisy", 3, 2, 117),
        ],
    "Ganondorf": [ # 42nd Previously
        MatchResult("Ganondorf", "Ganondorf", 1, 3, 128),
        MatchResult("Ganondorf", "Greninja", 2, 2, 17),
        MatchResult("Ganondorf", "Duck Hunt", 3, 2, 77),
        MatchResult("Ganondorf", "Ness", 4, 2, 6),
        ],
    "Byleth": [ # 43rd Previously
        MatchResult("Byleth", "Pokemon Trainer", 1, 1, 0),
        MatchResult("Byleth", "Ness", 2, -2, 98),
        ],
    "Mr Game & Watch": [ # 44th Previously
        MatchResult("Mr Game & Watch", "Bowser", 1, 1, 33),
        MatchResult("Mr Game & Watch", "Bayonetta", 2, 3, 85),
        MatchResult("Mr Game & Watch", "Wii Fit Trainer", 3, 1, 37),
        ],
    "Duck Hunt": [ # 45th Previously
        MatchResult("Duck Hunt", "Samus", 1, 1, 92),
        MatchResult("Duck Hunt", "Sephiroth", 2, 2, 74),
        MatchResult("Duck Hunt", "Roy", 3, 2, 52),
        ],
    "Captain Falcon": [ # 46th Previously
        MatchResult("Captain Falcon", "Olimar", 1, 1, 18),
        MatchResult("Captain Falcon", "Mega Man", 2, 2, 0),
        MatchResult("Captain Falcon", "Wario", 3, 2, 76),
        ],
    "Incineroar": [ # 47th Previously
        MatchResult("Incineroar", "Inkling", 1, 2, 0),
        MatchResult("Incineroar", "Luigi", 2, 2, 66),
        MatchResult("Incineroar", "Ryu", 3, 2, 23),
        ],
    "Inkling": [ # 48th Previously
        MatchResult("Inkling", "Lucas", 1, 1, 31),
        MatchResult("Inkling", "Greninja", 2, 1, 29),
        MatchResult("Inkling", "King Dedede", 3, 1, 26),
        ],
    "PacMan": [ # 49th Previously
        MatchResult("Pac Man", "Ken", 1, 1, 27),
        MatchResult("Pac Man", "King K Rool", 2, 2, 40),
        MatchResult("Pac Man", "Jigglypuff", 3, 2, 9),
        ],
    "Lucario": [ # 50th Previously
        MatchResult("Lucario", "Marth", 1, 2, 99),
        MatchResult("Lucario", "Snake", 2, 2, 163),
        MatchResult("Lucario", "Bowser Jr", 3, 3, 122),
        ],
    "Dark Samus": [ # 51st Previously
        MatchResult("Dark Samus", "Richter", 1, 2, 0),
        MatchResult("Dark Samus", "Mr Game & Watch", 2, 2, 22),
        MatchResult("Dark Samus", "Daisy", 3, 2, 73),
        ],
    "Mii Swordfighter": [ # 52nd Previously
        MatchResult("Mii Swordfighter", "Ice Climbers", 1, 3, 115),
        MatchResult("Mii Swordfighter", "Luigi", 2, 3, 165),
        MatchResult("Mii Swordfighter", "Sonic", 3, 2, 28),
        ],
    "Mario": [ # 53rd Previously
        MatchResult("Mario", "Pokemon Trainer", 1, 3, 152),
        MatchResult("Mario", "Simon", 2, 1, 10),
        MatchResult("Mario", "Richter", 3, 1, 69),
        ],
    "Ness": [ # 54th Previously
        MatchResult("Ness", "Corrin", 1, 1, 0),
        MatchResult("Ness", "Dr Mario", 2, 3, 65),
        MatchResult("Ness", "Shulk", 3, 1, 133),
        MatchResult("Ness", "ROB", 4, 2, 109),
        ],
    "Sheik": [ # 55th Previously
        MatchResult("Sheik", "Olimar", 1, 1, 129),
        MatchResult("Sheik", "Pyra & Mythra", 2, 2, 99),
        MatchResult("Sheik", "Sonic", 3, 1, 84),
        ],
    "Marth": [ # 56th Previously
        MatchResult("Marth", "Hero", 1, -1, 7),
        ],
    "Peach": [ # 57th Previously
        MatchResult("Peach", "Ness", 1, 3, 84),
        MatchResult("Peach", "Link", 2, 1, 93),
        MatchResult("Peach", "Joker", 3, 2, 60),
        ],
    "Mii Brawler": [ # 58th Previously
        MatchResult("Mii Brawler", "Sheik", 1, 2, 129),
        MatchResult("Mii Brawler", "Ike", 2, 1, 0),
        MatchResult("Mii Brawler", "Lucina", 3, 3, 20),
        ],
    "Wolf": [ # 59th Previously
        MatchResult("Wolf", "Snake", 1, 2, 64),
        MatchResult("Wolf", "Dark Pit", 2, 2, 100),
        MatchResult("Wolf", "Mewtwo", 3, 2, 88),
        ],
    "Jigglypuff": [ # 60th Previously
        MatchResult("Jigglypuff", "Mega Man", 1, 2, 59),
        MatchResult("Jigglypuff", "Kazuya", 2, 1, 37),
        MatchResult("Jigglypuff", "Piranha Plant", 3, 1, 0),
        ],
    "Palutena": [ # 61st Previously
        MatchResult("Palutena", "Donkey Kong", 1, -1, 76),
        ],
    "Fox": [ # 62nd Previously
        MatchResult("Fox", "Isabelle", 1, 1, 49),
        MatchResult("Fox", "Jigglypuff", 2, 1, 0),
        MatchResult("Fox", "Ice Climbers", 3, 1, 26),
        ],
    "Robin": [ # 63rd Previously
        MatchResult("Robin", "Ridley", 1, 1, 12),
        MatchResult("Robin", "Mr Game & Watch", 2, 2, 85),
        MatchResult("Robin", "Bayonetta", 3, 3, 157),
        ],
    "Greninja": [ # 64th Previously
        MatchResult("Greninja", "Banjo & Kazooie", 1, 1, 10),
        MatchResult("Greninja", "Pichu", 2, 1, 27),
        MatchResult("Greninja", "Snake", 3, 2, 123),
        MatchResult("Greninja", "Pyra & Mythra", 4, 3, 158),
        ],
    "Villager": [ # 65th Previously
        MatchResult("Villager", "Kirby", 1, 2, 57),
        MatchResult("Villager", "Robin", 2, 1, 78),
        MatchResult("Villager", "Young Link", 3, 2, 186),
        MatchResult("Villager", "Ice Climbers", 4, 1, 0),
        ],
    "Richter": [ # 66th Previously
        MatchResult("Richter", "Captain Falcon", 1, 3, 168),
        MatchResult("Richter", "Terry", 2, -1, 2),
        ],
    "Shulk": [ # 67th Previously
        MatchResult("Shulk", "Wii Fit Trainer", 1, 2, 87),
        MatchResult("Shulk", "Dark Samus", 2, 2, 10),
        MatchResult("Shulk", "Sheik", 3, 2, 110),
        ],
    "Zero Suit Samus": [ # 68th Previously
        MatchResult("Zero Suit Samus", "Peach", 1, 2, 70),
        MatchResult("Zero Suit Samus", "Fox", 2, 1, 101),
        MatchResult("Zero Suit Samus", "Dark Pit", 3, 1, 71),
        ],
    "Olimar": [ # 69th Previously
        MatchResult("Olimar", "Pokemon Trainer", 1, 2, 105),
        MatchResult("Olimar", "Peach", 2, 2, 95),
        MatchResult("Olimar", "Lucas", 3, 3, 9),
        ],
    "Terry": [ # 70th Previously
        MatchResult("Terry", "Dark Samus", 1, 3, 135),
        MatchResult("Terry", "Lucina", 2, 2, 116),
        MatchResult("Terry", "Zelda", 3, 2, 111),
        ],
    "Daisy": [ # 71st Previously
        MatchResult("Daisy", "Duck Hunt", 1, 1, 0),
        MatchResult("Daisy", "Young Link", 2, 1, 82),
        MatchResult("Daisy", "Pit", 3, 2, 44),
        ],
    "Pichu": [ # 72nd Previously
        MatchResult("Pichu", "Kazuya", 1, 1, 84),
        MatchResult("Pichu", "Bowser", 2, 1, 79),
        MatchResult("Pichu", "Simon", 3, 2, 66),
        ],
    "Ryu": [ # 73rd Previously
        MatchResult("Ryu", "Byleth", 1, 3, 128),
        MatchResult("Ryu", "Sheik", 2, 2, 22),
        MatchResult("Ryu", "Sora", 3, 1, 123),
        MatchResult("Ryu", "Kazuya", 5, -1, 102),
        ],
    "Lucina": [ # 74th Previously
        MatchResult("Lucina", "ROB", 1, 2, 23),
        MatchResult("Lucina", "Kazuya", 2, -1, 0),
        ],
    "Snake": [ # 75th Previously
        MatchResult("Snake", "King K Rool", 1, 1, 15),
        MatchResult("Snake", "Jigglypuff", 2, 2, 38),
        MatchResult("Snake", "Dark Pit", 3, 1, 6),
        ],
    "Diddy Kong": [ # 76th Previously
        MatchResult("Diddy Kong", "Bayonetta", 1, 2, 107),
        MatchResult("Diddy Kong", "Rosalina & Luma", 2, 2, 33),
        MatchResult("Diddy Kong", "Inkling", 3, -1, 38),
        ],
    "Pit": [ # 77th Previously
        MatchResult("Pit", "Yoshi", 1, 1, 17),
        MatchResult("Pit", "Sonic", 2, 3, 108),
        MatchResult("Pit", "Greninja", 3, 2, 81),
        ],
    "Corrin": [ # 78th Previously
        MatchResult("Corrin", "Little Mac", 1, 1, 8),
        MatchResult("Corrin", "Ness", 2, 3, 96),
        MatchResult("Corrin", "Shulk", 3, 2, 152),
        MatchResult("Corrin", "Fox", 4, 2, 17),
        ],
    "Steve": [ # 79th Previously
        MatchResult("Steve", "Cloud", 1, 2, 133),
        MatchResult("Steve", "Link", 2, -1, 98),
        ],
    "Wario": [ # 80th Previously
        MatchResult("Wario", "Wolf", 1, 1, 19),
        MatchResult("Wario", "Wii Fit Trainer", 2, 1, 28),
        MatchResult("Wario", "Rosalina & Luma", 3, 2, 113),
        ],
    "Bayonetta": [ # 81st Previously
        MatchResult("Bayonetta", "Samus", 1, 1, 172),
        MatchResult("Bayonetta", "Wario", 2, -1, 0),
        ],
    "Simon": [ # 82nd Previously
        MatchResult("Simon", "Fox", 1, 1, 7),
        MatchResult("Simon", "Mega Man", 2, 2, 92),
        MatchResult("Simon", "Donkey Kong", 3, 2, 143),
        MatchResult("Simon", "Villager", 4, 2, 88),
        ],
    "Joker": [ # 83rd Previously
        MatchResult("Joker", "Young Link", 1, 3, 210),
        MatchResult("Joker", "Mario", 2, 2, 77),
        MatchResult("Joker", "Sora", 3, 1, 198),
        MatchResult("Joker", "Wario", 4, 1, 14),
        ],
    "Mega Man": [ # 84th Previously
        MatchResult("Mega Man", "Kirby", 1, -1, 99),
        ],
    "Kazuya": [ # 85th Previously
        MatchResult("Kazuya", "Marth", 1, 3, 125),
        MatchResult("Kazuya", "Bowser", 2, -1, 146),
        ],
    "Ken": [ # 86th Previously
        MatchResult("Ken", "Falco", 1, 2, 92),
        MatchResult("Ken", "Daisy", 2, 2, 91),
        MatchResult("Ken", "King Dedede", 3, -1, 94),
        ]
}

#################################################
################### ROUND 2 #####################
#################################################

ROUND_2_RULE = RoundScoringRule(
    round_number=2,
    max_percentage=150,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1 + (m - 1) / 4,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_2_MATCHES: dict[str, list[MatchResult]] = {
    "Dr Mario": [ # 1st Previously
        MatchResult("Dr Mario", "Dark Pit", 1, 2, 163),
        MatchResult("Dr Mario", "King K Rool", 2, 2, 22),
        MatchResult("Dr Mario", "Bowser", 3, 1, 0),
    ],
    "Mii Swordfighter": [ # 2nd Previously
        MatchResult("Mii Swordfighter", "Greninja", 1, 1, 82),
        MatchResult("Mii Swordfighter", "Mega Man", 2, 2, 74),
        MatchResult("Mii Swordfighter", "Lucario", 3, 1, 37),
    ],
    "Ganondorf": [ # 3rd Previously
        MatchResult("Ganondorf", "Sephiroth", 1, 1, 145),
        MatchResult("Ganondorf", "PacMan", 2, 1, 0),
        MatchResult("Ganondorf", "Samus", 3, 1, 70),
    ],
    "Min Min": [ # 4th Previously
        MatchResult("Min Min", "Ken", 1, 2, 0),
        MatchResult("Min Min", "Ness", 2, 2, 10),
        MatchResult("Min Min", "Bayonetta", 3, 3, 108),
    ],
    "Piranha Plant": [ # 5th Previously
        MatchResult("Piranha Plant", "Pokemon Trainer", 1, 2, 156),
        MatchResult("Piranha Plant", "Jigglypuff", 2, 2, 0),
        MatchResult("Piranha Plant", "Captain Falcon", 3, 2, 103),
    ],
    "Chrom": [ # 6th Previously
        MatchResult("Chrom", "Mr Game & Watch", 1, 1, 59),
        MatchResult("Chrom", "Wii Fit Trainer", 2, 2, 72),
        MatchResult("Chrom", "Sephiroth", 3, 2, 25),
    ],
    "Incineroar": [ # 7th Previously
        MatchResult("Incineroar", "Falco", 1, 2, 112),
        MatchResult("Incineroar", "Wario", 2, 2, 132),
        MatchResult("Incineroar", "Palutena", 3, 2, 67),
    ],
    "Zelda": [ # 8th Previously
        MatchResult("Zelda", "Pichu", 1, 2, 0),
        MatchResult("Zelda", "King Dedede", 2, 3, 102),
        MatchResult("Zelda", "Kazuya", 3, 3, 47),
    ],
    "Sephiroth": [ # 9th Previously
        MatchResult("Sephiroth", "Pyra & Mythra", 1, 2, 76),
        MatchResult("Sephiroth", "Lucario", 2, 2, 27),
        MatchResult("Sephiroth", "Dark Pit", 3, 2, 27),
    ],
    "Ice Climbers": [ # 10th Previously
        MatchResult("Ice Climbers", "Sheik", 1, 2, 12),
        MatchResult("Ice Climbers", "Bowser", 2, 1, 92),
        MatchResult("Ice Climbers", "Roy", 3, 1, 5),
    ],
    "Toon Link": [ # 11th Previously
        MatchResult("Toon Link", "Pichu", 1, 2, 48),
        MatchResult("Toon Link", "Banjo & Kazooie", 2, 1, 15),
        MatchResult("Toon Link", "Steve", 3, 1, 52),
    ],
    "Lucas": [ # 12th Previously
        MatchResult("Lucas", "Pit", 1, 2, 3),
        MatchResult("Lucas", "Ike", 2, 3, 129),
        MatchResult("Lucas", "PacMan", 3, 2, 14),
    ],
    "Mii Gunner": [ # 13th Previously
        MatchResult("Mii Gunner", "Shulk", 1, 3, 149),
        MatchResult("Mii Gunner", "Zelda", 2, 2, 0),
        MatchResult("Mii Gunner", "Duck Hunt", 3, 3, 155),
    ],
    "Roy": [ # 14th Previously
        MatchResult("Roy", "Zero Suit Samus", 1, 3, 100),
        MatchResult("Roy", "Luigi", 2, 2, 59),
        MatchResult("Roy", "Captain Falcon", 3, 3, 121),
        MatchResult("Roy", "Samus", 4, 1, 35),
    ],
    "Lucario": [ # 15th Previously
        MatchResult("Lucario", "Byleth", 1, -1, 0),
    ],
    "Dark Samus": [ # 16th Previously
        MatchResult("Dark Samus", "ROB", 1, 2, 85),
        MatchResult("Dark Samus", "Steve", 2, 2, 73),
        MatchResult("Dark Samus", "Richter", 3, 3, 85),
    ],
    "Olimar": [ # 17th Previously
        MatchResult("Olimar", "Yoshi", 1, 2, 98),
        MatchResult("Olimar", "Pit", 2, 2, 12),
        MatchResult("Olimar", "PacMan", 3, 1, 32),
    ],
    "Bowser": [ # 18th Previously
        MatchResult("Bowser", "ROB", 1, 3, 167),
        MatchResult("Bowser", "Sheik", 2, 2, 45),
        MatchResult("Bowser", "Link", 3, 1, 89),
        MatchResult("Bowser", "King Dedede", 4, 2, 8),
    ],
    "Wii Fit Trainer": [ # 19th Previously
        MatchResult("Wii Fit Trainer", "Toon Link", 1, 2, 36),
        MatchResult("Wii Fit Trainer", "Pyra & Mythra", 2, 1, 142),
        MatchResult("Wii Fit Trainer", "King Dedede", 3, -1, 85),
    ],
    "King K Rool": [ # 20th Previously
        MatchResult("King K Rool", "Dark Samus", 1, 1, 0),
        MatchResult("King K Rool", "Kirby", 2, 2, 30),
        MatchResult("King K Rool", "Chrom", 3, 2, 23),
    ],
    "Young Link": [ # 21st Previously
        MatchResult("Young Link", "Sephiroth", 1, 1, 0),
        MatchResult("Young Link", "Diddy Kong", 2, 3, 86),
        MatchResult("Young Link", "Villager", 3, -1, 6),
    ],
    "Terry": [ # 22nd Previously
        MatchResult("Terry", "Dark Pit", 1, 1, 73),
        MatchResult("Terry", "Palutena", 2, 1, 0),
        MatchResult("Terry", "Duck Hunt", 3, 1, 0),
    ],
    "Robin": [ # 23rd Previously
        MatchResult("Robin", "Corrin", 1, 1, 61),
        MatchResult("Robin", "Incineroar", 2, 2, 10),
        MatchResult("Robin", "Shulk", 3, 1, 0),
        MatchResult("Robin", "Villager", 5, 2, 25),
    ],
    "Corrin": [ # 24th Previously
        MatchResult("Corrin", "Lucina", 1, 2, 94),
        MatchResult("Corrin", "Zero Suit Samus", 2, 2, 57),
        MatchResult("Corrin", "Bayonetta", 3, 3, 131),
        MatchResult("Corrin", "Villager", 4, -1, 63),
    ],
    "Pit": [ # 25th Previously
        MatchResult("Pit", "Marth", 1, 2, 38),
        MatchResult("Pit", "Daisy", 2, 3, 148),
        MatchResult("Pit", "King Dedede", 3, -1, 101),
    ],
    "Mii Brawler": [ # 26th Previously
        MatchResult("Mii Brawler", "Terry", 1, -1, 102),
    ],
    "Donkey Kong": [ # 27th Previously
        MatchResult("Donkey Kong", "Luigi", 1, 2, 94),
        MatchResult("Donkey Kong", "Jigglypuff", 2, 2, 0),
        MatchResult("Donkey Kong", "Roy", 3, 2, 50),
        MatchResult("Donkey Kong", "King Dedede", 4, -1, 66),
    ],
    "Captain Falcon": [ # 28th Previously
        MatchResult("Captain Falcon", "Ike", 1, 1, 47),
        MatchResult("Captain Falcon", "Steve", 2, -1, 118),
    ],
    "Shulk": [ # 29th Previously
        MatchResult("Shulk", "Wii Fit Trainer", 1, 3, 125),
        MatchResult("Shulk", "Jigglypuff", 2, 2, 0),
        MatchResult("Shulk", "Daisy", 3, 2, 122),
    ],
    "Ryu": [ # 30th Previously
        MatchResult("Ryu", "Diddy Kong", 1, 1, 149),
        MatchResult("Ryu", "Joker", 2, 1, 22),
        MatchResult("Ryu", "Snake", 3, -1, 146),
    ],
    "Hero": [ # 31st Previously
        MatchResult("Hero", "Ike", 1, 2, 58),
        MatchResult("Hero", "Pikachu", 2, 1, 104),
        MatchResult("Hero", "Chrom", 3, 2, 57),
        MatchResult("Hero", "Snake", 4, 2, 98),
    ],
    "Peach": [ # 32nd Previously
        MatchResult("Peach", "Min Min", 1, 1, 57),
        MatchResult("Peach", "Incineroar", 2, 2, 54),
        MatchResult("Peach", "Lucina", 3, 1, 44),
    ],
    "Kirby": [ # 33rd Previously
        MatchResult("Kirby", "Mr Game & Watch", 1, 3, 129),
        MatchResult("Kirby", "Bowser Jr", 2, 2, 45),
        MatchResult("Kirby", "Captain Falcon", 3, -1, 146),
    ],
    "Yoshi": [ # 34th Previously
        MatchResult("Yoshi", "Hero", 1, 2, 67),
        MatchResult("Yoshi", "Olimar", 2, 1, 0),
        MatchResult("Yoshi", "Robin", 3, 2, 119),
    ],
    "Wolf": [ # 35th Previously
        MatchResult("Wolf", "Falco", 1, 2, 83),
        MatchResult("Wolf", "Kazuya", 2, 1, 112),
        MatchResult("Wolf", "Dark Pit", 3, 2, 41),
    ],
    "Sora": [ # 36th Previously
        MatchResult("Sora", "Palutena", 1, 1, 12),
        MatchResult("Sora", "Sephiroth", 2, 2, 15),
        MatchResult("Sora", "Joker", 3, 2, 130),
        MatchResult("Sora", "Captain Falcon", 4, 3, 106),
    ],
    "King Dedede": [ # 37th Previously
        MatchResult("King Dedede", "Joker", 1, 2, 143),
        MatchResult("King Dedede", "Pokemon Trainer", 2, 1, 0),
        MatchResult("King Dedede", "Marth", 3, 3, 123),
        MatchResult("King Dedede", "Sephiroth", 4, 2, 90),
    ],
    "Simon": [ # 38th Previously
        MatchResult("Simon", "Toon Link", 1, 2, 47),
        MatchResult("Simon", "Robin", 2, 1, 40),
        MatchResult("Simon", "Sephiroth", 3, -1, 118),
    ],
    "Duck Hunt": [ # 39th Previously
        MatchResult("Duck Hunt", "Meta Knight", 1, 2, 62),
        MatchResult("Duck Hunt", "Rosalina & Luma", 2, 2, 48),
        MatchResult("Duck Hunt", "Diddy Kong", 3, 2, 100),
        MatchResult("Duck Hunt", "Incineroar", 4, 1, 15),
    ],
    "Ness": [ # 40th Previously
        MatchResult("Ness", "Incineroar", 1, -1, 93),
    ],
    "Greninja": [ # 41st Previously
        MatchResult("Greninja", "Simon", 1, 2, 15),
        MatchResult("Greninja", "Bowser", 2, 1, 60),
        MatchResult("Greninja", "Ridley", 3, 1, 15),
    ],
    "Cloud": [ # 42nd Previously
        MatchResult("Cloud", "Lucas", 1, 2, 0),
        MatchResult("Cloud", "Dark Pit", 2, 1, 60),
        MatchResult("Cloud", "Pikachu", 3, 2, 115),
    ],
    "PacMan": [ # 43rd Previously
        MatchResult("PacMan", "Mario", 1, 1, 6),
        MatchResult("PacMan", "Olimar", 2, 2, 66),
        MatchResult("PacMan", "Shulk", 3, 2, 102),
        MatchResult("PacMan", "Pichu", 4, 2, 204),
    ],
    "Pikachu": [ # 44th Previously
        MatchResult("Pikachu", "Ike", 1, -1, 29),
    ],
    "Banjo & Kazooie": [ # 45th Previously
        MatchResult("Banjo & Kazooie", "Rosalina & Luma", 1, 2, 101),
        MatchResult("Banjo & Kazooie", "Mega Man", 2, 2, 4),
        MatchResult("Banjo & Kazooie", "Little Mac", 3, 2, 18),
        MatchResult("Banjo & Kazooie", "Marth", 4, 1, 39),
    ],
    "Villager": [ # 46th Previously
        MatchResult("Villager", "Pit", 1, 1, 74),
        MatchResult("Villager", "Hero", 2, -2, 101),
        MatchResult("Villager", "Marth", 3, 0, 0),
    ],
    "Mr Game & Watch": [ # 47th Previously
        MatchResult("Mr Game & Watch", "Toon Link", 1, 2, 78),
        MatchResult("Mr Game & Watch", "Steve", 2, 1, 125),
        MatchResult("Mr Game & Watch", "Min Min", 3, 3, 159),
    ],
    "Joker": [ # 48th Previously
        MatchResult("Joker", "Ryu", 1, 2, 124),
        MatchResult("Joker", "Meta Knight", 2, 3, 185),
        MatchResult("Joker", "Ice Climbers", 3, 2, 135),
    ],
    "Luigi": [ # 49th Previously
        MatchResult("Luigi", "Pichu", 1, 1, 46),
        MatchResult("Luigi", "Mega Man", 2, 1, 13),
        MatchResult("Luigi", "Zelda", 3, 1, 67),
        MatchResult("Luigi", "Sora", 4, -1, 100),
    ],
    "Mario": [ # 50th Previously
        MatchResult("Mario", "Young Link", 1, 2, 104),
        MatchResult("Mario", "Ryu", 2, 2, 170),
        MatchResult("Mario", "Pyra & Mythra", 3, 2, 102),
    ],
    "Snake": [ # 51st Previously
        MatchResult("Snake", "Sora", 1, -1, 192),
    ],
    "Jigglypuff": [ # 52nd Previously
        MatchResult("Jigglypuff", "Ike", 1, 2, 0),
        MatchResult("Jigglypuff", "Ridley", 2, 2, 0),
        MatchResult("Jigglypuff", "Lucina", 3, 1, 13),
        MatchResult("Jigglypuff", "Sora", 5, 1, 2),
    ],
    "Daisy": [ # 53rd Previously
        MatchResult("Daisy", "Steve", 1, -2, 104),
    ],
    "Pichu": [ # 54th Previously
        MatchResult("Pichu", "Lucina", 1, -2, 74),
    ],
    "Wario": [ # 55th Previously
        MatchResult("Wario", "Samus", 1, 2, 148),
        MatchResult("Wario", "Terry", 2, -1, 66),
    ],
    "Ike": [ # 56th Previously
        MatchResult("Ike", "Pikachu", 1, 2, 27),
        MatchResult("Ike", "Bayonetta", 2, 3, 108),
        MatchResult("Ike", "Piranha Plant", 3, 1, 98),
        MatchResult("Ike", "Lucina", 4, 3, 144),
        MatchResult("Ike", "Sheik", 5, 2, 90),
    ],
    "Isabelle": [ # 57th Previously
        MatchResult("Isabelle", "Bowser", 1, 2, 52),
        MatchResult("Isabelle", "Hero", 2, -1, 125),
    ],
    "Pokemon Trainer": [ # 58th Previously
        MatchResult("Pokemon Trainer", "Banjo & Kazooie", 1, 1, 12),
        MatchResult("Pokemon Trainer", "Wii Fit Trainer", 2, 2, 114),
        MatchResult("Pokemon Trainer", "Corrin", 3, 1, 54),
    ],
    "Zero Suit Samus": [ # 59th Previously
        MatchResult("Zero Suit Samus", "Bowser Jr", 1, 1, 41),
        MatchResult("Zero Suit Samus", "Ken", 2, 1, 60),
        MatchResult("Zero Suit Samus", "Cloud", 3, 1, 48),
    ],
    "Bowser Jr": [ # 60th Previously
        MatchResult("Bowser Jr", "ROB", 1, 3, 203),
        MatchResult("Bowser Jr", "Diddy Kong", 2, 3, 140),
        MatchResult("Bowser Jr", "Joker", 3, 2, 39),
        MatchResult("Bowser Jr", "Hero", 4, 2, 62),
    ],
    "Fox": [ # 61st Previously
        MatchResult("Fox", "Captain Falcon", 1, 1, 110),
        MatchResult("Fox", "Mr Game & Watch", 2, -2, 106),
    ],
    "Sheik": [ # 62nd Previously
        MatchResult("Sheik", "Banjo & Kazooie", 1, 2, 91),
        MatchResult("Sheik", "Luigi", 2, 1, 29),
        MatchResult("Sheik", "Pokemon Trainer", 3, 1, 0),
        MatchResult("Sheik", "Ganondorf", 4, -1, 115),
    ],
    "Meta Knight": [ # 63rd Previously
        MatchResult("Meta Knight", "Daisy", 1, 2, 116),
        MatchResult("Meta Knight", "Mega Man", 2, -1, 129),
    ],
    "Little Mac": [ # 64th Previously
        MatchResult("Little Mac", "Mewtwo", 1, -2, 37),
    ],
    "Inkling": [ # 65th Previously
        MatchResult("Inkling", "Kirby", 1, 1, 116),
        MatchResult("Inkling", "Roy", 2, 2, 131),
        MatchResult("Inkling", "Sonic", 3, 2, 115),
        MatchResult("Inkling", "Bowser", 4, -1, 129),
    ],
    "Ken": [ # 66th Previously
        MatchResult("Ken", "ROB", 1, 1, 23),
        MatchResult("Ken", "Snake", 2, 2, 80),
        MatchResult("Ken", "Bowser", 3, -1, 69),
    ],
    "Diddy Kong": [ # 67th Previously
        MatchResult("Diddy Kong", "Ridley", 1, 2, 48),
        MatchResult("Diddy Kong", "Wario", 2, 1, 51),
        MatchResult("Diddy Kong", "Fox", 3, 2, 105),
    ],
    "Ridley": [ # 68th Previously
        MatchResult("Ridley", "Bowser Jr", 1, 2, 45),
        MatchResult("Ridley", "Robin", 2, 2, 90),
        MatchResult("Ridley", "Steve", 3, 2, 0),
        MatchResult("Ridley", "Inkling", 5, 2, 144),
    ],
    "Falco": [ # 69th Previously
        MatchResult("Falco", "Pit", 1, 2, 135),
        MatchResult("Falco", "Captain Falcon", 2, -1, 48),
    ],
    "Kazuya": [ # 70th Previously
        MatchResult("Kazuya", "Lucario", 1, 1, 126),
        MatchResult("Kazuya", "Robin", 2, -1, 78),
    ],
    "Sonic": [ # 71st Previously
        MatchResult("Sonic", "Ganondorf", 1, 2, 72),
        MatchResult("Sonic", "Joker", 2, 2, 138),
        MatchResult("Sonic", "Richter", 3, 2, 39),
        MatchResult("Sonic", "Pikachu", 4, 3, 197),
    ],
    "Dark Pit": [ # 72nd Previously
        MatchResult("Dark Pit", "Fox", 1, 2, 0),
        MatchResult("Dark Pit", "PacMan", 2, 2, 8),
        MatchResult("Dark Pit", "Hero", 3, 1, 13),
        MatchResult("Dark Pit", "Cloud", 4, 2, 47),
    ],
    "Lucina": [ # 73rd Previously
        MatchResult("Lucina", "Banjo & Kazooie", 1, 2, 99),
        MatchResult("Lucina", "Olimar", 2, 2, 147),
        MatchResult("Lucina", "Kazuya", 3, 1, 0),
    ],
    "Richter": [ # 74th Previously
        MatchResult("Richter", "Incineroar", 1, 2, 0),
        MatchResult("Richter", "Peach", 2, 1, 68),
        MatchResult("Richter", "Piranha Plant", 3, 2, 0),
    ],
    "Steve": [ # 75th Previously
        MatchResult("Steve", "Shulk", 1, 1, 84),
        MatchResult("Steve", "Hero", 2, 1, 138),
        MatchResult("Steve", "Mewtwo", 3, 2, 0),
    ],
    "ROB": [ # 76th Previously
        MatchResult("ROB", "Inkling", 1, 2, 65),
        MatchResult("ROB", "Villager", 2, 2, 53),
        MatchResult("ROB", "Ike", 3, 3, 105),
    ],
    "Byleth": [ # 77th Previously
        MatchResult("Byleth", "Pit", 1, 2, 65),
        MatchResult("Byleth", "Yoshi", 2, -1, 74),
    ],
    "Bayonetta": [ # 78th Previously
        MatchResult("Bayonetta", "Ice Climbers", 1, 2, 42),
        MatchResult("Bayonetta", "Sephiroth", 2, -1, 86),
    ],
    "Mega Man": [ # 79th Previously
        MatchResult("Mega Man", "Rosalina & Luma", 1, 2, 63),
        MatchResult("Mega Man", "Greninja", 2, 2, 143),
        MatchResult("Mega Man", "PacMan", 3, 1, 0),
        MatchResult("Mega Man", "Chrom", 4, 2, 129),
    ],
    "Link": [ # 80th Previously
        MatchResult("Link", "Dark Pit", 1, 3, 150),
        MatchResult("Link", "King Dedede", 2, 1, 0),
        MatchResult("Link", "Captain Falcon", 3, 2, 99),
        MatchResult("Link", "Ryu", 4, 3, 163),
    ],
    "Palutena": [ # 81st Previously
        MatchResult("Palutena", "Zelda", 1, 1, 24),
        MatchResult("Palutena", "Captain Falcon", 2, 2, 78),
        MatchResult("Palutena", "Snake", 3, 3, 147),
        MatchResult("Palutena", "Meta Knight", 4, 2, 24),
    ],
    "Samus": [ # 82nd Previously
        MatchResult("Samus", "Richter", 1, 2, 113),
        MatchResult("Samus", "Incineroar", 2, 2, 84),
        MatchResult("Samus", "Greninja", 3, 3, 97),
    ],
    "Rosalina & Luma": [ # 83rd Previously
        MatchResult("Rosalina & Luma", "Dr Mario", 1, 2, 199),
        MatchResult("Rosalina & Luma", "Piranha Plant", 2, -2, 113),
    ],
    "Pyra & Mythra": [ # 84th Previously
        MatchResult("Pyra & Mythra", "Jigglypuff", 1, 1, 9),
        MatchResult("Pyra & Mythra", "Pokemon Trainer", 2, 2, 68),
        MatchResult("Pyra & Mythra", "PacMan", 3, 3, 81),
        MatchResult("Pyra & Mythra", "Little Mac", 4, 1, 41),
    ],
    "Mewtwo": [ # 85th Previously
        MatchResult("Mewtwo", "Yoshi", 1, 2, 145),
        MatchResult("Mewtwo", "Mario", 2, 2, 87),
        MatchResult("Mewtwo", "Lucas", 3, 2, 124),
    ],
    "Marth": [ # 86th Previously
        MatchResult("Marth", "Piranha Plant", 1, 1, 0),
        MatchResult("Marth", "Terry", 2, 1, 62),
        MatchResult("Marth", "Little Mac", 3, -1, 83),
    ],
}

#######################################################
################### ELIMINATION 1 #####################
#######################################################

ELIMINATION_1_RULE = RoundScoringRule(
    round_number=3,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1 + (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ELIMINATION_1_MATCHES: dict[str, list[MatchResult]] = {
    "Palutena": [ # 65th Previously
        MatchResult("Palutena", "Mr Game & Watch", 1, 3, 95),
        MatchResult("Palutena", "King K Rool", 2, -1, 64),
    ],
    "Mii Brawler": [ # 66th Previously
        MatchResult("Mii Brawler", "Marth", 1, 2, 53),
        MatchResult("Mii Brawler", "Steve", 2, 2, 101),
        MatchResult("Mii Brawler", "Bowser", 3, 2, 71),
    ],
    "Meta Knight": [ # 67th Previously
        MatchResult("Meta Knight", "Robin", 1, 2, 5),
        MatchResult("Meta Knight", "Kazuya", 2, 1, 108),
        MatchResult("Meta Knight", "Simon", 3, 2, 0),
    ],
    "Lucario": [ # 68th Previously
        MatchResult("Lucario", "Lucina", 1, 3, 135),
        MatchResult("Lucario", "Wolf", 2, 1, 93),
        MatchResult("Lucario", "Simon", 3, 1, 5),
    ],
    "Steve": [ # 69th Previously
        MatchResult("Steve", "Mr Game & Watch", 1, 2, 0),
        MatchResult("Steve", "Link", 2, -2, 90),
    ],
    "Wario": [ # 70th Previously
        MatchResult("Wario", "Samus", 1, 1, 11),
        MatchResult("Wario", "Min Min", 2, 2, 28),
        MatchResult("Wario", "Zero Suit Samus", 3, 2, 0),
        MatchResult("Wario", "Little Mac", 4, 2, 64),
        MatchResult("Wario", "Falco", 5, 2, 58),
    ],
    "Mega Man": [ # 71st Previously
        MatchResult("Mega Man", "Samus", 1, 1, 55),
        MatchResult("Mega Man", "Pichu", 2, 2, 110),
        MatchResult("Mega Man", "Pit", 3, 3, 143),
    ],
    "Villager": [ # 72nd Previously
        MatchResult("Villager", "Ken", 1, 2, 127),
        MatchResult("Villager", "King Dedede", 2, 1, 93),
        MatchResult("Villager", "Daisy", 3, 3, 131),
    ],
    "Ness": [ # 73rd Previously
        MatchResult("Ness", "Ridley", 1, 2, 69),
        MatchResult("Ness", "Ryu", 2, 2, 0),
        MatchResult("Ness", "Zero Suit Samus", 3, 1, 0),
    ],
    "Mewtwo": [ # 74th Previously
        MatchResult("Mewtwo", "Donkey Kong", 1, 1, 0),
        MatchResult("Mewtwo", "Sephiroth", 2, 1, 79),
        MatchResult("Mewtwo", "Palutena", 3, 2, 22),
    ],
    "Snake": [ # 75th Previously
        MatchResult("Snake", "Lucina", 1, 1, 11),
        MatchResult("Snake", "Olimar", 2, 1, 69),
        MatchResult("Snake", "Mega Man", 3, 2, 104),
    ],
    "Pikachu": [ # 76th Previously
        MatchResult("Pikachu", "Ganondorf", 1, -1, 74),
    ],
    "Fox": [ # 77th Previously
        MatchResult("Fox", "Luigi", 1, 2, 12),
        MatchResult("Fox", "Kirby", 2, 1, 0),
        MatchResult("Fox", "Ken", 3, 2, 2),
        MatchResult("Fox", "Link", 4, 1, 71),
    ],
    "Falco": [ # 78th Previously
        MatchResult("Falco", "Dr Mario", 1, -1, 107),
    ],
    "Daisy": [ # 79th Previously
        MatchResult("Daisy", "Cloud", 1, 2, 32),
        MatchResult("Daisy", "Little Mac", 2, -1, 83),
    ],
    "Pichu": [ # 80th Previously
        MatchResult("Pichu", "Link", 1, 1, 27),
        MatchResult("Pichu", "Peach", 2, 1, 3),
        MatchResult("Pichu", "Duck Hunt", 3, 3, 135),
    ],
    "Kazuya": [ # 81st Previously
        MatchResult("Kazuya", "Lucas", 1, -1, 124),
    ],
    "Little Mac": [ # 82nd Previously
        MatchResult("Little Mac", "Incineroar", 1, 2, 106),
        MatchResult("Little Mac", "Yoshi", 2, 2, 152),
        MatchResult("Little Mac", "Cloud", 3, 3, 79),
    ],
    "Marth": [ # 83rd Previously
        MatchResult("Marth", "Olimar", 1, 1, 56),
        MatchResult("Marth", "Terry", 2, -2, 135),
        MatchResult("Marth", "PacMan", 3, 0, 0),
    ],
    "Byleth": [ # 84th Previously
        MatchResult("Byleth", "King Dedede", 1, 1, 0),
        MatchResult("Byleth", "Pokemon Trainer", 2, 1, 40),
        MatchResult("Byleth", "Dr Mario", 3, 1, 78),
    ],
    "Bayonetta": [ # 85th Previously
        MatchResult("Bayonetta", "Ridley", 1, 2, 72),
        MatchResult("Bayonetta", "Toon Link", 2, 1, 117),
        MatchResult("Bayonetta", "King Dedede", 3, 2, 86),
        MatchResult("Bayonetta", "Terry", 4, 1, 60),
    ],
    "Rosalina & Luma": [ # 86th Previously
        MatchResult("Rosalina & Luma", "Mr Game & Watch", 1, 1, 42),
        MatchResult("Rosalina & Luma", "Zelda", 2, 2, 25),
        MatchResult("Rosalina & Luma", "Pyra & Mythra", 3, 2, 114),
    ],
}

#################################################
################### ROUND 3 #####################
#################################################

ROUND_3_RULE = RoundScoringRule(
    round_number=4,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1 + (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_3_MATCHES: dict[str, list[MatchResult]] = {
    "Zelda": [ # 1st Previously
        MatchResult("Zelda", "Pikachu", 1, 2, 82),
        MatchResult("Zelda", "King Dedede", 2, 2, 120),
        MatchResult("Zelda", "Lucario", 3, 2, 32),
    ],
    "Min Min": [ # 2nd Previously
        MatchResult("Min Min", "ROB", 1, 2, 163),
        MatchResult("Min Min", "Bowser", 2, 2, 39),
        MatchResult("Min Min", "Captain Falcon", 3, 1, 41),
    ],
    "Lucas": [ # 3rd Previously
        MatchResult("Lucas", "PacMan", 1, 2, 36),
        MatchResult("Lucas", "Richter", 2, 2, 145),
        MatchResult("Lucas", "Ken", 3, 2, 63),
    ],
    "Roy": [ # 4th Previously
        MatchResult("Roy", "Piranha Plant", 1, 2, 26),
        MatchResult("Roy", "Ganondorf", 2, 3, 95),
        MatchResult("Roy", "Hero", 3, 2, 0),
        MatchResult("Roy", "Lucas", 4, 1, 0),
    ],
    "Dark Samus": [ # 5th Previously
        MatchResult("Dark Samus", "Snake", 1, 3, 149),
        MatchResult("Dark Samus", "Meta Knight", 2, 2, 79),
        MatchResult("Dark Samus", "Robin", 3, 1, 0),
    ],
    "Mii Gunner": [ # 6th Previously
        MatchResult("Mii Gunner", "Isabelle", 1, 1, 0),
        MatchResult("Mii Gunner", "Pichu", 2, 1, 0),
        MatchResult("Mii Gunner", "Lucas", 3, 2, 117),
    ],
    "Sephiroth": [ # 7th Previously
        MatchResult("Sephiroth", "Terry", 1, 3, 97),
        MatchResult("Sephiroth", "Daisy", 2, 3, 92),
        MatchResult("Sephiroth", "Ike", 3, 3, 125),
    ],
    "Piranha Plant": [ # 8th Previously
        MatchResult("Piranha Plant", "Min Min", 1, 2, 57),
        MatchResult("Piranha Plant", "Duck Hunt", 2, 3, 138),
        MatchResult("Piranha Plant", "Kazuya", 3, -1, 0),
    ],
    "Dr Mario": [ # 9th Previously
        MatchResult("Dr Mario", "Ken", 1, 1, 46),
        MatchResult("Dr Mario", "Mega Man", 2, 2, 49),
        MatchResult("Dr Mario", "ROB", 3, 3, 118),
    ],
    "Chrom": [ # 10th Previously
        MatchResult("Chrom", "Diddy Kong", 1, 3, 135),
        MatchResult("Chrom", "Fox", 2, 2, 24),
        MatchResult("Chrom", "Corrin", 3, 2, 109),
    ],
    "Corrin": [ # 11th Previously
        MatchResult("Corrin", "Duck Hunt", 1, 2, 126),
        MatchResult("Corrin", "Hero", 2, 2, 46),
        MatchResult("Corrin", "Shulk", 3, 2, 87),
    ],
    "Incineroar": [ # 12th Previously
        MatchResult("Incineroar", "Lucario", 1, 1, 101),
        MatchResult("Incineroar", "Ike", 2, 2, 13),
        MatchResult("Incineroar", "Samus", 3, 1, 80),
    ],
    "Bowser Jr": [ # 13th Previously
        MatchResult("Bowser Jr", "Banjo & Kazooie", 1, 2, 143),
        MatchResult("Bowser Jr", "Ganondorf", 2, 2, 0),
        MatchResult("Bowser Jr", "PacMan", 3, 2, 0),
    ],
    "Banjo & Kazooie": [ # 14th Previously
        MatchResult("Banjo & Kazooie", "Snake", 1, 2, 92),
        MatchResult("Banjo & Kazooie", "ROB", 2, 2, 37),
        MatchResult("Banjo & Kazooie", "Inkling", 3, 2, 190),
    ],
    "Bowser": [ # 15th Previously
        MatchResult("Bowser", "Link", 1, 2, 116),
        MatchResult("Bowser", "Wario", 2, 3, 92),
        MatchResult("Bowser", "ROB", 3, 2, 0),
        MatchResult("Bowser", "Captain Falcon", 4, 2, 36),
    ],
    "Shulk": [ # 16th Previously
        MatchResult("Shulk", "Simon", 1, 2, 60),
        MatchResult("Shulk", "Isabelle", 2, 3, 156),
        MatchResult("Shulk", "Captain Falcon", 3, 1, 131),
    ],
    "Mii Swordfighter": [ # 17th Previously
        MatchResult("Mii Swordfighter", "Jigglypuff", 1, 2, 20),
        MatchResult("Mii Swordfighter", "Villager", 2, -1, 35),
    ],
    "Donkey Kong": [ # 18th Previously
        MatchResult("Donkey Kong", "Hero", 1, 2, 65),
        MatchResult("Donkey Kong", "Wolf", 2, 1, 69),
        MatchResult("Donkey Kong", "Pichu", 3, 3, 107),
    ],
    "King K Rool": [ # 19th Previously
        MatchResult("King K Rool", "Toon Link", 1, 2, 16),
        MatchResult("King K Rool", "Byleth", 2, 2, 165),
        MatchResult("King K Rool", "Captain Falcon", 3, -2, 80),
    ],
    "King Dedede": [ # 20th Previously
        MatchResult("King Dedede", "Isabelle", 1, 2, 158),
        MatchResult("King Dedede", "Bowser Jr", 2, 1, 46),
        MatchResult("King Dedede", "Greninja", 3, 3, 122),
    ],
    "Duck Hunt": [ # 21st Previously
        MatchResult("Duck Hunt", "PacMan", 1, 2, 7),
        MatchResult("Duck Hunt", "Wolf", 2, 2, 137),
        MatchResult("Duck Hunt", "Luigi", 3, 1, 16),
    ],
    "Robin": [ # 22nd Previously
        MatchResult("Robin", "Olimar", 1, 2, 128),
        MatchResult("Robin", "Sephiroth", 2, 2, 153),
        MatchResult("Robin", "Banjo & Kazooie", 3, 1, 38),
        MatchResult("Robin", "Link", 4, 1, 16),
    ],
    "Olimar": [ # 23rd Previously
        MatchResult("Olimar", "Pikachu", 1, 3, 176),
        MatchResult("Olimar", "Yoshi", 2, 3, 124),
        MatchResult("Olimar", "Palutena", 3, 1, 52),
    ],
    "Sora": [ # 24th Previously
        MatchResult("Sora", "Wolf", 1, 1, 32),
        MatchResult("Sora", "Steve", 2, 2, 103),
        MatchResult("Sora", "Sonic", 3, 2, 17),
    ],
    "PacMan": [ # 25th Previously
        MatchResult("PacMan", "Banjo & Kazooie", 1, 2, 25),
        MatchResult("PacMan", "Lucario", 2, 2, 0),
        MatchResult("PacMan", "Wii Fit Trainer", 3, 2, 0),
    ],
    "Ridley": [ # 26th Previously
        MatchResult("Ridley", "Ike", 1, 2, 142),
        MatchResult("Ridley", "Wii Fit Trainer", 2, 3, 141),
        MatchResult("Ridley", "Min Min", 3, 1, 113),
    ],
    "Toon Link": [ # 27th Previously
        MatchResult("Toon Link", "Banjo & Kazooie", 1, 2, 116),
        MatchResult("Toon Link", "Ken", 2, 2, 63),
        MatchResult("Toon Link", "Dr Mario", 3, 3, 152),
        MatchResult("Toon Link", "Captain Falcon", 4, -1, 52),
    ],
    "Ike": [ # 28th Previously
        MatchResult("Ike", "Ganondorf", 1, 2, 53),
        MatchResult("Ike", "Hero", 2, 1, 0),
        MatchResult("Ike", "Mewtwo", 3, 1, 0),
    ],
    "Hero": [ # 29th Previously
        MatchResult("Hero", "Palutena", 1, 3, 175),
        MatchResult("Hero", "PacMan", 2, 3, 85),
        MatchResult("Hero", "Mr Game & Watch", 3, 1, 0),
    ],
    "Jigglypuff": [ # 30th Previously
        MatchResult("Jigglypuff", "Ridley", 1, 1, 59),
        MatchResult("Jigglypuff", "Lucas", 2, -1, 121),
    ],
    "Ganondorf": [ # 31st Previously
        MatchResult("Ganondorf", "Meta Knight", 1, 1, 0),
        MatchResult("Ganondorf", "Duck Hunt", 2, 2, 114),
        MatchResult("Ganondorf", "Lucina", 3, 2, 0),
        MatchResult("Ganondorf", "Terry", 4, 2, 181),
    ],
    "Wolf": [ # 32nd Previously
        MatchResult("Wolf", "Wii Fit Trainer", 1, 3, 108),
        MatchResult("Wolf", "Marth", 2, 2, 125),
        MatchResult("Wolf", "Shulk", 3, 3, 151),
        MatchResult("Wolf", "Ganondorf", 5, 3, 55),
    ],
    "Ice Climbers": [ # 33rd Previously
        MatchResult("Ice Climbers", "Joker", 1, 2, 19),
        MatchResult("Ice Climbers", "Jigglypuff", 2, 2, 105),
        MatchResult("Ice Climbers", "ROB", 3, 3, 152),
    ],
    "Yoshi": [ # 34th Previously
        MatchResult("Yoshi", "Marth", 1, 1, 70),
        MatchResult("Yoshi", "Sonic", 2, 2, 47),
        MatchResult("Yoshi", "Roy", 3, 3, 109),
    ],
    "Cloud": [ # 35th Previously
        MatchResult("Cloud", "Dr Mario", 1, 1, 119),
        MatchResult("Cloud", "Mr Game & Watch", 2, 2, 65),
        MatchResult("Cloud", "Zero Suit Samus", 3, 3, 66),
    ],
    "Kirby": [ # 36th Previously
        MatchResult("Kirby", "Peach", 1, 3, 90),
        MatchResult("Kirby", "Captain Falcon", 2, 1, 117),
        MatchResult("Kirby", "Duck Hunt", 3, 2, 51),
    ],
    "Terry": [ # 37th Previously
        MatchResult("Terry", "Pyra & Mythra", 1, 3, 149),
        MatchResult("Terry", "Mega Man", 2, 3, 155),
        MatchResult("Terry", "Pikachu", 3, 2, 42),
        MatchResult("Terry", "Meta Knight", 5, 1, 7),
    ],
    "Mr Game & Watch": [ # 38th Previously
        MatchResult("Mr Game & Watch", "Simon", 1, 2, 16),
        MatchResult("Mr Game & Watch", "Wolf", 2, 1, 111),
        MatchResult("Mr Game & Watch", "Ness", 3, 1, 0),
    ],
    "Joker": [ # 39th Previously
        MatchResult("Joker", "Samus", 1, 3, 150),
        MatchResult("Joker", "Ness", 2, -1, 87),
    ],
    "Pit": [ # 40th Previously
        MatchResult("Pit", "Toon Link", 1, 2, 34),
        MatchResult("Pit", "Shulk", 2, 2, 142),
        MatchResult("Pit", "Roy", 3, 2, 0),
    ],
    "Peach": [ # 41st Previously
        MatchResult("Peach", "Inkling", 1, -1, 50),
    ],
    "Young Link": [ # 42nd Previously
        MatchResult("Young Link", "Falco", 1, 3, 151),
        MatchResult("Young Link", "Pyra & Mythra", 2, 3, 163),
        MatchResult("Young Link", "Diddy Kong", 3, 2, 50),
        MatchResult("Young Link", "Daisy", 4, 2, 79),
    ],
    "Mario": [ # 43rd Previously
        MatchResult("Mario", "Peach", 1, 1, 49),
        MatchResult("Mario", "Palutena", 2, 1, 87),
        MatchResult("Mario", "Zero Suit Samus", 3, 1, 99),
        MatchResult("Mario", "Lucas", 4, 2, 71),
    ],
    "Greninja": [ # 44th Previously
        MatchResult("Greninja", "Robin", 1, 2, 34),
        MatchResult("Greninja", "Ryu", 2, 2, 112),
        MatchResult("Greninja", "Sheik", 3, 2, 53),
    ],
    "Wii Fit Trainer": [ # 45th Previously
        MatchResult("Wii Fit Trainer", "Daisy", 1, -1, 73),
    ],
    "Dark Pit": [ # 46th Previously
        MatchResult("Dark Pit", "Pichu", 1, 2, 81),
        MatchResult("Dark Pit", "Wario", 2, 2, 88),
        MatchResult("Dark Pit", "Roy", 3, 2, 35),
        MatchResult("Dark Pit", "Captain Falcon", 5, 2, 92),
    ],
    "Sheik": [ # 47th Previously
        MatchResult("Sheik", "Greninja", 1, 2, 21),
        MatchResult("Sheik", "Steve", 2, -1, 121),
    ],
    "Inkling": [ # 48th Previously
        MatchResult("Inkling", "Wii Fit Trainer", 1, 1, 39),
        MatchResult("Inkling", "Wario", 2, 2, 99),
        MatchResult("Inkling", "Pyra & Mythra", 3, 1, 14),
    ],
    "Luigi": [ # 49th Previously
        MatchResult("Luigi", "Steve", 1, 1, 40),
        MatchResult("Luigi", "Rosalina & Luma", 2, 2, 39),
        MatchResult("Luigi", "Snake", 3, 2, 83),
    ],
    "Pokemon Trainer": [ # 50th Previously
        MatchResult("Pokemon Trainer", "Falco", 1, 2, 183),
        MatchResult("Pokemon Trainer", "Kazuya", 2, 1, 152),
        MatchResult("Pokemon Trainer", "Wolf", 3, 1, 33),
    ],
    "Ryu": [ # 51st Previously
        MatchResult("Ryu", "Wario", 1, 1, 45),
        MatchResult("Ryu", "Banjo & Kazooie", 2, 2, 104),
        MatchResult("Ryu", "King Dedede", 3, 1, 81),
    ],
    "Diddy Kong": [ # 52nd Previously
        MatchResult("Diddy Kong", "PacMan", 1, 1, 0),
        MatchResult("Diddy Kong", "Pokemon Trainer", 2, -1, 20),
    ],
    "Simon": [ # 53rd Previously
        MatchResult("Simon", "Joker", 1, 1, 32),
        MatchResult("Simon", "ROB", 2, 2, 80),
        MatchResult("Simon", "Young Link", 3, 1, 0),
    ],
    "Sonic": [ # 54th Previously
        MatchResult("Sonic", "Ice Climbers", 1, 2, 60),
        MatchResult("Sonic", "Meta Knight", 2, 2, 73),
        MatchResult("Sonic", "Roy", 3, 1, 63),
        MatchResult("Sonic", "Ken", 4, 1, 0),
    ],
    "Zero Suit Samus": [ # 55th Previously
        MatchResult("Zero Suit Samus", "Jigglypuff", 1, 1, 20),
        MatchResult("Zero Suit Samus", "King K Rool", 2, -1, 37),
    ],
    "Richter": [ # 56th Previously
        MatchResult("Richter", "Toon Link", 1, 2, 21),
        MatchResult("Richter", "Pikachu", 2, 2, 88),
        MatchResult("Richter", "ROB", 3, 2, 130),
    ],
    "ROB": [ # 57th Previously
        MatchResult("ROB", "King Dedede", 1, 1, 0),
        MatchResult("ROB", "Little Mac", 2, -1, 0),
    ],
    "Lucina": [ # 58th Previously
        MatchResult("Lucina", "Peach", 1, 3, 160),
        MatchResult("Lucina", "Min Min", 2, 2, 51),
        MatchResult("Lucina", "Roy", 3, 1, 0),
    ],
    "Ken": [ # 59th Previously
        MatchResult("Ken", "Mewtwo", 1, 1, 106),
        MatchResult("Ken", "Byleth", 2, 1, 75),
        MatchResult("Ken", "Pikachu", 3, 1, 82),
    ],
    "Captain Falcon": [ # 60th Previously
        MatchResult("Captain Falcon", "Meta Knight", 1, 1, 126),
        MatchResult("Captain Falcon", "Jigglypuff", 2, 2, 105),
        MatchResult("Captain Falcon", "Lucario", 3, 1, 133),
    ],
    "Pyra & Mythra": [ # 61st Previously
        MatchResult("Pyra & Mythra", "Jigglypuff", 1, 3, 153),
        MatchResult("Pyra & Mythra", "Sora", 2, 1, 0),
        MatchResult("Pyra & Mythra", "Meta Knight", 3, -1, 17),
    ],
    "Samus": [ # 62nd Previously
        MatchResult("Samus", "Duck Hunt", 1, 2, 104),
        MatchResult("Samus", "Diddy Kong", 2, 2, 121),
        MatchResult("Samus", "Isabelle", 3, 2, 88),
        MatchResult("Samus", "Robin", 4, 1, 143),
    ],
    "Link": [ # 63rd Previously
        MatchResult("Link", "Ganondorf", 1, 2, 114),
        MatchResult("Link", "Pikachu", 2, 2, 48),
        MatchResult("Link", "Greninja", 3, 3, 45),
    ],
    "Isabelle": [ # 64th Previously
        MatchResult("Isabelle", "Corrin", 1, 1, 14),
        MatchResult("Isabelle", "Ryu", 2, 2, 57),
        MatchResult("Isabelle", "Pokemon Trainer", 3, 2, 59),
    ],
    "Wario": [ # 65th Previously
        MatchResult("Wario", "Sonic", 1, 1, 0),
        MatchResult("Wario", "Ice Climbers", 2, 2, 80),
        MatchResult("Wario", "Link", 3, -1, 76),
    ],
    "Little Mac": [ # 66th Previously
        MatchResult("Little Mac", "Palutena", 1, 2, 34),
        MatchResult("Little Mac", "Fox", 2, 2, 66),
        MatchResult("Little Mac", "Wario", 3, 2, 76),
    ],
    "Mii Brawler": [ # 67th Previously
        MatchResult("Mii Brawler", "Wii Fit Trainer", 1, 3, 97),
        MatchResult("Mii Brawler", "Robin", 2, 2, 90),
        MatchResult("Mii Brawler", "Ridley", 3, 1, 105),
    ],
    "Mega Man": [ # 68th Previously
        MatchResult("Mega Man", "Bowser", 1, 2, 152),
        MatchResult("Mega Man", "Captain Falcon", 2, 1, 124),
        MatchResult("Mega Man", "Peach", 3, 1, 134),
    ],
    "Fox": [ # 69th Previously
        MatchResult("Fox", "Robin", 1, -2, 101),
    ],
    "Villager": [ # 70th Previously
        MatchResult("Villager", "Duck Hunt", 1, 2, 12),
        MatchResult("Villager", "Banjo & Kazooie", 2, 2, 0),
        MatchResult("Villager", "Little Mac", 3, 2, 61),
    ],
    "Meta Knight": [ # 71st Previously
        MatchResult("Meta Knight", "Richter", 1, 2, 103),
        MatchResult("Meta Knight", "Dark Samus", 2, 2, 43),
        MatchResult("Meta Knight", "Dr Mario", 3, 3, 122),
    ],
    "Mewtwo": [ # 72nd Previously
        MatchResult("Mewtwo", "Lucina", 1, 2, 0),
        MatchResult("Mewtwo", "Joker", 2, 2, 65),
        MatchResult("Mewtwo", "Ganondorf", 3, 1, 101),
    ],
}

#################################################
################ ELIMINATION 2 ##################
#################################################

ELIMINATION_2_RULE = RoundScoringRule(
    round_number=5,
    max_percentage=175,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1.25 + (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ELIMINATION_2_RANK_START = 57
ELIMINATION_2_RANK_END = 80
ELIMINATION_2_RECALC_RANK_END = 71
ELIMINATION_2_ENTRY_EXPONENT = 0.8037
ROUND_4_SETUP_EXPONENT = 0.814

ELIMINATION_2_MATCHES: dict[str, list[MatchResult]] = {
    "Captain Falcon": [ # 57th Previously
        MatchResult("Captain Falcon", "Lucina", 1, 2, 63),
        MatchResult("Captain Falcon", "PacMan", 2, 1, 11),
        MatchResult("Captain Falcon", "Wario", 3, -1, 117),
    ],
    "Ken": [ # 58th Previously
        MatchResult("Ken", "Greninja", 1, 3, 111),
        MatchResult("Ken", "Inkling", 2, -2, 39),
    ],
    "King K Rool": [ # 59th Previously
        MatchResult("King K Rool", "Bayonetta", 1, 3, 146),
        MatchResult("King K Rool", "Steve", 2, 3, 163),
        MatchResult("King K Rool", "Sonic", 3, 3, 172),
    ],
    "Wario": [ # 60th Previously
        MatchResult("Wario", "Ridley", 1, 2, 79),
        MatchResult("Wario", "Samus", 2, 2, 85),
        MatchResult("Wario", "Inkling", 3, 1, 42),
    ],
    "Mega Man": [ # 61st Previously
        MatchResult("Mega Man", "Samus", 1, -1, 106),
    ],
    "Pyra & Mythra": [ # 62nd Previously
        MatchResult("Pyra & Mythra", "Incineroar", 1, 3, 125),
        MatchResult("Pyra & Mythra", "Sephiroth", 2, 3, 63),
        MatchResult("Pyra & Mythra", "King K Rool", 3, 2, 64),
    ],
    "Mii Swordfighter": [ # 63rd Previously
        MatchResult("Mii Swordfighter", "Lucas", 1, 1, 0),
        MatchResult("Mii Swordfighter", "Ryu", 2, 2, 78),
        MatchResult("Mii Swordfighter", "Wolf", 3, 2, 94),
    ],
    "Joker": [ # 64th Previously
        MatchResult("Joker", "Isabelle", 1, 2, 80),
        MatchResult("Joker", "Peach", 2, 2, 43),
        MatchResult("Joker", "Wii Fit Trainer", 3, 2, 48),
    ],
    "Sheik": [ # 65th Previously
        MatchResult("Sheik", "Dr Mario", 1, 1, 84),
        MatchResult("Sheik", "Corrin", 2, 2, 110),
        MatchResult("Sheik", "Ike", 3, 2, 55),
    ],
    "Jigglypuff": [ # 66th Previously
        MatchResult("Jigglypuff", "Bowser Jr", 1, -1, 131),
    ],
    "Diddy Kong": [ # 67th Previously
        MatchResult("Diddy Kong", "Bowser", 1, 3, 114),
        MatchResult("Diddy Kong", "Rosalina & Luma", 2, 2, 57),
        MatchResult("Diddy Kong", "Wario", 3, 2, 68),
    ],
    "Zero Suit Samus": [ # 68th Previously
        MatchResult("Zero Suit Samus", "Robin", 1, 2, 123),
        MatchResult("Zero Suit Samus", "Cloud", 2, 1, 9),
        MatchResult("Zero Suit Samus", "Diddy Kong", 3, 2, 0),
    ],
    "ROB": [ # 69th Previously
        MatchResult("ROB", "Dr Mario", 1, 2, 94),
        MatchResult("ROB", "Robin", 2, 1, 36),
        MatchResult("ROB", "Ice Climbers", 3, 2, 129),
    ],
    "Peach": [ # 70th Previously
        MatchResult("Peach", "Peach", 1, 2, 122),
        MatchResult("Peach", "Chrom", 2, 2, 56),
        MatchResult("Peach", "Lucas", 3, 1, 10),
    ],
    "Wii Fit Trainer": [ # 71st Previously
        MatchResult("Wii Fit Trainer", "Lucina", 1, 2, 136),
        MatchResult("Wii Fit Trainer", "Sheik", 2, 2, 33),
        MatchResult("Wii Fit Trainer", "Roy", 3, 2, 6),
        MatchResult("Wii Fit Trainer", "Wolf", 4, -1, 17),
    ],
    "Pichu": [ # 72nd Previously
        MatchResult("Pichu", "Link", 1, 2, 110),
        MatchResult("Pichu", "Ken", 2, 2, 78),
        MatchResult("Pichu", "Falco", 3, 2, 121),
        MatchResult("Pichu", "Isabelle", 4, 2, 112),
    ],
    "Ness": [ # 73rd Previously
        MatchResult("Ness", "Sonic", 1, 2, 79),
        MatchResult("Ness", "Jigglypuff", 2, 3, 128),
        MatchResult("Ness", "Little Mac", 3, -1, 67),
    ],
    "Lucario": [ # 74th Previously
        MatchResult("Lucario", "Diddy Kong", 1, 2, 110),
        MatchResult("Lucario", "Banjo & Kazooie", 2, 1, 87),
        MatchResult("Lucario", "Toon Link", 3, 2, 117),
    ],
    "Snake": [ # 75th Previously
        MatchResult("Snake", "Pichu", 1, 1, 55),
        MatchResult("Snake", "Chrom", 2, 2, 44),
        MatchResult("Snake", "ROB", 3, 1, 37),
    ],
    "Rosalina & Luma": [ # 76th Previously
        MatchResult("Rosalina & Luma", "Duck Hunt", 1, 1, 96),
        MatchResult("Rosalina & Luma", "Snake", 2, 2, 42),
        MatchResult("Rosalina & Luma", "Kazuya", 3, 2, 121),
        MatchResult("Rosalina & Luma", "Wario", 4, 2, 81),
    ],
    "Fox": [ # 77th Previously
        MatchResult("Fox", "Zero Suit Samus", 1, 2, 55),
        MatchResult("Fox", "Sephiroth", 2, 2, 82),
        MatchResult("Fox", "Steve", 3, -1, 84),
    ],
    "Bayonetta": [ # 78th Previously
        MatchResult("Bayonetta", "Kirby", 1, 3, 154),
        MatchResult("Bayonetta", "Wii Fit Trainer", 2, 1, 10),
        MatchResult("Bayonetta", "Pokemon Trainer", 3, 2, 0),
    ],
    "Byleth": [ # 79th Previously
        MatchResult("Byleth", "Mr Game & Watch", 1, 3, 84),
        MatchResult("Byleth", "Young Link", 2, 1, 12),
        MatchResult("Byleth", "Ganondorf", 3, 1, 0),
        MatchResult("Byleth", "Little Mac", 4, 1, 92),
    ],
    "Palutena": [ # 80th Previously
        MatchResult("Palutena", "Snake", 1, 2, 32),
        MatchResult("Palutena", "Richter", 2, 1, 78),
        MatchResult("Palutena", "Corrin", 3, 2, 64),
    ],
}

#################################################
################### ROUND 4 #####################
#################################################

ROUND_4_RULE = RoundScoringRule(
    round_number=5,
    max_percentage=175,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1.33 + (m - 1) / 3,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_4_MATCHES: dict[str, list[MatchResult]] = {
    'Bowser': [ # 1st Previously
        MatchResult('Bowser', "Bowser", 1, 0, 0),
        MatchResult('Bowser', "Bowser", 2, 0, 0),
        MatchResult('Bowser', "Bowser", 3, 0, 0),
    ],
    'Sephiroth': [ # 2nd Previously
        MatchResult('Sephiroth', "Bowser", 1, 0, 0),
        MatchResult('Sephiroth', "Bowser", 2, 1, 0),
        MatchResult('Sephiroth', "Bowser", 3, 1, 0),
    ],
    'Roy': [ # 3rd Previously
        MatchResult('Roy', "Bowser", 1, 1, 0),
        MatchResult('Roy', "Bowser", 2, 0, 0),
        MatchResult('Roy', "Bowser", 3, 3, 0),
    ],
    'Dr Mario': [ # 4th Previously
        MatchResult('Dr Mario', "Bowser", 1, 0, 0),
        MatchResult('Dr Mario', "Bowser", 2, 0, 0),
        MatchResult('Dr Mario', "Bowser", 3, 0, 0),
    ],
    'Young Link': [ # 5th Previously
        MatchResult('Young Link', "Bowser", 1, 0, 0),
        MatchResult('Young Link', "Bowser", 2, 0, 0),
        MatchResult('Young Link', "Bowser", 3, 0, 0),
    ],
    'Chrom': [ # 6th Previously
        MatchResult('Chrom', "Bowser", 1, 0, 0),
        MatchResult('Chrom', "Bowser", 2, 0, 0),
        MatchResult('Chrom', "Bowser", 3, 0, 0),
    ],
    'Wolf': [ # 7th Previously
        MatchResult('Wolf', "Bowser", 1, 0, 0),
        MatchResult('Wolf', "Bowser", 2, 0, 0),
        MatchResult('Wolf', "Bowser", 3, 0, 0),
    ],
    'Ice Climbers': [ # 8th Previously
        MatchResult('Ice Climbers', "Bowser", 1, 0, 0),
        MatchResult('Ice Climbers', "Bowser", 2, 0, 0),
        MatchResult('Ice Climbers', "Bowser", 3, 0, 0),
    ],
    'Bowser Jr': [ # 9th Previously
        MatchResult('Bowser Jr', "Bowser", 1, 0, 0),
        MatchResult('Bowser Jr', "Bowser", 2, 0, 0),
        MatchResult('Bowser Jr', "Bowser", 3, 0, 0),
    ],
    'PacMan': [ # 10th Previously
        MatchResult('PacMan', "Bowser", 1, 0, 0),
        MatchResult('PacMan', "Bowser", 2, 0, 0),
        MatchResult('PacMan', "Bowser", 3, 0, 0),
    ],
    'Terry': [ # 11th Previously
        MatchResult('Terry', "Bowser", 1, 0, 0),
        MatchResult('Terry', "Bowser", 2, 0, 0),
        MatchResult('Terry', "Bowser", 3, 0, 0),
    ],
    'Toon Link': [ # 12th Previously
        MatchResult('Toon Link', "Bowser", 1, 0, 0),
        MatchResult('Toon Link', "Bowser", 2, 0, 0),
        MatchResult('Toon Link', "Bowser", 3, 0, 0),
    ],
    'Zelda': [ # 13th Previously
        MatchResult('Zelda', "Bowser", 1, 0, 0),
        MatchResult('Zelda', "Bowser", 2, 0, 0),
        MatchResult('Zelda', "Bowser", 3, 0, 0),
    ],
    'Yoshi': [ # 14th Previously
        MatchResult('Yoshi', "Bowser", 1, 0, 0),
        MatchResult('Yoshi', "Bowser", 2, 0, 0),
        MatchResult('Yoshi', "Bowser", 3, 0, 0),
    ],
    'Lucas': [ # 15th Previously
        MatchResult('Lucas', "Bowser", 1, 0, 0),
        MatchResult('Lucas', "Bowser", 2, 0, 0),
        MatchResult('Lucas', "Bowser", 3, 0, 0),
    ],
    'Pit': [ # 16th Previously
        MatchResult('Pit', "Bowser", 1, 0, 0),
        MatchResult('Pit', "Bowser", 2, 0, 0),
        MatchResult('Pit', "Bowser", 3, 0, 0),
    ],
    'Dark Pit': [ # 17th Previously
        MatchResult('Dark Pit', "Bowser", 1, 0, 0),
        MatchResult('Dark Pit', "Bowser", 2, 0, 0),
        MatchResult('Dark Pit', "Bowser", 3, 0, 0),
    ],
    'King Dedede': [ # 18th Previously
        MatchResult('King Dedede', "Bowser", 1, 0, 0),
        MatchResult('King Dedede', "Bowser", 2, 0, 0),
        MatchResult('King Dedede', "Bowser", 3, 0, 0),
    ],
    'Link': [ # 19th Previously
        MatchResult('Link', "Bowser", 1, 0, 0),
        MatchResult('Link', "Bowser", 2, 0, 0),
        MatchResult('Link', "Bowser", 3, 0, 0),
    ],
    'Donkey Kong': [ # 20th Previously
        MatchResult('Donkey Kong', "Bowser", 1, 0, 0),
        MatchResult('Donkey Kong', "Bowser", 2, 0, 0),
        MatchResult('Donkey Kong', "Bowser", 3, 0, 0),
    ],
    'Cloud': [ # 21st Previously
        MatchResult('Cloud', "Bowser", 1, 0, 0),
        MatchResult('Cloud', "Bowser", 2, 0, 0),
        MatchResult('Cloud', "Bowser", 3, 0, 0),
    ],
    'Dark Samus': [ # 22nd Previously
        MatchResult('Dark Samus', "Bowser", 1, 0, 0),
        MatchResult('Dark Samus', "Bowser", 2, 0, 0),
        MatchResult('Dark Samus', "Bowser", 3, 0, 0),
    ],
    'Corrin': [ # 23rd Previously
        MatchResult('Corrin', "Bowser", 1, 0, 0),
        MatchResult('Corrin', "Bowser", 2, 0, 0),
        MatchResult('Corrin', "Bowser", 3, 0, 0),
    ],
    'Ganondorf': [ # 24th Previously
        MatchResult('Ganondorf', "Bowser", 1, 0, 0),
        MatchResult('Ganondorf', "Bowser", 2, 0, 0),
        MatchResult('Ganondorf', "Bowser", 3, 0, 0),
    ],
    'Sora': [ # 25th Previously
        MatchResult('Sora', "Bowser", 1, 0, 0),
        MatchResult('Sora', "Bowser", 2, 0, 0),
        MatchResult('Sora', "Bowser", 3, 0, 0),
    ],
    'Banjo & Kazooie': [ # 26th Previously
        MatchResult('Banjo & Kazooie', "Bowser", 1, 0, 0),
        MatchResult('Banjo & Kazooie', "Bowser", 2, 0, 0),
        MatchResult('Banjo & Kazooie', "Bowser", 3, 0, 0),
    ],
    'Hero': [ # 27th Previously
        MatchResult('Hero', "Bowser", 1, 0, 0),
        MatchResult('Hero', "Bowser", 2, 0, 0),
        MatchResult('Hero', "Bowser", 3, 0, 0),
    ],
    'Little Mac': [ # 28th Previously
        MatchResult('Little Mac', "Bowser", 1, 0, 0),
        MatchResult('Little Mac', "Bowser", 2, 0, 0),
        MatchResult('Little Mac', "Bowser", 3, 0, 0),
    ],
    'Meta Knight': [ # 29th Previously
        MatchResult('Meta Knight', "Bowser", 1, 0, 0),
        MatchResult('Meta Knight', "Bowser", 2, 0, 0),
        MatchResult('Meta Knight', "Bowser", 3, 0, 0),
    ],
    'Olimar': [ # 30th Previously
        MatchResult('Olimar', "Bowser", 1, 0, 0),
        MatchResult('Olimar', "Bowser", 2, 0, 0),
        MatchResult('Olimar', "Bowser", 3, 0, 0),
    ],
    'Greninja': [ # 31st Previously
        MatchResult('Greninja', "Bowser", 1, 0, 0),
        MatchResult('Greninja', "Bowser", 2, 0, 0),
        MatchResult('Greninja', "Bowser", 3, 0, 0),
    ],
    'Robin': [ # 32nd Previously
        MatchResult('Robin', "Bowser", 1, 0, 0),
        MatchResult('Robin', "Bowser", 2, 0, 0),
        MatchResult('Robin', "Bowser", 3, 0, 0),
    ],
    'Min Min': [ # 33rd Previously
        MatchResult('Min Min', "Bowser", 1, 0, 0),
        MatchResult('Min Min', "Bowser", 2, 0, 0),
        MatchResult('Min Min', "Bowser", 3, 0, 0),
    ],
    'Richter': [ # 34th Previously
        MatchResult('Richter', "Bowser", 1, 0, 0),
        MatchResult('Richter', "Bowser", 2, 0, 0),
        MatchResult('Richter', "Bowser", 3, 0, 0),
    ],
    'Kirby': [ # 35th Previously
        MatchResult('Kirby', "Bowser", 1, 0, 0),
        MatchResult('Kirby', "Bowser", 2, 0, 0),
        MatchResult('Kirby', "Bowser", 3, 0, 0),
    ],
    'Mii Gunner': [ # 36th Previously
        MatchResult('Mii Gunner', "Bowser", 1, 0, 0),
        MatchResult('Mii Gunner', "Bowser", 2, 0, 0),
        MatchResult('Mii Gunner', "Bowser", 3, 0, 0),
    ],
    'Luigi': [ # 37th Previously
        MatchResult('Luigi', "Bowser", 1, 0, 0),
        MatchResult('Luigi', "Bowser", 2, 0, 0),
        MatchResult('Luigi', "Bowser", 3, 0, 0),
    ],
    'Duck Hunt': [ # 38th Previously
        MatchResult('Duck Hunt', "Bowser", 1, 0, 0),
        MatchResult('Duck Hunt', "Bowser", 2, 0, 0),
        MatchResult('Duck Hunt', "Bowser", 3, 0, 0),
    ],
    'Shulk': [ # 39th Previously
        MatchResult('Shulk', "Bowser", 1, 0, 0),
        MatchResult('Shulk', "Bowser", 2, 0, 0),
        MatchResult('Shulk', "Bowser", 3, 0, 0),
    ],
    'Ridley': [ # 40th Previously
        MatchResult('Ridley', "Bowser", 1, 0, 0),
        MatchResult('Ridley', "Bowser", 2, 0, 0),
        MatchResult('Ridley', "Bowser", 3, 0, 0),
    ],
    'Lucina': [ # 41st Previously
        MatchResult('Lucina', "Bowser", 1, 0, 0),
        MatchResult('Lucina', "Bowser", 2, 0, 0),
        MatchResult('Lucina', "Bowser", 3, 0, 0),
    ],
    'Isabelle': [ # 42nd Previously
        MatchResult('Isabelle', "Bowser", 1, 0, 0),
        MatchResult('Isabelle', "Bowser", 2, 0, 0),
        MatchResult('Isabelle', "Bowser", 3, 0, 0),
    ],
    'Incineroar': [ # 43rd Previously
        MatchResult('Incineroar', "Bowser", 1, 0, 0),
        MatchResult('Incineroar', "Bowser", 2, 0, 0),
        MatchResult('Incineroar', "Bowser", 3, 0, 0),
    ],
    'Samus': [ # 44th Previously
        MatchResult('Samus', "Bowser", 1, 0, 0),
        MatchResult('Samus', "Bowser", 2, 0, 0),
        MatchResult('Samus', "Bowser", 3, 0, 0),
    ],
    'Ike': [ # 45th Previously
        MatchResult('Ike', "Bowser", 1, 0, 0),
        MatchResult('Ike', "Bowser", 2, 0, 0),
        MatchResult('Ike', "Bowser", 3, 0, 0),
    ],
    'Sonic': [ # 46th Previously
        MatchResult('Sonic', "Bowser", 1, 0, 0),
        MatchResult('Sonic', "Bowser", 2, 0, 0),
        MatchResult('Sonic', "Bowser", 3, 0, 0),
    ],
    'Villager': [ # 47th Previously
        MatchResult('Villager', "Bowser", 1, 0, 0),
        MatchResult('Villager', "Bowser", 2, 0, 0),
        MatchResult('Villager', "Bowser", 3, 0, 0),
    ],
    'Simon': [ # 48th Previously
        MatchResult('Simon', "Bowser", 1, 0, 0),
        MatchResult('Simon', "Bowser", 2, 0, 0),
        MatchResult('Simon', "Bowser", 3, 0, 0),
    ],
    'Inkling': [ # 49th Previously
        MatchResult('Inkling', "Bowser", 1, 0, 0),
        MatchResult('Inkling', "Bowser", 2, 0, 0),
        MatchResult('Inkling', "Bowser", 3, 0, 0),
    ],
    'Mii Brawler': [ # 50th Previously
        MatchResult('Mii Brawler', "Bowser", 1, 0, 0),
        MatchResult('Mii Brawler', "Bowser", 2, 0, 0),
        MatchResult('Mii Brawler', "Bowser", 3, 0, 0),
    ],
    'Piranha Plant': [ # 51st Previously
        MatchResult('Piranha Plant', "Bowser", 1, 0, 0),
        MatchResult('Piranha Plant', "Bowser", 2, 0, 0),
        MatchResult('Piranha Plant', "Bowser", 3, 0, 0),
    ],
    'Mr Game & Watch': [ # 52nd Previously
        MatchResult('Mr Game & Watch', "Bowser", 1, 0, 0),
        MatchResult('Mr Game & Watch', "Bowser", 2, 0, 0),
        MatchResult('Mr Game & Watch', "Bowser", 3, 0, 0),
    ],
    'Mewtwo': [ # 53rd Previously
        MatchResult('Mewtwo', "Bowser", 1, 0, 0),
        MatchResult('Mewtwo', "Bowser", 2, 0, 0),
        MatchResult('Mewtwo', "Bowser", 3, 0, 0),
    ],
    'Ryu': [ # 54th Previously
        MatchResult('Ryu', "Bowser", 1, 0, 0),
        MatchResult('Ryu', "Bowser", 2, 0, 0),
        MatchResult('Ryu', "Bowser", 3, 0, 0),
    ],
    'Mario': [ # 55th Previously
        MatchResult('Mario', "Bowser", 1, 0, 0),
        MatchResult('Mario', "Bowser", 2, 0, 0),
        MatchResult('Mario', "Bowser", 3, 0, 0),
    ],
    'Pokemon Trainer': [ # 56th Previously
        MatchResult('Pokemon Trainer', "Bowser", 1, 0, 0),
        MatchResult('Pokemon Trainer', "Bowser", 2, 0, 0),
        MatchResult('Pokemon Trainer', "Bowser", 3, 0, 0),
    ],
    'King K Rool': [ # 57th Previously
        MatchResult('King K Rool', "Bowser", 1, 0, 0),
        MatchResult('King K Rool', "Bowser", 2, 0, 0),
        MatchResult('King K Rool', "Bowser", 3, 0, 0),
    ],
    'Pyra & Mythra': [ # 58th Previously
        MatchResult('Pyra & Mythra', "Bowser", 1, 0, 0),
        MatchResult('Pyra & Mythra', "Bowser", 2, 0, 0),
        MatchResult('Pyra & Mythra', "Bowser", 3, 0, 0),
    ],
    'Diddy Kong': [ # 59th Previously
        MatchResult('Diddy Kong', "Bowser", 1, 0, 0),
        MatchResult('Diddy Kong', "Bowser", 2, 0, 0),
        MatchResult('Diddy Kong', "Bowser", 3, 0, 0),
    ],
    'Mii Swordfighter': [ # 60th Previously
        MatchResult('Mii Swordfighter', "Bowser", 1, 0, 0),
        MatchResult('Mii Swordfighter', "Bowser", 2, 0, 0),
        MatchResult('Mii Swordfighter', "Bowser", 3, 0, 0),
    ],
    'Joker': [ # 61st Previously
        MatchResult('Joker', "Bowser", 1, 0, 0),
        MatchResult('Joker', "Bowser", 2, 0, 0),
        MatchResult('Joker', "Bowser", 3, 0, 0),
    ],
    'Zero Suit Samus': [ # 62nd Previously
        MatchResult('Zero Suit Samus', "Bowser", 1, 0, 0),
        MatchResult('Zero Suit Samus', "Bowser", 2, 0, 0),
        MatchResult('Zero Suit Samus', "Bowser", 3, 0, 0),
    ],
    'Wario': [ # 63rd Previously
        MatchResult('Wario', "Bowser", 1, 0, 0),
        MatchResult('Wario', "Bowser", 2, 0, 0),
        MatchResult('Wario', "Bowser", 3, 0, 0),
    ],
    'Wii Fit Trainer': [ # 64th Previously
        MatchResult('Wii Fit Trainer', "Bowser", 1, 0, 0),
        MatchResult('Wii Fit Trainer', "Bowser", 2, 0, 0),
        MatchResult('Wii Fit Trainer', "Bowser", 3, 0, 0),
    ],
}

def main() -> None:
    manager = TournamentManager(
        records_dir=RECORDS_DIR,
        reports_dir=REPORTS_DIR,
        ranking_changes_dir=RANKING_CHANGES_DIR,
        matchup_df=MATCHUP_DF,
    )

    # Bootstrap rounds in dependency order: each block runs only if prior data exists.
    round_1_summary: RoundSummary | None = None
    if ROUND_1_MATCHES:
        seed_order = list(ROUND_1_MATCHES.keys())
        round_1_summary = manager.bootstrap_round_from_matches(1, ROUND_1_MATCHES)
        #print("Rebuilt Round 1 from in-file match data.")
        #print(round_1_summary.scores)
        #print_placeholder_only_characters("Round 1", ROUND_1_MATCHES)
        manager._ranking_changes_black_arrows(seed_order, round_1_summary.scores, round_number=1)

    round_2_summary: RoundSummary | None = None
    if round_1_summary is not None and ROUND_2_MATCHES:
        seed_order = [character for character, _score in sorted(round_1_summary.scores.items(), key=lambda item: item[1], reverse=True)]
        round_2_summary = manager.bootstrap_round_from_matches(2, ROUND_2_MATCHES, previous_scores=round_1_summary.scores)
        #print("Rebuilt Round 2 from in-file match data.")
        #print_placeholder_only_characters("Round 2", ROUND_2_MATCHES)
        manager._ranking_changes_black_arrows(seed_order, round_2_summary.scores, round_number=2)

    elim_1_summary: RoundSummary | None = None
    if round_2_summary is not None and ELIMINATION_1_MATCHES:
        reduced_scores = apply_score_reduction(round_2_summary.scores)
        elim_1_summary = manager.bootstrap_round_from_matches(3, ELIMINATION_1_MATCHES, previous_scores=reduced_scores)
        #print("Rebuilt Elimination 1 from in-file match data.")
        #print_placeholder_only_characters("Elimination 1", ELIMINATION_1_MATCHES)

    round_3_summary: RoundSummary | None = None
    if elim_1_summary is not None and ROUND_3_MATCHES:
        elimination_characters = set(ELIMINATION_1_MATCHES.keys())
        round_3_start_scores = apply_selective_score_reduction(elim_1_summary.scores, elimination_characters, exponent=0.53955)
        round_3_summary = manager.bootstrap_round_from_matches(4, ROUND_3_MATCHES, previous_scores=round_3_start_scores)
        #print("Rebuilt Round 3 from in-file match data.")
        print_placeholder_only_characters("Round 3", ROUND_3_MATCHES)

    elim_2_summary: RoundSummary | None = None
    round_4_seed_scores: dict[str, float] | None = None
    if round_3_summary is not None and ELIMINATION_2_MATCHES:
        elimination_2_targets = set(ELIMINATION_2_MATCHES.keys())
        elim_2_start_scores = apply_selective_score_reduction(
            round_3_summary.scores,
            elimination_2_targets,
            exponent=ELIMINATION_2_ENTRY_EXPONENT,
        )
        elim_2_summary = manager.bootstrap_round_from_matches(5, ELIMINATION_2_MATCHES, previous_scores=elim_2_start_scores)
        ordered_elim_2_scores = dict(sorted(elim_2_summary.scores.items(), key=lambda item: item[1], reverse=True))
        #print("Rebuilt Elimination 2 from in-file match data.")
        #print(ordered_elim_2_scores)
        round_4_seed_scores = apply_selective_score_reduction(
            elim_2_summary.scores,
            set(ELIMINATION_2_MATCHES.keys()),
            exponent=ROUND_4_SETUP_EXPONENT,
        )
        ordered_round_4_seed_scores = dict(
            sorted(round_4_seed_scores.items(), key=lambda item: item[1], reverse=True)
        )
        print("Round 4 seed scores after Elimination 2 rescale.")
        print(ordered_round_4_seed_scores)
        #print_placeholder_only_characters("Elimination 2", ELIMINATION_2_MATCHES)

    if round_4_seed_scores is not None and ROUND_4_MATCHES:
        round_4_engine = Round(
            round_number=6,
            matches_by_character=ROUND_4_MATCHES,
            scoring_rule=ROUND_4_RULE,
            matchup_df=MATCHUP_DF,
        )
        round_4_summary = round_4_engine.calculate(round_4_seed_scores, defaultdict(int))
        manager._ranking_changes_round_4(round_4_seed_scores, round_4_summary.scores)

    final_scores = manager.run()
    #print("Tournament rerun complete.")
    #print(final_scores)
    regenerate_analysis_outputs()

if __name__ == "__main__":
    main()


