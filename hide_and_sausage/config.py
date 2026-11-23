# =============================================================================
#  HIDE & SAUSAGE  -  a Battleship-style game with hidden dachshunds
#  5FTC2067 Artificial Intelligence Principles - Mini Project
#
#  Student Name : Kenzo Jonathan Harapan Ji
#  Student ID   : 4234QLMV
#
#  config.py - all the numbers, colours and folder paths you might want to
#  tweak are kept here, so the rest of the code doesn't have random
#  "magic numbers" hiding in it.
# =============================================================================

import os

# ---------------------------------------------------------------------------
# Who made this (shown on the title screen, the code headers and the report)
# ---------------------------------------------------------------------------
STUDENT_NAME = "Kenzo Jonathan Harapan Ji"
STUDENT_ID = "4234QLMV"
GAME_TITLE = "Hide & Sausage"
GAME_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Board rules
# ---------------------------------------------------------------------------
BOARD_SIZE = 10                      # the garden is a 10 x 10 grid of lawn
ROW_LABELS = "ABCDEFGHIJ"            # rows are letters, columns are numbers

# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)
ASSET_DIR = os.path.join(PROJECT_DIR, "assets")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")

# ---------------------------------------------------------------------------
# Window and layout (everything is drawn on a 1280 x 720 canvas and then
# scaled to the real window, so the game looks the same on every screen)
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
CELL_SIZE = 42                       # pixels per lawn square
BOARD_PIXELS = CELL_SIZE * BOARD_SIZE

# ---------------------------------------------------------------------------
# Colour palette - mostly black and white, like a sketchbook, so the
# hand-drawn dogs are the only really colourful thing on screen
# ---------------------------------------------------------------------------
INK = (30, 30, 30)                   # pen black, used for every outline
INK_SOFT = (95, 95, 95)
PAPER = (250, 249, 245)              # the page behind everything
CREAM = (255, 255, 255)              # panels and buttons are plain white
CREAM_DARK = (225, 224, 219)
BUTTER = (255, 214, 102)             # the one accent: highlighter yellow
TOMATO = (226, 83, 61)
SKY = (215, 225, 238)
GRASS = (240, 241, 235)              # the lawn is just paper with a grid
GRASS_DARK = (196, 196, 190)
CARAMEL = (214, 150, 88)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
HEAT_COLD = (70, 120, 255)           # heat-map colour for "probably empty"
HEAT_HOT = (255, 60, 40)             # heat-map colour for "probably a dog"

# ---------------------------------------------------------------------------
# AI timing - the AI is fast, but we pause so humans can watch it "think"
# ---------------------------------------------------------------------------
AI_THINK_SECONDS = 1.1
EXPECTIMAX_CANDIDATES = 8            # how many top squares get a deep look
