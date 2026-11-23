# Hide & Sausage: how the code works

Student Name: Kenzo Jonathan Harapan Ji · Student ID: 4234QLMV

This guide follows the data: **rules → AI → screens**. Read each section next to
its file. Section 7 gives an order for rewriting the code yourself.

---

## 1. The big picture

```
main.py ──► ui/app.py (game loop + scenes)
              │
              ├── ui/scenes_menu.py   title, opponent select, how-to, AI lab
              └── ui/scenes_game.py   placement ─► battle ─► results
                        │
                        ├── core/board.py   Garden (truth) + Knowledge (what you've seen)
                        ├── core/fleet.py   dog shapes + every legal placement
                        └── ai/agents.py    the 3 opponents
                               └── ai/probability.py   counting → heat map / probabilities
```

The most important design decision: **the AI only ever receives a `Knowledge`
object, never the `Garden`.** It cannot see where your dogs are, so it can't
cheat. Everything it knows, it has to work out from misses and BORKs.

---

## 2. `core/fleet.py`: the dogs as geometry

* A **cell** is `(row, col)`. A dog is a set of cells. Big Frank's shape is
  `((0,0),(0,1),(0,2),(0,3),(0,4))`, Boomerang is an L, Donut is a 2×2 square.
* A `Transform` = a number of 90° clockwise turns + an optional mirror. There are
  8 of them. Mirroring is `col → -col`; a clockwise turn is `(row, col) → (col, -row)`;
  then `normalise_cells` slides the shape back to (0,0).
* `unique_shapes(dog)`: a straight dog has 8 transforms but only **2 different
  outlines** (across and down). Each outline must be counted once, or the AI would
  think straight dogs are 4× more likely than they really are.
* `PLACEMENT_TABLE` is built once at start-up: every legal spot for every dog
  (Nugget 180, Bean 160, Long Boi 140, Big Frank 120, Boomerang 576, Donut 81).

## 3. `core/board.py`: the rules

* `Garden`: where one player's dogs **really** are. `receive_ball(cell)` returns a
  `ShotOutcome`: `MISS`, `HIT`, or `FOUND` (the last square of a dog), plus
  `game_over` when all 22 dog squares are hit.
* `Knowledge`: the thrower's view: a 10×10 grid of `UNKNOWN / MISS / HIT / FOUND`,
  the list of shots, and which dogs are found. Helpers: `unknown_cells()`,
  `open_hits()` (BORKs whose dog isn't found yet), `hidden_dogs()`, `copy()`.

## 4. `ai/probability.py`: counting where dogs could be

One idea: **for every hidden dog, look at every spot it could still be lying in.**

* `possible_placements`: a dog can't lie on a miss or on a dog already found.
* `placement_weight`: normally each spot counts 1. While there is an open BORK, a
  spot that covers *k* BORKs counts `40^k`, because explaining a clue makes it far
  more believable.
* `placement_heatmap`: for each square, add up the weights of every spot covering
  it. Big number = hot square. (Empty lawn: corner A1 = 15 spots, centre E5 = 64.)
  Used by the Hint button and by the Dogfather's hiding.
* `placement_probabilities`: turns the counts into real percentages. For one dog,
  P = (weight covering the square) ÷ (all its weight). A square is empty only if
  *every* dog misses it, so `P(dog) = 1 − (1 − P1)(1 − P2)…(1 − P6)`.

## 5. The three AIs (`ai/agents.py`)

Every AI has the same method: `choose(knowledge, situation) → Decision`. A
`Decision` holds the chosen cell **and its reasoning** (thought text, heat map,
probabilities, top candidates), which is what the Brain View shows.

| Level | AI | Idea | Key code |
|---|---|---|---|
| 1 | **Pupper** | Random unknown square. The baseline. | `rng.choice(knowledge.unknown_cells())` |
| 2 | **Good Boy** | *Hunt* randomly; after a BORK, *target* its neighbours (+1 each, +3 more if it continues a line of BORKs). | `target_cells()` |
| 3 | **The Dogfather** | Counting + **expectimax** + race awareness + adversarial hiding (below). | `DogfatherAgent` |

### The Dogfather, step by step

1. **Count**: `placement_probabilities(knowledge)`, from section 4.
2. **Shortlist**: the 8 most likely squares get a deep look.
3. **Expectimax** (`expectimax_value`): for each shortlisted square, look at
   **both consequences**:
   ```
   MAX     (choose a square)
    └─ CHANCE: BORK with probability p  /  MISS with probability 1 − p
         └─ MAX (best next square in that imagined world)
   value = p + γ · ( p · next_if_hit + (1 − p) · next_if_miss )
   ```
   `best_next_chance` does the imagining. It **copies the board, writes the
   imagined result (BORK or miss) on the copy, recounts the probabilities, and
   takes the highest one.** The value is the expected number of BORKs over the
   next two throws. This is exactly the spec: *"evaluates all the possible
   consequences of each move and chooses the one that is closest to victory."*
4. **One fixed γ = 0.3** (`GAMMA`). γ = 0 would be plain greedy (only this throw
   counts). On the same 300 gardens γ 0…0.7 all need ~49 balls (a tie), γ 1 needs
   56. (There used to be a "panic mode" that dropped γ to 0 near the end; tests
   showed it changed nothing, so it was removed.)
5. **Adversarial hiding** (`hide_dogs`), the *min* side of expectiminimax: it tries
   250 random gardens and scores each with `layout_risk` (how hot its squares are
   on the starting heat map + 0.5 for every place two dogs touch). It keeps a
   random one of the 8 safest so it isn't predictable.

### Worked example (from `tools/deck_media.py`, reproducible)

Two open BORKs side by side at E3 and E4, γ = 0.3:

| Square | p | next if BORK | next if miss | value |
|---|---|---|---|---|
| **E2 (chosen)** | 94.6% | 99.8% | 99.7% | **1.245** |
| E5 (greedy pick) | 98.9% | 84.3% | 98.4% | 1.242 |

E5 is slightly more likely, but after E2 the next throw is almost certain (99.8%),
while after E5 it is only 84.3%. So expectimax prefers E2. It's a tie-breaker,
which is exactly what a small γ is for.

## 6. The experiment (`tournament.py`)

* **Part 1, efficiency:** every AI searches the **same 100 random gardens**.
  Average balls to find all 22 dog squares: **Pupper 96.3 → Good Boy 64.3 →
  Dogfather 49.6.** (Random theory: 22 × 101 / 23 = 96.6, which matches the measured 96.3.)
* **Part 2, head-to-head:** every pair plays 100 full games (300 total).
  Good Boy beats Pupper 100%. The Dogfather beats Pupper 100% and Good Boy 85%.
* **Tuning γ** (`tools/gamma_study.py`, the same 300 gardens for every γ):
  γ 0 → 48.8, 0.1 → 48.4, 0.2 → 48.4, **0.3 → 49.0**, 0.5 → 49.1, 0.7 → 49.0, 1.0 → 56.4.
  0 to 0.7 is a tie (gaps smaller than the luck between gardens); 1.0 is clearly
  worse. Head-to-head γ 0.3 vs γ 0 (greedy): 51%, a coin flip. So a little
  look-ahead is free and a lot hurts; the counting is what makes him strong.
* **Top-8 shortlist check** (`tools/shortlist_check.py`): scoring every square
  instead of the top 8 changed the pick in 1 of 2,890 turns.

## 7. Rewriting it yourself: suggested order

**Must understand (the AI part the marker will ask about):** about 650 lines of real code.

| # | File | Code lines | What to focus on |
|---|---|---|---|
| 1 | `config.py` | 33 | Just settings |
| 2 | `core/fleet.py` | 85 | Shapes, transforms, `PLACEMENT_TABLE` |
| 3 | `core/board.py` | 112 | `Garden.receive_ball`, `Knowledge.record` |
| 4 | `ai/probability.py` | 60 | Counting, the `1 − (1−P1)…` formula |
| 5 | `ai/agents.py` | 213 | The 3 AIs; Dogfather's `expectimax_value` |
| 6 | `tournament.py` | 149 | How the experiment is run |

**Know what it does (the game screens):** about 1,600 lines. You need to explain
these, not memorise them: the game loop in `app.py`, the battle state machine in
`scenes_game.py`, and how `board_view.py` draws the board.

**Don't need to rewrite (`tools/`):** drawing processing, sound synthesis,
screenshots, tests. They are helpers for making assets and checking the game.

## 8. The screens (`ui/`)

* **`app.py`**: the game loop: events → `scene.update(dt)` → `scene.draw()`, 60 FPS.
  Everything is drawn on a 1280×720 canvas that `pygame.SCALED` stretches to the window.
* **`scenes_game.py` / `BattleScene`**: a **state machine**:
  `coin → human_turn → human_throw → pause → ai_think → ai_scan → ai_throw → pause → …`
  * The AI thinks on a **background thread** so animations never freeze.
  * `ai_scan` moves the reticle through the top candidates so you can see it compare squares.
  * Brain View (`B`) paints the AI's probabilities over **your** garden.
  * Hint (`H`, 3 per game) shows the heat map over the **enemy** garden.
* **`board_view.py`**: lawn, labels, dogs (rotated exactly like their `Transform`),
  balls, BORK holes, heat map, reticle, flying-ball arc.
* **`widgets.py`**: buttons, speech bubble, particles, pop-up text.
* **`assets.py`**: loads images/sounds/fonts once; `portrait()` reuses the neutral
  face if a mood isn't drawn; draws a simple shape if a picture is missing.

## 9. Art and music

* **Art:** hand-drawn. See `DRAWING_PACK/DRAWING_CHECKLIST.md`. Drawings go in
  `drawings/`, then `tools/process_assets.py` removes the paper and fits them.
* **Music:** the Wiener Dog Song, `assets/sounds/music.mp3`, looped by
  `ASSETS.start_music()`. Sound effects are synthesised by `tools/make_sounds.py`.
