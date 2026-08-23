import pandas as pd
from pathlib import Path
from next_smash_mains_profiles import build_profiles, RECORDS_DIR, MATCHUP_DF

op = pd.read_csv(Path("records/next_smash_mains_records/overall_ranking_profile.csv"))
profiles = build_profiles(RECORDS_DIR, MATCHUP_DF)

op_sorted = op.sort_values("Rank")
print(f"{'Char':<22} {'Official':>8} {'Computed':>8} {'Comp Score':>12} {'Off Score':>10}")
for _, row in op_sorted.iterrows():
    name = row["Character"]
    p = profiles.get(name)
    cr = p.current_rank if p else "?"
    cs = f"{p.current_score:.3f}" if p else "?"
    diff = (p.current_rank - int(row["Rank"])) if p else 0
    flag = " <--" if abs(diff) > 5 else ""
    print(f"{name:<22} {int(row['Rank']):>8} {str(cr):>8} {cs:>12} {row['Score']:>10.3f}{flag}")
