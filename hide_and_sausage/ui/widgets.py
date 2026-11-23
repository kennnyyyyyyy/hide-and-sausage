# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  widgets.py - the little UI bits we use all over the game. Panels and
#  buttons with a thick black outline, text with an outline around it, a
#  speech bubble that types itself out, particles, and pop-up words like
#  "BORK!" that bounce in and float away.
# =============================================================================

import math
import random

import pygame

from hide_and_sausage.config import (INK, INK_SOFT, CREAM, CREAM_DARK, BUTTER,
                                     WHITE, TOMATO)
from hide_and_sausage.ui.assets import ASSETS


# -----------------------------------------------------------------------------
# draw_panel - draws a rounded box with a thick black outline and a solid
# shadow underneath it.
#   surface : the screen (or image) we draw on
#   rect    : where the box goes and how big it is
#   fill    : the colour inside the box
#   radius  : how round the corners are
#   border  : how thick the outline is
#   shadow  : how far down the shadow sticks out (0 means no shadow)
# -----------------------------------------------------------------------------
def draw_panel(surface, rect, fill=CREAM, radius=18, border=4, shadow=6):
    if shadow:
        shadow_rect = rect.move(0, shadow)
        pygame.draw.rect(surface, INK, shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, INK, rect, border, border_radius=radius)


# -----------------------------------------------------------------------------
# render_text - turns some words into a picture, with an outline around the
# letters if you want one (like comic book text).
#   text    : the words to write
#   size    : how big the font is
#   colour  : the colour of the letters
#   outline : how thick the outline is in pixels (0 means no outline)
#   weight  : how bold the font is, like "bold" or "semibold"
#   outline_colour : the colour of the outline
# Gives back the text as an image we can stick on the screen. For the
# outline we just draw the words a bunch of times in a little circle around
# the middle, then put the real letters on top.
# -----------------------------------------------------------------------------
def render_text(text, size, colour=INK, outline=0, weight="bold",
                outline_colour=INK):
    font = ASSETS.font(size, weight)
    inner = font.render(text, True, colour)
    if not outline:
        return inner
    w, h = inner.get_width() + outline * 2, inner.get_height() + outline * 2
    result = pygame.Surface((w, h), pygame.SRCALPHA)
    edge = font.render(text, True, outline_colour)
    for angle in range(0, 360, 30):
        dx = round(math.cos(math.radians(angle)) * outline)
        dy = round(math.sin(math.radians(angle)) * outline)
        result.blit(edge, (outline + dx, outline + dy))
    result.blit(inner, (outline, outline))
    return result


# -----------------------------------------------------------------------------
# blit_text - makes the text and puts it on the screen in one go.
#   surface : the screen we draw on
#   text    : the words to write
#   pos     : the (x, y) spot to put the text at
#   size, colour, outline, weight : same as in render_text
#   anchor  : which part of the text sits on pos ("center", "topleft", ...)
# Gives back the box the text ended up in, in case we need it.
# -----------------------------------------------------------------------------
def blit_text(surface, text, pos, size, colour=INK, outline=0, weight="bold",
              anchor="center"):
    image = render_text(text, size, colour, outline, weight)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)
    return rect


# -----------------------------------------------------------------------------
# wrap_text - chops a long sentence into lines so it fits inside a box.
#   text   : the sentence to chop up
#   font   : the font it'll be drawn with (so we can measure the words)
#   width  : how wide one line is allowed to be, in pixels
# Gives back a list of lines. We just keep adding words to the line until
# the next one won't fit, then start a new line.
# -----------------------------------------------------------------------------
def wrap_text(text, font, width):
    lines, current = [], ""
    for word in text.split():
        attempt = f"{current} {word}".strip()
        if font.size(attempt)[0] <= width:
            current = attempt
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# =============================================================================
# Button - a chunky clickable button that squishes when you press it.
# =============================================================================
class Button:

    # -------------------------------------------------------------------------
    # __init__ - sets up a new button.
    #   rect     : where the button goes and how big it is (x, y, w, h)
    #   label    : the words on the button
    #   on_click : the function we run when it gets clicked
    #   fill     : the button's colour
    #   size     : how big the text is
    #   hotkey   : a keyboard key that presses it too (optional)
    # -------------------------------------------------------------------------
    def __init__(self, rect, label, on_click, fill=BUTTER, size=26, hotkey=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.fill = fill
        self.size = size
        self.hotkey = hotkey
        self.hovered = False
        self.pressed = False
        self.enabled = True
        self.wobble = 0.0

    # -------------------------------------------------------------------------
    # handle_event - checks if the mouse or keyboard did something to this
    # button. Hovering plays a little sound and makes it wiggle. A click only
    # counts if you press AND let go while you're still on the button.
    #   event : the mouse or keyboard thing that just happened
    # Gives back True if the button got pressed.
    # -------------------------------------------------------------------------
    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            was = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            if self.hovered and not was:
                ASSETS.play("hover", 0.5)
                self.wobble = 1.0
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            fire = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            if fire:
                ASSETS.play("click")
                self.on_click()
                return True
        elif event.type == pygame.KEYDOWN and self.hotkey and event.key == self.hotkey:
            ASSETS.play("click")
            self.on_click()
            return True
        return False

    # -------------------------------------------------------------------------
    # update - slowly calms the hover wiggle down until it stops.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        self.wobble = max(0.0, self.wobble - dt * 4)

    # -------------------------------------------------------------------------
    # draw - draws the button. It pops up a bit when you hover over it and
    # squishes down when you press it. Turned-off buttons go grey.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        lift = 0 if self.pressed else (3 if self.hovered else 0)
        rect = self.rect.move(0, -lift + (3 if self.pressed else 0))
        fill = self.fill if self.enabled else CREAM_DARK
        if self.hovered and self.enabled:
            fill = tuple(min(255, c + 18) for c in fill)
        draw_panel(surface, rect, fill, radius=rect.height // 2 - 2, border=4,
                   shadow=0 if self.pressed else 6 + lift)
        # little shine stripe at the top
        shine = pygame.Rect(rect.x + rect.height // 3, rect.y + 7,
                            rect.width - rect.height // 1.5, 6)
        pygame.draw.rect(surface, WHITE, shine, border_radius=3)
        angle = math.sin(self.wobble * 12) * self.wobble * 3
        text = render_text(self.label, self.size, INK if self.enabled else INK_SOFT)
        if angle:
            text = pygame.transform.rotate(text, angle)
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 2)))


# =============================================================================
# SpeechBubble - the AI's thoughts, typed out letter by letter.
# =============================================================================
class SpeechBubble:

    # -------------------------------------------------------------------------
    # __init__ - makes an empty speech bubble.
    #   rect : where the bubble sits on the screen and how big it is
    # -------------------------------------------------------------------------
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.shown = 0.0
        self.speed = 70          # letters per second

    # -------------------------------------------------------------------------
    # say - gives the bubble a new line and starts typing it from the start.
    #   text : what the AI wants to say
    # -------------------------------------------------------------------------
    def say(self, text):
        self.text = text
        self.shown = 0.0

    # -------------------------------------------------------------------------
    # update - shows a few more letters, so it looks like it's being typed.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        self.shown = min(len(self.text), self.shown + dt * self.speed)

    # -------------------------------------------------------------------------
    # draw - draws the bubble, with a little pointy tail going up to the
    # AI's face, and the letters that have been typed so far.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        draw_panel(surface, self.rect, WHITE, radius=20, border=4, shadow=5)
        tail = [(self.rect.centerx - 14, self.rect.top + 2),
                (self.rect.centerx + 14, self.rect.top + 2),
                (self.rect.centerx, self.rect.top - 18)]
        pygame.draw.polygon(surface, WHITE, tail)
        pygame.draw.lines(surface, INK, False, [tail[0], tail[2], tail[1]], 4)
        font = ASSETS.font(16, "semibold")
        visible = self.text[:int(self.shown)]
        y = self.rect.top + 14
        for line in wrap_text(visible, font, self.rect.width - 28):
            surface.blit(font.render(line, True, INK), (self.rect.left + 14, y))
            y += font.get_linesize()


# =============================================================================
# Particles - confetti, grass clippings, water spray...
# =============================================================================
class Particles:

    # -------------------------------------------------------------------------
    # __init__ - starts with no particles at all.
    #   (no parameters)
    # Each particle in self.items is just a list:
    #   [x, y, speed x, speed y, life left, starting life, colour, size, falls?]
    # -------------------------------------------------------------------------
    def __init__(self):
        self.items = []

    # -------------------------------------------------------------------------
    # burst - shoots a bunch of particles out in random directions, like a
    # little explosion of confetti.
    #   pos     : the (x, y) spot they all start from
    #   colours : the colours we randomly pick from
    #   count   : how many particles to make
    #   speed   : how fast they fly out
    #   size    : roughly how big each one is, in pixels
    #   gravity : True if they should get a small hop up and then fall down
    # -------------------------------------------------------------------------
    def burst(self, pos, colours, count=18, speed=220, size=5, gravity=True):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = random.uniform(0.4, 1.0) * speed
            life = random.uniform(0.5, 1.0)
            self.items.append([pos[0], pos[1], math.cos(angle) * velocity,
                               math.sin(angle) * velocity - (120 if gravity else 0),
                               life, life, random.choice(colours),
                               random.uniform(size * 0.6, size * 1.3), gravity])

    # -------------------------------------------------------------------------
    # update - moves every particle a bit, pulls the falling ones down, and
    # throws away the ones whose time is up.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        alive = []
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            if p[8]:
                p[3] += 600 * dt
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    # -------------------------------------------------------------------------
    # draw - draws every particle as a dot that gets smaller as it runs out
    # of life.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        for x, y, _, _, life, max_life, colour, size, _ in self.items:
            radius = max(1, int(size * life / max_life))
            pygame.draw.circle(surface, colour, (int(x), int(y)), radius)


# =============================================================================
# PopText - a word or picture that pops up, bounces, then floats away.
# =============================================================================
class PopText:

    # -------------------------------------------------------------------------
    # __init__ - sets up a new pop-up.
    #   pos      : the (x, y) spot where it shows up
    #   text     : the word to show (we skip it if an image is given)
    #   colour   : the colour of the letters
    #   size     : how big the text is
    #   image    : a picture to pop instead of text (optional)
    #   duration : how many seconds it stays before it's gone
    # -------------------------------------------------------------------------
    def __init__(self, pos, text="", colour=TOMATO, size=40, image=None, duration=1.0):
        self.pos = pos
        self.image = image if image is not None else render_text(text, size, colour, 4,
                                                                 outline_colour=WHITE)
        self.age = 0.0
        self.duration = duration

    # -------------------------------------------------------------------------
    # alive - tells us if the pop-up is still showing. True until its time
    # runs out.
    #   (no parameters)
    # -------------------------------------------------------------------------
    @property
    def alive(self):
        return self.age < self.duration

    # -------------------------------------------------------------------------
    # update - just adds to how long the pop-up has been around.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        self.age += dt

    # -------------------------------------------------------------------------
    # draw - draws the pop-up. It grows in with a springy "boing", tilts
    # side to side a little, floats upward, and fades out near the end.
    #   surface : the screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        t = self.age / self.duration
        scale = 1 + math.sin(min(t * 8, math.pi)) * 0.35 if t < 0.4 else 1.0
        scale *= min(1.0, t * 10)
        if scale <= 0.05:
            return
        image = pygame.transform.rotozoom(self.image, math.sin(t * 9) * 6, scale)
        if t > 0.6:
            image.set_alpha(int(255 * (1 - (t - 0.6) / 0.4)))
        rect = image.get_rect(center=(self.pos[0], self.pos[1] - t * 40))
        surface.blit(image, rect)


# -----------------------------------------------------------------------------
# ease_out_back - a curve for smooth movement that goes a bit too far and
# then settles back. It's what makes stuff feel bouncy and cartoony.
#   t : how far along the movement is, from 0 (start) to 1 (end)
# Gives back the eased amount, which is 1 at the end but goes a little over
# 1 just before that.
# -----------------------------------------------------------------------------
def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
