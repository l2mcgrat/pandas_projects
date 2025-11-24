# New_Smash_Gods__Discovery_Training

import pandas as pd
matchup_df = pd.read_csv(r"C:\Users\anime\OneDrive\Desktop\coding_projects\pandas_projects\matchup_chart.csv")
import matplotlib.pyplot as plt
import seaborn as sns
import math

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

def histogram_generator(character_dict):
    
    values = list(character_dict.values())
    
    plt.hist(values, bins=[i/2 for i in range(-3, 26)], edgecolor='black')
    plt.xlabel('Value')
    plt.ylabel('Count')
    plt.title('Histogram of Scores')
    plt.show()
    
def distribution_generator(character_dict):
    
    values = list(character_dict.values())

    sns.kdeplot(values, fill=True, color="skyblue", linewidth=2)
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.title("Continuous Distribution of Dictionary Values")
    plt.show()

def round_1_calculator(Tourney_List, max_percentage):
    
    character_dict = {}
    for tourney in Tourney_List:
        for key in tourney:
            character_dict[key] = 0
    
    for tourney in Tourney_List:
        for key, fights in tourney.items():
            for n, fight in enumerate(fights):
                multiplier = 1 if not bool(fight[1][0]) else (1 - matchup_df[matchup_df["Character"] == key.lower()][fight[0].lower()].iloc[0]/20)
                if fight[1][0] > 0 and n + 1 <= 3:
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)
                elif fight[1][0] > 0 and n + 1 > 3:
                    character_dict[key] += multiplier*(1 + n/10)*(fight[1][0] + (max(0, max_percentage - fight[1][1]))/max_percentage)/n
                elif fight[1][0] < 0 and n + 1 <= 3:
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))
                elif fight[1][0] < 0 and n + 1 > 2:
                    character_dict[key] += multiplier*(1 + n/10)*(1 + fight[1][0] + min(1, fight[1][1]/max_percentage))/n
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
        "Sonic": [["Joker", [1, 71]], ["Greninja", [3, 105]], ["Toon Link", [1, 15]], ["Pyra & Mythra", [2, 174]], ["Opponent 5", [0, 0]]], 
        "Mii Brawler": [["Pyra & Mythra", [-2, 143]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Mario": [["Falco", [-1, 47]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Bayonetta": [["Olimar", [-2, 86]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
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

Tourney_N = {
        "Character A": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character B": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]], 
        "Character C": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]],          
        "Character D": [["Opponent 1", [0, 0]], ["Opponent 2", [0, 0]], ["Opponent 3", [0, 0]], ["Opponent 4", [0, 0]], ["Opponent 5", [0, 0]]] 
        }

Tourney_List = [Tourney_1, Tourney_2, Tourney_3, Tourney_4, Tourney_5, Tourney_6, Tourney_7, Tourney_8, Tourney_9, Tourney_10,
                Tourney_11, Tourney_12, Tourney_13, Tourney_14, Tourney_15, Tourney_16, Tourney_17, Tourney_18, Tourney_19, Tourney_20, 
                Tourney_N]

max_percentage = 200
character_dict = round_1_calculator(Tourney_List, max_percentage)
sorted_dict = dict(sorted(character_dict.items(), key=lambda item: item[1], reverse=False))
for n, (key, value) in enumerate(sorted_dict.items()):
    print(len(sorted_dict.items()) - n, value, key)

distribution_generator(character_dict)
histogram_generator(character_dict)
