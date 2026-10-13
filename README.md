# peter-elia-t-bench

10 deterministic StatsBomb-style T-Bench tasks (StatsBomb open-data inspired, fully synthetic fixtures).

| Task | Difficulty | Skill |
|---|---|---|
| 01-forward-passes | easy | forward filter + half-time flip |
| 02-progressive-carries | medium | 10m + final third, missing-field skip |
| 03-switch-of-play | medium | recomputed length, wing flip, anti-cheat decoys |
| 04-possession-chains | medium | (possession, play_pattern) groupby |
| 05-press-then-win | hard | 5s temporal join |
| 06-shot-ending-sequences | medium | N=5 backward walk + breaks |
| 07-crosses | easy | nested cross + box |
| 08-set-piece-splitter | easy | precedence-table tagging |
| 09-counter-attacks | hard | <12s + 15m + same chain |
| 10-lineup-consistency | medium | two-file join + sub minutes |

Each task: `task.toml`, `instruction.md`, `environment/Dockerfile` (+`events.json`/`lineups.json`), `solution/solve.sh`+`solve.py`, `tests/test.sh`+`test_outputs.py`, `README.md`.
Inputs at `/workspace/events.json` (`/workspace/lineups.json` for task 10), output `/workspace/output.csv`.
