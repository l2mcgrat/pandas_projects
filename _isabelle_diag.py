import pandas as pd
from pathlib import Path
from next_smash_mains_profiles import build_profiles, RECORDS_DIR, MATCHUP_DF, LABEL_TO_ROUND, ROUND_DISPLAY

# Rebuild and expose internal data
import next_smash_mains_profiles as pm
from collections import defaultdict

rd = RECORDS_DIR
matchup_df = MATCHUP_DF

# ---- replicate build_profiles internals ----
LABEL_TO_ROUND = pm.LABEL_TO_ROUND
files = sorted(
    rd.glob("*_records.csv"),
    key=lambda f: LABEL_TO_ROUND.get(f.stem.removesuffix("_records"), 99),
)
all_matches = defaultdict(list)
exit_scores = {}
entry_scores = {}

for path in files:
    label = path.stem.removesuffix("_records")
    if label not in LABEL_TO_ROUND:
        continue
    df = pd.read_csv(path)
    if df.empty:
        continue
    round_exit = {}
    round_entry = {}
    for character, grp in df.groupby("Character", sort=False):
        char = str(character)
        grp = grp.sort_values("Round")
        round_exit[char]  = float(grp.iloc[-1]["Accumulated_Sum"])
        round_entry[char] = float(grp.iloc[0]["Accumulated_Sum"]) - float(grp.iloc[0]["Score"])
    exit_scores[label]  = round_exit
    entry_scores[label] = round_entry

ordered = sorted(exit_scores.keys(), key=lambda l: LABEL_TO_ROUND.get(l, 99))

# Print Isabelle's score at each round boundary
print("=== Isabelle round-by-round ===")
for label in ordered:
    ex = exit_scores.get(label, {}).get("Isabelle")
    en = entry_scores.get(label, {}).get("Isabelle")
    rd_disp = ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label)
    played = "PLAYED" if ex is not None else "skipped"
    print(f"  {rd_disp:12s} ({label:20s})  exit={ex!s:10}  entry={en!s:10}  {played}")

# Show what the 'effective' score is at each round boundary (from new logic)
profiles = build_profiles(RECORDS_DIR, MATCHUP_DF)
isabelle = profiles["Isabelle"]
print("\n=== Isabelle ranks_by_round ===")
for label, rank in isabelle.ranks_by_round.items():
    rd_disp = ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label)
    print(f"  {rd_disp:12s}: rank {rank}")

print(f"\ncurrent_rank={isabelle.current_rank}  current_score={isabelle.current_score:.3f}")
print(f"rescoring events: {isabelle.rescoring_events}")
