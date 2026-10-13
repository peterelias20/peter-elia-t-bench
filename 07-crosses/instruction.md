# Crosses

## Goal
Find crosses: passes with a cross trait that end in the box.

## Inputs
- `/workspace/events.json` with `type.name`, `pass` (optional dict), `location`, `end_location`, `period`, `team.name`.

## Definitions (use exactly ONE rule to stay deterministic)
- Only `type.name == "Pass"` with `end_location` present AND `pass` dict contains key `"cross"` with non-null value (`pass.cross != null`). Ignore `pass.height` and subtypes.
- Normalize for attack direction FIRST: `attack_sign` as in task 01 (+1 if (Team A,p1) or (Team B,p2) else -1); `norm_end_x = end_x` if sign==+1 else `120 - end_x`. y unchanged.
- Keep if `norm_end_x >= 102` AND `18 <= end_y <= 62` (inclusive).

## Output
- `/workspace/output.csv` header: `id,minute,player,end_x,end_y` (raw end coords).
- Sort by `minute`, then `id`.
