# Switch of Play

## Goal
Find switches of play: long passes that flip the wing.

## Inputs
- `/workspace/events.json` with `type.name`, `location`, `end_location`, optional `pass.length`.

## Definitions (follow exactly — do NOT trust redundant fields)
- Only `type.name == "Pass"` with `end_location` present. Skip if missing.
- Recompute length: `length = hypot(end_x - x, end_y - y)` from coordinates. IGNORE `pass.length` entirely (it may conflict; coordinates are truth).
- Wing zones by raw y: left `y < 30`, middle `30 <= y <= 50`, right `y > 50`.
- Keep if `length > 35` (strictly) AND wing flips left<->right: `(y<30 and end_y>50)` OR `(y>50 and end_y<30)`. Middle involved => reject.

## Output
- `/workspace/output.csv` header: `id,minute,player,length,end_x,end_y`
- `length` recomputed, rounded to 2 decimals. `end_x,end_y` raw.
- Sort by `minute`, then `id`.
