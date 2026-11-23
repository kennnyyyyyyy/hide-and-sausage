# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  reactions.py - what each AI dog SAYS when something happens in the game.
#  (The "here's why I threw there" lines are in agents.py, this file is just
#  the trash talk.) {dog} gets swapped for a dog's name, and {cell} for a
#  square like "E5".
# =============================================================================

import random

REACTIONS = {
    "pupper": {
        "start":        ["hi!! i'm pupper!! what are we doing", "is this the fetch game??"],
        "ai_hit":       ["BORK!! i did a thing!!", "wait i found one?? :D"],
        "ai_miss":      ["ball go bye bye", "where did the ball go", "oops"],
        "ai_found":     ["i found {dog}!! best day ever!!"],
        "player_hit":   ["hey that's my friend!!", "BORK? who borked"],
        "player_miss":  ["haha grass", "you missed! i think? yay?"],
        "player_found": ["noooo not {dog} :(", "{dog} come back!!"],
        "ai_win":       ["I WON?? what did i win?? is it a treat"],
        "ai_lose":      ["good game!! can we play fetch now"],
    },
    "good_boy": {
        "start":        ["let's play!! i'm a good boy and i'm READY", "ball ball ball ball"],
        "ai_hit":       ["BORK! sniffing all around it now!", "found the scent!!"],
        "ai_miss":      ["no dog there. next sniff!", "hmm, just grass."],
        "ai_found":     ["got {dog}! am i a good boy? i'm a good boy."],
        "player_hit":   ["eep! you found part of one!", "nice throw... for a human."],
        "player_miss":  ["missed! my pack is hiding well.", "nope! keep trying!"],
        "player_found": ["aww, {dog} got found.", "{dog}! you were supposed to stay hidden!"],
        "ai_win":       ["I WIN! treats for everyone! (mostly me)"],
        "ai_lose":      ["you're a good human. GG!"],
    },
    "dogfather": {
        "start":        ["you come to my garden... on the day of my nap?",
                         "let's play. I already know where you hid them."],
        "ai_hit":       ["BORK. nothing personal, kid.", "found one of your boys."],
        "ai_miss":      ["...that was a warning shot.", "the grass talks. I'm listening."],
        "ai_found":     ["{dog} sleeps with the fishes now.",
                         "I made {dog} an offer he couldn't refuse."],
        "player_hit":   ["you touched one of my family.", "...lucky."],
        "player_miss":  ["heh. nothing there but grass, kid.", "you're throwing blind."],
        "player_found": ["{dog}!! you'll pay for this.", "you found {dog}. that was a mistake."],
        "ai_win":       ["the family always wins. remember that."],
        "ai_lose":      ["...respect. you're one of us now."],
    },
}


# -----------------------------------------------------------------------------
# react - picks a random line for something that just happened and fills in
# the blanks. If we don't know the AI we use Good Boy's lines, and if we
# don't know the event it just says "...".
#   agent_key : which AI dog is talking
#   event     : what just happened, like "ai_hit" or "player_found"
#   rng       : the random number maker we pick the line with
#   **details : the words to fill in the blanks, like dog="Big Frank"
# Gives back the finished line.
# -----------------------------------------------------------------------------
def react(agent_key, event, rng=random, **details):
    lines = REACTIONS.get(agent_key, REACTIONS["good_boy"]).get(event, ["..."])
    return rng.choice(lines).format(**details)
