# Shot-Ending Sequences

## Goal
For each `Shot`, walk back up to N=5 previous events in the same possession to find the attack origin.

## Inputs
- `/workspace/events.json` with `possession`, `play_pattern.name`, `period`,`minute`,`second`, `type.name`, `location`.

## Rules (exact, N=5)
- Sort all events by `(period, minute*60+second, id)`.
- For each Shot at index i, walk backwards collecting previous events while `len(chain) < 6` (shot + up to 5 prior):
  - STOP before an event if: different `possession`, different `play_pattern.name`, OR `type.name` in `[Half Start, Half End, Foul Committed, Foul Won, Offside]` (treat any name containing `Foul` or `Offside` or `Half` as break), OR `play_pattern.name != "Open Play"`.
  - If the Shot itself has `play_pattern.name != "Open Play"`, chain is just `[shot]` (length 1).
- `chain_length` = len(chain) including shot. `origin_x,origin_y` = `location` of FIRST (earliest) event in chain.

## Output
- `/workspace/output.csv` header: `shot_id,chain_length,origin_x,origin_y`
- Sort by `shot_id`.
