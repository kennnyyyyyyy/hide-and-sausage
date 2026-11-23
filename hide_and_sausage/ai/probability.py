# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  probability.py - "where could the dogs be?"
#
#  The whole idea is just COUNTING. For every dog that's still hiding, we
#  look at every spot it could be lying in (not on a miss, and not on top of
#  a dog we already found). If lots of those spots go over a square, there's
#  probably a dog there. If hardly any do, there probably isn't.
#
#  Two functions use this idea:
#    placement_heatmap       - the raw counts ("heat"), used for the Hint
#                              button and when the Dogfather hides its dogs
#    placement_probabilities - the counts turned into real percentages,
#                              used by The Dogfather and the brain view
# =============================================================================

from hide_and_sausage.config import BOARD_SIZE
from hide_and_sausage.core.board import UNKNOWN, MISS, HIT, FOUND
from hide_and_sausage.core.fleet import PLACEMENT_TABLE

# How much extra a dog position counts when it sits on a BORK we already got.
# A position that explains a BORK is WAY more likely than one in empty grass,
# and one that covers two BORKs counts 40 x 40 = 1600 times more.
HIT_BONUS = 40


# -----------------------------------------------------------------------------
# empty_grid - makes a fresh board-sized grid with the same number in every
# square.
#   value : the number every square starts with (0.0 if you don't say)
# Gives back the new grid.
# -----------------------------------------------------------------------------
def empty_grid(value=0.0):
    return [[value] * BOARD_SIZE for _ in range(BOARD_SIZE)]


# -----------------------------------------------------------------------------
# possible_placements - lists every spot where this dog could still be hiding.
#   knowledge : everything we've seen so far (misses, BORKs, found dogs)
#   dog       : which dog we're looking for
# A dog can't be lying on a square we already missed, and it can't be on top
# of a dog we already found, so those spots get thrown out.
# Gives back the list of spots that are still possible.
# -----------------------------------------------------------------------------
def possible_placements(knowledge, dog):
    result = []
    for placement in PLACEMENT_TABLE[dog.key]:
        allowed = True
        for row, col in placement.cells:
            if knowledge.grid[row][col] in (MISS, FOUND):
                allowed = False
                break
        if allowed:
            result.append(placement)
    return result


# -----------------------------------------------------------------------------
# placement_weight - how likely this one dog position is, compared to others.
#   knowledge : everything we've seen so far (misses, BORKs, found dogs)
#   placement : the dog position we're checking
# Normally every position just counts as 1. But if there's an open BORK (we
# hit a dog but haven't found all of it yet), a position that covers k BORKs
# counts as 40^k, because it explains what we've seen.
# Gives back the weight as a number.
# -----------------------------------------------------------------------------
def placement_weight(knowledge, placement):
    if not knowledge.open_hits():
        return 1
    hits_covered = 0
    for row, col in placement.cells:
        if knowledge.grid[row][col] == HIT:
            hits_covered += 1
    return HIT_BONUS ** hits_covered


# -----------------------------------------------------------------------------
# placement_heatmap - the classic heat map. For each square, we add up the
# weights of every possible dog position that goes over it. Bigger number
# means more likely to have a dog.
#   knowledge : everything we've seen so far (misses, BORKs, found dogs)
# Gives back heat[row][col] (squares we already threw at stay at 0).
# -----------------------------------------------------------------------------
def placement_heatmap(knowledge):
    heat = empty_grid()
    for dog in knowledge.hidden_dogs():
        for placement in possible_placements(knowledge, dog):
            weight = placement_weight(knowledge, placement)
            for row, col in placement.cells:
                if knowledge.grid[row][col] == UNKNOWN:
                    heat[row][col] += weight
    return heat


# -----------------------------------------------------------------------------
# placement_probabilities - turns the counting into real percentages.
#   knowledge : everything we've seen so far (misses, BORKs, found dogs)
#
# For ONE dog, the chance it's lying on a square is:
#       (weight of its positions covering the square) / (weight of all its positions)
# A square is only empty if NONE of the hidden dogs are on it, so:
#       P(dog on square) = 1 - (1 - P_dog1) x (1 - P_dog2) x ... x (1 - P_dog6)
# Gives back probs[row][col], each between 0 and 1 (squares we already threw
# at stay at 0).
# -----------------------------------------------------------------------------
def placement_probabilities(knowledge):
    chance_empty = empty_grid(1.0)           # chance that NO dog covers it
    for dog in knowledge.hidden_dogs():
        coverage = empty_grid()
        total = 0.0
        for placement in possible_placements(knowledge, dog):
            weight = placement_weight(knowledge, placement)
            total += weight
            for row, col in placement.cells:
                coverage[row][col] += weight
        if total == 0:
            continue
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                chance_empty[row][col] *= 1 - coverage[row][col] / total

    probs = empty_grid()
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if knowledge.grid[row][col] == UNKNOWN:
                probs[row][col] = 1 - chance_empty[row][col]
    return probs


# -----------------------------------------------------------------------------
# chance_text - writes a chance as a percentage for the screen, WITHOUT lying.
#   p : the chance, between 0 and 1
# Normal rounding would show 99.6% as "100%" and 0.3% as "0%", which sounds
# certain when it isn't. So "100%" only appears when the chance is exactly 1
# (every ghost of some dog covers the square, so a dog really IS there), and
# "0%" only when it's exactly 0 (no ghost covers it at all). Anything in
# between is kept to 1%..99%.
# Gives back the text, like "84%".
# -----------------------------------------------------------------------------
def chance_text(p):
    if p >= 1:
        return "100%"
    if p <= 0:
        return "0%"
    return f"{min(99, max(1, round(p * 100)))}%"


# -----------------------------------------------------------------------------
# normalise_for_display - squishes a grid down to 0..1 so the screen can
# colour it. We just divide everything by the biggest number.
#   grid : the grid of numbers to squish
# Gives back the new 0..1 grid (all zeros if there was nothing above 0).
# -----------------------------------------------------------------------------
def normalise_for_display(grid):
    biggest = max(max(row) for row in grid)
    if biggest <= 0:
        return empty_grid()
    return [[value / biggest for value in row] for row in grid]
