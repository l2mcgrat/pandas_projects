from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
RECORDS_DIR = ROOT / "records" / "next_smash_mains_records"
OUTPUT_DIR = ROOT / "reports" / "next_smash_mains_analysis_output"
TABLES_DIR = OUTPUT_DIR / "tables"
CHARTS_DIR = OUTPUT_DIR / "charts"
ROUND_TABLES_DIR = TABLES_DIR / "per_round"
ROUND_CHARTS_DIR = CHARTS_DIR / "per_round"
ROUND_SUMMARY_PDF = OUTPUT_DIR / "next_smash_mains_rounds_summary.pdf"

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


def sorted_round_files(records_dir: Path) -> list[Path]:
    round_files = [
        path
        for path in records_dir.glob("*_records.csv")
        if path.stem.removesuffix("_records") in LABEL_TO_ROUND
    ]

    def round_key(path: Path) -> int:
        label = path.stem.removesuffix("_records")
        return LABEL_TO_ROUND.get(label, 0)

    return sorted(round_files, key=round_key)


def round_number_from_path(path: Path) -> int:
    label = path.stem.removesuffix("_records")
    return LABEL_TO_ROUND.get(label, 0)


def prepare_round_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = {"Character", "Stock Diff", "Percentage", "Score"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in round records: {sorted(missing)}")

    working_df = df.copy()
    # Build reliable win/loss columns from stock differential.
    working_df["Win_Calc"] = (working_df["Stock Diff"] > 0).astype(int)
    working_df["Loss_Calc"] = (working_df["Stock Diff"] < 0).astype(int)
    return working_df


def load_round_records(records_dir: Path) -> pd.DataFrame:
    files = sorted_round_files(records_dir)
    if not files:
        raise FileNotFoundError(f"No round record files found in {records_dir}")

    frames = [prepare_round_dataframe(pd.read_csv(path)) for path in files]
    combined = pd.concat(frames, ignore_index=True)
    return combined


def load_round_records_by_round(records_dir: Path) -> dict[int, pd.DataFrame]:
    files = sorted_round_files(records_dir)
    if not files:
        raise FileNotFoundError(f"No round record files found in {records_dir}")

    per_round: dict[int, pd.DataFrame] = {}
    for path in files:
        round_number = round_number_from_path(path)
        per_round[round_number] = prepare_round_dataframe(pd.read_csv(path))
    return per_round


def compute_character_summary(records_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        records_df.groupby("Character", as_index=False)
        .agg(
            Fights=("Character", "size"),
            Avg_Stock_Diff=("Stock Diff", "mean"),
            Avg_Damage=("Percentage", "mean"),
            Wins=("Win_Calc", "sum"),
            Losses=("Loss_Calc", "sum"),
            Total_Score=("Score", "sum"),
        )
    )
    summary["Win_Rate"] = (summary["Wins"] / summary["Fights"]).fillna(0)
    return summary.sort_values("Total_Score", ascending=False).reset_index(drop=True)


def compute_total_win_loss(records_df: pd.DataFrame) -> pd.DataFrame:
    wins = int(records_df["Win_Calc"].sum())
    losses = int(records_df["Loss_Calc"].sum())
    total = wins + losses
    return pd.DataFrame(
        {
            "Total_Wins": [wins],
            "Total_Losses": [losses],
            "Win_Percentage": [wins / total if total else 0.0],
            "Loss_Percentage": [losses / total if total else 0.0],
        }
    )


def compute_round_score_profile(records_df: pd.DataFrame) -> pd.DataFrame:
    score_profile = (
        records_df.groupby("Character", as_index=False)
        .agg(Score=("Score", "sum"))
        .sort_values("Score", ascending=False)
        .reset_index(drop=True)
    )
    return score_profile


def load_score_profile(records_dir: Path) -> pd.DataFrame:
    profile_path = records_dir / "overall_ranking_profile.csv"
    if not profile_path.exists():
        raise FileNotFoundError(f"Missing score profile file: {profile_path}")

    scores = pd.read_csv(profile_path)
    required = {"Character", "Score"}
    missing = required - set(scores.columns)
    if missing:
        raise ValueError(f"Missing required columns in score profile: {sorted(missing)}")

    return scores.sort_values("Score", ascending=False).reset_index(drop=True)


def apply_current_rank_order(summary_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    rank_order = {character: idx for idx, character in enumerate(scores_df["Character"].tolist())}
    ordered = summary_df.copy()
    ordered["_rank_order"] = ordered["Character"].map(rank_order).fillna(len(rank_order) + 1000).astype(int)
    ordered = ordered.sort_values(["_rank_order", "Character"], ascending=[True, True]).reset_index(drop=True)
    return ordered.drop(columns=["_rank_order"])


def save_tables(character_summary: pd.DataFrame, total_summary: pd.DataFrame) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    character_summary.to_csv(TABLES_DIR / "average_stock_damage_per_fight_by_character.csv", index=False)
    character_summary[["Character", "Wins", "Losses", "Win_Rate", "Fights"]].to_csv(
        TABLES_DIR / "wins_vs_losses_by_character.csv", index=False
    )
    total_summary.to_csv(TABLES_DIR / "total_wins_vs_losses.csv", index=False)


def save_round_tables(round_number: int, character_summary: pd.DataFrame, total_summary: pd.DataFrame) -> None:
    label = ROUND_LABEL.get(round_number, f"round_{round_number}")
    round_dir = ROUND_TABLES_DIR / label
    round_dir.mkdir(parents=True, exist_ok=True)
    character_summary.to_csv(round_dir / "average_stock_damage_per_fight_by_character.csv", index=False)
    character_summary[["Character", "Wins", "Losses", "Win_Rate", "Fights"]].to_csv(
        round_dir / "wins_vs_losses_by_character.csv", index=False
    )
    total_summary.to_csv(round_dir / "total_wins_vs_losses.csv", index=False)


def plot_avg_stock_and_damage(character_summary: pd.DataFrame, output_path: Path, title: str, pdf: PdfPages | None = None) -> None:
    sns.set_theme(style="whitegrid")
    n = len(character_summary)
    fig_width = max(24, n * 0.45)

    fig, ax1 = plt.subplots(figsize=(fig_width, 11), dpi=220)
    x = range(n)

    bars = ax1.bar(x, character_summary["Avg_Stock_Diff"], color="#2A9D8F", alpha=0.85, label="Avg Stock Diff")
    ax1.set_ylabel("Average Stock Differential", fontsize=12)
    ax1.set_xlabel("Character", fontsize=12)

    ax2 = ax1.twinx()
    line = ax2.plot(x, character_summary["Avg_Damage"], color="#E76F51", linewidth=2.5, marker="o", markersize=4, label="Avg Damage")
    ax2.set_ylabel("Average Damage (%)", fontsize=12)

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(character_summary["Character"], rotation=78, ha="right", fontsize=8)

    plt.title(title, fontsize=16, pad=14)

    handles = [bars, line[0]]
    labels = ["Avg Stock Diff", "Avg Damage"]
    ax1.legend(handles, labels, loc="upper right")

    plt.tight_layout(rect=(0, 0.17, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    if pdf is not None:
        pdf.savefig(fig)
    plt.close(fig)


def plot_wins_vs_losses(character_summary: pd.DataFrame, output_path: Path, title: str, pdf: PdfPages | None = None) -> None:
    sns.set_theme(style="whitegrid")
    n = len(character_summary)
    fig_width = max(24, n * 0.45)

    fig, ax = plt.subplots(figsize=(fig_width, 11), dpi=220)
    x = range(n)
    width = 0.42

    ax.bar([i - width / 2 for i in x], character_summary["Wins"], width=width, color="#264653", label="Wins")
    ax.bar([i + width / 2 for i in x], character_summary["Losses"], width=width, color="#F4A261", label="Losses")

    ax.set_xticks(list(x))
    ax.set_xticklabels(character_summary["Character"], rotation=78, ha="right", fontsize=8)
    ax.set_ylabel("Count", fontsize=12)
    ax.set_xlabel("Character", fontsize=12)
    ax.set_title(title, fontsize=16, pad=14)
    ax.legend(loc="upper right")

    plt.tight_layout(rect=(0, 0.17, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    if pdf is not None:
        pdf.savefig(fig)
    plt.close(fig)


def plot_total_wins_vs_losses(total_summary: pd.DataFrame, output_path: Path, title: str, pdf: PdfPages | None = None) -> None:
    sns.set_theme(style="whitegrid")
    wins = int(total_summary.iloc[0]["Total_Wins"])
    losses = int(total_summary.iloc[0]["Total_Losses"])

    fig, ax = plt.subplots(figsize=(9, 7), dpi=220)
    wedges, texts, autotexts = ax.pie(
        [wins, losses],
        labels=["Wins", "Losses"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#1D3557", "#E63946"],
        wedgeprops={"width": 0.45, "edgecolor": "white"},
        textprops={"fontsize": 12},
    )

    ax.set_title(title, fontsize=16, pad=12)
    ax.text(0, 0, f"W: {wins}\nL: {losses}", ha="center", va="center", fontsize=13, weight="bold")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    if pdf is not None:
        pdf.savefig(fig)
    plt.close(fig)


def plot_pareto(scores_df: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    pareto = scores_df.copy()
    pareto = pareto.sort_values("Score", ascending=False).reset_index(drop=True)
    total_score = pareto["Score"].sum()
    pareto["Cumulative_Percent"] = (pareto["Score"].cumsum() / total_score) * 100 if total_score else 0

    n = len(pareto)
    fig_width = max(28, n * 0.5)
    fig, ax1 = plt.subplots(figsize=(fig_width, 12), dpi=240)

    x = range(n)
    colors = sns.color_palette("viridis", n)
    bars = ax1.bar(x, pareto["Score"], color=colors, alpha=0.9)
    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_xlabel("Character", fontsize=12)

    ax2 = ax1.twinx()
    ax2.plot(x, pareto["Cumulative_Percent"], color="#D62828", marker="o", markersize=4, linewidth=2.5)
    ax2.set_ylabel("Cumulative Score (%)", fontsize=12)
    ax2.set_ylim(0, 105)

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(pareto["Character"], rotation=80, ha="right", fontsize=8)

    for threshold in [50, 80, 90]:
        ax2.axhline(y=threshold, color="#6C757D", linestyle="--", linewidth=1)

    plt.title("Pareto Curve of Character Scores (All Characters Visible)", fontsize=17, pad=16)

    y_offset = max(0.03, pareto["Score"].max() * 0.004)
    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + y_offset,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=6,
            rotation=90,
        )

    plt.tight_layout(rect=(0, 0.2, 1, 1))
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(CHARTS_DIR / "pareto_curve_all_characters_scores.png", bbox_inches="tight")
    plt.close(fig)


def plot_round_pareto(scores_df: pd.DataFrame, output_path: Path, title: str, pdf: PdfPages | None = None) -> None:
    sns.set_theme(style="whitegrid")
    pareto = scores_df.copy().sort_values("Score", ascending=False).reset_index(drop=True)
    total_score = pareto["Score"].sum()
    pareto["Cumulative_Percent"] = (pareto["Score"].cumsum() / total_score) * 100 if total_score else 0

    n = len(pareto)
    fig_width = max(28, n * 0.5)
    fig, ax1 = plt.subplots(figsize=(fig_width, 12), dpi=240)

    x = range(n)
    colors = sns.color_palette("mako", n)
    bars = ax1.bar(x, pareto["Score"], color=colors, alpha=0.92)
    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_xlabel("Character", fontsize=12)

    ax2 = ax1.twinx()
    ax2.plot(x, pareto["Cumulative_Percent"], color="#A4161A", marker="o", markersize=4, linewidth=2.5)
    ax2.set_ylabel("Cumulative Score (%)", fontsize=12)
    ax2.set_ylim(0, 105)

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(pareto["Character"], rotation=80, ha="right", fontsize=8)

    for threshold in [50, 80, 90]:
        ax2.axhline(y=threshold, color="#6C757D", linestyle="--", linewidth=1)

    plt.title(title, fontsize=17, pad=16)

    y_offset = max(0.03, pareto["Score"].max() * 0.004)
    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + y_offset,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=6,
            rotation=90,
        )

    plt.tight_layout(rect=(0, 0.2, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    if pdf is not None:
        pdf.savefig(fig)
    plt.close(fig)


def _stagger_positions(y_values: list[float], min_gap: float) -> list[float]:
    if not y_values:
        return []
    adjusted = y_values[:]
    for idx in range(1, len(adjusted)):
        if adjusted[idx] - adjusted[idx - 1] < min_gap:
            adjusted[idx] = adjusted[idx - 1] + min_gap
    return adjusted


def plot_character_scores_all_rounds(round_records: dict[int, pd.DataFrame], scores_df: pd.DataFrame, output_path: Path) -> None:
    sns.set_theme(style="whitegrid")
    sorted_rounds = sorted(round_records)

    all_characters = sorted({char for df in round_records.values() for char in df["Character"].unique().tolist()})
    rank_order = {character: idx for idx, character in enumerate(scores_df["Character"].tolist())}
    ordered_characters = sorted(all_characters, key=lambda c: rank_order.get(c, len(rank_order) + 1000))

    matrix = pd.DataFrame(index=ordered_characters)
    for round_number in sorted_rounds:
        grouped = round_records[round_number].groupby("Character")["Score"].sum()
        matrix[f"Round_{round_number}"] = grouped
    matrix = matrix.fillna(0)
    cumulative_matrix = matrix.cumsum(axis=1)

    fig_width = max(24, len(sorted_rounds) * 8)
    fig_height = max(24, len(ordered_characters) * 0.42)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=250)

    x = list(sorted_rounds)
    cmap = plt.get_cmap("turbo")
    norm_denominator = max(1, len(ordered_characters) - 1)
    for idx, character in enumerate(ordered_characters):
        y = [float(cumulative_matrix.loc[character, f"Round_{round_number}"]) for round_number in sorted_rounds]
        ax.plot(x, y, color=cmap(idx / norm_denominator), linewidth=1.2, alpha=0.6)

    y_range = max(1.0, cumulative_matrix.to_numpy().max() - cumulative_matrix.to_numpy().min())
    min_gap = max(0.06, 0.009 * y_range)
    color_by_character = {character: cmap(idx / norm_denominator) for idx, character in enumerate(ordered_characters)}

    for round_number in sorted_rounds:
        col = f"Round_{round_number}"
        points = [(character, float(cumulative_matrix.loc[character, col])) for character in ordered_characters]
        points.sort(key=lambda item: item[1])
        adjusted_y = _stagger_positions([y_val for _char, y_val in points], min_gap=min_gap)

        x_shift = 0.055 if round_number % 2 else -0.055
        for (character, y_original), y_text in zip(points, adjusted_y):
            x_text = round_number + x_shift
            ax.plot([round_number, x_text], [y_original, y_text], color="#9CA3AF", linewidth=0.35, alpha=0.4)
            ax.text(
                x_text,
                y_text,
                character,
                fontsize=4.6,
                va="center",
                ha="center",
                rotation=90,
                color=color_by_character[character],
                alpha=0.9,
            )

    ax.set_xlim(min(x) - 0.35, max(x) + 0.35)
    ax.set_xticks(x)
    ax.set_xticklabels([ROUND_DISPLAY.get(rn, str(rn)) for rn in x])
    ax.set_xlabel("Round", fontsize=12)
    ax.set_ylabel("Accumulated Score", fontsize=12)
    ax.set_title("Accumulated Character Scores by Round (All Points Labeled)", fontsize=17, pad=16)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    records_df = load_round_records(RECORDS_DIR)
    round_records = load_round_records_by_round(RECORDS_DIR)
    character_summary = compute_character_summary(records_df)
    total_summary = compute_total_win_loss(records_df)
    scores_df = load_score_profile(RECORDS_DIR)

    rank_ordered_summary = apply_current_rank_order(character_summary, scores_df)

    save_tables(character_summary, total_summary)
    plot_avg_stock_and_damage(
        rank_ordered_summary,
        CHARTS_DIR / "average_stock_and_damage_per_fight.png",
        "Average Stock Differential and Damage per Fight (All Characters, Rank Ordered)",
    )
    plot_wins_vs_losses(
        rank_ordered_summary,
        CHARTS_DIR / "wins_vs_losses_by_character.png",
        "Wins vs Losses by Character (All Characters, Rank Ordered)",
    )
    plot_total_wins_vs_losses(
        total_summary,
        CHARTS_DIR / "total_wins_vs_losses_donut.png",
        "Total Wins vs Losses",
    )
    plot_pareto(scores_df)
    plot_character_scores_all_rounds(
        round_records,
        scores_df,
        CHARTS_DIR / "character_scores_by_round_labeled.png",
    )

    with PdfPages(ROUND_SUMMARY_PDF) as pdf:
        for round_number in sorted(round_records):
            round_df = round_records[round_number]
            round_character_summary = compute_character_summary(round_df)
            round_character_summary_ranked = apply_current_rank_order(round_character_summary, scores_df)
            round_total_summary = compute_total_win_loss(round_df)
            round_score_profile = compute_round_score_profile(round_df)

            save_round_tables(round_number, round_character_summary_ranked, round_total_summary)

            round_label = ROUND_LABEL.get(round_number, f"round_{round_number}")
            round_display = ROUND_DISPLAY.get(round_number, f"Round {round_number}")
            round_chart_dir = ROUND_CHARTS_DIR / round_label

            plot_avg_stock_and_damage(
                round_character_summary_ranked,
                round_chart_dir / "average_stock_and_damage_per_fight.png",
                f"{round_display}: Average Stock Differential and Damage per Fight (Rank Ordered)",
                pdf=pdf,
            )
            plot_wins_vs_losses(
                round_character_summary_ranked,
                round_chart_dir / "wins_vs_losses_by_character.png",
                f"{round_display}: Wins vs Losses by Character (Rank Ordered)",
                pdf=pdf,
            )
            plot_total_wins_vs_losses(
                round_total_summary,
                round_chart_dir / "total_wins_vs_losses_donut.png",
                f"{round_display}: Total Wins vs Losses",
                pdf=pdf,
            )
            plot_round_pareto(
                round_score_profile,
                round_chart_dir / "pareto_curve_round_scores.png",
                f"{round_display}: Pareto Curve by Character Score",
                pdf=pdf,
            )

    print(f"Analysis output generated in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
