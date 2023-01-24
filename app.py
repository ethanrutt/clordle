import json
import re
from spellchecker import SpellChecker
from flask import Flask, request, jsonify, render_template
from random import randint

app = Flask(__name__)

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

    game_dict = data # gets data and puts into dictionary #FIXME potentially take out json.loads
    #g = request.get_json() #FIXME do I want application/JSON only in header or do I want to accept all text?
    correct_word = WORDS[game_dict.get("word")] 
    correct_word_list = [x for x in correct_word]
    temp_attempts_list = game_dict.get("attempts")

    if (len(temp_attempts_list) < 1):
        raise Exception("Attempts list failed to create a guess and the size is below 1")

    curr_guess_dict = temp_attempts_list[len(temp_attempts_list) - 1]
    curr_guess_word = curr_guess_dict.get("guess") #FIXME make sure words are capitalized
    curr_guess_word_list = [x for x in curr_guess_word] # each element is letter in word

    if (not check_word(curr_guess_word)): # checks if word is a real word
        raise Exception("Guess word must be a real word")

    if (len(curr_guess_word_list) != 5):
        raise Exception("Guess word is not of length 5")

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
    if (correctness_list == "GGGGG"):
        return render_template("succeeded.html")

    # check attempt limit
    if (len(temp_attempts_list) >= 6):
        return render_template("failed.html")
    
    # back to json and return
    return game_dict

@app.route("/test")
def test():
    return render_template("gamepage.html")

@app.route("/game")
def game():
    word_index = randint(0, len(WORDS)-1) # gets random word from WORDS
    game_dict = {'word' : word_index,
                 'attempts' : []
                 }
    
    #return jsonify(game_dict)
    return render_template("gamepage.html", game_dict=game_dict)

@app.route("/game/guess_html", methods = ['POST'])
def doGuess():
    print("request.forms:", request.form)
    # FIXME
    # .join guess1-5, let's call it guess_word
    # pull game_json, convert to python dict
    new_guess_list = []
    for key, val in request.form.items():
        if (key.startswith("game_json")):
            print(val)
            data = json.loads(val)
        if (key.startswith("guess")):
            new_guess_list.append(val)
        
    new_word = ''.join(new_guess_list)
    attempts_list = data.get("attempts")
    attempts_list.append({"guess" : new_word})
    # add guess_word to python dict of game_json, let's call it data
    # call guess on data
    game_dict = guess(data)
    return render_template("gamepage.html", game_dict=game_dict)