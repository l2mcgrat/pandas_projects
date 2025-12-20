import pandas as pd

# ------------------------------------------------------------
# Load and preprocess the word list
# ------------------------------------------------------------

df_ranked_words = pd.read_csv("unigram_freq.csv")
df_ranked_words.columns = ["Words", "Count"]

# Keep only 5‑letter words
df_ranked_words = df_ranked_words[df_ranked_words["Words"].str.len() == 5]

# Reset index
df_ranked_words = df_ranked_words.reset_index(drop=True)

# Convert to uppercase (keep DataFrame intact)
df_ranked_words["Words"] = df_ranked_words["Words"].str.upper()


# ------------------------------------------------------------
# Wordle filtering function
# ------------------------------------------------------------

def wordle_word_limiter(df_5_letter_words, green_letter_list, grey_letter_list, yellow_letter_list, all_yellow_letters):

    # GREEN letters: must match exact position
    for n, l in enumerate(green_letter_list):
        if l != "":
            df_5_letter_words = df_5_letter_words[df_5_letter_words["Words"].str[n] == l]

    # GREY letters: must NOT appear anywhere
    for l in grey_letter_list:
        df_5_letter_words = df_5_letter_words[df_5_letter_words["Words"].str.contains(l) == False]

    # YELLOW letters: cannot appear in these positions
    for n, letters in enumerate(yellow_letter_list):
        for l in letters:
            df_5_letter_words = df_5_letter_words[df_5_letter_words["Words"].str[n] != l]

    # YELLOW letters: must appear somewhere in the word
    for l in all_yellow_letters:
        df_5_letter_words = df_5_letter_words[df_5_letter_words["Words"].str.contains(l) == True]

    return df_5_letter_words


# ------------------------------------------------------------
# Cheating Tools (example input)
# ------------------------------------------------------------

green_letter_list = ["", "", "", "R", ""]
grey_letters = "LEANCUO"
yellow_letter_list = ["H", "H", "", "", ""]

# Build list of all yellow letters
all_yellow_letters = "".join(yellow_letter_list)

# ------------------------------------------------------------
# Apply filters
# ------------------------------------------------------------

df_remaining = wordle_word_limiter(
    df_ranked_words.copy(),
    green_letter_list,
    grey_letters,
    yellow_letter_list,
    all_yellow_letters
)

df_remaining = df_remaining.reset_index(drop=True)

# ------------------------------------------------------------
# Output results
# ------------------------------------------------------------

if len(df_remaining) == 1:
    print("\n------------------------------------------------------------\n")
    print("The Wordle today is:", df_remaining["Words"].iloc[0])
    print("\n------------------------------------------------------------")

elif len(df_remaining) > 50:
    print("\n------------------------------------------------------------")
    print(f"\nRemaining Word Options ({len(df_remaining)} total):\n")
    print(df_remaining.head(15))
    print("\nRecommended word is:", df_remaining["Words"].iloc[0])
    print("\n------------------------------------------------------------")

else:
    print("\n------------------------------------------------------------")
    print(f"\nRemaining Word Options ({len(df_remaining)} total):\n")
    print(df_remaining)
    print("\nRecommended word is:", df_remaining["Words"].iloc[0])
    print("\n------------------------------------------------------------")
