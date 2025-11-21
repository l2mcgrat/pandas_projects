# New_Smash_Gods__Discovery_Training

import pandas as pd
matchup_df = pd.read_csv(r"C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects\matchup_chart.csv")

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

Bonus Stock Points are Divided by Round Number

"""

def round_1_calculator(Tourney_List):
    
    character_dict = {}
    for tourney in Tourney_List:
        for key in tourney:
            character_dict[key] = 0
    
    for tourney in Tourney_List:
        for key, fights in tourney.items():
            for n, fight in enumerate(fights):
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n <= 2:
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, 200 - fight[1][1]))/200)
                elif fight[1][0] > 0 and n > 2:
                    multiplier = (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, 200 - fight[1][1]))/200)/n
                elif fight[1][0] < 0 and n <= 2:
                    multiplier = (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/200))
                elif fight[1][0] < 0 and n > 2:
                    multiplier = (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/200))/n
                else:
                    continue
    
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict 

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
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_N = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_List = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_N, Tourney_N, Tourney_N, Tourney_N, Tourney_N]
character_dict = round_1_calculator(Tourney_List)
sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=True))
print(sorted_dict)
