# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  assets.py - loads the pictures, fonts and sounds just once, then hands
#  them out to whoever needs them.
#
#  If a file is missing the game does NOT crash. You just get a simple
#  stand-in instead (plain paper, a plain font, a sausage drawn in code), so
#  the game always works even if some art isn't there.
# =============================================================================

import os

import pygame

from hide_and_sausage.config import (IMAGE_DIR, SOUND_DIR, ASSET_DIR, CELL_SIZE,
                                     INK, CARAMEL, CREAM)
from hide_and_sausage.core.fleet import DOG_BY_KEY, shape_for

FONT_DIR = os.path.join(ASSET_DIR, "fonts")
FONT_FILES = {"regular": "Poppins-Regular.ttf", "medium": "Poppins-Medium.ttf",
              "semibold": "Poppins-SemiBold.ttf", "bold": "Poppins-Bold.ttf"}


class Assets:
    """One shared bag of images, fonts and sounds."""

    # -------------------------------------------------------------------------
    # __init__ - sets up empty storage for the images, fonts and sounds, and
    # turns music and sound on. You call load() once pygame is ready.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def __init__(self):
        self.images = {}
        self.fonts = {}
        self.sounds = {}
        self.sprite_cache = {}
        self.sound_on = True
        self.music_on = True

    # -------------------------------------------------------------------------
    # load - loads every .wav sound in the sounds folder (if the sound system
    # is working). Pictures and fonts only get loaded the first time someone
    # asks for them, so the game starts up quicker.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def load(self):
        if pygame.mixer.get_init():
            for file_name in os.listdir(SOUND_DIR) if os.path.isdir(SOUND_DIR) else []:
                if file_name.endswith(".wav"):
                    name = file_name[:-4]
                    self.sounds[name] = pygame.mixer.Sound(os.path.join(SOUND_DIR, file_name))

    # -------------------------------------------------------------------------
    # image - gets a picture from assets/images, and remembers it so we only
    # load it once.
    #   name : the picture's name, like "logo" or "opponents/dogfather_happy"
    # Gives back the picture, or None if the file isn't there.
    # -------------------------------------------------------------------------
    def image(self, name):
        if name not in self.images:
            path = os.path.join(IMAGE_DIR, f"{name}.png")
            if os.path.exists(path):
                self.images[name] = pygame.image.load(path).convert_alpha()
            else:
                self.images[name] = None
        return self.images[name]

    # -------------------------------------------------------------------------
    # scaled - gets a picture shrunk or stretched to fit inside a box, without
    # squashing it. We remember the result so we don't resize it every frame.
    #   name   : the picture's name, same as for image()
    #   width  : how wide it can be at most
    #   height : how tall it can be at most (same as width if left out)
    # Gives back the resized picture, or None if the file isn't there.
    # -------------------------------------------------------------------------
    def scaled(self, name, width, height=None):
        height = height or width
        key = ("scaled", name, width, height)
        if key not in self.sprite_cache:
            source = self.image(name)
            if source is None:
                self.sprite_cache[key] = None
            else:
                scale = min(width / source.get_width(), height / source.get_height())
                size = (max(1, int(source.get_width() * scale)),
                        max(1, int(source.get_height() * scale)))
                self.sprite_cache[key] = pygame.transform.smoothscale(source, size)
        return self.sprite_cache[key]

    # -------------------------------------------------------------------------
    # portrait - gets an opponent's face for a certain mood, sized to fit a
    # box. If there's no picture for that mood we just use the normal face.
    #   key  : which opponent, like "dogfather"
    #   mood : "neutral", "happy", "shocked" or "sad"
    #   size : how big the box is, in pixels
    # Gives back the face picture, or None if there isn't one at all.
    # -------------------------------------------------------------------------
    def portrait(self, key, mood, size):
        picture = self.scaled(f"opponents/{key}_{mood}", size)
        if picture is None:
            picture = self.scaled(f"opponents/{key}_neutral", size)
        return picture

    # -------------------------------------------------------------------------
    # font - gets the Poppins font at a certain size and boldness, and
    # remembers it. If the font file is missing we fall back to Segoe UI.
    #   size   : how big the font is
    #   weight : how bold it is: "regular", "medium", "semibold" or "bold"
    # Gives back the font, ready to draw text with.
    # -------------------------------------------------------------------------
    def font(self, size, weight="bold"):
        key = (size, weight)
        if key not in self.fonts:
            path = os.path.join(FONT_DIR, FONT_FILES[weight])
            if os.path.exists(path):
                self.fonts[key] = pygame.font.Font(path, size)
            else:
                self.fonts[key] = pygame.font.SysFont("segoeui", size, bold=weight == "bold")
        return self.fonts[key]

    # -------------------------------------------------------------------------
    # play - plays a sound effect, but only if sound is on and we actually
    # have that sound.
    #   name   : the sound's file name, without the .wav bit
    #   volume : how loud, from 0 (silent) to 1 (full)
    # -------------------------------------------------------------------------
    def play(self, name, volume=1.0):
        sound = self.sounds.get(name)
        if sound is not None and self.sound_on:
            sound.set_volume(volume)
            sound.play()

    # -------------------------------------------------------------------------
    # start_music - starts the background music and keeps looping it, as
    # long as music is on and the music file is there.
    #   (no parameters)
    # -------------------------------------------------------------------------
    def start_music(self):
        path = os.path.join(SOUND_DIR, "music.mp3")     # the Wiener Dog Song
        if pygame.mixer.get_init() and os.path.exists(path) and self.music_on:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)

    # -------------------------------------------------------------------------
    # toggle_music - flips the music on or off (this is what the M key does).
    #   (no parameters)
    # -------------------------------------------------------------------------
    def toggle_music(self):
        self.music_on = not self.music_on
        if self.music_on:
            self.start_music()
        elif pygame.mixer.get_init():
            pygame.mixer.music.stop()

    # -------------------------------------------------------------------------
    # dog_sprite - gets a dog's picture, turned and flipped the same way the
    # dog is lying on the lawn, and stretched to fit its squares. We
    # remember each one because rotating pictures is slow.
    #   dog_key   : which dog we want
    #   transform : how the dog is turned and flipped
    #   cell      : how big one lawn square is, in pixels
    # Gives back the dog picture (or a drawn sausage if the art is missing).
    # -------------------------------------------------------------------------
    def dog_sprite(self, dog_key, transform, cell=CELL_SIZE):
        key = ("dog", dog_key, transform, cell)
        if key in self.sprite_cache:
            return self.sprite_cache[key]

        dog = DOG_BY_KEY[dog_key]
        shape = shape_for(dog, transform)
        rows = max(r for r, _ in shape) + 1
        cols = max(c for _, c in shape) + 1
        source = self.image(f"dogs/{dog_key}")
        if source is None:
            sprite = self.placeholder_dog(shape, rows, cols, cell)
        else:
            sprite = source
            if transform.mirrored:
                sprite = pygame.transform.flip(sprite, True, False)
            # pygame rotates anticlockwise for positive angles
            sprite = pygame.transform.rotate(sprite, -90 * transform.quarter_turns)
            sprite = pygame.transform.smoothscale(sprite, (cols * cell, rows * cell))
        self.sprite_cache[key] = sprite
        return sprite

    # -------------------------------------------------------------------------
    # placeholder_dog - draws a simple stand-in dog in code when the picture
    # is missing. It's just a rounded brown block with a dot on each square.
    #   shape      : the squares the dog takes up
    #   rows, cols : how many squares tall and wide the dog is overall
    #   cell       : how big one square is, in pixels
    # Gives back the drawn dog as a picture.
    # -------------------------------------------------------------------------
    @staticmethod
    def placeholder_dog(shape, rows, cols, cell):
        surface = pygame.Surface((cols * cell, rows * cell), pygame.SRCALPHA)
        for row, col in shape:
            rect = pygame.Rect(col * cell + 3, row * cell + 3, cell - 6, cell - 6)
            pygame.draw.rect(surface, CARAMEL, rect, border_radius=cell // 3)
            pygame.draw.rect(surface, INK, rect, 3, border_radius=cell // 3)
            pygame.draw.circle(surface, CREAM, rect.center, cell // 8)
        return surface


# The one shared Assets that the whole game uses
ASSETS = Assets()
