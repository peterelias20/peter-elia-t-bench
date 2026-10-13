# Lineup Consistency

## Goal: reconcile active-player intervals

Also read `/workspace/lineups.json`, with schema
`[{team_id, players: [{id,name,starter}]}]`. Add a REQUIRED `--lineups LINEUPS`
argument to your program. Names in this roster and match.json are authoritative.
The roster includes starters and registered bench players; player IDs may be
reused by the other team, so identity is `(team_id,player_id)`.

Process ALL canonical events in order using an active set and disjoint playing
intervals. Starters are active from 0. Substitution has outgoing `player.id`
and incoming `substitution.replacement.id`. It is valid only if both players
are registered on that team, outgoing is active, incoming is inactive and
has never been dismissed, and the IDs differ. Apply valid substitutions
atomically: close outgoing interval and open incoming. Reject an invalid sub
without changing state and flag BOTH participants `invalid_substitution`
(missing incoming ID: flag only outgoing). Multiple valid reentries are allowed.

Red Card closes an active player's interval and permanently dismisses them.
If inactive, flag `invalid_dismissal` without state change. A control event is
an appearance: flag `inactive_appearance` if its player is currently inactive
and `unregistered_player` if not in that team's roster. Control event outcomes
and geometry do not affect appearances. Substitution/Red Card/Pressure are
not appearances. Same-timestamp event indices determine whether an appearance
comes before/after a substitution. No inferred activation from appearances.
Flag each starter with no control appearances as `started_no_events`.

Playing time for an event is period.offset_ms + min(timestamp_ms,
period.duration_ms). This clips stoppage time separately in every period.
Periods are chronological, with contiguous regulation offsets and durations.
Close remaining intervals at sum(period.duration_ms). Sum all intervals per
player, then divide by 60000. Do not count the gap caused by stoppage time;
never give an unregistered/inactive player default 90 minutes.

Emit one row per flagged player, combining flags in lexicographic order with
semicolons. For unregistered players use the first name encountered in canonical
order (including a replacement's name). Emit ALL applicable flags.

Header: `team_id,player_id,team,player,mismatch_types,minutes_played`

Sort numerically by team_id, then player_id. Zero playing time is allowed.

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
