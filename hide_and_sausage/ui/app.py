# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  app.py - the main game loop, plus the "scene" setup.
#
#  The game is split into SCENES, basically one per screen (title screen,
#  picking an opponent, hiding your dogs, the battle, results...). Only one
#  scene is on at a time. Every frame the App:
#                         1. gives the mouse/keyboard stuff to the scene
#                         2. lets the scene move its animations along
#                         3. lets the scene draw itself
#  When we change scene the screen fades to black and back, so it feels
#  like a proper game.
# =============================================================================

import os
import sys

import pygame

from hide_and_sausage.config import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
                                     GAME_TITLE, INK, PAPER)
from hide_and_sausage.ui.assets import ASSETS


class Scene:
    """Base class every screen of the game inherits from."""

    # -------------------------------------------------------------------------
    # __init__ - sets up a scene. Every scene keeps a link to the App so it
    # can do things like switch to another scene.
    #   app : the game that's running right now
    # -------------------------------------------------------------------------
    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.time = 0.0

    # -------------------------------------------------------------------------
    # handle_event - the normal version just hands the event to each button
    # until one of them uses it.
    #   event : the mouse or keyboard thing that just happened
    # Gives back True if a button got pressed.
    # -------------------------------------------------------------------------
    def handle_event(self, event):
        for button in list(self.buttons):
            if button.handle_event(event):
                return True
        return False

    # -------------------------------------------------------------------------
    # update - the normal version just counts up the time and lets the
    # buttons do their little animations.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        for button in self.buttons:
            button.update(dt)

    # -------------------------------------------------------------------------
    # draw - the normal version just draws the buttons.
    #   surface : the 1280 x 720 game screen we draw on
    # -------------------------------------------------------------------------
    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)

    # -------------------------------------------------------------------------
    # draw_background - fills the whole screen with a background picture. If
    # the picture isn't there we just fill it with the plain paper colour.
    #   surface : the screen we draw on
    #   name    : the picture's name inside assets/images
    #   colour  : not used anymore (a missing picture just means plain paper)
    #   dim     : how much to darken the picture, 0-255, so stuff on top is
    #             easier to read (only used when there is a picture)
    # -------------------------------------------------------------------------
    @staticmethod
    def draw_background(surface, name, colour=(150, 205, 120), dim=0):
        image = ASSETS.image(name)
        if image is None:                  # no picture: a plain sheet of paper
            surface.fill(PAPER)
            return
        surface.blit(image, (0, 0))
        if dim:
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((*INK, dim))
            surface.blit(shade, (0, 0))


class App:
    """Owns the window, the clock, the current scene and shared game data."""

    # -------------------------------------------------------------------------
    # __init__ - starts pygame, opens the window, loads the sounds and sets
    # the little window icon. No scene is showing yet at this point.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        # SCALED lets the 1280x720 screen stretch to fit any window size or
        # fullscreen. (The automatic screenshot tour runs without a real window.)
        flags = 0 if os.environ.get("HS_HEADLESS") else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        ASSETS.load()
        icon = ASSETS.scaled("dogs/donut", 64)
        if icon is not None:
            pygame.display.set_icon(icon)

        self.scene = None
        self.next_scene = None
        self.fade = 0.0                      # 0 = clear, 1 = fully black
        self.fading_out = False
        self.running = True

    # -------------------------------------------------------------------------
    # switch - asks to go to a new scene. The very first scene just shows up
    # straight away, after that the swap happens while the screen is faded.
    #   scene : the scene we want to show next
    # -------------------------------------------------------------------------
    def switch(self, scene):
        if self.scene is None:
            self.scene = scene
            return
        self.next_scene = scene
        self.fading_out = True

    # -------------------------------------------------------------------------
    # quit - tells the main loop to stop, so the game closes.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def quit(self):
        self.running = False

    # -------------------------------------------------------------------------
    # handle_global_keys - deals with the keys that work on every screen.
    # F11 = fullscreen on/off, M = music on/off.
    #   event : the key press that just happened
    # Gives back True if it was one of those keys, so the scene doesn't
    # get it as well.
    # -------------------------------------------------------------------------
    def handle_global_keys(self, event):
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return True
        if event.key == pygame.K_m:
            ASSETS.toggle_music()
            return True
        return False

    # -------------------------------------------------------------------------
    # run - the main loop. It keeps going until the player quits. Each frame
    # it handles input, updates the fade and the scene, draws everything,
    # then puts it on the window.
    #   first_scene : the scene to start on (the title screen)
    # -------------------------------------------------------------------------
    def run(self, first_scene):
        self.switch(first_scene)
        ASSETS.start_music()
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and self.handle_global_keys(event):
                    continue
                elif not self.fading_out:
                    self.scene.handle_event(event)

            self.update_fade(dt)
            self.scene.update(dt)
            self.scene.draw(self.canvas)
            if self.fade > 0:
                shade = pygame.Surface(self.canvas.get_size())
                shade.fill(INK)
                shade.set_alpha(int(255 * self.fade))
                self.canvas.blit(shade, (0, 0))
            self.screen.blit(self.canvas, (0, 0))
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # -------------------------------------------------------------------------
    # update_fade - handles the fade between scenes. First it fades to
    # black, then swaps in the new scene once it's fully black, then fades
    # back in.
    #   dt : how many seconds since the last frame
    # -------------------------------------------------------------------------
    def update_fade(self, dt):
        if self.fading_out:
            self.fade = min(1.0, self.fade + dt * 5)
            if self.fade >= 1.0:
                self.scene = self.next_scene
                self.next_scene = None
                self.fading_out = False
        elif self.fade > 0:
            self.fade = max(0.0, self.fade - dt * 4)
