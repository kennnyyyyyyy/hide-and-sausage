# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  tournament.py - the EXPERIMENT. This is the "Experimentally evaluate and
#  compare various AI methods" part of the brief (project spec, section 1).
#
#  Part 1 - EFFICIENCY: every AI searches the SAME bunch of random gardens,
#           and we count how many balls it takes to find all 22 dog squares.
#  Part 2 - HEAD-TO-HEAD: every AI plays every other AI in full games (they
#           take turns throwing, and a coin flip decides who goes first).
#  The results get printed and saved into results/ as CSV files, plus PNG
#  charts if matplotlib is installed, so I can use them in the report and
#  slides.
#
#  Usage:  python tournament.py [games_per_test]
# =============================================================================

import csv
import os
import random
import statistics
import sys
import time

from hide_and_sausage.core.board import Garden, Knowledge
from hide_and_sausage.ai.agents import AGENT_CLASSES, Situation

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# -----------------------------------------------------------------------------
# solo_search - lets one AI search a garden on its own and counts how many
# balls it needs to find every dog.
#   agent  : the AI we're testing
#   garden : the garden to search (we copy it first, so the same garden
#            can be used again for the next AI)
# Gives back the number of balls thrown.
# -----------------------------------------------------------------------------
def solo_search(agent, garden):
    target = Garden()
    for placement in garden.placements.values():
        target.place(placement)
    knowledge = Knowledge()
    situation = Situation()
    while True:
        decision = agent.choose(knowledge, situation)
        outcome = target.receive_ball(decision.cell)
        knowledge.record(outcome)
        situation.my_shots += 1
        if outcome.result != 1:
            situation.my_hits += 1
        if outcome.game_over:
            return len(knowledge.shots)


# -----------------------------------------------------------------------------
# head_to_head - plays one full game between two AIs. Each one hides its
# dogs, then they take turns throwing until someone finds all 22 squares.
#   agent_a, agent_b : the two AIs playing
#   rng              : the random number maker for the coin flip
# Gives back 0 if agent_a wins, 1 if agent_b wins.
# -----------------------------------------------------------------------------
def head_to_head(agent_a, agent_b, rng):
    players = [agent_a, agent_b]
    gardens = [agent_a.hide_dogs(), agent_b.hide_dogs()]
    knowledge = [Knowledge(), Knowledge()]      # knowledge[i] = what i knows
    hits = [0, 0]
    turn = rng.randint(0, 1)                    # coin flip: who throws first
    while True:
        me, them = turn, 1 - turn
        situation = Situation(hits[me], hits[them],
                              len(knowledge[me].shots), len(knowledge[them].shots))
        decision = players[me].choose(knowledge[me], situation)
        outcome = gardens[them].receive_ball(decision.cell)
        knowledge[me].record(outcome)
        if outcome.result != 1:
            hits[me] += 1
        if outcome.game_over:
            return me
        turn = them


# -----------------------------------------------------------------------------
# run_efficiency - Part 1 of the experiment. We make the same random gardens
# for everyone, let each AI search all of them, and print how it did.
#   games : how many gardens each AI gets to search
# Gives back, for each AI's name, the list of how many balls it needed.
# -----------------------------------------------------------------------------
def run_efficiency(games):
    layout_rng = random.Random(2026)
    gardens = []
    for _ in range(games):
        garden = Garden()
        garden.scatter_randomly(layout_rng)
        gardens.append(garden)

    results = {}
    for agent_class in AGENT_CLASSES:
        agent = agent_class(seed=7)
        started = time.perf_counter()
        counts = [solo_search(agent, garden) for garden in gardens]
        elapsed = time.perf_counter() - started
        results[agent.name] = counts
        print(f"  {agent.name:<16} mean {statistics.mean(counts):6.1f} balls   "
              f"best {min(counts):3d}   worst {max(counts):3d}   "
              f"({elapsed / games * 1000:7.1f} ms per game)")
    return results


# -----------------------------------------------------------------------------
# run_head_to_head - Part 2 of the experiment, a round robin where every AI
# plays every other AI.
#   games : how many games each pair plays
# Gives back, for each (name_a, name_b) pair, how often a beat b (0 to 1).
# -----------------------------------------------------------------------------
def run_head_to_head(games):
    rng = random.Random(99)
    table = {}
    for i, class_a in enumerate(AGENT_CLASSES):
        for class_b in AGENT_CLASSES[i + 1:]:
            agent_a, agent_b = class_a(seed=1), class_b(seed=2)
            wins_a = sum(1 for _ in range(games)
                         if head_to_head(agent_a, agent_b, rng) == 0)
            rate = wins_a / games
            table[(agent_a.name, agent_b.name)] = rate
            table[(agent_b.name, agent_a.name)] = 1 - rate
            print(f"  {agent_a.name:<16} vs {agent_b.name:<16} "
                  f"{rate:5.0%} - {1 - rate:5.0%}")
    return table


# -----------------------------------------------------------------------------
# save_results - saves the results as CSV files, then draws the charts too
# (if matplotlib is there).
#   efficiency : the ball counts we got from run_efficiency
#   matchups   : the win rates we got from run_head_to_head
# -----------------------------------------------------------------------------
def save_results(efficiency, matchups):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    names = list(efficiency)

    with open(os.path.join(RESULTS_DIR, "efficiency.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent", "mean_balls", "median", "best", "worst", "stdev"])
        for name, counts in efficiency.items():
            writer.writerow([name, round(statistics.mean(counts), 2),
                             statistics.median(counts), min(counts), max(counts),
                             round(statistics.pstdev(counts), 2)])

    with open(os.path.join(RESULTS_DIR, "head_to_head.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent"] + names)
        for a in names:
            writer.writerow([a] + ["" if a == b else round(matchups[(a, b)], 3)
                                   for b in names])

    make_charts()


# -----------------------------------------------------------------------------
# make_charts - draws the charts for the report from the saved CSV files.
# That way we can redraw them without running the whole slow experiment
# again. If matplotlib isn't installed, it just skips the charts.
#   (no parameters)
# -----------------------------------------------------------------------------
def make_charts():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib not installed - CSV saved, charts skipped)")
        return

    with open(os.path.join(RESULTS_DIR, "efficiency.csv"), newline="") as f:
        rows = list(csv.reader(f))[1:]
    names = [row[0] for row in rows]
    means = [float(row[1]) for row in rows]
    spreads = [float(row[5]) for row in rows]

    figure, axis = plt.subplots(figsize=(8, 4.5))
    colours = ["#aadc78", "#8cc8f0", "#eb5746"]       # Pupper, Good Boy, Dogfather
    bars = axis.bar(names, means, yerr=spreads, capsize=6, color=colours,
                    edgecolor="#3b2418", linewidth=2)
    for bar, mean in zip(bars, means):
        axis.text(bar.get_x() + bar.get_width() / 2, mean + 2, f"{mean:.1f}",
                  ha="center", va="bottom", fontweight="bold")
    axis.set_ylabel("Balls to find all 22 dog squares\n(lower = better, bars = 1 std dev)")
    axis.set_title("Search efficiency on the same 100 random gardens")
    axis.set_ylim(0, 115)
    figure.tight_layout()
    figure.savefig(os.path.join(RESULTS_DIR, "efficiency.png"), dpi=160)

    with open(os.path.join(RESULTS_DIR, "head_to_head.csv"), newline="") as f:
        table = list(csv.reader(f))
    names = table[0][1:]
    matchups = {}
    for row in table[1:]:
        for name, value in zip(names, row[1:]):
            if value:
                matchups[(row[0], name)] = float(value)

    figure, axis = plt.subplots(figsize=(6.5, 5.5))
    grid = [[matchups.get((a, b), 0.5) for b in names] for a in names]
    image = axis.imshow(grid, cmap="RdYlGn", vmin=0, vmax=1)
    axis.set_xticks(range(len(names)), names, rotation=30, ha="right")
    axis.set_yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(names)):
            if i != j:
                axis.text(j, i, f"{grid[i][j]:.0%}", ha="center", va="center")
    axis.set_title("Head-to-head win rate (row vs column)")
    figure.colorbar(image)
    figure.tight_layout()
    figure.savefig(os.path.join(RESULTS_DIR, "head_to_head.png"), dpi=160)
    print(f"  charts saved to {RESULTS_DIR}")


# -----------------------------------------------------------------------------
# main - runs both parts of the experiment and saves everything.
#   games : how many games per test (more games = more accurate, but slower)
# -----------------------------------------------------------------------------
def main(games):
    print(f"\nPART 1 - search efficiency over {games} identical random gardens")
    efficiency = run_efficiency(games)
    print(f"\nPART 2 - head-to-head round robin, {games} games per pairing")
    matchups = run_head_to_head(games)
    save_results(efficiency, matchups)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--charts":
        make_charts()                 # redraw charts from saved CSVs only
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
