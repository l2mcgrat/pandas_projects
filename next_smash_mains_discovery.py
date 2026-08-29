# New_Smash_Gods__Discovery_Training (Object-Oriented Rewrite)

from __future__ import annotations

import argparse
import math
import time
import warnings
warnings.filterwarnings("ignore")

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from typing import Callable, Iterable

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
PAGES_REPO_DIR = ROOT.parent / "liammspandasprojects"

# Maps internal sequential round number → semantic filename prefix and display name.
# Pattern: Round 1, Round 2, Elimination 1, Round 3, Elimination 2, Round 4, ...
ROUND_LABEL: dict[int, str] = {
    1: "round_1",
    2: "round_2",
    3: "elimination_1",
    4: "round_3",
    5: "elimination_2",
    6: "round_4",
    7: "elimination_3",
    8: "round_5",
    9: "elimination_4",
    10: "round_6",
    11: "elimination_5",
}
ROUND_DISPLAY: dict[int, str] = {
    1: "Round 1",
    2: "Round 2",
    3: "Elimination 1",
    4: "Round 3",
    5: "Elimination 2",
    6: "Round 4",
    7: "Elimination 3",
    8: "Round 5",
    9: "Elimination 4",
    10: "Round 6",
    11: "Elimination 5",
}
LABEL_TO_ROUND: dict[str, int] = {v: k for k, v in ROUND_LABEL.items()}
ROUND_5_ELIMINATION_3_ENTRY_EXPONENT = 0.8905
ELIMINATION_4_ENTRY_EXPONENT = 0.83
ROUND_6_ELIM4_SELECTIVE_EXPONENT = 0.966
ROUND_6_GLOBAL_EXPONENT = 0.75

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

def apply_score_reduction_custom(scores: dict[str, float], exponent: float) -> dict[str, float]:
    """Reduce all scores to score^exponent."""
    return {char: round(score ** exponent, 3) for char, score in scores.items()}

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
        if matches and all(match.stock_diff == 0 and match.percentage == 0 for match in matches)
    ]

def print_placeholder_only_characters(round_label: str, matches_by_character: dict[str, list[MatchResult]]) -> None:
    characters = placeholder_only_characters(matches_by_character)
    print(f"{round_label} placeholder-only characters: {characters}")

def print_score_window(label: str, scores: dict[str, float], limit: int = 12) -> None:
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    print(f"\n{label} top {min(limit, len(ordered))}:")
    for character, score in ordered[:limit]:
        print(f"  {character}: {score:.3f}")
    print(f"{label} bottom {min(limit, len(ordered))}:")
    for character, score in ordered[-limit:]:
        print(f"  {character}: {score:.3f}")

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

def build_round_5_matches(round_4_scores: dict[str, float], elimination_3_scores: dict[str, float]) -> dict[str, list[MatchResult]]:
    top_48 = rank_window_characters(round_4_scores, 1, 48)
    top_8 = rank_window_characters(elimination_3_scores, 1, 8)
    ordered_characters = top_48 + [character for character in top_8 if character not in top_48]
    return {character: placeholder_round_matches(character, opponent="Bowser Jr") for character in ordered_characters}

def build_round_5_entry_scores(round_4_scores: dict[str, float], elimination_3_scores: dict[str, float]) -> dict[str, float]:
    top_48_round_4 = set(rank_window_characters(round_4_scores, 1, 48))
    entry_scores: dict[str, float] = {}
    for character in ROUND_5_MATCHES:
        if character in top_48_round_4 and character in round_4_scores:
            entry_scores[character] = round(round_4_scores[character], 3)
        elif character in elimination_3_scores:
            entry_scores[character] = round(elimination_3_scores[character] ** ROUND_5_ELIMINATION_3_ENTRY_EXPONENT, 3)
    return entry_scores

def placeholder_round_matches(character: str, opponent: str = "Mario") -> list[MatchResult]:
    return [
        MatchResult(character, opponent, 1, 0, 0),
        MatchResult(character, opponent, 2, 0, 0),
        MatchResult(character, opponent, 3, 0, 0),
    ]


def build_elimination_5_matchup_window(
    round_6_scores: dict[str, float],
    elimination_4_scores: dict[str, float],
    *,
    round_6_start_rank: int = 33,
    round_6_end_rank: int = 48,
    elim_4_start_rank: int = 41,
    elim_4_end_rank: int = 48,
) -> list[str]:
    """Build the Elimination 5 field from the bottom 16 of Round 6 plus the middle 8 from Elimination 4."""
    ordered_round_6 = [
        character for character, _score in sorted(round_6_scores.items(), key=lambda item: item[1], reverse=True)
    ]
    ordered_elim_4 = [
        character for character, _score in sorted(elimination_4_scores.items(), key=lambda item: item[1], reverse=True)
    ]

    selected: list[str] = []
    seen: set[str] = set()

    for character in ordered_round_6[round_6_start_rank - 1:round_6_end_rank]:
        if character not in seen:
            selected.append(character)
            seen.add(character)

    for character in ordered_elim_4[elim_4_start_rank - 1:elim_4_end_rank]:
        if character not in seen:
            selected.append(character)
            seen.add(character)

    return selected


def build_elimination_5_matches(
    round_6_scores: dict[str, float],
    elimination_4_scores: dict[str, float],
    *,
    opponent: str = "Pyra & Mythra",
) -> dict[str, list[MatchResult]]:
    """Construct the Elimination 5 placeholder bracket using the round_6 bottom 16 + Elim 4 middle 8 rule."""
    brackets: dict[str, list[MatchResult]] = {}
    for character in build_elimination_5_matchup_window(round_6_scores, elimination_4_scores):
        brackets[character] = [
            MatchResult(character, opponent, 1, 0, 0),
            MatchResult(character, opponent, 2, 0, 0),
            MatchResult(character, opponent, 3, 0, 0),
        ]
    return brackets


ELIMINATION_5_ENTRY_COEFFICIENT = 1 / 5
ELIMINATION_5_SCORE_MAX = 58.63
ELIMINATION_5_TOTAL_REMAINING = 56


def build_elimination_5_entry_scores(
    round_6_final_ranks: dict[str, int],
    participants: Iterable[str],
    *,
    total_remaining: int = ELIMINATION_5_TOTAL_REMAINING,
    coefficient: float = ELIMINATION_5_ENTRY_COEFFICIENT,
    score_max: float = ELIMINATION_5_SCORE_MAX,
) -> dict[str, float]:
    """Apply the custom entry formula: ((T - rank) / T) * C * S_max, using each character's Round 6 final rank."""
    entry_scores: dict[str, float] = {}
    for character in participants:
        rank = round_6_final_ranks.get(character, total_remaining)
        entry_scores[character] = round(
            ((total_remaining - rank) / total_remaining) * coefficient * score_max,
            3,
        )
    return entry_scores


def round_5_placeholder(character: str) -> list[MatchResult]:
    return [
        MatchResult(character, "Bowser Jr", 1, 0, 0),
        MatchResult(character, "Bowser Jr", 2, 0, 0),
        MatchResult(character, "Bowser Jr", 3, 0, 0),
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


def generate_score_reduction_pareto(
    transitions: list[tuple[str, dict[str, float], dict[str, float]]],
    output_pdf: Path,
) -> None:
    """Multi-page pareto chart of score reductions at each inter-round transition.

    transitions: list of (label, before_scores, after_scores)
    Output saved to output_pdf (one page per transition).
    """
    with PdfPages(output_pdf) as pdf:
        for label, before, after in transitions:
            reductions = {
                c: round(before[c] - after.get(c, before[c]), 6)
                for c in before
                if before[c] - after.get(c, before[c]) > 1e-9
            }
            if not reductions:
                continue

            sorted_chars = sorted(reductions, key=lambda c: reductions[c], reverse=True)
            values = [reductions[c] for c in sorted_chars]
            total = sum(values)
            cumulative = [sum(values[: i + 1]) / total * 100 for i in range(len(values))]

            n = len(sorted_chars)
            fig_width = max(20, n * 0.45)
            fig, ax1 = plt.subplots(figsize=(fig_width, 11), dpi=200)

            norm_vals = [v / max(values) for v in values]
            colors = [plt.cm.RdYlGn_r(nv) for nv in norm_vals]  # type: ignore[attr-defined]
            bars = ax1.bar(range(n), values, color=colors, alpha=0.88)
            ax1.set_ylabel("Score Reduction", fontsize=12)
            ax1.set_xlabel("Character", fontsize=12)
            ax1.set_xticks(range(n))
            ax1.set_xticklabels(sorted_chars, rotation=78, ha="right", fontsize=8)

            ax2 = ax1.twinx()
            ax2.plot(range(n), cumulative, color="#1a1aff", linewidth=2.5, marker="o", markersize=4)
            ax2.set_ylabel("Cumulative Reduction (%)", fontsize=12)
            ax2.set_ylim(0, 105)
            for threshold in [80, 90]:
                ax2.axhline(y=threshold, color="#888888", linestyle="--", linewidth=1)

            y_offset = max(values) * 0.004
            for bar, val in zip(bars, values):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    val + y_offset,
                    f"{val:.3f}",
                    ha="center", va="bottom", fontsize=6, rotation=90,
                )

            plt.title(f"Score Reductions: {label}", fontsize=15, pad=14)
            plt.tight_layout(rect=(0, 0.18, 1, 1))
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

    print(f"Score reductions pareto saved: {output_pdf}")

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
    adjusted_scores: dict[str, float]
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

    def _score_parts(self, match: MatchResult) -> tuple[float, float, float, float, float]:
        cap = self.scoring_rule.max_percentage
        if match.won:
            base_score = match.stock_diff + max(0.0, cap - match.percentage) / cap
        elif match.lost:
            base_score = 1 + match.stock_diff + min(1.0, match.percentage / cap)
        else:
            return 0.0, 1.0, 1.0, 1.0, 1.0
        stage_multiplier = self.scoring_rule.stage_multiplier(match.match_number)
        matchup_multiplier = self._matchup_multiplier(match.character, match.opponent, match.stock_diff)
        late_divisor = match.match_number if self.scoring_rule.late_match_division and match.match_number > self.scoring_rule.early_round_limit else 1.0
        total_multiplier = stage_multiplier * matchup_multiplier / late_divisor
        return base_score, stage_multiplier, matchup_multiplier, late_divisor, total_multiplier

    def calculate_with_records(
        self,
        previous_scores: dict[str, float],
        loss_counter: dict[str, int],
        previous_adjusted_scores: dict[str, float] | None = None,
    ) -> tuple[RoundSummary, pd.DataFrame]:
        scores = dict(previous_scores)
        adjusted_scores = dict(previous_adjusted_scores or previous_scores)
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
            adjusted_running_score = adjusted_scores.get(character, running_score)
            last_real_match: MatchResult | None = None
            for match in matches:
                all_characters.add(match.opponent)
                if match.is_placeholder:
                    continue
                last_real_match = match
                base_score, stage_multiplier, matchup_multiplier, late_divisor, total_multiplier = self._score_parts(match)
                match_score = base_score * total_multiplier
                multiplier_adjusted_score = match_score / total_multiplier if abs(total_multiplier) > 1e-9 else match_score
                running_score += match_score
                adjusted_running_score += multiplier_adjusted_score
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
                        "Base Score": round(base_score, 3),
                        "Stage Multiplier": round(stage_multiplier, 3),
                        "Matchup": round(matchup_multiplier, 3),
                        "Late Match Divisor": round(late_divisor, 3),
                        "Total Multiplier": round(total_multiplier, 3),
                        "Multiplier Adjusted Score": round(multiplier_adjusted_score, 3),
                        "Accumulated_Sum": round(running_score, 3),
                        "Multiplier Adjusted Accumulated Sum": round(adjusted_running_score, 3),
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
            adjusted_scores[character] = round(adjusted_running_score, 3)
        summary = RoundSummary(
            round_number=self.round_number,
            scores=scores,
            adjusted_scores=adjusted_scores,
            win_loses=win_loses,
            characters_played=characters_played,
            all_characters=all_characters,
            losses_received=dict(loss_counter),
        )
        records_df = pd.DataFrame(
            record_rows,
            columns=["Character", "Opponent", "Round", "Win", "Loss", "Stock Diff", "Percentage", "Score", "Base Score", "Stage Multiplier", "Matchup", "Late Match Divisor", "Total Multiplier", "Multiplier Adjusted Score", "Accumulated_Sum", "Multiplier Adjusted Accumulated Sum"],
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
        rules[6] = ROUND_4_RULE
        rules[7] = ELIMINATION_3_RULE
        rules[8] = ROUND_5_RULE
        rules[9] = ELIMINATION_4_RULE
        rules[10] = ROUND_6_RULE
        rules[11] = ELIMINATION_5_RULE
        for r in range(12, 51):
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

    def _elimination_3_constrained_ranks(
        self,
        initial_scores: dict[str, float],
        final_scores: dict[str, float],
    ) -> dict[str, int]:
        initial_ranks = self._score_to_ranks(initial_scores)
        if not initial_ranks:
            return self._score_to_ranks(final_scores)

        ordered_initial = [character for character, _rank in sorted(initial_ranks.items(), key=lambda item: item[1])]
        locked_top = [character for character in ordered_initial if initial_ranks[character] <= 48]
        elimination_3_characters = [character for character in ordered_initial if character in ELIMINATION_3_MATCHES]
        other_bottom = [
            character
            for character in ordered_initial
            if character not in locked_top and character not in ELIMINATION_3_MATCHES
        ]

        elimination_3_sorted = sorted(
            elimination_3_characters,
            key=lambda character: final_scores.get(character, float("-inf")),
            reverse=True,
        )
        other_bottom_sorted = sorted(
            other_bottom,
            key=lambda character: final_scores.get(character, float("-inf")),
            reverse=True,
        )

        final_ranks = {character: initial_ranks[character] for character in locked_top}
        for index, character in enumerate(elimination_3_sorted):
            final_ranks[character] = 49 + index

        next_rank = 49 + len(elimination_3_sorted)
        for index, character in enumerate(other_bottom_sorted):
            final_ranks[character] = next_rank + index

        for character in final_scores:
            final_ranks.setdefault(character, initial_ranks.get(character, len(final_ranks) + 1))
        return final_ranks

    def _round_5_final_ranks(self, initial_scores: dict[str, float], final_scores: dict[str, float]) -> dict[str, int]:
        initial_ranks = self._score_to_ranks(initial_scores)
        active_characters = set(ROUND_5_MATCHES)
        ordered_active = sorted(
            [character for character in active_characters if character in final_scores],
            key=lambda character: final_scores[character],
            reverse=True,
        )
        ordered_inactive = [
            character
            for character, _rank in sorted(initial_ranks.items(), key=lambda item: item[1])
            if character not in active_characters
        ]
        final_ranks: dict[str, int] = {}
        for index, character in enumerate(ordered_active):
            final_ranks[character] = index + 1
        for index, character in enumerate(ordered_inactive, start=len(ordered_active) + 1):
            final_ranks[character] = index
        return final_ranks

    def _ranking_changes_round_5(self, initial_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 40:
                return "#2ca02c"   # green  — top 40
            if rank <= 64:
                return "#bcbd22"   # yellow — ranks 41-56 (elim-3 pull-ins) and 57-64
            if rank <= 72:
                return "#d62728"   # red    — ranks 65-72 (bottom of Elimination 3)
            return "#000000"       # black  — ranks 73-86 (eliminated before Elimination 3)

        initial_ranks = self._score_to_ranks(initial_scores)
        final_ranks = self._round_5_final_ranks(initial_scores, final_scores)
        ordered = sorted(initial_ranks, key=lambda character: initial_ranks[character])
        changes = []
        for character in ordered:
            initial_rank = initial_ranks[character]
            final_rank = final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            changes.append((character, initial_rank, final_rank, delta, band_color(final_rank)))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))
        for character, initial_rank, final_rank, _delta, color in changes:
            i_score = math.floor(initial_scores.get(character, 0) * 100) / 100
            f_score = math.floor(final_scores.get(character, initial_scores.get(character, 0)) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title("Round 5: Rank 86 to 1 Ranking Changes", fontsize=14)
        plt.tight_layout()
        filename = self.ranking_changes_dir / "round_5_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_round_6(
        self,
        prior_ranks: dict[str, int],
        entry_scores: dict[str, float],
        final_scores: dict[str, float],
    ) -> None:
        """Generate Round 6 ranking changes showing all 86 characters.

        prior_ranks: the Elim 4 final ranks (1-86) — used as the left side.
        Only Round 6 participants (ranks 1-48) reorder; 49-86 locked.
        """

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 32:
                return "#2ca02c"  # green — top 32
            if rank <= 56:
                return "#bcbd22"  # yellow — ranks 33-56
            if rank <= 64:
                return "#d62728"  # red — ranks 57-64
            return "#000000"      # black — ranks 65-86
        if not prior_ranks:
            return

        ordered = [c for c, _rank in sorted(prior_ranks.items(), key=lambda x: x[1])]

        # Only Round 6 participants reorder; everyone else locked.
        r6_chars = [c for c in ordered if c in ROUND_6_MATCHES]
        r6_sorted = sorted(
            r6_chars,
            key=lambda c: final_scores.get(c, float("-inf")),
            reverse=True,
        )

        display_final_ranks: dict[str, int] = {}
        for c in ordered:
            if c not in ROUND_6_MATCHES:
                display_final_ranks[c] = prior_ranks[c]
        for idx, character in enumerate(r6_sorted):
            display_final_ranks[character] = 1 + idx

        changes = []
        for character in ordered:
            initial_rank = prior_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            i_score = math.floor(entry_scores.get(character, 0) * 100) / 100
            f_score = math.floor(final_scores.get(character, entry_scores.get(character, 0)) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title("Round 6: Rank 86 to 1 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "round_6_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

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
            i_score = math.floor(initial_scores[c] * 100) / 100
            f_score = math.floor(final_scores.get(c, initial_scores[c]) * 100) / 100
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{f_score:.2f}  {ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
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
            i_score = math.floor(initial_scores[character] * 100) / 100
            f_score = math.floor(final_scores.get(character, initial_scores[character]) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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

    def _ranking_changes_elimination_3(self, initial_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        """Generate Elimination 3 ranking changes with fixed top 48 and reordered ranks 49-72."""

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 48:
                return "#7f7f7f"  # grey (locked)
            if rank <= 56:
                return "#2ca02c"  # green
            if rank <= 64:
                return "#bcbd22"  # yellow
            if rank <= 72:
                return "#d62728"  # red
            return "#000000"      # black

        initial_ranks = self._score_to_ranks(initial_scores)
        if not initial_ranks:
            return

        ordered_initial = [c for c, _rank in sorted(initial_ranks.items(), key=lambda x: x[1])]
        display_final_ranks = self._elimination_3_constrained_ranks(initial_scores, final_scores)

        changes = []
        for character in ordered_initial:
            initial_rank = initial_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            i_score = math.floor(initial_scores[character] * 100) / 100
            f_score = math.floor(final_scores.get(character, initial_scores[character]) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title("Elimination 3: Rank 72 to 49 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "elimination_3_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _render_elimination_rank_chart(
        self,
        prior_ranks: dict[str, int],
        left_scores: dict[str, float],
        right_scores: dict[str, float],
        *,
        title: str,
        filename: str,
        band_color,
        movable_characters: set[str],
        start_rank: int | None = None,
        rank_order_source: str = "score",
    ) -> None:
        """Render the shared elimination-style rank-change chart.

        The only inputs are:
        - the prior rank order on the left
        - the score source on the left
        - the score source on the right
        - the set of characters allowed to move
        - the color rule for the arrows

        There is no hidden branching between rounds; each round passes the exact rule it needs.
        """

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        if not prior_ranks or not left_scores:
            return

        ordered = [c for c, _rank in sorted(prior_ranks.items(), key=lambda x: x[1])]
        display_final_ranks: dict[str, int] = {c: prior_ranks[c] for c in ordered}

        move_candidates = [c for c in ordered if c in movable_characters]
        if rank_order_source == "start_rank" and start_rank is not None:
            for idx, character in enumerate(move_candidates):
                display_final_ranks[character] = start_rank + idx
        else:
            right_ranks = self._score_to_ranks(right_scores)
            for character in move_candidates:
                display_final_ranks[character] = right_ranks.get(character, prior_ranks[character])

        changes = []
        for character in ordered:
            initial_rank = prior_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            left_score = math.floor(left_scores.get(character, 0) * 100) / 100
            right_score = math.floor(right_scores.get(character, left_scores.get(character, 0)) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {left_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{right_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title(title, fontsize=14)

        plt.tight_layout()
        with PdfPages(self.ranking_changes_dir / filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_elimination_4(
        self,
        prior_ranks: dict[str, int],
        entry_scores: dict[str, float],
        final_scores: dict[str, float],
    ) -> None:
        """Generate Elimination 4 ranking changes showing all 86 characters.

        prior_ranks: the Round 5 final ranks (1-86) — used as the left side.
        entry_scores: scores entering Elimination 4 (after refactoring).
        final_scores: scores after Elimination 4 matches.

        Ranks 1-40: grey.  41-48: green.  49-56: yellow.
        57-64: red.  65-86: black.
        Only Elim 4 participants (41-64) reorder; everyone else keeps their rank.
        """

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 40:
                return "#7f7f7f"  # grey (locked top 40)
            if rank <= 48:
                return "#2ca02c"  # green
            if rank <= 56:
                return "#bcbd22"  # yellow
            if rank <= 64:
                return "#d62728"  # red
            return "#000000"      # black (eliminated)

        if not prior_ranks:
            return

        ordered = [c for c, _rank in sorted(prior_ranks.items(), key=lambda x: x[1])]

        elim4_chars = [c for c in ordered if c in ELIMINATION_4_MATCHES]
        elim4_sorted = sorted(
            elim4_chars,
            key=lambda c: final_scores.get(c, float("-inf")),
            reverse=True,
        )

        display_final_ranks: dict[str, int] = {}
        for c in ordered:
            if c not in ELIMINATION_4_MATCHES:
                display_final_ranks[c] = prior_ranks[c]
        for idx, character in enumerate(elim4_sorted):
            display_final_ranks[character] = 41 + idx

        changes = []
        for character in ordered:
            initial_rank = prior_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            i_score = math.floor(entry_scores.get(character, 0) * 100) / 100
            f_score = math.floor(final_scores.get(character, entry_scores.get(character, 0)) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title("Elimination 4: Rank 86 to 1 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "elimination_4_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_elimination_5(
        self,
        prior_ranks: dict[str, int],
        entry_scores: dict[str, float],
        final_scores: dict[str, float],
    ) -> None:
        """Generate Elimination 5 ranking changes in the Elimination 4 visual format.

        Rule: keep all non-Elimination-5 characters fixed in their prior rank order; for the
        Elimination 5 subset, reorder only within their initial rank band based on their final
        Elimination 5 scores, while keeping the full 86-character chart visible.
        """

        def ordinal(n: int) -> str:
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        def band_color(rank: int) -> str:
            if rank <= 32:
                return "#7f7f7f"  # grey
            if rank <= 48:
                return "#2ca02c"  # green
            if rank <= 56:
                return "#d62728"  # red
            return "#000000"      # black

        if not prior_ranks:
            return

        ordered = [c for c, _rank in sorted(prior_ranks.items(), key=lambda x: x[1])]
        elim5_chars = [c for c in ordered if c in ELIMINATION_5_MATCHES]

        display_final_ranks: dict[str, int] = {c: prior_ranks[c] for c in ordered}

        if elim5_chars:
            # Preserve the original rank-band placement, then reorder only within that subset.
            subset_rank_min = 33
            subset_rank_max = 56
            subset_order = sorted(
                elim5_chars,
                key=lambda c: final_scores.get(c, float("-inf")),
                reverse=True,
            )
            for idx, character in enumerate(subset_order):
                target_rank = subset_rank_min + idx
                if target_rank > subset_rank_max:
                    target_rank = subset_rank_max
                display_final_ranks[character] = target_rank

        changes = []
        for character in ordered:
            initial_rank = prior_ranks[character]
            final_rank = display_final_ranks.get(character, initial_rank)
            delta = initial_rank - final_rank
            color = band_color(final_rank)
            changes.append((character, initial_rank, final_rank, delta, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for character, initial_rank, final_rank, _delta, color in changes:
            i_score = math.floor(entry_scores.get(character, 0) * 100) / 100
            f_score = math.floor(final_scores.get(character, entry_scores.get(character, 0)) * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        ax.set_title("Elimination 5: Rank 86 to 1 Rank Changes", fontsize=14)

        plt.tight_layout()
        filename = self.ranking_changes_dir / "elimination_5_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_black_arrows(self, seed_order: list[str], final_scores: dict[str, float], round_number: int = 1, initial_scores: dict[str, float] | None = None) -> None:
        """Generate Round 1 ranking changes with black arrows only (no color coding).
        
        seed_order: List of character names in seed/bracket order (1st seed, 2nd seed, etc.)
        final_scores: Dictionary of character names to their final round scores.
        initial_scores: Optional dict of scores at the start of this round (shown on left side).
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
            left_score = f"  {math.floor(initial_scores[c] * 100) / 100:.2f}" if initial_scores and c in initial_scores else ""
            right_score = f"{math.floor(final_scores[c] * 100) / 100:.2f}  " if c in final_scores else ""
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}{left_score}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{right_score}{ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
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
            i_score = math.floor(previous_scores[c] * 100) / 100
            f_score = math.floor(final_scores[c] * 100) / 100
            ax.text(0, i_rank, f"{ordinal(i_rank)} {c}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, f_rank, f"{f_score:.2f}  {ordinal(f_rank)} {c}", ha="left", va="center", fontsize=8)
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
            i_score = math.floor(previous_scores[character] * 100) / 100
            f_score = math.floor(final_scores[character] * 100) / 100
            ax.text(0, initial_rank, f"{ordinal(initial_rank)} {character}  {i_score:.2f}", ha="right", va="center", fontsize=8)
            ax.text(1, final_rank, f"{f_score:.2f}  {ordinal(final_rank)} {character}", ha="left", va="center", fontsize=8)
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
        previous_adjusted_scores: dict[str, float] | None = None,
    ) -> RoundSummary:
        rule = self.rules.get(round_number, RoundScoringRule(round_number=round_number, max_percentage=175))
        round_engine = Round(
            round_number=round_number,
            matches_by_character=matches_by_character,
            scoring_rule=rule,
            matchup_df=self.matchup_df,
        )
        summary, records_df = round_engine.calculate_with_records(
            previous_scores or {},
            defaultdict(int),
            previous_adjusted_scores=previous_adjusted_scores,
        )
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
        round_entry_history: dict[int, dict[str, float]] = {}
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
            elif round_number == 7 and cumulative_scores:
                elim_3_pool = {c: cumulative_scores[c] for c in ELIMINATION_3_MATCHES if c in cumulative_scores}
                late_targets = set(rank_window_characters(elim_3_pool, 1, 16))
                cumulative_scores = apply_selective_score_reduction(cumulative_scores, late_targets, exponent=ELIMINATION_3_LATE_ENTRY_EXPONENT)
                previous_scores = dict(cumulative_scores)
            elif round_number == 8 and cumulative_scores:
                # Capture full 86-char pre-round-5 scores before filtering.
                # Elim 3 characters get the same score refactoring applied to their
                # joined scores as regular round-5 entrants receive.
                full_pre_round5 = {
                    c: round(s ** ROUND_5_ELIMINATION_3_ENTRY_EXPONENT, 3) if c in ELIMINATION_3_MATCHES else s
                    for c, s in cumulative_scores.items()
                }
                previous_scores = build_round_5_entry_scores(round_history.get(6, cumulative_scores), cumulative_scores)
                cumulative_scores = dict(previous_scores)
            elif round_number == 9 and cumulative_scores:
                # Restore full 86-char state: Round 5 only tracked 56 participants.
                full_state = dict(full_pre_round5)
                full_state.update(cumulative_scores)
                # All ranks 41-64 (by Round 5 final ranking) get score^0.83.
                r5_final_ranks = self._round_5_final_ranks(full_pre_round5, cumulative_scores)
                elim_4_targets = {c for c, rank in r5_final_ranks.items() if 41 <= rank <= 64}
                full_state = apply_selective_score_reduction(full_state, elim_4_targets, exponent=ELIMINATION_4_ENTRY_EXPONENT)
                cumulative_scores = full_state
                previous_scores = dict(cumulative_scores)
            elif round_number == 10 and cumulative_scores:
                # Step 1: Selective — Elim 4 ranks 41-56 get score^0.966
                e4_chars = [c for c in ELIMINATION_4_MATCHES if c in cumulative_scores]
                e4_sorted = sorted(e4_chars, key=lambda c: cumulative_scores.get(c, 0), reverse=True)
                e4_ranks = {c: 41 + i for i, c in enumerate(e4_sorted)}
                selective_41_56 = {c for c, rank in e4_ranks.items() if 41 <= rank <= 56}
                cumulative_scores = apply_selective_score_reduction(cumulative_scores, selective_41_56, exponent=ROUND_6_ELIM4_SELECTIVE_EXPONENT)
                # Step 2: Global — ALL scores get score^0.6
                cumulative_scores = apply_score_reduction_custom(cumulative_scores, exponent=ROUND_6_GLOBAL_EXPONENT)
                previous_scores = dict(cumulative_scores)
            else:
                previous_scores = dict(cumulative_scores)
            round_entry_history[round_number] = dict(previous_scores)
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
            elif round_number == 7 and previous_scores:
                self._ranking_changes_elimination_3(previous_scores, cumulative_scores)
            elif round_number == 8 and previous_scores:
                self._ranking_changes_round_5(full_pre_round5, cumulative_scores)
            elif round_number == 9 and previous_scores:
                # Elimination 4 ranking changes are generated in main() with full 86-char scores.
                pass
            elif round_number == 10 and previous_scores:
                # Round 6 ranking changes are generated in main() with full 86-char scores.
                pass
            elif round_number == 11 and previous_scores:
                # Elimination 5 is generated explicitly in main() using the text-heavy Elimination 4 layout.
                pass
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
        if final_round == 7:
            final_ranks = self._elimination_3_constrained_ranks(round_entry_history.get(final_round, {}), final_scores)
        elif final_round == 8:
            final_ranks = self._round_5_final_ranks(round_entry_history.get(final_round, {}), final_scores)
        elif final_round == 9:
            # Elim 4: lock ranks 1-40 and 65-86, reorder only 41-64 by final score.
            r5_ranks = self._round_5_final_ranks(full_pre_round5, round_history.get(8, {}))
            elim4_chars = [c for c, rank in r5_ranks.items() if 41 <= rank <= 64]
            elim4_sorted = sorted(elim4_chars, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)
            final_ranks = dict(r5_ranks)
            for idx, character in enumerate(elim4_sorted):
                final_ranks[character] = 41 + idx
        elif final_round == 10:
            # Round 6: top 48 reorder by score, 49-86 keep Elim 4 ranks.
            r6_chars = [c for c in ROUND_6_MATCHES if c in final_scores]
            r6_sorted = sorted(r6_chars, key=lambda c: final_scores.get(c, float("-inf")), reverse=True)
            # Build Elim 4 final ranks for the locked characters
            r5_ranks = self._round_5_final_ranks(full_pre_round5, round_history.get(8, {}))
            e4_chars = [c for c, rank in r5_ranks.items() if 41 <= rank <= 64]
            e4_sorted = sorted(e4_chars, key=lambda c: round_history.get(9, {}).get(c, float("-inf")), reverse=True)
            final_ranks = dict(r5_ranks)
            for idx, character in enumerate(e4_sorted):
                final_ranks[character] = 41 + idx
            # Now overlay Round 6 participants with ranks 1-48
            for idx, character in enumerate(r6_sorted):
                final_ranks[character] = 1 + idx
        else:
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
        MatchResult('Bowser', "Steve", 1, 1, 49),
        MatchResult('Bowser', "Piranha Plant", 2, 1, 67),
        MatchResult('Bowser', "PacMan", 3, 2, 57),
    ],
    'Sephiroth': [ # 2nd Previously
        MatchResult('Sephiroth', "Mr Game & Watch", 1, 1, 0),
        MatchResult('Sephiroth', "Corrin", 2, 2, 66),
        MatchResult('Sephiroth', "Sonic", 3, 3, 104),
        MatchResult('Sephiroth', "Ness", 4, 1, 44),
        MatchResult('Sephiroth', "Villager", 5, 2, 85),
    ],
    'Roy': [ # 3rd Previously
        MatchResult('Roy', "Fox", 1, 2, 16),
        MatchResult('Roy', "Bowser Jr", 2, 1, 0),
        MatchResult('Roy', "Isabelle", 3, 1, 147),
        MatchResult('Roy', "Olimar", 4, 1, 78),
    ],
    'Dr Mario': [ # 4th Previously
        MatchResult('Dr Mario', "Ganondorf", 1, -1, 29),
    ],
    'Young Link': [ # 5th Previously
        MatchResult('Young Link', "PacMan", 1, 2, 152),
        MatchResult('Young Link', "Pokemon Trainer", 2, 2, 26),
        MatchResult('Young Link', "Bowser", 3, 2, 111),
    ],
    'Chrom': [ # 6th Previously
        MatchResult('Chrom', "Samus", 1, 2, 65),
        MatchResult('Chrom', "Pyra & Mythra", 2, 2, 110),
        MatchResult('Chrom', "Wario", 3, 1, 61),
    ],
    'Wolf': [ # 7th Previously
        MatchResult('Wolf', "Sheik", 1, 1, 125),
        MatchResult('Wolf', "Mario", 2, 2, 45),
        MatchResult('Wolf', "Rosalina & Luma", 3, 2, 10),
    ],
    'Ice Climbers': [ # 8th Previously
        MatchResult('Ice Climbers', "Palutena", 1, 2, 28),
        MatchResult('Ice Climbers', "Roy", 2, 3, 96),
        MatchResult('Ice Climbers', "Greninja", 3, 2, 80),
        MatchResult('Ice Climbers', "Marth", 4, 3, 175),
    ],
    'Bowser Jr': [ # 9th Previously
        MatchResult('Bowser Jr', "Yoshi", 1, 3, 177),
        MatchResult('Bowser Jr', "Toon Link", 2, 2, 71),
        MatchResult('Bowser Jr', "Ken", 3, 3, 34),
    ],
    'PacMan': [ # 10th Previously
        MatchResult('PacMan', "Hero", 1, 1, 119),
        MatchResult('PacMan', "Min-Min", 2, 2, 112),
        MatchResult('PacMan', "Richter", 3, 1, 135),
    ],
    'Terry': [ # 11th Previously
        MatchResult('Terry', "Chrom", 1, 2, 0),
        MatchResult('Terry', "King Dedede", 2, 1, 60),
        MatchResult('Terry', "Lucas", 3, 2, 12),
    ],
    'Toon Link': [ # 12th Previously
        MatchResult('Toon Link', "Daisy", 1, -2, 85),
    ],
    'Zelda': [ # 13th Previously
        MatchResult('Zelda', "Falco", 1, 2, 69),
        MatchResult('Zelda', "Zero Suit Samus", 2, 2, 76),
        MatchResult('Zelda', "Bowser Jr", 3, 3, 127),
    ],
    'Yoshi': [ # 14th Previously
        MatchResult('Yoshi', "Mewtwo", 1, 2, 109),
        MatchResult('Yoshi', "Ike", 2, 1, 109),
        MatchResult('Yoshi', "Richter", 3, 2, 0),
        MatchResult('Yoshi', "Link", 4, 1, 93),
    ],
    'Lucas': [ # 15th Previously
        MatchResult('Lucas', "Dr Mario", 1, 2, 22),
        MatchResult('Lucas', "Bayonetta", 2, 2, 141),
        MatchResult('Lucas', "Mr Game & Watch", 3, 3, 131),
    ],
    'Pit': [ # 16th Previously
        MatchResult('Pit', "Ryu", 1, 1, 0),
        MatchResult('Pit', "Sephiroth", 2, 2, 11),
        MatchResult('Pit', "Young Link", 3, 2, 53),
    ],
    'Dark Pit': [ # 17th Previously
        MatchResult('Dark Pit', "Robin", 1, 2, 48),
        MatchResult('Dark Pit', "Mario", 2, 2, 57),
        MatchResult('Dark Pit', "Toon Link", 3, 3, 168),
    ],
    'King Dedede': [ # 18th Previously
        MatchResult('King Dedede', "Bayonetta", 1, 3, 159),
        MatchResult('King Dedede', "Marth", 2, 3, 159),
        MatchResult('King Dedede', "Pit", 3, 1, 0),
    ],
    'Link': [ # 19th Previously
        MatchResult('Link', "Kazuya", 1, 2, 166),
        MatchResult('Link', "Terry", 2, 2, 99),
        MatchResult('Link', "Peach", 3, 2, 44),
    ],
    'Donkey Kong': [ # 20th Previously
        MatchResult('Donkey Kong', "Roy", 1, 3, 172),
        MatchResult('Donkey Kong', "Zero Suit Samus", 2, 2, 27),
        MatchResult('Donkey Kong', "Sephiroth", 3, 1, 44),
    ],
    'Cloud': [ # 21st Previously
        MatchResult('Cloud', "Snake", 1, 1, 57),
        MatchResult('Cloud', "Isabelle", 2, 1, 21),
        MatchResult('Cloud', "Samus", 3, 3, 118),
    ],
    'Dark Samus': [ # 22nd Previously
        MatchResult('Dark Samus', "Ice Climbers", 1, 1, 99),
        MatchResult('Dark Samus', "Olimar", 2, 2, 207),
        MatchResult('Dark Samus', "Sonic", 3, 2, 8),
        MatchResult('Dark Samus', "Snake", 4, 1, 142),
    ],
    'Corrin': [ # 23rd Previously
        MatchResult('Corrin', "Ness", 1, 1, 15),
        MatchResult('Corrin', "Ridley", 2, 1, 39),
        MatchResult('Corrin', "Wolf", 3, 1, 73),
    ],
    'Ganondorf': [ # 24th Previously
        MatchResult('Ganondorf', "Daisy", 1, 2, 15),
        MatchResult('Ganondorf', "Lucas", 2, 3, 137),
        MatchResult('Ganondorf', "Inkling", 3, 1, 103),
    ],
    'Sora': [ # 25th Previously
        MatchResult('Sora', "Dark Samus", 1, 3, 64),
        MatchResult('Sora', "Dark Pit", 2, 2, 124),
        MatchResult('Sora', "Pikachu", 3, 1, 82),
        MatchResult('Sora', "King K Rool", 4, 1, 0),
    ],
    'Banjo & Kazooie': [ # 26th Previously
        MatchResult('Banjo & Kazooie', "Piranha Plant", 1, 1, 0),
        MatchResult('Banjo & Kazooie', "Sonic", 2, 2, 54),
        MatchResult('Banjo & Kazooie', "Ike", 3, 3, 153),
        MatchResult('Banjo & Kazooie', "Ridley", 5, 2, 91),
    ],
    'Hero': [ # 27th Previously
        MatchResult('Hero', "Zero Suit Samus", 1, 3, 122),
        MatchResult('Hero', "Chrom", 2, 2, 39),
        MatchResult('Hero', "Luigi", 3, -1, 0),
    ],
    'Little Mac': [ # 28th Previously
        MatchResult('Little Mac', "Mega Man", 1, 2, 50),
        MatchResult('Little Mac', "Ganondorf", 2, 2, 20),
        MatchResult('Little Mac', "Bowser", 3, 1, 106),
    ],
    'Meta Knight': [ # 29th Previously
        MatchResult('Meta Knight', "Chrom", 1, 2, 141),
        MatchResult('Meta Knight', "Villager", 2, -1, 60),
    ],
    'Olimar': [ # 30th Previously
        MatchResult('Olimar', "Cloud", 1, 1, 0),
        MatchResult('Olimar', "Diddy Kong", 2, 3, 88),
        MatchResult('Olimar', "Ike", 3, 2, 140),
    ],
    'Greninja': [ # 31st Previously
        MatchResult('Greninja', "Peach", 1, 2, 25),
        MatchResult('Greninja', "Palutena", 2, 3, 118),
        MatchResult('Greninja', "Snake", 3, 2, 93),
    ],
    'Robin': [ # 32nd Previously
        MatchResult('Robin', "Pit", 1, 1, 0),
        MatchResult('Robin', "Greninja", 2, 2, 66),
        MatchResult('Robin', "Villager", 3, 1, 54),
        MatchResult('Robin', "Wolf", 4, 1, 142),
    ],
    'Min Min': [ # 33rd Previously
        MatchResult('Min Min', "Ness", 1, 3, 57),
        MatchResult('Min Min', "Banjo & Kazooie", 2, 2, 150),
        MatchResult('Min Min', "Snake", 3, 2, 0),
    ],
    'Richter': [ # 34th Previously
        MatchResult('Richter', "Snake", 1, -1, 48),
        MatchResult('Richter', "Kazuya", 2, 0, 0),
        MatchResult('Richter', "Kazuya", 3, 0, 0),
    ],
    'Kirby': [ # 35th Previously
        MatchResult('Kirby', "Pokemon Trainer", 1, 2, 37),
        MatchResult('Kirby', "Pikachu", 2, 2, 22),
        MatchResult('Kirby', "Peach", 3, 2, 13),
        MatchResult('Kirby', "Piranha Plant", 4, 2, 73)
    ],
    'Mii Gunner': [ # 36th Previously
        MatchResult('Mii Gunner', "Hero", 1, 1, 57),
        MatchResult('Mii Gunner', "Bowser", 2, 1, 0),
        MatchResult('Mii Gunner', "Dark Samus", 3, 1, 13),
    ],
    'Luigi': [ # 37th Previously
        MatchResult('Luigi', "Wolf", 1, 1, 93),
        MatchResult('Luigi', "Byleth", 2, 2, 88),
        MatchResult('Luigi', "Richter", 3, 1, 49),
    ],
    'Duck Hunt': [ # 38th Previously
        MatchResult('Duck Hunt', "Byleth", 1, 1, 71),
        MatchResult('Duck Hunt', "Ganondorf", 2, 1, 0),
        MatchResult('Duck Hunt', "Olimar", 3, 1, 184),
    ],
    'Shulk': [ # 39th Previously
        MatchResult('Shulk', "Ness", 1, 2, 156),
        MatchResult('Shulk', "Link", 2, 1, 39),
        MatchResult('Shulk', "Toon Link", 3, 2, 0),
        MatchResult('Shulk', "Lucario", 5, 2, 38),
    ],
    'Ridley': [ # 40th Previously
        MatchResult('Ridley', "Greninja", 1, 2, 15),
        MatchResult('Ridley', "Dr Mario", 2, 2, 0),
        MatchResult('Ridley', "Samus", 3, 3, 147),
    ],
    'Lucina': [ # 41st Previously
        MatchResult('Lucina', "Villager", 1, 3, 154),
        MatchResult('Lucina', "Incineroar", 2, -1, 122),
    ],
    'Isabelle': [ # 42nd Previously
        MatchResult('Isabelle', "Bowser Jr", 1, 2, 127),
        MatchResult('Isabelle', "Lucario", 2, 1, -78),
    ],
    'Incineroar': [ # 43rd Previously
        MatchResult('Incineroar', "Falco", 1, 1, 0),
        MatchResult('Incineroar', "Dark Pit", 2, 2, 119),
        MatchResult('Incineroar', "King Dedede", 3, 1, 36),
    ],
    'Samus': [ # 44th Previously
        MatchResult('Samus', "Pyra & Mythra", 1, -1, 81),
    ],
    'Ike': [ # 45th Previously
        MatchResult('Ike', "Kirby", 1, 1, 26),
        MatchResult('Ike', "Donkey Kong", 2, 2, 54),
        MatchResult('Ike', "Cloud", 3, 2, 127),
        MatchResult('Ike', "Banjo & Kazooie", 5, 1, 4),
    ],
    'Sonic': [ # 46th Previously
        MatchResult('Sonic', "Inkling", 1, -1, 137),
    ],
    'Villager': [ # 47th Previously
        MatchResult('Villager', "Falco", 1, -1, 97),
    ],
    'Simon': [ # 48th Previously
        MatchResult('Simon', "Sonic", 1, 2, 111),
        MatchResult('Simon', "Incineroar", 2, 1, 30),
        MatchResult('Simon', "Sora", 3, 2, 73),
    ],
    'Inkling': [ # 49th Previously
        MatchResult('Inkling', "Byleth", 1, 2, 70),
        MatchResult('Inkling', "Rosalina & Luma", 2, 2, 92),
        MatchResult('Inkling', "Pit", 3, 1, 0),
        MatchResult('Inkling', "Pikachu", 4, 2, 48),
    ],
    'Mii Brawler': [ # 50th Previously
        MatchResult('Mii Brawler', "Ridley", 1, 2, 23),
        MatchResult('Mii Brawler', "Ice Climbers", 2, 1, 0),
        MatchResult('Mii Brawler', "Inkling", 3, 3, 181),
        MatchResult('Mii Brawler', "Villager", 4, -1, 18),
    ],
    'Piranha Plant': [ # 51st Previously
        MatchResult('Piranha Plant', "Daisy", 1, 1, 0),
        MatchResult('Piranha Plant', "Wario", 2, 1, 6),
        MatchResult('Piranha Plant', "Bowser", 3, 2, 45),
    ],
    'Mr Game & Watch': [ # 52nd Previously
        MatchResult('Mr Game & Watch', "Mega Man", 1, 2, 47),
        MatchResult('Mr Game & Watch', "Inkling", 2, 3, 161),
        MatchResult('Mr Game & Watch', "Piranha Plant", 3, -1, 69),
    ],
    'Mewtwo': [ # 53rd Previously
        MatchResult('Mewtwo', "Byleth", 1, 1, 0),
        MatchResult('Mewtwo', "Chrom", 2, 3, 89),
        MatchResult('Mewtwo', "Kirby", 3, 2, 0),
        MatchResult('Mewtwo', "Incineroar", 4, 1, 25),
    ],
    'Ryu': [ # 54th Previously
        MatchResult('Ryu', "Ganondorf", 1, -1, 54),
    ],
    'Mario': [ # 55th Previously
        MatchResult('Mario', "Dr Mario", 1, 2, 134),
        MatchResult('Mario', "Byleth", 2, -1, 46),
    ],
    'Pokemon Trainer': [ # 56th Previously
        MatchResult('Pokemon Trainer', "Yoshi", 1, 1, 81),
        MatchResult('Pokemon Trainer', "Lucas", 2, 2, 159),
        MatchResult('Pokemon Trainer', "Ryu", 3, 2, 6),
        MatchResult('Pokemon Trainer', "Ryu", 5, 0, 0),
    ],
    'King K Rool': [ # 57th Previously
        MatchResult('King K Rool', "Pokemon Trainer", 1, 2, 0),
        MatchResult('King K Rool', "Lucario", 2, 1, 10),
        MatchResult('King K Rool', "Sonic", 3, 2, 40),
    ],
    'Pyra & Mythra': [ # 58th Previously
        MatchResult('Pyra & Mythra', "Mr Game & Watch", 1, 1, 41),
        MatchResult('Pyra & Mythra', "Jigglypuff", 2, 2, 61),
        MatchResult('Pyra & Mythra', "Cloud", 3, 2, 107),
    ],
    'Diddy Kong': [ # 59th Previously
        MatchResult('Diddy Kong', "Cloud", 1, 1, 0),
        MatchResult('Diddy Kong', "ROB", 2, 2, 67),
        MatchResult('Diddy Kong', "Villager", 3, 2, 21),
    ],
    'Mii Swordfighter': [ # 60th Previously
        MatchResult('Mii Swordfighter', "Ness", 1, -1, 50),
    ],
    'Joker': [ # 61st Previously
        MatchResult('Joker', "Peach", 1, 2, 130),
        MatchResult('Joker', "Sephiroth", 2, 2, 103),
        MatchResult('Joker', "Ridley", 3, -1, 118),
    ],
    'Zero Suit Samus': [ # 62nd Previously
        MatchResult('Zero Suit Samus', "Richter", 1, 1, 140),
        MatchResult('Zero Suit Samus', "Kirby", 2, 2, 83),
        MatchResult('Zero Suit Samus', "Palutena", 3, 1, 100),
        MatchResult('Zero Suit Samus', "Ridley", 4, -1, 69),
    ],
    'Wario': [ # 63rd Previously
        MatchResult('Wario', "Simon", 1, 1, 113),
        MatchResult('Wario', "Chrom", 2, 2, 58),
        MatchResult('Wario', "Wolf", 3, -1, 87),
    ],
    'Wii Fit Trainer': [ # 64th Previously
        MatchResult('Wii Fit Trainer', "Min Min", 1, 1, 38),
        MatchResult('Wii Fit Trainer', "Lucas", 2, 1, 87),
        MatchResult('Wii Fit Trainer', "Sheik", 3, 2, 87),
    ],
}

#################################################
################ ELIMINATION 3 ##################
#################################################

ELIMINATION_3_RULE = RoundScoringRule(
    round_number=5,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1.5 + 1.25 * (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ELIMINATION_3_RANK_START = 57
ELIMINATION_3_RANK_END = 80
ELIMINATION_3_RECALC_RANK_END = 71
ELIMINATION_3_ENTRY_EXPONENT = 0.8037
ELIMINATION_3_LATE_ENTRY_EXPONENT = 0.938  # applied to ranks 49-64 only; ranks 65-72 (and 48) enter unchanged

ELIMINATION_3_MATCHES: dict[str, list[MatchResult]] = {
    'Isabelle': [ # 49th Previously
        MatchResult('Isabelle', "Luigi", 1, 1, 0),
        MatchResult('Isabelle', "Peach", 2, 1, 105),
        MatchResult('Isabelle', "Lucario", 3, 2, 100),
    ],
    'Lucina': [ # 50th Previously
        MatchResult('Lucina', "Ganondorf", 1, 1, 0),
        MatchResult('Lucina', "Ike", 2, 2, 24),
        MatchResult('Lucina', "Rosalina & Luma", 3, 2, 143),
    ],
    'Dr Mario': [ # 51st Previously
        MatchResult('Dr Mario', "King K Rool", 1, 2, 88),
        MatchResult('Dr Mario', "Pikachu", 2, 2, 98),
        MatchResult('Dr Mario', "Min Min", 3, 1, 81),
    ],
    'Meta Knight': [ # 52nd Previously
        MatchResult('Meta Knight', "Greninja", 1, 2, 35),
        MatchResult('Meta Knight', "Ice Climbers", 2, 1, 11),
        MatchResult('Meta Knight', "Pokemon Trainer", 3, 2, 71),
    ],
    'Wii Fit Trainer': [ # 53rd Previously
        MatchResult('Wii Fit Trainer', "Dr Mario", 1, -1, 83),
    ],
    'Zero Suit Samus': [ # 54th Previously
        MatchResult('Zero Suit Samus', "Cloud", 1, -1, 27),
    ],
    'Joker': [ # 55th Previously
        MatchResult('Joker', "Rosalina & Luma", 1, 1, 30),
        MatchResult('Joker', "Ridley", 2, 2, 16),
        MatchResult('Joker', "Meta Knight", 3, -2, 120),
    ],
    'Toon Link': [ # 56th Previously
        MatchResult('Toon Link', "Diddy Kong", 1, 2, 92),
        MatchResult('Toon Link', "Mewtwo", 2, 2, 122),
        MatchResult('Toon Link', "Mega Man", 3, 2, 44),
    ],
    'Richter': [ # 57th Previously
        MatchResult('Richter', "Captain Falcon", 1, 2, 80),
        MatchResult('Richter', "King K Rool", 2, 2, 15),
        MatchResult('Richter', "Zelda", 3, 2, 80),
        MatchResult('Richter', "Piranha Plant", 4, 1, 41),
    ],
    'Sonic': [ # 58th Previously
        MatchResult('Sonic', "Toon Link", 1, 3, 144),
        MatchResult('Sonic', "Yoshi", 2, 1, 90),
        MatchResult('Sonic', "Link", 3, 1, 17),
        MatchResult('Sonic', "Sora", 4, 2, 24),
    ],
    'Mario': [ # 59th Previously
        MatchResult('Mario', "Ness", 1, 1, 14),
        MatchResult('Mario', "King K Rool", 2, 1, 15),
        MatchResult('Mario', "Sheik", 3, 2, 106),
    ],
    'Samus': [ # 60th Previously
        MatchResult('Samus', "Donkey Kong", 1, 1, 21),
        MatchResult('Samus', "Sora", 2, -1, 41),
    ],
    'Wario': [ # 61st Previously
        MatchResult('Wario', "Wii Fit Trainer", 1, 2, 88),
        MatchResult('Wario', "PacMan", 2, 1, 31),
        MatchResult('Wario', "Ice Climbers", 3, 3, 199),
    ],
    'Villager': [ # 62nd Previously
        MatchResult('Villager', "Zelda", 1, -1, 40),
    ],
    'Ryu': [ # 63rd Previously
        MatchResult('Ryu', "Mega Man", 1, 3, 159),
        MatchResult('Ryu', "Dark Samus", 2, 2, 17),
        MatchResult('Ryu', "Sheik", 3, 2, 34),
    ],
    'Mii Swordfighter': [ # 64th Previously
        MatchResult('Mii Swordfighter', "Mega Man", 1, 3, 155),
        MatchResult('Mii Swordfighter', "Bayonetta", 2, 3, 101),
        MatchResult('Mii Swordfighter', "Little Mac", 3, 2, 146),
        MatchResult('Mii Swordfighter', "Wii Fit Trainer", 4, 2, 103),
    ],
    'Sheik': [ # 65th Previously
        MatchResult('Sheik', "Simon", 1, -2, 43),
    ],
    'Bayonetta': [ # 66th Previously
        MatchResult('Bayonetta', "Sora", 1, 1, 15),
        MatchResult('Bayonetta', "Roy", 2, 1, 29),
        MatchResult('Bayonetta', "Jigglypuff", 3, -1, 87),
    ],
    'Captain Falcon': [ # 67th Previously
        MatchResult('Captain Falcon', "Min Min", 1, 2, 66),
        MatchResult('Captain Falcon', "Corrin", 2, 2, 100),
        MatchResult('Captain Falcon', "Kirby", 3, 1, 0),
    ],
    'Byleth': [ # 68th Previously
        MatchResult('Byleth', "King Dedede", 1, 2, 124),
        MatchResult('Byleth', "Chrom", 2, 1, 15),
        MatchResult('Byleth', "Daisy", 3, 2, 88),
        MatchResult('Byleth', "Ike", 4, 2, 41),
    ],
    'Pichu': [ # 69th Previously
        MatchResult('Pichu', "Steve", 1, 2, 151),
        MatchResult('Pichu', "Yoshi", 2, 1, 3),
        MatchResult('Pichu', "Donkey Kong", 3, 1, 104),
        MatchResult('Pichu', "Jigglypuff", 3, 2, 48),
    ],
    'Peach': [ # 70th Previously
        MatchResult('Peach', "Donkey Kong", 1, 1, 85),
        MatchResult('Peach', "Robin", 2, 2, 48),
        MatchResult('Peach', "Bowser", 3, 2, 124),
        MatchResult('Peach', "Meta Knight", 4, -1, 23),
    ],
    'Rosalina & Luma': [ # 71st Previously
        MatchResult('Rosalina & Luma', "Wario", 1, 1, 45),
        MatchResult('Rosalina & Luma', "Kazuya", 2, 3, 153),
        MatchResult('Rosalina & Luma', "Richter", 3, 1, 42),
        MatchResult('Rosalina & Luma', "Duck Hunt", 4, -1, 83),
    ],
    'ROB': [ # 72nd Previously
        MatchResult('ROB', "Toon Link", 1, 1, 58),
        MatchResult('ROB', "Min Min", 2, 2, 0),
        MatchResult('ROB', "Pichu", 3, 3, 174),
    ],
}

#################################################
################### ROUND 5 #####################
#################################################

ROUND_5_RULE = RoundScoringRule(
    round_number=8,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 1.61 + 1.25 * (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_5_MATCHES: dict[str, list[MatchResult]] = {
    "Bowser Jr": [ # 1st Previously
        MatchResult("Bowser Jr", "Snake", 1, 3, 122),
        MatchResult("Bowser Jr", "Dark Samus", 2, 1, 168),
        MatchResult("Bowser Jr", "Fox", 3, 2, 121),
        MatchResult("Bowser Jr", "Incineroar", 4, 2, 135),
    ],
    "Sephiroth": [ # 2nd Previously
        MatchResult("Sephiroth", "Olimar", 1, 2, 42),
        MatchResult("Sephiroth", "Piranha Plant", 2, 1, 30),
        MatchResult("Sephiroth", "Snake", 3, 2, 91),
    ],
    "Ice Climbers": [ # 3rd Previously
        MatchResult("Ice Climbers", "Rosalina & Luma", 1, 2, 96),
        MatchResult("Ice Climbers", "Lucas", 2, 2, 10),
        MatchResult("Ice Climbers", "Olimar", 3, 2, 23),
    ],
    "Zelda": [ # 4th Previously
        MatchResult("Zelda", "King Dedede", 1, 2, 50),
        MatchResult("Zelda", "Cloud", 2, 2, 54),
        MatchResult("Zelda", "Zero Suit Samus", 3, 2, 59),
    ],
    "Lucas": [ # 5th Previously
        MatchResult("Lucas", "Meta Knight", 1, 3, 126),
        MatchResult("Lucas", "Robin", 2, 2, 50),
        MatchResult("Lucas", "Ness", 3, 3, 82),
        MatchResult("Lucas", "Banjo & Kazooie", 4, 2, 63),
    ],
    "Bowser": [ # 6th Previously
        MatchResult("Bowser", "Banjo & Kazooie", 1, 1, 31),
        MatchResult("Bowser", "Wolf", 2, 2, 76),
        MatchResult("Bowser", "Yoshi", 3, 3, 119),
    ],
    "Dark Pit": [ # 7th Previously
        MatchResult("Dark Pit", "Palutena", 1, 1, 22),
        MatchResult("Dark Pit", "King Dedede", 2, 1, 46),
        MatchResult("Dark Pit", "King K Rool", 3, 2, 31),
    ],
    "Ridley": [ # 8th Previously
        MatchResult("Ridley", "Bowser Jr", 1, 3, 31),
        MatchResult("Ridley", "Corrin", 2, 2, 156),
        MatchResult("Ridley", "Simon", 3, 3, 188),
        MatchResult("Ridley", "Robin", 4, 0, 0),
    ],
    "Young Link": [ # 9th Previously
        MatchResult("Young Link", "Richter", 1, 2, 0),
        MatchResult("Young Link", "Greninja", 2, 3, 123),
        MatchResult("Young Link", "Pit", 3, 2, 52),
    ],
    "Greninja": [ # 10th Previously
        MatchResult("Greninja", "Isabelle", 1, 2, 45),
        MatchResult("Greninja", "Lucina", 2, 2, 53),
        MatchResult("Greninja", "Ice Climbers", 3, 1, 0),
    ],
    "Kirby": [ # 11th Previously
        MatchResult("Kirby", "Dr Mario", 1, 1, 48),
        MatchResult("Kirby", "Ike", 2, 2, 85),
        MatchResult("Kirby", "Ridley", 3, 3, 182),
        MatchResult("Kirby", "Roy", 4, 1, 105),
    ],
    "Banjo & Kazooie": [ # 12th Previously
        MatchResult("Banjo & Kazooie", "Incineroar", 1, 2, 27),
        MatchResult("Banjo & Kazooie", "Mewtwo", 2, 3, 112),
        MatchResult("Banjo & Kazooie", "Wario", 3, 2, 0),
    ],
    "King Dedede": [ # 13th Previously
        MatchResult("King Dedede", "Min Min", 1, -1, 76),
    ],
    "Wolf": [ # 14th Previously
        MatchResult("Wolf", "Sora", 1, 1, 0),
        MatchResult("Wolf", "Snake", 2, 2, 95),
        MatchResult("Wolf", "Captain Falcon", 3, 1, 63),
        MatchResult("Wolf", "Dark Samus", 4, 1, 65),
    ],
    "Pit": [ # 15th Previously
        MatchResult("Pit", "Corrin", 1, 1, 0),
        MatchResult("Pit", "Lucina", 2, 1, 133),
        MatchResult("Pit", "King K Rool", 3, 1, 26),
    ],
    "Chrom": [ # 16th Previously
        MatchResult("Chrom", "Diddy Kong", 1, 3, 144),
        MatchResult("Chrom", "Mewtwo", 2, 3, 119),
        MatchResult("Chrom", "Mario", 3, 2, 118),
    ],
    "Terry": [ # 17th Previously
        MatchResult("Terry", "Palutena", 1, 3, 85),
        MatchResult("Terry", "Ice Climbers", 2, 2, 120),
        MatchResult("Terry", "Pyra & Mythra ", 3, 1, 85),
        MatchResult("Terry", "Kazuya", 4, 2, 176),
    ],
    "Link": [ # 18th Previously
        MatchResult("Link", "Terry", 1, 1, 0),
        MatchResult("Link", "Kazuya", 2, -1, 104),  
    ],
    "Roy": [ # 19th Previously
        MatchResult("Roy", "Sephiroth", 1, -1, 122),
    ],
    "Min Min": [ # 20th Previously
        MatchResult("Min Min", "Inkling", 1, 2, 51),
        MatchResult("Min Min", "Peach", 2, 3, 56),
        MatchResult("Min Min", "Samus", 3, 1, 10),
    ],
    "Cloud": [ # 21st Previously
        MatchResult("Cloud", "Corrin", 1, 2, 42),
        MatchResult("Cloud", "Roy", 2, 2, 35),
        MatchResult("Cloud", "Villager", 3, 1, 55),
    ],
    "Donkey Kong": [ # 22nd Previously
        MatchResult("Donkey Kong", "Mario", 1, 3, 153),
        MatchResult("Donkey Kong", "Sephiroth", 2, 2, 102),
        MatchResult("Donkey Kong", "Bowser Jr", 3, 1, 20),
    ],
    "Sora": [ # 23rd Previously
        MatchResult("Sora", "Lucas", 1, 2, 91),
        MatchResult("Sora", "Duck Hunt", 2, 2, 75),
        MatchResult("Sora", "Steve", 3, 2, 99),
    ],
    "Yoshi": [ # 24th Previously
        MatchResult("Yoshi", "Terry", 1, 1, 109),
        MatchResult("Yoshi", "Lucario", 2, 2, 32),
        MatchResult("Yoshi", "Ken", 3, 3, 146),
    ],
    "Dark Samus": [ # 25th Previously
        MatchResult("Dark Samus", "Fox", 1, 1, 10),
        MatchResult("Dark Samus", "Corrin", 2, 2, 0),
        MatchResult("Dark Samus", "Palutena", 3, 2, 0),
    ],
    "Olimar": [ # 26th Previously
        MatchResult("Olimar", "Chrom", 1, 2, 108),
        MatchResult("Olimar", "Simon", 2, 2, 55),
        MatchResult("Olimar", "Corrin", 3, 1, 103),
    ],
    "Ganondorf": [ # 27th Previously
        MatchResult("Ganondorf", "Sephiroth", 1, 1, 121),
        MatchResult("Ganondorf", "Pikachu", 2, 2, 225),
        MatchResult("Ganondorf", "Little Mac", 3, 3, 121),
    ],
    "Little Mac": [ # 28th Previously
        MatchResult("Little Mac", "Samus", 1, 1, 5),
        MatchResult("Little Mac", "Simon", 2, 1, 56),
        MatchResult("Little Mac", "Incineroar", 3, 1, 52),
    ],
    "Robin": [ # 29th Previously
        MatchResult("Robin", "Bowser Jr", 1, 2, 144),
        MatchResult("Robin", "Pikachu", 2, 2, 58),
        MatchResult("Robin", "Dr Mario", 3, 1, 101),
    ],
    "Mewtwo": [ # 30th Previously
        MatchResult("Mewtwo", "King Dedede", 1, 1, 40),
        MatchResult("Mewtwo", "Dark Pit", 2, -1, 106),
    ],
    "Shulk": [ # 31st Previously
        MatchResult("Shulk", "Byleth", 1, -2, 57),
    ],
    "Ike": [ # 32nd Previously
        MatchResult("Ike", "Bayonetta", 1, 2, 9),
        MatchResult("Ike", "Wario", 2, 1, 0),
        MatchResult("Ike", "Steve", 3, 3, 142),
    ],
    "Mii Brawler": [ # 33rd Previously
        MatchResult("Mii Brawler", "Donkey Kong", 1, 3, 138),
        MatchResult("Mii Brawler", "Terry", 2, 1, 88),
        MatchResult("Mii Brawler", "Lucina", 3, 2, 92),
        MatchResult("Mii Brawler", "Inkling", 4, 2, 192),
    ],
    "PacMan": [ # 34th Previously
        MatchResult("PacMan", "Chrom", 1, -1, 101),
    ],
    "Inkling": [ # 35th Previously
        MatchResult("Inkling", "Peach", 1, -1, 120),
    ],
    "Piranha Plant": [ # 36th Previously
        MatchResult("Piranha Plant", "Fox", 1, 2, 116),
        MatchResult("Piranha Plant", "Pikachu", 2, 3, 165),
        MatchResult("Piranha Plant", "Falco", 3, 2, 136),
        MatchResult("Piranha Plant", "Sora", 4, 2, 134),
    ],
    "Corrin": [ # 37th Previously
        MatchResult("Corrin", "Zero Suit Samus", 1, 1, 0),
        MatchResult("Corrin", "Meta Knight", 2, 3, 142),
        MatchResult("Corrin", "Greninja", 3, 2, 16),
    ],
    "Hero": [ # 38th Previously
        MatchResult("Hero", "Kirby", 1, 1, 0),
        MatchResult("Hero", "Dark Samus", 2, 3, 116),
        MatchResult("Hero", "Bowser Jr", 3, 3, 71),
    ],
    "Incineroar": [ # 39th Previously
        MatchResult("Incineroar", "ROB", 1, 2, 61),
        MatchResult("Incineroar", "King Dedede", 2, 2, 0),
        MatchResult("Incineroar", "Mega Man", 3, 2, 83),
    ],
    "Simon": [ # 40th Previously
        MatchResult("Simon", "Sonic", 1, 2, 0),
        MatchResult("Simon", "Ridley", 2, 2, 19),
        MatchResult("Simon", "Ken", 3, 1, 74),
    ],
    "Mii Gunner": [ # 41st Previously
        MatchResult("Mii Gunner", "Sephiroth", 1, 2, 26),
        MatchResult("Mii Gunner", "Min Min", 2, 3, 125),
        MatchResult("Mii Gunner", "Meta Knight", 3, 2, 0),
    ],
    "King K Rool": [ # 42nd Previously
        MatchResult("King K Rool", "Duck Hunt", 1, 2, 81),
        MatchResult("King K Rool", "Fox", 2, 1, 71),
        MatchResult("King K Rool", "Dr Mario", 3, 2, 0),
    ],
    "Luigi": [ # 43rd Previously
        MatchResult("Luigi", "Falco", 1, 2, 32),
        MatchResult("Luigi", "Joker", 2, 1, 102),
        MatchResult("Luigi", "Ike", 3, 3, 100),
    ],
    "Pokemon Trainer": [ # 44th Previously
        MatchResult("Pokemon Trainer", "Min Min", 1, 2, 173),
        MatchResult("Pokemon Trainer", "Daisy", 2, 2, 234),
        MatchResult("Pokemon Trainer", "Banjo & Kazooie", 3, 2, 49),
    ],
    "Duck Hunt": [ # 45th Previously
        MatchResult("Duck Hunt", "Shulk", 1, 1, 30),
        MatchResult("Duck Hunt", "Ken", 2, 2, 70),
        MatchResult("Duck Hunt", "Palutena", 3, 2, 28),
    ],
    "Mr Game & Watch": [ # 46th Previously
        MatchResult("Mr Game & Watch", "Richter", 1, 2, 68),
        MatchResult("Mr Game & Watch", "Dark Samus", 2, 2, 105),
        MatchResult("Mr Game & Watch", "Ganondorf", 3, 2, 35),
    ],
    "Diddy Kong": [ # 47th Previously
        MatchResult("Diddy Kong", "Cloud", 1, 2, 110),
        MatchResult("Diddy Kong", "Rosalina & Luma", 2, 2, 74),
        MatchResult("Diddy Kong", "Hero", 3, 1, 48),
    ],
    "Pyra & Mythra": [ # 48th Previously
        MatchResult("Pyra & Mythra", "Bowser Jr", 1, 2, 6),
        MatchResult("Pyra & Mythra", "Little Mac", 2, 2, 40),
        MatchResult("Pyra & Mythra", "Ice Climbers", 3, 2, 58),
    ],
    "Lucina": [ # 49th Previously
        MatchResult("Lucina", "Byleth", 1, 2, 57),
        MatchResult("Lucina", "Ice Climbers ", 2, 2, 53),
        MatchResult("Lucina", "Pikachu", 3, 2, 65),
    ],
    "Meta Knight": [ # 50th Previously
        MatchResult("Meta Knight", "Rosalina & Luma", 1, 1, 17),
        MatchResult("Meta Knight", "Little Mac", 2, 1, 15),
        MatchResult("Meta Knight", "Jigglypuff", 3, 2, 81),
    ],
    "Richter": [ # 51st Previously
        MatchResult("Richter", "Marth", 1, 1, 7),
        MatchResult("Richter", "Mega Man", 2, 1, 102),
        MatchResult("Richter", "Falco", 3, 1, 16),
    ],
    "Isabelle": [ # 52nd Previously
        MatchResult("Isabelle", "King K Rool", 1, 1, 22),
        MatchResult("Isabelle", "Inkling", 2, 2, 130),
        MatchResult("Isabelle", "Robin", 3, 2, 105),
    ],
    "Toon Link": [ # 53rd Previously
        MatchResult("Toon Link", "Falco", 1, 2, 88),
        MatchResult("Toon Link", "Ness", 2, 1, 15),
        MatchResult("Toon Link", "Mewtwo", 3, 2, 36),
        MatchResult("Toon Link", "Robin", 4, 2, 63),
    ],
    "Ryu": [ # 54th Previously
        MatchResult("Ryu", "Sora", 1, -2, 145),
    ],
    "Mii Swordfighter": [ # 55th Previously
        MatchResult("Mii Swordfighter", "Pichu", 1, 2, 46),
        MatchResult("Mii Swordfighter", "Dark Pit", 2, 1, 30),
        MatchResult("Mii Swordfighter", "Incineroar", 3, -1, 120),
    ],
    "Wario": [ # 56th Previously
        MatchResult("Wario", "Kazuya", 1, 1, 86),
        MatchResult("Wario", "Olimar", 2, 1, 59),
        MatchResult("Wario", "Ken", 3, 1, 102),
    ],
}

#################################################
################ ELIMINATION 4 ##################
#################################################

ELIMINATION_4_RULE = RoundScoringRule(
    round_number=9,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 2.73 + 1.0 * (m - 1) / 2,
    use_matchup_multiplier=True,
    late_match_division=True,
)

ELIMINATION_4_RANK_START = 41
ELIMINATION_4_RANK_END = 64

ELIMINATION_4_MATCHES: dict[str, list[MatchResult]] = {
    "Pyra & Mythra": [  # 41st Previously
        MatchResult("Pyra & Mythra", "ROB", 1, 3, 120),
        MatchResult("Pyra & Mythra", "Incineroar", 2, 3, 69),
        MatchResult("Pyra & Mythra", "Olimar", 3, 2, 26),
        MatchResult("Pyra & Mythra", "Mewtwo", 4, 2, 105),
    ],
    "Toon Link": [  # 42nd Previously
        MatchResult("Toon Link", "Isabelle", 1, 2, 23),
        MatchResult("Toon Link", "Marth", 2, 1, 33),
        MatchResult("Toon Link", "Chrom", 3, 1, 72),
        MatchResult("Toon Link", "Wolf", 4, 2, 45),
    ],
    "Diddy Kong": [  # 43rd Previously
        MatchResult("Diddy Kong", "Greninja", 1, 2, 117),
        MatchResult("Diddy Kong", "Captain Falcon", 2, 2, 98),
        MatchResult("Diddy Kong", "Young Link", 3, 3, 175),
    ],
    "Meta Knight": [  # 44th Previously
        MatchResult("Meta Knight", "Joker", 1, 1, 81),
        MatchResult("Meta Knight", "Bayonetta", 2, 2, 179),
        MatchResult("Meta Knight", "Min Min", 3, 2, 164),
    ],
    "Isabelle": [  # 45th Previously
        MatchResult("Isabelle", "Jigglypuff", 1, 2, 54),
        MatchResult("Isabelle", "Hero", 2, 1, 90),
        MatchResult("Isabelle", "Mega Man", 3, 2, 105),
    ],
    "Link": [  # 46th Previously
        MatchResult("Link", "Ice Climbers", 1, 1, 22),
        MatchResult("Link", "Sonic", 2, 3, 155),
        MatchResult("Link", "Piranha Plant", 3, 3, 170),
    ],
    "Richter": [  # 47th Previously
        MatchResult("Richter", "Simon", 1, -1, 88),
    ],
    "King Dedede": [  # 48th Previously
        MatchResult("King Dedede", "Lucario", 1, 3, 122),
        MatchResult("King Dedede", "Donkey Kong", 2, 2, 111),
        MatchResult("King Dedede", "Villager", 3, -1, 80),
    ],
    "Mewtwo": [  # 49th Previously
        MatchResult("Mewtwo", "Terry", 1, -2, 114),
        MatchResult("Mewtwo", "Lucina", 2, 0, 0),
        MatchResult("Mewtwo", "Lucina", 3, 0, 0),
    ],
    "Wario": [  # 50th Previously
        MatchResult("Wario", "Bayonetta", 1, 2, 92),
        MatchResult("Wario", "Zelda", 2, 1, 8),
        MatchResult("Wario", "Toon Link", 3, 1, 73),
        MatchResult("Wario", "Villager", 4, 1, 21),
    ],
    "Roy": [  # 51st Previously
        MatchResult("Roy", "Samus", 1, 2, 137),
        MatchResult("Roy", "Lucas", 2, 2, 66),
        MatchResult("Roy", "Sonic", 3, 2, 45),
    ],
    "Mii Swordfighter": [  # 52nd Previously
        MatchResult("Mii Swordfighter", "Mario", 1, 2, 132),
        MatchResult("Mii Swordfighter", "Zero Suit Samus", 2, 2, 23),
        MatchResult("Mii Swordfighter", "Daisy", 3, 2, 23),
        MatchResult("Mii Swordfighter", "Mr Game & Watch", 4, 2, 34),
    ],
    "PacMan": [  # 53rd Previously
        MatchResult("PacMan", "Yoshi", 1, 1, 88),
        MatchResult("PacMan", "Roy", 2, 2, 15),
        MatchResult("PacMan", "Mewtwo", 3, -1, 13),
    ],
    "Inkling": [  # 54th Previously
        MatchResult("Inkling", "Palutena", 1, 1, 13),
        MatchResult("Inkling", "Pokemon Trainer", 2, 2, 87),
        MatchResult("Inkling", "Zero Suit Samus", 3, 1, 0),
    ],
    "Shulk": [  # 55th Previously
        MatchResult("Shulk", "Ice Climbers", 1, 2, 108),
        MatchResult("Shulk", "Bowser", 2, 1, 0),
        MatchResult("Shulk", "Wolf", 3, -1, 0),
    ],
    "Ryu": [  # 56th Previously
        MatchResult("Ryu", "PacMan", 1, 2, 133),
        MatchResult("Ryu", "Dark Samus", 2, 3, 202),
        MatchResult("Ryu", "Hero", 3, 1, 0),
        MatchResult("Ryu", "Mega Man", 3, 1, 6),
    ],
    "Dr Mario": [  # 57th Previously 
        MatchResult("Dr Mario", "Dark Pit", 1, 3, 133),
        MatchResult("Dr Mario", "Olimar", 2, 2, 113),
        MatchResult("Dr Mario", "Ken", 3, 3, 172),
    ],
    "Pichu": [  # 58th Previously 
        MatchResult("Pichu", "Mega Man", 1, 1, 4),
        MatchResult("Pichu", "Hero", 2, 1, 114),
        MatchResult("Pichu", "Yoshi", 3, 2, 118),
    ],
    "Sonic": [  # 59th Previously 
        MatchResult("Sonic", "Byleth", 1, 2, 67),
        MatchResult("Sonic", "Sephiroth", 2, 2, 83),
        MatchResult("Sonic", "Palutena", 3, 1, 69),
    ],
    "Mario": [  # 60th Previously 
        MatchResult("Mario", "Meta Knight", 1, 2, 75),
        MatchResult("Mario", "Lucario", 2, 1, 0),
        MatchResult("Mario", "Diddy Kong", 3, 2, 10),
    ],
    "ROB": [  # 61st Previously 
        MatchResult("ROB", "Piranha Plant", 1, 2, 0),
        MatchResult("ROB", "Mario", 2, 1, 17),
        MatchResult("ROB", "Ness", 3, 3, 152),
    ],
    "Captain Falcon": [  # 62nd Previously 
        MatchResult("Captain Falcon", "Terry", 1, 2, 0),
        MatchResult("Captain Falcon", "Ken", 2, 2, 34),
        MatchResult("Captain Falcon", "Ryu", 3, 1, 133),
    ],
    "Byleth": [  # 63rd Previously 
        MatchResult("Byleth", "Olimar", 1, 2, 133),
        MatchResult("Byleth", "Ken", 2, 2, 73),
        MatchResult("Byleth", "ROB", 3, 2, 103),
        MatchResult("Byleth", "Chrom", 4, 2, 13),
    ],
    "Peach": [  # 64th Previously 
        MatchResult("Peach", "Pichu", 1, 1, 123),
        MatchResult("Peach", "Mega Man", 2, -1, 145),
    ],
}

#################################################
################### ROUND 6 #####################
#################################################

ROUND_6_RULE = RoundScoringRule(
    round_number=10,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 3.14 + 1.0 * (m - 1),
    use_matchup_multiplier=True,
    late_match_division=True,
)

ROUND_6_MATCHES: dict[str, list[MatchResult]] = {
    "Lucas": [  # 1st Previously
        MatchResult("Lucas", "Toon Link", 1, 2, 51),
        MatchResult("Lucas", "Villager", 2, 1, 0),
        MatchResult("Lucas", "Ganondorf", 3, 2, 66),
    ],
    "Banjo & Kazooie": [  # 2nd Previously
        MatchResult("Banjo & Kazooie", "Mr Game & Watch", 1, 2, 80),
        MatchResult("Banjo & Kazooie", "Roy", 2, 2, 0),
        MatchResult("Banjo & Kazooie", "Pit", 3, 2, 58),
    ],
    "Ridley": [  # 3rd Previously
        MatchResult("Ridley", "Wolf", 1, 2, 113),
        MatchResult("Ridley", "Wii Fit Trainer", 2, 3, 88),
        MatchResult("Ridley", "Roy", 3, 1, 0),
    ],
    "Ice Climbers": [  # 4th Previously
        MatchResult("Ice Climbers", "Luigi", 1, 2, 100),
        MatchResult("Ice Climbers", "Villager", 2, 1, 77),
        MatchResult("Ice Climbers", "Bowser", 3, 3, 139),
    ],
    "Bowser Jr": [  # 5th Previously
        MatchResult("Bowser Jr", "Cloud", 1, 2, 110),
        MatchResult("Bowser Jr", "Chrom", 2, 2, 0),
        MatchResult("Bowser Jr", "ROB", 3, 2, 58),
    ],
    "Chrom": [  # 6th Previously
        MatchResult("Chrom", "Ryu", 1, -1, 41),
    ],
    "Zelda": [  # 7th Previously
        MatchResult("Zelda", "Mewtwo", 1, 2, 34),
        MatchResult("Zelda", "Palutena", 2, 1, 47),
        MatchResult("Zelda", "Rosalina & Luma", 3, 3, 138),
        MatchResult("Zelda", "Daisy", 4, 1, 155),
    ],
    "Young Link": [  # 8th Previously
        MatchResult("Young Link", "Pokemon Trainer", 1, 2, 75),
        MatchResult("Young Link", "Diddy Kong", 2, 3, 108),
        MatchResult("Young Link", "Wario", 3, 2, 48),
        MatchResult("Young Link", "Ridley", 4, 2, 46),
    ],
    "Sephiroth": [  # 9th Previously
        MatchResult("Sephiroth", "Bowser Jr", 1, 3, 125),
        MatchResult("Sephiroth", "Wolf", 2, 1, 31),
        MatchResult("Sephiroth", "Wario", 3, 2, 0),
    ],
    "Bowser": [  # 10th Previously
        MatchResult("Bowser", "Pikachu", 1, 1, 123),
        MatchResult("Bowser", "Richter", 2, 2, 169),
        MatchResult("Bowser", "Ike", 3, 1, 115),
        MatchResult("Bowser", "Wario", 4, 2, 83),
    ],
    "Kirby": [  # 11th Previously
        MatchResult("Kirby", "Ken", 1, 2, 11),
        MatchResult("Kirby", "Wolf", 2, 1, 120),
        MatchResult("Kirby", "Meta Knight", 3, 2, 44),
        MatchResult("Kirby", "Jigglypuff", 4, 3, 153),
    ],
    "Mii Gunner": [  # 12th Previously
        MatchResult("Mii Gunner", "Villager", 1, 2, 6),
        MatchResult("Mii Gunner", "Pichu", 2, 2, 185),
        MatchResult("Mii Gunner", "Sheik", 3, 3, 199),
        MatchResult("Mii Gunner", "Kazuya", 4, 3, 39),
    ],
    "Ike": [  # 13th Previously
        MatchResult("Ike", "Ryu", 1, 2, 44),
        MatchResult("Ike", "Peach", 2, 3, 145),
        MatchResult("Ike", "Lucas", 3, 2, 29),
    ],
    "Terry": [  # 14th Previously
        MatchResult("Terry", "Isabelle", 1, 2, 55),
        MatchResult("Terry", "Pit", 2, 2, 128),
        MatchResult("Terry", "Zelda", 3, 2, 54),
    ],
    "Min Min": [  # 15th Previously
        MatchResult("Min Min", "Hero", 1, 1, 29),
        MatchResult("Min Min", "Ike", 2, -2, 124),
    ],
    "Dark Pit": [  # 16th Previously
        MatchResult("Dark Pit", "Jigglypuff", 1, 2, 12),
        MatchResult("Dark Pit", "Mr Game & Watch", 2, 2, 59),
        MatchResult("Dark Pit", "Daisy", 3, 2, 28),
        MatchResult("Dark Pit", "King K Rool", 4, 1, 0),
    ],
    "Greninja": [  # 17th Previously
        MatchResult("Greninja", "Mewtwo", 1, 3, 36),
        MatchResult("Greninja", "Banjo & Kazooie", 2, -1, 56),
    ],
    "Sora": [  # 18th Previously
        MatchResult("Sora", "Kazuya", 1, -1, 89),
    ],
    "Donkey Kong": [  # 19th Previously
        MatchResult("Donkey Kong", "Snake", 1, 2, 90),
        MatchResult("Donkey Kong", "Min Min", 2, 2, 90),
        MatchResult("Donkey Kong", "Kirby", 3, 2, 0),
    ],
    "Dark Samus": [  # 20th Previously
        MatchResult("Dark Samus", "Robin", 1, 3, 32),
        MatchResult("Dark Samus", "Cloud", 2, 2, 131),
        MatchResult("Dark Samus", "Ness", 3, 1, 0),
    ],
    "Hero": [  # 21st Previously
        MatchResult("Hero", "PacMan", 1, 2, 89),
        MatchResult("Hero", "Donkey Kong", 2, 2, 69),
        MatchResult("Hero", "Yoshi", 3, 3, 136),
    ],
    "Piranha Plant": [  # 22nd Previously
        MatchResult("Piranha Plant", "Ryu", 1, 2, 37),
        MatchResult("Piranha Plant", "Mewtwo", 2, 2, 97),
        MatchResult("Piranha Plant", "Palutena", 3, 3, 136),
    ],
    "Yoshi": [  # 23rd Previously
        MatchResult("Yoshi", "Samus", 1, 2, 110),
        MatchResult("Yoshi", "Captain Falcon", 2, 2, 23),
        MatchResult("Yoshi", "Luigi", 3, 2, 151),
    ],
    "Corrin": [  # 24th Previously
        MatchResult("Corrin", "Villager", 1, 1, 0),
        MatchResult("Corrin", "Toon Link", 2, 2, 60),
        MatchResult("Corrin", "Fox", 3, 2, 85),
        MatchResult("Corrin", "PacMan", 4, 2, 42),
    ],
    "Incineroar": [  # 25th Previously
        MatchResult("Incineroar", "Ridley", 1, 3, 109),
        MatchResult("Incineroar", "ROB", 2, 2, 103),
        MatchResult("Incineroar", "Ike", 3, 1, 0),
    ],
    "Ganondorf": [  # 26th Previously
        MatchResult("Ganondorf", "Peach", 1, 3, 150),
        MatchResult("Ganondorf", "Samus", 2, 2, 68),
        MatchResult("Ganondorf", "Lucas", 3, 3, 176),
    ],
    "Wolf": [  # 27th Previously
        MatchResult("Wolf", "Ridley", 1, 2, 31),
        MatchResult("Wolf", "Kirby", 2, -1, 155),
    ],
    "Cloud": [  # 28th Previously
        MatchResult("Cloud", "Meta Knight", 1, 2, 42),
        MatchResult("Cloud", "Snake", 2, 2, 0),
        MatchResult("Cloud", "Hero", 3, -1, 62),
    ],
    "Mii Brawler": [  # 29th Previously
        MatchResult("Mii Brawler", "Ike", 1, 2, 115),
        MatchResult("Mii Brawler", "Palutena", 2, 1, 0),
        MatchResult("Mii Brawler", "Mega Man", 3, 2, 93),
    ],
    "Olimar": [  # 30th Previously
        MatchResult("Olimar", "Toon Link", 1, 2, 101),
        MatchResult("Olimar", "Corrin", 2, 2, 35),
        MatchResult("Olimar", "Wario", 3, 2, 112),
        MatchResult("Olimar", "Kirby", 4, 2, 152),
    ],
    "Luigi": [  # 31st Previously
        MatchResult("Luigi", "Link", 1, -2, 75),
    ],
    "Duck Hunt": [  # 32nd Previously
        MatchResult("Duck Hunt", "Cloud", 1, 2, 136),
        MatchResult("Duck Hunt", "Olimar", 2, 2, 140),
        MatchResult("Duck Hunt", "Wario", 3, 2, 58),
    ],
    "Pit": [  # 33rd Previously
        MatchResult("Pit", "Byleth", 1, -1, 29),
    ],
    "King K Rool": [  # 34th Previously
        MatchResult("King K Rool", "Hero", 1, 1, 75),
        MatchResult("King K Rool", "Kirby", 2, 2, 7),
        MatchResult("King K Rool", "Ice Climbers", 3, 3, 172),
    ],
    "Robin": [  # 35th Previously
        MatchResult("Robin", "Wii Fit Trainer", 1, 2, 0),
        MatchResult("Robin", "Ice Climbers", 2, 1, 12),
        MatchResult("Robin", "Chrom", 3, 1, 8),
        MatchResult("Robin", "Banjo & Kazooie", 4, 1, 76),
    ],
    "Little Mac": [  # 36th Previously
        MatchResult("Little Mac", "Terry", 1, -1, 63),
    ],
    "Simon": [  # 37th Previously
        MatchResult("Simon", "Yoshi", 1, 1, 89),
        MatchResult("Simon", "Mewtwo", 2, 1, 0),
        MatchResult("Simon", "Duck Hunt", 3, 2, 121),
    ],
    "Lucina": [  # 38th Previously
        MatchResult("Lucina", "Wolf", 1, 2, 162),
        MatchResult("Lucina", "Fox", 2, 2, 54),
        MatchResult("Lucina", "Isabelle", 3, 2, 90),
    ],
    "Mr Game & Watch": [  # 39th Previously
        MatchResult("Mr Game & Watch", "Pokemon Trainer", 1, 1, 0),
        MatchResult("Mr Game & Watch", "Min Min", 2, 2, 22),
        MatchResult("Mr Game & Watch", "Pyra & Mythra", 3, 2, 126),
    ],
    "Pokemon Trainer": [  # 40th Previously
        MatchResult("Pokemon Trainer", "Ken", 1, 1, 21),
        MatchResult("Pokemon Trainer", "Isabelle", 2, 2, 160),
        MatchResult("Pokemon Trainer", "Yoshi", 3, 2, 74),
        MatchResult("Pokemon Trainer", "Hero", 4, 2, 117),
    ],
    "Pyra & Mythra": [  # 41st Previously 
        MatchResult("Pyra & Mythra", "Donkey Kong", 1, 1, 102),
        MatchResult("Pyra & Mythra", "Steve", 2, 3, 122),
        MatchResult("Pyra & Mythra", "Mr Game & Watch", 3, 1, 6),
    ],
    "Link": [  # 42nd Previously 
        MatchResult("Link", "Steve", 1, 2, 0),  
        MatchResult("Link", "Luigi", 2, 1, 81),
        MatchResult("Link", "Ice Climbers", 3, 3, 119),
    ],
    "Diddy Kong": [  # 43rd Previously 
        MatchResult("Diddy Kong", "King K Rool", 1, -1, 130),
    ],
    "Dr Mario": [  # 44th Previously 
        MatchResult("Dr Mario", "Ice Climbers", 1, 2, 39),
        MatchResult("Dr Mario", "Pikachu", 2, 2, 95),
        MatchResult("Dr Mario", "Hero", 3, 1, 0),
        MatchResult("Dr Mario", "Byleth", 4, 1, 0),
    ],
    "Mii Swordfighter": [  # 45th Previously 
        MatchResult("Mii Swordfighter", "Bowser", 1, 1, 95),
        MatchResult("Mii Swordfighter", "Captain Falcon", 2, 2, 212),
        MatchResult("Mii Swordfighter", "Sheik", 3, 2, 174),
    ],
    "Ryu": [  # 46th Previously 
        MatchResult("Ryu", "Toon Link", 1, 1, 121),
        MatchResult("Ryu", "Bowser", 2, 1, 0),
        MatchResult("Ryu", "Fox", 3, 2, 107),
    ],
    "Isabelle": [  # 47th Previously 
        MatchResult("Isabelle", "Pit", 1, 2, 109),
        MatchResult("Isabelle", "Samus", 2, 2, 81),
        MatchResult("Isabelle", "Marth", 3, 1, 61),
    ],
    "Roy": [  # 48th Previously 
        MatchResult("Roy", "Rosalina & Luma", 1, 3, 122),
        MatchResult("Roy", "Lucina", 2, 3, 127),
        MatchResult("Roy", "Kazuya", 3, -1, 161),
    ],
}

#######################################################
################### ELIMINATION 5 #####################
#######################################################

ELIMINATION_5_RULE = RoundScoringRule(
    round_number=11,
    max_percentage=250,
    early_round_limit=3,
    early_multiplier_fn=lambda m: 4.0 + 1.25 * (m - 1),
    use_matchup_multiplier=True,
    late_match_division=True,
)

ELIMINATION_5_MATCHES: dict[str, list[MatchResult]] = {
    "Isabelle": [  # 33rd Previously
        MatchResult("Isabelle", "Pyra & Mythra", 1, 1, 0),
        MatchResult("Isabelle", "Pyra & Mythra", 2, 1, 0),
        MatchResult("Isabelle", "Pyra & Mythra", 3, 1, 0),
    ],
    "Roy": [  # 34th Previously
        MatchResult("Roy", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Roy", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Roy", "Pyra & Mythra", 3, 0, 0),
    ],
    "Simon": [  # 35th Previously
        MatchResult("Simon", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Simon", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Simon", "Pyra & Mythra", 3, 0, 0),
    ],
    "Mii Swordfighter": [  # 36th Previously
        MatchResult("Mii Swordfighter", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Mii Swordfighter", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Mii Swordfighter", "Pyra & Mythra", 3, 0, 0),
    ],
    "Bowser": [  # 37th Previously
        MatchResult("Bowser", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Bowser", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Bowser", "Pyra & Mythra", 3, 0, 0),
    ],
    "Ryu": [  # 38th Previously
        MatchResult("Ryu", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Ryu", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Ryu", "Pyra & Mythra", 3, 0, 0),
    ],
    "Cloud": [  # 39th Previously
        MatchResult("Cloud", "Dark Samus", 1, 0, 0),
        MatchResult("Cloud", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Cloud", "Pyra & Mythra", 3, 0, 0),
    ],
    "Greninja": [  # 40th Previously
        MatchResult("Greninja", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Greninja", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Greninja", "Pyra & Mythra", 3, 0, 0),
    ],
    "Wolf": [  # 41st Previously
        MatchResult("Wolf", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Wolf", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Wolf", "Pyra & Mythra", 3, 0, 0),
    ],
    "Min Min": [  # 42nd Previously
        MatchResult("Min Min", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Min Min", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Min Min", "Pyra & Mythra", 3, 0, 0),
    ],
    "Chrom": [  # 43rd Previously
        MatchResult("Chrom", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Chrom", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Chrom", "Pyra & Mythra", 3, 0, 0),
    ],
    "Sora": [  # 44th Previously
        MatchResult("Sora", "Roy", 1, 0, 0),
        MatchResult("Sora", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Sora", "Pyra & Mythra", 3, 0, 0),
    ],
    "Diddy Kong": [  # 45th Previously
        MatchResult("Diddy Kong", "Sora", 1, 0, 0),
        MatchResult("Diddy Kong", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Diddy Kong", "Pyra & Mythra", 3, 0, 0),
    ],
    "Little Mac": [  # 46th Previously
        MatchResult("Little Mac", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Little Mac", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Little Mac", "Pyra & Mythra", 3, 0, 0),
    ],
    "Pit": [  # 47th Previously
        MatchResult("Pit", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Pit", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Pit", "Pyra & Mythra", 3, 0, 0),
    ],
    "Luigi": [  # 48th Previously
        MatchResult("Luigi", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Luigi", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Luigi", "Pyra & Mythra", 3, 0, 0),
    ],
    "Toon Link": [  # 49th Previously
        MatchResult("Toon Link", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Toon Link", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Toon Link", "Pyra & Mythra", 3, 0, 0),
    ],
    "Meta Knight": [  # 50th Previously
        MatchResult("Meta Knight", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Meta Knight", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Meta Knight", "Pyra & Mythra", 3, 0, 0),
    ],
    "Inkling": [  # 51st Previously
        MatchResult("Inkling", "Pyra & Mythra", 1, 0, 0),
        MatchResult("Inkling", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Inkling", "Pyra & Mythra", 3, 0, 0),
    ],
    "Wario": [  # 52nd Previously
        MatchResult("Wario", "Luigi", 1, 0, 0),
        MatchResult("Wario", "Pyra & Mythra", 2, 0, 0),
        MatchResult("Wario", "Pyra & Mythra", 3, 0, 0),
    ],
    "King Dedede": [  # 53rd Previously
        MatchResult("King Dedede", "Pyra & Mythra", 1, 0, 0),
        MatchResult("King Dedede", "Pyra & Mythra", 2, 0, 0),
        MatchResult("King Dedede", "Pyra & Mythra", 3, 0, 0),
    ],
    "Byleth": [  # 54th Previously
        MatchResult("Byleth", "Pyra & Mythra", 1, 1, 0),
        MatchResult("Byleth", "Pyra & Mythra", 2, 2, 0),
        MatchResult("Byleth", "Pyra & Mythra", 3, 3, 0),
    ],
    "ROB": [  # 55th Previously
        MatchResult("ROB", "Pyra & Mythra", 1, 0, 0),
        MatchResult("ROB", "Pyra & Mythra", 2, 0, 0),
        MatchResult("ROB", "Pyra & Mythra", 3, 0, 0),
    ],
    "Mario": [  # 56th Previously
        MatchResult("Mario", "Pyra & Mythra", 1, 2, 0),
        MatchResult("Mario", "Pyra & Mythra", 2, 2, 0),
        MatchResult("Mario", "Pyra & Mythra", 3, 2, 0),
    ],
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Next Smash Mains tournament pipeline.")
    parser.add_argument(
        "--publish-site",
        action="store_true",
        help="After regenerating the static site, commit and push the Pages repo.",
    )
    parser.add_argument(
        "--site-commit-message",
        default="Update Smash site data",
        help="Commit message used with --publish-site.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip regenerating supplemental analysis outputs.",
    )
    parser.add_argument(
        "--skip-profiles",
        action="store_true",
        help="Skip regenerating character profile PDFs.",
    )
    parser.add_argument(
        "--skip-site",
        action="store_true",
        help="Skip regenerating the static website.",
    )
    parser.add_argument(
        "--skip-opponents",
        action="store_true",
        help="Skip regenerating opponent profile PDFs.",
    )
    return parser.parse_args()


def publish_site(commit_message: str) -> None:
    if not PAGES_REPO_DIR.exists():
        print(f"Pages repo not found; skipped publish: {PAGES_REPO_DIR}")
        return

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=PAGES_REPO_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        print(f"Could not inspect Pages repo status; skipped publish: {status.stderr.strip()}")
        return
    if not status.stdout.strip():
        print("No generated site changes to publish.")
        return

    subprocess.run(["git", "add", "-A"], cwd=PAGES_REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", commit_message], cwd=PAGES_REPO_DIR, check=True)
    subprocess.run(["git", "push"], cwd=PAGES_REPO_DIR, check=True)
    print("Generated site changes published to GitHub Pages repo.")


def main(
    *,
    publish_generated_site: bool = False,
    site_commit_message: str = "Update Smash site data",
    update_analysis: bool = True,
    update_profiles: bool = True,
    update_opponents: bool = True,
    update_site: bool = True,
) -> None:
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
        round_2_summary = manager.bootstrap_round_from_matches(
            2,
            ROUND_2_MATCHES,
            previous_scores=round_1_summary.scores,
            previous_adjusted_scores=round_1_summary.adjusted_scores,
        )
        #print("Rebuilt Round 2 from in-file match data.")
        #print_placeholder_only_characters("Round 2", ROUND_2_MATCHES)
        manager._ranking_changes_black_arrows(seed_order, round_2_summary.scores, round_number=2, initial_scores=round_1_summary.scores)

    elim_1_summary: RoundSummary | None = None
    elim_1_entry_scores: dict[str, float] | None = None
    elim_1_entry_adjusted_scores: dict[str, float] | None = None
    if round_2_summary is not None and ELIMINATION_1_MATCHES:
        elim_1_entry_scores = apply_score_reduction(round_2_summary.scores)
        elim_1_entry_adjusted_scores = apply_score_reduction(round_2_summary.adjusted_scores)
        elim_1_summary = manager.bootstrap_round_from_matches(
            3,
            ELIMINATION_1_MATCHES,
            previous_scores=elim_1_entry_scores,
            previous_adjusted_scores=elim_1_entry_adjusted_scores,
        )
        #print("Rebuilt Elimination 1 from in-file match data.")
        #print_placeholder_only_characters("Elimination 1", ELIMINATION_1_MATCHES)

    round_3_summary: RoundSummary | None = None
    round_3_entry_scores: dict[str, float] | None = None
    round_3_entry_adjusted_scores: dict[str, float] | None = None
    if elim_1_summary is not None and ROUND_3_MATCHES:
        elimination_characters = set(ELIMINATION_1_MATCHES.keys())
        round_3_entry_scores = apply_selective_score_reduction(elim_1_summary.scores, elimination_characters, exponent=0.53955)
        round_3_entry_adjusted_scores = apply_selective_score_reduction(elim_1_summary.adjusted_scores, elimination_characters, exponent=0.53955)
        round_3_summary = manager.bootstrap_round_from_matches(
            4,
            ROUND_3_MATCHES,
            previous_scores=round_3_entry_scores,
            previous_adjusted_scores=round_3_entry_adjusted_scores,
        )
        #print("Rebuilt Round 3 from in-file match data.")
        #print_placeholder_only_characters("Round 3", ROUND_3_MATCHES)

    elim_2_summary: RoundSummary | None = None
    elim_2_entry_scores: dict[str, float] | None = None
    elim_2_entry_adjusted_scores: dict[str, float] | None = None
    round_4_seed_scores: dict[str, float] | None = None
    round_4_seed_adjusted_scores: dict[str, float] | None = None
    if round_3_summary is not None and ELIMINATION_2_MATCHES:
        elimination_2_targets = set(ELIMINATION_2_MATCHES.keys())
        elim_2_entry_scores = apply_selective_score_reduction(
            round_3_summary.scores,
            elimination_2_targets,
            exponent=ELIMINATION_2_ENTRY_EXPONENT,
        )
        elim_2_entry_adjusted_scores = apply_selective_score_reduction(
            round_3_summary.adjusted_scores,
            elimination_2_targets,
            exponent=ELIMINATION_2_ENTRY_EXPONENT,
        )
        elim_2_summary = manager.bootstrap_round_from_matches(
            5,
            ELIMINATION_2_MATCHES,
            previous_scores=elim_2_entry_scores,
            previous_adjusted_scores=elim_2_entry_adjusted_scores,
        )
        ordered_elim_2_scores = dict(sorted(elim_2_summary.scores.items(), key=lambda item: item[1], reverse=True))
        #print("Rebuilt Elimination 2 from in-file match data.")
        #print(ordered_elim_2_scores)
        round_4_seed_scores = apply_selective_score_reduction(
            elim_2_summary.scores,
            set(ELIMINATION_2_MATCHES.keys()),
            exponent=ROUND_4_SETUP_EXPONENT,
        )
        round_4_seed_adjusted_scores = apply_selective_score_reduction(
            elim_2_summary.adjusted_scores,
            set(ELIMINATION_2_MATCHES.keys()),
            exponent=ROUND_4_SETUP_EXPONENT,
        )
        ordered_round_4_seed_scores = dict(
            sorted(round_4_seed_scores.items(), key=lambda item: item[1], reverse=True)
        )
        #print("Round 4 seed scores after Elimination 2 rescale.")
        #print(ordered_round_4_seed_scores)
        #print_placeholder_only_characters("Elimination 2", ELIMINATION_2_MATCHES)

    round_4_summary: RoundSummary | None = None
    if round_4_seed_scores is not None and ROUND_4_MATCHES:
        round_4_summary = manager.bootstrap_round_from_matches(
            6,
            ROUND_4_MATCHES,
            previous_scores=round_4_seed_scores,
            previous_adjusted_scores=round_4_seed_adjusted_scores,
        )
        #print_placeholder_only_characters("Round 4", ROUND_4_MATCHES)
        manager._ranking_changes_round_4(round_4_seed_scores, round_4_summary.scores)

    elim_3_summary: RoundSummary | None = None
    elim_3_entry_scores: dict[str, float] | None = None
    elim_3_entry_adjusted_scores: dict[str, float] | None = None
    if round_4_summary is not None and ELIMINATION_3_MATCHES:
        elim_3_pool = {c: round_4_summary.scores[c] for c in ELIMINATION_3_MATCHES if c in round_4_summary.scores}
        late_targets = set(rank_window_characters(elim_3_pool, 1, 16))
        elim_3_entry_scores = apply_selective_score_reduction(round_4_summary.scores, late_targets, exponent=ELIMINATION_3_LATE_ENTRY_EXPONENT)
        elim_3_entry_adjusted_scores = apply_selective_score_reduction(round_4_summary.adjusted_scores, late_targets, exponent=ELIMINATION_3_LATE_ENTRY_EXPONENT)
        elim_3_summary = manager.bootstrap_round_from_matches(
            7,
            ELIMINATION_3_MATCHES,
            previous_scores=elim_3_entry_scores,
            previous_adjusted_scores=elim_3_entry_adjusted_scores,
        )
        #print_placeholder_only_characters("Elimination 3", ELIMINATION_3_MATCHES)
        manager._ranking_changes_elimination_3(elim_3_entry_scores, elim_3_summary.scores)

    round_5_summary: RoundSummary | None = None
    round_5_entry_scores: dict[str, float] | None = None
    if round_4_summary is not None and elim_3_summary is not None and ROUND_5_MATCHES:
        round_5_entry_scores = build_round_5_entry_scores(round_4_summary.scores, elim_3_summary.scores)
        round_5_entry_adjusted_scores = build_round_5_entry_scores(round_4_summary.adjusted_scores, elim_3_summary.adjusted_scores)
        #print_score_window("Round 5 entry scores", round_5_entry_scores)
        if placeholder_only_characters(ROUND_5_MATCHES) == list(ROUND_5_MATCHES.keys()):
            print_placeholder_only_characters("Round 5", ROUND_5_MATCHES)
        else:
            round_5_summary = manager.bootstrap_round_from_matches(
                8,
                ROUND_5_MATCHES,
                previous_scores=round_5_entry_scores,
                previous_adjusted_scores=round_5_entry_adjusted_scores,
            )
            #print("Rebuilt Round 5 from in-file match data.")
            #print_placeholder_only_characters("Round 5", ROUND_5_MATCHES)
            # Print post-match scores for Round 5 participants (more accurate than entry scores)
            current_round_5_scores = {c: round_5_summary.scores[c] for c in round_5_entry_scores if c in round_5_summary.scores}
            #print_score_window("Round 5 current scores (post-match)", current_round_5_scores)
            # Build the full 86-char pre-round-5 score dict (elim-3 chars refactored).
            # elim_3_summary.scores carries all accumulated history so it covers all 86 chars.
            full_pre_round5_main = {
                c: round(s ** ROUND_5_ELIMINATION_3_ENTRY_EXPONENT, 3) if c in ELIMINATION_3_MATCHES else s
                for c, s in elim_3_summary.scores.items()
            }
            manager._ranking_changes_round_5(full_pre_round5_main, round_5_summary.scores)

    elim_4_summary: RoundSummary | None = None
    elim_4_entry_scores: dict[str, float] | None = None
    elim_4_entry_adjusted_scores: dict[str, float] | None = None
    if round_5_summary is not None and ELIMINATION_4_MATCHES:
        # Build full 86-char score state: pre-round-5 base + Round 5 results overlaid.
        full_post_round5 = dict(full_pre_round5_main)
        full_post_round5.update(round_5_summary.scores)
        full_post_round5_adj = dict(full_pre_round5_main)
        full_post_round5_adj.update(round_5_summary.adjusted_scores)

        # All characters ranked 41-64 after Round 5 get score^0.83.
        round_5_final_ranks = manager._round_5_final_ranks(full_pre_round5_main, round_5_summary.scores)
        elim_4_targets = {c for c, rank in round_5_final_ranks.items() if 41 <= rank <= 64}
        full_pre_elim4 = apply_selective_score_reduction(full_post_round5, elim_4_targets, exponent=ELIMINATION_4_ENTRY_EXPONENT)
        full_pre_elim4_adj = apply_selective_score_reduction(full_post_round5_adj, elim_4_targets, exponent=ELIMINATION_4_ENTRY_EXPONENT)

        # Entry scores for the bootstrap: only the Elim 4 participants.
        elim_4_entry_scores = {c: full_pre_elim4[c] for c in ELIMINATION_4_MATCHES if c in full_pre_elim4}
        elim_4_entry_adjusted_scores = {c: full_pre_elim4_adj[c] for c in ELIMINATION_4_MATCHES if c in full_pre_elim4_adj}

        elim_4_summary = manager.bootstrap_round_from_matches(
            9,
            ELIMINATION_4_MATCHES,
            previous_scores=elim_4_entry_scores,
            previous_adjusted_scores=elim_4_entry_adjusted_scores,
        )
        #print_placeholder_only_characters("Elimination 4", ELIMINATION_4_MATCHES)

        # Full 86-char post-elim4 scores for ranking changes chart.
        full_post_elim4 = dict(full_pre_elim4)
        full_post_elim4.update(elim_4_summary.scores)
        manager._ranking_changes_elimination_4(round_5_final_ranks, full_pre_elim4, full_post_elim4)

    round_6_summary: RoundSummary | None = None
    round_6_entry_scores: dict[str, float] | None = None
    if elim_4_summary is not None and ROUND_6_MATCHES:
        # Step 1: Selective reduction — ranks 41-56 (Elim 4 constrained) get score^0.966
        elim_4_final_ranks = dict(round_5_final_ranks)
        elim4_chars = [c for c, rank in round_5_final_ranks.items() if 41 <= rank <= 64]
        elim4_sorted = sorted(elim4_chars, key=lambda c: full_post_elim4.get(c, float("-inf")), reverse=True)
        for idx, character in enumerate(elim4_sorted):
            elim_4_final_ranks[character] = 41 + idx
        selective_targets = {c for c, rank in elim_4_final_ranks.items() if 41 <= rank <= 56}
        full_after_selective = apply_selective_score_reduction(full_post_elim4, selective_targets, exponent=ROUND_6_ELIM4_SELECTIVE_EXPONENT)

        # Step 2: Global reduction — ALL 86 characters get score^0.6
        full_pre_round6 = apply_score_reduction_custom(full_after_selective, exponent=ROUND_6_GLOBAL_EXPONENT)
        full_pre_round6_adj = apply_score_reduction_custom(full_after_selective, exponent=ROUND_6_GLOBAL_EXPONENT)

        # Step 3: Entry scores for Round 6 — top 48 only
        round_6_entry_scores = {c: full_pre_round6[c] for c in ROUND_6_MATCHES if c in full_pre_round6}
        round_6_entry_adjusted = {c: full_pre_round6_adj[c] for c in ROUND_6_MATCHES if c in full_pre_round6_adj}

        round_6_summary = manager.bootstrap_round_from_matches(
            10,
            ROUND_6_MATCHES,
            previous_scores=round_6_entry_scores,
            previous_adjusted_scores=round_6_entry_adjusted,
        )
        #print_placeholder_only_characters("Round 6", ROUND_6_MATCHES)

        # Ranking changes chart: full 86-char post-round-6 scores
        full_post_round6 = dict(full_pre_round6)
        full_post_round6.update(round_6_summary.scores)
        manager._ranking_changes_round_6(elim_4_final_ranks, full_pre_round6, full_post_round6)

        # Round 6 final ranks: only Round 6 participants reorder into 1-48; 49-86 stay at Elim 4 ranks.
        round_6_final_ranks = dict(elim_4_final_ranks)
        round_6_sorted = sorted(
            [c for c in ROUND_6_MATCHES if c in full_post_round6],
            key=lambda c: full_post_round6[c],
            reverse=True,
        )
        for idx, character in enumerate(round_6_sorted):
            round_6_final_ranks[character] = 1 + idx

        # Pre-Elimination 5 score recalculation off the Round 6 results.
        elim_5_entry_scores = build_elimination_5_entry_scores(round_6_final_ranks, ELIMINATION_5_MATCHES)
        full_pre_elim5 = dict(full_post_round6)
        full_pre_elim5.update(elim_5_entry_scores)

        # Elimination 5 ranking changes should only reflect the currently completed matches.
        # Right now that is just Isabelle, so everything else stays at its pre-Elim-5 score.
        completed_elim5 = {
            character: matches
            for character, matches in ELIMINATION_5_MATCHES.items()
            if matches and any(result.stock_diff != 0 or result.percentage != 0 for result in matches)
        }
        if completed_elim5:
            elim5_entry_subset = {c: full_pre_elim5[c] for c in completed_elim5 if c in full_pre_elim5}
            elim5_summary = manager.bootstrap_round_from_matches(
                11,
                completed_elim5,
                previous_scores=elim5_entry_subset,
                previous_adjusted_scores=elim5_entry_subset,
            )
            elim5_current_scores = dict(full_pre_elim5)
            elim5_current_scores.update(elim5_summary.scores)
            manager._ranking_changes_elimination_5(round_6_final_ranks, full_pre_elim5, elim5_current_scores)

    final_scores = manager.run()

    score_reduction_transitions: list[tuple[str, dict[str, float], dict[str, float]]] = []
    if round_2_summary is not None and elim_1_entry_scores is not None:
        score_reduction_transitions.append(("Round 2 to Elimination 1 (Global)", round_2_summary.scores, elim_1_entry_scores))
    if elim_1_summary is not None and round_3_entry_scores is not None:
        score_reduction_transitions.append(("Elimination 1 to Round 3 (Selective)", elim_1_summary.scores, round_3_entry_scores))
    if round_3_summary is not None and elim_2_entry_scores is not None:
        score_reduction_transitions.append(("Round 3 to Elimination 2 (Selective)", round_3_summary.scores, elim_2_entry_scores))
    if elim_2_summary is not None and round_4_seed_scores is not None:
        score_reduction_transitions.append(("Elimination 2 to Round 4 (Selective)", elim_2_summary.scores, round_4_seed_scores))
    if round_4_summary is not None and elim_3_entry_scores is not None:
        score_reduction_transitions.append(("Round 4 to Elimination 3 (Selective)", round_4_summary.scores, elim_3_entry_scores))
    if elim_3_summary is not None and round_5_entry_scores is not None:
        round_5_pull_ins = set(ROUND_5_MATCHES) - set(rank_window_characters(round_4_summary.scores, 1, 48) if round_4_summary is not None else [])
        score_reduction_transitions.append((
            "Elimination 3 to Round 5 (Top 8 Pull-ins)",
            {character: elim_3_summary.scores[character] for character in round_5_pull_ins if character in elim_3_summary.scores},
            {character: round_5_entry_scores[character] for character in round_5_pull_ins if character in round_5_entry_scores},
        ))
    if round_5_summary is not None and elim_4_entry_scores is not None:
        score_reduction_transitions.append(("Round 5 to Elimination 4 (Selective)", round_5_summary.scores, elim_4_entry_scores))
    if score_reduction_transitions:
        generate_score_reduction_pareto(score_reduction_transitions, REPORTS_DIR / "score_reductions_pareto.pdf")

    if update_analysis:
        regenerate_analysis_outputs()
    else:
        print("Skipped analysis output regeneration.")

    if update_profiles:
        from next_smash_mains_profiles import generate_all_profiles

        generate_all_profiles(
            records_dir=RECORDS_DIR,
            matchup_df=MATCHUP_DF,
        )
    else:
        print("Skipped character profile PDF regeneration.")

    if update_opponents:
        from next_smash_mains_profiles import generate_all_opponent_profiles

        generate_all_opponent_profiles(records_dir=RECORDS_DIR)
    else:
        print("Skipped opponent profile PDF regeneration.")

    if update_site:
        subprocess.run([sys.executable, str(ROOT / "generate_liamms_site.py")], check=True)
    else:
        print("Skipped static site regeneration.")

    if publish_generated_site and update_site:
        publish_site(site_commit_message)
    elif publish_generated_site:
        print("Skipped publish because static site regeneration was skipped.")

if __name__ == "__main__":
    args = parse_args()
    start_time = time.perf_counter()
    main(
        publish_generated_site=args.publish_site,
        site_commit_message=args.site_commit_message,
        update_analysis=not args.skip_analysis,
        update_profiles=not args.skip_profiles,
        update_opponents=not args.skip_opponents,
        update_site=not args.skip_site,
    )
    elapsed_seconds = int(round(time.perf_counter() - start_time))
    minutes, seconds = divmod(elapsed_seconds, 60)
    print(f"Finished in {minutes} minute(s) {seconds} second(s).")


