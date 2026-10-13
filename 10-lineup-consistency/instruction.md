# Lineup Consistency Check

## Goal
Compare `lineups.json` starters vs players appearing in `events.json`, resolving substitutions.

## Inputs
- `/workspace/lineups.json`: list of `{"team_id","team_name","lineup":[{"player_name","jersey_number"}]}`.
- `/workspace/events.json`: events with `team.name`, `player.name`, `minute`, `type.name=="Substitution"` events shaped as `{"player":{"name": OFF},"substitution":{"replacement":{"name": ON}},"minute"}`.

## Rules
- Appearances: distinct `player.name` per team from NON-substitution events (ignore the `player` field of Substitution events for appearances; ON player appears via later events).
- Subs: from Substitution events: OFF at `minute`, ON at `minute`.
- `minutes_played = (sub_off_minute or 90) - (sub_on_minute or 0)`, capped to [0,90]. Starters default on=0; non-starters default on=sub_on (if none, 0 but flagged).
- Emit a row ONLY for mismatches:
  - `started_no_events`: starter never appears (in non-sub events).
  - `played_not_started`: non-starter appears but has NO sub-on event.
  - `sub_minute_mismatch`: player's first appearance minute < sub_on minute (came on later per subs but seen earlier), OR starter with sub_off who still appears after off minute.
- Extra time: cap at 90 (ignore 90+ for minutes).

## Output
- `/workspace/output.csv` header: `team,player,mismatch_type,minutes_played`
- Sort by `team`, then `player`.
