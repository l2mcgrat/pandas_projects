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

def helper(num):   

    import pyautogui
    from time import sleep     

    if num == 1:
        sleep(4)
        for i in range(36):
            pyautogui.press('#')
            pyautogui.press('space')
            pyautogui.press('down')
            pyautogui.press('left')
            pyautogui.press('left')
            
    if num == 2:
        sleep(4)
        for i in range(54):
            pyautogui.press('backspace')
            pyautogui.press('backspace')
            pyautogui.press(str(int((86-i)/10.0)))
            pyautogui.press(str((86-i) % 10))
            pyautogui.press('down')

    return None

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

with PdfPages("reports/round_6_results.pdf") as pdf:
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

with PdfPages("reports/ranking_changes/3rd_restructuring.pdf") as pdf:
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

with PdfPages("reports/round_7_results.pdf") as pdf:
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
print("\nRound 8\n")
# print_sorted_dict(round_8_scores_dict)
round_8_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

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

with PdfPages("reports/ranking_changes/4th_restructuring.pdf") as pdf:
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
    
############################
####### Zombies 42-33 ######
############################
    
round_8_total_records = pd.read_csv(r"C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects\records\all_records.csv")

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

Tourney_List_9 = [Tourney_1, Tourney_2]
Tourney_List_9 = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9]

max_percentage = 200
round_9_scores_dict, win_loses, characters_played, all_characters, loss_dict = round_9_calculator(Tourney_List_9, max_percentage, round_9_scores_dict, loss_dict)
round_9_scores_dict = dict(sorted(round_9_scores_dict.items(), key=lambda item: item[1], reverse=False))
print("\nRound 9 Standings, Top 16 Advance\n")
print_sorted_dict(round_9_scores_dict)
round_9_loss_dict = dict(sorted(loss_dict.items(), key=lambda item: item[1], reverse=True)).copy()

#%%
##################################################
################ REPORT GENERATION ###############
##################################################

with PdfPages("reports/round_7_results.pdf") as pdf:
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
            
copy_loss_dict = loss_dict.copy()

def round_9_score_distribution_evolution(Tourney_Lists, renormalized_scores, loss_dict):
    
    with PdfPages("reports/round_9_histogram_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_9_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            histogram_generator(character_dict, "Score", "Frequency", "Round 9: Rank 42 to 9 Score Distribution", pdf)     
            
    character_dict = {}
    with PdfPages("reports/round_9_distribution_evolution.pdf") as pdf:
        for i in range(4):
            Tourney_List = Tourney_Lists[:2*(i+1)]
            character_dict, temp_loss_dict = renormalized_scores.copy(), loss_dict.copy()
            character_dict, win_loses, characters_played, all_characters, temp_loss_dict = round_9_calculator(Tourney_List, max_percentage, character_dict, temp_loss_dict)
            distribution_generator(character_dict, "Score", "Frequency", "Round 9: Rank 42 to 9 Score Distribution", pdf)   
            
round_9_scores = round_9_scores_dict.copy()
round_9_score_distribution_evolution(Tourney_List_9, round_9_scores, copy_loss_dict)

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

# All Rounds
max_percentage = 200
blank_dict = {character:[] for character in round_1_scores_dict}
Tourneys = [Tourney_List_1, Tourney_List_2, Tourney_List_3, Tourney_List_4, 
            Tourney_List_5, Tourney_List_6, Tourney_List_7, Tourney_List_7]
round_all_records = records(Tourneys, blank_dict, max_percentage)
round_all_records["Score"] = pd.to_numeric(round_all_records["Score"], errors="coerce")
round_all_records["Accumulated_Sum"] = round_all_records.groupby("Character")["Score"].cumsum()
round_all_records.to_csv("records/all_records.csv", index=False)