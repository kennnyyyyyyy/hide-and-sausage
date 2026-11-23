# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  board_view.py - draws one 10 x 10 garden on the screen. That means the
#  lawn and its grid, the A-J / 1-10 labels, the dogs, tennis balls for
#  misses, dirt holes for BORKs, the AI's heat map, the target box under
#  your mouse, and the tennis ball flying through the air.
# =============================================================================

import math

import pygame

from hide_and_sausage.config import (BOARD_SIZE, CELL_SIZE, BOARD_PIXELS,
                                     ROW_LABELS, INK, CREAM, WHITE, GRASS,
                                     GRASS_DARK, BUTTER, TOMATO, HEAT_COLD,
                                     HEAT_HOT)
from hide_and_sausage.core.board import MISS, HIT, FOUND
from hide_and_sausage.ai.probability import chance_text
from hide_and_sausage.ui.assets import ASSETS
from hide_and_sausage.ui.widgets import render_text


# -----------------------------------------------------------------------------
# heat_colour - picks a colour for the heat map. It goes from cold blue,
# through yellow in the middle, up to hot red.
#   value : how hot the square is, from 0 (cold) to 1 (hot)
# Gives back the colour as (red, green, blue).
# -----------------------------------------------------------------------------
def heat_colour(value):
    value = max(0.0, min(1.0, value))
    if value < 0.5:
        t = value * 2
        return tuple(int(HEAT_COLD[i] + (BUTTER[i] - HEAT_COLD[i]) * t) for i in range(3))
    t = (value - 0.5) * 2
    return tuple(int(BUTTER[i] + (HEAT_HOT[i] - BUTTER[i]) * t) for i in range(3))


class BoardView:
    """Draws one garden at a fixed spot on the screen."""

    # -------------------------------------------------------------------------
    # __init__ - sets up a board at a spot on the screen and draws its lawn
    # once so it's ready to go.
    #   origin : the (x, y) screen spot of the top-left lawn square
    #   title  : the name written above the board
    # -------------------------------------------------------------------------
    def __init__(self, origin, title):
        self.origin = origin
        self.title = title
        self.rect = pygame.Rect(origin[0], origin[1], BOARD_PIXELS, BOARD_PIXELS)
        self.lawn = self.build_lawn()
        self.shake = 0.0

    # -------------------------------------------------------------------------
    # build_lawn - draws the lawn once at the start so we don't redo it every
    # frame. If there's no grass picture it's just a plain pale fill. Then
    # every other square gets a light checker shade and we add grid lines,
    # so the squares are easy to count.
    #   (no parameters)
    # Gives back the finished lawn picture.
    # -------------------------------------------------------------------------
    def build_lawn(self):
        lawn = pygame.Surface((BOARD_PIXELS, BOARD_PIXELS))
        tile = ASSETS.image("grass_tile")
        if tile is not None:
            tile = pygame.transform.smoothscale(tile, (CELL_SIZE * 2, CELL_SIZE * 2))
            for y in range(0, BOARD_PIXELS, tile.get_height()):
                for x in range(0, BOARD_PIXELS, tile.get_width()):
                    lawn.blit(tile, (x, y))
        else:
            lawn.fill(GRASS)
        # light checker pattern so the squares are easy to count
        stripe = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        stripe.fill((255, 255, 255, 28))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 0:
                    lawn.blit(stripe, (col * CELL_SIZE, row * CELL_SIZE))
        for i in range(1, BOARD_SIZE):
            pygame.draw.line(lawn, GRASS_DARK, (i * CELL_SIZE, 0), (i * CELL_SIZE, BOARD_PIXELS), 1)
            pygame.draw.line(lawn, GRASS_DARK, (0, i * CELL_SIZE), (BOARD_PIXELS, i * CELL_SIZE), 1)
        return lawn

    # -------------------------------------------------------------------------
    # cell_at - works out which lawn square a spot on the screen is on.
    #   pos : the (x, y) spot, usually where the mouse is
    # Gives back (row, col), or None if the spot is off the board.
    # -------------------------------------------------------------------------
    def cell_at(self, pos):
        if not self.rect.collidepoint(pos):
            return None
        col = (pos[0] - self.origin[0]) // CELL_SIZE
        row = (pos[1] - self.origin[1]) // CELL_SIZE
        return int(row), int(col)

    # -------------------------------------------------------------------------
    # cell_rect - finds where a lawn square is on the screen.
    #   cell : the square, as (row, col)
    # Gives back the box that square takes up on the screen.
    # -------------------------------------------------------------------------
    def cell_rect(self, cell):
        row, col = cell
        return pygame.Rect(self.origin[0] + col * CELL_SIZE,
                           self.origin[1] + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    # -------------------------------------------------------------------------
    # cell_center - finds the middle of a lawn square on the screen.
    #   cell : the square, as (row, col)
    # Gives back the (x, y) of the middle of that square.
    # -------------------------------------------------------------------------
    def cell_center(self, cell):
        return self.cell_rect(cell).center

    # -------------------------------------------------------------------------
    # draw_frame - draws the white box with a black outline around the
    # board, the A-J / 1-10 labels down the side and along the top, and the
    # board's name above it.
    #   surface : the screen we draw on
    #   glow    : True to put a pulsing yellow edge around this board (it's
    #             the one being thrown at right now)
    # -------------------------------------------------------------------------
    def draw_frame(self, surface, glow=False):
        frame = self.rect.inflate(44, 44).move(-6, -6)
        frame.width -= 0
        pygame.draw.rect(surface, INK, frame.move(0, 6), border_radius=22)
        pygame.draw.rect(surface, WHITE, frame, border_radius=22)
        pygame.draw.rect(surface, INK, frame, 4, border_radius=22)
        if glow:
            pulse = 3 + int(2 * math.sin(pygame.time.get_ticks() / 180))
            pygame.draw.rect(surface, BUTTER, frame.inflate(10, 10), pulse, border_radius=26)

        font = ASSETS.font(15, "bold")
        for i in range(BOARD_SIZE):
            number = font.render(str(i + 1), True, INK)
            surface.blit(number, number.get_rect(center=(self.origin[0] + i * CELL_SIZE + CELL_SIZE // 2,
                                                         self.origin[1] - 15)))
            letter = font.render(ROW_LABELS[i], True, INK)
            surface.blit(letter, letter.get_rect(center=(self.origin[0] - 15,
                                                         self.origin[1] + i * CELL_SIZE + CELL_SIZE // 2)))
        title = render_text(self.title, 22, CREAM, 3)
        surface.blit(title, title.get_rect(midbottom=(self.rect.centerx, frame.top + 4)))

    # -------------------------------------------------------------------------
    # draw_lawn - sticks the ready-made lawn on the screen and puts a black
    # outline around it.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw_lawn(self, surface):
        surface.blit(self.lawn, self.origin)
        pygame.draw.rect(surface, INK, self.rect, 3)

    # -------------------------------------------------------------------------
    # draw_dogs - draws the dog pictures where the dogs are lying.
    #   surface    : the screen we draw on
    #   placements : the dogs to show, and where each one is lying
    #   alpha      : how see-through they are (255 = solid). Lower is used
    #                for "ghost" dogs
    #   tint_found : which dogs have been found, so we draw them a little
    #                faded
    # -------------------------------------------------------------------------
    def draw_dogs(self, surface, placements, alpha=255, tint_found=()):
        for placement in placements:
            sprite = ASSETS.dog_sprite(placement.dog_key, placement.transform)
            if alpha != 255 or placement.dog_key in tint_found:
                sprite = sprite.copy()
                sprite.set_alpha(alpha if alpha != 255 else 205)
            row, col = placement.anchor
            surface.blit(sprite, (self.origin[0] + col * CELL_SIZE,
                                  self.origin[1] + row * CELL_SIZE))

    # -------------------------------------------------------------------------
    # draw_marks - puts a tennis ball on every miss and a dirt hole on every
    # BORK. Squares of a dog that's been fully found get a red outline. If a
    # picture is missing we just draw a simple circle instead.
    #   surface   : the screen we draw on
    #   knowledge : everything known about the throws at this board so far
    #   show_hits : True to draw the holes on BORK squares (found dogs get
    #               drawn on their own anyway)
    # -------------------------------------------------------------------------
    def draw_marks(self, surface, knowledge, show_hits=True):
        ball = ASSETS.scaled("tennis_ball", int(CELL_SIZE * 0.55))
        hole = ASSETS.scaled("dirt_hole", int(CELL_SIZE * 0.9))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                state = knowledge.grid[row][col]
                center = self.cell_center((row, col))
                if state == MISS:
                    if ball is not None:
                        surface.blit(ball, ball.get_rect(center=center))
                    else:
                        pygame.draw.circle(surface, (220, 240, 90), center, CELL_SIZE // 4)
                        pygame.draw.circle(surface, INK, center, CELL_SIZE // 4, 2)
                elif state == HIT and show_hits:
                    if hole is not None:
                        surface.blit(hole, hole.get_rect(center=center))
                    else:
                        pygame.draw.circle(surface, TOMATO, center, CELL_SIZE // 3)
                        pygame.draw.circle(surface, INK, center, CELL_SIZE // 3, 3)
                elif state == FOUND:
                    pygame.draw.rect(surface, TOMATO, self.cell_rect((row, col)).inflate(-4, -4), 2,
                                     border_radius=8)

    # -------------------------------------------------------------------------
    # draw_heat - draws the AI's heat map: see-through coloured squares
    # showing where it thinks the dogs are. The 8 hottest squares also get
    # their chance written on them as a percentage.
    #   surface : the screen we draw on
    #   heat    : a grid of numbers from 0 to 1 saying how strong each colour is
    #   probs   : a grid of the actual chances, to write as numbers (optional)
    #   strength: how visible the whole thing is, 0 to 1 (used to fade it in)
    # -------------------------------------------------------------------------
    def draw_heat(self, surface, heat, probs=None, strength=1.0):
        overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        values = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                value = heat[row][col]
                if value <= 0.001:
                    continue
                overlay.fill((*heat_colour(value), int((45 + 115 * value) * strength)))
                surface.blit(overlay, self.cell_rect((row, col)))
                if probs is not None:
                    values.append((probs[row][col], (row, col)))
        # label the eight hottest squares with their probability
        for probability, cell in sorted(values, reverse=True)[:8]:
            if probability <= 0:
                continue
            label = render_text(chance_text(probability), 13, WHITE, 2)
            surface.blit(label, label.get_rect(center=self.cell_center(cell)))

    # -------------------------------------------------------------------------
    # draw_cursor - draws a target box over a square that gently pulses, with
    # a dot in the middle.
    #   surface : the screen we draw on
    #   cell    : the square to highlight, as (row, col)
    #   colour  : the colour of the target box
    # -------------------------------------------------------------------------
    def draw_cursor(self, surface, cell, colour=BUTTER):
        rect = self.cell_rect(cell)
        pulse = 2 * math.sin(pygame.time.get_ticks() / 120)
        reticle = rect.inflate(6 + pulse, 6 + pulse)
        pygame.draw.rect(surface, INK, reticle.move(0, 2), 5, border_radius=10)
        pygame.draw.rect(surface, colour, reticle, 4, border_radius=10)
        pygame.draw.circle(surface, colour, rect.center, 4)


class FlyingBall:
    """A tennis ball flying in an arc from one point to a lawn square."""

    # -------------------------------------------------------------------------
    # __init__ - starts a new throw.
    #   start    : the (x, y) spot the ball is thrown from
    #   end      : the (x, y) spot where it lands
    #   duration : how many seconds it's in the air
    # -------------------------------------------------------------------------
    def __init__(self, start, end, duration=0.55):
        self.start = start
        self.end = end
        self.duration = duration
        self.age = 0.0

    # -------------------------------------------------------------------------
    # done - tells us if the ball has landed yet (True once it has).
    #   (no parameters)
    # -------------------------------------------------------------------------
    @property
    def done(self):
        return self.age >= self.duration

    # -------------------------------------------------------------------------
    # update - moves the ball further along its flight.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        self.age = min(self.duration, self.age + dt)

    # -------------------------------------------------------------------------
    # draw - draws the spinning ball and its shadow on the ground. The ball
    # goes up in an arc and gets bigger in the middle of the throw, so it
    # looks like it's coming closer.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        t = self.age / self.duration
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t
        height = math.sin(t * math.pi) * 140
        shadow_size = int(10 + 8 * (1 - math.sin(t * math.pi)))
        shadow = pygame.Surface((shadow_size * 2, shadow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surface.blit(shadow, shadow.get_rect(center=(x, y + 6)))
        size = int(CELL_SIZE * (0.55 + 0.45 * math.sin(t * math.pi)))
        ball = ASSETS.scaled("tennis_ball", size)
        if ball is not None:
            ball = pygame.transform.rotate(ball, -t * 720)
            surface.blit(ball, ball.get_rect(center=(x, y - height)))
        else:
            pygame.draw.circle(surface, (220, 240, 90), (int(x), int(y - height)), size // 2)
            pygame.draw.circle(surface, INK, (int(x), int(y - height)), size // 2, 2)
