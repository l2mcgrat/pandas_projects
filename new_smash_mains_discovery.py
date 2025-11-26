# New_Smash_Gods__Discovery_Training

import pandas as pd
matchup_df = pd.read_csv(r"C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects\matchup_chart.csv")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math

def bar_generator(win_loses, x_axis, y_axis, title):
    
    keys = list(win_loses.keys())
    values = list(win_loses.values())
    
    bars = plt.bar(keys, values, color="skyblue", edgecolor="black")
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, str(height), ha='center', va='bottom')
    plt.bar(keys, values, color="skyblue", edgecolor="black")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.xticks(rotation=60)
    plt.show()

def histogram_generator(character_dict, x_axis, y_axis, title):
    
    values = list(character_dict.values())
    
    plt.hist(values, bins=[i/2 for i in range(-3, 26)], edgecolor='black')
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.show()
    
def distribution_generator(character_dict, x_axis, y_axis, title):
    
    values = list(character_dict.values())

    sns.kdeplot(values, fill=True, color="skyblue", linewidth=2)
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.show()

def table_generator(win_loses, title):
    
    # Prepare table data: each row is [key, comma-separated values]
    table_data = [[key, ", ".join(values)] for key, values in win_loses.items()]

    # Function to chunk list into groups of n
    def chunk_list(lst, n=3):
        return [", ".join(lst[i:i+n]) for i in range(0, len(lst), n)]
    
    # Prepare table data
    table_data = []
    for key, values in win_loses.items():
        chunks = chunk_list(values, 9)
        # Join chunks with newlines
        value_str = "\n".join(chunks)
        # Pad the category with newlines to match number of chunks
        category_str = "\n".join([key] + [""]*(len(chunks)-1))
        table_data.append([category_str, value_str])

    fig, ax = plt.subplots(figsize=(15, 7))
    ax.axis('off')
    table = ax.table(cellText=table_data, colLabels=["Category", "Values"], cellLoc='center', loc='center')
    table.scale(1.2, 1.5)
    
    for (row, col), cell in table.get_celld().items():
        cell.set_height(0.2)  
        if col == 0:
            cell.set_width(0.3)  
        else:
            cell.set_width(1.7)  
        cell.set_text_props(va='center', ha='center')
        
    table.set_fontsize(12)
    table.auto_set_column_width([0, 1]) 
    # plt.title(title, fontsize=14)
    plt.show()

def generator(character_dict, win_loses):
    
    # Win Category Data
    win_loss_totals = {category:total for category, (total, total_score, characters) in win_loses.items()}
    win_loss_averages = {category:int(200*total_score/total)/200 for category, (total, total_score, characters) in win_loses.items()}
    win_loss_characters = {category:characters for category, (total, total_score, characters) in win_loses.items()}
    
    # Win Category Plotting and Tables
    bar_generator(win_loss_totals, "Count", "Category", "Round 1: Win/Loss Categories")
    bar_generator(win_loss_averages, "Average Score", "Category", "Round 1: Score Comparisons")
    table_generator(win_loss_characters, "Character Fighting End Scenario Table")
    
    # Score Distributions
    histogram_generator(character_dict, "Score", "Frequency", "Round 1: Score Distribution")
    distribution_generator(character_dict, "Score", "Density", "Round 1: Score Density Plot")

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

def round_1_calculator(Tourney_List, max_percentage):
    
    character_dict = {}
    for tourney in Tourney_List:
        for key in tourney:
            character_dict[key] = 0
    
    win_loses = {"Lost Round 1": [0, 0, []], "Lost Round 2": [0, 0, []], "Lost Round 3": [0, 0, []], "Lost Round 4": [0, 0, []], 
                 "Lost Round 5": [0, 0, []], "Won Round 3": [0, 0, []], "Won Round 4": [0, 0, []], "Won Tourney": [0, 0, []]}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
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
                    score = multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                    character_dict[key] += score
                    if (n + 1 == 5): 
                        win_loses["Won Tourney"][0] += 1
                        win_loses["Won Tourney"][1] += character_dict[key]
                        win_loses["Won Tourney"][2].append(key)
                elif fight[1][0] < 0 and n + 1 <= 3:
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
                    match_won = False
                    score = multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
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
    
    return character_dict, win_loses, characters_played, all_characters 

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

max_percentage = 200
character_dict, win_loses, characters_played, all_characters = round_1_calculator(Tourney_List, max_percentage)
sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
for n, (key, value) in enumerate(sorted_dict.items()):
    print(len(sorted_dict.items()) - n, value, key)
    
# call plot generator
generator(character_dict, win_loses)

top_sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=True))
Information_Round_1 = {"Results Round 1:": {"Rankings":top_sorted_dict}}

#%%
#######################################################
####################### ROUND 2 #######################
#######################################################

"""

Recalculated Scores

score = score

Round 2 Grader

IF Stock_Diff > 0
1pt/Stock_Diff and 0.05pts per 10% below 200

ex)

IF Stock_Diff < 0
0pts for 1 Stock Diff, -1pts for 2 Stock, etc.
0.05pts per 10% Damage Given up to 200%

ex) 

Bonus Match Points are Divided by Round Number

"""

round_1_scores = [score for key, score in sorted_dict.items()]
min_score, max_score = min(round_1_scores), max(round_1_scores)
for character, score in sorted_dict.items(): 
    character_dict[character] = int(2000*np.sqrt(10*((2.0 + score)**(3/2))/(max_score-min_score)))/2000

sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
for n, (key, value) in enumerate(sorted_dict.items()):
    print(len(sorted_dict.items()) - n, value, key)

#%%

def round_2_calculator(Tourney_List, max_percentage, character_dict):
    
    character_dict = {}
    for tourney in Tourney_List:
        for key in tourney:
            character_dict[key] = 0
    
    win_loses = {"Lost Round 1": 0, "Lost Round 2": 0, "Lost Round 3": 0, "Lost Round 4": 0, 
                 "Lost Round 5": 0, "Won Round 3": 0, "Won Round 4": 0, "Won Tourney": 0}
    
    characters_played = set()
    all_characters = set()
    for tourney in Tourney_List:
        for key, fights in tourney.items():
            characters_played.add(key)
            for n, fight in enumerate(fights):
                all_characters.add(fight[0])
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                    match_won = True
                elif fight[1][0] > 0 and n + 1 > 3:
                    if (n + 1 == 5): win_loses["Won Tourney"] += 1
                    match_won = True
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/(n + 1)
                elif fight[1][0] < 0 and n + 1 <= 3:
                    match_won = False
                    if (n + 1 == 1): win_loses["Lost Round 1"] += 1
                    if (n + 1 == 2): win_loses["Lost Round 2"] += 1
                    if (n + 1 == 3): win_loses["Lost Round 3"] += 1
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                elif fight[1][0] < 0 and n + 1 > 3:
                    match_won = False
                    if (n + 1 == 4): win_loses["Lost Round 4"] += 1
                    if (n + 1 == 5): win_loses["Lost Round 5"] += 1
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/(n + 1)
                else:
                    if n + 1 == 4 and match_won: 
                        win_loses["Won Round 3"] += 1
                        match_won = False
                    if n + 1 == 5 and match_won: 
                        win_loses["Won Round 4"] += 1             
                
    for fighter in character_dict:
        character_dict[fighter] = int(character_dict[fighter]*100)/100
    
    return character_dict, win_loses, characters_played, all_characters 

#####################
###### Matches ######
#####################

Tourney_1 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_2 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_3 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_4 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_5 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_6 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_7 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_8 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_9 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_10 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_11 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_12 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_13 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_14 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_15 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_16 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_17 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_18 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_19 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_20 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_21 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_22 = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_List = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9, Tourney_10,
                Tourney_11, Tourney_12, Tourney_13, Tourney_14, Tourney_15, Tourney_16, Tourney_17, Tourney_18, Tourney_19,
                Tourney_20, Tourney_21, Tourney_22]

max_percentage = 200
character_dict, win_loses, characters_played, all_characters = round_1_calculator(Tourney_List, max_percentage)
sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
for n, (key, value) in enumerate(sorted_dict.items()):
    print(len(sorted_dict.items()) - n, value, key)
    
# call plot generator
generator(character_dict, win_loses)

