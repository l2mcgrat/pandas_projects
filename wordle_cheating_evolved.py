
import os
import pandas as pd

# Download unigram frequency dataset on kaggle and set the appropriate file path location

df_ranked_words = pd.read_csv("unigram_freq.csv")
df_ranked_words.columns = ["Words","Count"]
df_ranked_words = df_ranked_words[df_ranked_words["Words"].str.len() == 5]
df_ranked_words = df_ranked_words.reset_index(drop = True)
df_ranked_words = df_ranked_words['Words'].str.upper()

def wordle_word_limiter(df_5_letter_words, green_letter_list, grey_letter_list, yellow_letter_list, all_yellow_letters):
    
    # filter out words based on which letters occupy which spaces
    for n, l in enumerate(green_letter_list):
        if not l == "": df_5_letter_words = df_5_letter_words[df_5_letter_words['Words'].str[n] == l]
    
    # filter out words based on which words aren't optional
    for l in grey_letter_list: df_5_letter_words = df_5_letter_words[df_5_letter_words['Words'].str.contains(l) == False]
    
    # filter out words based on which words aren't occupied in certain spaces
    for n, letters in enumerate(yellow_letter_list):
        for l in letters:
            df_5_letter_words = df_5_letter_words[df_5_letter_words['Words'].str[n] != l]

    # filter out words based on which letters exist
    for l in all_yellow_letters: df_5_letter_words = df_5_letter_words[df_5_letter_words['Words'].str.contains(l) == True]

    return df_5_letter_words

# Cheating Tools Backup

green_letter_list = ["","","","",""]
grey_letters = ""
yellow_letter_list = ["","","","",""]
all_yellow_letters = ""
for l in yellow_letter_list: all_yellow_letters += l 

# Cheating Tools 

green_letter_list = ["","","","",""]
grey_letters = ""
yellow_letter_list = ["","","","",""]
all_yellow_letters = ""
for l in yellow_letter_list: all_yellow_letters += l  

df_remaining = wordle_word_limiter(df_ranked_words, green_letter_list, grey_letters, yellow_letter_list, all_yellow_letters)

if len(df_remaining) == 1:
    df_remaining = df_remaining.reset_index(drop = True)
    print("\n------------------------------------------------------------\n")
    print("\nThe Wordle today is; " + df_remaining[0] + "\n")
    print("\n------------------------------------------------------------")
elif len(df_remaining) > 50:
    df_remaining = df_remaining.reset_index(drop = True)
    print("\n------------------------------------------------------------")
    print("\nRemaining Word Options, a total of " + str(len(df_remaining)) + " are; \n\n", df_remaining.head(15))
    print("\n\nRecommended word is; " + df_remaining[0] + "\n")
    print("\n------------------------------------------------------------")
else: 
    df_remaining = df_remaining.reset_index(drop = True)
    print("\n------------------------------------------------------------")
    print("\nRemaining Word Options, a total of " + str(len(df_remaining)) + " are; \n\n", df_remaining)
    print("\n\nRecommended word is; " + df_remaining[0] + "\n")
    print("\n------------------------------------------------------------")
