# Forward Passes

## Goal
Find all forward passes: passes whose `end_location` is closer to the opponent goal than `location`.

## Inputs
- `/workspace/events.json`: list of StatsBomb-style events. Each has `id`, `period` (1|2), `minute`, `second`, `timestamp` ("HH:MM:SS.mmm"), `team` (`id`,`name`), `player` (`name`), `type` (`name`), `location` ([x,y] on 120x80), optional `end_location` ([x,y]).

## Attack direction (DO NOT hardcode team -> direction)
- Period 1: Team A attacks +x, Team B attacks -x.
- Period 2: sides flip — Team A attacks -x, Team B attacks +x.
- Derive `attack_sign`: +1 if (team is "Team A" and period==1) or (team is "Team B" and period==2), else -1.
- Alternatively infer from first-half average x progression, but result must equal the rule above.

## Definition of forward
- Only consider events with `type.name == "Pass"` AND `end_location` present. If `end_location` is missing: SKIP the event (do not crash).
- `forward = (end_x - x) * attack_sign > 0`. Strictly greater than 0; `== 0` is NOT forward.

## Output
- Write `/workspace/output.csv` with exact header: `id,minute,player,end_x,end_y`
- `player` is `player.name`. `end_x,end_y` are raw `end_location` values (do NOT normalize).
- One row per forward pass. Sort by `minute` ascending, then `id` ascending.
- Use stdlib or pandas; no network.

## Hints
- Missing `end_location` must be skipped, not crash.
- The half-time flip matters: same coordinates can be forward in period 1 and backward in period 2.
