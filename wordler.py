import re
import sys
from collections import Counter, defaultdict

# ANSI escape codes for colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    GREY = '\033[90m'
    ENDC = '\033[0m'

def colorize(text, color):
    """Applies ANSI color codes to text."""
    return f"{color}{text}{Colors.ENDC}"

class WordleSolver:
    """
    A class to encapsulate the logic for solving Wordle puzzles.
    """
    def __init__(self, word_length=5, word_list_path="./english-words/words_alpha.txt", hard_mode=False):
        self.word_length = word_length
        self.word_list_path = word_list_path
        self.hard_mode = hard_mode
        self.all_words = self._load_words()
        self.possible_words = [w for w in self.all_words if len(w) == self.word_length]
        self.algorithm = "minimax"  # Default algorithm

        # Game State
        self.green_pattern = ['-'] * self.word_length
        self.yellow_misplaced = defaultdict(set)  # {letter: {positions}}
        self.letter_min_counts = Counter()
        self.letter_max_counts = {}
        self.greys = set()
        self.turn = 1

    def _load_words(self):
        """Loads the word list from the specified path."""
        try:
            with open(self.word_list_path, "r") as f:
                return {line.strip().lower() for line in f}
        except FileNotFoundError:
            print(f"❌ Error: Word list not found at '{self.word_list_path}'.")
            sys.exit(1)

    def _remove_word_from_database(self, word_to_remove):
        """Removes a word from the word list file."""
        import os
        temp_file_path = self.word_list_path + ".tmp"
        try:
            with open(self.word_list_path, "r") as original_file, open(temp_file_path, "w") as temp_file:
                for line in original_file:
                    if line.strip().lower() != word_to_remove:
                        temp_file.write(line)
            os.replace(temp_file_path, self.word_list_path)
        except Exception as e:
            print(f"❌ Error removing word from database: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def find_best_guess_frequency(self):
        """Analyzes possible words to find the best next guess based on letter frequency."""
        if not self.possible_words: return None
        if len(self.possible_words) == 1: return self.possible_words[0]

        letter_frequency = Counter()
        for word in self.possible_words:
            for letter in set(word):
                letter_frequency[letter] += 1

        best_word, max_score = "", -1
        for word in self.possible_words:
            score = sum(letter_frequency[letter] for letter in set(word))
            if score > max_score:
                max_score, best_word = score, word
        return best_word

    def _get_pattern(self, guess, answer):
        """Determines the G/Y/- pattern for a guess against a potential answer."""
        pattern = ['-'] * self.word_length
        used_in_answer = [False] * self.word_length
        for i in range(self.word_length):
            if guess[i] == answer[i]:
                pattern[i] = 'g'
                used_in_answer[i] = True
        for i in range(self.word_length):
            if pattern[i] == '-':
                for j in range(self.word_length):
                    if not used_in_answer[j] and guess[i] == answer[j]:
                        pattern[i] = 'y'
                        used_in_answer[j] = True
                        break
        return "".join(pattern)

    def find_best_guess_minimax(self):
        """Finds the best guess by minimizing the maximum number of remaining possibilities."""
        if not self.possible_words: return None
        if len(self.possible_words) == 1: return self.possible_words[0]

        best_guess, min_max_remaining = "", float('inf')
        guess_candidates = list(self.all_words) if len(self.possible_words) > 2 else self.possible_words

        for guess in guess_candidates:
            if len(guess) != self.word_length: continue
            pattern_counts = defaultdict(int)
            for answer in self.possible_words:
                pattern = self._get_pattern(guess, answer)
                pattern_counts[pattern] += 1
            max_remaining = max(pattern_counts.values())

            if max_remaining < min_max_remaining:
                min_max_remaining, best_guess = max_remaining, guess
            elif max_remaining == min_max_remaining:
                if guess in self.possible_words and best_guess not in self.possible_words:
                    best_guess = guess
        return best_guess

    def _update_knowledge(self, guess, results):
        """Updates the solver's knowledge based on the results of a guess."""
        guess_counts = Counter(guess)
        for i, char in enumerate(guess):
            if results[i] == 'g':
                self.green_pattern[i] = char
            elif results[i] == 'y':
                self.yellow_misplaced[char].add(i)

        for char in guess_counts:
            green_count = sum(1 for i, c in enumerate(guess) if c == char and results[i] == 'g')
            yellow_count = sum(1 for i, c in enumerate(guess) if c == char and results[i] == 'y')
            grey_count = sum(1 for i, c in enumerate(guess) if c == char and results[i] == '-')
            min_count = green_count + yellow_count
            self.letter_min_counts[char] = max(self.letter_min_counts[char], min_count)
            if grey_count > 0:
                self.letter_max_counts[char] = min_count
            if green_count == 0 and yellow_count == 0:
                self.greys.add(char)

    def _filter_words(self):
        """Filters the list of possible words based on all current knowledge."""
        temp_possible_words = []
        green_regex = re.compile("".join(self.green_pattern).replace('-', '.'))
        for word in self.possible_words:
            if not green_regex.match(word): continue
            if any(c in self.greys for c in word): continue
            word_counts = Counter(word)
            valid = True
            for char, count in self.letter_min_counts.items():
                if word_counts[char] < count: valid = False; break
            if not valid: continue
            for char, count in self.letter_max_counts.items():
                if word_counts[char] != count: valid = False; break
            if not valid: continue
            for char, positions in self.yellow_misplaced.items():
                if any(word[pos] == char for pos in positions): valid = False; break
            if not valid: continue
            temp_possible_words.append(word)
        self.possible_words = temp_possible_words

    def _is_valid_hard_mode_guess(self, guess):
        """Checks if a guess is valid under hard mode rules."""
        # Must use all green letters in their correct positions
        for i, char in enumerate(self.green_pattern):
            if char != '-' and guess[i] != char:
                print(f"❌ Hard mode rule: Green letter '{char}' must be at position {i+1}.")
                return False
        # Must use all yellow letters
        for char in self.yellow_misplaced:
            if char not in guess:
                print(f"❌ Hard mode rule: Yellow letter '{char}' must be in the guess.")
                return False
        return True

    def run(self):
        """Runs the main interactive loop for the solver."""
        print("--- Wordle Solver ---")
        algo_choice = input("Choose algorithm (1=Frequency, 2=Minimax) [2]: ").strip()
        if algo_choice == '1':
            self.algorithm = "frequency"
            print("Using Frequency-based algorithm.")
        else:
            print("Using Minimax algorithm (can be slow on first turn).")
        
        hard_mode_choice = input("Enable Hard Mode? (y/N) [N]: ").strip().lower()
        if hard_mode_choice == 'y':
            self.hard_mode = True
            print("Hard Mode enabled.")

        while True:
            print(f"\n--- Turn {self.turn} ---")
            if len(self.possible_words) > 1:
                print(f"Possible words remaining: {len(self.possible_words)}")
            if len(self.possible_words) < 20:
                print("Possibilities:", ", ".join(self.possible_words))

            suggested_guess = self.find_best_guess_minimax() if self.algorithm == "minimax" else self.find_best_guess_frequency()
            if not suggested_guess:
                print("🤔 Hmm, no words match all the criteria. There might be an error in the clues provided.")
                return
            
            colorized_suggestion = ""
            for i, char in enumerate(suggested_guess):
                if self.green_pattern[i] == char:
                    colorized_suggestion += colorize(char, Colors.GREEN)
                elif char in self.yellow_misplaced and i not in self.yellow_misplaced[char]:
                     colorized_suggestion += colorize(char, Colors.YELLOW)
                else:
                    colorized_suggestion += char
            print(f"💡 Suggested guess: {colorized_suggestion}")

            last_guess = ""
            while True:
                last_guess = input("Enter the word you guessed (or '/new' for a different suggestion): ").lower()
                if last_guess == '/new':
                    if suggested_guess:
                        print(f"Removing '{suggested_guess}' from the word list and getting a new suggestion.")
                        self.all_words.remove(suggested_guess)
                        if suggested_guess in self.possible_words:
                            self.possible_words.remove(suggested_guess)
                        self._remove_word_from_database(suggested_guess)
                    break
                elif len(last_guess) != self.word_length:
                    print(f"❌ Error: Guess must be {self.word_length} letters long.")
                elif self.hard_mode and not self._is_valid_hard_mode_guess(last_guess):
                    continue
                else:
                    break

            if last_guess == '/new':
                continue

            results_input = input(f"Enter results for '{last_guess}' (G=Green, Y=Yellow, -=Grey): ").lower()
            if len(results_input) != self.word_length or not all(c in 'gy-' for c in results_input):
                print("❌ Error: Invalid results format. Use 'G', 'Y', or '-'.")
                continue
            
            colorized_result = ""
            for i, char in enumerate(last_guess):
                if results_input[i] == 'g':
                    colorized_result += colorize(char, Colors.GREEN)
                elif results_input[i] == 'y':
                    colorized_result += colorize(char, Colors.YELLOW)
                else:
                    colorized_result += colorize(char, Colors.GREY)
            print(f"Your guess: {colorized_result}")

            if results_input == 'g' * self.word_length:
                print(f"\n🎉 Excellent! Solved in {self.turn} turns. The word was '{last_guess}'.")
                break

            self._update_knowledge(last_guess, results_input)
            self._filter_words()
            self.turn += 1

def main():
    """Main function to set up and run the Wordle solver."""
    try:
        word_length = int(input("Enter the word length (usually 5): "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return
    solver = WordleSolver(word_length)
    solver.run()

if __name__ == "__main__":
    main()
