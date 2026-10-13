# Press-then-Win

## Goal
Find Pressure -> win sequences: a `Pressure` by a team followed within 5s by a `Duel`/`Interception`/`Ball Recovery` by the SAME team.

## Inputs
- `/workspace/events.json` with `id`,`period`,`timestamp` ("HH:MM:SS.mmm"), `team.id`, `type.name`.

## Rules (exact)
- Parse `timestamp` as seconds: `HH*3600 + MM*60 + SS.mmm`.
- Candidate win types: `Duel`, `Interception`, `Ball Recovery` (exact match).
- Conditions: same `period`, same `team.id`, `0 < win_ts - pressure_ts <= 5.0` (5.0 inclusive, 5.001 excluded).
- For each Pressure (in time order), pair with the EARLIEST qualifying win after it. Each win used at most once (greedy).
- `related_events` may exist but time window is primary; ignore it.
- Do NOT use `minute`/`second` for diffs (they drift); always use `timestamp` diff.

## Output
- `/workspace/output.csv` header: `pressure_id,win_id,team,seconds_between`
- `team` is team.name. `seconds_between` rounded to 3 decimals.
- Sort by `pressure_id`.
