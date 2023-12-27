import json
import re
from spellchecker import SpellChecker
from flask import Flask, request, render_template
from random import randint

app = Flask(__name__)

RED_HEX = "#800000"
YELLOW_HEX = "#FFF000"
GREEN_HEX = "#228B22"

##########################################################################################
# Generate dictionary (is actually a list not a python dictionary) of words
##########################################################################################

spell = SpellChecker() # also initialize now for check_word function
WORDS = []

for word in spell.word_frequency:
    if (re.match("^[a-z]{5}$", word)): # gets all words with only a-z and of length 5
        WORDS.append(word.upper())

##########################################################################################

def check_word(word):
    """
    This checks if a word is a word in the english language according to the spellchecker library
    function was found at
    https://replit.com/talk/ask/How-to-check-if-a-word-is-an-English-word-with-Python/31374
    """
    if (word == spell.correction(word)):
        return True
    else:
        return False

def update_keyboard(data):
    """
    Updates keyboard accepts game_dict and returns dict of all keys on keyboard with
    their respected color as either "", "R", "Y", or "G"
    """
    keyboard_state = {
        "A": "",
        "B": "",
        "C": "",
        "D": "",
        "E": "",
        "F": "",
        "G": "",
        "H": "",
        "I": "",
        "J": "",
        "K": "",
        "L": "",
        "M": "",
        "N": "",
        "O": "",
        "P": "",
        "Q": "",
        "R": "",
        "S": "",
        "T": "",
        "U": "",
        "V": "",
        "W": "",
        "X": "",
        "Y": "",
        "Z": "",
    }
    if (not data.get("attempts")):
        return keyboard_state

    attempts_list = data.get("attempts")
    for attempt in attempts_list:
        guess = attempt.get("guess")
        correctness = attempt.get("correctness")
        for i in range(5):
            if (keyboard_state[guess[i]] == GREEN_HEX):
                # if something is already green we want to keep it green
                continue
            if (keyboard_state[guess[i]] == YELLOW_HEX and correctness[i] != GREEN_HEX):
                # only want to change when it's green
                continue

            if (correctness[i] == "R"):
                keyboard_state[guess[i]] = RED_HEX
            elif (correctness[i] == "Y"):
                keyboard_state[guess[i]] = YELLOW_HEX
            elif (correctness[i] == "G"):
                keyboard_state[guess[i]] = GREEN_HEX

    return keyboard_state

def guess(data):
    """ This will do the guess function by updating the game_dict dictionary
        will extract the guess, append a correctness key to the current guess
        that will consist of a string of the form RGY
            R: That letter is not in the word
            Y: That letter is in the word but not in the correct position
            G: That letter is in the correct position
        The size of the attempts list keeps track of how many attempts
        On the first guess for example, the game_dict input will look something like this
            {
                "word" : 0,
                "attempts" :
                [
                    {
                        "guess" : "CHECK"
                    }
                ]
            }
        and the guess function will send this back to client
            {
                "word" : 0,
                "attempts" :
                [
                    {
                        "guess" : "CHECK",
                        "correctness" : "RYYRR"
                    }
                ]
            }
    """

    ##########################################################################################
    # Parse Data
    ##########################################################################################

    game_dict = data # gets data and puts into dictionary
    temp_attempts_list = game_dict.get("attempts")

    if (len(temp_attempts_list) < 1):
        raise SystemError("Attempts list failed to create a guess and the size is below 1")

    correct_word = WORDS[game_dict.get("word")]
    print(correct_word) # FIXME
    correct_word_list = [x for x in correct_word]

    curr_guess_dict = temp_attempts_list[len(temp_attempts_list) - 1]
    curr_guess_word = curr_guess_dict.get("guess") #FIXME make sure words are capitalized
    curr_guess_word_list = [x for x in curr_guess_word] # each element is letter in word

    if (not check_word(curr_guess_word)): # checks if word is a real word
        raise ValueError("Guess word must be a real word")

    if (len(curr_guess_word_list) != 5):
        raise IndexError("Guess word is not of length 5")

    ##########################################################################################
    # Check Guess
    ##########################################################################################

    correctness_list = ['', '', '', '', '']

    # first pass get rid of all matches and R letters
    for i in range(5):
        if (correct_word_list[i] == curr_guess_word_list[i]):
            correct_word_list[i] = "1" # make sure we write different things to guess and correct
            curr_guess_word_list[i] = "0"
            correctness_list[i] = "G"
        elif (correct_word_list.count(curr_guess_word_list[i]) == 0):
            correctness_list[i] = "R"

    # second pass to handle all letters in word but not in correct spot
    for i in range(5):
        try:
            if (correctness_list[i] != ''): # skip if we have already written G/R in that spot
                continue

            index_in_word = correct_word_list.index(curr_guess_word_list[i]) # throws value error if not in list

            curr_guess_word_list[i] = "2"
            correct_word_list[index_in_word] = "3"
            correctness_list[i] = "Y"
        except ValueError: # catches when letter is not in list anymore
            correctness_list[i] = "R"
            continue

    curr_guess_dict["correctness"] = ''.join(correctness_list)

    ##########################################################################################

    # check correctness
    if ("".join(correctness_list) == "GGGGG"):
        return None

    # check attempt limit
    if (len(temp_attempts_list) >= 6):
        return correct_word

    # back to json and return
    return game_dict

@app.route("/test")
def test():
    return render_template("gamepage.html")

@app.route("/game")
def game():
    word_index = randint(0, len(WORDS)-1) # gets random word from WORDS
    game_dict = {
        'word' : word_index,
        'attempts' : []
    }

    keyboard_status = update_keyboard(game_dict)

    return render_template("gamepage.html", game_dict=game_dict, keyboard_colors=keyboard_status)

@app.route("/game/guess_html", methods = ['POST'])
def doGuess():
    new_guess_list = []
    data = None
    error = None
    for key, val in request.form.items():
        if (key.startswith("game_json")):
            data = json.loads(val)
        if (key.startswith("guess")):
            new_guess_list.append(val)

    if (data is None):
        raise RuntimeError("game data is empty")
    game_dict = data

    new_word = ''.join(new_guess_list)
    attempts_list = data.get("attempts")
    attempts_list.append({"guess" : new_word})

    try:
        game_dict = guess(data)
    except ValueError as e:
        error = e
        game_dict['attempts'] = attempts_list[:-1]
    except IndexError as e:
        error = e
        game_dict['attempts'] = attempts_list[:-1]
    except SystemError as e:
        return render_template("failed.html")

    if (game_dict == "success"):
        # i love python able to return strings and dictionaries in same function LOL
        return render_template("succeeded.html")
    if (isinstance(game_dict, str)):
        # python bruh moment fr
        return render_template("failed.html", correct_word=game_dict)

    keyboard_status = update_keyboard(game_dict)

    return render_template("gamepage.html", game_dict=game_dict, keyboard_colors=keyboard_status, error_message=error)

