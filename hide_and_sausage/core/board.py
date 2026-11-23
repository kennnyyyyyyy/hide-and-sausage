# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  board.py - the rules of the game.
#
#  There are two really different things in here:
#    * Garden    - the TRUTH: where one player's dogs are actually hiding.
#    * Knowledge - what the OTHER player has figured out about that garden
#                  from the balls they threw (misses, BORKs, found dogs).
#  The AI only ever gets the Knowledge, never the Garden, so there's just
#  no way for it to cheat and peek.
# =============================================================================

import random
from dataclasses import dataclass, field

from hide_and_sausage.config import BOARD_SIZE, ROW_LABELS
from hide_and_sausage.core.fleet import (PACK, DOG_BY_KEY, PLACEMENT_TABLE,
                                         TOTAL_DOG_CELLS)

# What a square looks like to the player throwing balls at it
UNKNOWN = 0      # never thrown at
MISS = 1         # ball landed on empty grass
HIT = 2          # BORK! part of a dog, but the dog is not fully found yet
FOUND = 3        # part of a dog that has been completely found


# -----------------------------------------------------------------------------
# cell_name - turns a (row, col) into the label you see on screen, like "E5".
#   cell : the (row, col) square, counting from 0
# Gives back the label as text.
# -----------------------------------------------------------------------------
def cell_name(cell):
    row, col = cell
    return f"{ROW_LABELS[row]}{col + 1}"


# -----------------------------------------------------------------------------
# all_cells - lists every square on the lawn, going from top-left to
# bottom-right.
#   (no parameters)
# Gives back the list of (row, col) squares.
# -----------------------------------------------------------------------------
def all_cells():
    return [(row, col) for row in range(BOARD_SIZE) for col in range(BOARD_SIZE)]


# -----------------------------------------------------------------------------
# neighbours - finds the squares right above, below, left and right of a
# square, skipping any that would fall off the lawn.
#   cell : the (row, col) square in the middle
# Gives back the list of neighbour squares.
# -----------------------------------------------------------------------------
def neighbours(cell):
    row, col = cell
    result = []
    for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        n_row, n_col = row + d_row, col + d_col
        if 0 <= n_row < BOARD_SIZE and 0 <= n_col < BOARD_SIZE:
            result.append((n_row, n_col))
    return result


# -----------------------------------------------------------------------------
# ShotOutcome - what happened when one ball got thrown.
#   cell      : the (row, col) square the ball was thrown at
#   result    : MISS, HIT or FOUND
#   dog_key   : which dog got fully found (only filled in when it's FOUND)
#   dog_cells : all the squares of that found dog (only when it's FOUND)
#   game_over : True if that ball found the last dog in the garden
# -----------------------------------------------------------------------------
@dataclass
class ShotOutcome:
    cell: tuple
    result: int
    dog_key: str = None
    dog_cells: frozenset = None
    game_over: bool = False


# =============================================================================
# Garden - the real hiding spots of one player's dogs.
# =============================================================================
class Garden:

    # -------------------------------------------------------------------------
    # __init__ - sets up an empty garden with no dogs in it yet.
    #   (no parameters)
    #   self.placements : for each hidden dog, where it's lying
    #   self.cell_owner : for each square, which dog is on it, so we can check
    #                     "is there a dog here?" really fast
    #   self.hits_taken : for each dog, which of its squares got hit already
    #   self.thrown_at  : every square the other player has thrown at
    # -------------------------------------------------------------------------
    def __init__(self):
        self.placements = {}
        self.cell_owner = {}
        self.hits_taken = {dog.key: set() for dog in PACK}
        self.thrown_at = set()

    # -------------------------------------------------------------------------
    # can_place - checks that a dog put here wouldn't land on another dog.
    #   placement  : the dog position we want to try
    #   ignore_key : a dog we don't count (when you drag a dog to a new spot,
    #                it shouldn't bump into where it used to be)
    # Gives back True if it fits, False if it overlaps.
    # -------------------------------------------------------------------------
    def can_place(self, placement, ignore_key=None):
        for cell in placement.cells:
            owner = self.cell_owner.get(cell)
            if owner is not None and owner != ignore_key:
                return False
        return True

    # -------------------------------------------------------------------------
    # place - hides a dog here. If that dog was already somewhere else, we
    # move it.
    #   placement : where the dog should go (which dog and which squares)
    # Gives back True if it worked, False if it would land on another dog.
    # -------------------------------------------------------------------------
    def place(self, placement):
        if not self.can_place(placement, ignore_key=placement.dog_key):
            return False
        self.remove(placement.dog_key)
        self.placements[placement.dog_key] = placement
        for cell in placement.cells:
            self.cell_owner[cell] = placement.dog_key
        return True

    # -------------------------------------------------------------------------
    # remove - takes a dog off the lawn. If it isn't on the lawn, nothing
    # happens.
    #   dog_key : which dog to take off
    # -------------------------------------------------------------------------
    def remove(self, dog_key):
        old = self.placements.pop(dog_key, None)
        if old is not None:
            for cell in old.cells:
                self.cell_owner.pop(cell, None)

    # -------------------------------------------------------------------------
    # is_complete - checks if every dog in the pack has been hidden yet.
    #   (no parameters)
    # Gives back True once they're all in the garden.
    # -------------------------------------------------------------------------
    def is_complete(self):
        return len(self.placements) == len(PACK)

    # -------------------------------------------------------------------------
    # scatter_randomly - clears the garden, then hides every dog in a random
    # spot where it fits.
    #   rng : the random number maker to use, so tests and tournaments can
    #         come out the same every time (we make a new one if it's None)
    # The big dogs go first, since they're the hardest to squeeze in.
    # -------------------------------------------------------------------------
    def scatter_randomly(self, rng=None):
        rng = rng or random.Random()
        self.__init__()
        for dog in sorted(PACK, key=lambda d: -d.size):
            options = [p for p in PLACEMENT_TABLE[dog.key] if self.can_place(p)]
            self.place(rng.choice(options))

    # -------------------------------------------------------------------------
    # receive_ball - the other player throws a ball at one square, and we
    # work out if it's a miss, a BORK, or the last bit of a dog (FOUND).
    #   cell : the (row, col) square the ball lands on
    # Gives back a ShotOutcome. You can't throw at the same square twice, it
    # raises an error if you try.
    # -------------------------------------------------------------------------
    def receive_ball(self, cell):
        if cell in self.thrown_at:
            raise ValueError(f"{cell_name(cell)} was already thrown at")
        self.thrown_at.add(cell)

        owner = self.cell_owner.get(cell)
        if owner is None:
            return ShotOutcome(cell, MISS)

        self.hits_taken[owner].add(cell)
        dog_cells = self.placements[owner].cells
        if self.hits_taken[owner] == set(dog_cells):
            return ShotOutcome(cell, FOUND, owner, dog_cells, self.all_found())
        return ShotOutcome(cell, HIT)

    # -------------------------------------------------------------------------
    # all_found - checks if every square of every dog has been hit.
    #   (no parameters)
    # Gives back True when the whole pack is found.
    # -------------------------------------------------------------------------
    def all_found(self):
        hits = sum(len(cells) for cells in self.hits_taken.values())
        return hits == TOTAL_DOG_CELLS

    # -------------------------------------------------------------------------
    # dog_found - checks if one dog has been fully found (all its squares hit).
    #   dog_key : which dog to check
    # Gives back True or False.
    # -------------------------------------------------------------------------
    def dog_found(self, dog_key):
        placement = self.placements.get(dog_key)
        return placement is not None and self.hits_taken[dog_key] == set(placement.cells)


# =============================================================================
# Knowledge - everything a player has figured out about the other garden.
# This is the ONLY thing the AI gets to look at.
# =============================================================================
@dataclass
class Knowledge:
    grid: list = field(default_factory=lambda: [[UNKNOWN] * BOARD_SIZE
                                                for _ in range(BOARD_SIZE)])
    found_dogs: dict = field(default_factory=dict)   # dog_key -> frozenset cells
    shots: list = field(default_factory=list)        # ShotOutcomes in order

    # -------------------------------------------------------------------------
    # record - writes down what we learned after a ball lands.
    #   outcome : what happened with that ball (the garden tells us this)
    # When a dog gets fully found, all of its squares get marked FOUND.
    # -------------------------------------------------------------------------
    def record(self, outcome):
        row, col = outcome.cell
        self.shots.append(outcome)
        if outcome.result == MISS:
            self.grid[row][col] = MISS
        elif outcome.result == HIT:
            self.grid[row][col] = HIT
        else:
            # A found dog: all its squares become FOUND (they were HIT before)
            self.found_dogs[outcome.dog_key] = outcome.dog_cells
            for d_row, d_col in outcome.dog_cells:
                self.grid[d_row][d_col] = FOUND

    # -------------------------------------------------------------------------
    # state_of - tells you what we know about one square.
    #   cell : the (row, col) square to look up
    # Gives back UNKNOWN, MISS, HIT or FOUND.
    # -------------------------------------------------------------------------
    def state_of(self, cell):
        return self.grid[cell[0]][cell[1]]

    # -------------------------------------------------------------------------
    # unknown_cells - lists the squares nobody has thrown at yet.
    #   (no parameters)
    # Gives back a list of (row, col) squares.
    # -------------------------------------------------------------------------
    def unknown_cells(self):
        return [cell for cell in all_cells() if self.state_of(cell) == UNKNOWN]

    # -------------------------------------------------------------------------
    # open_hits - lists the squares that went BORK but whose dog we haven't
    # fully found yet. These are the best clues on the board.
    #   (no parameters)
    # Gives back a list of (row, col) squares.
    # -------------------------------------------------------------------------
    def open_hits(self):
        return [cell for cell in all_cells() if self.state_of(cell) == HIT]

    # -------------------------------------------------------------------------
    # hidden_dogs - lists the dogs that are still hiding out there somewhere.
    #   (no parameters)
    # Gives back a list of dog types.
    # -------------------------------------------------------------------------
    def hidden_dogs(self):
        return [dog for dog in PACK if dog.key not in self.found_dogs]

    # -------------------------------------------------------------------------
    # hits_so_far - counts how many dog squares we've hit so far (you need
    # all 22 to win).
    #   (no parameters)
    # Gives back the count.
    # -------------------------------------------------------------------------
    def hits_so_far(self):
        return sum(1 for shot in self.shots if shot.result != MISS)

    # -------------------------------------------------------------------------
    # copy - makes a separate copy of what we know, so the AI can play
    # "what if" with future throws without messing up the real thing.
    #   (no parameters)
    # Gives back the new Knowledge.
    # -------------------------------------------------------------------------
    def copy(self):
        return Knowledge([row[:] for row in self.grid],
                         dict(self.found_dogs), list(self.shots))


# Re-exported so other modules can say board.DOG_BY_KEY
__all__ = ["UNKNOWN", "MISS", "HIT", "FOUND", "Garden", "Knowledge",
           "ShotOutcome", "cell_name", "all_cells", "neighbours", "DOG_BY_KEY"]
