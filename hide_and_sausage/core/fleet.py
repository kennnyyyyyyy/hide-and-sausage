# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  fleet.py - the pack of dachshunds (our "ships") and their shapes.
#
#  Every dog is just a bunch of grid squares, and a square is a (row, col)
#  pair. Dogs can be turned and flipped, so this file works out every way
#  each dog can face and every spot it could lie on the lawn. The AI uses
#  these lists a LOT: "how many ways could Big Frank be lying across E5?" is
#  pretty much just looking it up in the tables we build here.
# =============================================================================

from dataclasses import dataclass

from hide_and_sausage.config import BOARD_SIZE


# -----------------------------------------------------------------------------
# DogType - describes one dog in the pack.
#   key         : a short id we use in the code, like "big_frank"
#   name        : the name players see, like "Big Frank"
#   base_cells  : the dog's shape in its normal pose (head pointing right)
#   blurb       : a silly one-liner we show on screen
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DogType:
    key: str
    name: str
    base_cells: tuple
    blurb: str

    # -------------------------------------------------------------------------
    # size - how many lawn squares this dog takes up (kind of like its
    # "health", since each square needs one hit).
    #   (no parameters)
    # Gives back the number of squares.
    # -------------------------------------------------------------------------
    @property
    def size(self):
        return len(self.base_cells)


# The whole pack. The straight dogs are 1 square tall, Boomerang is an L
# shape and Donut is a 2 x 2 curled-up sleeper. That's 22 squares of dog on
# a 100-square lawn.
PACK = (
    DogType("nugget", "Nugget", ((0, 0), (0, 1)),
            "A tiny puppy. Mostly ears."),
    DogType("bean", "Bean", ((0, 0), (0, 1), (0, 2)),
            "Small, round, suspicious."),
    DogType("long_boi", "Long Boi", ((0, 0), (0, 1), (0, 2), (0, 3)),
            "Long. Boi. That's it."),
    DogType("big_frank", "Big Frank", ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
            "An absolute unit of a sausage."),
    DogType("boomerang", "Boomerang", ((0, 0), (0, 1), (0, 2), (1, 2)),
            "Bent in half mid-nap. Somehow comfy."),
    DogType("donut", "Donut", ((0, 0), (0, 1), (1, 0), (1, 1)),
            "Curled into a perfect sleepy circle."),
)

# Quick lookup: key -> DogType
DOG_BY_KEY = {dog.key: dog for dog in PACK}

# How many lawn squares the whole pack takes up (22). You win after 22 hits.
TOTAL_DOG_CELLS = sum(dog.size for dog in PACK)


# -----------------------------------------------------------------------------
# Transform - one way of turning and/or flipping a dog.
#   quarter_turns : how many 90-degree CLOCKWISE turns (0, 1, 2 or 3)
#   mirrored      : True if we flip the dog left-to-right BEFORE turning it
# The screen turns the dog's picture in exactly the same way, so the drawing
# always lines up with the squares the game thinks the dog is on.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Transform:
    quarter_turns: int
    mirrored: bool


# All 8 possible transforms (4 rotations, each with or without a mirror).
ALL_TRANSFORMS = tuple(Transform(turns, mirror)
                       for mirror in (False, True)
                       for turns in range(4))


# -----------------------------------------------------------------------------
# normalise_cells - slides a shape over so its top-left corner sits at (0, 0).
#   cells : the shape's (row, col) squares, in any kind of list
# Gives back the squares sorted in a tuple, so two shapes that look the same
# always count as equal.
# -----------------------------------------------------------------------------
def normalise_cells(cells):
    cells = list(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


# -----------------------------------------------------------------------------
# transform_cells - flips and/or turns a shape.
#   cells     : the shape's (row, col) squares
#   transform : how to turn/flip it
# Turning 90 degrees clockwise on screen just moves (row, col) to
# (col, -row). After that we slide it back to (0, 0) and give it back.
# -----------------------------------------------------------------------------
def transform_cells(cells, transform):
    result = []
    for row, col in cells:
        if transform.mirrored:
            col = -col
        for _ in range(transform.quarter_turns):
            row, col = col, -row
        result.append((row, col))
    return normalise_cells(result)


# -----------------------------------------------------------------------------
# shape_for - works out which squares a dog covers when it's turned a
# certain way, with its top-left corner at (0, 0).
#   dog       : which dog
#   transform : how the dog is turned/flipped
# Gives back the shape's squares.
# -----------------------------------------------------------------------------
def shape_for(dog, transform):
    return transform_cells(dog.base_cells, transform)


# -----------------------------------------------------------------------------
# unique_shapes - lists every DIFFERENT outline a dog can make.
#   dog : which dog
# A straight dog only really has 2 outlines (across and down), even though
# there are 8 ways to turn/flip it. The AI has to count each outline once,
# or else it would think straight dogs are 4x more likely than they are.
# Gives back a list of (shape_cells, transform) pairs.
# -----------------------------------------------------------------------------
def unique_shapes(dog):
    seen = set()
    shapes = []
    for transform in ALL_TRANSFORMS:
        shape = shape_for(dog, transform)
        if shape not in seen:
            seen.add(shape)
            shapes.append((shape, transform))
    return shapes


# -----------------------------------------------------------------------------
# Placement - one exact spot a dog could be lying in.
#   dog_key   : which dog
#   cells     : the (row, col) squares it covers
#   transform : how its picture needs to be turned/flipped to match
#   anchor    : the (row, col) of the top-left corner of the box around it
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Placement:
    dog_key: str
    cells: frozenset
    transform: Transform
    anchor: tuple


# -----------------------------------------------------------------------------
# place_shape - slides a shape to a square on the lawn and makes a Placement
# out of it.
#   dog_key   : which dog
#   shape     : the shape's squares, already slid to (0, 0)
#   transform : the turn/flip that made this shape
#   anchor    : the (row, col) where the shape's top-left corner goes
# Gives back the Placement, or None if any bit of the dog would hang off
# the lawn.
# -----------------------------------------------------------------------------
def place_shape(dog_key, shape, transform, anchor):
    anchor_row, anchor_col = anchor
    cells = frozenset((anchor_row + row, anchor_col + col) for row, col in shape)
    for row, col in cells:
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None
    return Placement(dog_key, cells, transform, anchor)


# -----------------------------------------------------------------------------
# build_placement_table - lists EVERY spot each dog could fit on an empty
# lawn. We only build it once at the start, then the AI just filters it
# every turn.
#   (no parameters)
# Gives back, for each dog, its list of Placements (each outline counted
# once).
# -----------------------------------------------------------------------------
def build_placement_table():
    table = {}
    for dog in PACK:
        placements = []
        for shape, transform in unique_shapes(dog):
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    placement = place_shape(dog.key, shape, transform, (row, col))
                    if placement is not None:
                        placements.append(placement)
        table[dog.key] = placements
    return table


# Gets built once when this file is loaded (a few thousand spots, super quick).
PLACEMENT_TABLE = build_placement_table()
