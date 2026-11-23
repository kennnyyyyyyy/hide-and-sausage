# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  scenes_menu.py - all the screens you see when you're not in a match:
#    TitleScene     - the logo, the play button, and the credits with my
#                     name and student ID
#    SelectScene    - pick which AI you want to play against (3 of them,
#                     from easy to hard)
#    HowToScene     - the rules, plus a look at every dog in the pack
#    LabScene       - the AI lab: what each AI does, and the results from
#                     the experiments
# =============================================================================

import csv
import importlib.util
import math
import os

import pygame

from hide_and_sausage.config import (SCREEN_WIDTH, SCREEN_HEIGHT, STUDENT_NAME,
                                     STUDENT_ID, GAME_VERSION, INK, INK_SOFT,
                                     CREAM, BUTTER, TOMATO, SKY, WHITE,
                                     PROJECT_DIR, CARAMEL)
from hide_and_sausage.core.fleet import PACK, ALL_TRANSFORMS
from hide_and_sausage.ai.agents import AGENT_CLASSES
from hide_and_sausage.ui.app import Scene
from hide_and_sausage.ui.assets import ASSETS
from hide_and_sausage.ui.widgets import (Button, draw_panel, blit_text,
                                         wrap_text, Particles)

# -----------------------------------------------------------------------------
# has_testing_mode - checks if the Testing Mode file is here. It's only on my
# own copy (I use it to test the Dogfather), not in the handed-in game.
#   (no parameters)
# -----------------------------------------------------------------------------
def has_testing_mode():
    try:
        return importlib.util.find_spec("hide_and_sausage.ui.scenes_testing") is not None
    except (ImportError, ValueError):
        return False


LEVEL_COLOURS = {1: (232, 240, 222), 2: SKY, 3: (250, 222, 214)}   # soft pale colours, like a sketchbook


# =============================================================================
# TitleScene
# =============================================================================
class TitleScene(Scene):

    # -------------------------------------------------------------------------
    # __init__ - sets up the menu buttons (Play, How to play, AI Lab, Quit).
    # Enter also presses Play and Escape presses Quit. Testing Mode is my own
    # private test tool, so its button only shows up on my copy (where the
    # scenes_testing.py file exists). The handed-in game doesn't have it.
    #   app : the game that's running right now
    # -------------------------------------------------------------------------
    def __init__(self, app):
        super().__init__(app)
        x = SCREEN_WIDTH // 2 - 150
        self.buttons = [
            Button((x, 362, 300, 58), "PLAY", lambda: app.switch(SelectScene(app)),
                   BUTTER, 30, pygame.K_RETURN),
            Button((x, 432, 300, 46), "How to play", lambda: app.switch(HowToScene(app)),
                   CREAM, 22),
            Button((x, 488, 300, 46), "AI Lab", lambda: app.switch(LabScene(app)),
                   SKY, 22),
        ]
        y = 544
        if has_testing_mode():
            self.buttons.append(Button((x, y, 300, 46), "Testing Mode", self.open_testing,
                                       (205, 235, 180), 22, pygame.K_t))
            y += 56
        self.buttons.append(Button((x, y, 300, 46), "Quit", app.quit, (240, 170, 160), 22,
                                   pygame.K_ESCAPE))
        self.particles = Particles()
        self.spawn_timer = 0.0

    # -------------------------------------------------------------------------
    # open_testing - opens Testing Mode, the sandbox where you set up any
    # board and watch the Dogfather think through his next throw.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def open_testing(self):
        from hide_and_sausage.ui.scenes_testing import TestingScene
        self.app.switch(TestingScene(self.app))

    # -------------------------------------------------------------------------
    # update - every quarter of a second we drop a new pink petal from the
    # top of the screen, just to make the menu feel a bit alive.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        super().update(dt)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = 0.25
            x = (pygame.time.get_ticks() * 37) % SCREEN_WIDTH
            self.particles.items.append([x, -10, 15, 40, 9, 9, (255, 200, 210), 5, False])
        self.particles.update(dt)

    # -------------------------------------------------------------------------
    # draw - draws the background, the falling petals, the logo bobbing up
    # and down, two dogs peeking in from the corners, the buttons, and the
    # credits and key hints along the edges.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "menu_bg", dim=20)
        self.particles.draw(surface)

        bob = math.sin(self.time * 2.2) * 6
        logo = ASSETS.scaled("logo", 640, 300)
        if logo is not None:
            surface.blit(logo, logo.get_rect(center=(SCREEN_WIDTH // 2, 200 + bob)))
        else:
            blit_text(surface, "HIDE & SAUSAGE", (SCREEN_WIDTH // 2, 190 + bob), 76,
                      BUTTER, 6)
            blit_text(surface, "a battleship game with dachshunds", (SCREEN_WIDTH // 2, 260),
                      24, WHITE, 3)

        # dogs peeking in the corners
        for key, pos, angle in (("big_frank", (150, 600), 12), ("donut", (1130, 610), 0)):
            sprite = ASSETS.scaled(f"dogs/{key}", 230, 140)
            if sprite is not None:
                sprite = pygame.transform.rotate(sprite, angle + math.sin(self.time * 1.5) * 3)
                surface.blit(sprite, sprite.get_rect(center=pos))

        super().draw(surface)
        credit = f"{STUDENT_NAME}  |  {STUDENT_ID}  |  5FTC2067 AI Principles  |  v{GAME_VERSION}"
        blit_text(surface, credit, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 12), 14, WHITE, 2,
                  "semibold", "midbottom")
        blit_text(surface, "M: music   F11: fullscreen", (SCREEN_WIDTH - 12, 12), 13, WHITE, 2,
                  "semibold", "topright")
        blit_text(surface, "Music: Wiener Dog Song (all rights to its creator)",
                  (12, 12), 13, WHITE, 2, "semibold", "topleft")


# =============================================================================
# SelectScene - pick an opponent
# =============================================================================
class SelectScene(Scene):

    CARD_W, CARD_H = 320, 440

    # -------------------------------------------------------------------------
    # __init__ - lines up one card for each AI opponent across the screen,
    # plus a Back button (Escape works too).
    #   app : the game that's running right now
    # -------------------------------------------------------------------------
    def __init__(self, app):
        super().__init__(app)
        self.cards = []
        gap = 40
        total = len(AGENT_CLASSES) * self.CARD_W + (len(AGENT_CLASSES) - 1) * gap
        left = (SCREEN_WIDTH - total) // 2
        for index, agent_class in enumerate(AGENT_CLASSES):
            rect = pygame.Rect(left + index * (self.CARD_W + gap), 150, self.CARD_W, self.CARD_H)
            self.cards.append((rect, agent_class))
        self.hovered = None
        self.buttons = [Button((30, 30, 140, 50), "< Back",
                               lambda: app.switch(TitleScene(app)), CREAM, 20,
                               pygame.K_ESCAPE)]

    # -------------------------------------------------------------------------
    # handle_event - keeps track of which card the mouse is over, and when
    # you click a card it takes you to hiding your dogs against that AI.
    #   event : the mouse or keyboard thing that just happened
    # Gives back True if something used the event.
    # -------------------------------------------------------------------------
    def handle_event(self, event):
        if super().handle_event(event):
            return True
        if event.type == pygame.MOUSEMOTION:
            previous = self.hovered
            self.hovered = None
            for rect, agent_class in self.cards:
                if rect.collidepoint(event.pos):
                    self.hovered = agent_class
            if self.hovered and self.hovered is not previous:
                ASSETS.play("hover", 0.5)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for rect, agent_class in self.cards:
                if rect.collidepoint(event.pos):
                    ASSETS.play("bork_small")
                    from hide_and_sausage.ui.scenes_game import PlacementScene
                    self.app.switch(PlacementScene(self.app, agent_class))
                    return True
        return False

    # -------------------------------------------------------------------------
    # draw - draws the title and a card for each opponent. Each card has the
    # AI's face, stars for how hard it is, its name, a short bio and what AI
    # trick it uses. The card you're hovering lifts up and the face smiles.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "menu_bg", dim=110)
        blit_text(surface, "CHOOSE YOUR OPPONENT", (SCREEN_WIDTH // 2, 70), 44, BUTTER, 5)
        blit_text(surface, "each one is a different AI technique - from random to expectimax",
                  (SCREEN_WIDTH // 2, 115), 18, WHITE, 2, "semibold")

        for rect, agent_class in self.cards:
            hovered = agent_class is self.hovered
            card = rect.move(0, -10 if hovered else 0)
            colour = LEVEL_COLOURS[agent_class.level]
            draw_panel(surface, card, CREAM, radius=20, border=4, shadow=8)
            header = pygame.Rect(card.x, card.y, card.width, 200)
            pygame.draw.rect(surface, colour, header, border_top_left_radius=20,
                             border_top_right_radius=20)
            pygame.draw.rect(surface, INK, card, 4, border_radius=20)
            pygame.draw.line(surface, INK, (card.x, card.y + 200), (card.right - 1, card.y + 200), 4)

            mood = "happy" if hovered else "neutral"
            portrait = ASSETS.portrait(agent_class.key, mood, 190)
            if portrait is not None:
                surface.blit(portrait, portrait.get_rect(midbottom=(card.centerx, card.y + 200)))
            else:
                blit_text(surface, "?", (card.centerx, card.y + 100), 90, INK)

            # stars for difficulty
            for star in range(3):
                filled = star < agent_class.level
                centre = (card.centerx - 24 + star * 24, card.y + 222)
                pygame.draw.circle(surface, BUTTER if filled else (220, 210, 190), centre, 9)
                pygame.draw.circle(surface, INK, centre, 9, 2)

            blit_text(surface, agent_class.name, (card.centerx, card.y + 252), 22, INK)
            blit_text(surface, agent_class.title, (card.centerx, card.y + 278), 14, INK_SOFT,
                      0, "semibold")
            font = ASSETS.font(14, "medium")
            y = card.y + 304
            for line in wrap_text(agent_class.bio, font, card.width - 28):
                surface.blit(font.render(line, True, INK), (card.x + 14, y))
                y += font.get_linesize()
            y += 6
            font = ASSETS.font(13, "semibold")
            for line in wrap_text("AI: " + agent_class.method, font, card.width - 28):
                surface.blit(font.render(line, True, (60, 110, 60)), (card.x + 14, y))
                y += font.get_linesize()

        super().draw(surface)


# =============================================================================
# HowToScene - rules
# =============================================================================
class HowToScene(Scene):

    RULES = (
        "1.  Hide your 6 dachshunds on your lawn. Drag them, R to rotate, F to flip.",
        "2.  A dog biscuit is flipped to decide who throws first (that's the luck!).",
        "3.  Take turns throwing tennis balls at the other garden.",
        "4.  Miss = the ball bounces on the grass.  Hit = BORK!",
        "5.  Hit every square of a dog to make it pop out.",
        "6.  Find the whole pack first to win.",
        "Tip: press B in a match to open the AI's BRAIN VIEW and watch it think.",
    )

    # -------------------------------------------------------------------------
    # __init__ - this screen only needs a Back button (Escape works too).
    #   app : the game that's running right now
    # -------------------------------------------------------------------------
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [Button((30, 30, 140, 50), "< Back",
                               lambda: app.switch(TitleScene(app)), CREAM, 20,
                               pygame.K_ESCAPE)]

    # -------------------------------------------------------------------------
    # draw - draws the rules on the left, and on the right every dog in the
    # pack with its name, size and a little line about it.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "menu_bg", dim=120)
        blit_text(surface, "HOW TO PLAY", (SCREEN_WIDTH // 2, 60), 48, BUTTER, 5)
        panel = pygame.Rect(70, 110, 640, 560)
        draw_panel(surface, panel, CREAM)
        y = panel.y + 26
        font = ASSETS.font(18, "semibold")
        for rule in self.RULES:
            for line in wrap_text(rule, font, panel.width - 50):
                surface.blit(font.render(line, True, INK if not rule.startswith("Tip") else (40, 110, 60)),
                             (panel.x + 25, y))
                y += font.get_linesize()
            y += 14

        pack = pygame.Rect(740, 110, 470, 560)
        draw_panel(surface, pack, (214, 236, 190))
        blit_text(surface, "THE PACK", (pack.centerx, pack.y + 30), 26, INK)
        y = pack.y + 62
        for dog in PACK:
            sprite = ASSETS.dog_sprite(dog.key, ALL_TRANSFORMS[0], 36)
            surface.blit(sprite, (pack.x + 20, y))
            blit_text(surface, f"{dog.name}  ({dog.size})", (pack.x + 215, y + 4), 18, INK,
                      0, "bold", "topleft")
            blit_text(surface, dog.blurb, (pack.x + 215, y + 28), 13, INK_SOFT, 0,
                      "medium", "topleft")
            y += 80
        super().draw(surface)


# =============================================================================
# LabScene - the AI lab (for the lecturer!)
# =============================================================================
class LabScene(Scene):

    # -------------------------------------------------------------------------
    # __init__ - sets up the Back and "Watch AI vs AI" buttons, and loads the
    # experiment results (if tournament.py has been run already).
    #   app : the game that's running right now
    # -------------------------------------------------------------------------
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [Button((30, 30, 140, 50), "< Back",
                               lambda: app.switch(TitleScene(app)), CREAM, 20,
                               pygame.K_ESCAPE),
                        Button((SCREEN_WIDTH - 330, 30, 300, 50), "Watch AI vs AI",
                               self.watch, BUTTER, 20)]
        self.efficiency = self.load_csv("efficiency.csv")
        self.matchups = self.load_csv("head_to_head.csv")

    # -------------------------------------------------------------------------
    # watch - starts a match you just sit back and watch. Good Boy (hunt &
    # target) plays your side against The Dogfather (expectimax), with the
    # brain view on. Your side's dogs are hidden randomly.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def watch(self):
        import random
        from hide_and_sausage.core.board import Garden
        from hide_and_sausage.ai.agents import GoodBoyAgent, DogfatherAgent
        from hide_and_sausage.ui.scenes_game import BattleScene
        garden = Garden()
        garden.scatter_randomly(random.Random())
        self.app.switch(BattleScene(self.app, DogfatherAgent, garden, spectator=GoodBoyAgent))

    # -------------------------------------------------------------------------
    # load_csv - reads one of the results tables that tournament.py saves.
    #   name : the file's name inside the results/ folder
    # Gives back the rows of the table (each row is a list of text), or an
    # empty list if the file isn't there yet.
    # -------------------------------------------------------------------------
    @staticmethod
    def load_csv(name):
        path = os.path.join(PROJECT_DIR, "results", name)
        if not os.path.exists(path):
            return []
        with open(path, newline="") as handle:
            return list(csv.reader(handle))

    # -------------------------------------------------------------------------
    # draw - on the left, each AI and how it works. On the right, a bar chart
    # of how many balls each AI needed to find every dog, plus a win rate
    # table for who beats who. If there are no results yet it just tells
    # you how to make them.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "menu_bg", dim=150)
        blit_text(surface, "THE AI LAB", (SCREEN_WIDTH // 2, 60), 48, BUTTER, 5)

        left = pygame.Rect(60, 110, 560, 570)
        draw_panel(surface, left, CREAM)
        blit_text(surface, "The opponents", (left.centerx, left.y + 28), 24, INK)
        y = left.y + 58
        for agent_class in AGENT_CLASSES:
            portrait = ASSETS.portrait(agent_class.key, "neutral", 70)
            if portrait is not None:
                surface.blit(portrait, (left.x + 16, y))
            blit_text(surface, f"L{agent_class.level}  {agent_class.name}", (left.x + 100, y + 6),
                      18, INK, 0, "bold", "topleft")
            font = ASSETS.font(14, "medium")
            line_y = y + 32
            for line in wrap_text(agent_class.method, font, left.width - 120):
                surface.blit(font.render(line, True, INK_SOFT), (left.x + 100, line_y))
                line_y += font.get_linesize()
            y += 150

        right = pygame.Rect(650, 110, 570, 570)
        draw_panel(surface, right, CREAM)
        blit_text(surface, "Experiment: balls needed to find all 22 squares",
                  (right.centerx, right.y + 28), 18, INK)
        if len(self.efficiency) <= 1:
            font = ASSETS.font(16, "medium")
            y = right.y + 80
            for line in wrap_text("No results yet. Run  python tournament.py  to pit every "
                                  "AI against the same gardens and against each other. "
                                  "The results will appear here and in the results/ folder.",
                                  font, right.width - 60):
                surface.blit(font.render(line, True, INK), (right.x + 30, y))
                y += font.get_linesize()
            return super().draw(surface)

        rows = self.efficiency[1:]
        best = max(float(row[1]) for row in rows)
        bar_left, bar_width = right.x + 190, right.width - 230
        y = right.y + 70
        for row in rows:
            mean = float(row[1])
            blit_text(surface, row[0], (bar_left - 12, y + 14), 16, INK, 0, "bold", "midright")
            length = int(bar_width * mean / max(best, 100))
            bar = pygame.Rect(bar_left, y, length, 28)
            pygame.draw.rect(surface, CARAMEL, bar, border_radius=8)
            pygame.draw.rect(surface, INK, bar, 3, border_radius=8)
            blit_text(surface, f"{mean:.1f}", (bar.right + 8, y + 14), 16, INK, 0, "bold", "midleft")
            y += 44

        if len(self.matchups) > 1:
            blit_text(surface, "Head-to-head win rate (row beats column)",
                      (right.centerx, y + 24), 16, INK)
            names = self.matchups[0][1:]
            cell = 66
            grid_left = right.x + 150
            top = y + 62
            for j, name in enumerate(names):
                blit_text(surface, name.split()[-1][:9], (grid_left + j * cell + cell // 2, top - 4),
                          12, INK, 0, "bold", "midbottom")
            for i, row in enumerate(self.matchups[1:]):
                blit_text(surface, row[0], (grid_left - 8, top + i * 30 + 14), 13, INK, 0,
                          "bold", "midright")
                for j, value in enumerate(row[1:]):
                    rect = pygame.Rect(grid_left + j * cell, top + i * 30, cell - 4, 26)
                    if value:
                        rate = float(value)
                        colour = (int(235 - 120 * rate), int(110 + 110 * rate), 90)
                        pygame.draw.rect(surface, colour, rect, border_radius=6)
                        blit_text(surface, f"{rate:.0%}", rect.center, 13, INK)
                    else:
                        pygame.draw.rect(surface, (210, 200, 180), rect, border_radius=6)
        super().draw(surface)
