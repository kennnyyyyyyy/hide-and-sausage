# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  scenes_game.py - this is where the actual game happens:
#    PlacementScene - you drag your six dachshunds onto your lawn to hide them
#    BattleScene    - you and the AI take turns throwing balls, and you can
#                     watch the AI think while it plays
#    ResultScene    - shows who won plus some stats from the match
# =============================================================================

import math
import random
import threading

import pygame

from hide_and_sausage.config import (SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE,
                                     BOARD_PIXELS, AI_THINK_SECONDS, INK,
                                     INK_SOFT, CREAM, BUTTER, TOMATO, SKY, WHITE,
                                     GRASS, GRASS_DARK, CARAMEL)
from hide_and_sausage.core.fleet import (PACK, DOG_BY_KEY, ALL_TRANSFORMS,
                                         Transform, shape_for, place_shape,
                                         TOTAL_DOG_CELLS)
from hide_and_sausage.core.board import (Garden, Knowledge, MISS, FOUND,
                                         cell_name)
from hide_and_sausage.ai.agents import Situation, win_chance
from hide_and_sausage.ai.probability import (placement_heatmap, placement_probabilities,
                                             normalise_for_display, chance_text)
from hide_and_sausage.ai.reactions import react
from hide_and_sausage.ui.app import Scene
from hide_and_sausage.ui.assets import ASSETS
from hide_and_sausage.ui.board_view import BoardView, FlyingBall
from hide_and_sausage.ui.widgets import (Button, SpeechBubble, Particles,
                                         PopText, draw_panel, blit_text,
                                         render_text, wrap_text, ease_out_back)

CONFETTI = [TOMATO, BUTTER, SKY, (170, 220, 120), (240, 160, 210), WHITE]
GRASS_BITS = [GRASS, GRASS_DARK, (170, 220, 120)]


# -----------------------------------------------------------------------------
# draw_roster - draws a little row of mini dog pictures under a garden.
# Dogs that are still hidden look normal, and dogs that got found are faded
# out with a big red X over them, so you can tell who's left at a glance.
#   surface  : the screen we draw on
#   center   : (x, y) spot where the middle of the row goes
#   found    : the keys of the dogs that have already been found
# -----------------------------------------------------------------------------
def draw_roster(surface, center, found):
    mini = 15
    widths = []
    for dog in PACK:
        shape = shape_for(dog, ALL_TRANSFORMS[0])
        widths.append((max(c for _, c in shape) + 1) * mini)
    x = center[0] - (sum(widths) + 12 * (len(PACK) - 1)) // 2
    for dog, width in zip(PACK, widths):
        sprite = ASSETS.dog_sprite(dog.key, ALL_TRANSFORMS[0], mini)
        rect = sprite.get_rect(midleft=(x, center[1]))
        if dog.key in found:
            faded = sprite.copy()
            faded.set_alpha(90)
            surface.blit(faded, rect)
            pygame.draw.line(surface, TOMATO, rect.topleft, rect.bottomright, 4)
            pygame.draw.line(surface, TOMATO, rect.bottomleft, rect.topright, 4)
        else:
            surface.blit(sprite, rect)
        x += width + 12


# =============================================================================
# PlacementScene - hide your dogs
# =============================================================================
class PlacementScene(Scene):

    # -------------------------------------------------------------------------
    # __init__ - sets up the hiding screen: an empty lawn, the pack of dogs
    # waiting on a bench at the side, and the buttons.
    #   app         : the main game app, so we can switch screens later
    #   agent_class : which AI you picked to play against
    # -------------------------------------------------------------------------
    def __init__(self, app, agent_class):
        super().__init__(app)
        self.agent_class = agent_class
        self.board = BoardView((150, 185), "YOUR GARDEN")
        self.garden = Garden()
        self.transforms = {dog.key: ALL_TRANSFORMS[0] for dog in PACK}
        self.held = None                  # dog key currently carried by the mouse
        self.mouse = (0, 0)
        self.particles = Particles()
        self.slots = {}
        y = 200
        for dog in PACK:
            self.slots[dog.key] = pygame.Rect(700, y, 300, 62)
            y += 72
        self.ready_button = Button((1030, 600, 200, 64), "READY!", self.start_battle,
                                   BUTTER, 28, pygame.K_RETURN)
        self.buttons = [
            Button((30, 30, 140, 50), "< Back", self.go_back, CREAM, 20, pygame.K_ESCAPE),
            Button((1030, 200, 200, 56), "Randomise", self.randomise, SKY, 20, pygame.K_SPACE),
            Button((1030, 270, 200, 56), "Clear", self.clear, CREAM, 20),
            self.ready_button,
        ]

    # -------------------------------------------------------------------------
    # go_back - takes you back to the screen where you pick your opponent.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def go_back(self):
        from hide_and_sausage.ui.scenes_menu import SelectScene
        self.app.switch(SelectScene(self.app))

    # -------------------------------------------------------------------------
    # randomise - hides all the dogs in random spots for you, turned random
    # ways too. Handy if you can't be bothered placing them yourself.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def randomise(self):
        self.garden.scatter_randomly(random.Random())
        for key, placement in self.garden.placements.items():
            self.transforms[key] = placement.transform
        self.held = None
        ASSETS.play("drop")

    # -------------------------------------------------------------------------
    # clear - picks every dog back up off the lawn so you can start over.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def clear(self):
        self.garden = Garden()
        self.held = None

    # -------------------------------------------------------------------------
    # start_battle - jumps to the actual match, but only if all the dogs
    # are hidden. If any are still on the bench, nothing happens.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def start_battle(self):
        if self.garden.is_complete():
            self.app.switch(BattleScene(self.app, self.agent_class, self.garden))

    # -------------------------------------------------------------------------
    # turn_held - spins or flips the dog you're carrying around. If you're
    # not holding a dog, it just does nothing.
    #   rotate : True to turn it 90 degrees, False to flip it like a mirror
    # -------------------------------------------------------------------------
    def turn_held(self, rotate):
        if self.held is None:
            return
        old = self.transforms[self.held]
        if rotate:
            self.transforms[self.held] = Transform((old.quarter_turns + 1) % 4, old.mirrored)
        else:
            self.transforms[self.held] = Transform(old.quarter_turns, not old.mirrored)
        ASSETS.play("hover")

    # -------------------------------------------------------------------------
    # preview_placement - works out where the dog you're carrying would land
    # if you dropped it right now. The dog is centred on the square under
    # the mouse.
    #   (no parameters)
    # Gives back that spot (a Placement), or None if you're not holding a
    # dog or the mouse isn't over the lawn. It doesn't check if the spot is
    # actually free, that's done separately.
    # -------------------------------------------------------------------------
    def preview_placement(self):
        if self.held is None:
            return None
        cell = self.board.cell_at(self.mouse)
        if cell is None:
            return None
        transform = self.transforms[self.held]
        shape = shape_for(DOG_BY_KEY[self.held], transform)
        rows = max(r for r, _ in shape) + 1
        cols = max(c for _, c in shape) + 1
        anchor = (cell[0] - (rows - 1) // 2, cell[1] - (cols - 1) // 2)
        return place_shape(self.held, shape, transform, anchor)

    # -------------------------------------------------------------------------
    # handle_event - deals with the mouse and keyboard on the hiding screen.
    # R or right-click spins the dog, F flips it, and left-click picks up
    # or drops a dog. The buttons get their turn too.
    #   event : the input that just happened (a key press, click, mouse move)
    # Gives back True if we used the event, False if we didn't.
    # -------------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.turn_held(True)
                return True
            if event.key == pygame.K_f:
                self.turn_held(False)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.turn_held(True)
            return True
        if super().handle_event(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click(event.pos)
            return True
        return False

    # -------------------------------------------------------------------------
    # click - what a left click does. If you're holding a dog, we try to drop
    # it there (or put it back on the bench if you clicked off the lawn).
    # If your hands are empty, we pick up whichever dog you clicked on,
    # either from the lawn or from the bench.
    #   pos : where the mouse was when you clicked
    # -------------------------------------------------------------------------
    def click(self, pos):
        if self.held is not None:
            placement = self.preview_placement()
            if placement is not None and self.garden.can_place(placement, self.held):
                self.garden.place(placement)
                ASSETS.play("drop")
                self.particles.burst(self.board.cell_center(min(placement.cells)), GRASS_BITS, 12, 160, 4)
                self.held = None
            elif placement is None and not self.board.rect.collidepoint(pos):
                self.held = None          # clicked away: put it back on the bench
            else:
                ASSETS.play("miss", 0.4)
            return
        # pick up a dog from the lawn...
        cell = self.board.cell_at(pos)
        if cell is not None and cell in self.garden.cell_owner:
            self.held = self.garden.cell_owner[cell]
            self.garden.remove(self.held)
            ASSETS.play("pickup")
            return
        # ...or from the bench
        for key, rect in self.slots.items():
            if rect.collidepoint(pos):
                self.held = key
                self.garden.remove(key)
                ASSETS.play("pickup")

    # -------------------------------------------------------------------------
    # update - runs every frame. Moves the little grass particles along and
    # only lets you press Ready once every dog is hidden.
    #   dt : how many seconds passed since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        super().update(dt)
        self.particles.update(dt)
        self.ready_button.enabled = self.garden.is_complete()

    # -------------------------------------------------------------------------
    # draw - draws the whole hiding screen: the lawn, the dogs you already
    # hid, a green/red preview of where the held dog would go, the bench
    # with the pack, and the dog stuck to your mouse.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "battle_bg", dim=40)
        blit_text(surface, "HIDE YOUR PACK", (SCREEN_WIDTH // 2, 60), 44, BUTTER, 5)
        blit_text(surface, f"against {self.agent_class.name}  -  click a dog, move it, click to drop.  "
                           f"R / right-click = rotate, F = flip",
                  (SCREEN_WIDTH // 2, 105), 17, WHITE, 2, "semibold")

        self.board.draw_frame(surface)
        self.board.draw_lawn(surface)
        self.board.draw_dogs(surface, self.garden.placements.values())

        preview = self.preview_placement()
        if preview is not None:
            fits = self.garden.can_place(preview, self.held)
            tint = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            tint.fill((120, 230, 120, 110) if fits else (255, 80, 60, 130))
            for cell in preview.cells:
                surface.blit(tint, self.board.cell_rect(cell))
            self.board.draw_dogs(surface, [preview], alpha=190)

        # the bench
        bench = pygame.Rect(680, 150, 340, 520)
        draw_panel(surface, bench, CREAM)
        blit_text(surface, "THE PACK", (bench.centerx, bench.y + 26), 22, INK)
        for dog in PACK:
            slot = self.slots[dog.key]
            placed = dog.key in self.garden.placements
            carried = dog.key == self.held
            colour = (205, 235, 180) if placed else ((255, 236, 170) if carried else WHITE)
            if slot.collidepoint(self.mouse) and not placed:
                colour = (255, 244, 205)
            draw_panel(surface, slot, colour, radius=12, border=3, shadow=3)
            if not carried:
                sprite = ASSETS.dog_sprite(dog.key, ALL_TRANSFORMS[0], 26)
                surface.blit(sprite, sprite.get_rect(midleft=(slot.x + 10, slot.centery)))
            blit_text(surface, dog.name, (slot.x + 150, slot.y + 10), 17, INK, 0, "bold", "topleft")
            status = "hidden!" if placed else ("carrying..." if carried else f"{dog.size} squares")
            blit_text(surface, status, (slot.x + 150, slot.y + 34), 13, INK_SOFT, 0,
                      "semibold", "topleft")

        # carried dog follows the mouse when off the lawn
        if self.held is not None and preview is None:
            sprite = ASSETS.dog_sprite(self.held, self.transforms[self.held])
            surface.blit(sprite, sprite.get_rect(center=self.mouse))

        self.particles.draw(surface)
        hidden = len(self.garden.placements)
        blit_text(surface, f"{hidden} / {len(PACK)} hidden", (1130, 580), 18, WHITE, 2)
        super().draw(surface)


# =============================================================================
# BattleScene - the match
# =============================================================================
class BattleScene(Scene):

    LEFT_ORIGIN = (70, 178)
    RIGHT_ORIGIN = (SCREEN_WIDTH - 70 - BOARD_PIXELS, 178)
    MIDDLE_X = SCREEN_WIDTH // 2
    HINTS = 3

    # -------------------------------------------------------------------------
    # __init__ - gets the match ready. The AI hides its own dogs, both sides
    # start with a blank record of throws, and we pick at random who goes
    # first (that's the biscuit flip at the start).
    #   app          : the main game app, so we can switch screens later
    #   agent_class  : which AI you're playing against
    #   human_garden : the garden where you hid your dogs
    #   spectator    : optional second AI that plays for you instead, so you
    #                  can just sit back and watch AI vs AI
    # -------------------------------------------------------------------------
    def __init__(self, app, agent_class, human_garden, spectator=None):
        super().__init__(app)
        self.rng = random.Random()
        self.ai = agent_class()
        self.autopilot = spectator() if spectator else None

        self.human_garden = human_garden
        self.ai_garden = self.ai.hide_dogs()
        self.human_knowledge = Knowledge()       # human's throws at the AI
        self.ai_knowledge = Knowledge()          # AI's throws at the human

        left_title = "YOUR GARDEN" if not self.autopilot else f"{self.autopilot.name.upper()}'S GARDEN"
        self.my_view = BoardView(self.LEFT_ORIGIN, left_title)
        self.enemy_view = BoardView(self.RIGHT_ORIGIN, f"{self.ai.name.upper()}'S GARDEN")
        self.bubble = SpeechBubble((self.MIDDLE_X - 125, 292, 250, 128))
        self.particles = Particles()
        self.pops = []
        self.reveal_times = {}                    # (side, dog_key) -> time revealed

        self.state = "coin"
        self.state_time = 0.0
        self.first_player = self.rng.choice(("human", "ai"))
        self.flying = None
        self.pending_cell = None
        self.decision = None
        self.thinking_thread = None
        self.thinking_result = None
        self.scan_index = 0

        self.mood = "neutral"
        self.mood_time = 0.0
        self.show_brain = True
        self.hint_heat = None
        self.hints_left = self.HINTS
        self.hover = None
        self.shake = 0.0
        self.winner = None
        self.streaks = {"player": 0, "ai": 0}

        self.buttons = [
            Button((self.MIDDLE_X - 125, 610, 120, 44), "Brain [B]", self.toggle_brain, SKY, 16,
                   pygame.K_b),
            Button((self.MIDDLE_X + 5, 610, 120, 44), f"Hint [H] x{self.hints_left}", self.use_hint,
                   BUTTER, 16, pygame.K_h),
            Button((self.MIDDLE_X - 60, 662, 120, 40), "Menu", self.to_menu, CREAM, 16),
        ]
        self.hint_button = self.buttons[1]
        if self.autopilot:
            self.hint_button.enabled = False
        self.bubble.say(react(self.ai.key, "start", self.rng))
        ASSETS.play("coin")

    # ------------------------------------------------------------------ helpers

    # -------------------------------------------------------------------------
    # to_menu - quits the match and goes back to the title screen.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def to_menu(self):
        from hide_and_sausage.ui.scenes_menu import TitleScene
        self.app.switch(TitleScene(self.app))

    # -------------------------------------------------------------------------
    # toggle_brain - turns the Brain View on or off. That's the heat map on
    # your garden showing where the AI thinks your dogs are.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def toggle_brain(self):
        self.show_brain = not self.show_brain

    # -------------------------------------------------------------------------
    # use_hint - uses up one of your hints. It puts a heat map over the AI's
    # garden for this turn, showing where its dogs are most likely to be,
    # based on what your own throws have found so far. You only get 3 per
    # game, and it only works on your turn (once per turn).
    #   (no parameters)
    # -------------------------------------------------------------------------
    def use_hint(self):
        if self.hints_left <= 0 or self.state != "human_turn" or self.hint_heat is not None:
            return
        self.hints_left -= 1
        self.hint_button.label = f"Hint [H] x{self.hints_left}"
        self.hint_button.enabled = self.hints_left > 0
        heat = placement_heatmap(self.human_knowledge)
        probs = placement_probabilities(self.human_knowledge)
        self.hint_heat = (normalise_for_display(heat), probs)
        self.pops.append(PopText((self.enemy_view.rect.centerx, self.enemy_view.rect.top - 40),
                                 "Heat map hint!", SKY, 24, duration=1.4))

    # -------------------------------------------------------------------------
    # set_state - moves the match on to a new step (like "ai_think" or
    # "human_turn") and resets the timer for that step back to zero.
    #   state : the name of the step we're moving to
    # -------------------------------------------------------------------------
    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    # -------------------------------------------------------------------------
    # set_mood - changes the face on the AI's portrait for a little while.
    #   mood     : the face to show, "neutral", "happy", "shocked" or "sad"
    #   duration : how many seconds it keeps that face before going back
    #              to neutral
    # -------------------------------------------------------------------------
    def set_mood(self, mood, duration=2.2):
        self.mood = mood
        self.mood_time = duration

    # -------------------------------------------------------------------------
    # situation - sums up who's ahead, from the AI's side. Basically how many
    # dog squares each side has hit and how many balls each has thrown.
    #   (no parameters)
    # Gives back a Situation with those numbers in it.
    # -------------------------------------------------------------------------
    def situation(self):
        return Situation(self.ai_knowledge.hits_so_far(), self.human_knowledge.hits_so_far(),
                         len(self.ai_knowledge.shots), len(self.human_knowledge.shots))

    # ------------------------------------------------------------------ turns

    # -------------------------------------------------------------------------
    # start_human_turn - starts your turn and waits for you to throw. Any
    # hint from last turn gets cleared. If an AI is playing for you, we ask
    # it now which square it wants, and it throws a moment later.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def start_human_turn(self):
        self.hint_heat = None
        self.set_state("human_turn")
        if self.autopilot:
            situation = Situation(self.human_knowledge.hits_so_far(), self.ai_knowledge.hits_so_far(),
                                  len(self.human_knowledge.shots), len(self.ai_knowledge.shots))
            self.autopilot_choice = self.autopilot.choose(self.human_knowledge, situation).cell

    # -------------------------------------------------------------------------
    # throw_at_ai - you throw a ball at the AI's garden. This just starts the
    # ball flying, we find out if it hit once it lands.
    #   cell : the square you're aiming at
    # -------------------------------------------------------------------------
    def throw_at_ai(self, cell):
        self.pending_cell = cell
        self.flying = FlyingBall((self.enemy_view.rect.centerx, SCREEN_HEIGHT + 20),
                                 self.enemy_view.cell_center(cell))
        ASSETS.play("throw")
        self.set_state("human_throw")

    # -------------------------------------------------------------------------
    # start_ai_turn - gets the AI thinking about its move. The thinking runs
    # on a separate thread in the background, so the screen doesn't freeze
    # while the smarter AIs crunch numbers. We hand it a copy of what it
    # knows so nothing changes under its feet.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def start_ai_turn(self):
        self.set_state("ai_think")
        self.set_mood("neutral", 0)
        self.thinking_result = None
        knowledge = self.ai_knowledge.copy()
        situation = self.situation()

        # think - this is what runs on the background thread. It just asks the
        # AI for its move and saves the answer so update() can grab it.
        #   (no parameters)
        def think():
            self.thinking_result = self.ai.choose(knowledge, situation)

        self.thinking_thread = threading.Thread(target=think, daemon=True)
        self.thinking_thread.start()
        ASSETS.play("think", 0.6)

    # -------------------------------------------------------------------------
    # resolve_throw - sorts out what happens once a ball lands. We check if
    # it missed, hit a dog (BORK) or found a whole dog, write that down,
    # and then play the sounds, particles, pop-up text, face changes and
    # what the AI says about it.
    #   side : whose garden the ball landed in, "ai" if you threw at the
    #          AI, "human" if the AI threw at you
    # Gives back the outcome of the throw so we can check if the game's over.
    # -------------------------------------------------------------------------
    def resolve_throw(self, side):
        cell = self.pending_cell
        if side == "ai":
            outcome = self.ai_garden.receive_ball(cell)
            self.human_knowledge.record(outcome)
            view, thrower = self.enemy_view, "player"
        else:
            outcome = self.human_garden.receive_ball(cell)
            self.ai_knowledge.record(outcome)
            view, thrower = self.my_view, "ai"

        center = view.cell_center(cell)
        self.update_streak(thrower, outcome, view)
        if outcome.result == MISS:
            ASSETS.play("miss")
            self.particles.burst(center, GRASS_BITS, 14, 170, 4)
            self.pops.append(PopText(center, "boing", (110, 160, 60), 22, duration=0.8))
            event = f"{thrower}_miss"
            if thrower == "player":
                self.set_mood("happy", 1.6)
        else:
            if outcome.result == FOUND:
                dog = DOG_BY_KEY[outcome.dog_key]
                ASSETS.play("found")
                ASSETS.play("bork")
                self.reveal_times[(side, dog.key)] = self.time
                self.particles.burst(center, CONFETTI, 40, 320, 6)
                label = f"FOUND {dog.name.upper()}!"
                self.pops.append(PopText((view.rect.centerx, view.rect.centery), label,
                                         BUTTER, 34, duration=1.6))
                event = f"{thrower}_found"
                self.shake = 0.35
                if thrower == "player":
                    self.set_mood("sad", 2.5)
                else:
                    self.set_mood("happy", 2.5)
                self.bubble.say(react(self.ai.key, event, self.rng, dog=dog.name))
            else:
                ASSETS.play("bork")
                bork = ASSETS.scaled("bork", 110)
                self.pops.append(PopText(center, "BORK!", TOMATO, 34, image=bork, duration=1.0))
                self.particles.burst(center, [TOMATO, BUTTER, WHITE], 18, 240, 5)
                self.shake = 0.2
                event = f"{thrower}_hit"
                self.set_mood("shocked" if thrower == "player" else "happy", 1.8)
        if outcome.result != FOUND and (thrower == "player" or self.rng.random() < 0.5):
            self.bubble.say(react(self.ai.key, event, self.rng))
        return outcome

    # -------------------------------------------------------------------------
    # update_streak - keeps count of how many hits in a row someone gets. A
    # miss resets it to zero. From 2 in a row we pop up a combo shout like
    # "DOUBLE BORK!" that gets bigger the longer the streak goes.
    #   thrower : who threw, "player" or "ai"
    #   outcome : what that throw just did (miss, hit or found)
    #   view    : the garden it landed on, so we know where to put the shout
    # -------------------------------------------------------------------------
    def update_streak(self, thrower, outcome, view):
        if outcome.result == MISS:
            self.streaks[thrower] = 0
            return
        self.streaks[thrower] += 1
        names = {2: "DOUBLE BORK!", 3: "TRIPLE BORK!!", 4: "QUADRA BORK!!!"}
        streak = self.streaks[thrower]
        if streak >= 2:
            text = names.get(streak, "BORK-TASTIC!!!")
            self.pops.append(PopText((view.rect.centerx, view.rect.top + 40), text,
                                     BUTTER, 30 + 4 * min(streak, 5), duration=1.3))

    # -------------------------------------------------------------------------
    # finish - ends the match once someone has found the whole pack. Plays
    # the win or lose sound, sets the AI's face and last line, and throws
    # confetti if you won.
    #   winner : who won, "human" or "ai"
    # -------------------------------------------------------------------------
    def finish(self, winner):
        self.winner = winner
        self.set_state("game_over")
        if winner == "human":
            ASSETS.play("win")
            self.set_mood("sad", 99)
            self.bubble.say(react(self.ai.key, "ai_lose", self.rng))
            for _ in range(6):
                self.particles.burst((self.rng.randint(100, 1180), self.rng.randint(100, 400)),
                                     CONFETTI, 30, 380, 6)
        else:
            ASSETS.play("lose")
            self.set_mood("happy", 99)
            self.bubble.say(react(self.ai.key, "ai_win", self.rng))

    # ------------------------------------------------------------------ input

    # -------------------------------------------------------------------------
    # handle_event - deals with input during the match. Tracks which square
    # the mouse is over, throws a ball when you click a square you haven't
    # tried yet (only on your turn), and Escape takes you to the menu.
    #   event : the input that just happened (a key press, click, mouse move)
    # Gives back True if we used the event, False if we didn't.
    # -------------------------------------------------------------------------
    def handle_event(self, event):
        if super().handle_event(event):
            return True
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.enemy_view.cell_at(event.pos)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.state == "human_turn" and not self.autopilot):
            cell = self.enemy_view.cell_at(event.pos)
            if cell is not None and self.human_knowledge.state_of(cell) == 0:
                self.throw_at_ai(cell)
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.to_menu()
            return True
        return False

    # ------------------------------------------------------------------ update

    # -------------------------------------------------------------------------
    # update - runs every frame and pretty much drives the whole match. It
    # moves all the animations along, then checks which step we're on and
    # whether it's time for the next one. The order goes: biscuit flip ->
    # your turn -> your ball flies -> short pause -> AI thinks -> AI scans
    # its top picks -> AI's ball flies -> short pause -> back to you, until
    # someone wins and we go to the result screen.
    #   dt : how many seconds passed since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        super().update(dt)
        self.state_time += dt
        self.bubble.update(dt)
        self.particles.update(dt)
        for pop in self.pops:
            pop.update(dt)
        self.pops = [pop for pop in self.pops if pop.alive]
        self.shake = max(0.0, self.shake - dt)
        if self.mood_time > 0:
            self.mood_time -= dt
            if self.mood_time <= 0 and self.state != "game_over":
                self.mood = "neutral"
        if self.flying:
            self.flying.update(dt)

        state = self.state
        if state == "coin" and self.state_time > 2.4:
            if self.first_player == "human":
                self.start_human_turn()
            else:
                self.start_ai_turn()

        elif state == "human_turn" and self.autopilot and self.state_time > 0.9:
            self.throw_at_ai(self.autopilot_choice)

        elif state == "human_throw" and self.flying.done:
            self.flying = None
            outcome = self.resolve_throw("ai")
            if outcome.game_over:
                self.finish("human")
            else:
                self.set_state("pause_after_human")

        elif state == "pause_after_human" and self.state_time > 0.7:
            self.start_ai_turn()

        elif state == "ai_think":
            ready = self.thinking_result is not None
            if ready and self.state_time > AI_THINK_SECONDS:
                self.decision = self.thinking_result
                self.scan_index = 0
                self.set_state("ai_scan")

        elif state == "ai_scan":
            # flick through the top candidates so you can SEE it compare them
            steps = max(1, min(4, len(self.decision.candidates)))
            self.scan_index = min(steps - 1, int(self.state_time / 0.22))
            if self.state_time > steps * 0.22 + 0.25:
                self.bubble.say(self.decision.thought)
                self.pending_cell = self.decision.cell
                self.flying = FlyingBall((self.MIDDLE_X, 170), self.my_view.cell_center(self.decision.cell))
                ASSETS.play("throw")
                self.set_state("ai_throw")

        elif state == "ai_throw" and self.flying.done:
            self.flying = None
            outcome = self.resolve_throw("human")
            if outcome.game_over:
                self.finish("ai")
            else:
                self.set_state("pause_after_ai")

        elif state == "pause_after_ai" and self.state_time > 0.6:
            self.start_human_turn()

        elif state == "game_over" and self.state_time > 4.0:
            self.app.switch(ResultScene(self.app, self))

    # ------------------------------------------------------------------ drawing

    # -------------------------------------------------------------------------
    # draw - draws everything on the battle screen, piece by piece. If the
    # screen is meant to be shaking (after a big hit), we draw it all onto
    # a copy and stick it down slightly off-centre.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "battle_bg", dim=30)
        offset = (self.rng.randint(-4, 4), self.rng.randint(-4, 4)) if self.shake > 0 else (0, 0)
        layer = surface
        if offset != (0, 0):
            layer = surface.copy()

        self.draw_top_banner(layer)
        self.draw_my_side(layer)
        self.draw_enemy_side(layer)
        self.draw_middle(layer)
        if self.flying:
            self.flying.draw(layer)
        self.particles.draw(layer)
        for pop in self.pops:
            pop.draw(layer)
        if self.state == "coin":
            self.draw_coin(layer)
        if self.state == "game_over":
            self.draw_game_over(layer)

        if layer is not surface:
            surface.fill(INK)
            surface.blit(layer, offset)
        super().draw(surface)

    # -------------------------------------------------------------------------
    # draw_top_banner - draws the banner at the top that says whose turn it
    # is (or that the biscuit is flipping, or that the game's over).
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_top_banner(self, surface):
        if self.state in ("human_turn", "human_throw", "pause_after_human"):
            text, colour = ("YOUR TURN - throw a ball!" if not self.autopilot
                            else f"{self.autopilot.name} is throwing..."), BUTTER
        elif self.state in ("ai_think", "ai_scan", "ai_throw", "pause_after_ai"):
            dots = "." * (1 + int(self.time * 3) % 3)
            text, colour = f"{self.ai.name} is thinking{dots}", SKY
        elif self.state == "coin":
            text, colour = "Flipping the dog biscuit...", WHITE
        else:
            text, colour = "GAME OVER", TOMATO
        banner = pygame.Rect(self.MIDDLE_X - 260, 14, 520, 52)
        draw_panel(surface, banner, colour, radius=26, border=4, shadow=5)
        blit_text(surface, text, banner.center, 24, INK)

    # -------------------------------------------------------------------------
    # draw_my_side - draws your garden on the left: your dogs, where the AI
    # has thrown, and (if Brain View is on) the AI's heat map of where it
    # thinks your dogs are. While it's thinking we show a shimmer wave
    # instead, and while it scans we show a cursor jumping between its top
    # picks. The score and dog roster go underneath.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_my_side(self, surface):
        view = self.my_view
        ai_turn = self.state in ("ai_think", "ai_scan", "ai_throw")
        view.draw_frame(surface, glow=ai_turn)
        view.draw_lawn(surface)
        found = set(self.ai_knowledge.found_dogs)
        view.draw_dogs(surface, self.human_garden.placements.values(), tint_found=found)
        view.draw_marks(surface, self.ai_knowledge)

        if self.show_brain:
            if self.state == "ai_think":
                # shimmering "thinking" scan across the board
                t = self.state_time * 2.5
                shimmer = [[max(0.0, math.sin(t - (r + c) * 0.35)) * 0.6
                            if self.ai_knowledge.grid[r][c] == 0 else 0
                            for c in range(10)] for r in range(10)]
                view.draw_heat(surface, shimmer, None, 0.6)
            elif self.decision is not None and self.state in ("ai_scan", "ai_throw", "pause_after_ai",
                                                               "human_turn", "human_throw",
                                                               "pause_after_human"):
                fade = 1.0 if self.state != "ai_scan" else min(1.0, self.state_time * 4)
                view.draw_heat(surface, self.decision.heat, self.decision.probs, fade)

        if self.state == "ai_scan" and self.decision.candidates:
            cell = self.decision.candidates[self.scan_index][0]
            view.draw_cursor(surface, cell, SKY)
        if self.state == "ai_throw":
            view.draw_cursor(surface, self.decision.cell, TOMATO)
        blit_text(surface, f"{self.ai.name} found {self.ai_knowledge.hits_so_far()}/{TOTAL_DOG_CELLS}",
                  (view.rect.centerx, view.rect.bottom + 38), 16, WHITE, 2, "semibold")
        draw_roster(surface, (view.rect.centerx, view.rect.bottom + 70), found)

    # -------------------------------------------------------------------------
    # draw_enemy_side - draws the AI's garden on the right: your throws, any
    # hint heat map, and found dogs that pop out with a bouncy animation.
    # Once the game's over, the dogs you never found show up see-through.
    # It also shows a cursor and square name where your mouse is, plus the
    # score and dog roster underneath.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_enemy_side(self, surface):
        view = self.enemy_view
        view.draw_frame(surface, glow=self.state == "human_turn")
        view.draw_lawn(surface)
        if self.hint_heat is not None:
            view.draw_heat(surface, self.hint_heat[0], self.hint_heat[1], 0.85)

        # found dogs pop out with a bouncy scale animation
        for key in self.human_knowledge.found_dogs:
            placement = self.ai_garden.placements[key]
            age = self.time - self.reveal_times.get(("ai", key), -10)
            sprite = ASSETS.dog_sprite(key, placement.transform)
            scale = ease_out_back(min(1.0, age / 0.5)) if age < 0.5 else 1.0
            if scale <= 0:
                continue
            sprite = pygame.transform.rotozoom(sprite, 0, scale)
            anchor = view.cell_rect(placement.anchor)
            box = pygame.Rect(anchor.topleft, ASSETS.dog_sprite(key, placement.transform).get_size())
            surface.blit(sprite, sprite.get_rect(center=box.center))
        view.draw_marks(surface, self.human_knowledge)

        if self.state == "game_over":
            hidden = [p for k, p in self.ai_garden.placements.items()
                      if k not in self.human_knowledge.found_dogs]
            view.draw_dogs(surface, hidden, alpha=150)

        if self.state == "human_turn" and self.hover and not self.autopilot:
            if self.human_knowledge.state_of(self.hover) == 0:
                view.draw_cursor(surface, self.hover)
                blit_text(surface, cell_name(self.hover),
                          (view.cell_rect(self.hover).centerx, view.cell_rect(self.hover).top - 12),
                          14, WHITE, 2)
        found = set(self.human_knowledge.found_dogs)
        who = "You" if not self.autopilot else self.autopilot.name
        blit_text(surface, f"{who} found {self.human_knowledge.hits_so_far()}/{TOTAL_DOG_CELLS}",
                  (view.rect.centerx, view.rect.bottom + 38), 16, WHITE, 2, "semibold")
        draw_roster(surface, (view.rect.centerx, view.rect.bottom + 70), found)

    # -------------------------------------------------------------------------
    # draw_middle - draws the middle column: the AI's bobbing portrait, its
    # speech bubble, a bar showing how confident it is that it's winning,
    # and the BRAIN panel listing its top 3 squares and their scores.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_middle(self, surface):
        x = self.MIDDLE_X
        bob = math.sin(self.time * 2.5) * 3
        if self.state == "ai_think":
            bob = math.sin(self.time * 14) * 2      # nervous jitter while thinking
        frame = pygame.Rect(x - 82, 78, 164, 164)
        draw_panel(surface, frame, (255, 236, 200), radius=82, border=4, shadow=5)
        portrait = ASSETS.portrait(self.ai.key, self.mood, 158)
        if portrait is not None:
            surface.blit(portrait, portrait.get_rect(midbottom=(x, frame.bottom - 2 + bob)))
        blit_text(surface, self.ai.name, (x, frame.bottom + 2), 18, CREAM, 3, "bold", "midtop")
        self.bubble.draw(surface)

        # the AI's confidence that it is winning
        chance = win_chance(self.situation())
        bar = pygame.Rect(x - 125, 432, 250, 22)
        draw_panel(surface, bar, (230, 220, 200), radius=11, border=3, shadow=0)
        fill = bar.inflate(-6, -6)
        fill.width = max(4, int(fill.width * chance))
        pygame.draw.rect(surface, TOMATO if chance > 0.5 else SKY, fill, border_radius=8)
        blit_text(surface, f"{self.ai.name.split()[-1]}'s confidence: {chance:.0%}",
                  (x, bar.bottom + 4), 13, WHITE, 2, "semibold", "midtop")

        # brain panel: what the AI is weighing up
        panel = pygame.Rect(x - 125, 478, 250, 120)
        draw_panel(surface, panel, (30, 40, 60), radius=14, border=3, shadow=4)
        blit_text(surface, "BRAIN", (panel.x + 12, panel.y + 8), 14, BUTTER, 0, "bold", "topleft")
        if self.decision is not None:
            blit_text(surface, self.decision.mode, (panel.right - 12, panel.y + 8), 14, SKY, 0,
                      "bold", "topright")
            y = panel.y + 32
            for index, (cell, score) in enumerate(self.decision.candidates[:3]):
                chosen = cell == self.decision.cell
                text = f"{index + 1}. {cell_name(cell):<4} score {score:.2f}"
                if self.decision.probs is not None:
                    text = f"{index + 1}. {cell_name(cell):<4} p={chance_text(self.decision.probs[cell[0]][cell[1]])}" \
                           f"  value {score:.2f}"
                blit_text(surface, text, (panel.x + 12, y), 13, BUTTER if chosen else WHITE, 0,
                          "semibold", "topleft")
                y += 19
            stats = self.decision.stats
            if "gamma" in stats:
                blit_text(surface, f"if miss, next best {chance_text(stats['next_miss'])}   gamma={stats['gamma']}",
                          (panel.x + 12, panel.bottom - 22), 12, (160, 200, 240), 0, "medium", "topleft")
        else:
            blit_text(surface, "waiting for first move...", (panel.centerx, panel.centery + 6), 14,
                      (160, 200, 240), 0, "medium")

    # -------------------------------------------------------------------------
    # draw_coin - draws the dog biscuit flip at the start. It goes up,
    # spins (we fake that by squashing it) and comes down, then a big
    # message pops up saying who throws first.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_coin(self, surface):
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((*INK, 150))
        surface.blit(shade, (0, 0))
        t = self.state_time
        spin = abs(math.cos(t * 14 * max(0.15, 1.6 - t))) if t < 1.6 else 1.0
        height = math.sin(min(t, 1.6) / 1.6 * math.pi) * 160
        biscuit = ASSETS.scaled("biscuit", 200)
        center = (SCREEN_WIDTH // 2, 380 - height)
        if biscuit is not None:
            squashed = pygame.transform.smoothscale(biscuit, (biscuit.get_width(),
                                                              max(2, int(biscuit.get_height() * spin))))
            surface.blit(squashed, squashed.get_rect(center=center))
        else:
            pygame.draw.ellipse(surface, CARAMEL, pygame.Rect(0, 0, 180, max(4, int(180 * spin))).move(
                center[0] - 90, center[1] - int(90 * spin)))
        if t > 1.6:
            who = "YOU throw first!" if self.first_player == "human" else f"{self.ai.name} throws first!"
            scale = ease_out_back(min(1.0, (t - 1.6) / 0.4))
            text = render_text(who, 48, BUTTER, 5)
            text = pygame.transform.rotozoom(text, 0, max(0.01, scale))
            surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 560)))

    # -------------------------------------------------------------------------
    # draw_game_over - draws the big wobbly win or lose text (like "YOU WIN!")
    # in the middle of the screen when the match ends.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_game_over(self, surface):
        t = min(1.0, self.state_time / 0.5)
        scale = ease_out_back(t)
        won = self.winner == "human"
        if self.autopilot:
            text = f"{self.autopilot.name.upper()} WINS!" if won else f"{self.ai.name.upper()} WINS!"
        else:
            text = "YOU WIN!" if won else f"{self.ai.name.upper()} WINS"
        image = render_text(text, 72, BUTTER if won else TOMATO, 7)
        image = pygame.transform.rotozoom(image, math.sin(self.time * 3) * 3, max(0.01, scale))
        surface.blit(image, image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))


# =============================================================================
# ResultScene - after the match
# =============================================================================
class ResultScene(Scene):

    # -------------------------------------------------------------------------
    # __init__ - sets up the result screen. We grab the stats from the match
    # (throws, accuracy, hints used), make the Rematch / New opponent / Menu
    # buttons, and fire off some confetti if you won.
    #   app    : the main game app, so we can switch screens later
    #   battle : the match that just ended, where we get all the stats from
    # -------------------------------------------------------------------------
    def __init__(self, app, battle):
        super().__init__(app)
        self.battle = battle
        self.won = battle.winner == "human"
        human_shots = len(battle.human_knowledge.shots)
        ai_shots = len(battle.ai_knowledge.shots)
        who = f"{battle.autopilot.name}'s" if battle.autopilot else "Your"
        self.stats = [
            (f"{who} throws", str(human_shots)),
            (f"{who} accuracy", f"{battle.human_knowledge.hits_so_far() / max(1, human_shots):.0%}"),
            (f"{battle.ai.name}'s throws", str(ai_shots)),
            (f"{battle.ai.name}'s accuracy",
             f"{battle.ai_knowledge.hits_so_far() / max(1, ai_shots):.0%}"),
            ("Hints used", str(BattleScene.HINTS - battle.hints_left)),
        ]
        agent_class = type(battle.ai)
        self.buttons = [
            Button((SCREEN_WIDTH // 2 - 320, 630, 200, 60), "Rematch",
                   lambda: app.switch(PlacementScene(app, agent_class)), BUTTER, 24,
                   pygame.K_RETURN),
            Button((SCREEN_WIDTH // 2 - 100, 630, 200, 60), "New opponent", self.new_opponent,
                   SKY, 20),
            Button((SCREEN_WIDTH // 2 + 120, 630, 200, 60), "Menu", self.menu, CREAM, 24,
                   pygame.K_ESCAPE),
        ]
        self.particles = Particles()
        if self.won:
            for _ in range(8):
                self.particles.burst((random.randint(100, 1180), random.randint(50, 300)),
                                     CONFETTI, 30, 350, 6)

    # -------------------------------------------------------------------------
    # new_opponent - takes you back to pick a different AI to play.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def new_opponent(self):
        from hide_and_sausage.ui.scenes_menu import SelectScene
        self.app.switch(SelectScene(self.app))

    # -------------------------------------------------------------------------
    # menu - takes you back to the title screen.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def menu(self):
        from hide_and_sausage.ui.scenes_menu import TitleScene
        self.app.switch(TitleScene(self.app))

    # -------------------------------------------------------------------------
    # update - runs every frame. Moves the confetti along, and if you won it
    # keeps randomly throwing in more so the party doesn't stop.
    #   dt : how many seconds passed since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        super().update(dt)
        self.particles.update(dt)
        if self.won and random.random() < dt * 2:
            self.particles.burst((random.randint(100, 1180), random.randint(50, 250)), CONFETTI, 20, 300, 5)

    # -------------------------------------------------------------------------
    # draw - draws the result screen: a win or lose picture, the headline
    # (shrunk down if it's too long), the stats panel with the AI's face,
    # and whatever the AI said last.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        self.draw_background(surface, "menu_bg", dim=130)
        art = ASSETS.scaled("victory" if self.won else "defeat", 560, 400)
        if art is not None:
            surface.blit(art, art.get_rect(center=(340, 330 + math.sin(self.time * 2) * 5)))
        headline = "YOU WIN!" if self.won else "YOU LOST..."
        if self.battle.autopilot:
            headline = (self.battle.autopilot.name if self.won else self.battle.ai.name) + " wins!"
        size = 60
        while size > 24 and ASSETS.font(size).size(headline)[0] > 540:
            size -= 4                     # shrink long headlines to fit
        blit_text(surface, headline, (940, 90), size, BUTTER if self.won else TOMATO, 6)

        panel = pygame.Rect(680, 150, 520, 450)
        draw_panel(surface, panel, CREAM)
        portrait = ASSETS.portrait(self.battle.ai.key, "sad" if self.won else "happy", 110)
        if portrait is not None:
            surface.blit(portrait, (panel.right - 125, panel.y + 12))
        y = panel.y + 30
        for label, value in self.stats:
            blit_text(surface, label, (panel.x + 30, y), 20, INK_SOFT, 0, "semibold", "topleft")
            blit_text(surface, value, (panel.x + 330, y), 22, INK, 0, "bold", "topleft")
            y += 42
        quote = self.battle.bubble.text
        font = ASSETS.font(17, "semibold")
        y += 10
        for line in wrap_text(f"{self.battle.ai.name}: \"{quote}\"", font, panel.width - 60):
            surface.blit(font.render(line, True, (60, 110, 60)), (panel.x + 30, y))
            y += font.get_linesize()

        self.particles.draw(surface)
        super().draw(surface)
