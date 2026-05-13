#!/usr/bin/env python3
"""
Human vs your minimax agent on a 5x5 grid in the terminal.

  cd .../MiniGo
  python3 play_interactive.py              # quick agent (depth 2)
  python3 play_interactive.py --full       # same strength as my_player.py main
  python3 play_interactive.py --you-white

Enter moves as:  row col   (0-4, e.g. 2 3)   or   pass   or   p
Type q to quit.
"""

from __future__ import annotations

import argparse
import copy
import os
import re

import numpy as np

import my_player
from my_player import (
    GAME_IO_DIR,
    STEP_FILE,
    Go_agent,
    black,
    grid_size,
    KOMI,
    white,
)


def _reset_step_file() -> None:
    if os.path.exists(STEP_FILE):
        os.remove(STEP_FILE)


def print_grid(curr: np.ndarray, to_move: int, human_is: int) -> None:
    sym = {0: ".", 1: "X", 2: "O"}
    tname = "Black (X)" if to_move == black else "White (O)"
    human_side = "Black (X)" if human_is == black else "White (O)"
    print()
    print(f"To move: {tname}   |   You are: {human_side}")
    print("    " + "  ".join(str(c) for c in range(grid_size)))
    for r in range(grid_size):
        print(f"  {r} " + "  ".join(sym[int(curr[r, c])] for c in range(grid_size)))
    print("  X = Black  |  O = White  |  . = empty")
    print()


def parse_move(line: str) -> tuple[int, int] | str | None:
    """Return (r,c), 'quit', or 'bad' for invalid format."""
    s = line.strip().lower()
    if not s:
        return "bad"
    if s in ("q", "quit", "exit"):
        return "quit"
    if s in ("p", "pass"):
        return (-1, -1)
    m = re.match(r"^\s*(\d)\s+(\d)\s*$", s)
    if not m:
        m = re.match(r"^\s*(\d)\s*,\s*(\d)\s*$", s)
    if m:
        r, c = int(m.group(1)), int(m.group(2))
        if 0 <= r < grid_size and 0 <= c < grid_size:
            return (r, c)
    return "bad"


def agent_choose(
    prev: np.ndarray,
    curr: np.ndarray,
    turn: int,
    *,
    target_depth: int,
    branching_factor: int,
) -> tuple[int, int]:
    step_number = my_player.step_calculator(prev.copy(), curr.copy())
    agent = Go_agent(turn, prev, curr)
    my_player.hashMap.clear()
    move, _ = agent.minimax(
        curr,
        turn,
        step_number,
        0,
        target_depth,
        branching_factor,
        True,
        None,
        False,
        float("-inf"),
        float("inf"),
    )
    return move if move is not None else (-1, -1)


def play(
    *,
    human_is_black: bool,
    target_depth: int,
    branching_factor: int,
) -> None:
    os.makedirs(GAME_IO_DIR, exist_ok=True)
    _reset_step_file()

    prev = np.zeros((grid_size, grid_size), dtype=int)
    curr = np.zeros((grid_size, grid_size), dtype=int)
    human = black if human_is_black else white
    consecutive_passes = 0
    to_move = black  # Black first (standard Go)

    print("Mini-Go 5x5 — you and the agent alternate. Black plays first.")
    if target_depth <= 2:
        print("(Quick search mode. Use --full for depth 4 like my_player.py.)")
    print("Moves: `row col` with 0-4, e.g. `2 3` or `2,3`. `pass` / `p` to pass. `q` to quit.")

    while True:
        print_grid(curr, to_move, human)

        if to_move == human:
            raw = input("Your move: ")
            parsed = parse_move(raw)
            if parsed == "quit":
                print("Bye.")
                return
            if parsed == "bad":
                print("Invalid input. Use e.g. `2 3`, `2,3`, `pass`, or `q`.")
                continue
            move = parsed
            agent = Go_agent(to_move, prev, curr)
            legal = set(agent.legal_moves(curr, to_move))
            if move not in legal:
                print("Illegal move (suicide, ko, or occupied). Try again.")
                print(f"Legal moves include: {sorted(m for m in legal if m != (-1, -1))[:12]}… pass allowed.")
                continue
        else:
            print("Agent is thinking…")
            move = agent_choose(prev, curr, to_move, target_depth=target_depth, branching_factor=branching_factor)
            if move == (-1, -1):
                print("Agent plays: PASS")
            else:
                print(f"Agent plays: {move[0]} {move[1]}")

        agent = Go_agent(to_move, prev, curr)
        new_curr = apply_move(agent, curr, to_move, move)
        if move == (-1, -1):
            consecutive_passes += 1
        else:
            consecutive_passes = 0

        prev = curr.copy()
        curr = new_curr
        to_move = white if to_move == black else black

        if consecutive_passes >= 2:
            print("\nGame over (two passes).")
            b = int(np.sum(curr == black))
            w = int(np.sum(curr == white))
            sb, sw = float(b), float(w) + float(KOMI)
            print(f"Stones — Black: {b}, White: {w} (White +komi {KOMI})")
            print(f"Totals — Black: {sb:.1f}, White: {sw:.1f}")
            if sb > sw:
                print("Result: Black ahead on this simple count.")
            elif sw > sb:
                print("Result: White ahead on this simple count.")
            else:
                print("Result: roughly even.")
            return


def apply_move(agent: Go_agent, board: np.ndarray, turn: int, move: tuple[int, int]) -> np.ndarray:
    nb, _ = agent.make_move(copy.deepcopy(board), turn, move)
    return nb


def main() -> None:
    p = argparse.ArgumentParser(description="Play your agent on a terminal grid (human vs AI).")
    p.add_argument("--you-white", action="store_true", help="You play White; agent plays Black.")
    p.add_argument(
        "--full",
        action="store_true",
        help="Use full search (depth 4, branching 20) like my_player.py — slower per move.",
    )
    p.add_argument("--target-depth", type=int, default=None, help="Override search depth.")
    p.add_argument("--branching-factor", type=int, default=None, help="Override branching factor.")
    args = p.parse_args()

    target_depth = 4 if args.full else 2
    branching_factor = 20 if args.full else 12
    if args.target_depth is not None:
        target_depth = args.target_depth
    if args.branching_factor is not None:
        branching_factor = args.branching_factor

    play(
        human_is_black=not args.you_white,
        target_depth=target_depth,
        branching_factor=branching_factor,
    )


if __name__ == "__main__":
    main()
