# New_Smash_Gods__Discovery_Training (Object-Oriented Rewrite)

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

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

MATCHUP_PATH = ROOT / "matchup_chart.csv"
MATCHUP_DF = pd.read_csv(MATCHUP_PATH) if MATCHUP_PATH.exists() else pd.DataFrame()

def apply_score_reduction(scores: dict[str, float]) -> dict[str, float]:
    """Reduce all scores to score^(2/3), applied entering/exiting elimination rounds."""
    return {char: round(score ** (2 / 3), 3) for char, score in scores.items()}

def apply_selective_score_reduction(scores: dict[str, float], target_characters: set[str], exponent: float) -> dict[str, float]:
    """Reduce only selected character scores to score^exponent."""
    return {
        char: round(score ** exponent, 3) if char in target_characters else score
        for char, score in scores.items()
    }

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
        for r in range(5, 51):
            rules[r] = RoundScoringRule(round_number=r, max_percentage=175, early_multiplier_fn=lambda _m: 1.0)
        return rules

    def _round_files(self) -> list[tuple[int, Path]]:
        files = []
        for f in self.records_dir.glob("round_*_records.csv"):
            try:
                number = int(f.stem.split("_")[1])
                files.append((number, f))
            except Exception:
                continue
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
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Previous Round", f"Round {round_number}"])
        ax.invert_yaxis()
        ax.set_ylabel("Rank")
        ax.set_title(f"Round {round_number}: Ranking Changes")
        ax.grid(axis="y", alpha=0.2)
        plt.tight_layout()
        filename = self.ranking_changes_dir / f"round_{round_number}_ranking_changes.pdf"
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
            changes.append((c, i_rank, f_rank, color))

        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for c, i_rank, f_rank, color in changes:
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
        
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title(f"Round {round_number}: Rank 86 to 1 Rank Changes", fontsize=14)
        
        plt.tight_layout()
        filename = self.ranking_changes_dir / f"round_{round_number}_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _ranking_changes_round_3(self, previous_scores: dict[str, float], final_scores: dict[str, float]) -> None:
        """Generate Round 4 changes chart as 'Round 3 Ranking Changes' with rank-band colors."""
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
            if f_rank <= 56:
                color = "#2ca02c"  # green
            elif f_rank <= 80:
                color = "#bcbd22"  # yellow
            else:
                color = "#d62728"  # red
            changes.append((c, i_rank, f_rank, color))

        if not changes:
            return

        changes.sort(key=lambda x: x[1])
        fig_height = max(15, 0.25 * len(changes))
        fig, ax = plt.subplots(figsize=(15, fig_height))

        for c, i_rank, f_rank, color in changes:
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

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0.5, len(changes) + 0.5)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Round 3 Ranking Changes", fontsize=14)

        plt.tight_layout()
        legacy_filename = self.ranking_changes_dir / "round_4_ranking_changes.pdf"
        if legacy_filename.exists():
            legacy_filename.unlink()
        filename = self.ranking_changes_dir / "round_3_ranking_changes.pdf"
        with PdfPages(filename) as pdf:
            pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def _round_report(summary: RoundSummary, output_pdf: Path) -> None:
        win_loss_totals = {k: v[0] for k, v in summary.win_loses.items()}
        win_loss_averages = {k: round(v[1] / (v[0] if v[0] else 1), 3) for k, v in summary.win_loses.items()}
        win_loss_characters = {k: v[2] for k, v in summary.win_loses.items()}
        with PdfPages(output_pdf) as pdf:
            bar_generator(win_loss_totals, "Category", "Count", f"Round {summary.round_number}: Win/Loss Totals", pdf)
            bar_generator(win_loss_averages, "Category", "Average Score", f"Round {summary.round_number}: Win/Loss Average Scores", pdf)
            table_generator(win_loss_characters, f"Round {summary.round_number}: End-Scenario Characters", pdf)
            histogram_generator(summary.scores, "Score", "Frequency", f"Round {summary.round_number}: Score Distribution", pdf)
            distribution_generator(summary.scores, "Score", "Density", f"Round {summary.round_number}: Score Density", pdf)

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
        records_path = self.records_dir / f"round_{round_number}_records.csv"
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
            else:
                previous_scores = dict(cumulative_scores)
            summary = round_engine.calculate(cumulative_scores, loss_counter)
            cumulative_scores = summary.scores
            round_history[round_number] = dict(cumulative_scores)
            report_path = self.reports_dir / f"round_{round_number}_results.pdf"
            self._round_report(summary, report_path)
            if round_number == 2 and previous_scores:
                seed_order = [character for character, _score in sorted(previous_scores.items(), key=lambda item: item[1], reverse=True)]
                self._ranking_changes_black_arrows(seed_order, cumulative_scores, round_number=round_number)
            elif round_number == 3 and previous_scores:
                self._ranking_changes_elimination(previous_scores, cumulative_scores, round_number=round_number)
            elif round_number == 4 and previous_scores:
                self._ranking_changes_round_3(previous_scores, cumulative_scores)
            elif previous_scores:
                eliminated = set(previous_scores) - set(cumulative_scores)
                self._ranking_changes_colored(previous_scores, cumulative_scores, round_number, eliminated)
        if not round_history:
            return {}
        with PdfPages(self.reports_dir / "all_rounds_histogram_evolution.pdf") as pdf:
            for rn in sorted(round_history):
                histogram_generator(round_history[rn], "Score", "Frequency", f"Round {rn}: Score Distribution", pdf)
        with PdfPages(self.reports_dir / "all_rounds_distribution_evolution.pdf") as pdf:
            for rn in sorted(round_history):
                distribution_generator(round_history[rn], "Score", "Density", f"Round {rn}: Score Density", pdf)
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
        MatchResult("Min Min", "Link", 1, 0, 0),
        MatchResult("Min Min", "Link", 2, 0, 0),
        MatchResult("Min Min", "Link", 3, 0, 0),
    ],
    "Lucas": [ # 3rd Previously
        MatchResult("Lucas", "Link", 1, 0, 0),
        MatchResult("Lucas", "Link", 2, 0, 0),
        MatchResult("Lucas", "Link", 3, 0, 0),
    ],
    "Roy": [ # 4th Previously
        MatchResult("Roy", "Link", 1, 0, 0),
        MatchResult("Roy", "Link", 2, 0, 0),
        MatchResult("Roy", "Link", 3, 0, 0),
    ],
    "Dark Samus": [ # 5th Previously
        MatchResult("Dark Samus", "Link", 1, 0, 0),
        MatchResult("Dark Samus", "Link", 2, 0, 0),
        MatchResult("Dark Samus", "Link", 3, 0, 0),
    ],
    "Mii Gunner": [ # 6th Previously
        MatchResult("Mii Gunner", "Link", 1, 0, 0),
        MatchResult("Mii Gunner", "Link", 2, 0, 0),
        MatchResult("Mii Gunner", "Link", 3, 0, 0),
    ],
    "Sephiroth": [ # 7th Previously
        MatchResult("Sephiroth", "Link", 1, 0, 0),
        MatchResult("Sephiroth", "Link", 2, 0, 0),
        MatchResult("Sephiroth", "Link", 3, 0, 0),
    ],
    "Piranha Plant": [ # 8th Previously
        MatchResult("Piranha Plant", "Min Min", 1, 2, 57),
        MatchResult("Piranha Plant", "Duck Hunt", 2, 3, 138),
        MatchResult("Piranha Plant", "Kazuya", 3, -1, 0),
    ],
    "Dr Mario": [ # 9th Previously
        MatchResult("Dr Mario", "Link", 1, 0, 0),
        MatchResult("Dr Mario", "Link", 2, 0, 0),
        MatchResult("Dr Mario", "Link", 3, 0, 0),
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
        MatchResult("Incineroar", "Link", 1, 0, 0),
        MatchResult("Incineroar", "Link", 2, 0, 0),
        MatchResult("Incineroar", "Link", 3, 0, 0),
    ],
    "Bowser Jr": [ # 13th Previously
        MatchResult("Bowser Jr", "Link", 1, 0, 0),
        MatchResult("Bowser Jr", "Link", 2, 0, 0),
        MatchResult("Bowser Jr", "Link", 3, 0, 0),
    ],
    "Banjo & Kazooie": [ # 14th Previously
        MatchResult("Banjo & Kazooie", "Link", 1, 0, 0),
        MatchResult("Banjo & Kazooie", "Link", 2, 0, 0),
        MatchResult("Banjo & Kazooie", "Link", 3, 0, 0),
    ],
    "Bowser": [ # 15th Previously
        MatchResult("Bowser", "Link", 1, 2, 116),
        MatchResult("Bowser", "Wario", 2, 3, 92),
        MatchResult("Bowser", "ROB", 3, 2, 0),
        MatchResult("Bowser", "Captain Falcon", 4, 2, 36),
    ],
    "Shulk": [ # 16th Previously
        MatchResult("Shulk", "Link", 1, 0, 0),
        MatchResult("Shulk", "Link", 2, 0, 0),
        MatchResult("Shulk", "Link", 3, 0, 0),
    ],
    "Mii Swordfighter": [ # 17th Previously
        MatchResult("Mii Swordfighter", "Jigglypuff", 1, 2, 20),
        MatchResult("Mii Swordfighter", "Villager", 2, -1, 35),
    ],
    "Donkey Kong": [ # 18th Previously
        MatchResult("Donkey Kong", "Link", 1, 0, 0),
        MatchResult("Donkey Kong", "Link", 2, 0, 0),
        MatchResult("Donkey Kong", "Link", 3, 0, 0),
    ],
    "King K Rool": [ # 19th Previously
        MatchResult("King K Rool", "Toon Link", 1, 2, 16),
        MatchResult("King K Rool", "Byleth", 2, 2, 165),
        MatchResult("King K Rool", "Captain Falcon", 3, -2, 80),
    ],
    "King Dedede": [ # 20th Previously
        MatchResult("King Dedede", "Link", 1, 0, 0),
        MatchResult("King Dedede", "Link", 2, 0, 0),
        MatchResult("King Dedede", "Link", 3, 0, 0),
    ],
    "Duck Hunt": [ # 21st Previously
        MatchResult("Duck Hunt", "Link", 1, 0, 0),
        MatchResult("Duck Hunt", "Link", 2, 0, 0),
        MatchResult("Duck Hunt", "Link", 3, 0, 0),
    ],
    "Robin": [ # 22nd Previously
        MatchResult("Robin", "Link", 1, 0, 0),
        MatchResult("Robin", "Link", 2, 0, 0),
        MatchResult("Robin", "Link", 3, 0, 0),
    ],
    "Olimar": [ # 23rd Previously
        MatchResult("Olimar", "Link", 1, 0, 0),
        MatchResult("Olimar", "Link", 2, 0, 0),
        MatchResult("Olimar", "Link", 3, 0, 0),
    ],
    "Sora": [ # 24th Previously
        MatchResult("Sora", "Link", 1, 0, 0),
        MatchResult("Sora", "Link", 2, 0, 0),
        MatchResult("Sora", "Link", 3, 0, 0),
    ],
    "PacMan": [ # 25th Previously
        MatchResult("PacMan", "Link", 1, 0, 0),
        MatchResult("PacMan", "Link", 2, 0, 0),
        MatchResult("PacMan", "Link", 3, 0, 0),
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
        MatchResult("Ike", "Link", 1, 0, 0),
        MatchResult("Ike", "Link", 2, 0, 0),
        MatchResult("Ike", "Link", 3, 0, 0),
    ],
    "Hero": [ # 29th Previously
        MatchResult("Hero", "Palutena", 1, 3, 175),
        MatchResult("Hero", "PacMan", 2, 3, 85),
        MatchResult("Hero", "Mr Game & Watch", 3, 1, 0),
    ],
    "Jigglypuff": [ # 30th Previously
        MatchResult("Jigglypuff", "Link", 1, 0, 0),
        MatchResult("Jigglypuff", "Link", 2, 0, 0),
        MatchResult("Jigglypuff", "Link", 3, 0, 0),
    ],
    "Ganondorf": [ # 31st Previously
        MatchResult("Ganondorf", "Link", 1, 0, 0),
        MatchResult("Ganondorf", "Link", 2, 0, 0),
        MatchResult("Ganondorf", "Link", 3, 0, 0),
    ],
    "Wolf": [ # 32nd Previously
        MatchResult("Wolf", "Wii Fit Trainer", 1, 3, 108),
        MatchResult("Wolf", "Marth", 2, 2, 125),
        MatchResult("Wolf", "Shulk", 3, 3, 151),
        MatchResult("Wolf", "Ganondorf", 5, 3, 55),
    ],
    "Ice Climbers": [ # 33rd Previously
        MatchResult("Ice Climbers", "Link", 1, 0, 0),
        MatchResult("Ice Climbers", "Link", 2, 0, 0),
        MatchResult("Ice Climbers", "Link", 3, 0, 0),
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
        MatchResult("Kirby", "Link", 1, 0, 0),
        MatchResult("Kirby", "Link", 2, 0, 0),
        MatchResult("Kirby", "Link", 3, 0, 0),
    ],
    "Terry": [ # 37th Previously
        MatchResult("Terry", "Pyra & Mythra", 1, 3, 149),
        MatchResult("Terry", "Mega Man", 2, 0, 0),
        MatchResult("Terry", "Link", 3, 0, 0),
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
        MatchResult("Pit", "Link", 1, 0, 0),
        MatchResult("Pit", "Link", 2, 0, 0),
        MatchResult("Pit", "Link", 3, 0, 0),
    ],
    "Peach": [ # 41st Previously
        MatchResult("Peach", "Link", 1, 0, 0),
        MatchResult("Peach", "Link", 2, 0, 0),
        MatchResult("Peach", "Link", 3, 0, 0),
    ],
    "Young Link": [ # 42nd Previously
        MatchResult("Young Link", "Link", 1, 0, 0),
        MatchResult("Young Link", "Link", 2, 0, 0),
        MatchResult("Young Link", "Link", 3, 0, 0),
    ],
    "Mario": [ # 43rd Previously
        MatchResult("Mario", "Link", 1, 0, 0),
        MatchResult("Mario", "Link", 2, 0, 0),
        MatchResult("Mario", "Link", 3, 0, 0),
    ],
    "Greninja": [ # 44th Previously
        MatchResult("Greninja", "Link", 1, 0, 0),
        MatchResult("Greninja", "Link", 2, 0, 0),
        MatchResult("Greninja", "Link", 3, 0, 0),
    ],
    "Wii Fit Trainer": [ # 45th Previously
        MatchResult("Wii Fit Trainer", "Link", 1, 0, 0),
        MatchResult("Wii Fit Trainer", "Link", 2, 0, 0),
        MatchResult("Wii Fit Trainer", "Link", 3, 0, 0),
    ],
    "Dark Pit": [ # 46th Previously
        MatchResult("Dark Pit", "Pichu", 1, 2, 81),
        MatchResult("Dark Pit", "Wario", 2, 2, 88),
        MatchResult("Dark Pit", "Roy", 3, 2, 35),
        MatchResult("Dark Pit", "Captain Falcon", 5, 2, 92),
    ],
    "Sheik": [ # 47th Previously
        MatchResult("Sheik", "Greninja", 1, 2, 21),
        MatchResult("Sheik", "Steve", 2, 0, 0),
        MatchResult("Sheik", "Link", 3, 0, 0),
    ],
    "Inkling": [ # 48th Previously
        MatchResult("Inkling", "Link", 1, 0, 0),
        MatchResult("Inkling", "Link", 2, 0, 0),
        MatchResult("Inkling", "Link", 3, 0, 0),
    ],
    "Luigi": [ # 49th Previously
        MatchResult("Luigi", "Steve", 1, 1, 40),
        MatchResult("Luigi", "Rosalina & Luma", 2, 2, 39),
        MatchResult("Luigi", "Snake", 3, 2, 83),
    ],
    "Pokemon Trainer": [ # 50th Previously
        MatchResult("Pokemon Trainer", "Link", 1, 0, 0),
        MatchResult("Pokemon Trainer", "Link", 2, 0, 0),
        MatchResult("Pokemon Trainer", "Link", 3, 0, 0),
    ],
    "Ryu": [ # 51st Previously
        MatchResult("Ryu", "Link", 1, 0, 0),
        MatchResult("Ryu", "Link", 2, 0, 0),
        MatchResult("Ryu", "Link", 3, 0, 0),
    ],
    "Diddy Kong": [ # 52nd Previously
        MatchResult("Diddy Kong", "Link", 1, 0, 0),
        MatchResult("Diddy Kong", "Link", 2, 0, 0),
        MatchResult("Diddy Kong", "Link", 3, 0, 0),
    ],
    "Simon": [ # 53rd Previously
        MatchResult("Simon", "Joker", 1, 1, 32),
        MatchResult("Simon", "ROB", 2, 2, 80),
        MatchResult("Simon", "Young Link", 3, 1, 0),
    ],
    "Sonic": [ # 54th Previously
        MatchResult("Sonic", "Link", 1, 0, 0),
        MatchResult("Sonic", "Link", 2, 0, 0),
        MatchResult("Sonic", "Link", 3, 0, 0),
    ],
    "Zero Suit Samus": [ # 55th Previously
        MatchResult("Zero Suit Samus", "Link", 1, 0, 0),
        MatchResult("Zero Suit Samus", "Link", 2, 0, 0),
        MatchResult("Zero Suit Samus", "Link", 3, 0, 0),
    ],
    "Richter": [ # 56th Previously
        MatchResult("Richter", "Toon Link", 1, 2, 21),
        MatchResult("Richter", "Pikachu", 2, 2, 88),
        MatchResult("Richter", "ROB", 3, 2, 130),
    ],
    "ROB": [ # 57th Previously
        MatchResult("ROB", "Link", 1, 0, 0),
        MatchResult("ROB", "Link", 2, 0, 0),
        MatchResult("ROB", "Link", 3, 0, 0),
    ],
    "Lucina": [ # 58th Previously
        MatchResult("Lucina", "Link", 1, 0, 0),
        MatchResult("Lucina", "Link", 2, 0, 0),
        MatchResult("Lucina", "Link", 3, 0, 0),
    ],
    "Ken": [ # 59th Previously
        MatchResult("Ken", "Link", 1, 0, 0),
        MatchResult("Ken", "Link", 2, 0, 0),
        MatchResult("Ken", "Link", 3, 0, 0),
    ],
    "Captain Falcon": [ # 60th Previously
        MatchResult("Captain Falcon", "Link", 1, 0, 0),
        MatchResult("Captain Falcon", "Link", 2, 0, 0),
        MatchResult("Captain Falcon", "Link", 3, 0, 0),
    ],
    "Pyra & Mythra": [ # 61st Previously
        MatchResult("Pyra & Mythra", "Jigglypuff", 1, 3, 153),
        MatchResult("Pyra & Mythra", "Sora", 2, 0, 0),
        MatchResult("Pyra & Mythra", "Link", 3, 0, 0),
    ],
    "Samus": [ # 62nd Previously
        MatchResult("Samus", "Link", 1, 0, 0),
        MatchResult("Samus", "Link", 2, 0, 0),
        MatchResult("Samus", "Link", 3, 0, 0),
    ],
    "Link": [ # 63rd Previously
        MatchResult("Link", "Link", 1, 0, 0),
        MatchResult("Link", "Link", 2, 0, 0),
        MatchResult("Link", "Link", 3, 0, 0),
    ],
    "Isabelle": [ # 64th Previously
        MatchResult("Isabelle", "Link", 1, 0, 0),
        MatchResult("Isabelle", "Link", 2, 0, 0),
        MatchResult("Isabelle", "Link", 3, 0, 0),
    ],
    "Wario": [ # 65th Previously
        MatchResult("Wario", "Link", 1, 0, 0),
        MatchResult("Wario", "Link", 2, 0, 0),
        MatchResult("Wario", "Link", 3, 0, 0),
    ],
    "Little Mac": [ # 66th Previously
        MatchResult("Little Mac", "Link", 1, 0, 0),
        MatchResult("Little Mac", "Link", 2, 0, 0),
        MatchResult("Little Mac", "Link", 3, 0, 0),
    ],
    "Mii Brawler": [ # 67th Previously
        MatchResult("Mii Brawler", "Link", 1, 0, 0),
        MatchResult("Mii Brawler", "Link", 2, 0, 0),
        MatchResult("Mii Brawler", "Link", 3, 0, 0),
    ],
    "Mega Man": [ # 68th Previously
        MatchResult("Mega Man", "Link", 1, 0, 0),
        MatchResult("Mega Man", "Link", 2, 0, 0),
        MatchResult("Mega Man", "Link", 3, 0, 0),
    ],
    "Fox": [ # 69th Previously
        MatchResult("Fox", "Link", 1, 0, 0),
        MatchResult("Fox", "Link", 2, 0, 0),
        MatchResult("Fox", "Link", 3, 0, 0),
    ],
    "Villager": [ # 70th Previously
        MatchResult("Villager", "Duck Hunt", 1, 2, 12),
        MatchResult("Villager", "Link", 2, 0, 0),
        MatchResult("Villager", "Link", 3, 0, 0),
    ],
    "Meta Knight": [ # 71st Previously
        MatchResult("Meta Knight", "Link", 1, 0, 0),
        MatchResult("Meta Knight", "Link", 2, 0, 0),
        MatchResult("Meta Knight", "Link", 3, 0, 0),
    ],
    "Mewtwo": [ # 72nd Previously
        MatchResult("Mewtwo", "Lucina", 1, 2, 0),
        MatchResult("Mewtwo", "Joker", 2, 2, 65),
        MatchResult("Mewtwo", "Ganondorf", 3, 1, 101),
    ],
}

def main() -> None:
    manager = TournamentManager(
        records_dir=RECORDS_DIR,
        reports_dir=REPORTS_DIR,
        ranking_changes_dir=RANKING_CHANGES_DIR,
        matchup_df=MATCHUP_DF,
    )
    round_1_summary: RoundSummary | None = None
    if ROUND_1_MATCHES:
        seed_order = list(ROUND_1_MATCHES.keys())
        round_1_summary = manager.bootstrap_round_from_matches(1, ROUND_1_MATCHES)
        #print("Rebuilt Round 1 from in-file match data.")
        #print(round_1_summary.scores)
        manager._ranking_changes_black_arrows(seed_order, round_1_summary.scores, round_number=1)
    round_2_summary: RoundSummary | None = None
    if ROUND_2_MATCHES and round_1_summary is not None:
        seed_order = [character for character, _score in sorted(round_1_summary.scores.items(), key=lambda item: item[1], reverse=True)]
        round_2_summary = manager.bootstrap_round_from_matches(2, ROUND_2_MATCHES, previous_scores=round_1_summary.scores)
        ordered_summary = {character: round_2_summary.scores[character] for character in seed_order if character in round_2_summary.scores}
        #print("Rebuilt Round 2 from in-file match data.")
        #print(ordered_summary)
        manager._ranking_changes_black_arrows(seed_order, round_2_summary.scores, round_number=2)
    elim_1_summary: RoundSummary | None = None
    if ELIMINATION_1_MATCHES and round_2_summary is not None:
        reduced_scores = apply_score_reduction(round_2_summary.scores)
        elim_1_summary = manager.bootstrap_round_from_matches(3, ELIMINATION_1_MATCHES, previous_scores=reduced_scores)
        ordered_summary = dict(sorted(elim_1_summary.scores.items(), key=lambda item: item[1], reverse=True))
        #print("Rebuilt Elimination 1 from in-file match data.")
        #print(ordered_summary)
    if ROUND_3_MATCHES and elim_1_summary is not None:
        elimination_characters = set(ELIMINATION_1_MATCHES.keys())
        round_3_start_scores = apply_selective_score_reduction(elim_1_summary.scores, elimination_characters, exponent=0.53955)
        round_3_summary = manager.bootstrap_round_from_matches(4, ROUND_3_MATCHES, previous_scores=round_3_start_scores)
        ordered_summary = dict(sorted(round_3_summary.scores.items(), key=lambda item: item[1], reverse=True))
        print("Rebuilt Round 3 from in-file match data.")
        print(ordered_summary)

    final_scores = manager.run()
    #print("Tournament rerun complete.")
    #print(final_scores)

if __name__ == "__main__":
    main()

########################################################
####################### ROUND 23 #######################
########################################################

'''

#######################################################
####################### ROUND 1 #######################
#######################################################

"""

Round 1 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 200

ex) Terry v Ryu 2 Stock 129 percent (floor)
2pts for 2 Stock_Diff
125 <= 129 < 130 so 0.05*7 = 0.35
Total Pts = 2.35pts

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 200%

ex) Megaman v Wii Fit Trainer
0pts for 0 Stocks
0.05pts*100/10% = 0.5pts

Bonus Match Points are Divided by Round Number

"""

def round_1_calculator(Tourney_List, max_percentage, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    character_dict = {}
    for tourney in Tourney_List:
        for key in tourney:
            character_dict[key] = 0
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict

loss_dict = defaultdict(int)

def round_1_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/total)/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 1: Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 1: Score Comparisons", pdf)
    table_generator(win_loss_characters, "Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 1: Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 1: Score Density Plot", pdf)


#####################
###### Matches ######
#####################

Tourney_1 = {
        "Mega Man": [["Wii Fit Trainer", [-1, 108]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Diddy Kong": [["Kazuya", [-1, 19]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Terry": [["Ryu", [2, 129]], ["Mr Game & Watch", [2, 105]], ["Sheik", [2, 84]], ["Bowser Jr", [2, 130]], ["Kazuya", [-1, 27]]],          
        "Palutena": [["Inkling", [-2, 60]],  ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]]
        }

Tourney_2 = {
        "Marth": [["Ridley", [1, 0]], ["Mega Man", [-1, 14]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Luigi": [["Inkling", [1, 102]], ["Sheik", [2, 52]], ["Greninja", [1, 139]], ["Lucario", [1, 53]], ["Opponent 5", [0, 0]]], 
        "Ken": [["Steve", [-1, 50]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Pit": [["King K Rool", [1, 0]], ["Chrom", [1, 0]], ["Pikachu", [2, 144]], ["Dr Mario", [1, 104]], ["Opponent 5", [0, 0]]] 
        }

Tourney_3 = {
        "Kazuya": [["Villager", [-1, 73]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Banjo & Kazooie": [["Captain Falcon", [3, 107]], ["Peach", [2, 35]], ["Sonic", [2, 99]], ["Young Link", [2, 106]], ["Opponent 5", [0, 0]]], 
        "Little Mac": [["Steve", [-1, 35]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Isabelle": [["Bowser", [2, 73]], ["Ken", [2, 80]], ["Mewtwo", [1, 0]], ["Bowser Jr", [2, 39]], ["Opponent 5", [0, 0]]] 
        }

Tourney_4 = {
        "Ganondorf": [["Dark Samus", [2, 72]], ["King Dedede", [1, 84]], ["Corrin", [2, 90]], ["Captain Falcon", [1, 0]], ["Opponent 5", [0, 0]]], 
        "Lucina": [["Cloud", [1, 104]], ["Captain Falcon", [-1, 84]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Ike": [["Peach", [1, 62]], ["Sonic", [2, 102]], ["Ridley", [2, 111]], ["Steve", [2, 141]], ["Opponent 5", [0, 0]]],          
        "Samus": [["Lucario", [-2, 89]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_5 = {
        "Donkey Kong": [["Richter", [2, 70]], ["Ken", [2, 137]], ["Ryu", [3, 122]], ["Opponent 4", [0, 0]], ["Sora", [2, 130]]], 
        "Hero": [["Pit", [2, 89]], ["Ganondorf", [1, 73]], ["Mewtwo", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Villager": [["Lucas", [1, 83]], ["Mario", [2, 87]], ["Sora", [-1, 96]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Greninja": [["Pichu", [2, 36]], ["Isabelle", [1, 56]], ["Pyra & Mythra", [2, 63]], ["Sora", [-1, 62]], ["Opponent 5", [0, 0]]] 
        }

Tourney_6 = {
        "Sheik": [["Lucina", [1, 11]], ["Falco", [2, 68]], ["Inkling", [-1, 21]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Dr Mario": [["Kirby", [1, 93]], ["Ridley", [2, 71]], ["Rosalina & Luma", [2, 27]], ["Inkling", [3, 180]], ["Opponent 5", [0, 0]]], 
        "Kirby": [["Mega Man", [1, 93]], ["Bayonetta", [2, 25]], ["Duck Hunt", [-1, 128]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Snake": [["Dark Pit", [3, 155]], ["Incineroar", [1, 16]], ["Fox", [1, 89]], ["Duck Hunt", [3, 150]], ["Opponent 5", [0, 0]]] 
        }

Tourney_7 = {
        "Inkling": [["Rosalina & Luma", [2, 116]], ["Young Link", [1, 0]], ["Richter", [1, 111]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "King K Rool": [["Olimar", [1, 5]], ["Samus", [2, 117]], ["Lucario", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Yoshi": [["Mega Man", [2, 56]], ["Piranha Plant", [2, 83]], ["Terry", [2, 80]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Zero Suit Samus": [["Byleth", [2, 123]], ["Peach", [1, 45]], ["Lucas", [1, 27]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_8 = {
        "Rosalina & Luma": [["Incineroar", [1, 19]], ["Zelda", [-1, 22]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Wario": [["Ridley", [2, 66]], ["Richter", [2, 154]], ["Duck Hunt", [2, 193]], ["Hero", [1, 121]], ["Opponent 5", [0, 0]]], 
        "ROB": [["Pit", [-1, 54]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Lucas": [["Yoshi", [2, 146]], ["Simon", [3, 87]], ["Terry", [2, 57]], ["Pit", [2, 95]], ["Opponent 5", [0, 0]]] 
        }

Tourney_9 = {
        "Pikachu": [["Zero Suit Samus", [3, 94]], ["Bowser Jr", [2, 80]], ["Little Mac", [1, 47]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Falco": [["Sheik", [1, 109]], ["Mario", [1, 143]], ["King K Rool", [1, 31]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Bowser": [["Kirby", [2, 73]], ["Simon", [3, 149]], ["Pichu", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Ness": [["Sonic", [1, 100]], ["Bayonetta", [2, 18]], ["Mewtwo", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_10 = {
        "Duck Hunt": [["Robin", [2, 101]], ["Mewtwo", [2, 68]], ["Palutena", [2, 94]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Link": [["Bayonetta", [2, 0]], ["Kirby", [1, 55]], ["Jigglypuff", [2, 111]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Toon Link": [["Steve", [1, 0]], ["Piranha Plant", [2, 89]], ["Zero Suit Samus", [2, 104]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Ice Climbers": [["Captain Falcon", [2, 90]], ["Yoshi", [2, 114]], ["Kazuya", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_11 = {
        "Ryu": [["Mario", [1, 151]], ["Little Mac", [2, 86]], ["Marth", [-1, 106]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Jigglypuff": [["Dr Mario", [1, 39]], ["Zelda", [-1, 7]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Lucario": [["Samus", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Mr Game & Watch": [["Wii Fit Trainer", [1, 15]], ["Richter", [1, 38]], ["Meta Knight", [2, 117]], ["Peach", [2, 121]], ["Marth", [2, 130]]] 
        }

Tourney_12 = {
        "Cloud": [["Pit", [2, 117]], ["Duck Hunt", [3, 141]], ["Min Min", [1, 7]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mewtwo": [["Young Link", [2, 114]], ["Ice Climbers", [1, 55]], ["Little Mac", [2, 46]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Wii Fit Trainer": [["Lucas", [1, 107]], ["Wario", [1, 107]], ["Donkey Kong", [1, 98]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Robin": [["Olimar", [1, 0]], ["Pikachu", [1, 110]], ["Luigi", [1, 48]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_13 = {
        "Steve": [["Captain Falcon", [-1, 23]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Chrom": [["Ridley", [2, 134]], ["Sora", [1, 0]], ["Isabelle", [2, 36]], ["Captain Falcon", [-1, 112]], ["Opponent 5", [0, 0]]], 
        "Meta Knight": [["Kirby", [-2, 161]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Dark Samus": [["Villager", [-1, 84]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_14 = {
        "Incineroar": [["Dr Mario", [2, 67]], ["Shulk", [1, 61]], ["Captain Falcon", [2, 63]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Sora": [["Wii Fit Trainer", [2, 47]], ["Pit", [2, 81]], ["Banjo & Kazooie", [1, 71]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Fox": [["Jigglypuff", [2, 52]], ["Sheik", [1, 6]], ["Pikachu", [1,13]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Roy": [["Ryu", [2, 46]], ["Ike", [2, 116]], ["Duck Hunt", [2, 92]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_15 = {
        "Sephiroth": [["Greninja", [2, 36]], ["ROB", [3, 97]], ["Samus", [1, 0]], ["Ridley", [1, 29]], ["Opponent 5", [0, 0]]], 
        "Olimar": [["Bowser", [1, 97]], ["Ridley", [-2, 63]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "King Dedede": [["Cloud", [3, 103]], ["Villager", [1, 30]], ["Mewtwo", [1, 37]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Captain Falcon": [["Bayonetta", [2, 0]], ["Roy", [2, 79]], ["Marth", [2, 119]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_16 = {
        "Daisy": [["Wii Fit Trainer", [2, 133]], ["King Dedede", [-2, 83]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Peach": [["Mega Man", [1, 13]], ["Palutena", [1, 0]], ["ROB", [-1, 6]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Pyra & Mythra": [["Bowser Jr", [1, 30]], ["Pichu", [1, 55]], ["Donkey Kong", [1, 93]], ["Ness", [2, 106]], ["Rob", [2, 117]]],          
        "Corrin": [["Marth", [2, 111]], ["Ness", [-1, 70]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_17 = {
        "Joker": [["Lucario", [-1, 63]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mii Swordfighter": [["Mega Man", [1, 17]], ["Samus", [1, 0]], ["Richter", [2, 96]], ["Ness", [-1, 75]], ["Opponent 5", [0, 0]]], 
        "Dark Pit": [["Chrom", [3, 142]], ["Young Link", [2, 77]], ["King Dedede", [1, 110]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Byleth": [["Lucas", [2, 67]], ["Wii Fit Trainer", [2, 60]], ["ROB", [1, 5]], ["Ness", [1, 0]], ["Opponent 5", [0, 0]]] 
        } 

Tourney_18 = {
        "Sonic": [["Joker", [1, 71]], ["Greninja", [3, 105]], ["Toon Link", [1, 15]], ["Pyra & Mythra", [2, 174]], ["Ryu", [2, 134]]], 
        "Mii Brawler": [["Pyra & Mythra", [-2, 143]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mario": [["Falco", [-1, 47]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Bayonetta": [["Olimar", [-2, 86]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_19 = {
        "PacMan": [["Pichu", [1, 84]], ["ROB", [-1, 16]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Pokemon Trainer": [["Palutena", [2, 36]], ["Cloud", [-1, 90]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Zelda": [["Inkling", [1, 0]], ["Ken", [2, 68]], ["Wario", [2, 0]], ["Opponent 4", [0, 0]], ["Lucina", [2, 144]]],          
        "Wolf": [["Greninja", [3, 165]], ["Bowser Jr", [1, 56]], ["Dr Mario", [1, 14]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_20 = {
        "Min Min": [["Steve", [1, 12]], ["Diddy Kong", [2, 129]], ["Pyra & Mythra", [2, 53]], ["Lucina", [1, 36]], ["Villager", [1, 54]]], 
        "Simon": [["Lucina", [-2, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Bowser Jr": [["Banjo & Kazooie", [1, 105]], ["Villager", [-1, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Shulk": [["Zelda", [2, 107]], ["Roy", [2, 54]], ["Link", [-1, 77]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_21 = {
        "Richter": [["Palutena", [1, 37]], ["Hero", [-1, 76]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mii Gunner": [["Wolf", [1, 21]], ["Banjo & Kazooie", [-1, 96]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Piranha Plant": [["Dark Samus", [2, 128]], ["Pichu", [3, 155]], ["Simon", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Young Link": [["Kirby", [1, 37]], ["Roy", [3, 93]], ["Ridley", [2, 24]], ["Opponent 4", [0, 0]], ["Bayonetta", [2, 12]]] 
        }

Tourney_22 = {
        "Ridley": [["Ryu", [2, 38]], ["Ken", [2, 114]], ["Ganondorf", [2, 111]], ["Dark Pit", [1, 36]], ["Daisy", [3, 137]]],          
        "Pichu": [["Link", [-1, 81]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]]
        }

Tourney_List = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9, Tourney_10,
                Tourney_11, Tourney_12, Tourney_13, Tourney_14, Tourney_15, Tourney_16, Tourney_17, Tourney_18, Tourney_19,
                Tourney_20, Tourney_21, Tourney_22]

Tourney_List_1 = Tourney_List

max_percentage = 200
character_dict, win_loses, characters_played, all_characters, loss_dict = round_1_calculator(Tourney_List, max_percentage, loss_dict)
round_1_scores_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_1_scores_dict)
round_1_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_1_loss_dict)

################
#### Report ####
################

with PdfPages("reports/round_1_results.pdf") as pdf:
    round_1_generator(character_dict, win_loses, pdf)

##################
#### ANALYSIS ####
##################

def line_plot(original_scores, renormalized_scores, x_axis, y_axis, title, pdf):

    old_scores = [score for player, score in original_scores.items()][::-1]
    renormalized = [score for player, score in renormalized_scores.items()][::-1]
    x = range(len(old_scores))  # x-axis positions
    
    # Create line plot
    plt.plot(x, old_scores, marker='o', label="Previous Round Scores")
    plt.plot(x, renormalized, marker='s', label="Renormalized Scores")
    
    # Add labels and title
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.legend()
    pdf.savefig()   # save current plt figure
    plt.close() 

def round_1_score_distribution_evolution(Tourney_Lists, loss_dict):
    
    with PdfPages("reports/round_1_histogram_evolution.pdf") as pdf:
        for i in range(11):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, win_loses, characters_played, all_characters, loss_dict = round_1_calculator(Tourney_List, max_percentage, loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 1: Score Distribution", pdf)
    
    with PdfPages("reports/round_1_distribution_evolution.pdf") as pdf:
        for i in range(11):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, win_loses, characters_played, all_characters, loss_dict = round_1_calculator(Tourney_List, max_percentage, loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 1: Score Distribution", pdf)

copy_loss_dict = loss_dict.copy()
round_1_score_distribution_evolution(Tourney_List_1, copy_loss_dict)

def round_1_renormalizer(character_dict):
    
    round_1_scores = [score for key, score in round_1_scores_dict.items()]
    min_score, max_score = min(round_1_scores), max(round_1_scores)
    for character, score in round_1_scores_dict.items(): 
        character_dict[character] = int(2000*np.sqrt(10*((2.0 + score)**(3/2))/(max_score-min_score)))/2000
        
    return character_dict

character_dict = round_1_renormalizer(character_dict)

renormalized_scores = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False)).copy()
# print_sorted_dict(renormalized_scores)

# for rank changes visual (Round 2 starts from these renormalized scores)
inital_round_2_scores = renormalized_scores.copy()

with PdfPages("reports/round_1_to_2_transition.pdf") as pdf:

    # Score Comparison
    line_plot(round_1_scores_dict, renormalized_scores, "Rank", "Score","Comparison of Previous Round vs Renormalized Scores", pdf)
    
    # Score Distributions
    histogram_generator(round_1_scores_dict, "Score", "Frequency", "End of Round 1 Scores: Score Distribution", pdf)
    histogram_generator(renormalized_scores, "Score", "Frequency", "Renormalized Pre Round 2: Score Distribution", pdf)
    distribution_generator(round_1_scores_dict, "Score", "Density", "End of Round 1 Scores: Score Density Plot", pdf)
    distribution_generator(renormalized_scores, "Score", "Density", "Renormalized Pre Round 2: Score Density Plot", pdf)

#%%
#######################################################
####################### ROUND 2 #######################
#######################################################

"""

Recalculated Scores

new_score = sqrt ( 10 x (score + 2)^(3/2) / (score_range) )

Round 2 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number - 1)*0.25)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number - 1)*0.25)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_2_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n*0.25)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1 + n*0.25)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.25)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.25)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_2_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 2: Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 2: Score Comparisons", pdf)
    table_generator(win_loss_characters, "Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 2: Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 2: Score Density Plot", pdf)

#############################
###### ROUND 2 Matches ######
#############################

Tourney_1 = {
        "Simon": [["Greninja", [1, 101]], ["Yoshi", [-1, 58]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Palutena": [["Mewtwo", [2, 177]], ["Lucina", [2, 47]], ["Olimar", [2, 178]], ["Peach", [2, 102]], ["Opponent 5", [0, 0]]], 
        "Samus": [["Byleth", [2, 182]], ["Fox", [1, 168]], ["Young Link", [2, 6]], ["Wolf", [2, 106]], ["Opponent 5", [0, 0]]],          
        "Bayonetta": [["Incineroar", [1, 99]], ["Wolf", [-1, 38]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_2 = {
        "Steve": [["Ice Climbers", [2, 94]], ["Ken", [2, 62]], ["Zero Suit Samus", [2, 68]], ["Lucina", [2, 94]], ["Kazuya", [-1, 35]]], 
        "Diddy Kong": [["Wario", [1, 36]], ["King K Rool", [1, 41]], ["Lucina", [-2, 69]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Meta Knight": [["Wolf", [2, 102]], ["Yoshi", [-1, 34]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Mii Gunner": [["Rosalina & Luma", [2, 0]], ["Kazuya", [-2, 62]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_3 = {
        "Little Mac": [["Meta Knight", [1, 70]], ["Mewtwo", [2, 36]], ["Dark Pit", [2, 24]], ["Ganondorf", [2, 78]], ["Opponent 5", [0, 0]]], 
        "Mii Brawler": [["Palutena", [2, 100]], ["PacMan", [2, 0]], ["Ganondorf", [-1, 96]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mario": [["Chrom", [2, 0]], ["Ice Climbers", [2, 102]], ["King K Rool", [2, 105]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "ROB": [["Richter", [2, 78]], ["Lucas", [3, 80]], ["Bayonetta", [2, 81]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_4 = {
        "Ken": [["Chrom", [-2, 56]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Pichu": [["Terry", [1, 82]], ["Shulk", [1, 24]], ["Captain Falcon", [-1, 32]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Joker": [["King Dedede", [-1, 96]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Kazuya": [["Kazuya", [-1, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_5 = {
        "Dark Samus": [["Ken", [2, 91]], ["Bowser Jr", [1, 20]], ["Ganondorf", [2, 0]], ["Sephiroth", [2, 93]], ["Opponent 5", [0, 0]]], 
        "Mega Man": [["Mewtwo", [-1, 36]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Lucario": [["Min Min", [2, 140]], ["Luigi", [3, 167]], ["Ryu", [2, 112]], ["Inkling", [2, 40]], ["Opponent 5", [0, 0]]],          
        "Olimar": [["Roy", [2, 42]], ["Villager", [2, 69]], ["Inkling", [-1, 130]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_6 = {
        "PacMan": [["Min Min", [1, 3]], ["Yoshi", [2, 211]], ["Roy", [2, 6]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Bowser Jr": [["Kirby", [2, 39]], ["Lucas", [2, 56]], ["Captain Falcon", [2, 77]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Jigglypuff": [["Mr Game & Watch", [1, 21]], ["Joker", [1, 17]], ["Samus", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Daisy": [["Dark Samus", [2, 128]], ["Dark Pit", [2, 122]], ["Pikachu", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_7 = {
        "Marth": [["Richter", [2, 164]], ["Palutena", [2, 78]], ["Meta Knight", [-1, 124]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Rosalina & Luma": [["Kirby", [2, 114]], ["Ridley", [1, 69]], ["Incineroar", [-1, 81]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Richter": [["Daisy", [2, 108]], ["Steve", [1, 0]], ["Diddy Kong", [1, 133]], ["Kazuya", [-1, 81]], ["Opponent 5", [0, 0]]],          
        "Lucina": [["Hero", [2, 82]], ["Sora", [-1, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_8 = {
        "Peach": [["Wii Fit Trainer", [1, 57]], ["Shulk", [1, 35]], ["Duck Hunt", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Corrin": [["Marth", [2, 67]], ["Sephiroth", [1, 37]], ["Ridley", [2, 34]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Falco": [["Isabelle", [3, 185]], ["Rosalina & Luma", [2, 106]], ["Roy", [2, 47]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Pokemon Trainer": [["Daisy", [2, 136]], ["Dark Pit", [1, 175]], ["Zero Suit Samus", [3, 126]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_9 = {
        "Ryu": [["Mario", [-1, 97]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Villager": [["Piranha Plant", [1, 110]], ["Young Link", [-1, 61]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Wii Fit Trainer": [["Corrin", [1, 46]], ["Ken", [2, 128]], ["Byleth", [2, 109]], ["Opponent 4", [0, 0]], ["Roy", [1, 15]]],          
        "Sheik": [["Toon Link", [1, 0]], ["Samus", [2, 169]], ["Lucario", [1, 63]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_10 = {
        "Luigi": [["Isabelle", [1, 86]], ["Peach", [1, 58]], ["Pikachu", [2, 27]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Shulk": [["Terry", [1, 0]], ["Duck Hunt", [1, 0]], ["Link", [1, 35]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Robin": [["Meta Knight", [1, 17]], ["Mega Man", [2, 27]], ["Mr Game & Watch", [2, 47]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Kirby": [["Diddy Kong", [3, 114]], ["Ice Climbers", [2, 35]], ["Mario", [1, 71]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_11 = {
        "Zero Suit Samus": [["Shulk", [1, 89]], ["Yoshi", [1, 63]], ["Marth", [1, 73]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Ness": [["Meta Knight", [1, 29]], ["Lucas", [2, 68]], ["Incineroar", [1, 11]], ["Opponent 4", [0, 0]], ["Kazuya", [-2, 163]]], 
        "Inkling": [["Roy", [1, 71]], ["Samus", [2, 79]], ["Simon", [2, 112]], ["Kazuya", [-1, 73]], ["Opponent 5", [0, 0]]],          
        "Pyra & Mythra": [["Diddy Kong", [2, 56]], ["Bowser Jr", [1, 26]], ["Kazuya", [-1, 49]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_12 = {
        "Pit": [["Dark Samus", [2, 118]], ["Ness", [2, 172]], ["Isabelle", [2, 61]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Sora": [["ROB", [2, 51]], ["Sheik", [2, 76]], ["King Dedede", [1, 28]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Wolf": [["Mewtwo", [3, 110]], ["Inkling", [2, 126]], ["Joker", [2, 89]], ["Corrin", [2, 104]], ["Opponent 5", [0, 0]]],          
        "Fox": [["Villager", [1, 111]], ["Corrin", [-2, 92]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_13 = {
        "Mii Swordfighter": [["Meta Knight", [1, 54]], ["Zero Suit Samus", [2, 43]], ["Lucario", [2, 155]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Ganondorf": [["Ness", [2, 59]], ["Mario", [2, 138]], ["King K Rool", [2, 75]], ["Opponent 4", [0, 0]], ["Simon", [3, 137]]], 
        "Mr Game & Watch": [["King Dedede", [-1, 96]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Roy": [["Sonic", [2, 0]], ["Banjo & Kazooie", [-2, 59]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_14 = {
        "Toon Link": [["King K Rool", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Cloud": [["Shulk", [2, 8]], ["Ganondorf", [2, 67]], ["Duck Hunt", [1, 128]], ["Mario", [2, 53]], ["Opponent 5", [0, 0]]], 
        "Hero": [["Incineroar", [2, 91]], ["Simon", [2, 0]], ["Robin", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Dark Pit": [["Ness", [2, 100]], ["Banjo & Kazooie", [2, 120]], ["Snake", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_15 = {
        "Incineroar": [["King Dedede", [2, 90]], ["Corrin", [2, 69]], ["Rosalina & Luma", [3, 177]], ["Ike", [2, 70]], ["Opponent 5", [0, 0]]], 
        "Snake": [["King K Rool", [-1, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Wario": [["Isabelle", [1, 16]], ["Ridley", [1, 0]], ["Sora", [2, 113]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Greninja": [["Zelda", [1, 77]], ["Kirby", [1, 82]], ["Olimar", [1, 63]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_16 = {
        "Chrom": [["Simon", [2, 12]], ["Marth", [2, 11]], ["Snake", [2, 115]], ["Kirby", [2, 82]], ["Opponent 5", [0, 0]]], 
        "King Dedede": [["Richter", [3, 141]], ["Kirby", [-1, 25]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "King K Rool": [["Sheik", [2, 38]], ["Ice Climbers", [2, 98]], ["Kazuya", [1, 101]], ["Piranha Plant", [2, 126]], ["Opponent 5", [0, 0]]],          
        "Yoshi": [["Pyra & Mythra", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_17 = {
        "Mewtwo": [["Ridley", [2, 46]], ["Olimar", [1, 21]], ["Dark Pit", [-1, 127]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Sonic": [["Isabelle", [1, 59]], ["Robin", [2, 85]], ["Lucas", [2, 0]], ["Dark Pit", [2, 78]], ["Opponent 5", [0, 0]]], 
        "Pikachu": [["King Dedede", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Ike": [["Ganondorf", [1, 0]], ["Link", [2, 24]], ["Peach", [3, 109]], ["Hero", [1, 55]], ["Opponent 5", [0, 0]]] 
        }

Tourney_18 = {
        "Isabelle": [["Mr Game & Watch", [2, 170]], ["Falco", [2, 148]], ["Pyra & Mythra", [1, 32]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Young Link": [["Richter", [1, 74]], ["Wolf", [2, 68]], ["Bayonetta", [3, 189]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Dr Mario": [["Piranha Plant", [1, 152]], ["Zero Suit Samus", [3, 174]], ["Yoshi", [2, 16]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Captain Falcon": [["Villager", [1, 30]], ["Sonic", [2, 25]], ["Olimar", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_19 = {
        "Ice Climbers": [["Mr Game & Watch", [3, 75]], ["PacMan", [2, 0]], ["Sheik", [1, 30]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Link": [["Ryu", [2, 58]], ["Dark Pit", [2, 37]], ["Sonic", [3, 206]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Byleth": [["Inkling", [2, 108]], ["Bowser", [-1, 24]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Min Min": [["Mega Man", [1, 0]], ["Olimar", [1, 50]], ["Joker", [1, 90]], ["Corrin", [1, 3]], ["Opponent 5", [0, 0]]] 
        }

Tourney_20 = {
        "Bowser": [["Sora", [2, 114]], ["Sheik", [3, 178]], ["Luigi", [2, 80]], ["Opponent 4", [0, 0]], ["Lucas", [3, 110]]], 
        "Piranha Plant": [["Ken", [3, 136]], ["Ike", [2, 109]], ["Captain Falcon", [1, 98]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Duck Hunt": [["Wii Fit Trainer", [1, 0]], ["Pichu", [1, 49]], ["Daisy", [2, 30]], ["Lucas", [-1, 55]], ["Opponent 5", [0, 0]]],          
        "Terry": [["Inkling", [2, 168]], ["Lucas", [-1, 82]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_21 = {
        "Sephiroth": [["Isabelle", [3, 106]], ["Dark Samus", [2, 40]], ["Sheik", [2, 27]], ["Dr Mario", [-1, 75]], ["Opponent 5", [0, 0]]], 
        "Donkey Kong": [["Mr Game & Watch", [2, 5]], ["Greninja", [2, 153]], ["Dr Mario", [-1, 26]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Zelda": [["Lucas", [2, 0]], ["Young Link", [2, 106]], ["Lucina", [2, 107]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Ridley": [["Joker", [2, 80]], ["Wolf", [2, 132]], ["Meta Knight", [3, 127]], ["Opponent 4", [0, 0]], ["Dr Mario", [-2, 176]]] 
        }

Tourney_22 = {
        "Lucas": [["Duck Hunt", [2, 40]], ["King K Rool", [2, 34]], ["Pichu", [1, 0]], ["Dark Pit", [2, 53]], ["Opponent 5", [0, 0]]], 
        "Banjo & Kazooie": [["Steve", [1, 117]], ["Bayonetta", [2, 78]], ["Kirby", [2, 108]], ["Ryu", [2, 0]], ["Opponent 5", [0, 0]]], 
        }

Tourney_List = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9, Tourney_10,
                Tourney_11, Tourney_12, Tourney_13, Tourney_14, Tourney_15, Tourney_16, Tourney_17, Tourney_18, Tourney_19,
                Tourney_20, Tourney_21, Tourney_22]

Tourney_List_2 = Tourney_List

max_percentage = 200
character_dict, win_loses, characters_played, all_characters, loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, loss_dict)
round_2_scores_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_2_scores_dict)
round_2_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()
# print_sorted_dict(round_2_loss_dict)

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

with PdfPages("reports/round_2_results.pdf") as pdf:
    round_2_generator(character_dict, win_loses, pdf)

bottom_6 = {"Ken": 86, 
            "Kazuya": 85,
            "Mega Man": 84,
            "Joker": 83,
            "Simon": 82,
            "Bayonetta": 81}

eliminated_6 = {character for character in bottom_6}
            
copy_loss_dict = loss_dict.copy()

def round_2_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_2_histogram_evolution.pdf") as pdf:
        for i in range(11):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 2: Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_2_distribution_evolution.pdf") as pdf:
        for i in range(11):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 2: Score Distribution", pdf)   
            
round_2_score_distribution_evolution(Tourney_List_2, renormalized_scores, copy_loss_dict)

#%%
#########################################
################ ANALYSIS ###############
#########################################

def line_plot_2(original_scores, intermediate_scores, renormalized_scores, x_axis, y_axis, title, pdf):

    old_scores = [score for player, score in original_scores.items()][::-1]
    intermediate = [score for player, score in intermediate_scores.items()][::-1]
    renormalized = [score for player, score in renormalized_scores.items()][::-1]
    x = range(len(old_scores))  # x-axis positions
    
    # Create line plot
    plt.plot(x, old_scores, marker='o', label="Previous Round Scores")
    plt.plot(x, intermediate, marker='x', label="Intermediate Calculation Scores")
    plt.plot(x, renormalized, marker='s', label="Renormalized Scores")
    
    # Add labels and title
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.legend()
    pdf.savefig()   # save current plt figure
    plt.close() 

def round_2_renormalizer(round_2_scores_dict):
    
    renormalized_round_2 = {}
    intermediate_scores = {}
    round_2_scores = sorted(round_2_scores_dict.items(), key=lambda x: x[1])
    
    for i in range(5):
        quintile = dict(round_2_scores[i*16:(i+1)*16])
        median = round(statistics.median(list(quintile.values())), 4)
        minimum, maximum = min(list(quintile.values())), max(list(quintile.values()))
        score_range = maximum - minimum
        for character, score in quintile.items():
            intermediate_scores[character] = minimum + score_range/(1 + np.exp(-(5.0/score_range)*(score - median)))
            renormalized_round_2[character] = round(((intermediate_scores[character])**(1/2))*np.log(intermediate_scores[character]), 3)
    
    return intermediate_scores, renormalized_round_2
    
# to conform with quintile structure, we add previous data back in
for character in eliminated_6: del round_2_scores_dict[character]
intermediate_scores, renormalized_round_2_scores = round_2_renormalizer(round_2_scores_dict)
for character in eliminated_6: 
    intermediate_scores[character] = character_dict[character]
    renormalized_round_2_scores[character] = character_dict[character]
    round_2_scores_dict[character] = character_dict[character]
# print_sorted_dict(renormalized_round_2_scores)

with PdfPages("reports/round_2_to_3_transition.pdf") as pdf:

    # Score Comparison
    line_plot_2(round_2_scores_dict, intermediate_scores, renormalized_round_2_scores, "Rank", "Score","Comparison of Previous Round vs Renormalized Scores", pdf)
    
    # Score Distributions
    
    histogram_generator(round_2_scores_dict, "Score", "Frequency", "End of Round 2 Scores: Score Distribution", pdf)
    histogram_generator(renormalized_round_2_scores, "Score", "Frequency", "Renormalized Pre Round 3: Score Distribution", pdf)
    distribution_generator(round_2_scores_dict, "Score", "Density", "End of Round 2 Scores: Score Density Plot", pdf)
    distribution_generator(renormalized_round_2_scores, "Score", "Density", "Renormalized Pre Round 3: Score Density Plot", pdf)

#%%
#######################################################
####################### ROUND 3 #######################
#######################################################

"""

Recalculated Scores; Divided into Quintiles of 16 Characters each from 80th to 1st

median = round(statistics.median(list(quintile.values())), 4)
minimum, maximum = min(list(quintile.values())), max(list(quintile.values()))
score_range = maximum - minimum
intermediate_score = minimum + score_range/(1 + np.exp(-(5.0/score_range)*(score - median)))
new_score = S^(1/2)*log(S)

--> Essentially a Quintile Based Sigmoid then N^(1/2)LOG(N)

Round 3 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 175%
Score is Multiplied by (1 + (match_number - 1)*0.33)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 175%
Score is Multiplied by (1 + (match_number - 1)*0.33)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_3_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n*0.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1 + n*0.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_3_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 3: Rank 49 to 80 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 3: Rank 49 to 80 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 3: Rank 49 to 80 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 3: Rank 49 to 80 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 3: Rank 49 to 80 Score Density Plot", pdf)
    
###########################
###### Matches 80-49 ######
###########################

# Bottom 16 will be Eliminated
# Character List:
#
# 80 3.401 Meta Knight
# 79 3.557 Ryu
# 78 3.643 Diddy Kong
# 77 3.872 Lucina
# 76 3.939 Mii Gunner
# 75 4.181 Snake
# 74 4.448 Fox
# 73 4.477 Mr Game & Watch
# 72 4.563 Toon Link
# 71 4.677 Yoshi
# 70 4.724 Pikachu
# 69 4.771 Villager
# 68 4.976 Pichu
# 67 5.66 Roy
# 66 5.844 Rosalina & Luma
# 65 5.903 Terry
# 64 6.07 Byleth
# 63 6.125 Mii Brawler
# 62 6.139 King Dedede
# 61 6.155 Olimar
# 60 6.355 Marth
# 59 6.688 Samus
# 58 6.741 Pyra & Mythra
# 57 6.987 Richter
# 56 7.2 Daisy
# 55 7.316 Palutena
# 54 7.316 Peach
# 53 7.372 Zero Suit Samus
# 52 7.576 Shulk
# 51 7.621 Greninja
# 50 7.657 Sheik
# 49 7.681 Mario

Tourney_1 = {
    "Lucina": [["Piranha Plant", [-1, 176]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ryu": [["Pyra & Mythra", [2, 70]], ["Kazuya", [-2, 73]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Meta Knight": [["Diddy Kong", [3, 159]], ["Min Min", [2, 99]], ["Toon Link", [2, 58]], ["Jigglypuff", [1, 0]], ["Young Link", [2, 0]]],          
    "Diddy Kong": [["Simon", [-1, 128]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Mii Gunner": [["Fox", [2, 0]], ["Piranha Plant", [3, 182]], ["Sephiroth", [1, 13]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Fox": [["PacMan", [1, 14]], ["Peach", [2, 86]], ["Lucario", [2, 62]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Snake": [["Daisy", [-1, 54]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mr Game & Watch": [["Toon Link", [2, 148]], ["Sora", [1, 78]], ["Olimar", [2, 45]], ["Greninja", [2, 4]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Yoshi": [["Donkey Kong", [1, 0]], ["Chrom", [2, 78]], ["Incineroar", [2, 43]], ["Olimar", [2, 125]], ["Opponent 5", [0, 0]]], 
    "Villager": [["Link", [2, 105]], ["Joker", [2, 136]], ["Olimar", [-1, 6]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pikachu": [["Marth", [2, 130]], ["Banjo & Kazooie", [3, 171]], ["Wolf", [2, 52]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Toon Link": [["Bowser", [2, 113]], ["Fox", [2, 12]], ["Young Link", [2, 45]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Roy": [["Ken", [3, 124]], ["Greninja", [3, 176]], ["Diddy Kong", [2, 61]], ["Byleth", [1, 0]], ["Opponent 5", [0, 0]]], 
    "Pichu": [["Steve", [-1, 82]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Rosalina & Luma": [["Mr Game & Watch", [1, 0]], ["Wii Fit Trainer", [2, 68]], ["Corrin", [2, 115]], ["Palutena", [1, 116]], ["Opponent 5", [0, 0]]],          
    "Terry": [["Bowser", [-1, 156]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "Byleth": [["Marth", [2, 0]], ["Bayonetta", [3, 106]], ["Ridley", [-1, 13]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Olimar": [["Joker", [2, 68]], ["Ice Climbers", [-2, 70]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Mii Brawler": [["King K Rool", [1, 38]], ["Luigi", [2, 92]], ["Lucario", [2, 32]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "King Dedede": [["Fox", [2, 88]], ["Kazuya", [2, 146]], ["Pokemon Trainer", [2, 21]], ["Opponent 4", [0, 0]], ["Ice Climbers", [3, 115]]] 
    }

Tourney_6 = {
    "Marth": [["Wii Fit Trainer", [1, 0]], ["Olimar", [3, 97]], ["Bowser", [-1, 49]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pyra & Mythra": [["Marth", [3, 110]], ["ROB", [3, 189]], ["Ice Climbers", [2, 0]], ["Bowser", [-1, 99]], ["Opponent 5", [0, 0]]], 
    "Richter": [["Daisy", [2, 12]], ["Isabelle", [-2, 107]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Samus": [["Rosalina & Luma", [2, 12]], ["Pikachu", [1, 77]], ["Ganondorf", [2, 93]], ["Link", [3, 130]], ["Bowser", [2, 20]]] 
    }

Tourney_7 = {
    "Peach": [["Mario", [1, 56]], ["Marth", [1, 0]], ["Min Min", [1, 99]], ["Sora", [2, 26]], ["Donkey Kong", [2, 62]]], 
    "Daisy": [["Sora", [-2, 24]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Zero Suit Samus": [["King Dedede", [-1, 123]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Palutena": [["Pyra & Mythra", [1, 100]], ["Steve", [3, 136]], ["Donkey Kong", [-1, 81]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "Sheik": [["Chrom", [2, 116]], ["Bowser", [1, 120]], ["Pokemon Trainer", [1, 70]], ["Meta Knight", [2, 16]], ["Opponent 5", [0, 0]]], 
    "Shulk": [["Meta Knight", [-1, 95]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Greninja": [["Captain Falcon", [2, 119]], ["Joker", [-1, 72]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mario": [["Young Link", [3, 160]], ["Shulk", [2, 0]], ["Rosalina & Luma", [1, 72]], ["Toon Link", [1, 62]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_3 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8]

round_3_scores_dict = dict(sorted(renormalized_round_2_scores.items(), key=lambda x: x[1])[6:38])
inital_round_3_scores = round_3_scores_dict.copy()
max_percentage = 175
round_3_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_3_calculator(Tourney_List_3, max_percentage, round_3_scores_dict, loss_dict)
round_3_scores_dict = dict(sorted(round_3_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("Round 3 Scores")
# print_sorted_dict(round_3_scores_dict)
round_3_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()
# print_sorted_dict(round_3_loss_dict)

# Bottom 16 will be Eliminated
# Character List:
    
# 80 4.3 Diddy Kong
# 79 4.5 Snake
# 78 4.87 Lucina
# 77 5.34 Ryu
# 76 5.49 Pichu
# 75 6.38 Daisy
# 74 6.79 Terry
# 73 7.87 Olimar
# 72 8.0 Zero Suit Samus
# 71 8.06 Shulk
# 70 9.4 Richter
# 69 9.92 Villager
# 68 10.51 Greninja
# 67 13.24 Byleth
# 66 13.46 Fox
# 65 13.47 Marth

# Top 16 will Advance to Next Elimination (Top 64-??)
# Character List:
    
# 64 13.76 Palutena
# 63 13.82 Mii Gunner
# 62 14.88 Mr Game & Watch
# 61 15.3 Mii Brawler
# 60 15.5 Yoshi
# 59 15.59 Pikachu
# 58 15.67 Rosalina & Luma
# 57 15.75 Toon Link
# 56 15.78 Sheik
# 55 16.65 Peach
# 54 17.16 Meta Knight
# 53 17.75 Mario
# 52 18.39 Roy
# 51 18.43 King Dedede
# 50 18.57 Samus
# 49 19.08 Pyra & Mythra

#%%
##################################################
################### ANALYSIS #####################
##################################################

def records(Tourneys, record_dict, max_percentage=200):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    for Tourney_List in Tourneys:
        for tourney in Tourney_List:
            if tourney == example_tourney: 
                continue
            for character, fights in tourney.items():
                for n, fight in enumerate(fights):
                    matchup = 20 if not bool(fight[1][0]) else matchup_df[matchup_df["Character"] == character.lower()][fight[0].lower()].iloc[0]
                    if fight[1][0] > 0:
                        score = (fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                        record_dict[character].append([character, fight[0], n + 1, 1, 0, fight[1][0], fight[1][1], round(score, 3), matchup])
                    elif fight[1][0] < 0:
                        score = (1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                        record_dict[character].append([character, fight[0], n + 1, 0, 1, fight[1][0], fight[1][1], round(score, 3), matchup])
    
    record_df = pd.DataFrame()
    for character in record_dict:
        if record_dict[character]:
            record_dict[character] = np.array(record_dict[character])
            df = pd.DataFrame(record_dict[character], 
                              columns=['Character', 'Opponent', 'Round', 'Win', 'Loss', 
                                       'Stock Diff', 'Percentage', 'Score', 'Matchup'])
            record_df = pd.concat([record_df, df])
    
    return record_df
    
#%%
##################################################
################ REPORT GENERATION ###############
##################################################

with PdfPages("reports/round_3_results.pdf") as pdf:
    round_3_generator(round_3_scores_dict, win_loses, pdf)

bottom_16 = {"Diddy Kong": 80,
             "Snake": 79,
             "Lucina": 78,
             "Ryu": 77,
             "Pichu": 76,
             "Daisy": 75,
             "Terry": 74,
             "Olimar": 73,
             "Zero Suit Samus": 72,
             "Shulk": 71,
             "Richter": 70,
             "Villager": 69,
             "Greninja": 68,
             "Byleth": 67,
             "Fox": 66,
             "Marth": 65}
             
eliminated_16 = {character for character in bottom_16}
            
copy_loss_dict = loss_dict.copy()

def round_3_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_3_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 3: Rank 49 to 80 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_3_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 3: Rank 49 to 80 Score Distribution", pdf)   
            
round_3_score_distribution_evolution(Tourney_List_3, renormalized_scores, copy_loss_dict)

#%%
#######################################################
####################### ROUND 4 #######################
#######################################################

"""

Recalculated Scores; Divided into Quintiles of 16 Characters each from 80th to 1st

median = round(statistics.median(list(quintile.values())), 4)
minimum, maximum = min(list(quintile.values())), max(list(quintile.values()))
score_range = maximum - minimum
intermediate_score = minimum + score_range/(1 + np.exp(-(5.0/score_range)*(score - median)))
new_score = S^(1/2)*log(S)

--> Essentially a Quintile Based Sigmoid then N^(1/2)LOG(N)

Round 4 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 175%
Score is Multiplied by (1 + (match_number - 1)*0.33)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 175%
Score is Multiplied by (1 + (match_number - 1)*0.33)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_4_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n*0.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1 + n*0.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n*0.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_4_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 4: Rank 1 to 48 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 4: Rank 1 to 48 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 4: Rank 1 to 48 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 4: Rank 1 to 48 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 4: Rank 1 to 48 Score Density Plot", pdf)
    
###########################
###### Matches 48-1 #######
###########################

round_4_scores_dict = renormalized_round_2_scores.copy()
for character in eliminated_16: del round_4_scores_dict[character]
round_4_scores_dict = dict(sorted(renormalized_round_2_scores.items(), key=lambda x: x[1])[38:])
# print_sorted_dict(round_4_scores_dict)

# for rank changes visual
inital_round_4_scores = round_4_scores_dict.copy()

# Bottom 16 of (1st to 48th) the Top 48 will be Face (49th to 64th) the Bottom 64 for Bottom 16 Spots in Top 48
# Character List:
#
# 48 8.364 Jigglypuff
# 47 8.445 PacMan
# 46 8.466 Dark Samus
# 45 8.507 Mewtwo
# 44 8.629 Luigi
# 43 8.713 Steve
# 42 8.753 Pokemon Trainer
# 41 8.801 Donkey Kong
# 40 8.809 Little Mac
# 39 9.036 Corrin
# 38 9.128 Ness
# 37 9.194 Min Min
# 36 9.207 ROB
# 35 9.33 Wii Fit Trainer
# 34 9.331 Bowser Jr
# 33 9.344 Wario
# 32 9.533 Inkling
# 31 9.558 Sora
# 30 9.683 Lucario
# 29 9.698 Mii Swordfighter
# 28 9.883 Isabelle
# 27 9.89 Pit
# 26 9.947 Hero
# 25 10.098 Kirby
# 24 10.121 Falco
# 23 10.197 Cloud
# 22 10.242 Piranha Plant
# 21 10.354 Duck Hunt
# 20 10.447 King K Rool
# 19 10.543 Robin
# 18 10.564 Dr Mario
# 17 10.681 Young Link
# 16 10.903 Dark Pit
# 15 10.92 Zelda
# 14 10.967 Ice Climbers
# 13 10.983 Wolf
# 12 10.995 Sonic
# 11 11.032 Ganondorf
# 10 11.042 Captain Falcon
# 9 11.249 Banjo & Kazooie
# 8 11.525 Link
# 7 11.532 Lucas
# 6 11.66 Sephiroth
# 5 11.766 Ridley
# 4 11.84 Incineroar
# 3 11.87 Ike
# 2 11.892 Bowser
# 1 11.91 Chrom

Tourney_1 = {
    "PacMan": [["Little Mac", [2, 69]], ["Piranha Plant", [1, 79]], ["Toon Link", [1, 22]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dark Samus": [["Kazuya", [3, 180]], ["Wolf", [1, 10]], ["Lucas", [2, 112]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Mewtwo": [["Samus", [2, 114]], ["Falco", [2, 46]], ["Bowser Jr", [1, 100]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Jigglypuff": [["Sora", [1, 83]], ["Rosalina & Luma", [1, 107]], ["Bowser", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Luigi": [["Falco", [2, 7]], ["Hero", [2, 50]], ["Jigglypuff", [2, 98]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Donkey Kong": [["Link", [1, 0]], ["Simon", [1, 56]], ["Pikachu", [2, 15]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Steve": [["Byleth", [-3, 126]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Pokemon Trainer": [["Young Link", [2, 69]], ["Samus", [1, 123]], ["Dr Mario", [2, 97]], ["Corrin", [2, 83]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Corrin": [["Mewtwo", [-1, 23]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Min Min": [["Robin", [1, 47]], ["Yoshi", [2, 62]], ["Bowser", [2, 101]], ["Olimar", [3, 109]], ["Opponent 5", [0, 0]]], 
    "Little Mac": [["Shulk", [2, 155]], ["Pichu", [1, 8]], ["Corrin", [2, 126]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Ness": [["Ganondorf", [1, 0]], ["Chrom", [1, 129]], ["Luigi", [3, 156]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Bowser Jr": [["Peach", [2, 117]], ["Pyra & Mythra", [3, 146]], ["King Dedede", [1, 141]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Wii Fit Trainer": [["Dark Pit", [1, 7]], ["Richter", [2, 17]], ["Simon", [2, 137]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "ROB": [["Dr Mario", [1, 12]], ["Kazuya", [1, 0]], ["Pichu", [2, 110]], ["Toon Link", [2, 80]], ["Opponent 5", [0, 0]]],          
    "Wario": [["Ice Climbers", [-1, 78]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "Lucario": [["Ganondorf", [2, 40]], ["Dark Samus", [2, 136]], ["Greninja", [1, 45]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sora": [["Link", [2, 13]], ["Yoshi", [1, 13]], ["Duck Hunt", [1, 34]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Mii Swordfighter": [["Mega Man", [1, 91]], ["Ness", [1, 0]], ["Bowser Jr", [1, 59]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Inkling": [["Lucas", [2, 43]], ["Kirby", [1, 72]], ["Young Link", [3, 155]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Hero": [["Dr Mario", [1, 60]], ["Pichu", [2, 75]], ["Yoshi", [2, 80]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pit": [["Greninja", [2, 98]], ["Joker", [2, 60]], ["Ridley", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Kirby": [["Meta Knight", [1, 15]], ["Cloud", [2, 16]], ["Peach", [2, 60]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Isabelle": [["Olimar", [2, 3]], ["Ice Climbers", [2, 17]], ["Duck Hunt", [2, 130]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Duck Hunt": [["PacMan", [2, 27]], ["Greninja", [2, 39]], ["Marth", [2, 28]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Falco": [["Lucina", [1, 32]], ["Incineroar", [3, 144]], ["Bayonetta", [2, 108]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Chrom", [2, 8]], ["King K Rool", [-2, 145]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Cloud": [["Kirby", [1, 0]], ["Wii Fit Trainer", [2, 81]], ["Terry", [2, 53]], ["King K Rool", [1, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "King K Rool": [["Diddy Kong", [1, 45]], ["Greninja", [1, 0]], ["Mr Game & Watch", [2, 33]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dr Mario": [["Shulk", [3, 109]], ["Link", [2, 162]], ["Wolf", [2, 92]], ["Opponent 4", [0, 0]], ["Ike", [2, 108]]], 
    "Robin": [["Byleth", [-1, 5]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Young Link": [["Dr Mario", [-1, 27]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_9 = {
    "Wolf": [["ROB", [-1, 108]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dark Pit": [["Pikachu", [1, 44]], ["Incineroar", [-2, 90]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Zelda": [["Cloud", [2, 87]], ["Duck Hunt", [2, 52]], ["Richter", [3, 126]], ["Opponent 4", [0, 0]], ["Palutena", [3, 159]]],          
    "Ice Climbers": [["Diddy Kong", [2, 81]], ["Greninja", [3, 88]], ["Mario", [2, 20]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_10 = {
    "Ganondorf": [["Donkey Kong", [2, 88]], ["Toon Link", [2, 115]], ["Dark Samus", [2, 27]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sonic": [["Samus", [1, 0]], ["Lucario", [1, 33]], ["Hero", [1, 101]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Captain Falcon": [["Ice Climbers", [2, 13]], ["Snake", [2, 29]], ["Piranha Plant", [1, 137]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Banjo & Kazooie": [["Marth", [2, 116]], ["Wario", [1, 93]], ["Richter", [1, 12]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_11 = {
    "Sephiroth": [["Mewtwo", [2, 5]], ["Isabelle", [2, 33]], ["Min Min", [1, 51]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ridley": [["Wolf", [1, 0]], ["Sora", [2, 0]], ["Mr Game & Watch", [2, 75]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Lucas": [["Joker", [1, 33]], ["Ryu", [2, 0]], ["Roy", [2, 80]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Link": [["Duck Hunt", [3, 104]], ["Marth", [3, 155]], ["Wario", [2, 90]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_12 = {
    "Incineroar": [["Min Min", [2, 25]], ["Bayonetta", [1, 0]], ["Pyra & Mythra", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Bowser": [["Ganondorf", [1, 41]], ["Olimar", [2, 125]], ["Richter", [1, 131]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ike": [["Pokemon Trainer", [2, 32]], ["Greninja", [3, 131]], ["Villager", [2, 107]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Chrom": [["Robin", [2, 118]], ["Link", [2, 0]], ["Mewtwo", [3, 125]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_4 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, 
                  Tourney_7, Tourney_8, Tourney_9, Tourney_10, Tourney_11, Tourney_12]

max_percentage = 175
round_4_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_3_calculator(Tourney_List_4, max_percentage, round_4_scores_dict, loss_dict)
round_4_scores_dict = dict(sorted(round_4_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_4_scores_dict)
round_4_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()
# print_sorted_dict(round_4_loss_dict)

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

with PdfPages("reports/round_4_results.pdf") as pdf:
    round_4_generator(character_dict, win_loses, pdf)

bottom_16 = {"Diddy Kong": 80,
             "Snake": 79,
             "Lucina": 78,
             "Ryu": 77,
             "Pichu": 76,
             "Daisy": 75,
             "Terry": 74,
             "Olimar": 73,
             "Zero Suit Samus": 72,
             "Shulk": 71,
             "Richter": 70,
             "Villager": 69,
             "Greninja": 68,
             "Byleth": 67,
             "Fox": 66,
             "Marth": 65}
             
eliminated_16 = {character for character in bottom_16}
            
copy_loss_dict = loss_dict.copy()

def round_4_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_4_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 4: Rank 1 to 48 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_4_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 4: Rank 1 to 48 Score Distribution", pdf)   
            
round_4_scores = round_4_scores_dict.copy()
round_4_score_distribution_evolution(Tourney_List_4, round_4_scores, copy_loss_dict)

#%%
##################################################
################### ANALYSIS #####################
##################################################

def ranking_changes(characters, initial_ranks, final_ranks):
    # Example data: old vs new ranks
    old_ranks = [rank for character, rank in initial_ranks.items()]
    new_ranks = [final_ranks[character] for character in initial_ranks]
    
    def ordinal(n: int) -> str:
        # Handle special cases for 11th, 12th, 13th
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    fig, ax = plt.subplots(figsize=(15,15))

    for i, char in enumerate(characters):
        # Left side: old rank + name
        ax.text(0, old_ranks[i], f"{ordinal(len(characters)-old_ranks[i]+1)} {char}",
                ha='right', va='center', fontsize=8)
        
        # Right side: new rank + name
        ax.text(1, new_ranks[i], f"{ordinal(len(characters)-new_ranks[i]+1)} {char}",
                ha='left', va='center', fontsize=8)
        
        # Arrow showing movement
        ax.annotate("",
                    xy=(1, new_ranks[i]), xycoords='data',
                    xytext=(0, old_ranks[i]), textcoords='data',
                    arrowprops=dict(arrowstyle="->", lw=2))

    # Format axes
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0.5, len(characters)+0.5)
    ax.axis("off")
    ax.set_title("Rank Changes", fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close()                 


def _ranks_best_from_scores(scores_dict):
    """Return ranks where 1 is best (highest score).

    Works regardless of input dict ordering.
    """
    ordered = sorted(scores_dict.items(), key=lambda item: item[1])  # worst -> best
    n = len(ordered)
    return {character: n - i for i, (character, _score) in enumerate(ordered)}


def ranking_changes_colored(pdf, characters, initial_ranks, final_ranks, advance_cutoff=None, eliminated_characters=None, title="Rank Changes"):
    """Arrow plot of rank changes with color categories.

    - advance_cutoff: top-K (ranks 1..K) considered advanced.
    - eliminated_characters: set of characters considered eliminated (colored red).
    - "advanced after being behind" is computed as: initial_rank > advance_cutoff and final_rank <= advance_cutoff.

    pdf: PdfPages handle to write the figure into.
    """

    def ordinal(n: int) -> str:
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    eliminated_characters = set(eliminated_characters or [])
    if advance_cutoff is None and eliminated_characters:
        advance_cutoff = max(0, len(characters) - len(eliminated_characters))

    old_ranks = [initial_ranks[character] for character in characters]
    new_ranks = [final_ranks[character] for character in characters]

    fig_height = max(15, 0.25 * len(characters))
    fig, ax = plt.subplots(figsize=(15, fig_height))

    for i, character in enumerate(characters):
        old_rank = old_ranks[i]
        new_rank = new_ranks[i]

        is_eliminated = character in eliminated_characters
        is_advanced = (advance_cutoff is not None) and (new_rank <= advance_cutoff)
        was_behind = (advance_cutoff is not None) and (old_rank > advance_cutoff)
        comeback = bool(is_advanced and was_behind)

        if is_eliminated:
            color = "red"
        elif comeback:
            color = "green"
        elif is_advanced:
            color = "purple"
        elif (advance_cutoff is not None) and (old_rank <= advance_cutoff) and (new_rank > advance_cutoff):
            color = "orange"
        else:
            color = "gray"

        ax.text(0, old_rank, f"{ordinal(old_rank)} {character}", ha="right", va="center", fontsize=8)
        ax.text(1, new_rank, f"{ordinal(new_rank)} {character}", ha="left", va="center", fontsize=8)
        ax.annotate(
            "",
            xy=(1, new_rank),
            xycoords="data",
            xytext=(0, old_rank),
            textcoords="data",
            arrowprops=dict(arrowstyle="->", lw=2, color=color),
        )

    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0.5, len(characters) + 0.5)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(title, fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close()


def generate_round_ranking_changes_pdf(round_number, initial_scores, final_scores, advance_cutoff=None, eliminated_characters=None, title=None):
    """Create a per-round ranking-change PDF in reports/ranking_changes.

    initial_scores/final_scores are score dicts (not ranks). Ranks are computed with 1=best.
    """
    common_characters = [c for c in initial_scores.keys() if c in final_scores]
    if not common_characters:
        return

    initial_subset = {c: initial_scores[c] for c in common_characters}
    final_subset = {c: final_scores[c] for c in common_characters}

    initial_ranks = _ranks_best_from_scores(initial_subset)
    final_ranks = _ranks_best_from_scores(final_subset)

    filename = os.path.join(filepath, "reports", "ranking_changes", f"round_{round_number}_ranking_changes.pdf")
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with PdfPages(filename) as pdf:
        ranking_changes_colored(
            pdf,
            common_characters,
            initial_ranks,
            final_ranks,
            advance_cutoff=advance_cutoff,
            eliminated_characters=eliminated_characters,
            title=title or f"Round {round_number} Rank Changes",
        )

round_2_scores_dict = dict(sorted(round_2_scores_dict.items(), key=lambda item: item[1], reverse=False))
characters = [character for character in round_2_scores_dict]
initial_ranks = {character: rank + 1 for rank, character in enumerate(round_2_scores_dict)}
bottom_6 = {character: score for character, score in round_2_scores_dict.items() if score < 4.00}
all_round_scores_dict = bottom_6 | round_3_scores_dict | round_4_scores_dict
all_round_scores_dict = dict(sorted(all_round_scores_dict.items(), key=lambda item: item[1], reverse=False))
final_ranks = {character: rank + 1 for rank, character in enumerate(all_round_scores_dict)}

filename = os.path.join(filepath, "0th_Round_Elimination.pdf")
with PdfPages(filename) as pdf:
    ranking_changes(characters, initial_ranks, final_ranks)
    
#%%
######################################################
######################## ROUND 5 #####################
######################################################

round_3_and_4_scores_dict = round_3_scores_dict | round_4_scores_dict
round_3_and_4_scores_dict = dict(sorted(round_3_and_4_scores_dict.items(), key=lambda item: item[1], reverse=False))

def round_4_renormalizer(round_3_and_4_scores_dict):
    
    round_5_scores_dict = {}
    for character in round_3_and_4_scores_dict:
        if round_3_and_4_scores_dict[character] >= round_3_and_4_scores_dict["Robin"]:
            round_5_scores_dict[character] = round(((round_3_and_4_scores_dict[character])**(6/11))*np.log(round_3_and_4_scores_dict[character]), 3)
        
    return round_5_scores_dict

round_5_character_dict = round_4_renormalizer(round_3_and_4_scores_dict)
round_5_scores_dict = {character:score for character,score in round_5_character_dict.items() if score <= round_5_character_dict["Pyra & Mythra"]}
round_6_scores_dict = {character:score for character,score in round_5_character_dict.items() if score > round_5_character_dict["Pyra & Mythra"]}

# for rank changes visual
inital_round_5_scores = round_5_scores_dict.copy()

"""

Recalculated Scores; Divided into Quintiles of 16 Characters each from 80th to 1st

median = round(statistics.median(list(quintile.values())), 4)
minimum, maximum = min(list(quintile.values())), max(list(quintile.values()))
score_range = maximum - minimum
intermediate_score = minimum + score_range/(1 + np.exp(-(5.0/score_range)*(score - median)))
new_score = S^(6/11)*log(S)

--> Essentially a Quintile Based Sigmoid then N^(1/2)LOG(N)

Round 4 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number - 1)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 175%
Score is Multiplied by (1 + (match_number - 1)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_5_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                # print(key, fight[1][0], fights)
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_5_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 5: Rank 23 to 64 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 5: Rank 23 to 64 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 5: Rank 23 to 64 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 5: Rank 23 to 64 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 5: Rank 23 to 64 Score Density Plot", pdf)
    
###########################
###### Matches 64-23 #######
###########################

# 64 8.53 Robin
# 63 8.73 Young Link
# 62 9.35 Wolf
# 61 9.63 Dark Pit
# 60 10.25 Piranha Plant
# 59 10.57 Byleth
# 58 10.73 Fox
# 57 10.74 Marth
# 56 10.95 Palutena
# 55 11.0 Mii Gunner
# 54 11.57 Jigglypuff
# 53 11.77 Mr Game & Watch
# 52 12.07 Mii Brawler
# 51 12.22 Yoshi
# 50 12.28 Pikachu
# 49 12.34 Rosalina & Luma
# 48 12.4 Toon Link
# 47 12.42 Sheik
# 46 12.56 PacMan
# 45 13.04 Peach
# 44 13.29 Mii Swordfighter
# 43 13.36 Mewtwo
# 42 13.39 Meta Knight
# 41 13.68 Little Mac
# 40 13.72 Sonic
# 39 13.8 Sora
# 38 13.81 Mario
# 37 13.82 Dark Samus
# 36 13.83 Ness
# 35 13.99 Donkey Kong
# 34 14.02 Bowser Jr
# 33 14.21 Pokemon Trainer
# 32 14.25 Roy
# 31 14.28 King Dedede
# 30 14.35 ROB
# 29 14.37 Samus
# 28 14.38 Lucario
# 27 14.48 Bowser
# 26 14.56 Wii Fit Trainer
# 25 14.56 Banjo & Kazooie
# 24 14.68 Luigi
# 23 14.72 Pyra & Mythra

Tourney_1 = {
    "Wolf": [["Shulk", [2, 144]], ["King Dedede", [-1, 121]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Robin": [["Zelda", [1, 0]], ["Marth", [-2, 90]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dark Pit": [["Simon", [3, 86]], ["Sephiroth", [2, 79]], ["Chrom", [2, 75]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Young Link": [["Isabelle", [2, 85]], ["Little Mac", [3, 150]], ["Dr Mario", [2, 20]], ["Opponent 4", [0, 0]], ["Marth", [1, 31]]] 
    }

Tourney_2 = {
    "Marth": [["Mewtwo", [1, 9]], ["Steve", [-1, 28]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Mr Game & Watch", [3, 178]], ["King K Rool", [1, 23]], ["Sora", [2, 29]], ["Duck Hunt", [2, 29]], ["Opponent 5", [0, 0]]], 
    "Byleth": [["Greninja", [2, 122]], ["Zelda", [1, 57]], ["Inkling", [2, 117]], ["Yoshi", [1, 11]], ["Opponent 5", [0, 0]]],          
    "Fox": [["Dark Samus", [-1, 18]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Mii Gunner": [["Steve", [2, 110]], ["Piranha Plant", [2, 0]], ["Bowser Jr", [2, 67]], ["Richter", [2, 27]], ["Opponent 5", [0, 0]]], 
    "Palutena": [["Hero", [-1, 39]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Jigglypuff": [["Banjo & Kazooie", [-1, 19]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mr Game & Watch": [["Pokemon Trainer", [1, 51]], ["Corrin", [1, 23]], ["Falco", [1, 124]], ["Wolf", [1, 123]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Rosalina & Luma": [["Sonic", [2, 80]], ["Ike", [2, 34]], ["Robin", [1, 131]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pikachu": [["Snake", [1, 112]], ["Pyra & Mythra", [2, 11]], ["Bowser", [1, 0]], ["Opponent 4", [0, 0]], ["Piranha Plant", [1, 83]]], 
    "Mii Brawler": [["Bowser Jr", [-1, 74]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Yoshi": [["King Dedede", [1, 64]], ["Villager", [2, 112]], ["Donkey Kong", [2, 60]], ["Piranha Plant", [-2, 74]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "Toon Link": [["Fox", [2, 122]], ["Duck Hunt", [2, 56]], ["Wii Fit Trainer", [2, 32]], ["Mewtwo", [1, 55]], ["Roy", [1, 39]]], 
    "PacMan": [["Wario", [1, 0]], ["Ness", [-1, 38]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Peach": [["Toon Link", [-1, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Sheik": [["Ice Climbers", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Mii Swordfighter": [["Sora", [-1, 56]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Little Mac": [["Daisy", [1, 133]], ["Palutena", [1, 15]], ["Pokemon Trainer", [1, 51]], ["Duck Hunt", [2, 20]], ["Opponent 5", [0, 0]]], 
    "Mewtwo": [["Link", [2, 129]], ["Hero", [2, 67]], ["Sonic", [2, 143]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Meta Knight": [["Mario", [1, 5]], ["Pikachu", [2, 80]], ["Byleth", [2, 76]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Dark Samus": [["Dr Mario", [-1, 59]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sora": [["Chrom", [1, 31]], ["Pichu", [1, 60]], ["Ryu", [2, 65]], ["Incineroar", [2, 103]], ["Opponent 5", [0, 0]]], 
    "Mario": [["Sephiroth", [-2, 95]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Sonic": [["King K Rool", [2, 90]], ["Dark Pit", [2, 80]], ["Mario", [3, 146]], ["Young Link", [1, 44]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "Donkey Kong": [["Ice Climbers", [2, 97]], ["Wario", [1, 107]], ["Simon", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pokemon Trainer": [["Zero Suit Samus", [3, 100]], ["Bayonetta", [2, 30]], ["Young Link", [2, 112]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Bowser Jr": [["Lucina", [1, 0]], ["Terry", [2, 169]], ["Greninja", [3, 139]], ["Yoshi", [2, 105]], ["Opponent 5", [0, 0]]],          
    "Ness": [["Yoshi", [-2, 90]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_9 = {
    "King Dedede": [["Donkey Kong", [1, 107]], ["Steve", [1, 0]], ["Byleth", [2, 55]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Samus": [["Jigglypuff", [1, 60]], ["Richter", [2, 65]], ["Sephiroth", [2, 144]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "ROB": [["PacMan", [2, 138]], ["Corrin", [2, 160]], ["Dark Samus", [2, 150]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Roy": [["Pokemon Trainer", [1, 55]], ["Mario", [2, 138]], ["Bowser", [2, 72]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_10 = {
    "Bowser": [["Pikachu", [2, 32]], ["Cloud", [2, 87]], ["Jigglypuff", [2, 78]], ["Mr Game & Watch", [3, 175]], ["Sheik", [2, 61]]], 
    "Lucario": [["Peach", [-1, 28]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Wii Fit Trainer": [["Banjo & Kazooie", [1, 138]], ["Roy", [-1, 83]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Banjo & Kazooie": [["Olimar", [1, 2]], ["Ridley", [-1, 116]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_11 = {
    "Pyra & Mythra": [["Diddy Kong", [3, 189]], ["Sonic", [2, 80]], ["Peach", [2, 35]], ["Pit", [3, 110]], ["Opponent 5", [0, 0]]], 
    "Luigi": [["Fox", [2, 16]], ["Dark Pit", [1, 47]], ["Joker", [1, 13]], ["Pichu", [2, 0]], ["Opponent 5", [0, 0]]]}

Tourney_List_5 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, 
                  Tourney_7, Tourney_8, Tourney_9, Tourney_10, Tourney_11]

max_percentage = 150
round_5_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_5_calculator(Tourney_List_5, max_percentage, round_5_scores_dict, loss_dict)
round_5_scores_dict = dict(sorted(round_5_scores_dict.items(), key=lambda item: item[1], reverse=False))
initial_round_5_scores = round_5_scores_dict.copy()
# print_sorted_dict(round_5_scores_dict)
round_5_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################### ANALYSIS #####################
##################################################

def ranking_changes_2nd_elimination(characters, initial_ranks, final_ranks):
    
    # Previous and CUrrent Ranks
    old_ranks = [rank for character, rank in initial_ranks.items()]
    new_ranks = [final_ranks[character] for character in initial_ranks]
    
    def ordinal(n: int) -> str:
        # Handle special cases for 11th, 12th, 13th
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    colors = []
    fig, ax = plt.subplots(figsize=(15,15))

    for i, char in enumerate(characters):
        # Left side: old rank + name
        ax.text(0, old_ranks[i], f"{ordinal(old_ranks[i])} {char}",
                ha='right', va='center', fontsize=8)
        
        # Right side: new rank + name
        ax.text(1, new_ranks[i], f"{ordinal(new_ranks[i])} {char}",
                ha='left', va='center', fontsize=8)
        
        # Top 32 End Placements
        if old_ranks[i] < 33 and new_ranks[i] < 33:
            color = "purple"   # stayed top 10
        if 65 > old_ranks[i] > 48 and new_ranks[i] < 33:
            color = "green"     # massive improvement
        if 49 > old_ranks[i] > 32 and new_ranks[i] < 33:
            color = "pink"     # jumped into top 10
        
        # Top 48 End Placements
        if old_ranks[i] < 33 and (49 > new_ranks[i] > 32):
            color = "orange"     # dropped from 32nd to 23rd to bottom 48
        if (49 > old_ranks[i] > 32) and (49 > new_ranks[i] > 32):
            color = "gray"     # staying consistent, no improvement
        if old_ranks[i] > 48 and (49 > new_ranks[i] > 32):
            color = "yellow"     # improved but still struggling 

        # Top 64 End Placements
        if old_ranks[i] < 33 and new_ranks[i] > 48:
            color = "brown"    # worst case scenario
        if (49 > old_ranks[i] > 32) and (65 > new_ranks[i] > 48):
            color = "red"    # slipped to bottom elimination spot
        if (65 > old_ranks[i] > 48) and (65 > new_ranks[i] > 48):
            color = "black"    # stayed in eliminat

        colors.append(color)

        # Arrow showing movement
        ax.annotate("",
                    xy=(1, new_ranks[i]), xycoords='data',
                    xytext=(0, old_ranks[i]), textcoords='data',
                    arrowprops=dict(arrowstyle="->", lw=2, color=color))

    # Format axes
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(22.5, len(characters)+22.5)
    
    # Flip so rank 1 is at the top
    ax.invert_yaxis()
    
    ax.axis("off")
    ax.set_title("Rank Changes", fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close()                 

# Round 5 Ranking Regions
rank_86_to_81 = {character: score for character, score in round_2_scores_dict.items() if score < 4.00}
rank_80_to_65 = {character: score for character, score in round_3_scores_dict.items() if score < 13.50}
rank_64_to_49 = {character: score for character, score in round_5_scores_dict.items() if score < 17.00}
rank_48_to_23 = {character: score for character, score in round_5_scores_dict.items() if score > 17.00}

# Round 5 Ranking Changes Chart
initial_ranks = {character: len(inital_round_5_scores) + 22 - rank for rank, character in enumerate(inital_round_5_scores)}
final_ranks = {character: len(round_5_scores_dict) + 22 - rank for rank, character in enumerate(round_5_scores_dict)}
characters = [character for character in inital_round_5_scores]

filename = os.path.join(filepath, "reports", "ranking_changes", "2nd_elimination.pdf")

with PdfPages(filename) as pdf:
    ranking_changes_2nd_elimination(characters, initial_ranks, final_ranks)

################################################################
################### Round 3 Ranking Changes ####################
################################################################

def ranking_changes_1st_elimination(characters, initial_ranks, final_ranks):
    
    # Previous and CUrrent Ranks
    old_ranks = [rank for character, rank in initial_ranks.items()]
    new_ranks = [final_ranks[character] for character in initial_ranks]
    
    def ordinal(n: int) -> str:
        # Handle special cases for 11th, 12th, 13th
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    colors = []
    fig, ax = plt.subplots(figsize=(15,15))

    for i, char in enumerate(characters):
        # Left side: old rank + name
        ax.text(0, old_ranks[i], f"{ordinal(old_ranks[i])} {char}",
                ha='right', va='center', fontsize=8)
        
        # Right side: new rank + name
        ax.text(1, new_ranks[i], f"{ordinal(new_ranks[i])} {char}",
                ha='left', va='center', fontsize=8)
        
        # Top 32 End Placements
        if (64 >= old_ranks[i] >= 49) and (64 >= new_ranks[i] >= 49):
            color = "purple"    # maintained safety
        if (80 >= old_ranks[i] >= 65) and (64 >= new_ranks[i] >= 49):
            color = "green"    # upgraded to safety
        if (64 >= old_ranks[i] >= 49) and (80 >= new_ranks[i] >= 65):
            color = "red"      # dowgraded to elimination
        if (80 >= old_ranks[i] >= 65) and (80 >= new_ranks[i] >= 65):
            color = "black"    # stayed in elimination

        # Arrow showing movement
        ax.annotate("",
                    xy=(1, new_ranks[i]), xycoords='data',
                    xytext=(0, old_ranks[i]), textcoords='data',
                    arrowprops=dict(arrowstyle="->", lw=2, color=color))

    # Format axes
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(49.5, len(characters)+80.5)
    
    # Flip so rank 1 is at the top
    ax.invert_yaxis()
    
    ax.axis("off")
    ax.set_title("Rank Changes", fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close()      
    
# Round 3 Ranking Changes Chart

initial_ranks = {character: len(inital_round_3_scores) + 48 - rank for rank, character in enumerate(inital_round_3_scores)}
final_ranks = {character: len(round_3_scores_dict) + 48 - rank for rank, character in enumerate(round_3_scores_dict)}
characters = [character for character in inital_round_3_scores]

filename = os.path.join(filepath, "reports", "ranking_changes", "1st_elimination.pdf")

with PdfPages(filename) as pdf:
    ranking_changes_1st_elimination(characters, initial_ranks, final_ranks)

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

with PdfPages("reports/round_5_results.pdf") as pdf:
    round_5_generator(round_5_scores_dict, win_loses, pdf)

bottom_16 = {"Robin": 64,
             "Fox": 63,
             "Palutena": 62,
             "Jigglypuff": 61,
             "Wolf": 60,
             "Mii Brawler": 59,
             "Peach": 58,
             "Marth": 57,
             "Sheik": 56,
             "Ness": 55,
             "Mario": 54,
             "Mii Swordfighter": 53,
             "Dark Samus": 52,
             "Lucario": 51,
             "PacMan": 50,
             "Pit": 49}
             
eliminated_49_to_64 = {character for character in bottom_16}
            
copy_loss_dict = loss_dict.copy()

def round_5_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_5_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 5: Rank 23 to 64 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_5_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_2_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 5: Rank 23 to 64 Score Distribution", pdf)   
            
round_5_scores = round_5_scores_dict.copy()
round_5_score_distribution_evolution(Tourney_List_5, round_5_scores, copy_loss_dict)

#%%
######################################################
######################## ROUND 6 #####################
######################################################

# for rank changes visual
inital_round_6_scores = round_6_scores_dict.copy()

"""

Round 6 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 175%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_6_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                # print(key, fight[1][0], fights)
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_6_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 6: Rank 1 to 22 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 6: Rank 1 to 22 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 6: Rank 1 to 22 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 6: Rank 1 to 22 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 6: Rank 1 to 22 Score Density Plot", pdf)
    
###########################
###### Matches 22-1 #######
###########################

# 22 14.775 Inkling
# 21 14.979 Hero
# 20 15.034 Pit
# 19 15.412 Captain Falcon
# 18 15.426 Falco
# 17 15.486 Min Min
# 16 15.641 King K Rool
# 15 15.688 Cloud
# 14 15.802 Kirby
# 13 15.809 Sephiroth
# 12 15.989 Isabelle
# 11 16.375 Ganondorf
# 10 16.454 Duck Hunt
# 9 16.738 Lucas
# 8 16.876 Dr Mario
# 7 17.014 Incineroar
# 6 17.295 Ice Climbers
# 5 17.38 Ridley
# 4 17.646 Ike
# 3 17.866 Link
# 2 17.95 Chrom
# 1 18.592 Zelda


Tourney_1 = {
        "Captain Falcon": [["Bayonetta", [2, 0]], ["Marth", [1, 0]], ["Terry", [-1, 60]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Hero": [["Wario", [3, 81]], ["Byleth", [1, 94]], ["Yoshi", [1, 57]], ["Terry", [-1, 109]], ["Opponent 5", [0, 0]]], 
        "Inkling": [["Simon", [-2, 158]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Pit": [["Olimar", [-1, 50]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_2 = {
        "Min Min": [["Steve", [2, 34]], ["Young Link", [2, 100]], ["Duck Hunt", [2, 29]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Cloud": [["Snake", [1, 0]], ["Joker", [2, 0]], ["lucas", [3, 122]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "King K Rool": [["Ness", [2, 0]], ["Diddy Kong", [3, 121]], ["Mr Game & Watch", [2, 85]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Falco": [["Bowser Jr", [1, 82]], ["Ice Climbers", [3, 169]], ["Zelda", [1, 13]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_3 = {
        "Ganondorf": [["Dark Samus", [-1, 50]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Kirby": [["Duck Hunt", [2, 102]], ["Pit", [2, 0]], ["Greninja", [3, 88]], ["Inkling", [1, 133]], ["Opponent 5", [0, 0]]], 
        "Isabelle": [["Incineroar", [1, 90]], ["Villager", [2, 8]], ["Mario", [2, 160]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Sephiroth": [["Richter", [1, 0]], ["Chrom", [2, 63]], ["Sonic", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_4 = {
        "Duck Hunt": [["Greninja", [1, 59]], ["Pit", [-1, 48]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Incineroar": [["Chrom", [2, 7]], ["Captain Falcon", [-1, 72]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Lucas": [["Diddy Kong", [2, 69]], ["Kazuya", [-2, 16]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Dr Mario": [["Donkey Kong", [3, 121]], ["Pyra & Mythra", [1, 40]], ["PacMan", [3, 164]], ["Marth", [2, 0]], ["Captain Falcon", [-1, 64]]] 
        }

Tourney_5 = {
        "Ridley": [["Corrin", [3, 187]], ["ROB", [3, 186]], ["Zero Suit Samus", [2, 10]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Ike": [["Ryu", [2, 128]], ["Diddy Kong", [2, 60]], ["Little Mac", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Ice Climbers": [["Ken", [2, 56]], ["Simon", [1, 42]], ["Mario", [2, 60]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Link": [["Banjo & Kazooie", [1, 76]], ["Shulk", [2, 52]], ["Jigglypuff", [3, 125]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_6 = {
        "Chrom": [["Ness", [3, 123]], ["Donkey Kong", [2, 62]], ["Cloud", [2, 0]], ["Wolf", [1, 17]], ["Opponent 5", [0, 0]]], 
        "Zelda": [["Bayonetta", [2, 0]], ["Little Mac", [2, 48]], ["Ike", [2, 71]], ["Wii Fit Trainer", [2, 117]], ["Opponent 5", [0, 0]]], 
        }

Tourney_List_6 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6]

max_percentage = 150
round_6_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_6_calculator(Tourney_List_6, max_percentage, round_6_scores_dict, loss_dict)
round_6_scores_dict = dict(sorted(round_6_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_6_scores_dict)
round_6_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

filename = os.path.join(filepath, "reports", "round_6_results.pdf")

with PdfPages(filename) as pdf:
    round_6_generator(round_6_scores_dict, win_loses, pdf)
            
copy_loss_dict = loss_dict.copy()

def round_6_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_6_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_6_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 6: Rank 1 to 22 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_6_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_6_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 6: Rank 1 to 22 Score Distribution", pdf)   
            
round_6_scores = round_6_scores_dict.copy()
round_6_score_distribution_evolution(Tourney_List_6, round_6_scores, copy_loss_dict)
#%%
##################################################
################### ANALYSIS #####################
##################################################

def ranking_changes_3rd_remerger(characters, initial_ranks, final_ranks):
    
    # Previous and CUrrent Ranks
    old_ranks = [rank for character, rank in initial_ranks.items()]
    new_ranks = [final_ranks[character] for character in initial_ranks]
    
    def ordinal(n: int) -> str:
        # Handle special cases for 11th, 12th, 13th
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    colors = []
    fig, ax = plt.subplots(figsize=(15,15))

    for i, char in enumerate(characters):
        # Left side: old rank + name
        ax.text(0, old_ranks[i], f"{ordinal(old_ranks[i])} {char}",
                ha='right', va='center', fontsize=8)
        
        # Right side: new rank + name
        ax.text(1, new_ranks[i], f"{ordinal(new_ranks[i])} {char}",
                ha='left', va='center', fontsize=8)
            
        # Top 32 End Placements
        if old_ranks[i] < 16 and new_ranks[i] < 16:
            color = "purple"   # stayed top 10
        if 65 > old_ranks[i] > 32 and new_ranks[i] < 16:
            color = "pink"     # massive improvement
        if 33 > old_ranks[i] > 16 and new_ranks[i] < 16:
            color = "green"     # jumped into top 16
        
        # Top 48 End Placements
        if old_ranks[i] < 17 and (49 > new_ranks[i] > 16):
            color = "orange"     # dropped from Top 32 to Top 48
        if (49 > old_ranks[i] > 32) and (49 > new_ranks[i] > 16):
            color = "gray"     # staying consistent, no improvement
        if old_ranks[i] > 48 and (49 > new_ranks[i] > 16):
            color = "yellow"     # improved but still struggling 

        # Top 64 End Placements
        if old_ranks[i] < 33 and (65 > new_ranks[i] > 48):
            color = "brown"    # worst case scenario
        if (49 > old_ranks[i] > 32) and (65 > new_ranks[i] > 48):
            color = "red"    # slipped to bottom elimination spot
        if (65 > old_ranks[i] > 48) and (65 > new_ranks[i] > 48):
            color = "black"    # stayed in eliminat

        colors.append(color)

        # Arrow showing movement
        ax.annotate("",
                    xy=(1, new_ranks[i]), xycoords='data',
                    xytext=(0, old_ranks[i]), textcoords='data',
                    arrowprops=dict(arrowstyle="->", lw=2, color=color))

    # Format axes
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0.5, len(characters)+0.5)
    
    # Flip so rank 1 is at the top
    ax.invert_yaxis()
    
    ax.axis("off")
    ax.set_title("Rank Changes", fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close() 

initial_round_5_ranks = {character: len(inital_round_5_scores) + 22 - rank for rank, character in enumerate(inital_round_5_scores)}
initial_round_6_ranks = {character: len(inital_round_6_scores) - rank for rank, character in enumerate(inital_round_6_scores)}
initial_ranks = initial_round_5_ranks | initial_round_6_ranks
combined_scores = round_5_scores_dict | round_6_scores_dict
combined_scores['Inkling'] = combined_scores['Pit'] + 0.01
combined_scores = dict(sorted(combined_scores.items(), key=lambda item: item[1], reverse=False))
final_ranks = {character: len(combined_scores) - rank for rank, character in enumerate(combined_scores)}
characters = [character for character in (inital_round_5_scores | inital_round_6_scores)]

filename = os.path.join(filepath, "reports", "ranking_changes", "3rd_restructuring.pdf")

with PdfPages(filename) as pdf:
    ranking_changes_3rd_remerger(characters, initial_ranks, final_ranks)

#%%
######################################################
######################## ROUND 7 #####################
######################################################

round_5_and_6_scores_dict = round_5_scores_dict | round_6_scores_dict
round_5_and_6_scores_dict = dict(sorted(round_5_and_6_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_5_and_6_scores_dict['Inkling'] = round_5_and_6_scores_dict['Pit'] + 0.01
round_7_and_8_scores_dict = {character:score for character, score in round_5_and_6_scores_dict.items() if score > round_5_and_6_scores_dict["Pit"]}

def round_7_and_8_renormalizer(round_7_and_8_scores_dict):
    
    for character in round_7_and_8_scores_dict:
        round_7_and_8_scores_dict[character] = round(((round_7_and_8_scores_dict[character])**(5/11))*np.log(round_7_and_8_scores_dict[character]), 3)
        
    return round_7_and_8_scores_dict

round_7_and_8_characters_dict = round_7_and_8_renormalizer(round_7_and_8_scores_dict)
round_7_scores_dict = {character:score for character,score in round_7_and_8_characters_dict.items() if score <= round_7_and_8_characters_dict["Pokemon Trainer"]}
round_7_scores_dict = dict(sorted(round_7_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_8_scores_dict = {character:score for character,score in round_7_and_8_characters_dict.items() if score > round_7_and_8_characters_dict["Pokemon Trainer"]}

# for rank changes visual
inital_round_7_scores = round_7_scores_dict.copy()

"""

Refactored Scores: N^(5/11) * ln N

Round 7/8 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 200%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 200%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_7_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                # print(key, fight[1][0], fights)
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_7_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 7: Rank 17 to 48 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 7: Rank 17 to 48 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 7: Rank 17 to 48 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 7: Rank 17 to 48 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 7: Rank 17 to 48 Score Density Plot", pdf)
    
###########################
###### Matches 48-17 ######
###########################

# 48 9.461 Inkling
# 47 9.99 Wii Fit Trainer
# 46 10.118 Ganondorf
# 45 10.652 Banjo & Kazooie
# 44 10.872 Lucas
# 43 10.972 Duck Hunt
# 42 11.302 Mr Game & Watch
# 41 11.971 Incineroar
# 40 12.185 Byleth
# 39 12.347 Rosalina & Luma
# 38 12.495 Dark Pit
# 37 12.544 Young Link
# 36 12.553 Yoshi
# 35 12.691 Captain Falcon
# 34 12.82 Donkey Kong
# 33 12.965 Pikachu
# 32 13.136 Little Mac
# 31 13.167 Roy
# 30 13.206 ROB
# 29 13.432 Samus
# 28 13.466 Meta Knight
# 27 13.531 Mewtwo
# 26 13.579 King Dedede
# 25 13.613 Hero
# 24 13.652 Sora
# 23 13.66 Piranha Plant
# 22 13.772 Mii Gunner
# 21 13.857 Sephiroth
# 20 14.069 Falco
# 19 14.112 Luigi
# 18 14.431 Bowser Jr
# 17 14.431 Pokemon Trainer

                                                                                                                                                                                                                                                                                                                                                                          
Tourney_1 = {
    "Wii Fit Trainer": [["Kirby", [2, 87]], ["PacMan", [1, 123]], ["Dark Samus", [2, 108]], ["Captain Falcon", [1, 49]], ["Lucario", [-1, 124]]], 
    "Ganondorf": [["Chrom", [2, 66]], ["Yoshi", [1, 110]], ["Captain Falcon", [-1, 84]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Inkling": [["Meta Knight", [-1, 53]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Banjo & Kazooie": [["Link", [2, 33]], ["Min Min", [3, 70]], ["Wario", [1, 46]], ["Lucario", [-1, 39]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Duck Hunt": [["Mario", [1, 15]], ["Hero", [-1, 63]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Byleth": [["Ryu", [2, 0]], ["Mario", [-1, 23]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Lucas": [["Mr Game & Watch", [1, 25]], ["Ike", [2, 89]], ["Ganondorf", [1, 73]], ["Wario", [1, 117]], ["Piranha Plant", [-1, 107]]],          
    "Mr Game & Watch": [["Ken", [2, 45]], ["Incineroar", [-1, 98]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Yoshi": [["Ness", [2, 11]], ["Mario", [2, 129]], ["Peach", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dark Pit": [["Isabelle", [3, 159]], ["Palutena", [3, 124]], ["PacMan", [1, 91]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Rosalina & Luma": [["Banjo & Kazooie", [1, 0]], ["Lucas", [1, 70]], ["Captain Falcon", [2, 108]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],
    "Incineroar": [["Shulk", [-1, 40]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Donkey Kong": [["Duck Hunt", [2, 148]], ["Banjo & Kazooie", [1, 39]], ["Mewtwo", [3, 111]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pikachu": [["Pikachu", [1, 81]], ["Corrin", [1, 0]], ["Greninja", [1, 20]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Captain Falcon": [["Lucas", [-2, 148]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Young Link": [["Min Min", [2, 83]], ["Pit", [2, 0]], ["Dr Mario", [1, 0]], ["Lucas", [1, 44]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "Roy": [["Ike", [1, 63]], ["Palutena", [3, 89]], ["Richter", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "ROB": [["Diddy Kong", [2, 93]], ["Dr Mario", [1, 161]], ["Marth", [2, 71]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Samus": [["Mario", [1, 163]], ["Bayonetta", [3, 126]], ["Ridley", [1, 20]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Little Mac": [["Pikachu", [1, 73]], ["Joker", [2, 41]], ["Rosalina & Luma", [2, 48]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "King Dedede": [["Jigglypuff", [3, 137]], ["Bowser", [2, 111]], ["Pokemon Trainer", [2, 60]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Hero": [["Steve", [1, 28]], ["Banjo & Kazooie", [2, 171]], ["Toon Link", [3, 105]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Meta Knight": [["Sora", [1, 112]], ["King K Rool", [1, 38]], ["Lucina", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mewtwo": [["Piranha Plant", [1, 10]], ["Palutena", [2, 26]], ["Ryu", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Sora": [["Corrin", [2, 59]], ["Cloud", [2, 0]], ["Sheik", [2, 8]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Mewtwo", [2, 83]], ["Richter", [2, 80]], ["Luigi", [3, 159]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sephiroth": [["Pichu", [2, 68]], ["Olimar", [3, 146]], ["Donkey Kong", [2, 32]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mii Gunner": [["Dr Mario", [1, 0]], ["Mario", [2, 95]], ["Ryu", [3, 108]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "Pokemon Trainer": [["Zelda", [1, 126]], ["Dark Pit", [3, 196]], ["King K Rool", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Falco": [["Meta Knight", [2, 42]], ["Dark Samus", [2, 124]], ["Mega Man", [2, 70]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Bowser Jr": [["Marth", [1, 0]], ["Olimar", [1, 120]], ["Chrom", [3, 135]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Luigi": [["Diddy Kong", [3, 166]], ["Byleth", [1, 72]], ["Ness", [1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_7 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8]

max_percentage = 200
round_7_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_7_calculator(Tourney_List_7, max_percentage, round_7_scores_dict, loss_dict)
round_7_scores_dict = dict(sorted(round_7_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(round_7_scores_dict)
round_7_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

filename = os.path.join(filepath, "reports", "round_7_results.pdf")

with PdfPages(filename) as pdf:
    round_7_generator(round_7_scores_dict, win_loses, pdf)

bottom_16 = {"Inkling": 48,
             "Incineroar": 47,
             "Captain Falcon": 46,
             "Duck Hunt": 45,
             "Mr Game & Watch": 44,
             "Byleth": 43,
             "Ganondorf": 42,
             "Pikachu": 41,
             "Wii Fit Trainer": 40,
             "Rosalina & Luma": 39,
             "Lucas": 38,
             "ROB": 37,
             "Meta Knight": 36,
             "Samus": 35,
             "Luigi": 34,
             "Pokemon Trainer": 33}
             
eliminated_33_to_48 = {character for character in bottom_16}

#############################
#### Rounds 1-7 Rank Changes
#############################

# Round 1 has no meaningful pre-round ranks; instead, show the Round 1 -> Round 2 renormalization effect.
generate_round_ranking_changes_pdf(
    1,
    round_1_scores_dict,
    renormalized_scores,
    title="Round 1 → Round 2: Renormalization Rank Changes",
)

generate_round_ranking_changes_pdf(
    2,
    inital_round_2_scores,
    round_2_scores_dict,
    advance_cutoff=80,
    eliminated_characters=eliminated_6,
    title="Round 2: Rank 86 to 1 Rank Changes",
)

generate_round_ranking_changes_pdf(
    3,
    inital_round_3_scores,
    round_3_scores_dict,
    advance_cutoff=16,
    eliminated_characters=eliminated_16,
    title="Round 3: Rank 80 to 49 Rank Changes",
)

generate_round_ranking_changes_pdf(
    4,
    inital_round_4_scores,
    round_4_scores_dict,
    title="Round 4: Rank 48 to 1 Rank Changes",
)

generate_round_ranking_changes_pdf(
    5,
    inital_round_5_scores,
    round_5_scores_dict,
    advance_cutoff=26,
    eliminated_characters=eliminated_49_to_64,
    title="Round 5: Rank 64 to 23 Rank Changes",
)

generate_round_ranking_changes_pdf(
    6,
    inital_round_6_scores,
    round_6_scores_dict,
    title="Round 6: Rank 22 to 1 Rank Changes",
)

generate_round_ranking_changes_pdf(
    7,
    inital_round_7_scores,
    round_7_scores_dict,
    advance_cutoff=16,
    eliminated_characters=eliminated_33_to_48,
    title="Round 7: Rank 48 to 17 Rank Changes",
)
            
copy_loss_dict = loss_dict.copy()

def round_7_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_7_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_7_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 5: Rank 23 to 64 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_7_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_7_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 7: Rank 17 to 48 Score Distribution", pdf)   
            
round_7_scores = round_7_scores_dict.copy()
round_7_score_distribution_evolution(Tourney_List_7, round_7_scores, copy_loss_dict)

#%%
######################################################
######################## ROUND 8 #####################
######################################################

# for rank changes visual
inital_round_8_scores = round_8_scores_dict.copy()

"""

Round 8 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 200%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 200%
Score is Multiplied by (1.5 + match_number*/2)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_8_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_8_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 6: Rank 1 to 16 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 8: Rank 1 to 16 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 8: Rank 1 to 16 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 8: Rank 1 to 16 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 8: Rank 1 to 16 Score Density Plot", pdf)
    
###########################
###### Matches 16-1 #######
###########################

# 16 14.506 Toon Link
# 15 14.569 Sonic
# 14 14.581 Isabelle
# 13 14.813 Ice Climbers
# 12 14.896 Min Min
# 11 15.105 Ike
# 10 15.345 Cloud
# 9 15.548 Pyra & Mythra
# 8 15.725 King K Rool
# 7 16.004 Bowser
# 6 16.004 Link
# 5 16.151 Kirby
# 4 16.329 Dr Mario
# 3 16.463 Ridley
# 2 16.911 Zelda
# 1 17.069 Chrom

Tourney_1 = {
    "Toon Link": [["Pikachu", [2, 0]], ["Sephiroth", [2, 133]], ["Pichu", [3, 97]], ["King K Rool", [-2, 118]], ["Opponent 5", [0, 0]]], 
    "Sonic": [["Diddy Kong", [2, 27]], ["Little Mac", [2, 0]], ["Banjo & Kazooie", [-1, 83]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Isabelle": [["Wolf", [1, 57]], ["Olimar", [2, 89]], ["Falco", [-1, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ice Climbers": [["Isabelle", [2, 0]], ["Roy", [1, 11]], ["Toon Link", [1, 24]], ["Peach", [3, 127]], ["Falco", [2, 47]]] 
    }

Tourney_3 = {
    "Min Min": [["Sonic", [3, 159]], ["Ryu", [2, 15]], ["Bowser", [3, 113]], ["Cloud", [2, 0]], ["Opponent 5", [0, 0]]], 
    "Ike": [["Samus", [2, 5]], ["Lucario", [3, 163]], ["Zelda", [2, 0]], ["Palutena", [2, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Cloud": [["Incineroar", [2, 65]], ["Villager", [2, 65]], ["Ganondorf", [3, 133]], ["Falco", [1, 113]], ["Opponent 5", [0, 0]]], 
    "Pyra & Mythra": [["Toon Link", [3, 165]], ["Inkling", [1, 0]], ["Ness", [2, 53]], ["Ice Climbers", [2, 13]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "King K Rool": [["Kazuya", [2, 145]], ["Inkling", [1, 40]], ["PacMan", [1, 47]], ["Dark Samus", [3, 143]], ["Opponent 5", [0, 0]]], 
    "Bowser": [["Captain Falcon", [3, 127]], ["Wario", [1, 115]], ["Byleth", [1, 62]], ["Banjo & Kazooie", [1, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Link": [["Shulk", [3, 119]], ["Dark Pit", [1, 32]], ["King K Rool", [2, 98]], ["Daisy", [3, 126]], ["Opponent 5", [0, 0]]], 
    "Kirby": [["Sonic", [3, 95]], ["Lucas", [2, 110]], ["Banjo & Kazooie", [1, 61]], ["Bayonetta", [3, 132]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Dr Mario": [["Little Mac", [-1, 138]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ridley": [["Duck Hunt", [2, 88]], ["Dr Mario", [2, 56]], ["Lucas", [1, 29]], ["Robin", [3, 100]], ["Richter", [2, 0]]] 
    }

Tourney_8 = {
    "Zelda": [["Jigglypuff", [1, 78]], ["Wii Fit Trainer", [3, 161]], ["Isabelle", [2, 64]], ["Cloud", [3, 118]], ["Opponent 5", [0, 0]]], 
    "Chrom": [["Greninja", [3, 95]], ["Inkling", [2, 144]], ["Richter", [3, 135]], ["Luigi", [3, 78]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_8 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8]

max_percentage = 200
round_8_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_8_calculator(Tourney_List_8, max_percentage, round_8_scores_dict, loss_dict)
round_8_scores_dict = dict(sorted(round_8_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 8\n")
# print_sorted_dict(round_8_scores_dict)
round_8_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

##################################################
################ REPORT GENERATION ###############
##################################################

filename = os.path.join(filepath, "reports", "round_8_results.pdf")

with PdfPages(filename) as pdf:
    round_8_generator(round_8_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    8,
    inital_round_8_scores,
    round_8_scores_dict,
    advance_cutoff=16,
    title="Round 8: Rank 16 to 1 Rank Changes",
)

#%%
##################################################
################### ANALYSIS #####################
##################################################

def ranking_changes_4th_remerger(characters, initial_ranks, final_ranks):
    
    # Previous and CUrrent Ranks
    old_ranks = [rank for character, rank in initial_ranks.items()]
    new_ranks = [final_ranks[character] for character in initial_ranks]
    
    def ordinal(n: int) -> str:
        # Handle special cases for 11th, 12th, 13th
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    colors = []
    fig, ax = plt.subplots(figsize=(15,15))

    for i, char in enumerate(characters):
        # Left side: old rank + name
        ax.text(0, old_ranks[i], f"{ordinal(old_ranks[i])} {char}",
                ha='right', va='center', fontsize=8)
        
        # Right side: new rank + name
        ax.text(1, new_ranks[i], f"{ordinal(new_ranks[i])} {char}",
                ha='left', va='center', fontsize=8)
            
        # Top 32 End Placements
        if old_ranks[i] < 8 and new_ranks[i] < 9:
            color = "purple"   # stayed top 8
        if 49 > old_ranks[i] > 32 and new_ranks[i] < 9:
            color = "pink"     # massive improvement
        if 33 > old_ranks[i] > 16 and new_ranks[i] < 9:
            color = "green"     # jumped into top 16
        
        # Top 48 End Placements
        if old_ranks[i] < 9 and (33 > new_ranks[i] > 8):
            color = "orange"     # dropped from Top 32 to Top 48
        if (33 > old_ranks[i] > 16) and (33 > new_ranks[i] > 8):
            color = "gray"     # staying consistent, no improvement
        if old_ranks[i] > 32 and (33 > new_ranks[i] > 8):
            color = "yellow"     # improved but still struggling 

        # Top 64 End Placements
        if old_ranks[i] < 9 and (49 > new_ranks[i] > 32):
            color = "brown"    # worst case scenario
        if (33 > old_ranks[i] > 8) and (49 > new_ranks[i] > 32):
            color = "red"    # slipped to bottom elimination spot
        if (49 > old_ranks[i] > 32) and (49 > new_ranks[i] > 32):
            color = "black"    # stayed in eliminated

        colors.append(color)

        # Arrow showing movement
        ax.annotate("",
                    xy=(1, new_ranks[i]), xycoords='data',
                    xytext=(0, old_ranks[i]), textcoords='data',
                    arrowprops=dict(arrowstyle="->", lw=2, color=color))

    # Format axes
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0.5, len(characters)+0.5)
    
    # Flip so rank 1 is at the top
    ax.invert_yaxis()
    
    ax.axis("off")
    ax.set_title("Rank Changes", fontsize=14)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close() 

initial_round_7_ranks = {character: len(inital_round_7_scores) + 16 - rank for rank, character in enumerate(inital_round_7_scores)}
initial_round_8_ranks = {character: len(inital_round_8_scores) - rank for rank, character in enumerate(inital_round_8_scores)}
initial_ranks = initial_round_7_ranks | initial_round_8_ranks
combined_scores = round_7_scores_dict | round_8_scores_dict
combined_scores["Sonic"] = combined_scores["Pokemon Trainer"] + 0.03
combined_scores["Isabelle"] = combined_scores["Pokemon Trainer"] + 0.02
combined_scores["Dr Mario"] = combined_scores["Pokemon Trainer"] + 0.01
combined_scores = dict(sorted(combined_scores.items(), key=lambda item: item[1], reverse=False))
final_ranks = {character: len(combined_scores) - rank for rank, character in enumerate(combined_scores)}

# adjustments made; 

characters = [character for character in (inital_round_7_scores | inital_round_8_scores)]

filename = os.path.join(filepath, "reports", "ranking_changes", "4th_restructuring.pdf")

with PdfPages(filename) as pdf:
    ranking_changes_4th_remerger(characters, initial_ranks, final_ranks)

#%%
######################################################
######################## ROUND 9 #####################
######################################################

round_7_and_8_scores_dict = round_7_scores_dict | round_8_scores_dict
round_7_and_8_scores_dict = dict(sorted(round_7_and_8_scores_dict.items(), key=lambda item: item[1], reverse=False))
# Fixing some character scores
round_7_and_8_scores_dict["Sonic"] = round_7_and_8_scores_dict["Pokemon Trainer"] + 0.03
round_7_and_8_scores_dict["Isabelle"] = round_7_and_8_scores_dict["Pokemon Trainer"] + 0.02
round_7_and_8_scores_dict["Dr Mario"] = round_7_and_8_scores_dict["Pokemon Trainer"] + 0.01

round_9_and_10_scores_dict = {character:score for character, score in round_7_and_8_scores_dict.items() if score > round_7_and_8_scores_dict["Pokemon Trainer"]}
round_9_and_10_scores_dict["Sonic"] = round_8_scores_dict["Sonic"]
round_9_and_10_scores_dict["Isabelle"] = round_8_scores_dict["Isabelle"]
round_9_and_10_scores_dict["Dr Mario"] = round_8_scores_dict["Dr Mario"]

def round_9_and_10_renormalizer(round_9_and_10_scores_dict):
    
    for character in round_9_and_10_scores_dict:
        round_9_and_10_scores_dict[character] = round(((round_9_and_10_scores_dict[character])**(5/11))*np.log(round_9_and_10_scores_dict[character]), 3)
        
    return round_9_and_10_scores_dict

round_9_and_10_characters_dict = round_9_and_10_renormalizer(round_9_and_10_scores_dict)
round_9_scores_dict = {character:score for character,score in round_9_and_10_characters_dict.items() if score <= round_9_and_10_characters_dict["Sora"]}
round_9_scores_dict = dict(sorted(round_9_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_10_scores_dict = {character:score for character,score in round_9_and_10_characters_dict.items() if score > round_9_and_10_characters_dict["Sora"]}

# for rank changes visual
inital_round_9_scores = round_9_scores_dict.copy()

#%%

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 9/10 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_9_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                # print(key, fight[1][0], fights)
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + 0 if fight[1][0] < 4 else 1
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + 0 if fight[1][0] < 4 else 1
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_9_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 9: Rank 32 to 9 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 9: Rank 32 to 9 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 9: Rank 32 to 9 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 9: Rank 32 to 9 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 9: Rank 32 to 9 Score Density Plot", pdf)
    
#%%
############################
####### Zombies 42-33 ######
############################

round_8_total_records = pd.read_csv(os.path.join(filepath, "records", "all_records_to_8.csv"))

accumulated_score_dict = round_8_total_records.groupby('Character')['Accumulated_Sum'].max().to_dict()
for character in round_9_and_10_characters_dict: del accumulated_score_dict[character]
accumulated_score_dict = dict(sorted(accumulated_score_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nScore Count Dictionary\n")
# print_sorted_dict(accumulated_score_dict)

filtered = round_8_total_records[round_8_total_records['Round'] < 4]
filtered = filtered[~filtered['Character'].isin(round_9_and_10_characters_dict.keys())]
match_count = filtered.groupby('Character').size().to_dict()
match_count = dict(sorted(match_count.items(), key=lambda item: item[1], reverse=False))
# print("\nMatch Count Dictionary\n")
# print_sorted_dict(match_count)

score_average_dict = {character:round(accumulated_score_dict[character]/match_count[character], 3) for character in match_count}
score_average_dict = dict(sorted(score_average_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nAverage Score Dictionary\n")
# print_sorted_dict(score_average_dict)

# Average Score Dictionary    

# 86 0.125 Ken
# 85 0.182 Kazuya
# 84 0.262 Simon
# 83 0.36 Mega Man
# 82 0.375 Bayonetta
# 81 0.397 Joker
# 80 0.742 Diddy Kong
# 79 0.889 Pichu
# 78 1.074 Lucina
# 77 1.247 Ryu
# 76 1.369 Olimar
# 75 1.401 Villager
# 74 1.417 Daisy
# 73 1.533 Jigglypuff
# 72 1.534 Marth
# 71 1.619 Richter
# 70 1.642 Robin
# 69 1.645 Zero Suit Samus
# 68 1.648 Fox
# 67 1.657 Mii Brawler
# 66 1.695 PacMan
# 65 1.697 Shulk
# 64 1.703 Corrin
# 63 1.741 Inkling
# 62 1.775 Palutena
# 61 1.899 Greninja
# 60 1.908 Mii Swordfighter
# 59 1.926 Ness
# 58 1.944 Sheik
# 57 1.968 Duck Hunt
# 56 2.0 Rosalina & Luma
# 55 2.01 Captain Falcon
# 54 2.029 Peach
# 53 2.044 Snake
# 52 2.14 Steve
# 51 2.154 Wario
# 50 2.208 Terry
# 49 2.21 Byleth
# 48 2.216 Mario
# 47 2.224 Pikachu
# 46 2.247 Pit
# 45 2.273 Dark Samus
# 44 2.278 Incineroar
# 43 2.28 Lucario
# 42 2.307 Ganondorf
# 41 2.32 Wii Fit Trainer
# 40 2.345 Wolf
# 39 2.348 ROB
# 38 2.372 Meta Knight
# 37 2.4 Pokemon Trainer
# 36 2.423 Mr Game & Watch
# 35 2.493 Luigi
# 34 2.565 Samus
# 33 2.744 Lucas

# Score Count Dictionary

# 86 0.25 Ken
# 85 0.365 Kazuya
# 84 0.72 Mega Man
# 83 0.7850000000000001 Simon
# 82 0.7949999999999999 Joker
# 81 1.125 Bayonetta
# 80 3.71 Diddy Kong
# 79 4.445 Pichu
# 78 5.37 Lucina
# 77 7.48 Ryu
# 76 8.5 Daisy
# 75 9.585 Olimar
# 74 10.22 Corrin
# 73 10.22 Snake
# 72 10.7 Steve
# 71 11.21 Villager
# 70 11.335 Richter
# 69 11.515 Zero Suit Samus
# 68 11.88 Shulk
# 67 13.245 Terry
# 66 13.255 Mii Brawler
# 65 13.795 Jigglypuff
# 64 14.2 Palutena
# 63 14.78 Robin
# 62 14.83 Fox
# 61 15.075 Wario
# 60 15.19 Greninja
# 59 15.335 Marth
# 58 16.955 PacMan
# 57 17.73 Mario
# 56 18.185 Dark Samus
# 55 18.24 Lucario
# 54 19.08 Mii Swordfighter
# 53 19.26 Ness
# 52 19.44 Sheik
# 51 20.29 Peach
# 50 20.89 Inkling
# 49 21.105 Wolf
# 48 22.465 Pit
# 47 28.14 Captain Falcon
# 46 29.52 Duck Hunt
# 45 29.615 Incineroar
# 44 33.15 Byleth
# 43 33.925 Mr Game & Watch
# 42 34.005 Rosalina & Luma
# 41 35.58 Meta Knight
# 40 35.59 Pikachu
# 39 36.905 Ganondorf
# 38 37.575 ROB
# 37 39.44 Wii Fit Trainer
# 36 40.795 Pokemon Trainer
# 35 41.04 Samus
# 34 44.88 Luigi
# 33 46.64 Lucas

# Zombies Returning will be there first 8 to be in both lists

# 42 Wolf - 21.105, 2.345
# 41 Byleth - 33.15, 2.21
# 40 Mr. Game and Watch - 33.925, 2.423
# 39 Meta Knight - 35.58, 2.372
# 38 ROB - 37.545, 2.348
# 37 Wii Fit Trainer - 39.44, 2.4
# 36 Pokemon Trainer - 40.795, 2.4
# 35 Samus - 41.04, 2.565
# 34 Luigi - 44.88, 2.493
# 33 Lucas - 46.64, 2.744

# Now we need scores for Round 9, ans Merging the score dicts

old_scores_dict = {"Wolf": 11.63,
                   "Byleth": 16.69,
                   'Mr Game & Watch': 15.97,
                   'Meta Knight': 25.52,
                   'ROB': 25.11,
                   'Wii Fit Trainer': 24.1,
                   'Pokemon Trainer': 27.68,
                   'Samus': 26.89,
                   'Luigi': 27.06,
                   'Lucas': 24.83}

zombie_scores_dict = round_9_and_10_renormalizer(old_scores_dict)
zombie_scores_dict = dict(sorted(zombie_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print_sorted_dict(zombie_scores_dict)

min_score_zombies = min([score for character, score in zombie_scores_dict.items()])
min_score_32th_to_9th = min([score for character, score in round_9_scores_dict.items()])
difference = round(min_score_32th_to_9th - min_score_zombies, 3)

def zombie_score_sigmoidal_equalizer(zombie_scores_dict):
    
    for character in zombie_scores_dict: 
        zombie_scores_dict[character] = round(min_score_zombies + difference/(1 + np.exp(-(zombie_scores_dict[character]-min_score_32th_to_9th))), 3)

    return zombie_scores_dict

zombie_scores_dict = zombie_score_sigmoidal_equalizer(zombie_scores_dict)
# print_sorted_dict(zombie_scores_dict)

round_9_scores_dict = zombie_scores_dict | round_9_scores_dict 

############################
####### Matches 42-9 #######
############################

# 42 7.637 Wolf
# 41 8.504 Mr Game & Watch
# 40 8.749 Byleth
# 39 10.243 Wii Fit Trainer
# 38 10.273 Lucas
# 37 10.283 ROB
# 36 10.295 Meta Knight
# 35 10.323 Samus
# 34 10.325 Luigi
# 33 10.333 Pokemon Trainer

# 32 10.367 Dr Mario
# 31 12.939 Isabelle
# 30 14.225 Sonic
# 29 15.048 Donkey Kong
# 28 15.158 Banjo & Kazooie
# 27 15.28 Dark Pit
# 26 15.317 Bowser Jr
# 25 15.337 Young Link
# 24 15.451 Hero
# 23 15.487 Little Mac
# 22 15.576 Yoshi
# 21 15.777 Falco
# 20 15.801 Mewtwo
# 19 15.949 Bowser
# 18 15.977 King Dedede
# 17 15.981 Roy
# 16 16.072 King K Rool
# 15 16.545 Sephiroth
# 14 16.564 Piranha Plant
# 13 16.685 Mii Gunner
# 12 16.755 Pyra & Mythra
# 11 16.794 Ice Climbers
# 10 16.895 Toon Link
# 9 16.934 Sora

# Only Top 16 Survive Out of 34. Lots of Points to Be Earned Thought. We are doing 4 Stock Now.          
                                                                                                                                                                                                                                                                                                                                                             
Tourney_1 = {
    "Byleth": [["Rosalina & Luma", [3, 94]], ["Simon", [4, 132]], ["Olimar", [3, 11]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Wolf": [["Fox", [3, 186]], ["Greninja", [3, 11]], ["Lucas", [3, 50]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Wii Fit Trainer": [["Lucina", [3, 92]], ["Zero Suit Samus", [3, 58]], ["Ike", [2, 5]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mr Game & Watch": [["Mega Man", [2, 94]], ["Daisy", [2, 105]], ["Bowser", [2, 39]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Samus": [["Mega Man", [3, 112]], ["Sonic", [3, 106]], ["Kazuya", [-2, 54]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "ROB": [["Lucina", [3, 167]], ["King Dedede", [2, 91]], ["Greninja", [3, 25]], ["Kazuya", [-1, 52]], ["Opponent 5", [0, 0]]], 
    "Meta Knight": [["Bowser", [2, 48]], ["Peach", [3, 75]], ["Hero", [1, 52]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Lucas": [["Incineroar", [2, 40]], ["Villager", [2, 47]], ["Duck Hunt", [3, 91]], ["Opponent 4", [0, 0]], ["Kazuya", [3, 137]]] 
    }

Tourney_3 = {
    "Pokemon Trainer": [["Mr Game & Watch", [2, 135]], ["Steve", [3, 50]], ["Pichu", [3, 261]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dr Mario": [["Bayonetta", [3, 106]], ["Wario", [2, 22]], ["King Dedede", [3, 110]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Isabelle": [["Diddy Kong", [2, 73]], ["Pit", [3, 149]], ["Zelda", [2, 31]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Luigi": [["Isabelle", [3, 67]], ["Dark Pit", [3, 127]], ["Meta Knight", [3, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Banjo & Kazooie": [["Byleth", [1, 60]], ["Mr Game & Watch", [3, 111]], ["Link", [2, 86]], ["Bowser Jr", [2, 24]], ["Opponent 5", [0, 0]]], 
    "Sonic": [["Ice Climbers", [3, 105]], ["Ganondorf", [1, 0]], ["Bowser Jr", [-1, 96]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Dark Pit": [["Dark Pit", [1, 53]], ["Kazuya", [1, 120]], ["Robin", [2, 42]], ["King K Rool", [2, 70]], ["Opponent 5", [0, 0]]],          
    "Donkey Kong": [["King K Rool", [-1, 94]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "Little Mac": [["Meta Knight", [2, 55]], ["Shulk", [1, 5]], ["Mega Man", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Bowser Jr": [["Byleth", [2, 65]], ["Piranha Plant", [2, 45]], ["Olimar", [2, 129]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Hero": [["Joker", [2, 13]], ["Ganondorf", [2, 54]], ["Falco", [2, 21]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Young Link": [["Daisy", [3, 56]], ["Min Min", [3, 138]], ["Wii Fit Trainer", [3, 115]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Falco": [["Cloud", [2, 101]], ["Meta Knight", [2, 39]], ["Chrom", [2, 20]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Bowser": [["Ice Climbers", [2, 10]], ["Link", [3, 80]], ["Simon", [2, 39]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Yoshi": [["Sephiroth", [3, 106]], ["Donkey Kong", [1, 45]], ["Snake", [2, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Mewtwo": [["Kirby", [3, 85]], ["Sonic", [3, 4]], ["Pyra & Mythra", [2, 10]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Roy": [["Fox", [1, 54]], ["Sora", [2, 52]], ["Dark Pit", [2, 40]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "King K Rool": [["Snake", [2, 76]], ["Joker", [2, 0]], ["Hero", [1, 55]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sephiroth": [["Sephiroth", [3, 6]], ["Toon Link", [2, 13]], ["Jigglypuff", [1, 81]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "King Dedede": [["Ness", [3, 8]], ["Cloud", [2, 126]], ["Villager", [1, 76]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "Piranha Plant": [["Snake", [3, 37]], ["Sephiroth", [1, 117]], ["Kazuya", [2, 101]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Mii Gunner": [["ROB", [3, 135]], ["Diddy Kong", [3, 75]], ["Rosalina & Luma", [3, 24]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Pyra & Mythra": [["Zelda", [3, 85]], ["Toon Link", [2, 13]], ["Isabelle", [1, 79]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
    "Ice Climbers": [["Ike", [3, 79]], ["Pit", [3, 135]], ["Pichu", [3, 79]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_9 = {
    "Toon Link": [["Sora", [-1, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Sora": [["Meta Knight", [3, 61]], ["Mewtwo", [1, 85]], ["Wii Fit Trainer", [1, 47]], ["Cloud", [3, 118]], ["Pichu", [1, 0]]], 
   }

Tourney_List_9 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9]

max_percentage = 200
round_9_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_9_calculator(Tourney_List_9, max_percentage, round_9_scores_dict, loss_dict)
round_9_scores_dict = dict(sorted(round_9_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 9 Standings, Top 16 Advance\n")
# print_sorted_dict(round_9_scores_dict)
round_9_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

filename = os.path.join(filepath, "reports", "round_9_results.pdf")

with PdfPages(filename) as pdf:
    round_9_generator(round_9_scores_dict, win_loses, pdf)

bottom_18 = {"Donkey Kong": 42,
             "Toon Link": 41,
             "Samus": 40,
             "Mr Game & Watch": 39,
             "Sonic": 38,
             "Meta Knight": 37,
             "Byleth": 36,
             "ROB": 35,
             "Pokemon Trainer": 34,
             "Wolf": 33,
             "Dark Pit": 32,
             "Isabelle": 31,
             "Wii Fit Trainer": 30,
             "Pyra & Mythra": 29,
             "Luigi": 28,
             "King K Rool": 27,
             "Lucas": 26,
             "Roy": 25}
             
eliminated_25_to_42 = {character for character in bottom_16}
            
copy_loss_dict = loss_dict.copy()

def round_9_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_9_histogram_evolution.pdf") as pdf:
        for i in range(5):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_9_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 9: Rank 42 to 9 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_9_distribution_evolution.pdf") as pdf:
        for i in range(5):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_9_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 9: Rank 42 to 9 Score Distribution", pdf)   
            
round_9_scores = round_9_scores_dict.copy()
round_9_score_distribution_evolution(Tourney_List_9, round_9_scores, copy_loss_dict)

# Round 9 Ranking Changes Chart
generate_round_ranking_changes_pdf(
    9,
    inital_round_9_scores,
    round_9_scores_dict,
    advance_cutoff=16,
    title="Round 9: Rank 42 to 9 Rank Changes",
)

#%%
######################################################
######################## ROUND 10 ####################
######################################################

# for rank changes visual
inital_round_10_scores = round_10_scores_dict.copy()

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 9/10 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_10_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 3:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 3:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"][0] += 1
                        win_loses["Won Round 3"][1] += character_dict[key]
                        win_loses["Won Round 3"][2].append(key)
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_10_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 10: Rank 1 to 8 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 10: Rank 1 to 8 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 10: Rank 1 to 8 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 10: Rank 1 to 8 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 10: Rank 1 to 8 Score Density Plot", pdf)

###########################
###### Matches 8-1 #######
###########################

# 8 17.284 Kirby
# 7 17.441 Cloud
# 6 17.578 Link
# 5 18.075 Ike
# 4 18.183 Ridley
# 3 18.303 Zelda
# 2 18.344 Min Min
# 1 19.355 Chrom

Tourney_1 = {
    "Kirby": [["Simon", [3, 136]], ["Jigglypuff", [1, 29]], ["Simon", [3, 68]], ["Duck Hunt", [2, 11]], ["Opponent 5", [0, 0]]], 
    "Cloud": [["Ness", [1, 0]], ["ROB", [2, 65]], ["Zelda", [3, 98]], ["Meta Knight", [3, 99]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Link": [["Sheik", [3, 2]], ["Terry", [2, 47]], ["Dark Pit", [2, 79]], ["Dr Mario", [2, 34]], ["Opponent 5", [0, 0]]], 
    "Ike": [["Duck Hunt", [3, 19]], ["Greninja", [3, 0]], ["Corrin", [2, 0]], ["Mr Game & Watch", [3, 121]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Ridley": [["Lucario", [1, 0]], ["Sephiroth", [1, 55]], ["Incineroar", [3, 97]], ["Bayonetta", [4, 179]], ["Opponent 5", [0, 0]]], 
    "Zelda": [["Pikachu", [4, 189]], ["Dr Mario", [2, 4]], ["Daisy", [2, 6]], ["Kazuya", [2, 52]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Min Min": [["Chrom", [3, 70]], ["Pyra & Mythra", [2, 0]], ["Dr Mario", [2, 97]], ["Samus", [3, 65]], ["Opponent 5", [0, 0]]], 
    "Chrom": [["Ike", [2, 97]], ["Palutena", [3, 64]], ["ROB", [3, 15]], ["Shulk", [1, 84]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_10 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4]

max_percentage = 200
round_10_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_10_calculator(Tourney_List_10, max_percentage, round_10_scores_dict, loss_dict)
round_10_scores_dict = dict(sorted(round_10_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 10\n")
# print_sorted_dict(round_10_scores_dict)
round_10_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_10_results.pdf") as pdf:
    round_10_generator(round_10_scores_dict, win_loses, pdf)

# Round 10 Ranking Changes Chart
generate_round_ranking_changes_pdf(
    10,
    inital_round_10_scores,
    round_10_scores_dict,
    advance_cutoff=8,
    title="Round 10: Rank 8 to 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 11 ####################
######################################################

round_9_and_10_scores_dict = round_9_scores_dict | round_10_scores_dict
round_9_and_10_scores_dict = dict(sorted(round_9_and_10_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_11_and_12_scores_dict = {character:score for character, score in round_9_and_10_scores_dict.items() if score > round_9_and_10_scores_dict["Roy"]}

def round_11_and_12_renormalizer(round_11_and_12_scores_dict):
    
    for character in round_11_and_12_scores_dict:
        round_11_and_12_scores_dict[character] = round(((round_11_and_12_scores_dict[character])**(5/11))*np.log(round_11_and_12_scores_dict[character]), 3)
        
    return round_11_and_12_scores_dict

round_11_and_12_characters_dict = round_11_and_12_renormalizer(round_11_and_12_scores_dict)
round_11_scores_dict = {character:score for character,score in round_11_and_12_characters_dict.items() if score <= round_11_and_12_characters_dict["Mewtwo"]}
round_11_scores_dict = dict(sorted(round_11_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_12_scores_dict = {character:score for character,score in round_11_and_12_characters_dict.items() if score > round_11_and_12_characters_dict["Mewtwo"]}

# for rank changes visual
inital_round_11_scores = round_11_scores_dict.copy()

# for rank changes visual
inital_round_12_scores = round_12_scores_dict.copy()

"""

Refactored Scores: N^(6/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_11_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_11_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 11: Rank 24 to 7 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 11: Rank 24 to 7 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 11: Rank 24 to 7 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 11: Rank 24 to 7 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 11: Rank 24 to 7 Score Density Plot", pdf)

###########################
###### Matches 24-7 #######
###########################

# 24 16.49 Bowser Jr
# 23 16.53 Yoshi
# 22 16.6 Dr Mario
# 21 16.74 Little Mac
# 20 16.75 Falco
# 19 16.77 King Dedede
# 18 16.84 Sephiroth
# 17 17.06 Hero
# 16 17.07 Piranha Plant
# 15 17.39 Sora
# 14 17.45 Banjo & Kazooie
# 13 18.03 Bowser
# 12 18.14 Young Link
# 11 18.25 Ridley
# 10 18.38 Cloud
# 9 18.79 Ice Climbers
# 8 18.79 Min Min
# 7 18.91 Mewtwo

Tourney_1 = {
    "Bowser Jr": [["Little Mac", [2, 0]], ["Cloud", [2, 67]], ["Jigglypuff", [3, 50]], ["Pokemon Trainer", [2, 0]], ["Opponent 5", [0, 0]]], 
    "Yoshi": [["Pikachu", [2, 85]], ["Corrin", [2, 40]], ["Dark Pit", [2, 25]], ["Donkey Kong", [1, 0]], ["Opponent 5", [0, 0]]] 
    }
    
Tourney_2 = {
    "Dr Mario": [["King Dedede", [1, 0]], ["Pikachu", [2, 21]], ["Zelda", [3, 120]], ["PacMan", [3, 136]], ["Mr Game & Watch", [3, 105]]], 
    "Little Mac": [["Bayonetta", [3, 135]], ["Steve", [-1, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Falco": [["Lucas", [2, 154]], ["PacMan", [1, 54]], ["Banjo & Kazooie", [2, 0]], ["Pyra & Mythra", [-2, 0]], ["Opponent 5", [0, 0]]], 
    "King Dedede": [["Lucario", [2, 79]], ["Ridley", [2, 51]], ["Ice Climbers", [2, 121]], ["Byleth", [3, 153]], ["Pyra & Mythra", [1, 75]]] 
    }

Tourney_4 = {
    "Sephiroth": [["Young Link", [4, 161]], ["Byleth", [-2, 63]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Hero": [["Marth", [1, 120]], ["Piranha Plant", [2, 90]], ["Link", [2, 85]], ["Toon Link", [2, 88]], ["Cloud", [-1, 95]]] 
    }

Tourney_5 = {
    "Piranha Plant": [["Jigglypuff", [1, 54]], ["Hero", [2, 171]], ["Dark Pit", [1, 57]], ["Greninja", [2, 65]], ["Simon", [2, 97]]], 
    "Sora": [["Palutena", [2, 56]], ["King K Rool", [-1, 56]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Banjo & Kazooie": [["Mega Man", [2, 20]], ["Wii Fit Trainer", [2, 0]], ["Luigi", [2, 23]], ["Cloud", [3, 7]], ["Steve", [2, 49]]], 
    "Bowser": [["Terry", [-1, 100]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_7 = {
    "Young Link": [["Fox", [1, 18]], ["Incineroar", [1, 103]], ["Dark Samus", [3, 86]], ["Bowser Jr", [2, 116]], ["Opponent 5", [0, 0]]], 
    "Ridley": [["Pit", [1, 132]], ["Pikachu", [1, 13]], ["Bowser", [2, 102]], ["Pokemon Trainer", [1, 63]], ["Opponent 5", [0, 0]]] 
    }

Tourney_8 = {
    "Cloud": [["Lucario", [3, 38]], ["Dark Pit", [2, 111]], ["Inkling", [-1, 13]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Ice Climbers": [["Lucina", [2, 24]], ["Ken", [2, 92]], ["Ganondorf", [2, 61]], ["Kirby", [1, 36]], ["Inkling", [2, 22]]] 
    }

Tourney_9 = {
    "Min Min": [["Isabelle", [3, 0]], ["Inkling", [1, 70]], ["Captain Falcon", [1, 78]], ["King K Rool", [1, 81]], ["Opponent 5", [0, 0]]], 
    "Mewtwo": [["Jigglypuff", [2, 42]], ["Kazuya", [3, 111]], ["Pikachu", [1, 66]], ["Mario", [2, 122]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_11 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9]

max_percentage = 200
round_11_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_11_calculator(Tourney_List_11, max_percentage, round_11_scores_dict, loss_dict)
round_11_scores_dict = dict(sorted(round_11_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 11\n")
# print_sorted_dict(round_11_scores_dict)
round_11_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_11_results.pdf") as pdf:
    round_11_generator(round_11_scores_dict, win_loses, pdf)

# Round 11 Ranking Changes Chart
generate_round_ranking_changes_pdf(
    11,
    inital_round_11_scores,
    round_11_scores_dict,
    advance_cutoff=10,
    title="Round 11: Rank 24 to 7 Rank Changes",
)

#%%
######################################################
######################## ROUND 12 ####################
######################################################

"""

Refactored Scores: N^(6/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_12_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_12_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 12: Rank 6 to 1 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 12: Rank 6 to 1 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 12: Rank 6 to 1 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 12: Rank 6 to 1 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 12: Rank 6 to 1 Score Density Plot", pdf)

###########################
###### Matches 6-1 ########
###########################

# 6 18.951 Kirby
# 5 19.254 Link
# 4 19.542 Mii Gunner
# 3 19.639 Zelda
# 2 20.424 Chrom
# 1 20.976 Ike

Tourney_1 = {
    "Kirby": [["Palutena", [-1, 81]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Link": [["Wolf", [3, 105]], ["Ice Climbers", [2, 84]], ["Simon", [1, 78]], ["Wii Fit Trainer", [3, 54]], ["Shulk", [3, 0]]] 
    }

Tourney_2 = {
    "Mii Gunner": [["Robin", [-1, 109]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
    "Zelda": [["Bowser", [2, 15]], ["Corrin", [3, 45]], ["Ridley", [1, 0]], ["Mr Game & Watch", [4, 156]], ["Wario", [3, 130]]] 
    }

Tourney_3 = {
    "Chrom": [["Pikachu", [2, 50]], ["Pyra & Mythra", [2, 0]], ["Dark Samus", [2, 58]], ["Cloud", [2, 26]], ["Corrin", [3, 97]]], 
    "Ike": [["Richter", [-1, 55]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }
    
Tourney_List_12 = [Tourney_1, Tourney_2, Tourney_3]

max_percentage = 200
round_12_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_12_calculator(Tourney_List_12, max_percentage, round_12_scores_dict, loss_dict)
round_12_scores_dict = dict(sorted(round_12_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 12\n")
# print_sorted_dict(round_12_scores_dict)
round_12_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_12_results.pdf") as pdf:
    round_12_generator(round_12_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    12,
    inital_round_12_scores,
    round_12_scores_dict,
    advance_cutoff=6,
    title="Round 12: Rank 6 to 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 13 ####################
######################################################

# Pre-Filtering

# Out from top 24 to 7 (16th): 'Hero': 37.98,

# 'Kirby': 19.55,
# 'Mii Gunner': 20.27,
# 'Ike': 21.38,

round_11_and_12_scores_dict = round_11_scores_dict | round_12_scores_dict
round_11_and_12_scores_dict['Kirby'] = 37.99
round_11_and_12_scores_dict['Mii Gunner'] = 38.00
round_11_and_12_scores_dict['Ike'] = 38.01

round_11_and_12_scores_dict = dict(sorted(round_11_and_12_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_13_and_14_scores_dict = {character:score for character, score in round_11_and_12_scores_dict.items() if score > round_11_and_12_scores_dict["Hero"]}

round_13_and_14_scores_dict['Kirby'] = 19.55
round_13_and_14_scores_dict['Mii Gunner'] = 20.27
round_13_and_14_scores_dict['Ike'] = 21.38

def round_13_and_14_renormalizer(round_13_and_14_scores_dict):
    
    for character in round_13_and_14_scores_dict:
        round_13_and_14_scores_dict[character] = round(((round_13_and_14_scores_dict[character])**(5/11))*np.log(round_13_and_14_scores_dict[character]), 3)
        
    return round_13_and_14_scores_dict

round_13_and_14_characters_dict = round_13_and_14_renormalizer(round_13_and_14_scores_dict)
round_13_scores_dict = {character:score for character,score in round_13_and_14_characters_dict.items() if score <= round_13_and_14_characters_dict["Bowser Jr"]}
round_13_scores_dict = dict(sorted(round_13_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_14_scores_dict = {character:score for character,score in round_13_and_14_characters_dict.items() if score > round_13_and_14_characters_dict["Bowser Jr"]}

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_13_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_13_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 13: Rank 16 to 5 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 13: Rank 16 to 5 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 13: Rank 16 to 5 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 13: Rank 16 to 5 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 13: Rank 16 to 5 Score Density Plot", pdf)
    
############################
###### Matches 16-5 ########
############################

# Bonus 

round_13_scores_dict['Hero'] = 11.000

# for rank changes visual
inital_round_13_scores = round_13_scores_dict.copy()

# 15 11.484 Kirby
# 14 11.816 Mii Gunner
# 13 12.32 Ike
# 12 19.261 Yoshi
# 11 19.47 Young Link
# 10 19.481 Piranha Plant
# 9 19.779 Ice Climbers
# 8 20.784 Mewtwo
# 7 20.931 King Dedede
# 6 21.547 Dr Mario
# 5 21.646 Bowser Jr
    
Tourney_1 = {
    "Kirby": [["Palutena", [2, 10]], ["Rosalina & Luma", [4, 109]], ["Kazuya", [2, 25]], ["PacMan", [2, 16]], ["Opponent 5", [0, 0]]], 
    "Mii Gunner": [["Marth", [3, 54]], ["Pyra & Mythra", [2, 0]], ["Donkey Kong", [2, 0]], ["Wario", [2, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Ike": [["Dark Pit", [3, 57]], ["Lucina", [3, 119]], ["Min Min", [3, 72]], ["Zelda", [1, 78]], ["Opponent 5", [0, 0]]], 
    "Yoshi": [["Pikachu", [2, 31]], ["Peach", [3, 94]], ["Samus", [2, 45]], ["Mewtwo", [2, 67]], ["Opponent 5", [0, 0]]] 
    }

Tourney_3 = {
    "Young Link": [["Roy", [2, 30]], ["Sora", [2, 82]], ["Kirby", [1, 0]], ["Wario", [3, 78]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Duck Hunt", [3, 83]], ["Isabelle", [3, 174]], ["Diddy Kong", [2, 48]], ["Marth", [3, 37]], ["Opponent 5", [0, 0]]] 
    }

Tourney_4 = {
    "Ice Climbers": [["Zero Suit Samus", [2, 0]], ["Ryu", [2, 2]], ["Toon Link", [2, 37]], ["Zelda", [2, 116]], ["Sora", [2, 53]]], 
    "Mewtwo": [["Bowser", [3, 94]], ["Dark Samus", [2, 18]], ["Byleth", [-2, 74]], ["Sora", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_5 = {
    "King Dedede": [["Olimar", [2, 63]], ["Simon", [1, 32]], ["Incineroar", [2, 0]], ["Pikachu", [2, 23]], ["Opponent 5", [0, 0]]], 
    "Dr Mario": [["Chrom", [1, 100]], ["Daisy", [3, 153]], ["Palutena", [3, 0]], ["Ganondorf", [1, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_6 = {
    "Hero": [["Wolf", [1, 140]], ["Samus", [3, 45]], ["Ken", [2, 72]], ["Palutena", [3, 96]], ["Mr Game & Watch", [3, 144]]], 
    "Bowser Jr": [["Ridley", [-1, 63]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }
    
Tourney_List_13 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6]

max_percentage = 200
round_13_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_13_calculator(Tourney_List_13, max_percentage, round_13_scores_dict, loss_dict)
round_13_scores_dict = dict(sorted(round_13_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 13\n")
# print_sorted_dict(round_13_scores_dict)
round_13_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_13_results.pdf") as pdf:
    round_13_generator(round_13_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    13,
    inital_round_13_scores,
    round_13_scores_dict,
    advance_cutoff=6,
    title="Round 13: Rank 16 to 5 Rank Changes",
)

#%%
######################################################
######################## ROUND 14 ####################
######################################################

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 13/14 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1 + (match_number)*0.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_14_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/2)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_14_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 14: Rank 4 to 1 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 14: Rank 6 to 1 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 14: Rank 4 to 1 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 14: Rank 4 to 1 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 14: Rank 4 to 1 Score Density Plot", pdf)

###########################
###### Matches 4-1 ########
###########################

# 4 22.506 Link
# 3 22.64 Chrom
# 2 23.031 Banjo & Kazooie
# 1 24.228 Zelda

Tourney_1 = {
    "Link": [["Donkey Kong", [3, 96]], ["Isabelle", [3, 115]], ["Zero Suit Samus", [2, 77]], ["Jigglypuff", [4, 101]], ["Opponent 5", [0, 0]]], 
    "Chrom": [["Bayonetta", [2, 6]], ["Little Mac", [2, 73]], ["Wii Fit Trainer", [2, 7]], ["Dr Mario", [3, 62  ]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Banjo & Kazooie": [["Roy", [2, 83]], ["Snake", [1, 69]], ["Lucario", [3, 79]], ["ROB", [-1, 142]], ["Opponent 5", [0, 0]]], 
    "Zelda": [["Dark Samus", [2, 153]], ["Sora", [2, 31]], ["Villager", [1, 14]], ["King K Rool", [3, 143]], ["ROB", [1, 0]]] 
    }
    
Tourney_List_14 = [Tourney_1, Tourney_2]

# for rank changes visual
inital_round_14_scores = round_14_scores_dict.copy()

max_percentage = 200
round_14_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_14_calculator(Tourney_List_14, max_percentage, round_14_scores_dict, loss_dict)
round_14_scores_dict = dict(sorted(round_14_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 14\n")
# print_sorted_dict(round_14_scores_dict)
round_14_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_14_results.pdf") as pdf:
    round_14_generator(round_14_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    14,
    inital_round_14_scores,
    round_14_scores_dict,
    advance_cutoff=4,
    title="Round 14: Rank 4 to 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 15 ####################
######################################################

round_15_and_16_scores_dict = round_13_scores_dict | round_14_scores_dict
round_15_and_16_scores_dict['Banjo & Kazooie'] = 41.56

round_15_and_16_scores_dict = dict(sorted(round_15_and_16_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_15_and_16_scores_dict = {character:score for character, score in round_15_and_16_scores_dict.items() if score > round_15_and_16_scores_dict["Kirby"]}

round_15_and_16_scores_dict['Banjo & Kazooie'] = 41.56

def round_15_and_16_renormalizer(round_15_and_16_scores_dict):
    
    for character in round_15_and_16_scores_dict:
        round_15_and_16_scores_dict[character] = round(((round_15_and_16_scores_dict[character])**(5/11))*np.log(round_15_and_16_scores_dict[character]), 3)
        
    return round_15_and_16_scores_dict

round_15_and_16_characters_dict = round_15_and_16_renormalizer(round_15_and_16_scores_dict)
round_15_scores_dict = {character:score for character,score in round_15_and_16_characters_dict.items() if score <= round_15_and_16_characters_dict["Ice Climbers"]}
round_15_scores_dict = dict(sorted(round_15_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_16_scores_dict = {character:score for character,score in round_15_and_16_characters_dict.items() if score > round_15_and_16_characters_dict["Ice Climbers"]}

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1.5 + (match_number)/1.7)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1.5 + (match_number)/1.7)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_15_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.7)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.7)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_15_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 15: Rank 10 to 5 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 15: Rank 10 to 5 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 15: Rank 10 to 5 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 15: Rank 10 to 5 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 15: Rank 10 to 5 Score Density Plot", pdf)

###########################
##### Matches 10-5 ########
###########################

# 10 20.28 Banjo & Kazooie
# 09 21.04 Young Link
# 08 21.16 Yoshi
# 07 21.58 King Dedede
# 06 21.89 Dr Mario
# 05 22.33 Ice Climbers

Tourney_1 = {
    "Banjo & Kazooie": [["Joker", [4, 199]], ["Ice Climbers", [3, 66]], ["Pit", [2, 4]], ["Piranha Plant", [3, 118]], ["Opponent 5", [0, 0]]], 
    "Young Link": [["Ike", [1, 25]], ["Shulk", [2, 0]], ["ROB", [3, 105]], ["Chrom", [2, 44]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Yoshi": [["Zero Suit Samus", [2, 77]], ["Joker", [2, 88]], ["Byleth", [1, 82]], ["Wario", [2, 129]], ["Opponent 5", [0, 0]]], 
    "King Dedede": [["Young Link", [1, 74]], ["Little Mac", [3, 0]], ["Greninja", [3, 85]], ["Lucina", [3, 119]], ["Opponent 5", [0, 0]]] 
    }
    
Tourney_3 = {
    "Dr Mario": [["Dark Pit", [3, 43]], ["Fox", [3, 119]], ["Bayonetta", [4, 180]], ["Rosalina & Luma", [3, 109]], ["Opponent 5", [0, 0]]], 
    "Ice Climbers": [["Ice Climbers", [3, 29]], ["Snake", [3, 89]], ["Banjo & Kazooie", [1, 135]], ["Richter", [2, 89]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_15 = [Tourney_1, Tourney_2, Tourney_3]

# for rank changes visual
inital_round_15_scores = round_15_scores_dict.copy()

max_percentage = 200
round_15_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_15_calculator(Tourney_List_15, max_percentage, round_15_scores_dict, loss_dict)
round_15_scores_dict = dict(sorted(round_15_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 15\n")
# print_sorted_dict(round_15_scores_dict)
round_15_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_15_results.pdf") as pdf:
    round_15_generator(round_15_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    15,
    inital_round_15_scores,
    round_15_scores_dict,
    advance_cutoff=3,
    title="Round 15: Rank 10 to 5 Rank Changes",
)

#%%
######################################################
######################## ROUND 16 ####################
######################################################

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (1.5 + (match_number)/1.7)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (1.5 + (match_number)/1.7)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_16_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.7)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.7)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/2)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_16_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 16: Rank 4 to 1 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 16: Rank 4 to 1 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 16: Rank 4 to 1 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 16: Rank 4 to 1 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 16: Rank 4 to 1 Score Density Plot", pdf)

###########################
###### Matches 4-1 ########
###########################

# 4 22.796 Piranha Plant
# 3 22.971 Zelda
# 2 23.434 Chrom
# 1 24.957 Link

Tourney_1 = {
    "Piranha Plant": [["Inkling", [1, 38]], ["Bowser", [3, 164]], ["Greninja", [2, 0]], ["Captain Falcon", [-1, 77]], ["Opponent 5", [0, 0]]], 
    "Zelda": [["Little Mac", [3, 61]], ["Lucas", [4, 101]], ["Hero", [-1, 67]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Chrom": [["Zelda", [3, 60]], ["Wolf", [2, 87]], ["Simon", [3, 63]], ["Lucario", [3, 23]], ["Opponent 5", [0, 0]]], 
    "Link": [["Sonic", [3, 63]], ["Diddy Kong", [3, 55]], ["Ike", [4, 181]], ["Ganondorf", [3, 84]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_16 = [Tourney_1, Tourney_2]

# for rank changes visual
inital_round_16_scores = round_16_scores_dict.copy()

max_percentage = 200
round_16_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_16_calculator(Tourney_List_16, max_percentage, round_16_scores_dict, loss_dict)
round_16_scores_dict = dict(sorted(round_16_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 16\n")
# print_sorted_dict(round_16_scores_dict)
round_16_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_16_results.pdf") as pdf:
    round_16_generator(round_16_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    16,
    inital_round_16_scores,
    round_16_scores_dict,
    advance_cutoff=4,
    title="Round 16: Rank 4 to 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 17 ####################
######################################################

round_17_and_18_scores_dict = round_15_scores_dict | round_16_scores_dict
round_17_and_18_scores_dict['Zelda'] = 48.23
round_17_and_18_scores_dict['Piranha Plant'] = 48.24

round_17_and_18_scores_dict = dict(sorted(round_17_and_18_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_17_and_18_scores_dict = {character:score for character, score in round_17_and_18_scores_dict.items() if score > round_17_and_18_scores_dict["Young Link"]}

round_17_and_18_scores_dict['Zelda'] = 39.73
round_17_and_18_scores_dict['Piranha Plant'] = 42.33

def round_17_and_18_renormalizer(round_17_and_18_scores_dict):
    
    for character in round_17_and_18_scores_dict:
        round_17_and_18_scores_dict[character] = round(((round_17_and_18_scores_dict[character])**(5/11))*np.log(round_17_and_18_scores_dict[character]), 3)
        
    return round_17_and_18_scores_dict

round_17_and_18_characters_dict = round_17_and_18_renormalizer(round_17_and_18_scores_dict)
round_17_scores_dict = {character:score for character,score in round_17_and_18_characters_dict.items() if score < round_17_and_18_characters_dict["Chrom"]}
round_17_scores_dict = dict(sorted(round_17_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_18_scores_dict = {character:score for character,score in round_17_and_18_characters_dict.items() if score >= round_17_and_18_characters_dict["Chrom"]}

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_17_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_17_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 17: Rank 7 to 4 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 17: Rank 7 to 4 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 17: Rank 7 to 4 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 17: Rank 7 to 3 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 17: Rank 7 to 5 Score Density Plot", pdf)

###########################
###### Matches 7-4 ########
###########################

# 7 19.632 Zelda
# 6 20.554 Piranha Plant
# 5 24.490 Banjo & Kazooie
# 4 24.497 King Dedede

Tourney_1 = {
    "Zelda": [["Wario", [3, 131]], ["Sephiroth", [3, 128]], ["Mario", [2, 0]], ["Cloud", [1, 96]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Palutena", [2, 84]], ["Donkey Kong", [3, 0]], ["Falco", [2, 0]], ["Captain Falcon", [3, 113]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Banjo & Kazooie": [["Marth", [3, 73]], ["Bowser Jr", [1, 21]], ["Hero", [3, 83]], ["Sephiroth", [2, 119]], ["Opponent 5", [0, 0]]], 
    "King Dedede": [["Olimar", [3, 94]], ["Lucario", [3, 119]], ["Villager", [1, 19]], ["Donkey Kong", [2, 114]], ["Opponent 5", [0, 0]]] 
    }

Tourney_List_17 = [Tourney_1, Tourney_2]

# for rank changes visual
inital_round_17_scores = round_17_scores_dict.copy()

max_percentage = 200
round_17_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_17_calculator(Tourney_List_17, max_percentage, round_17_scores_dict, loss_dict)
round_17_scores_dict = dict(sorted(round_17_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 17\n")
# print_sorted_dict(round_17_scores_dict)
round_17_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_17_results.pdf") as pdf:
    round_17_generator(round_17_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    17,
    inital_round_17_scores,
    round_17_scores_dict,
    advance_cutoff=2,
    title="Round 17: Rank 7 to 4 Rank Changes",
)

#%%
######################################################
######################## ROUND 18 ####################
######################################################

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_18_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
       }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_18_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 18: Rank 3 to 1 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 18: Rank 3 to 1 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 18: Rank 3 to 1 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 18: Rank 3 to 1 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 18: Rank 3 to 1 Score Density Plot", pdf)

###########################
###### Matches 3-1 ########
###########################

# 3 25.331 Chrom
# 2 26.378 Dr Mario
# 1 26.638 Link

Tourney_1 = {
     "Chrom": [["Ryu", [2, 112]], ["Zelda", [2, 75]], ["Diddy Kong", [3, 183]], ["Pokemon Trainer", [3, 90]], ["Dr Mario", [2, 34]]], 
    }

Tourney_2 = {
     "Dr Mario": [["Inkling", [1, 141]], ["King K Rool", [2, 38]], ["Greninja", [3, 134]], ["Zero Suit Samus", [3, 71]], ["Little Mac", [3, 31]]], 
    }

Tourney_3 = {
     "Link": [["Dr Mario", [3, 30]], ["Sora", [2, 23]], ["King K Rool", [3, 133]], ["Joker", [4, 195]], ["Snake", [3, 42]]], 
    }

Tourney_List_18 = [Tourney_1, Tourney_2, Tourney_3]

# for rank changes visual
inital_round_18_scores = round_18_scores_dict.copy()

max_percentage = 200
round_18_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_18_calculator(Tourney_List_18, max_percentage, round_18_scores_dict, loss_dict)
round_18_scores_dict = dict(sorted(round_18_scores_dict.items(), key=lambda item: item[1], reverse=False))
# print("\nRound 18\n")
# print_sorted_dict(round_18_scores_dict)
round_18_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_18_results.pdf") as pdf:
    round_18_generator(round_18_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    18,
    inital_round_18_scores,
    round_18_scores_dict,
    advance_cutoff=3,
    title="Round 18: Rank 3 to 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 19 ####################
######################################################

round_19_and_20_scores_dict = round_17_scores_dict | round_18_scores_dict

round_19_and_20_scores_dict = dict(sorted(round_19_and_20_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_19_and_20_scores_dict = {character:score for character, score in round_19_and_20_scores_dict.items() if score > round_19_and_20_scores_dict["Banjo & Kazooie"]}

def round_19_and_20_renormalizer(round_19_and_10_scores_dict):
    
    for character in round_19_and_20_scores_dict:
        round_19_and_20_scores_dict[character] = round(((round_19_and_20_scores_dict[character])**(5/11))*np.log(round_19_and_20_scores_dict[character]), 3)
        
    return round_19_and_20_scores_dict

round_19_and_20_characters_dict = round_19_and_20_renormalizer(round_19_and_20_scores_dict)
round_19_scores_dict = {character:score for character,score in round_19_and_20_characters_dict.items() if score < round_19_and_20_characters_dict["Link"]}
round_19_scores_dict = dict(sorted(round_19_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_20_scores_dict = {character:score for character,score in round_19_and_20_characters_dict.items() if score >= round_19_and_20_characters_dict["Link"]}

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_19_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_19_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 19: Rank 5 to 2 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 19: Rank 5 to 2 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 19: Rank 5 to 2 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 19: Rank 5 to 2 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 19: Rank 5 to 2 Score Density Plot", pdf)

###########################
###### Matches 5-2 ########
###########################

# 5 23.941 King Dedede
# 4 24.586 Piranha Plant
# 3 26.332 Chrom
# 2 26.409 Dr Mario

Tourney_1 = {
    "King Dedede": [["Roy", [2, 0]], ["Min Min", [2, 115]], ["Samus", [2, 19]], ["Pichu", [3, 61]], ["Opponent 5", [0, 0]]], 
    "Piranha Plant": [["Luigi", [3, 84]], ["Palutena", [2, 62]], ["Kirby", [1, 44]], ["Robin", [2, 42]], ["Opponent 5", [0, 0]]] 
    }

Tourney_2 = {
    "Chrom": [["Ganondorf", [1, 144]], ["ROB", [4, 198]], ["PacMan", [3, 103]], ["King Dedede", [-2, 68]], ["Opponent 5", [0, 0]]], 
    "Dr Mario": [["Snake", [3, 128]], ["Greninja", [3, 142]], ["Inkling", [1, 41]], ["Mr Game & Watch", [3, 0]], ["King Dedede", [1, 0]]] 
    }

Tourney_List_19 = [Tourney_1, Tourney_2]

# for rank changes visual
inital_round_19_scores = round_19_scores_dict.copy()

max_percentage = 200
round_19_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_19_calculator(Tourney_List_19, max_percentage, round_19_scores_dict, loss_dict)
round_19_scores_dict = dict(sorted(round_19_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 19\n")
print_sorted_dict(round_19_scores_dict)
round_19_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_19_results.pdf") as pdf:
    round_19_generator(round_19_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    19,
    inital_round_19_scores,
    round_19_scores_dict,
    advance_cutoff=2,
    title="Round 19: Rank 5 to 2 Rank Changes",
)

#%%
######################################################
######################## ROUND 20 ####################
######################################################

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 11/12 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

"""

def round_20_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 4:
                    match_won = True
                    score = multiplier*(1.5 + n/1.5)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 4:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 4:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(1.5 + n/1.5)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_20_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 20: Rank 1 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 20: Rank 1 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 20: Rank 1 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 20: Rank 1 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 20: Rank 1 Score Density Plot", pdf)

###########################
######### Match 1 #########
###########################

# 1 28.944 Link

Tourney_1 = {
    "Link": [["Young Link", [4, 142]], ["Meta Knight", [2, 0]], ["Rosalina & Luma", [3, 99]], ["Sheik", [3, 79]], ["Robin", [2, 20]]], 
    }
    
Tourney_List_20 = [Tourney_1]

# for rank changes visual
inital_round_20_scores = round_20_scores_dict.copy()

max_percentage = 200
round_20_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_20_calculator(Tourney_List_20, max_percentage, round_20_scores_dict, loss_dict)
round_20_scores_dict = dict(sorted(round_20_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 20\n")
print_sorted_dict(round_20_scores_dict)
round_20_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_20_results.pdf") as pdf:
    round_20_generator(round_20_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    20,
    inital_round_20_scores,
    round_20_scores_dict,
    advance_cutoff=1,
    title="Round 20: Rank 1 Rank Changes",
)

#%%
######################################################
######################## ROUND 21 ####################
######################################################

round_21_and_22_scores_dict = round_19_scores_dict | round_20_scores_dict

round_21_and_22_scores_dict = dict(sorted(round_21_and_22_scores_dict.items(), key=lambda item: item[1], reverse=False))
round_21_and_22_scores_dict = {character:score for character, score in round_21_and_22_scores_dict.items() if score > round_21_and_22_scores_dict["Piranha Plant"]}

def round_21_and_22_renormalizer(round_21_and_22_scores_dict):
    
    for character in round_21_and_22_scores_dict:
        round_21_and_22_scores_dict[character] = round(((round_21_and_22_scores_dict[character])**(5/11))*np.log(round_21_and_22_scores_dict[character]), 3)
        
    return round_21_and_22_scores_dict

round_21_and_22_characters_dict = round_21_and_22_renormalizer(round_21_and_22_scores_dict)
round_21_scores_dict = {character:score for character,score in round_21_and_22_characters_dict.items() if score >= round_21_and_22_characters_dict["King Dedede"]}
round_21_scores_dict = dict(sorted(round_21_scores_dict.items(), key=lambda item: item[1], reverse=False))

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 21/22 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

Special;

Top 1 Makes it On to Final 2, Two Rounds for Each Advancement, Points Kept but Renormalized
--> 1 Redo per Both Rounds

"""

def round_21_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
       }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 5:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(2.0+ n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 5:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(2.0 + n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_21_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 21: Top 3 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 21: Top 3 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 21: Top 3 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 21: Top 3 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 21: Top 3 Score Density Plot", pdf)

###########################
######### Top 3 ###########
###########################

# 3 24.754 King Dedede
# 2 26.759 Dr Mario
# 1 29.005 Link

Tourney_1 = {
    "King Dedede": [["Captain Falcon", [4, 128]], ["Inkling", [3, 97]], ["Simon", [3, 157]], ["Roy", [3, 9]], ["Ike", [3, 86]]], 
    }

Tourney_2 = {
    "Dr Mario": [["Dark Samus", [3, 69]], ["Ridley", [3, 142]], ["Sheik", [1, 11]], ["Marth", [2, 0]], ["Falco", [3, 153]]], 
    }

Tourney_3 = {
    "Link": [["Inkling", [3, 3]], ["Ryu", [1, 130]], ["Duck Hunt", [3, 17]], ["Piranha Plant", [1, 32]], ["Sephiroth", [3, 199]]], 
    }

Tourney_List_21 = [Tourney_1, Tourney_2, Tourney_3]

# for rank changes visual
inital_round_21_scores = round_21_scores_dict.copy()

max_percentage = 200
round_21_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_21_calculator(Tourney_List_21, max_percentage, round_21_scores_dict, loss_dict)
round_21_scores_dict = dict(sorted(round_21_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 21\n")
print_sorted_dict(round_21_scores_dict)
round_21_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_21_results.pdf") as pdf:
    round_21_generator(round_21_scores_dict, win_loses, pdf)

generate_round_ranking_changes_pdf(
    21,
    inital_round_21_scores,
    round_21_scores_dict,
    advance_cutoff=1,
    title="Round 21: Top 3 Rank Changes",
)

#%%
######################################################
######################## ROUND 22 ####################
######################################################

round_21_and_22_characters_dict = round_21_and_22_renormalizer(round_21_scores_dict)
round_22_scores_dict = {character:score for character,score in round_21_and_22_characters_dict.items() if score < round_21_and_22_characters_dict["King Dedede"]}
round_22_scores_dict = dict(sorted(round_22_scores_dict.items(), key=lambda item: item[1], reverse=False))

first_top_2 = {character:score for character,score in round_21_and_22_characters_dict.items() if score >= round_21_and_22_characters_dict["King Dedede"]}

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 21/22 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

Special;

Top 1 Makes it On to Final 2, Two Rounds for Each Advancement, Points Kept but Renormalized
--> 1 Redo per Both Rounds

"""

def round_22_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
       }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 5:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(2.0+ n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 5:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(2.0 + n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_22_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 22: 2nd Last Elimination - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 22: 2nd Last Elimination - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 22: 2nd Last Elimination - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 22: 2nd Last Elimination Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 22: 2nd Last Elimination Score Density Plot", pdf)

################################################
############ 2nd Last Elimination ##############
################################################

# 3 16.622 Link
# 2 16.669 Dr Mario

Tourney_1 = {
    "Dr Mario": [["Captain Falcon", [3, 8]], ["Fox", [3, 110]], ["Min Min", [2, 29]], ["Pichu", [3, 119]], ["Pyra & Mythra", [2, 98]]], 
   }

Tourney_2 = {
    "Link": [["Shulk", [3, 102]], ["Wario", [2, 28]], ["Sonic", [3, 0]], ["Dr Mario", [2, 32]], ["Isabelle", [2, 0]]], 
   }

Tourney_List_22 = [Tourney_1, Tourney_2]

# for rank changes visual
inital_round_22_scores = round_22_scores_dict.copy()

max_percentage = 200
round_22_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_22_calculator(Tourney_List_22, max_percentage, round_22_scores_dict, loss_dict)
round_22_scores_dict = dict(sorted(round_22_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 22\n")
print_sorted_dict(round_22_scores_dict)
round_22_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_22_results.pdf") as pdf:
    round_22_generator(round_22_scores_dict, win_loses, pdf)

round_22_winner = max(round_22_scores_dict, key=round_22_scores_dict.get)
round_22_eliminated = set(round_22_scores_dict) - {round_22_winner}
generate_round_ranking_changes_pdf(
    22,
    inital_round_22_scores,
    round_22_scores_dict,
    advance_cutoff=1,
    eliminated_characters=round_22_eliminated,
    title="Round 22: 2nd Last Elimination Rank Changes",
)

#%%
######################################################
######################## ROUND 23 ####################
######################################################

round_23_scores_dict = {character:score for character,score in round_22_scores_dict.items() if score >= round_22_scores_dict["Link"]}

def round_23_renormalizer(round_23_scores_dict):
    
    for character in round_23_scores_dict:
        round_23_scores_dict[character] = round(((round_23_scores_dict[character])**(5/11))*np.log(round_23_scores_dict[character]), 3)
        
    return round_23_scores_dict

round_23_characters_dict = round_23_renormalizer(round_23_scores_dict)
second_top_2 = {character:score for character,score in round_23_scores_dict.items() if score >= round_23_scores_dict["Link"]}
round_23_characters_dict = second_top_2 | {character:score for character,score in round_21_scores_dict.items() if score >= round_21_scores_dict["King Dedede"]}
round_23_scores_dict = dict(sorted(round_23_characters_dict.items(), key=lambda item: item[1], reverse=False))

"""

Refactored Scores: N^(5/11) * ln N

4 Stock Matches Going Forward - And an Unmultiplied Bonus Point if you 4 Stock Someone

Round 21/22 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 150%
Score is Multiplied by (2.0 + (match_number)/1.5)

ex) 

Bonus Match Points are Divided by Round Number

Special;

Top 1 Makes it On to Final 2, Two Rounds for Each Advancement, Points Kept but Renormalized
--> 1 Redo per Both Rounds

"""

def round_23_calculator(Tourney_List, max_percentage, character_dict, loss_dict):
    
    example_tourney = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
       }
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        if tourney == example_tourney: 
            continue
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                elif fight[1][0] > 0 and n + 1 > 5:
                    match_won = True
                    score = multiplier*(2.0 + n/1.33)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score + (1 if fight[1][0] == 4 else 0)
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 5:
                    loss_dict[fight[0]] += 1
                    match_won = False
                    score = multiplier*(2.0+ n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                    character_dict[key] += score
                    if (n + 1 == 1): 
                        win_loses["Lost Round 1"][0] += 1
                        win_loses["Lost Round 1"][1] += character_dict[key]
                        win_loses["Lost Round 1"][2].append(key)
                    if (n + 1 == 2): 
                        win_loses["Lost Round 2"][0] += 1
                        win_loses["Lost Round 2"][1] += character_dict[key]
                        win_loses["Lost Round 2"][2].append(key)
                    if (n + 1 == 3): 
                        win_loses["Lost Round 3"][0] += 1
                        win_loses["Lost Round 3"][1] += character_dict[key]
                        win_loses["Lost Round 3"][2].append(key)
                    if (n + 1 == 4): 
                        win_loses["Lost Round 4"][0] += 1
                        win_loses["Lost Round 4"][1] += character_dict[key]
                        win_loses["Lost Round 4"][2].append(key)
                elif fight[1][0] < 0 and n + 1 > 5:
                    loss_dict[fight[0]] += 1
                    score = multiplier*(2.0 + n/1.33)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Lost Round 5"][0] += 1
                        win_loses["Lost Round 5"][1] += character_dict[key]
                        win_loses["Lost Round 5"][2].append(key)
                else:
                    if n + 1 == 5: 
                        win_loses["Won Round 4"][0] += 1    
                        win_loses["Won Round 4"][1] += character_dict[key]
                        win_loses["Won Round 4"][2].append(key)
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters, loss_dict 

def round_23_generator(character_dict, win_loses, pdf):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/(1 if not total else total))/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 23: Final 2 - Win/Loss Categories", pdf)
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 23: Final 2 - Score Comparisons", pdf)
    table_generator(win_loss_characters, "Round 23: Final 2 - Character Fighting End Scenario Table", pdf)
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 23: Final 2 Score Distribution", pdf)
    distribution_generator(character_dict, "Score", "Density", "Round 23: Final 2 Elimination Score Density Plot", pdf)

##################################
############ Finale ##############
##################################

"""

Any Scoring Matrix is Irrelevant Because the Winner is the Winner
Best 2/3 Fights 

"""

# 2 34.79 King Dedede
# 1 34.918 Link

Tourney_1 = {
    "Link": [["Byleth", [2, 23]], ["Diddy Kong", [3, 89]], ["PacMan", [3, 30]], ["Pit", [4, 150]], ["Pyra & Mythra", [3, 77]]], 
   }

Tourney_2 = {
    "King Dedede": [["Terry", [2, 105]], ["Pokemon Trainer", [2, 183]], ["Sora", [1, 0]], ["Dark Pit", [4, 199]], ["Hero", [3, 16]]], 
   }

Tourney_3 = {
    "Link": [["Lucas", [2, 82]], ["King Dedede", [2, 12]], ["Ryu", [4, 103]], ["Terry", [3, 102]], ["Bayonetta", [3, 57]]], 
   }

Tourney_4 = {
    "King Dedede": [["Isabelle", [1, 50]], ["Palutena", [2, 104]], ["Wario", [2, 156]], ["Fox", [2, 18]], ["Bowser Jr", [3, 70]]], 
   }

Tourney_5 = {
    "Link": [["Steve", [2, 67]], ["Marth", [2, 0]], ["Ken", [3, 8]], ["Palutena", [2, 115]], ["Banjo & Kazooie", [1, 117]]], 
   }

Tourney_6 = {
    "King Dedede": [["Piranha Plant", [1, 72]], ["Dark Samus", [2, 199]], ["Fox", [2, 144]], ["Ryu", [2, 29]], ["Min Min", [3, 128]]], 
   }

Tourney_List_23 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6]

# for rank changes visual
inital_round_23_scores = round_23_scores_dict.copy()

max_percentage = 200
round_23_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_23_calculator(Tourney_List_23, max_percentage, round_23_scores_dict, loss_dict)
round_23_scores_dict = dict(sorted(round_23_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 23\n")
print_sorted_dict(round_23_scores_dict)
round_23_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

with PdfPages("reports/round_23_results.pdf") as pdf:
    round_23_generator(round_23_scores_dict, win_loses, pdf)

round_23_winner = max(round_23_scores_dict, key=round_23_scores_dict.get)
round_23_eliminated = set(round_23_scores_dict) - {round_23_winner}
generate_round_ranking_changes_pdf(
    23,
    inital_round_23_scores,
    round_23_scores_dict,
    advance_cutoff=1,
    eliminated_characters=round_23_eliminated,
    title="Round 23: Final 2 Rank Changes",
)

#%%   
#############################
########## RECORDS ##########
#############################

# Rounds 1 and 2 
max_percentage = 200
blank_dict = {character:[] for character in round_1_scores_dict}
Tourneys = [Tourney_List_1, Tourney_List_2]
round_1_and_2_records = records(Tourneys, blank_dict, max_percentage)
round_1_and_2_records["Score"] = pd.to_numeric(round_1_and_2_records["Score"], errors="coerce")
round_1_and_2_records["Accumulated_Sum"] = round_1_and_2_records.groupby("Character")["Score"].cumsum()
round_1_and_2_records.to_csv("records/rounds_1_and_2_records.csv", index=False)

# Round 3 Only
max_percentage = 175
blank_dict = {character:[] for character in round_3_scores_dict}
Tourneys = [Tourney_List_3]
round_3_records = records(Tourneys, blank_dict, max_percentage)
round_3_records["Score"] = pd.to_numeric(round_3_records["Score"], errors="coerce")
round_3_records["Accumulated_Sum"] = round_3_records.groupby("Character")["Score"].cumsum()
round_3_records.to_csv("records/round_3_records.csv", index=False)

# Round 4 Only
max_percentage = 175
blank_dict = {character:[] for character in round_4_scores_dict}
Tourneys = [Tourney_List_4]
round_4_records = records(Tourneys, blank_dict, max_percentage)
round_4_records["Score"] = pd.to_numeric(round_4_records["Score"], errors="coerce")
round_4_records["Accumulated_Sum"] = round_4_records.groupby("Character")["Score"].cumsum()
round_4_records.to_csv("records/round_4_records.csv", index=False)

# Round 5 Only
max_percentage = 175
blank_dict = {character:[] for character in round_5_scores_dict}
Tourneys = [Tourney_List_5]
round_5_records = records(Tourneys, blank_dict, max_percentage)
round_5_records["Score"] = pd.to_numeric(round_5_records["Score"], errors="coerce")
round_5_records["Accumulated_Sum"] = round_5_records.groupby("Character")["Score"].cumsum()
round_5_records.to_csv("records/round_5_records.csv", index=False)

# Round 6 Only
max_percentage = 175
blank_dict = {character:[] for character in round_6_scores_dict}
Tourneys = [Tourney_List_6]
round_6_records = records(Tourneys, blank_dict, max_percentage)
round_6_records["Score"] = pd.to_numeric(round_6_records["Score"], errors="coerce")
round_6_records["Accumulated_Sum"] = round_6_records.groupby("Character")["Score"].cumsum()
round_6_records.to_csv("records/round_6_records.csv", index=False)

# Round 7 Only
max_percentage = 200
blank_dict = {character:[] for character in round_7_scores_dict}
Tourneys = [Tourney_List_7]
round_7_records = records(Tourneys, blank_dict, max_percentage)
round_7_records["Score"] = pd.to_numeric(round_7_records["Score"], errors="coerce")
round_7_records["Accumulated_Sum"] = round_7_records.groupby("Character")["Score"].cumsum()
round_7_records.to_csv("records/round_7_records.csv", index=False)

# Round 8 Only
max_percentage = 200
blank_dict = {character:[] for character in round_8_scores_dict}
Tourneys = [Tourney_List_8]
round_8_records = records(Tourneys, blank_dict, max_percentage)
round_8_records["Score"] = pd.to_numeric(round_8_records["Score"], errors="coerce")
round_8_records["Accumulated_Sum"] = round_8_records.groupby("Character")["Score"].cumsum()
round_8_records.to_csv("records/round_8_records.csv", index=False)

# Round 9 Only
max_percentage = 200
blank_dict = {character:[] for character in round_9_scores_dict}
Tourneys = [Tourney_List_9]
round_9_records = records(Tourneys, blank_dict, max_percentage)
round_9_records["Score"] = pd.to_numeric(round_9_records["Score"], errors="coerce")
round_9_records["Accumulated_Sum"] = round_9_records.groupby("Character")["Score"].cumsum()
round_9_records.to_csv("records/round_9_records.csv", index=False)

# Round 10 Only
max_percentage = 200
blank_dict = {character:[] for character in round_10_scores_dict}
Tourneys = [Tourney_List_10]
round_10_records = records(Tourneys, blank_dict, max_percentage)
round_10_records["Score"] = pd.to_numeric(round_10_records["Score"], errors="coerce")
round_10_records["Accumulated_Sum"] = round_10_records.groupby("Character")["Score"].cumsum()
round_10_records.to_csv("records/round_10_records.csv", index=False)

# Round 11 Only
max_percentage = 200
blank_dict = {character:[] for character in round_11_scores_dict}
Tourneys = [Tourney_List_11]
round_11_records = records(Tourneys, blank_dict, max_percentage)
round_11_records["Score"] = pd.to_numeric(round_11_records["Score"], errors="coerce")
round_11_records["Accumulated_Sum"] = round_11_records.groupby("Character")["Score"].cumsum()
round_11_records.to_csv("records/round_11_records.csv", index=False)

# Round 12 Only
max_percentage = 200
blank_dict = {character:[] for character in round_12_scores_dict}
Tourneys = [Tourney_List_12]
round_12_records = records(Tourneys, blank_dict, max_percentage)
round_12_records["Score"] = pd.to_numeric(round_12_records["Score"], errors="coerce")
round_12_records["Accumulated_Sum"] = round_12_records.groupby("Character")["Score"].cumsum()
round_12_records.to_csv("records/round_12_records.csv", index=False)

# Round 13 Only
max_percentage = 200
blank_dict = {character:[] for character in round_13_scores_dict}
Tourneys = [Tourney_List_13]
round_13_records = records(Tourneys, blank_dict, max_percentage)
round_13_records["Score"] = pd.to_numeric(round_13_records["Score"], errors="coerce")
round_13_records["Accumulated_Sum"] = round_13_records.groupby("Character")["Score"].cumsum()
round_13_records.to_csv("records/round_13_records.csv", index=False)

# Round 14 Only
max_percentage = 200
blank_dict = {character:[] for character in round_14_scores_dict}
Tourneys = [Tourney_List_14]
round_14_records = records(Tourneys, blank_dict, max_percentage)
round_14_records["Score"] = pd.to_numeric(round_14_records["Score"], errors="coerce")
round_14_records["Accumulated_Sum"] = round_14_records.groupby("Character")["Score"].cumsum()
round_14_records.to_csv("records/round_14_records.csv", index=False)

# Round 15 Only
max_percentage = 200
blank_dict = {character:[] for character in round_15_scores_dict}
Tourneys = [Tourney_List_15]
round_15_records = records(Tourneys, blank_dict, max_percentage)
round_15_records["Score"] = pd.to_numeric(round_15_records["Score"], errors="coerce")
round_15_records["Accumulated_Sum"] = round_15_records.groupby("Character")["Score"].cumsum()
round_15_records.to_csv("records/round_15_records.csv", index=False)

# Round 16 Only
max_percentage = 200
blank_dict = {character:[] for character in round_16_scores_dict}
Tourneys = [Tourney_List_16]
round_16_records = records(Tourneys, blank_dict, max_percentage)
round_16_records["Score"] = pd.to_numeric(round_16_records["Score"], errors="coerce")
round_16_records["Accumulated_Sum"] = round_16_records.groupby("Character")["Score"].cumsum()
round_16_records.to_csv("records/round_16_records.csv", index=False)

# Round 17 Only
max_percentage = 200
blank_dict = {character:[] for character in round_17_scores_dict}
Tourneys = [Tourney_List_17]
round_17_records = records(Tourneys, blank_dict, max_percentage)
round_17_records["Score"] = pd.to_numeric(round_17_records["Score"], errors="coerce")
round_17_records["Accumulated_Sum"] = round_17_records.groupby("Character")["Score"].cumsum()
round_17_records.to_csv("records/round_17_records.csv", index=False)

# Round 18 Only
max_percentage = 200
blank_dict = {character:[] for character in round_18_scores_dict}
Tourneys = [Tourney_List_18]
round_18_records = records(Tourneys, blank_dict, max_percentage)
round_18_records["Score"] = pd.to_numeric(round_18_records["Score"], errors="coerce")
round_18_records["Accumulated_Sum"] = round_18_records.groupby("Character")["Score"].cumsum()
round_18_records.to_csv("records/round_18_records.csv", index=False)

# Round 19 Only
max_percentage = 200
blank_dict = {character:[] for character in round_19_scores_dict}
Tourneys = [Tourney_List_19]
round_19_records = records(Tourneys, blank_dict, max_percentage)
round_19_records["Score"] = pd.to_numeric(round_19_records["Score"], errors="coerce")
round_19_records["Accumulated_Sum"] = round_19_records.groupby("Character")["Score"].cumsum()
round_19_records.to_csv("records/round_19_records.csv", index=False)

# Round 20 Only
max_percentage = 200
blank_dict = {character:[] for character in round_20_scores_dict}
Tourneys = [Tourney_List_20]
round_20_records = records(Tourneys, blank_dict, max_percentage)
round_20_records["Score"] = pd.to_numeric(round_20_records["Score"], errors="coerce")
round_20_records["Accumulated_Sum"] = round_20_records.groupby("Character")["Score"].cumsum()
round_20_records.to_csv("records/round_20_records.csv", index=False)

# Round 21 Only
max_percentage = 200
blank_dict = {character:[] for character in round_21_scores_dict}
Tourneys = [Tourney_List_21]
round_21_records = records(Tourneys, blank_dict, max_percentage)
round_21_records["Score"] = pd.to_numeric(round_21_records["Score"], errors="coerce")
round_21_records["Accumulated_Sum"] = round_21_records.groupby("Character")["Score"].cumsum()
round_21_records.to_csv("records/round_21_records.csv", index=False)

# Round 22 Only
max_percentage = 200
blank_dict = {character:[] for character in round_22_scores_dict}
Tourneys = [Tourney_List_22]
round_22_records = records(Tourneys, blank_dict, max_percentage)
round_22_records["Score"] = pd.to_numeric(round_22_records["Score"], errors="coerce")
round_22_records["Accumulated_Sum"] = round_22_records.groupby("Character")["Score"].cumsum()
round_22_records.to_csv("records/round_22_records.csv", index=False)

# Round 23 Only
max_percentage = 200
blank_dict = {character:[] for character in round_23_scores_dict}
Tourneys = [Tourney_List_23]
round_23_records = records(Tourneys, blank_dict, max_percentage)
round_23_records["Score"] = pd.to_numeric(round_23_records["Score"], errors="coerce")
round_23_records["Accumulated_Sum"] = round_23_records.groupby("Character")["Score"].cumsum()
round_23_records.to_csv("records/round_23_records.csv", index=False)

# All Rounds to 8
max_percentage = 200
blank_dict = {character:[] for character in round_1_scores_dict}
Tourneys = [Tourney_List_1, Tourney_List_2, Tourney_List_3, Tourney_List_4, 
            Tourney_List_5, Tourney_List_6, Tourney_List_7, Tourney_List_8]
round_all_records = records(Tourneys, blank_dict, max_percentage)
round_all_records["Score"] = pd.to_numeric(round_all_records["Score"], errors="coerce")
round_all_records["Accumulated_Sum"] = round_all_records.groupby("Character")["Score"].cumsum()
round_all_records.to_csv("records/all_records_to_8.csv", index=False)


#############################
#### OVERALL RANKING PROFILE
#############################

def generate_overall_ranking_profile(round_scores_by_round, output_pdf_path, output_csv_path=None, max_rows_per_page=35):
    """Generate an overall ranking profile for all characters.

    Ranks are computed per-round within that round's participant set (rank 1 = best).
    Characters missing from a round are treated as NaN for that round.
    """

    rounds = sorted(round_scores_by_round.keys())
    all_characters = sorted({c for scores in round_scores_by_round.values() for c in scores.keys()})

    ranks_by_round = {r: _ranks_best_from_scores(round_scores_by_round[r]) for r in rounds}

    rows = []
    for character in all_characters:
        present_rounds = [r for r in rounds if character in ranks_by_round[r]]
        if not present_rounds:
            continue

        per_round_ranks = [ranks_by_round[r][character] for r in present_rounds]
        last_round = max(present_rounds)
        last_rank = ranks_by_round[last_round][character]

        ranks_series = pd.Series(per_round_ranks, dtype="float")
        rows.append(
            {
                "Character": character,
                "Appearances": int(len(present_rounds)),
                "LastRound": int(last_round),
                "LastRank": int(last_rank),
                "BestRank": int(ranks_series.min()),
                "WorstRank": int(ranks_series.max()),
                "MeanRank": float(ranks_series.mean()),
                "StdRank": float(ranks_series.std(ddof=0) if len(ranks_series) > 1 else 0.0),
            }
        )

    profile_df = pd.DataFrame(rows)
    if profile_df.empty:
        return

    profile_df = profile_df.sort_values(["LastRound", "LastRank", "BestRank"], ascending=[False, True, True])

    if output_csv_path:
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        profile_df.to_csv(output_csv_path, index=False)

    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    with PdfPages(output_pdf_path) as pdf:
        # Summary page
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")

        winner = None
        try:
            winner = round_23_winner
        except Exception:
            pass

        last_round_counts = profile_df["LastRound"].value_counts().sort_index()
        summary_lines = [
            "Overall Ranking Profile",
            f"Total characters: {len(profile_df)}",
            f"Champion: {winner}" if winner else "Champion: (unknown)",
            "",
            "Last-round reached (count):",
        ]
        summary_lines += [f"  Round {r}: {int(cnt)}" for r, cnt in last_round_counts.items()]
        ax.text(0.01, 0.99, "\n".join(summary_lines), va="top", ha="left", fontsize=12)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Table pages
        columns = ["Character", "Appearances", "LastRound", "LastRank", "BestRank", "WorstRank", "MeanRank", "StdRank"]
        formatted = profile_df.copy()
        formatted["MeanRank"] = formatted["MeanRank"].map(lambda x: f"{x:.2f}")
        formatted["StdRank"] = formatted["StdRank"].map(lambda x: f"{x:.2f}")

        for start in range(0, len(formatted), max_rows_per_page):
            chunk = formatted.iloc[start : start + max_rows_per_page][columns]
            fig_height = 1.0 + 0.28 * len(chunk)
            fig, ax = plt.subplots(figsize=(11, max(8.5, fig_height)))
            ax.axis("off")
            table = ax.table(
                cellText=chunk.values,
                colLabels=chunk.columns,
                cellLoc="center",
                loc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1.0, 1.2)
            ax.set_title(
                f"Overall Ranking Profile (rows {start + 1}–{min(start + max_rows_per_page, len(formatted))} of {len(formatted)})",
                fontsize=12,
                pad=12,
            )
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


overall_round_scores = {
    1: round_1_scores_dict,
    2: round_2_scores_dict,
    3: round_3_scores_dict,
    4: round_4_scores_dict,
    5: round_5_scores_dict,
    6: round_6_scores_dict,
    7: round_7_scores_dict,
    8: round_8_scores_dict,
    9: round_9_scores_dict,
    10: round_10_scores_dict,
    11: round_11_scores_dict,
    12: round_12_scores_dict,
    13: round_13_scores_dict,
    14: round_14_scores_dict,
    15: round_15_scores_dict,
    16: round_16_scores_dict,
    17: round_17_scores_dict,
    18: round_18_scores_dict,
    19: round_19_scores_dict,
    20: round_20_scores_dict,
    21: round_21_scores_dict,
    22: round_22_scores_dict,
    23: round_23_scores_dict,
}

'''