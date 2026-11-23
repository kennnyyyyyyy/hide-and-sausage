# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  agents.py - the three AI dogs you play against, from silly to smart.
#
#   Level | Opponent       | How it plays
#   ------+----------------+---------------------------------------------------
#     1   | Pupper         | Just throws at random (the one to beat)
#     2   | Good Boy       | Hunt / Target: throws at random until it hears a
#         |                | BORK, then sniffs the squares around it
#     3   | The Dogfather  | EXPECTIMAX: counts up where the dogs could be,
#         |                | then thinks about both ways a throw could go
#         |                | (BORK or miss) plus one throw after that. It also
#         |                | hides its own dogs in the hardest spots to find
#
#  Every turn, each AI basically answers one question: "with what I know so
#  far, where should I throw?" It hands back a Decision that also says WHY,
#  so the game can show what the AI is thinking and its heat map live.
# =============================================================================

import math
import random
from dataclasses import dataclass, field

from hide_and_sausage.config import EXPECTIMAX_CANDIDATES
from hide_and_sausage.core.board import (UNKNOWN, MISS, HIT, Garden, Knowledge,
                                         ShotOutcome, cell_name, neighbours)
from hide_and_sausage.core.fleet import TOTAL_DOG_CELLS
from hide_and_sausage.ai.probability import (empty_grid, placement_heatmap,
                                             placement_probabilities,
                                             normalise_for_display, chance_text)


# -----------------------------------------------------------------------------
# Decision - what the AI picked this turn, and WHY it picked it.
#   cell       : the (row, col) square it's going to throw at
#   thought    : a line in the AI's own voice explaining the pick
#   heat       : a grid of 0..1 numbers we draw as the heat map
#   probs      : the real probability grid if the AI worked one out, else None
#   mode       : a short label for the screen, like "HUNTING" or "TARGETING"
#   candidates : the (cell, score) pairs it really thought about, best first
#   stats      : any extra numbers we want to show in the brain panel
# -----------------------------------------------------------------------------
@dataclass
class Decision:
    cell: tuple
    thought: str
    heat: list
    probs: list = None
    mode: str = ""
    candidates: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Situation - who's ahead in the race right now. The Dogfather looks at this
# to see if it has time to plan ahead or needs to hurry up.
#   my_hits        : how many dog squares this AI has hit so far
#   opponent_hits  : how many dog squares the other player has hit so far
#   my_shots       : how many balls this AI has thrown
#   opponent_shots : how many balls the other player has thrown
# -----------------------------------------------------------------------------
@dataclass
class Situation:
    my_hits: int = 0
    opponent_hits: int = 0
    my_shots: int = 0
    opponent_shots: int = 0


# =============================================================================
# Base class - shared by every opponent
# =============================================================================
class Agent:
    key = "base"
    name = "Base Agent"
    title = ""
    level = 0
    method = ""
    bio = ""

    # -------------------------------------------------------------------------
    # __init__ - sets up the AI with its own random number maker.
    #   seed : an optional number, so tournament games come out the same
    #          every time we run them
    # -------------------------------------------------------------------------
    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    # -------------------------------------------------------------------------
    # choose - picks the next square to throw at. This one does nothing on
    # its own, each AI writes its own version.
    #   knowledge : everything this AI has seen in the other garden so far
    #   situation : who's ahead in the race (see Situation)
    # -------------------------------------------------------------------------
    def choose(self, knowledge, situation):
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # hide_dogs - picks where the AI's own dogs hide. By default we just
    # scatter them around at random.
    #   (no parameters)
    # Gives back the Garden with the dogs in it.
    # -------------------------------------------------------------------------
    def hide_dogs(self):
        garden = Garden()
        garden.scatter_randomly(self.rng)
        return garden

    # -------------------------------------------------------------------------
    # pick_best - grabs the square with the best score. If a few squares tie,
    # we pick one of them at random so the AI doesn't get predictable.
    #   scores : each square and its score (bigger is better)
    # Gives back the chosen square.
    # -------------------------------------------------------------------------
    def pick_best(self, scores):
        best = max(scores.values())
        ties = [cell for cell, score in scores.items() if abs(score - best) < 1e-12]
        return self.rng.choice(ties)

    # -------------------------------------------------------------------------
    # flat_heat - makes a boring heat map where every square we haven't
    # thrown at gets the same value. It's for AIs that don't do any maths.
    #   knowledge : everything we've seen so far, so we know which squares
    #               are still untouched
    # Gives back the heat grid.
    # -------------------------------------------------------------------------
    @staticmethod
    def flat_heat(knowledge):
        heat = empty_grid()
        for row, col in knowledge.unknown_cells():
            heat[row][col] = 0.35
        return heat


# =============================================================================
# Level 1 - Pupper: throws at random.  The control group.
# =============================================================================
class PupperAgent(Agent):
    key = "pupper"
    name = "Pupper"
    title = "Level 1 - Random"
    level = 1
    method = "Random throws"
    bio = "Has never had a single thought. Throws wherever the ball wants to go."

    LINES = ("*chases tail* ...uhh, {cell}?",
             "ball go {cell}. weeee",
             "i forgor where the dogs are. {cell}!!",
             "{cell} smells like a tennis ball. throwing there.",
             "is that a squirrel at {cell}??")

    # -------------------------------------------------------------------------
    # choose - picks any square we haven't thrown at yet, totally at random,
    # and says something silly about it.
    #   knowledge : everything Pupper has seen in the other garden so far
    #   situation : not used, Pupper has no idea there's even a race
    # Gives back a Decision.
    # -------------------------------------------------------------------------
    def choose(self, knowledge, situation):
        cell = self.rng.choice(knowledge.unknown_cells())
        thought = self.rng.choice(self.LINES).format(cell=cell_name(cell))
        return Decision(cell, thought, self.flat_heat(knowledge), mode="VIBING")


# =============================================================================
# Level 2 - Good Boy: hunt / target.
# =============================================================================
class GoodBoyAgent(Agent):
    key = "good_boy"
    name = "Good Boy"
    title = "Level 2 - Hunt & Target"
    level = 2
    method = "Hunt randomly, then sniff around every BORK"
    bio = "Fetches. Sniffs. Very proud of himself."

    # -------------------------------------------------------------------------
    # target_cells - after a BORK, works out which squares are worth sniffing
    # next.
    #   knowledge : everything we've seen so far (misses, BORKs, found dogs)
    # Every untouched square next to a BORK (from a dog we haven't finished
    # finding) gets 1 point. If the square on the other side of that BORK is
    # also a BORK, then this square carries on a straight line, so it gets
    # 3 extra points (dogs are long and straight, so lines are a good sign).
    # Gives back each square with its score (bigger = better).
    # -------------------------------------------------------------------------
    @staticmethod
    def target_cells(knowledge):
        hits = knowledge.open_hits()
        scores = {}
        for hit in hits:
            for cell in neighbours(hit):
                if knowledge.state_of(cell) != UNKNOWN:
                    continue
                score = scores.get(cell, 0) + 1
                step_row = cell[0] - hit[0]
                step_col = cell[1] - hit[1]
                behind = (hit[0] - step_row, hit[1] - step_col)
                if behind in hits:
                    score += 3
                scores[cell] = score
        return scores

    # -------------------------------------------------------------------------
    # hunt_cells - the squares to search when there's no BORK to chase.
    #   knowledge : everything we've seen so far, so we know what's untouched
    # Good Boy isn't picky, every untouched square gets the same score of 1.
    # -------------------------------------------------------------------------
    def hunt_cells(self, knowledge):
        return {cell: 1 for cell in knowledge.unknown_cells()}

    # -------------------------------------------------------------------------
    # choose - if there's a BORK to follow, sniff around it. If not, just
    # hunt at random. Also builds the heat map and the top 5 list to show.
    #   knowledge : everything Good Boy has seen in the other garden so far
    #   situation : not used, Good Boy doesn't care who's winning
    # Gives back a Decision.
    # -------------------------------------------------------------------------
    def choose(self, knowledge, situation):
        targets = self.target_cells(knowledge)
        if targets:
            scores = targets
            cell = self.pick_best(scores)
            mode = "TARGETING"
            thought = (f"BORK heard nearby! sniffing {cell_name(cell)} "
                       f"right next to it. good boy behaviour.")
        else:
            scores = self.hunt_cells(knowledge)
            cell = self.pick_best(scores)
            mode = "HUNTING"
            thought = self.hunt_thought(cell)

        heat = empty_grid()
        biggest = max(scores.values())
        for (row, col), score in scores.items():
            heat[row][col] = score / biggest
        ranked = sorted(scores.items(), key=lambda item: -item[1])[:5]
        return Decision(cell, thought, heat, mode=mode, candidates=ranked)

    # -------------------------------------------------------------------------
    # hunt_thought - picks a random line for Good Boy to say while he's just
    # guessing.
    #   cell : the square he picked, so we can name it in the line
    # Gives back the line as text.
    # -------------------------------------------------------------------------
    def hunt_thought(self, cell):
        return self.rng.choice((
            f"no clues yet. {cell_name(cell)} feels lucky!",
            f"sniff sniff... nothing. trying {cell_name(cell)}.",
            f"random sniff at {cell_name(cell)}. i am a good boy."))


# =============================================================================
# Level 3 - The Dogfather: expectimax + adversarial hiding.
# =============================================================================
class DogfatherAgent(Agent):
    key = "dogfather"
    name = "The Dogfather"
    title = "Level 3 - Expectimax"
    level = 3
    method = "Expectimax: weighs BORK and miss for each throw, one throw ahead"
    bio = "Makes you an offer you can't refuse. Plans one throw ahead."

    # gamma is how much the NEXT throw matters compared to this one.
    # gamma 0 = only care about this throw (that's plain "greedy").
    # I tested it on the same 300 gardens (tools/gamma_study.py):
    #   gamma 0 -> 48.8 balls, 0.3 -> 49.0, 0.7 -> 49.0, 1.0 -> 56.4
    # Everything from 0 to 0.7 is a tie (the gaps are smaller than the luck
    # between gardens), but 1.0 is clearly worse: the next throw must count
    # LESS than this one. 0.3 keeps a little look-ahead to break near-ties.
    GAMMA = 0.3

    # -------------------------------------------------------------------------
    # best_next_chance - answers "if this throw went like THIS, how good
    # would my best next throw be?"
    #   knowledge : everything we've seen so far
    #   cell      : the square we're pretending to throw at
    #   result    : how we pretend it went, HIT or MISS
    # We make a copy of what we know, write the pretend result on the copy,
    # count up the chances again, and give back the highest chance left.
    # -------------------------------------------------------------------------
    @staticmethod
    def best_next_chance(knowledge, cell, result):
        imagined = knowledge.copy()
        imagined.record(ShotOutcome(cell, result))
        probs = placement_probabilities(imagined)
        best = 0.0
        for row, col in imagined.unknown_cells():
            best = max(best, probs[row][col])
        return best

    # -------------------------------------------------------------------------
    # expectimax_value - the main brain of the AI. It scores one throw by
    # thinking about BOTH ways it could go:
    #
    #     MAX     (me: pick a square)
    #      |
    #     CHANCE  -> BORK with probability p
    #             -> MISS with probability 1 - p
    #      |
    #     MAX     (me again: my best next square after that)
    #
    #   value = p + gamma * ( p * next_if_hit + (1 - p) * next_if_miss )
    #
    # So basically it's how many BORKs we expect to get over the next two
    # throws (with the second throw counting a bit less).
    #   knowledge : everything we've seen so far
    #   cell      : the square we're thinking about throwing at
    #   p         : the chance there's a dog on this square
    #   gamma     : how much the second throw counts
    # Gives back (value, next_if_hit, next_if_miss).
    # -------------------------------------------------------------------------
    def expectimax_value(self, knowledge, cell, p, gamma):
        next_if_hit = self.best_next_chance(knowledge, cell, HIT)
        next_if_miss = self.best_next_chance(knowledge, cell, MISS)
        value = p + gamma * (p * next_if_hit + (1 - p) * next_if_miss)
        return value, next_if_hit, next_if_miss

    # -------------------------------------------------------------------------
    # choose - how the Dogfather picks one throw, start to finish.
    #   knowledge : everything the Dogfather has seen in the other garden
    #   situation : who's ahead in the race (every AI gets it, this one doesn't need it)
    # 1. work out the chance of a dog on every square
    # 2. keep only the most likely squares (the deep thinking is slow, so
    #    only these get it)
    # 3. score each of those with expectimax
    # 4. throw at the best one and explain why
    # Gives back a Decision with the heat map, top 5 and some stats.
    # -------------------------------------------------------------------------
    def choose(self, knowledge, situation):
        probs = placement_probabilities(knowledge)
        gamma = self.GAMMA

        unknown = knowledge.unknown_cells()
        unknown.sort(key=lambda c: -probs[c[0]][c[1]])
        shortlist = unknown[:EXPECTIMAX_CANDIDATES]

        scores = {}
        details = {}
        for cell in shortlist:
            p = probs[cell[0]][cell[1]]
            value, next_hit, next_miss = self.expectimax_value(knowledge, cell, p, gamma)
            scores[cell] = value
            details[cell] = (p, next_hit, next_miss)

        cell = self.pick_best(scores)
        p, next_hit, next_miss = details[cell]
        ranked = sorted(scores.items(), key=lambda item: -item[1])[:5]
        thought = self.explain(cell, p, next_miss, ranked)

        if knowledge.open_hits():
            mode = "TARGETING"
        else:
            mode = "EXPECTIMAX"
        stats = {"gamma": gamma, "p_hit": p, "next_hit": next_hit, "next_miss": next_miss}
        return Decision(cell, thought, normalise_for_display(probs), probs,
                        mode=mode, candidates=ranked, stats=stats)

    # -------------------------------------------------------------------------
    # explain - turns the numbers into a line the Dogfather would say.
    #   cell      : the square we picked
    #   p         : the chance there's a dog on it
    #   next_miss : how good our next throw still is if this one misses
    #   ranked    : the top squares, so we can name the second best one
    # Gives back the sentence.
    # -------------------------------------------------------------------------
    def explain(self, cell, p, next_miss, ranked):
        sentence = f"{cell_name(cell)}: {chance_text(p)} chance of a dog."
        if len(ranked) > 1:
            runner_up = ranked[1][0]
            return (sentence + f" even if it misses, my next shot is still "
                    f"{chance_text(next_miss)}. better line than {cell_name(runner_up)}.")
        return sentence

    # -------------------------------------------------------------------------
    # hide_dogs - hides the Dogfather's dogs on purpose to be hard to find
    # (this is the "min" side of expectiminimax, playing against the seeker).
    # We try 250 random gardens and score each one. Good ones keep the dogs
    # away from the squares a heat map would check first, and don't let dogs
    # touch each other (if they touch, finding one helps find the other).
    #   (no parameters)
    # Gives back one of the 8 safest gardens, picked at random.
    # -------------------------------------------------------------------------
    def hide_dogs(self):
        start_heat = normalise_for_display(placement_heatmap(Knowledge()))
        options = []
        for _ in range(250):
            garden = Garden()
            garden.scatter_randomly(self.rng)
            options.append((self.layout_risk(garden, start_heat), garden))
        options.sort(key=lambda item: item[0])
        # pick randomly among the 8 safest so the hiding is not predictable
        return self.rng.choice(options[:8])[1]

    # -------------------------------------------------------------------------
    # layout_risk - scores how easy a garden would be to crack.
    #   garden     : the garden (with dogs placed) we're checking
    #   start_heat : the heat map a seeker would start with (0..1 per square)
    # We add up the heat under every dog square, then add 0.5 for every time
    # two different dogs touch. Lower score means a safer hiding spot.
    # -------------------------------------------------------------------------
    @staticmethod
    def layout_risk(garden, start_heat):
        risk = 0.0
        for row, col in garden.cell_owner:
            risk += start_heat[row][col]
        touching = 0
        for cell, owner in garden.cell_owner.items():
            for other_cell in neighbours(cell):
                other = garden.cell_owner.get(other_cell)
                if other is not None and other != owner:
                    touching += 1
        return risk + 0.5 * touching


# All opponents in level order, for menus and tournaments
AGENT_CLASSES = (PupperAgent, GoodBoyAgent, DogfatherAgent)


# -----------------------------------------------------------------------------
# win_chance - the AI's rough gut feeling about who's winning, from 0 to 1.
#   situation : who's ahead in the race, seen from the AI's side
# We guess how many more throws each side needs at the rate they're hitting
# right now, then squish the difference into a 0 to 1 number with a logistic
# (S-shaped) curve. It's only for the confidence bar on screen, it never
# changes what the AI does.
# -----------------------------------------------------------------------------
def win_chance(situation):
    my_left = TOTAL_DOG_CELLS - situation.my_hits
    their_left = TOTAL_DOG_CELLS - situation.opponent_hits
    if my_left == 0:
        return 1.0
    if their_left == 0:
        return 0.0
    # pretend each player starts with 10 throws at a 45% hit rate, so the
    # estimate doesn't jump around after the first few throws
    my_rate = (situation.my_hits + 4.5) / (situation.my_shots + 10)
    their_rate = (situation.opponent_hits + 4.5) / (situation.opponent_shots + 10)
    my_need = my_left / my_rate
    their_need = their_left / their_rate
    return 1 / (1 + math.exp(-(their_need - my_need) / 6))
