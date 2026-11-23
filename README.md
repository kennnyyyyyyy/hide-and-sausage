# Hide & Sausage 🌭🐕

**Play in your browser: https://kennnyyyyyyy.github.io/hide-and-sausage/** (no download)

**5FTC2067 Artificial Intelligence Principles - Mini Project**
Student Name: `Kenzo Jonathan Harapan Ji` · Student ID: `4234QLMV`

Battleship, but the ships are dachshunds hiding in a garden. You throw tennis
balls; a hit goes **BORK!** Find the whole pack before the AI finds yours.

## Play

* **Windows (no Python needed):** run `HideAndSausage.exe` from the `dist` folder.
* **From source:** `python -m pip install pygame-ce numpy` then `python main.py`
* **In the browser:** the link at the top (built with `python tools/build_web.py`,
  which packs the game with pygbag; the web version has no music).

Controls: click to throw · drag dogs to hide them · `R` rotate · `F` flip ·
`B` toggle the AI's Brain View · `H` hint · `M` music · `F11` fullscreen.

## The AI opponents

| Level | Opponent | Technique |
|---|---|---|
| 1 | Pupper | Random throws (the baseline) |
| 2 | Good Boy | Hunt & Target (random until a BORK, then search around it) |
| 3 | The Dogfather | Counts every possible dog position → probabilities, then **Expectimax** (weighs BORK and miss for each throw, one throw ahead) + adversarial hiding |

The chance element: you never know where the dogs are (hidden information), and a
dog-biscuit coin flip decides who starts. The Dogfather treats each throw as a
**chance node** (BORK or miss, with probabilities from counting every possible
dog position), imagines each result, and picks the throw with the best expected
outcome over the next two throws.

## The experiment

`python tournament.py 100` makes every AI search the same 100 random gardens
and play a round-robin against every other AI. Results go to `results/` (CSV +
charts) and appear in the in-game **AI Lab**.

## Project layout

```
main.py                     start the game
tournament.py               the AI comparison experiment
hide_and_sausage/
  config.py                 every setting in one place
  core/fleet.py             dog shapes, rotations, every legal placement
  core/board.py             rules: Garden (truth) and Knowledge (what you've seen)
  ai/probability.py         counting dog positions: heat map + probabilities
  ai/agents.py              the three AI opponents
  ai/reactions.py           trash talk
  ui/...                    pygame screens, board drawing, widgets, assets
drawings/                   the hand-drawn pictures (PNG) the game uses
DRAWING_PACK/               what to draw + DRAWING_CHECKLIST.md
tools/                      drawing processing, sound synth, screenshots, tests
assets/                     game-ready images, fonts, sounds, music
```

## Credits

* Art: hand-drawn in Excalidraw (editable files in `art/excalidraw`), no image
  generator used.
* Music: the class version plays the "Wiener Dog Song". It belongs to its
  creator, so it is not included here; drop your own `assets/sounds/music.mp3`
  in and the game will play it.
* Sound effects: synthesised from code (`tools/make_sounds.py`).
* Font: Poppins (SIL Open Font License).
* Everything else: written by me.
