# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  build_web.py - makes the version of the game that runs in a web browser
#  (the one on GitHub Pages), using a tool called pygbag.
#
#  The browser can't run the game exactly like Windows does, so this script
#  does NOT touch the real code. It copies the game into web_build/ and
#  makes a few small changes to that copy only:
#    * the main loop becomes "async" and lets the browser breathe every
#      frame (browsers freeze if a loop never gives control back)
#    * the AI thinks on the normal game loop instead of a background
#      thread, because browsers don't do threads here
#    * the Quit button is gone (you just close the tab)
#    * sounds get turned into .ogg files, which browsers play happily
#  Left out on purpose: Testing Mode (my private tool) and the music (the
#  Wiener Dog Song isn't mine to put on the internet).
#
#  Usage:  python tools/build_web.py           build into web_build/.../build/web
#          python tools/build_web.py --serve   build, then play it at
#                                              http://localhost:8000
#  Needs:  pip install pygbag   (and ffmpeg for the sound conversion)
# =============================================================================

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGE = ROOT / "web_build" / "hide-and-sausage"       # the copy we patch
OUTPUT = STAGE / "build" / "web"                       # what goes online

LEFT_OUT = {"scenes_testing.py", "__pycache__"}        # never copied to the web


# -----------------------------------------------------------------------------
# copy_game - wipes the old staging folder and copies in a fresh copy of the
# game: the code (minus Testing Mode), the pictures, the fonts, the AI Lab
# results tables, and the sounds turned into .ogg (minus the music).
#   (no parameters)
# -----------------------------------------------------------------------------
def copy_game():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copytree(ROOT / "hide_and_sausage", STAGE / "hide_and_sausage",
                    ignore=lambda folder, names: [n for n in names if n in LEFT_OUT])
    shutil.copytree(ROOT / "assets" / "images", STAGE / "assets" / "images")
    shutil.copytree(ROOT / "assets" / "fonts", STAGE / "assets" / "fonts")
    (STAGE / "results").mkdir()
    for table in (ROOT / "results").glob("*.csv"):
        shutil.copy2(table, STAGE / "results" / table.name)
    shutil.copy2(ROOT / "assets" / "images" / "dogs" / "donut.png", STAGE / "favicon.png")
    convert_sounds()


# -----------------------------------------------------------------------------
# convert_sounds - turns every .wav sound effect into an .ogg file in the
# staging folder, using ffmpeg. The music.mp3 is skipped on purpose.
#   (no parameters)
# -----------------------------------------------------------------------------
def convert_sounds():
    target = STAGE / "assets" / "sounds"
    target.mkdir(parents=True)
    for wav in sorted((ROOT / "assets" / "sounds").glob("*.wav")):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav),
                        "-c:a", "libvorbis", "-q:a", "5", str(target / f"{wav.stem}.ogg")],
                       check=True)


# -----------------------------------------------------------------------------
# patch - swaps one bit of text for another inside a copied file. If the
# old text isn't there (because the real code changed), it stops with an
# error, so we never put a half-patched game online by accident.
#   relative : the file, relative to the staging folder
#   old      : the exact text to look for
#   new      : what to put there instead
#   every    : True to swap every copy of it, not just the first one
# -----------------------------------------------------------------------------
def patch(relative, old, new, every=False):
    path = STAGE / relative
    text = path.read_text(encoding="utf-8")
    if old not in text:
        sys.exit(f"build_web: couldn't find the bit to patch in {relative}:\n{old}")
    path.write_text(text.replace(old, new, -1 if every else 1), encoding="utf-8")


# -----------------------------------------------------------------------------
# write_web_main - writes the browser version of main.py. pygbag looks for
# main.py and needs the game loop to be started with asyncio.run().
#   (no parameters)
# -----------------------------------------------------------------------------
def write_web_main():
    (STAGE / "main.py").write_text(
        '# Hide & Sausage - browser version of main.py, made by tools/build_web.py\n'
        'import asyncio\n\n'
        'import pygame          # pygbag only loads pygame if main.py imports it\n\n'
        'from hide_and_sausage.ui.app import App\n'
        'from hide_and_sausage.ui.scenes_menu import TitleScene\n\n\n'
        '# main - opens the game and starts on the title screen.\n'
        'async def main():\n'
        '    app = App()\n'
        '    await app.run(TitleScene(app))\n\n\n'
        'asyncio.run(main())\n', encoding="utf-8")


# -----------------------------------------------------------------------------
# patch_for_browser - makes all the small browser-only changes to the copy.
#   (no parameters)
# -----------------------------------------------------------------------------
def patch_for_browser():
    write_web_main()

    # the main loop: async, and hand control back to the browser every frame
    app = "hide_and_sausage/ui/app.py"
    patch(app, "import os\n", "import asyncio\nimport os\n")
    # in the browser the sound part of pygame has to be asked for by name
    patch(app, "import pygame\n",
          "import pygame\ntry:\n    import pygame.mixer\nexcept ImportError:\n    pass\n")
    patch(app, "        pygame.mixer.pre_init(44100, -16, 1, 512)\n",
          "        if hasattr(pygame, \"mixer\"):\n"
          "            pygame.mixer.pre_init(44100, -16, 1, 512)\n")
    # the web page already stretches the game to fit, so no SCALED window
    # (it would mix up where the mouse is)
    patch(app, 'flags = 0 if os.environ.get("HS_HEADLESS") else pygame.SCALED | pygame.RESIZABLE',
          "flags = 0")
    patch(app, "    def run(self, first_scene):", "    async def run(self, first_scene):")
    patch(app, "            pygame.display.flip()\n",
          "            pygame.display.flip()\n"
          "            await asyncio.sleep(0)          # web: let the browser show the frame\n"
          "            self.web_frames = getattr(self, 'web_frames', 0) + 1\n"
          "            if self.web_frames in (2, 30, 90):   # web: fit the page again once it's showing\n"
          "                try:\n"
          "                    import platform\n"
          "                    platform.window.window_resize()\n"
          "                except Exception:\n"
          "                    pass\n")

    # the page sizes itself before the game window exists, which can leave
    # the game squashed, so ask it to fit itself to the 16:9 game again
    patch(app, "        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))\n",
          "        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))\n"
          "        try:\n"
          "            import platform\n"
          "            platform.window.window_resize()\n"
          "        except Exception:\n"
          "            pass\n")
    # no threads in the browser: the AI does its thinking on the next frame
    # instead (after the "thinking..." screen has been drawn once)
    game = "hide_and_sausage/ui/scenes_game.py"
    patch(game, "        self.thinking_thread = threading.Thread(target=think, daemon=True)\n"
                "        self.thinking_thread.start()\n",
          "        self.thinking_thread = think       # web: update() runs this next frame\n")
    patch(game, "        elif state == \"ai_think\":\n",
          "        elif state == \"ai_think\":\n"
          "            if self.thinking_thread is not None and self.state_time > 0.05:\n"
          "                job, self.thinking_thread = self.thinking_thread, None\n"
          "                job()\n")

    # a Quit button makes no sense in a browser tab
    patch("hide_and_sausage/ui/scenes_menu.py",
          "        self.buttons.append(Button((x, y, 300, 46), \"Quit\", app.quit, (240, 170, 160), 22,\n"
          "                                   pygame.K_ESCAPE))\n", "")
    # no music on the web, so no music key and no music credit either
    patch("hide_and_sausage/ui/scenes_menu.py", '"M: music   F11: fullscreen"', '"F11: fullscreen"')
    patch("hide_and_sausage/ui/scenes_menu.py",
          '        blit_text(surface, "Music: Wiener Dog Song (all rights to its creator)",\n'
          '                  (12, 12), 13, WHITE, 2, "semibold", "topleft")\n', "")

    # the sounds are .ogg files in the web copy, and if the browser has no
    # sound at all the game just stays quiet instead of crashing
    assets = "hide_and_sausage/ui/assets.py"
    patch(assets, 'if file_name.endswith(".wav"):', 'if file_name.endswith(".ogg"):')
    patch(assets, "import pygame\n",
          "import pygame\ntry:\n    import pygame.mixer\nexcept ImportError:\n    pass\n")
    patch(assets, "pygame.mixer.get_init()",
          '(hasattr(pygame, "mixer") and pygame.mixer.get_init())', every=True)


# -----------------------------------------------------------------------------
# run_pygbag - packs the patched copy into a web page with pygbag. With
# serve=True it also starts a little web server on http://localhost:8000
# so you can try it before putting it online (Ctrl+C stops it).
# "--ume_block 0" makes the game start straight away, without pygbag's
# "Ready to start! Please click/touch page" screen.
#   serve : True to keep a local server running after the build
# -----------------------------------------------------------------------------
def run_pygbag(serve):
    command = [sys.executable, "-m", "pygbag", "--app_name", "hide-and-sausage",
               "--title", "Hide & Sausage", "--ume_block", "0"]
    if not serve:
        command.append("--build")
    subprocess.run(command + [str(STAGE)], check=True, cwd=STAGE)    # cwd: finds favicon.png


# -----------------------------------------------------------------------------
# main - copies, patches and builds the web version, then says where it is.
#   (no parameters)
# -----------------------------------------------------------------------------
def main():
    copy_game()
    patch_for_browser()
    serve = "--serve" in sys.argv
    if not serve:
        run_pygbag(serve=False)
        print(f"Web build ready: {OUTPUT}")
    else:
        run_pygbag(serve=True)


if __name__ == "__main__":
    main()
