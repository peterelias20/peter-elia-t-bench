# Lineup Consistency

## Files and submission

Read `/workspace/events.json` and `/workspace/match.json`. These are synthetic,
StatsBomb-style feeds. Submit a **stdlib-only Python program** at
`/workspace/analyze.py` supporting:

```sh
python3 /workspace/analyze.py --events EVENTS --match MATCH --lineups LINEUPS --output OUTPUT
```

Paths are arbitrary absolute paths. Write the sample result to
`/workspace/output.csv`. The verifier also executes your program on other feeds
with the same schema, including different IDs, team names, directions and order.
Use no network or external packages. Do not read `/solution` or `/tests`.

## Feed reconciliation (applies before every other rule)

The JSON root is a list of records, potentially out of order. First group by
string `id`. Select the largest nonnegative integer `revision` (missing = 0);
for equal revisions select the record **later in the original JSON array**.
Ignore records without a string ID or with an invalid revision. If the selected
record has `deleted: true`, remove that ID. Never fall back to an older revision
when the selected record is deleted or malformed.

A surviving record needs integer `period`, `index`, `possession`, and `team.id`,
a nonempty `type.name` and `play_pattern.name`, and a valid `timestamp` formatted
`HH:MM:SS.mmm` (two digits each for hours/minutes/seconds, three milliseconds;
minutes and seconds 0–59). Ignore malformed records and unknown team/period IDs.
Booleans are not integers. Sort by `(period, timestamp_in_integer_milliseconds,
index, id)`. The timestamp is **period-relative**, including stoppage time;
`minute`, `second`, `team.name`, `pass.length`, `related_events` are decoys.
Integer millisecond arithmetic decides temporal eligibility; compare unrounded
geometry to thresholds. Round only for serialization.

`match.json` supplies `teams: [{id, name, attack_sign: {"1": 1, ...}}]` and
`periods: [{id, offset_ms, duration_ms}]`. Team identity is always `team.id`;
player identity is `player.id` (names can collide). All valid control events have
integer player IDs. All supported periods have an explicit attack sign per team.
Pitch dimensions are 120 by 80. Normalize BOTH axes: sign +1 gives `(x,y)`;
sign -1 gives `(120-x,80-y)`. Do not infer directions from names or period parity.

A valid coordinate is a length-two JSON list of finite numbers (not booleans),
with `0 <= x <= 120`, `0 <= y <= 80`. Missing, null, malformed or out-of-pitch
coordinates are invalid; never infer them from neighbors. Invalid geometry
does not remove an otherwise valid event from the chronological stream.

## Shared event semantics

Control types are exactly `Pass`, `Carry`, `Ball Receipt`, `Shot`, `Ball Recovery`,
`Interception`, `Duel`. A Pass succeeds when `pass_outcome.name` is absent or
`Complete`; Duel and Interception succeed only when `outcome.name == "Won"`;
Ball Recovery succeeds unless `recovery_failure` is literal `true`. Other types
succeed. Break types are exactly `Half Start`, `Half End`, `Foul Committed`,
`Foul Won`, `Offside`, `Ball Out`, `Substitution`, `Red Card`.
The segment key is `(period, possession, play_pattern.name)`; a key change
and subsequent return creates a new segment, never a reusable group.

Where a reception is required, scan forward in the full reconciled stream.
Stop at a break, any segment-key change, or the specified deadline. Ignore
non-control events within that interval. The FIRST control event must be by the
pass's `recipient.id` on the same team, be successful, have valid `location`,
be strictly later in milliseconds, and be within Euclidean distance <=2 of the
pass's raw `end_location`. Never skip a wrong first touch to find a later one.

## CSV rules

Write exactly the specified header, every qualifying row, no extras or
duplicates. IDs are strings, integer columns must contain integers. Decimal
columns must be finite and accurate within absolute `0.000001` of the stated
quantity (six decimals suffice). Header-only output is valid for an empty
answer. The stated row order is required. CSV quoting must preserve commas and
Unicode in names. Eligibility must not use rounded values.

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
