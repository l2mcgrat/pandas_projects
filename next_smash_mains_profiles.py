# next_smash_mains_profiles.py
# Character profile builder and per-character visual report generator.

from __future__ import annotations

import math
import warnings
warnings.filterwarnings("ignore")

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

ROOT          = Path(__file__).resolve().parent
RECORDS_DIR   = ROOT / "records" / "next_smash_mains_records"
REPORTS_DIR   = ROOT / "reports" / "next_smash_mains_reports"
PROFILES_DIR  = REPORTS_DIR / "character_profiles"
IMAGES_DIR    = ROOT / "character_images"
MODELS_DIR    = ROOT / "character_models"
MATCHUP_PATH  = ROOT / "matchup_chart.csv"

MATCHUP_DF = pd.read_csv(MATCHUP_PATH) if MATCHUP_PATH.exists() else pd.DataFrame()

# ──────────────────────────────────────────────────────────────────────────────
# Round label maps  (mirrored from discovery.py)
# ──────────────────────────────────────────────────────────────────────────────

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
}
ROUND_DISPLAY: dict[int, str] = {
    1: "Round 1",
    2: "Round 2",
    3: "Elim 1",
    4: "Round 3",
    5: "Elim 2",
    6: "Round 4",
    7: "Elim 3",
    8: "Round 5",
    9: "Elim 4",
    10: "Round 6",
}
LABEL_TO_ROUND: dict[str, int] = {v: k for k, v in ROUND_LABEL.items()}

ELIMINATION_RANK_OFFSETS: dict[str, int] = {
    "elimination_1": 64,
    "elimination_2": 56,
    "elimination_3": 48,
    "elimination_4": 40,
}

# Colour assigned to each round for charts
ROUND_COLORS: dict[str, str] = {
    "round_1":       "#4e79a7",
    "round_2":       "#f28e2b",
    "elimination_1": "#e15759",
    "round_3":       "#76b7b2",
    "elimination_2": "#59a14f",
    "round_4":       "#edc948",
    "elimination_3": "#b07aa1",
    "round_5":       "#ff9da7",
    "elimination_4": "#9c755f",
    "round_6":       "#bab0ac",
}


def _elimination_rank_box_characters(label: str, fallback: list[str]) -> list[str]:
    """Characters in the fixed rank box for an active elimination round."""
    attr_by_label = {
        "elimination_1": "ELIMINATION_1_MATCHES",
        "elimination_2": "ELIMINATION_2_MATCHES",
        "elimination_3": "ELIMINATION_3_MATCHES",
        "elimination_4": "ELIMINATION_4_MATCHES",
    }
    attr = attr_by_label.get(label)
    if attr is None:
        return fallback
    try:
        import next_smash_mains_discovery as discovery
        matches = getattr(discovery, attr)
    except Exception:
        return fallback
    return list(matches.keys()) if isinstance(matches, dict) else fallback

# ──────────────────────────────────────────────────────────────────────────────
# Matchup helpers
# ──────────────────────────────────────────────────────────────────────────────

def _matchup_value(matchup_df: pd.DataFrame, character: str, opponent: str) -> float:
    """Raw matchup advantage of character over opponent (positive = character favoured)."""
    if matchup_df.empty or "Character" not in matchup_df.columns:
        return 0.0
    char_key = character.lower()
    opp_key  = opponent.lower()
    row = matchup_df[matchup_df["Character"].astype(str).str.lower() == char_key]
    if row.empty or opp_key not in matchup_df.columns:
        return 0.0
    try:
        return float(row[opp_key].iloc[0])
    except Exception:
        return 0.0


def _expected_stock_diff(matchup_val: float) -> float:
    """
    Expected stock differential derived from the matchup chart value.
    matchup_val ≈ -3..+3 → expected stock diff on the same scale.
    Positive means the character is expected to win stocks.
    """
    return matchup_val          # 1:1 mapping; +1 matchup advantage → +1 expected stock


# ──────────────────────────────────────────────────────────────────────────────
# CharacterProfile dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CharacterProfile:
    """Aggregated match statistics and tournament trajectory for one character."""

    name: str

    # Each element is a row-dict from a records CSV with two extra keys:
    #   'round_label'          (str)   e.g. "round_2"
    #   'expected_stock_diff'  (float) derived from matchup chart
    matches: list[dict] = field(default_factory=list)

    # Rank of this character after each round they appeared in
    ranks_by_round: dict[str, int] = field(default_factory=dict)

    # Official final score/rank from overall_ranking_profile.csv, when available.
    official_current_score: float | None = None
    official_current_rank: int | None = None

    # Effective (adjusted) score at the end of each round, accounting for
    # inter-round score reductions.  {round_label: adjusted_score}
    scores_by_round: dict[str, float] = field(default_factory=dict)

    # (transition_label, score_before_reduction, score_after_reduction)
    rescoring_events: list[tuple[str, float, float]] = field(default_factory=list)
    adjusted_rescoring_events: list[tuple[str, float, float]] = field(default_factory=list)

    # ── scalar stats ───────────────────────────────────────────────────────

    @property
    def current_score(self) -> float:
        if self.official_current_score is not None:
            return self.official_current_score
        return self.matches[-1]["Accumulated_Sum"] if self.matches else 0.0

    @property
    def current_rank(self) -> int:
        if self.official_current_rank is not None:
            return self.official_current_rank
        return list(self.ranks_by_round.values())[-1] if self.ranks_by_round else 0

    @property
    def average_rank(self) -> float:
        ranks = list(self.ranks_by_round.values())
        return sum(ranks) / len(ranks) if ranks else 0.0

    @property
    def win_rate(self) -> float:
        wins = sum(1 for m in self.matches if m["Win"])
        return wins / len(self.matches) if self.matches else 0.0

    @property
    def avg_points_per_match(self) -> float:
        """Mean score contribution per real match."""
        return sum(m["Score"] for m in self.matches) / len(self.matches) if self.matches else 0.0

    @property
    def avg_raw_performance(self) -> float:
        """
        Mean of (stock_diff + percentage / 200) per match.
        This is a multiplier-free measure of raw output — each stock is worth 1.0
        and the percentage component is expressed as a fraction of 200.
        """
        if not self.matches:
            return 0.0
        return sum(m["Stock Diff"] + m["Percentage"] / 200.0 for m in self.matches) / len(self.matches)

    # ── per-match dicts ────────────────────────────────────────────────────

    @property
    def scores_per_match(self) -> dict[str, float]:
        """Score contribution from each match.  Key: '{round_label} M{n} vs {opponent}'."""
        return {
            f"{m['round_label']} M{m['Round']} vs {m['Opponent']}": m["Score"]
            for m in self.matches
        }

    @property
    def multipliers_per_match(self) -> dict[str, float]:
        """Matchup multiplier applied to each match.  Same key scheme."""
        return {
            f"{m['round_label']} M{m['Round']} vs {m['Opponent']}": m["Matchup"]
            for m in self.matches
        }

    @property
    def scores_without_multiplier(self) -> dict[str, float]:
        """
        What each match score would have been with a neutral (1.0) matchup multiplier.
        Computed as score / matchup_multiplier.
        """
        result = {}
        for m in self.matches:
            key  = f"{m['round_label']} M{m['Round']} vs {m['Opponent']}"
            mult = m["Matchup"]
            result[key] = round(m["Score"] / mult, 3) if mult and abs(mult) > 1e-9 else m["Score"]
        return result

    # ── rescoring ──────────────────────────────────────────────────────────

    @property
    def num_rescoring_events(self) -> int:
        return len(self.rescoring_events)

    @property
    def lost_score_per_rescoring(self) -> dict[str, float]:
        """Score lost in each inter-round reduction.  Positive = score removed."""
        return {label: round(before - after, 3) for label, before, after in self.rescoring_events}

    @property
    def adjusted_lost_score_per_rescoring(self) -> dict[str, float]:
        """Multiplier-adjusted score lost in each inter-round reduction."""
        return {label: round(before - after, 3) for label, before, after in self.adjusted_rescoring_events}

    # ── expected vs. actual stock diff ────────────────────────────────────

    @property
    def expected_vs_actual(self) -> list[dict]:
        """
        Per-match comparison of actual stock diff vs. matchup-chart-predicted stock diff.
        'overperformance' > 0 means the character did better than the chart predicted.
        """
        return [
            {
                "round":                 m["round_label"],
                "match":                 m["Round"],
                "opponent":              m["Opponent"],
                "actual_stock_diff":     m["Stock Diff"],
                "expected_stock_diff":   m.get("expected_stock_diff", 0.0),
                "overperformance":       m["Stock Diff"] - m.get("expected_stock_diff", 0.0),
                "score":                 m["Score"],
                "multiplier":            m["Matchup"],
            }
            for m in self.matches
        ]

    @property
    def avg_overperformance(self) -> float:
        evs = self.expected_vs_actual
        return sum(e["overperformance"] for e in evs) / len(evs) if evs else 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Profile builder
# ──────────────────────────────────────────────────────────────────────────────

def build_profiles(
    records_dir: Path,
    matchup_df: pd.DataFrame,
) -> dict[str, CharacterProfile]:
    """
    Read all *_records.csv files and assemble a CharacterProfile for every character.

    rescoring_events are detected by comparing a character's exit score from round N
    against their entry score in round N+1.  If exit > entry the difference was removed
    by a score-reduction step between the two rounds.
    """
    # ── load all records ───────────────────────────────────────────────────
    files = sorted(
        records_dir.glob("*_records.csv"),
        key=lambda f: LABEL_TO_ROUND.get(f.stem.removesuffix("_records"), 99),
    )

    all_matches: dict[str, list[dict]]         = defaultdict(list)   # char -> match rows
    exit_scores:  dict[str, dict[str, float]]  = {}                  # label -> {char: exit}
    entry_scores: dict[str, dict[str, float]]  = {}                  # label -> {char: entry}
    adjusted_exit_scores:  dict[str, dict[str, float]] = {}          # label -> {char: adjusted exit}
    adjusted_entry_scores: dict[str, dict[str, float]] = {}          # label -> {char: adjusted entry}

    for path in files:
        label = path.stem.removesuffix("_records")
        if label not in LABEL_TO_ROUND:
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue

        round_exit:  dict[str, float] = {}
        round_entry: dict[str, float] = {}
        adjusted_round_exit: dict[str, float] = {}
        adjusted_round_entry: dict[str, float] = {}

        for character, grp in df.groupby("Character", sort=False):
            char = str(character)
            grp  = grp.sort_values("Round")
            first = grp.iloc[0]
            last  = grp.iloc[-1]
            round_exit[char]  = float(last["Accumulated_Sum"])
            round_entry[char] = float(first["Accumulated_Sum"]) - float(first["Score"])
            first_adjusted_score = float(first.get("Multiplier Adjusted Score", first["Score"]))
            first_adjusted_sum = float(first.get("Multiplier Adjusted Accumulated Sum", first["Accumulated_Sum"]))
            last_adjusted_sum = float(last.get("Multiplier Adjusted Accumulated Sum", last["Accumulated_Sum"]))
            adjusted_round_exit[char] = last_adjusted_sum
            adjusted_round_entry[char] = first_adjusted_sum - first_adjusted_score

            for _, row in grp.iterrows():
                d = row.to_dict()
                d["round_label"] = label
                if "Multiplier Adjusted Score" not in d:
                    total_multiplier = d.get("Total Multiplier", d.get("Matchup", 1.0))
                    d["Multiplier Adjusted Score"] = d["Score"] / total_multiplier if total_multiplier else d["Score"]
                mu_val = _matchup_value(matchup_df, char, str(row["Opponent"]))
                d["expected_stock_diff"] = _expected_stock_diff(mu_val)
                all_matches[char].append(d)

        exit_scores[label]  = round_exit
        entry_scores[label] = round_entry
        adjusted_exit_scores[label] = adjusted_round_exit
        adjusted_entry_scores[label] = adjusted_round_entry

    # ── sort each character's matches by round then match number ──────────
    for char in all_matches:
        all_matches[char].sort(
            key=lambda m: (LABEL_TO_ROUND.get(m["round_label"], 99), int(m["Round"]))
        )

    # ── ranks after each round (active round boxes only) ──────────────────
    # Round 1 establishes the initial global ranking.  After that, only the
    # characters active in a round can trade rank slots; everyone else keeps
    # their prior rank.  Elimination rounds use fixed tournament boxes
    # (e.g. Elim 3 = 49..72), while regular rounds reuse the active
    # characters' pre-round rank slots.
    ordered_labels_ranked = sorted(exit_scores.keys(), key=lambda l: LABEL_TO_ROUND.get(l, 99))
    _all_pool = set(c for ex in exit_scores.values() for c in ex)

    official_scores: dict[str, float] = {}
    official_ranks: dict[str, int] = {}
    overall_path = records_dir / "overall_ranking_profile.csv"
    if overall_path.exists():
        overall_df = pd.read_csv(overall_path)
        if {"Character", "Score"}.issubset(overall_df.columns):
            for _, row in overall_df.iterrows():
                character = str(row["Character"])
                official_scores[character] = float(row["Score"])
                if "Rank" in overall_df.columns:
                    official_ranks[character] = int(row["Rank"])

    # Build per-character effective score at every round boundary
    effective: dict[str, dict[str, float]] = {}
    for char in _all_pool:
        played = sorted(
            [l for l in ordered_labels_ranked if char in exit_scores.get(l, {})],
            key=lambda l: LABEL_TO_ROUND.get(l, 99),
        )
        if not played:
            continue
        cs: dict[str, float] = {}
        for label in ordered_labels_ranked:
            lo = LABEL_TO_ROUND.get(label, 99)
            if char in exit_scores.get(label, {}):
                cs[label] = exit_scores[label][char]
            else:
                prev_played = [l for l in played if LABEL_TO_ROUND.get(l, 99) < lo]
                if not prev_played:
                    continue
                nxt_played = [l for l in played if LABEL_TO_ROUND.get(l, 99) > lo]
                if nxt_played:
                    ne = entry_scores.get(nxt_played[0], {}).get(char)
                    cs[label] = ne if ne is not None else exit_scores[prev_played[-1]][char]
                else:
                    cs[label] = exit_scores[prev_played[-1]][char]
        effective[char] = cs

    current_ranks: dict[str, int] = {}
    ranks_by_round_all: dict[str, dict[str, int]] = {}
    for label in ordered_labels_ranked:
        snap = {c: effective[c][label] for c in effective if label in effective[c]}
        if not current_ranks:
            ranked = sorted(snap.items(), key=lambda x: x[1], reverse=True)
            current_ranks = {c: i + 1 for i, (c, _) in enumerate(ranked)}
        elif label not in ELIMINATION_RANK_OFFSETS:
            participants = [c for c in exit_scores.get(label, {}) if c in current_ranks]
            if not participants:
                ranks_by_round_all[label] = dict(current_ranks)
                continue
            pre_slots = sorted(current_ranks[c] for c in participants)
            by_score = sorted(
                participants,
                key=lambda c: exit_scores[label].get(c, float("-inf")),
                reverse=True,
            )
            new_ranks = dict(current_ranks)
            for i, character in enumerate(by_score):
                new_ranks[character] = pre_slots[i]
            current_ranks = new_ranks
        else:
            offset = ELIMINATION_RANK_OFFSETS[label]
            fallback_box = list(exit_scores.get(label, {}).keys())
            box_characters = _elimination_rank_box_characters(label, fallback_box) or fallback_box

            def _box_score(character: str) -> float:
                if label == ordered_labels_ranked[-1] and character in official_scores:
                    return official_scores[character]
                if character in exit_scores.get(label, {}):
                    return exit_scores[label][character]
                return snap.get(character, float("-inf"))

            previous_rank = max(current_ranks.values(), default=offset) + 1
            sorted_box = sorted(
                box_characters,
                key=lambda c: (-_box_score(c), current_ranks.get(c, previous_rank)),
            )
            new_ranks = dict(current_ranks)
            for i, character in enumerate(sorted_box):
                new_ranks[character] = offset + i + 1
            current_ranks = new_ranks

        ranks_by_round_all[label] = dict(current_ranks)

    # ── rescoring events ───────────────────────────────────────────────────
    # Walk each character's OWN played rounds in order and compare that
    # character's exit score to its entry score in the next round IT played.
    # Using consecutive global labels misses characters who skip elimination
    # rounds (e.g. round_2 exit vs round_3 entry when elim_1 is in-between).
    ordered_labels = sorted(exit_scores.keys(), key=lambda l: LABEL_TO_ROUND.get(l, 99))
    rescoring_by_char: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    adjusted_rescoring_by_char: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    all_chars_seen = set(c for ex in exit_scores.values() for c in ex)
    for char in all_chars_seen:
        played = [l for l in ordered_labels if char in exit_scores.get(l, {})]
        for i in range(len(played) - 1):
            prev_lbl   = played[i]
            next_lbl   = played[i + 1]
            prev_score = exit_scores[prev_lbl][char]
            next_score = entry_scores.get(next_lbl, {}).get(char)
            if next_score is not None and prev_score - next_score > 0.005:
                transition = f"{prev_lbl} -> {next_lbl}"
                rescoring_by_char[char].append((transition, round(prev_score, 3), round(next_score, 3)))
            adjusted_prev_score = adjusted_exit_scores.get(prev_lbl, {}).get(char)
            adjusted_next_score = adjusted_entry_scores.get(next_lbl, {}).get(char)
            if adjusted_prev_score is not None and adjusted_next_score is not None and adjusted_prev_score - adjusted_next_score > 0.005:
                transition = f"{prev_lbl} -> {next_lbl}"
                adjusted_rescoring_by_char[char].append((transition, round(adjusted_prev_score, 3), round(adjusted_next_score, 3)))

    # ── assemble profiles ──────────────────────────────────────────────────
    all_chars = set(all_matches.keys()) | {c for exits in exit_scores.values() for c in exits}
    profiles: dict[str, CharacterProfile] = {}
    for char in sorted(all_chars):
        r_by_round = {
            lbl: ranks_by_round_all[lbl][char]
            for lbl in ranks_by_round_all
            if char in ranks_by_round_all[lbl] and char in exit_scores.get(lbl, {})
        }
        r_by_round = dict(sorted(r_by_round.items(), key=lambda x: LABEL_TO_ROUND.get(x[0], 99)))
        char_effective = dict(effective.get(char, {}))
        # Override the last round's effective score with the official score so
        # carry-forward values for characters who were reduced but didn't play
        # the final round reflect the real post-reduction score.
        if char in official_scores and char_effective:
            last_label = max(char_effective, key=lambda lbl: LABEL_TO_ROUND.get(lbl, 0))
            char_effective[last_label] = official_scores[char]
        profiles[char] = CharacterProfile(
            name=char,
            matches=all_matches.get(char, []),
            ranks_by_round=r_by_round,
            scores_by_round=char_effective,
            official_current_score=official_scores.get(char),
            official_current_rank=official_ranks.get(char),
            rescoring_events=rescoring_by_char.get(char, []),
            adjusted_rescoring_events=adjusted_rescoring_by_char.get(char, []),
        )

    return profiles


# ──────────────────────────────────────────────────────────────────────────────
# Difficulty KPI
# ──────────────────────────────────────────────────────────────────────────────

def _matchup_lookup(matchup_df: pd.DataFrame, character: str, opponent: str) -> float:
    """Return the matchup chart value for *character* vs *opponent* (0 if missing)."""
    if matchup_df.empty:
        return 0.0
    char_lower = character.lower()
    opp_lower = opponent.lower()
    row = matchup_df[matchup_df["Character"].str.lower() == char_lower]
    if row.empty:
        return 0.0
    matching_cols = [c for c in matchup_df.columns if c.lower() == opp_lower]
    if not matching_cols:
        return 0.0
    return float(row[matching_cols[0]].values[0])


def compute_difficulty(
    profiles: dict[str, "CharacterProfile"],
    matchup_df: pd.DataFrame,
    w: float = 0.5,
) -> dict[str, float]:
    """Compute average schedule difficulty for each character.

    Per-match difficulty = 10 * alpha * (1 / r^w) * (1 + matchup / 10)
      r     = opponent's fighter rank (current_rank)
      matchup = matchup chart value (character perspective)
      alpha = normalization constant so  integral_1^N  alpha / r^w  dr = 1

    Returns {character_name: average_difficulty}.
    """
    N = len(profiles)
    if N < 2:
        return {}

    # Normalization: integral from 1 to N of 1/r^w dr
    if abs(w - 1.0) > 1e-6:
        integral = (N ** (1 - w) - 1) / (1 - w)
    else:
        import math
        integral = math.log(N)
    alpha = 1.0 / integral if integral > 0 else 1.0

    # Build opponent rank map
    opp_rank: dict[str, int] = {p.name: p.current_rank for p in profiles.values()}

    result: dict[str, float] = {}
    for char_name, profile in profiles.items():
        if not profile.matches:
            result[char_name] = 0.0
            continue
        total = 0.0
        count = 0
        for match in profile.matches:
            opponent = str(match.get("Opponent", ""))
            r = opp_rank.get(opponent, N)  # default to last rank if unknown
            if r < 1:
                r = 1
            matchup = _matchup_lookup(matchup_df, char_name, opponent)
            difficulty = 1000.0 * alpha * (1.0 / r ** w) * (1.0 + matchup / 10.0)
            total += difficulty
            count += 1
        result[char_name] = round(total / count, 2) if count > 0 else 0.0

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Image helper
# ──────────────────────────────────────────────────────────────────────────────

def _find_image(name: str, images_dir: Path) -> Path | None:
    if not images_dir.exists():
        return None
    candidates = [
        name,
        name.lower().replace(" & ", "_and_").replace(" ", "_"),
        name.lower().replace(" ", "_"),
        name.lower().replace(" ", "-"),
        name.lower(),
    ]
    extensions = [".png", ".jpg", ".jpeg", ".webp"]
    for stem in candidates:
        for ext in extensions:
            p = images_dir / f"{stem}{ext}"
            if p.exists():
                return p
    # case-insensitive fallback
    name_norm = name.lower().replace(" ", "_").replace("&", "and").replace(".", "")
    for f in images_dir.iterdir():
        f_norm = f.stem.lower().replace(" ", "_").replace("&", "and").replace(".", "")
        if f_norm == name_norm and f.suffix.lower() in extensions:
            return f
    return None


def _find_model_image(name: str, models_dir: Path) -> Path | None:
    """Locate a Fighter Display image in character_models/, e.g. Mario_Fighter_Display.png."""
    if not models_dir.exists():
        return None
    extensions = [".png", ".jpg", ".jpeg", ".webp"]
    safe = name.replace(" & ", "_and_").replace(" ", "_").replace(".", "")
    candidates = [
        f"{safe}_Fighter_Display",
        f"{safe}_Display",
        f"{name}_Fighter_Display",
        f"{name}_Display",
        safe,
        name,
    ]
    for stem in candidates:
        for ext in extensions:
            p = models_dir / f"{stem}{ext}"
            if p.exists():
                return p
    # case-insensitive scan
    name_norm = name.lower().replace(" ", "_").replace("&", "and").replace(".", "")
    for f in models_dir.iterdir():
        stem_norm = (
            f.stem.lower()
            .replace(" ", "_").replace("&", "and").replace(".", "")
            .replace("_fighter_display", "")
            .replace("_display", "")
        )
        if stem_norm == name_norm and f.suffix.lower() in extensions:
            return f
    return None


def _find_rank_neighbors(
    profile: "CharacterProfile",
    all_profiles: "dict[str, CharacterProfile]",
    delta: int = 10,
) -> "tuple[CharacterProfile | None, CharacterProfile | None]":
    """Return the profiles ranked delta positions above and below the current character."""
    target_above = profile.current_rank - delta
    target_below = profile.current_rank + delta
    above = next((p for p in all_profiles.values() if p.current_rank == target_above), None)
    below = next((p for p in all_profiles.values() if p.current_rank == target_below), None)
    return above, below


# ──────────────────────────────────────────────────────────────────────────────
# Profile visual
# ──────────────────────────────────────────────────────────────────────────────

def generate_character_profile_pdf(
    profile: CharacterProfile,
    output_path: Path,
    all_profiles: "dict[str, CharacterProfile]",
    models_dir: Path = MODELS_DIR,
    images_dir: Path = IMAGES_DIR,
) -> None:
    """
    Dark fighter-card style one-page PDF:
      · Right panel: character model image with a left-edge dark gradient fade
      · Top-left: name + three big hype callout numbers (rank / win-rate / score)
      · Middle: clustered score-per-match bars (current char + rank±10 neighbours)
      · Bottom-left: rank trajectory with glow + neighbour lines + best-jump callout
      · Bottom-right: expected vs actual stock diff with embedded definition note
    """
    # ─── colour theme ───────────────────────────────────────────────────────
    BG     = "#0c1220"   # outer dark background
    PANEL  = "#141f30"   # chart / stat panel fill
    PANEL2 = "#192338"   # secondary panel / legend fill
    CT     = "#e8eaf0"   # primary text (light)
    CS     = "#8a9bb5"   # secondary text (muted)
    CYAN   = "#00c8ff"   # current-character accent
    GOLD   = "#ffd369"   # rank-above neighbour / best-match highlight
    GREEN  = "#4ade80"   # positive / win
    RED    = "#f87171"   # negative / rank-below neighbour

    # derive a character-specific accent from their last played round's colour
    last_round   = list(profile.ranks_by_round.keys())[-1] if profile.ranks_by_round else "round_1"
    char_accent  = ROUND_COLORS.get(last_round, CYAN)

    wins  = sum(1 for m in profile.matches if m["Win"])
    total = len(profile.matches)

    fig = plt.figure(figsize=(20, 13), dpi=180)
    fig.patch.set_facecolor(BG)

    # ─── character model — full-bleed background for chars that have one ─
    model_path = _find_model_image(profile.name, models_dir)
    if model_path:
        # Full-figure background layer (added first so everything else renders on top)
        ax_model = fig.add_axes([0.0, 0.0, 1.0, 0.975])
        ax_model.set_facecolor("white")
        ax_model.axis("off")
        try:
            img_data = mpimg.imread(str(model_path))
            ax_model.imshow(img_data, aspect="equal", extent=[0, 1, 0, 1],
                            zorder=1, interpolation="lanczos")
        except Exception:
            pass
        # Dark gradient overlay: opaque on content-left, fades out toward character-right
        ov = np.zeros((100, 200, 4), dtype=np.float32)
        ov[:, :, 0] = int(BG[1:3], 16) / 255
        ov[:, :, 1] = int(BG[3:5], 16) / 255
        ov[:, :, 2] = int(BG[5:7], 16) / 255
        ov[:, :, 3] = np.concatenate([
            np.full(120, 0.88),           # left 60 %: near-solid dark
            np.linspace(0.88, 0.22, 80),  # right 40 %: fade to let character show
        ])[np.newaxis, :]
        ax_model.imshow(ov, aspect="auto", extent=[0, 1, 0, 1], zorder=2)
    else:
        ax_model = fig.add_axes([0.57, 0.0, 0.45, 0.975])
        ax_model.set_facecolor(BG)
        ax_model.axis("off")
        ax_model.text(0.5, 0.5, profile.name[0],
                      ha="center", va="center", fontsize=80,
                      fontweight="bold", color="#253550",
                      transform=ax_model.transAxes)

    # ─── top accent stripe (added after model so it stays on top) ─────────
    ax_stripe = fig.add_axes([0.0, 0.975, 1.0, 0.025])
    ax_stripe.set_facecolor(char_accent)
    ax_stripe.axis("off")

    # ─── banner (name + hype callouts) ────────────────────────────────────
    ax_ban = fig.add_axes([0.01, 0.818, 0.550, 0.150])
    ax_ban.set_facecolor(PANEL)
    ax_ban.patch.set_alpha(0.72)
    ax_ban.axis("off")
    # left accent stripe inside banner
    ax_ban.add_patch(plt.Rectangle((0, 0), 0.007, 1.0, transform=ax_ban.transAxes,
                                   color=char_accent, zorder=5, clip_on=False))

    name_text = ax_ban.text(0.025, 0.88, profile.name,
                            transform=ax_ban.transAxes, fontsize=30, fontweight="bold",
                            color=CT, va="top")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    name_right = ax_ban.transAxes.inverted().transform(
        (name_text.get_window_extent(renderer=renderer).x1, 0)
    )[0]
    hype_start = min(max(0.40, name_right + 0.055), 0.56)
    hype_gap = min(0.205, (0.92 - hype_start) / 2)

    # three hype callout numbers
    hype = [
        (f"#{profile.current_rank}",             "RANK",        GOLD),
        (f"{profile.win_rate:.0%}",               "WIN RATE",    GREEN),
        (f"{profile.current_score:.2f}",          "TOTAL SCORE", CYAN),
    ]
    for i, (val, lbl, col) in enumerate(hype):
        xp = hype_start + i * hype_gap
        if i > 0:
            divider_x = xp - hype_gap / 2
            ax_ban.plot([divider_x, divider_x], [0.2, 0.92],
                        color="#253550", linewidth=1,
                        transform=ax_ban.transAxes, clip_on=False)
        ax_ban.text(xp, 0.90, val,
                    transform=ax_ban.transAxes, fontsize=24,
                    fontweight="bold", color=col, va="top", ha="center")
        ax_ban.text(xp, 0.50, lbl,
                    transform=ax_ban.transAxes, fontsize=7.5,
                    color=CS, va="top", ha="center", fontweight="bold")

    # ─── KPI tile strip ────────────────────────────────────────────────────
    reductions = profile.num_rescoring_events
    total_lost = sum(profile.lost_score_per_rescoring.values())
    adjusted_total_lost = sum(profile.adjusted_lost_score_per_rescoring.values())

    kpi_items = [
        ("AVG RANK",    f"{profile.average_rank:.1f}",
         CS),
        ("WIN / LOSS",  f"{wins} / {total - wins}",
         CT),
        ("PTS / MATCH", f"{profile.avg_points_per_match:.3f}",
         CYAN),
        ("RAW PERF",    f"{profile.avg_raw_performance:.3f}",
         GOLD),
        ("OVERPERF",    f"{profile.avg_overperformance:+.3f}",
         GREEN if profile.avg_overperformance >= 0 else RED),
        ("SCORE LOST",  f"{total_lost:.3f}",
         RED if total_lost > 0.01 else CS),
        ("ADJ LOST",    f"{adjusted_total_lost:.3f}",
         RED if adjusted_total_lost > 0.01 else CS),
    ]

    nk = len(kpi_items)
    ax_kpi = fig.add_axes([0.01, 0.750, 0.550, 0.062])
    ax_kpi.set_facecolor("none")
    ax_kpi.patch.set_alpha(0)
    ax_kpi.axis("off")
    ax_kpi.set_xlim(0, nk)
    ax_kpi.set_ylim(0, 1)
    for i, (lbl, val, col) in enumerate(kpi_items):
        ax_kpi.add_patch(FancyBboxPatch(
            (i + 0.04, 0.06), 0.92, 0.88,
            boxstyle="round,pad=0.015",
            linewidth=0.8, edgecolor="#253550",
            facecolor=PANEL2, alpha=0.60,
        ))
        ax_kpi.text(i + 0.50, 0.68, val,
                    ha="center", va="center", fontsize=11,
                    fontweight="bold", color=col)
        ax_kpi.text(i + 0.50, 0.20, lbl,
                    ha="center", va="center", fontsize=6.5,
                    color=CS, fontweight="bold", alpha=0.85)

    # ─── rank neighbours (±5 and ±10) ───────────────────────────────────
    nb_above,  nb_below  = _find_rank_neighbors(profile, all_profiles, 10)
    nb_above5, nb_below5 = _find_rank_neighbors(profile, all_profiles,  5)

    def _score_map(p):
        """Dict of (round_label, match_num) -> score for quick lookup."""
        return {(m["round_label"], int(m["Round"])): m["Score"] for m in p.matches} if p else {}

    above_map = _score_map(nb_above)
    below_map = _score_map(nb_below)

    def _style_ax(ax):
        # Semi-transparent panel: lets the character model bleed through the charts
        r, g, b = int(PANEL[1:3], 16)/255, int(PANEL[3:5], 16)/255, int(PANEL[5:7], 16)/255
        ax.set_facecolor((r, g, b, 0.38))
        for sp in ax.spines.values():
            sp.set_color("#253550")
        ax.tick_params(colors=CS, labelsize=7)
        ax.yaxis.label.set_color(CS)
        ax.grid(axis="y", alpha=0.12, color="white", zorder=0)

    # ─── score per match — clustered ──────────────────────────────────────
    ax_sc = fig.add_axes([0.01, 0.435, 0.906, 0.290])
    _style_ax(ax_sc)
    ax_sc.axhline(0, color="#253550", linewidth=0.9, zorder=1)

    if profile.matches:
        n  = len(profile.matches)
        bw = 0.24
        x  = np.arange(n)

        has_a = nb_above is not None
        has_b = nb_below is not None
        if has_a and has_b:
            off_a, off_c, off_b = -bw, 0.0, bw
        elif has_a:
            off_a, off_c, off_b = -bw / 2, bw / 2, None
        elif has_b:
            off_a, off_c, off_b = None, -bw / 2, bw / 2
        else:
            off_a, off_c, off_b = None, 0.0, None

        if has_a:
            a_vals = [above_map.get((m["round_label"], int(m["Round"])), 0) for m in profile.matches]
            ax_sc.bar(x + off_a, a_vals, width=bw, color=GOLD, alpha=0.50, zorder=2,
                      label=f"{nb_above.name}  (#{nb_above.current_rank})  +10 rank")
        if has_b:
            b_vals = [below_map.get((m["round_label"], int(m["Round"])), 0) for m in profile.matches]
            ax_sc.bar(x + off_b, b_vals, width=bw, color=RED, alpha=0.50, zorder=2,
                      label=f"{nb_below.name}  (#{nb_below.current_rank})  -10 rank")

        cur_scores = [m["Score"] for m in profile.matches]
        cur_bars   = ax_sc.bar(x + off_c, cur_scores, width=bw,
                               color=CYAN, alpha=0.90, zorder=3,
                               label=f"{profile.name}  (#{profile.current_rank})")

        # value labels + star on personal best
        best_idx = int(np.argmax(cur_scores)) if cur_scores else -1
        for i, (bar, h) in enumerate(zip(cur_bars, cur_scores)):
            if abs(h) > 0.01:
                is_best = (i == best_idx)
                ax_sc.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 0.05 if h >= 0 else h - 0.12,
                    ("\u2605 " if is_best else "") + f"{h:.2f}",
                    ha="center", va="bottom" if h >= 0 else "top",
                    fontsize=6 if not is_best else 7,
                    fontweight="bold" if is_best else "normal",
                    color=GOLD if is_best else CT, zorder=5,
                )

        # round-colour strip along x-axis bottom
        for i, m in enumerate(profile.matches):
            rc = ROUND_COLORS.get(m["round_label"], "#999")
            ax_sc.axvspan(i - 0.43, i + 0.43, ymin=0, ymax=0.022,
                          color=rc, alpha=0.75, zorder=0)

        xlbls = [
            f"{ROUND_DISPLAY.get(LABEL_TO_ROUND.get(m['round_label'], 0), m['round_label'])}\n"
            f"M{m['Round']}\n{m['Opponent'][:7]}"
            for m in profile.matches
        ]
        ax_sc.set_xticks(x)
        ax_sc.set_xticklabels(xlbls, fontsize=6.5, color=CS)
        ax_sc.set_ylabel("Score", fontsize=9)
        ax_sc.set_title("Score Per Match", fontsize=11, color=CT, pad=5, fontweight="bold")
        leg = ax_sc.legend(fontsize=8, loc="upper left",
                           facecolor=PANEL2, edgecolor="#253550",
                           labelcolor=CT, framealpha=0.92)
    else:
        ax_sc.text(0.5, 0.5, "No matches", ha="center", va="center",
                   color=CS, transform=ax_sc.transAxes)

    # ─── rank trajectory ──────────────────────────────────────────────────
    ax_rk = fig.add_axes([0.01, 0.04, 0.43, 0.365])
    _style_ax(ax_rk)
    ax_rk.grid(alpha=0.12, color="white")

    if profile.ranks_by_round:
        rounds_list = list(profile.ranks_by_round.keys())
        rlabels     = [ROUND_DISPLAY.get(LABEL_TO_ROUND.get(l, 0), l) for l in rounds_list]
        rvals       = list(profile.ranks_by_round.values())
        xi          = list(range(len(rlabels)))

        # gradient fill under the current line
        ax_rk.fill_between(xi, rvals, max(rvals) + 6, alpha=0.07, color=CYAN)

        # glow + main line
        ax_rk.plot(xi, rvals, color=CYAN, linewidth=8, alpha=0.14, zorder=2)
        ax_rk.plot(xi, rvals, "o-", color=CYAN, linewidth=2.5, markersize=7,
                   zorder=3, label=f"{profile.name}  #{profile.current_rank}")

        for idx, v in enumerate(rvals):
            ax_rk.text(idx, v - 1.8, str(v),
                       ha="center", va="bottom", fontsize=8,
                       color=CT, fontweight="bold")

        # best rank-improvement arrow annotation
        if len(rvals) >= 2:
            diffs     = [rvals[i] - rvals[i + 1] for i in range(len(rvals) - 1)]
            best_jump = max(diffs)
            if best_jump >= 4:
                ji = diffs.index(best_jump)
                ax_rk.annotate(
                    f"+{int(best_jump)} ranks",
                    xy=(ji + 1, rvals[ji + 1]),
                    xytext=(ji + 1 + 0.25, rvals[ji + 1] - 5),
                    fontsize=8, color=GREEN, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
                )

        # neighbour lines — ±5 closer/brighter, ±10 more muted
        GOLD5 = "#f5d060"   # lighter gold for ±5 above
        RED5  = "#ff7070"   # lighter red  for ±5 below
        _neighbors = [
            (nb_above,  GOLD,  "--", "s", 1.5, 0.60, "+10 rank"),
            (nb_above5, GOLD5, "-.", "D", 1.8, 0.80,  "+5 rank"),
            (nb_below5, RED5,  "-.", "v", 1.8, 0.80,  "-5 rank"),
            (nb_below,  RED,   ":",  "^", 1.5, 0.60, "-10 rank"),
        ]
        for nb, col, sty, mkr, lw, alpha, tag in _neighbors:
            if nb is not None:
                shared  = [l for l in rounds_list if l in nb.ranks_by_round]
                s_xi    = [rounds_list.index(l) for l in shared]
                s_yvals = [nb.ranks_by_round[l]  for l in shared]
                if s_xi:
                    ax_rk.plot(s_xi, s_yvals, linestyle=sty, color=col,
                               linewidth=lw, marker=mkr, markersize=5,
                               alpha=alpha,
                               label=f"{nb.name}  #{nb.current_rank}  ({tag})")

        ax_rk.set_xticks(range(len(rlabels)))
        ax_rk.set_xticklabels(rlabels, fontsize=8, rotation=20, ha="right", color=CS)
        ax_rk.invert_yaxis()
        ax_rk.set_ylabel("Rank  (lower = better)", fontsize=9)
        ax_rk.set_title("Rank Trajectory", fontsize=11, color=CT, pad=5, fontweight="bold")
        ax_rk.legend(fontsize=8, facecolor=PANEL2, edgecolor="#253550",
                     labelcolor=CT, framealpha=0.92)
    else:
        ax_rk.text(0.5, 0.5, "No rank data", ha="center", va="center",
                   color=CS, transform=ax_rk.transAxes)

    # ─── round score totals — clustered against rank ±5 ──────────────────
    ax_ev = fig.add_axes([0.485, 0.04, 0.43, 0.365])
    _style_ax(ax_ev)
    ax_ev.axhline(0, color="#253550", linewidth=0.9)

    def _round_score_totals(p):
        totals: dict[str, float] = defaultdict(float)
        if p is None:
            return totals
        for match in p.matches:
            totals[match["round_label"]] += float(match["Score"])
        return totals

    cur_round_totals = _round_score_totals(profile)
    above5_round_totals = _round_score_totals(nb_above5)
    below5_round_totals = _round_score_totals(nb_below5)

    round_labels = [
        label for label in profile.ranks_by_round
        if label in cur_round_totals or label in above5_round_totals or label in below5_round_totals
    ]
    if round_labels:
        xe = np.arange(len(round_labels))
        bw = 0.23
        has_a5 = nb_above5 is not None
        has_b5 = nb_below5 is not None
        if has_a5 and has_b5:
            off_a5, off_c, off_b5 = -bw, 0.0, bw
        elif has_a5:
            off_a5, off_c, off_b5 = -bw / 2, bw / 2, None
        elif has_b5:
            off_a5, off_c, off_b5 = None, -bw / 2, bw / 2
        else:
            off_a5, off_c, off_b5 = None, 0.0, None

        if has_a5:
            vals = [above5_round_totals.get(label, 0.0) for label in round_labels]
            ax_ev.bar(xe + off_a5, vals, width=bw, color=GOLD, alpha=0.56, zorder=2,
                      label=f"{nb_above5.name}  (#{nb_above5.current_rank})  +5 rank")
        cur_vals = [cur_round_totals.get(label, 0.0) for label in round_labels]
        ax_ev.bar(xe + off_c, cur_vals, width=bw, color=CYAN, alpha=0.90, zorder=3,
                  label=f"{profile.name}  (#{profile.current_rank})")
        if has_b5:
            vals = [below5_round_totals.get(label, 0.0) for label in round_labels]
            ax_ev.bar(xe + off_b5, vals, width=bw, color=RED, alpha=0.56, zorder=2,
                      label=f"{nb_below5.name}  (#{nb_below5.current_rank})  -5 rank")

        for i, value in enumerate(cur_vals):
            if abs(value) > 0.01:
                ax_ev.text(
                    i + off_c,
                    value + 0.05 if value >= 0 else value - 0.12,
                    f"{value:.2f}",
                    ha="center", va="bottom" if value >= 0 else "top",
                    fontsize=7, color=CT, fontweight="bold", zorder=5,
                )

        for i, label in enumerate(round_labels):
            rc = ROUND_COLORS.get(label, "#999")
            ax_ev.axvspan(i - 0.43, i + 0.43, ymin=0, ymax=0.025,
                          color=rc, alpha=0.75, zorder=0)

        xlbls_ev = [ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label) for label in round_labels]
        ax_ev.set_xticks(xe)
        ax_ev.set_xticklabels(xlbls_ev, fontsize=8, rotation=20, ha="right", color=CS)
        ax_ev.set_ylabel("Round Score Total", fontsize=9)
        ax_ev.set_title("Round Score Totals vs. Rank ±5", fontsize=11,
                        color=CT, pad=5, fontweight="bold")
        ax_ev.legend(fontsize=7.5, facecolor=PANEL2, edgecolor="#253550",
                     labelcolor=CT, framealpha=0.92, loc="upper left")
    else:
        ax_ev.text(0.5, 0.5, "No match data", ha="center", va="center",
                   color=CS, transform=ax_ev.transAxes)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path) as pdf:
        pdf.savefig(fig, bbox_inches="tight", facecolor=BG, dpi=180)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# Opponent analysis  (NT = no-total-multiplier base score)
# ──────────────────────────────────────────────────────────────────────────────

OPPONENT_PROFILES_DIR: Path = REPORTS_DIR / "opponent_profiles"
_STANDARD_CAP: float = 175.0


@dataclass
class OpponentProfile:
    """Stats for a character when it appeared as the *opponent* in recorded matches."""

    name: str
    # Each element:
    #   round_label, round_num, against (the active character), opp_stock_diff,
    #   percentage, nt_score (no-total-multiplier base), win (bool)
    appearances: list[dict] = field(default_factory=list)

    # ── scalar stats ───────────────────────────────────────────────────────

    @property
    def total_appearances(self) -> int:
        return len(self.appearances)

    @property
    def wins(self) -> int:
        return sum(1 for a in self.appearances if a["win"])

    @property
    def losses(self) -> int:
        return self.total_appearances - self.wins

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_appearances if self.total_appearances else 0.0

    @property
    def total_nt_score(self) -> float:
        return round(sum(a["nt_score"] for a in self.appearances), 3)

    @property
    def avg_nt_score(self) -> float:
        return round(self.total_nt_score / self.total_appearances, 3) if self.total_appearances else 0.0

    @property
    def nt_score_by_round(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for a in self.appearances:
            lbl = a["round_label"]
            totals[lbl] = totals.get(lbl, 0.0) + a["nt_score"]
        return {
            lbl: round(s, 3)
            for lbl, s in sorted(totals.items(), key=lambda x: LABEL_TO_ROUND.get(x[0], 99))
        }


def _nt_base_score(stock_diff: int, percentage: float, cap: float = _STANDARD_CAP) -> float:
    """Base scoring formula with no stage/matchup/late-match multipliers."""
    if stock_diff > 0:
        return float(stock_diff) + max(0.0, cap - percentage) / cap
    if stock_diff < 0:
        return 1.0 + float(stock_diff) + min(1.0, percentage / cap)
    return 0.0


def build_opponent_profiles(records_dir: Path) -> dict[str, "OpponentProfile"]:
    """
    Scan all *_records.csv files and build an OpponentProfile for each character
    by flipping the perspective of every row.

    NT score = base formula only (no stage / matchup / late-match multipliers).
    """
    files = sorted(
        records_dir.glob("*_records.csv"),
        key=lambda f: LABEL_TO_ROUND.get(f.stem.removesuffix("_records"), 99),
    )
    raw: dict[str, list[dict]] = defaultdict(list)

    for path in files:
        label = path.stem.removesuffix("_records")
        if label not in LABEL_TO_ROUND:
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        for _, row in df.iterrows():
            opp_name      = str(row["Opponent"])
            char_sd       = int(row["Stock Diff"])
            pct           = float(row["Percentage"])
            opp_sd        = -char_sd
            raw[opp_name].append({
                "round_label": label,
                "round_num":   int(row["Round"]),
                "against":     str(row["Character"]),
                "opp_stock_diff": opp_sd,
                "percentage":  pct,
                "nt_score":    round(_nt_base_score(opp_sd, pct), 3),
                "win":         opp_sd > 0,
            })

    result: dict[str, OpponentProfile] = {}
    for name, apps in sorted(raw.items()):
        sorted_apps = sorted(
            apps,
            key=lambda a: (LABEL_TO_ROUND.get(a["round_label"], 99), a["round_num"]),
        )
        result[name] = OpponentProfile(name=name, appearances=sorted_apps)
    return result


def generate_opponent_profile_pdf(
    profile: OpponentProfile,
    output_path: Path,
    models_dir: Path = MODELS_DIR,
) -> None:
    """Dark single-page opponent-card PDF."""
    BG     = "#0c1220"
    PANEL  = "#141f30"
    PANEL2 = "#192338"
    CT     = "#e8eaf0"
    CS     = "#8a9bb5"
    CYAN   = "#00c8ff"
    GOLD   = "#ffd369"
    GREEN  = "#4ade80"
    RED    = "#f87171"
    PURPLE = "#c084fc"

    fig = plt.figure(figsize=(20, 13), dpi=180)
    fig.patch.set_facecolor(BG)

    # ─── model background ────────────────────────────────────────────────
    model_path = _find_model_image(profile.name, models_dir)
    ax_model   = fig.add_axes([0.0, 0.0, 1.0, 0.975])
    ax_model.set_facecolor(BG)
    ax_model.axis("off")
    if model_path:
        try:
            img_data = mpimg.imread(str(model_path))
            ax_model.imshow(img_data, aspect="equal", extent=[0, 1, 0, 1],
                            zorder=1, interpolation="lanczos")
        except Exception:
            pass
        ov = np.zeros((100, 200, 4), dtype=np.float32)
        ov[:, :, 0] = int(BG[1:3], 16) / 255
        ov[:, :, 1] = int(BG[3:5], 16) / 255
        ov[:, :, 2] = int(BG[5:7], 16) / 255
        ov[:, :, 3] = np.concatenate([
            np.full(120, 0.90),
            np.linspace(0.90, 0.24, 80),
        ])[np.newaxis, :]
        ax_model.imshow(ov, aspect="auto", extent=[0, 1, 0, 1], zorder=2)
    else:
        ax_model.text(0.5, 0.5, profile.name[0], ha="center", va="center",
                      fontsize=80, fontweight="bold", color="#253550",
                      transform=ax_model.transAxes)

    # ─── accent stripe ────────────────────────────────────────────────────
    ax_stripe = fig.add_axes([0.0, 0.975, 1.0, 0.025])
    ax_stripe.set_facecolor(PURPLE)
    ax_stripe.axis("off")

    # ─── banner ───────────────────────────────────────────────────────────
    ax_ban = fig.add_axes([0.01, 0.830, 0.550, 0.138])
    ax_ban.set_facecolor(PANEL)
    ax_ban.patch.set_alpha(0.72)
    ax_ban.axis("off")
    ax_ban.add_patch(plt.Rectangle((0, 0), 0.007, 1.0, transform=ax_ban.transAxes,
                                   color=PURPLE, zorder=5, clip_on=False))
    ax_ban.text(0.025, 0.92, profile.name,
                transform=ax_ban.transAxes, fontsize=30, fontweight="bold",
                color=CT, va="top")
    ax_ban.text(0.025, 0.42, "As Opponent  ·  NT Scores",
                transform=ax_ban.transAxes, fontsize=11,
                color=PURPLE, va="top", fontstyle="italic")

    hype = [
        (f"{profile.total_appearances}", "APPEARANCES", GOLD),
        (f"{profile.wins} / {profile.losses}", "W / L",     GREEN),
        (f"{profile.win_rate:.0%}",           "WIN RATE",  CYAN),
        (f"{profile.total_nt_score:.2f}",     "TOTAL NT",  PURPLE),
        (f"{profile.avg_nt_score:.3f}",       "AVG NT",    CT),
    ]
    hype_start = 0.37
    hype_gap   = min(0.12, (0.92 - hype_start) / (len(hype) - 1 + 0.5))
    for i, (val, lbl, col) in enumerate(hype):
        xp = hype_start + i * hype_gap
        if i > 0:
            ax_ban.plot([xp - hype_gap / 2, xp - hype_gap / 2], [0.18, 0.95],
                        color="#253550", linewidth=1,
                        transform=ax_ban.transAxes, clip_on=False)
        ax_ban.text(xp, 0.90, val,
                    transform=ax_ban.transAxes, fontsize=18,
                    fontweight="bold", color=col, va="top", ha="center")
        ax_ban.text(xp, 0.44, lbl,
                    transform=ax_ban.transAxes, fontsize=6.5,
                    color=CS, va="top", ha="center", fontweight="bold")

    def _style_ax(ax: plt.Axes) -> None:
        r, g, b = int(PANEL[1:3], 16) / 255, int(PANEL[3:5], 16) / 255, int(PANEL[5:7], 16) / 255
        ax.set_facecolor((r, g, b, 0.38))
        for sp in ax.spines.values():
            sp.set_color("#253550")
        ax.tick_params(colors=CS, labelsize=7)
        ax.yaxis.label.set_color(CS)
        ax.grid(axis="y", alpha=0.12, color="white", zorder=0)

    # ─── NT score per appearance ──────────────────────────────────────────
    ax_sc = fig.add_axes([0.01, 0.430, 0.900, 0.370])
    _style_ax(ax_sc)
    ax_sc.axhline(0, color="#253550", linewidth=0.9, zorder=1)

    if profile.appearances:
        n      = len(profile.appearances)
        nt_vals = [a["nt_score"] for a in profile.appearances]
        x      = np.arange(n)
        colors = [
            (GREEN if a["win"] else RED)
            for a in profile.appearances
        ]
        bars = ax_sc.bar(x, nt_vals, width=0.65, color=colors, alpha=0.82, zorder=2)
        for bar, val in zip(bars, nt_vals):
            if abs(val) > 0.01:
                ax_sc.text(
                    bar.get_x() + bar.get_width() / 2,
                    val + 0.04 if val >= 0 else val - 0.10,
                    f"{val:.2f}",
                    ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=5.5, color=CT, zorder=5,
                )
        # round-colour strip
        for i, a in enumerate(profile.appearances):
            rc = ROUND_COLORS.get(a["round_label"], "#999")
            ax_sc.axvspan(i - 0.38, i + 0.38, ymin=0, ymax=0.022,
                          color=rc, alpha=0.75, zorder=0)
        xlbls = [
            f"{ROUND_DISPLAY.get(LABEL_TO_ROUND.get(a['round_label'], 0), a['round_label'])}\n"
            f"M{a['round_num']}\nvs {a['against'][:7]}"
            for a in profile.appearances
        ]
        ax_sc.set_xticks(x)
        ax_sc.set_xticklabels(xlbls, fontsize=6, color=CS)
        ax_sc.set_ylabel("NT Score", fontsize=9)
        ax_sc.set_title("NT Score Per Appearance as Opponent  (green = opponent won)",
                        fontsize=11, color=CT, pad=5, fontweight="bold")
    else:
        ax_sc.text(0.5, 0.5, "No opponent appearances", ha="center", va="center",
                   color=CS, transform=ax_sc.transAxes)

    # ─── NT score by round ────────────────────────────────────────────────
    ax_rnd = fig.add_axes([0.01, 0.04, 0.43, 0.355])
    _style_ax(ax_rnd)

    rnd_totals = profile.nt_score_by_round
    if rnd_totals:
        rlbls  = [ROUND_DISPLAY.get(LABEL_TO_ROUND.get(l, 0), l) for l in rnd_totals]
        rvals  = list(rnd_totals.values())
        xr     = np.arange(len(rlbls))
        rcols  = [ROUND_COLORS.get(l, "#999") for l in rnd_totals]
        rbars  = ax_rnd.bar(xr, rvals, color=rcols, alpha=0.80, width=0.65, zorder=2)
        for bar, val in zip(rbars, rvals):
            ax_rnd.text(bar.get_x() + bar.get_width() / 2, val + 0.10,
                        f"{val:.2f}", ha="center", va="bottom", fontsize=8,
                        fontweight="bold", color=CT, zorder=5)
        ax_rnd.set_xticks(xr)
        ax_rnd.set_xticklabels(rlbls, fontsize=8, color=CS)
        ax_rnd.set_ylabel("Total NT Score", fontsize=9)
        ax_rnd.set_title("NT Score by Round", fontsize=11, color=CT, pad=5,
                          fontweight="bold")

    # ─── appearances table ────────────────────────────────────────────────
    ax_tbl = fig.add_axes([0.485, 0.04, 0.43, 0.355])
    ax_tbl.set_facecolor((int(PANEL[1:3], 16) / 255, int(PANEL[3:5], 16) / 255,
                          int(PANEL[5:7], 16) / 255, 0.38))
    for sp in ax_tbl.spines.values():
        sp.set_color("#253550")
    ax_tbl.axis("off")
    ax_tbl.set_title("Appearances Log", fontsize=11, color=CT, pad=5, fontweight="bold")

    if profile.appearances:
        tbl_data = [
            [
                ROUND_DISPLAY.get(LABEL_TO_ROUND.get(a["round_label"], 0), a["round_label"]),
                f"M{a['round_num']}",
                a["against"],
                "W" if a["win"] else "L",
                f"{a['nt_score']:.2f}",
            ]
            for a in profile.appearances
        ]
        col_headers = ["Round", "#", "vs Character", "W/L", "NT"]
        tbl = ax_tbl.table(
            cellText=tbl_data,
            colLabels=col_headers,
            cellLoc="center",
            loc="upper center",
            bbox=[0.02, 0.0, 0.96, 0.97],
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7.5)
        for (row_idx, col_idx), cell in tbl.get_celld().items():
            cell.set_facecolor(PANEL2 if row_idx == 0 else BG)
            cell.set_edgecolor("#253550")
            cell.set_text_props(color=GOLD if row_idx == 0 else CT)
        for row_idx, a in enumerate(profile.appearances, start=1):
            wl_cell = tbl[(row_idx, 3)]
            wl_cell.set_text_props(color=GREEN if a["win"] else RED, fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path) as pdf:
        pdf.savefig(fig, bbox_inches="tight", facecolor=BG, dpi=180)
    plt.close(fig)


def generate_all_opponent_profiles(
    records_dir: Path  = RECORDS_DIR,
    profiles_dir: Path = OPPONENT_PROFILES_DIR,
    models_dir: Path   = MODELS_DIR,
) -> dict[str, "OpponentProfile"]:
    """Build all OpponentProfile objects and generate one PDF per character."""
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profiles = build_opponent_profiles(records_dir)
    print(f"Built opponent profiles for {len(profiles)} characters.")
    for name, profile in profiles.items():
        safe_name = name.replace(" & ", "_and_").replace(" ", "_").replace("/", "_")
        out_path  = profiles_dir / f"{safe_name}_opponent_profile.pdf"
        generate_opponent_profile_pdf(profile, out_path, models_dir)
    print(f"Opponent profile PDFs saved to: {profiles_dir}")
    return profiles


# ──────────────────────────────────────────────────────────────────────────────
# Batch generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_all_profiles(
    records_dir: Path  = RECORDS_DIR,
    profiles_dir: Path = PROFILES_DIR,
    images_dir: Path   = IMAGES_DIR,
    models_dir: Path   = MODELS_DIR,
    matchup_df: pd.DataFrame = MATCHUP_DF,
) -> dict[str, CharacterProfile]:
    """Build all CharacterProfile objects and generate one PDF per character."""
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profiles = build_profiles(records_dir, matchup_df)
    print(f"Built profiles for {len(profiles)} characters.")
    for name, profile in profiles.items():
        safe_name = name.replace(" & ", "_and_").replace(" ", "_").replace("/", "_")
        out_path  = profiles_dir / f"{safe_name}_profile.pdf"
        generate_character_profile_pdf(profile, out_path, profiles, models_dir, images_dir)
    print(f"Profile PDFs saved to: {profiles_dir}")
    return profiles


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    generate_all_profiles()


if __name__ == "__main__":
    main()
