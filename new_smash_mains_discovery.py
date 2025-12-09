# New_Smash_Gods__Discovery_Training

import statistics
from collections import defaultdict
import pandas as pd
matchup_df = pd.read_csv(r"C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects\matchup_chart.csv")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import numpy as np
import math

def bar_generator(win_loses, x_axis, y_axis, title, pdf):
    
    keys = list(win_loses.keys())
    values = list(win_loses.values())
    
    plt.figure()
    bars = plt.bar(keys, values, color="skyblue", edgecolor="black")
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, str(height), ha='center', va='bottom')
    plt.bar(keys, values, color="skyblue", edgecolor="black")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    plt.xticks(rotation=60)
    pdf.savefig(bbox_inches="tight")   # save current plt figure
    plt.close()   

def histogram_generator(character_dict, x_axis, y_axis, title, pdf):
    
    values = list(character_dict.values())
    
    plt.figure()
    plt.hist(values, bins=[i/2 for i in range(int(2*min(values))-1, int(2*max(values)) + 2)], edgecolor='black')
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    pdf.savefig()   # save current plt figure
    plt.close()   
    
def distribution_generator(character_dict, x_axis, y_axis, title, pdf):
    
    values = list(character_dict.values())

    plt.figure()
    sns.kdeplot(values, fill=True, color="skyblue", linewidth=2)
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(title)
    pdf.savefig()   # save current plt figure
    plt.close()   

def table_generator(win_loses, title, pdf):
    
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

    plt.figure()
    fig, ax = plt.subplots(figsize=(8, 8))
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
    pdf.savefig(fig, bbox_inches="tight")
    plt.close()    
    
def print_sorted_dict(sorted_dict):
    for n, (key, value) in enumerate(sorted_dict.items()):
        print(len(sorted_dict.items()) - n, value, key)

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
################### ANALYSIS #####################
##################################################

# Round 4 Only
max_percentage = 175
blank_dict = {character:[] for character in round_4_scores_dict}
Tourneys = [Tourney_List_4]
round_4_records = records(Tourneys, blank_dict, max_percentage)
round_4_records["Score"] = pd.to_numeric(round_4_records["Score"], errors="coerce")
round_4_records["Accumulated_Sum"] = round_4_records.groupby("Character")["Score"].cumsum()
round_4_records.to_csv("records/round_4_records.csv", index=False)

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

round_2_scores_dict = dict(sorted(round_2_scores_dict.items(), key=lambda item: item[1], reverse=False))
characters = [character for character in round_2_scores_dict]
initial_ranks = {character: rank + 1 for rank, character in enumerate(round_2_scores_dict)}
bottom_6 = {character: score for character, score in round_2_scores_dict.items() if score < 4.00}
all_round_scores_dict = bottom_6 | round_3_scores_dict | round_4_scores_dict
all_round_scores_dict = dict(sorted(all_round_scores_dict.items(), key=lambda item: item[1], reverse=False))
final_ranks = {character: rank + 1 for rank, character in enumerate(all_round_scores_dict)}

with PdfPages("reports/ranking_changes/ranking_changes_1.pdf") as pdf:
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
print_sorted_dict(round_5_scores_dict)
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

with PdfPages("reports/ranking_changes/2nd_elimination.pdf") as pdf:
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

with PdfPages("reports/ranking_changes/1st_elimination.pdf") as pdf:
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
             "Wii Fit Trainer": 49}
             
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
##################################################
################ REPORT GENERATION ###############
##################################################
'''
def random_sigmoid(rank_64_to_49, round_5_scores_dict):
    
    # goal is to have scores range from 64 up at least greater than rank 65
    
    for character, score in rank_64_to_49.items():
        round_5_scores_dict[character] = round(13.5 + (3.5/(1 + np.exp(-(score-13.5)))),2)

    return round_5_scores_dict

round_5_scores_dict = random_sigmoid(rank_64_to_49, round_5_scores_dict)
'''


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

Tourney_List_6 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6]

max_percentage = 150
round_6_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_6_calculator(Tourney_List_6, max_percentage, round_6_scores_dict, loss_dict)
round_6_scores_dict = dict(sorted(round_6_scores_dict.items(), key=lambda item: item[1], reverse=False))
print_sorted_dict(round_6_scores_dict)
round_6_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################### ANALYSIS #####################
##################################################

def ranking_changes_2nd_remerger(characters, initial_ranks, final_ranks):
    
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

# All Rounds
max_percentage = 200
blank_dict = {character:[] for character in round_1_scores_dict}
Tourneys = [Tourney_List_1, Tourney_List_2, Tourney_List_3, Tourney_List_4]
round_all_records = records(Tourneys, blank_dict, max_percentage)
round_all_records["Score"] = pd.to_numeric(round_all_records["Score"], errors="coerce")
round_all_records["Accumulated_Sum"] = round_all_records.groupby("Character")["Score"].cumsum()
round_all_records.to_csv("records/all_records.csv", index=False)