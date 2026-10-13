# Progressive Carries

## Goal
Find all progressive carries: a `Carry` that moves >=10m toward goal AND ends in the final third.

## Inputs
- `/workspace/events.json`: StatsBomb-style events (`id`,`period`,`minute`,`team.name`,`player.name`,`type.name`,`location`,`end_location`).

## Attack normalization (same as forward passes)
- Period 1: Team A attacks +x, Team B attacks -x. Period 2 flips.
- `attack_sign = +1` if (Team A and period==1) or (Team B and period==2), else `-1`.
- Normalized x: `nx = x` if sign==+1 else `120 - x`. Apply to both start and end.
- `distance_forward = norm_end_x - norm_start_x`. `final_third = norm_end_x >= 80`.

## Definition
- Only `type.name == "Carry"` with `end_location` present. If `end_location` missing: SKIP (do not crash, do not infer from next event).
- Keep if `distance_forward >= 10` AND `norm_end_x >= 80`.

## Output
- `/workspace/output.csv` header exactly: `id,minute,player,start_x,start_y,end_x,end_y,distance_forward`
- `start_x,start_y` raw location; `end_x,end_y` raw end_location; `distance_forward` normalized forward distance rounded to 2 decimals.
- Sort by `minute`, then `id`.
