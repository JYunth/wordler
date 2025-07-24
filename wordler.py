import re
import sys
from collections import Counter

def find_best_guess(words):
    """
    Analyzes a list of possible words to find the best next guess.
    The "best" guess is the one containing the most frequent letters
    from the entire list of possibilities, maximizing information gain.
    """
    if not words:
        return None
    if len(words) == 1:
        return words[0]

    letter_frequency = Counter()
    for word in words:
        for letter in set(word):
            letter_frequency[letter] += 1
            
    best_word = ""
    max_score = -1
    for word in words:
        score = sum(letter_frequency[letter] for letter in set(word))
        if score > max_score:
            max_score = score
            best_word = word
            
    return best_word

def interactive_solver():
    """
    Runs an interactive Wordle solver that loops until the word is found.
    """
    # --- 1. Initialization ---
    WORD_LIST_PATH = "./english-words/words_alpha.txt"
    try:
        with open(WORD_LIST_PATH, "r") as f:
            all_words = {line.strip().lower() for line in f}
    except FileNotFoundError:
        print(f"❌ Error: Word list not found at '{WORD_LIST_PATH}'.")
        sys.exit(1)

    try:
        word_length = int(input("Enter the word length (usually 5): "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    # --- Game State Variables ---
    green_pattern = ['-'] * word_length
    all_yellows = set()
    all_greys = set()
    possible_words = [w for w in all_words if len(w) == word_length]
    
    turn = 1
    
    # --- 2. Main Game Loop ---
    while True:
        # --- Suggest a Guess ---
        if turn == 1:
            # Suggest a strong starting word for standard 5-letter games
            suggested_guess = "crane" if word_length == 5 else find_best_guess(possible_words)
            print(f"\n--- Turn {turn} ---")
            print(f"💡 Suggested starter: {suggested_guess}")
        else:
            print(f"\n--- Turn {turn} ---")
            # Display current state
            print(f"Possible words remaining: {len(possible_words)}")
            if len(possible_words) < 20:
                print("Possibilities:", ", ".join(possible_words))

            suggested_guess = find_best_guess(possible_words)
            if not suggested_guess:
                print("🤔 Hmm, no words match all the criteria. There might be an error in the clues provided.")
                return
            print(f"💡 Suggested guess: {suggested_guess}")

        # --- Get User Feedback on Their Last Guess ---
        last_guess = input("Enter the word you guessed: ").lower()
        if len(last_guess) != word_length:
            print(f"❌ Error: Guess must be {word_length} letters long. Please try again.")
            continue

        results = input(f"Enter results for '{last_guess}' (G=Green, Y=Yellow, -=Grey): ").lower()
        if len(results) != word_length or not all(c in 'gy-' for c in results):
            print("❌ Error: Invalid results format. Use 'G', 'Y', or '-'. Please try again.")
            continue
            
        if results == 'g' * word_length:
            print(f"\n🎉 Excellent! Solved in {turn} turns. The word was '{last_guess}'.")
            break

        # --- 3. Update Cumulative Knowledge ---
        for i, char in enumerate(last_guess):
            if results[i] == 'g':
                green_pattern[i] = char
                if char in all_yellows:
                    all_yellows.remove(char) # A letter can't be yellow if it's green
            elif results[i] == 'y':
                all_yellows.add(char)
            elif results[i] == '-':
                # Only add to greys if we don't know it's a green or yellow
                if char not in green_pattern and char not in all_yellows:
                    all_greys.add(char)

        # --- 4. Re-filter Word List with All Known Information ---
        current_greens_str = "".join(green_pattern)
        regex_pattern = f"^{current_greens_str.replace('-', '.')}$"
        
        # We start with the full list and apply all cumulative filters each time
        candidates = [w for w in all_words if len(w) == word_length]
        
        temp_possible_words = []
        for word in candidates:
            if not re.match(regex_pattern, word): continue
            if any(c in word for c in all_greys): continue
            if not all(c in word for c in all_yellows): continue

            # Advanced check: ensure a yellow letter isn't in a position it was found
            is_valid = True
            for i, char in enumerate(last_guess):
                if results[i] == 'y' and word[i] == char:
                    is_valid = False
                    break
            if not is_valid: continue

            temp_possible_words.append(word)

        possible_words = temp_possible_words
        turn += 1

if __name__ == "__main__":
    interactive_solver()
