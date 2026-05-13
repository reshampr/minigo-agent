#!/usr/bin/env python3
"""
Local self-play harness: your minimax Go_agent (from my_player.py) vs a simple opponent.

Run from the MiniGo directory:
  python3 play_match.py --fast
  python3 play_match.py --opponent greedy --games 3 --seed 42
  python3 play_match.py --target-depth 4 --branching-factor 20   # same as my_player __main__
"""

from __future__ import annotations

import argparse
import copy
import os
import random

import numpy as np

import my_player
from my_player import (
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


def _stone_counts(board: np.ndarray) -> tuple[int, int]:
    b = int(np.sum(board == black))
    w = int(np.sum(board == white))
    return b, w


def _final_score(board: np.ndarray) -> tuple[float, float]:
    """Simple score: stones on board; white gets komi (same constant as my_player)."""
    b, w = _stone_counts(board)
    return float(b), float(w) + float(KOMI)


def print_board(board: np.ndarray, caption: str = "") -> None:
    sym = {0: ".", 1: "X", 2: "O"}
    if caption:
        print(caption)
    for row in board:
        print(" ".join(sym[int(x)] for x in row))
    print()


def apply_legal_move(agent: Go_agent, board: np.ndarray, turn: int, move: tuple[int, int]) -> np.ndarray:
    new_board, _ = agent.make_move(copy.deepcopy(board), turn, move)
    if np.array_equal(new_board, board) and move != (-1, -1):
        # Should not happen if caller only uses legal moves
        return board.copy()
    return new_board


def random_move(agent: Go_agent, board: np.ndarray, turn: int) -> tuple[int, int]:
    choices = agent.legal_moves(board, turn)
    return random.choice(choices)


def greedy_move(agent: Go_agent, board: np.ndarray, turn: int) -> tuple[int, int]:
    """One-ply: maximize static eval for `turn` after the move."""
    moves = agent.legal_moves(board, turn)
    best: tuple[int, int] = (-1, -1)
    best_val = float("-inf")
    for m in moves:
        nb, _ = agent.make_move(copy.deepcopy(board), turn, m)
        if np.array_equal(nb, board):
            continue
        v = agent.evaluation_func(nb, turn, m)
        if v > best_val:
            best_val = v
            best = m
    return best


def minimax_move(
    agent: Go_agent,
    board: np.ndarray,
    turn: int,
    step_number: int,
    *,
    target_depth: int,
    branching_factor: int,
) -> tuple[int, int]:
    my_player.hashMap.clear()
    move, _ = agent.minimax(
        board,
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


def play_one_game(
    *,
    my_agent_is_black: bool,
    opponent: str,
    target_depth: int,
    branching_factor: int,
    max_half_moves: int,
    verbose: bool,
) -> tuple[str, np.ndarray]:
    """
    Returns (winner_label, final_board).
    winner_label is 'black', 'white', or 'draw' using stone+komi scoring after double pass or limit.
    """
    _reset_step_file()
    prev = np.zeros((grid_size, grid_size), dtype=int)
    curr = np.zeros((grid_size, grid_size), dtype=int)
    consecutive_passes = 0

    for half_move in range(max_half_moves):
        turn = black if (half_move % 2 == 0) else white
        my_turn = (turn == black) == my_agent_is_black

        step_number = my_player.step_calculator(prev, curr)
        agent = Go_agent(turn, prev, curr)

        if my_turn:
            move = minimax_move(
                agent,
                curr,
                turn,
                step_number,
                target_depth=target_depth,
                branching_factor=branching_factor,
            )
            who = "You (minimax)"
        else:
            if opponent == "greedy":
                move = greedy_move(agent, curr, turn)
            else:
                move = random_move(agent, curr, turn)
            who = f"Opponent ({opponent})"

        if move == (-1, -1):
            consecutive_passes += 1
        else:
            consecutive_passes = 0

        if verbose:
            print(f"--- Half-move {half_move + 1} | {who} | turn={'B' if turn == black else 'W'} ---")
            print_board(curr, "Position (before move):")

        curr_after = apply_legal_move(agent, curr, turn, move)
        if verbose:
            mv = "PASS" if move == (-1, -1) else f"{move[0]},{move[1]}"
            print_board(curr_after, f"After move: {mv}")

        prev = curr.copy()
        curr = curr_after

        if consecutive_passes >= 2:
            break

    sb, sw = _final_score(curr)
    if sb > sw:
        winner = "black"
    elif sw > sb:
        winner = "white"
    else:
        winner = "draw"

    if verbose:
        b_st, w_st = _stone_counts(curr)
        print(
            f"Game end. Stones B={b_st} W={w_st} (komi W+{KOMI}). "
            f"Totals B={sb:.1f} W={sw:.1f} -> {winner}"
        )
        print_board(curr, "Final:")
    return winner, curr


def main() -> None:
    p = argparse.ArgumentParser(description="Play your my_player Go_agent against a baseline.")
    p.add_argument("--opponent", choices=("random", "greedy"), default="random")
    p.add_argument("--games", type=int, default=1, help="Number of games to play")
    p.add_argument("--seed", type=int, default=None, help="RNG seed (random opponent only)")
    p.add_argument("--quiet", action="store_true", help="Only print per-game results")
    p.add_argument("--target-depth", type=int, default=4)
    p.add_argument("--branching-factor", type=int, default=20)
    p.add_argument(
        "--fast",
        action="store_true",
        help="Shallow search (depth 2, branching 12) for quicker interactive games.",
    )
    p.add_argument("--max-half-moves", type=int, default=200)
    p.add_argument(
        "--i-play-white",
        action="store_true",
        help="Let the baseline take Black; your minimax agent plays White (still uses same search).",
    )
    args = p.parse_args()

    if args.fast:
        args.target_depth = 2
        args.branching_factor = 12

    if args.seed is not None:
        random.seed(args.seed)

    my_black = not args.i_play_white
    wins = {"black": 0, "white": 0, "draw": 0}

    for g in range(args.games):
        verbose = not args.quiet
        if args.games > 1 and verbose:
            print(f"\n======== Game {g + 1}/{args.games} ========")
        winner, _ = play_one_game(
            my_agent_is_black=my_black,
            opponent=args.opponent,
            target_depth=args.target_depth,
            branching_factor=args.branching_factor,
            max_half_moves=args.max_half_moves,
            verbose=verbose,
        )
        wins[winner] += 1
        if args.quiet or args.games > 1:
            me = "black" if my_black else "white"
            opp = "white" if my_black else "black"
            if winner == "draw":
                tag = "draw"
            elif (winner == "black" and my_black) or (winner == "white" and not my_black):
                tag = "you_win"
            else:
                tag = "opponent_win"
            print(f"game={g + 1} winner={winner} you_were={me} opponent_was={opp} ({tag})")

    if args.games > 1:
        print(
            f"\nSummary over {args.games} games: "
            f"black={wins['black']} white={wins['white']} draw={wins['draw']}"
        )


if __name__ == "__main__":
    main()
