# Counter-Attacks

## Goal
Find counter-attacks: a recovery/due win leading to a shot quickly and with forward progress.

## Inputs
- `/workspace/events.json` with `id`,`period`,`timestamp` ("HH:MM:SS.mmm"), `possession`, `play_pattern.name`, `team.id/name`, `type.name`, `location`.

## Definitions (exact)
- Recovery types: `Ball Recovery`, `Duel`, `Interception`.
- For each recovery R and later Shot S:
  - Same `team.id`, same `period`, same `possession`, same `play_pattern.name`.
  - No intervening play_pattern change: every event with timestamp strictly between R and S (same period) must have the same `play_pattern.name` as S.
  - Timestamp diff: `0 < S_ts - R_ts <= 12.0` (12.0 inclusive). ALWAYS use `timestamp` diff, never `minute`.
  - Forward distance: normalize x by attack_sign (Team A p1 / Team B p2 => +1 else -1; `nx = x` if +1 else `120-x`); `distance_forward = shot_nx - recovery_nx >= 15`.
- Pair each recovery with the earliest qualifying shot (greedy, each shot used once).

## Output
- `/workspace/output.csv` header: `recovery_id,shot_id,team,seconds,distance_forward`
- `seconds` rounded 3 decimals, `distance_forward` rounded 2 decimals.
- Sort by `seconds`, then `recovery_id`.
