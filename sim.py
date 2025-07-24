import random
import sys
import os

def check_guess(guess, secret_word):
    """
    Compares a guess to the secret word and returns Wordle-style feedback.
    This two-pass method correctly handles duplicate letters.
    """
    length = len(secret_word)
    result = [''] * length
    secret_letters = list(secret_word)

    # First pass: Check for Greens (correct letter, correct position) 🟩
    for i in range(length):
        if guess[i] == secret_letters[i]:
            result[i] = '🟩'
            secret_letters[i] = None  # Mark this letter as "used"

    # Second pass: Check for Yellows (correct letter, wrong position) 🟨
    for i in range(length):
        if result[i] == '':  # Only check letters that aren't already green
            if guess[i] in secret_letters:
                result[i] = '🟨'
                secret_letters.remove(guess[i]) # Mark as used for yellow
    
    # Any remaining empty spots are Greys ⬜️
    for i in range(length):
        if result[i] == '':
            result[i] = '⬜️'
            
    return "".join(result)

def play_wordle():
    """
    Main function to run a single instance of a Wordle game.
    """
    # --- 1. Game Setup ---
    WORD_LIST_PATH = "./english-words/words_alpha.txt"
    MAX_TRIES = 6
    
    try:
        with open(WORD_LIST_PATH, "r") as f:
            all_words = {line.strip().lower() for line in f}
    except FileNotFoundError:
        print(f"❌ Error: Word list not found at '{WORD_LIST_PATH}'.")
        sys.exit(1)
        
    try:
        word_length = int(input("How many letters for this Wordle? "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    # Filter for words of the correct length and ensure they are valid for guessing
    valid_words = {w for w in all_words if len(w) == word_length}
    if not valid_words:
        print(f"😥 Sorry, no words of length {word_length} were found in the dictionary.")
        return
        
    secret_word = random.choice(list(valid_words))
    guess_history = []
    
    print(f"\nWordle instance started! You have {MAX_TRIES} tries to guess the {word_length}-letter word.")
    
    # --- 2. Game Loop ---
    for turn in range(1, MAX_TRIES + 1):
        print("-" * 20)
        print(f"Turn {turn}/{MAX_TRIES}")

        # Display previous guesses
        for g, r in guess_history:
            print(f"{g.upper()}  {r}")
            
        # Get a valid guess from the user
        while True:
            guess = input("Enter your guess: ").lower()
            if len(guess) != word_length:
                print(f"Guess must be {word_length} letters long.")
            elif guess not in valid_words:
                print("Not a valid word in the dictionary.")
            else:
                break # Guess is valid
        
        # Check the guess and store the result
        result = check_guess(guess, secret_word)
        guess_history.append((guess, result))
        
        # Clear screen for a cleaner look
        os.system('cls' if os.name == 'nt' else 'clear')

        # Check for win condition
        if guess == secret_word:
            print("-" * 20)
            print("Congratulations! You guessed it!\n")
            for g, r in guess_history:
                print(f"{g.upper()}  {r}")
            print(f"\nThe word was: {secret_word.upper()}")
            return
            
    # --- 3. End of Game (Loss) ---
    print("-" * 20)
    print("Game over! You ran out of tries.\n")
    for g, r in guess_history:
        print(f"{g.upper()}  {r}")
    print(f"\nThe word was: {secret_word.upper()}")

if __name__ == "__main__":
    play_wordle()

