# Possession Chains

## Goal
Rebuild possession chains grouped by `(possession, play_pattern)`.

## Inputs
- `/workspace/events.json` with `possession` (int), `play_pattern.name`, `period`, `minute`, `second`, `timestamp`, `team.name`.

## Rules
- Sort events by `(period, minute*60+second)` (then `id` for ties).
- Split chain when `play_pattern.name` changes even if `possession` id is reused. Key is `(possession, play_pattern.name)`.
- For each chain: `possession_id` (possession int), `team` (team.name of first event in chain in sorted order), `event_count`, `start_minute`, `end_minute` (min/max minute in chain).
- Extra time is already encoded in `minute` (e.g. 92); use it directly.

## Output
- `/workspace/output.csv` header: `possession_id,team,event_count,start_minute,end_minute`
- Sort by `possession_id`, then `play_pattern` order of first appearance? To keep deterministic: sort by `start_minute`, then `possession_id`. State: sort by start_minute, then possession_id.
