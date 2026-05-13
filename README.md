# MiniGo

5×5 Mini-Go player (`my_player.py`) plus small tools to run games locally.

## Requirements

- Python 3
- NumPy (`pip install numpy`)

## Project layout

| Path | Purpose |
|------|--------|
| `my_player.py` | Your `Go_agent` and minimax player |
| `game_io/input.txt` | Default input board for one-shot mode |
| `game_io/output.txt` | Move written by `my_player.py` |
| `game_io/step.txt` | Step counter (used by search / harnesses) |
| `play_interactive.py` | **You vs the agent** on a terminal grid |
| `play_match.py` | **Agent vs baseline** (random or greedy) |

## 1. One move (file in / file out)

Use this when you want a single reply from your player, same idea as many course autograders.

1. Edit `game_io/input.txt`: line 1 is `1` (Black) or `2` (White); lines 2–6 are the **previous** 5×5 board; lines 7–11 are the **current** board. Each row is five digits (`0` empty, `1` Black, `2` White), e.g. `00000`.

2. From the **MiniGo** directory run:

```bash
cd /path/to/MiniGo
python3 my_player.py
```

3. Read the answer in `game_io/output.txt`: either `row,col` or `PASS`.

The `game_io` folder is created if missing.

## 2. Interactive grid (recommended)

You and the agent take turns on a labeled 5×5 grid in the terminal.

```bash
cd /path/to/MiniGo
python3 play_interactive.py
```

- You are **Black (X)** by default and move first.
- Enter moves as two numbers `row col` (each **0–4**), e.g. `2 3`, or `2,3`.
- Type `pass` or `p` to pass; `q` to quit.
- Default search is **fast** (shallow depth). For the same depth as `my_player.py` (slower per move):

```bash
python3 play_interactive.py --full
```

To play **White** (agent plays Black and moves first):

```bash
python3 play_interactive.py --you-white
```

## 3. Agent vs baseline (no human)

Runs full games: your minimax vs random or greedy moves.

```bash
cd /path/to/MiniGo
python3 play_match.py --fast
```

- `--fast` — quicker games (shallow search).
- Omit `--fast` for stronger but slower play (depth 4, branching 20).
- `--opponent greedy` — stronger baseline than `random` (default).
- `--quiet --games 5` — short summaries for several games.
- `--i-play-white` — your agent is White.

## Tips

- Run all commands from the **MiniGo** directory so imports and `game_io/` paths resolve correctly.
- If an autograder writes `input.txt` somewhere else, point your run at that path (e.g. a small wrapper that calls `read_file(...)` with the grader path) or copy the file into `game_io/input.txt`.
