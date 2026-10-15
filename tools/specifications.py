"""Complete, standalone prompt text for the revised tasks."""

COMMON = """## Files and submission

Read `/workspace/events.json` and `/workspace/match.json`. These are synthetic,
StatsBomb-style feeds. Submit a **stdlib-only Python program** at
`/workspace/analyze.py` supporting:

```sh
python3 /workspace/analyze.py --events EVENTS --match MATCH --output OUTPUT
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
"""

DETAILS = {
    "forward-passes": """## Goal: verified, goalward forward passes

Consider only successful Open Play Passes with valid start/end coordinates.
Require normalized `end_x > start_x` AND a strictly positive reduction in
Euclidean distance to the goal center `(120,40)`. Require reception within
2000 ms. Count lines crossed among x=40,80,102 using `start_x < line <= end_x`.

Header:
`pass_id,receipt_id,team_id,player_id,forward_distance,goal_distance_gain,lines_crossed,start_x,end_x,end_y`

`player_id` is the passer; forward_distance is normalized end_x-start_x;
goal_distance_gain is start-goal distance minus end-goal distance.
The final three coordinate columns are RAW. Sort by the pass's canonical order.
""",
    "progressive-carries": """## Goal: stitch progressive carry episodes

Build maximal chains of Carry events with valid start/end coordinates.
Consecutive carries may join only with identical segment key, team and player,
time gap in [0,1000] ms, and Euclidean distance <=1 between the prior end and
next start. Pressure is transparent unless its segment key changes, which ends
the current chain. Every other non-Carry event ends the chain. An invalid Carry
also ends the chain and is excluded. Evaluate entire maximal chains, never
emit overlapping subchains. Single carries can qualify.

For each chain, distance_forward is normalized last end_x minus first start_x.
path_length is the sum of raw start-to-end Euclidean distances PLUS all bridging
end-to-next-start distances. efficiency = distance_forward/path_length (0 for
zero path). Keep only distance_forward >=10, normalized last end_x >=80, and
efficiency >=0.75, using unrounded values.

Header:
`first_id,last_id,team_id,player_id,carry_count,distance_forward,path_length,efficiency`

Sort by the first carry's canonical order.
""",
    "switch-of-play": """## Goal: switches with verified retention

Consider successful Open Play Passes with valid coordinates. Recompute length
from coordinates. Require length >35 and a strict normalized wing flip:
start_y<30 to end_y>50, or start_y>50 to end_y<30. y=30 and y=50 are central.
Require reception within 3000 ms.

After that receipt, require TWO additional successful control events by the
same team within 6000 ms of the receipt (inclusive). Ignore non-control events;
stop on any segment-key change, break, opponent control, or unsuccessful
control. A Shot counts but stops the scan immediately; a first-action shot
does not satisfy the two-action requirement. Receipts and later controls may
be at equal timestamps if their canonical order is later. Retention does not
require coordinates or player continuity for those two later controls.

Header:
`pass_id,receipt_id,retained_until_id,wing_change,length,reception_seconds`

retained_until_id is the second retained control. wing_change is
`left_to_right` or `right_to_left` in the NORMALIZED frame. reception_seconds
uses pass-to-receipt milliseconds/1000. Sort by the pass's canonical order.
""",
    "possession-chains": """## Goal: contiguous possession reconstruction

Drop every Pressure event first. Iterate the remaining canonical stream.
Break events end the current chain and are excluded. All other events count.
Start a new chain whenever segment key or team changes, or consecutive retained
events are >8000 ms apart. Shot and unsuccessful Pass terminate the chain AFTER
being included. A later return to an earlier possession/pattern starts a new
chain. Invalid geometry still counts as an event but contributes zero progress.

Header:
`chain_id,period,possession_id,team_id,play_pattern,event_count,unique_players,start_id,end_id,duration_seconds,net_progress,ends_in_shot`

chain_id and start_id are the first event ID; end_id is the last. unique_players
counts distinct present player IDs. duration_seconds is last-first timestamp.
net_progress is the signed sum of normalized end_x-start_x over Pass/Carry
events with BOTH valid coordinates, including an unsuccessful terminal pass.
ends_in_shot is integer 0 or 1. Sort by chain start's canonical order.
""",
    "press-then-win": """## Goal: optimal pressure-to-win attribution

Split the FULL stream into contiguous segment-key runs, also splitting and
excluding break events. Within each segment, pressures are Pressure events
with valid location; wins are successful Duel/Interception/Ball Recovery
events with valid location. Each segment has at most 12 pressures and 12 wins.
An eligible pair has same team, `0 < win_ms-pressure_ms <=5000`, and raw
Euclidean location distance <=10. Other control events do not cancel a pair.

Find a one-to-one matching independently per segment. Optimize in this order:
1. MAXIMIZE number of pairs.
2. MINIMIZE sum of unrounded millisecond gaps.
3. Choose the lexicographically smallest sorted list of `(pressure_id,win_id)`
   string tuples. A chronological greedy join is not sufficient.

Header: `pressure_id,win_id,team_id,seconds_between,distance`

seconds_between = millisecond gap/1000; distance is raw Euclidean distance.
Sort output by pressure_id, then win_id, using string order.
""",
    "shot-ending-sequences": """## Goal: reconstruct bounded shot origins

For every Shot with valid location, initialize a chain containing the shot.
For a non-Open Play shot, emit this singleton. Otherwise walk backwards in the
FULL canonical stream, stopping BEFORE a segment-key change, break, earlier
Shot, opponent non-Pressure event, unsuccessful non-Pressure event, or any
non-Pressure event with invalid location. Pressure is transparent after the
key/break checks and does not count or update the previous retained time.

For other events also stop if the gap to the earliest currently retained event
is >4000 ms or the shot-to-event age is >15000 ms. Retain up to FIVE previous
non-Pressure events plus the shot. Equal timestamps may be retained if ordered
earlier. An earlier shot is always excluded, even a same-team rebound.

Header:
`shot_id,origin_id,chain_length,event_ids,origin_x,origin_y,duration_seconds,distance_forward`

event_ids is the chronological retained IDs joined by semicolons. Origin is
the earliest retained event; origin coordinates are RAW. duration_seconds is
shot-origin milliseconds/1000; distance_forward is normalized shot_x-origin_x
(may be negative). Sort by shot_id string.
""",
    "crosses": """## Goal: verified cross-to-shot attribution

Candidate crosses are successful Passes where `pass` is a dictionary and
`cross` has a non-null value: false, 0, and {} all qualify. Require valid end
coordinates with normalized end_x>=102 and 18<=normalized end_y<=62.
Ignore height, length, and start location. Require reception within 2500 ms;
the first touch can itself be a Shot.

Starting at the receipt, find the first same-team successful Shot at most
8000 ms after the cross. Ignore non-controls; stop at a break, segment-key
change, opponent control or unsuccessful control. The first Shot stops the
search. If multiple crosses nominate the same Shot, assign it ONLY to the
latest cross in canonical order. Each cross nominates at most one shot.

Header:
`cross_id,receipt_id,shot_id,team_id,assist_type,seconds_to_shot,end_x,end_y`

assist_type is `direct` if receipt_id==shot_id, otherwise `assisted`.
seconds_to_shot uses cross-to-shot time; end coordinates are RAW.
Sort by the selected cross's canonical order.
""",
    "set-piece-splitter": """## Goal: restart provenance with bounded inheritance

Classify EVERY canonical event while maintaining at most one restart context.
Before classifying, clear context on period/possession change, age >10000 ms,
3 already-counted control events, a break, or opponent control. Pattern changes
alone do not clear context. An opponent Pressure does not clear it but cannot
inherit it. All break events emit open_play/default and cannot start context.

For other events choose an explicit restart first: ONLY on Pass events, a
dictionary `pass` with non-null corner, else free_kick, else throw, in that
precedence, yields corner/free_kick/throw_in and source `explicit_pass`.
false, 0 and {} count; null does not. Otherwise map play_pattern From Corner,
From Free Kick, From Throw In, From Kick Off to corner/free_kick/throw_in/kick_off
and source `pattern`. Each explicit or pattern restart REPLACES the context,
sets restart_id to itself, age to 0, and resets the count before counting itself.

Without explicit restart, a same-team active context yields its tag, source
`inherited`, originating restart_id, and restart-to-event age. Otherwise emit
open_play/default with empty restart_id and age 0. Open Play or unknown patterns
are not explicit restarts. After classification increment the context count for
any control event. Shot or unsuccessful Pass clears context AFTER its row.

Header: `id,derived_tag,source,restart_id,age_seconds`

Sort by canonical event order; age_seconds = integer millisecond age/1000.
""",
    "counter-attacks": """## Goal: optimal recovery-to-shot matching

A counter-attack is a transition phase: a ball recovery that progresses at
least 15 m normalized forward within 12 s toward a shot, without an opponent
touch or failed control killing the transition. A possession or play-pattern
change (e.g. Open Play to From Corner) marks a new phase even when the ball
is not touched, so the recovery and the shot must share one unbroken phase.

Segment FIRST. Split the FULL reconciled stream in canonical order into
contiguous segment-key `(period, possession, play_pattern.name)` runs BEFORE
any pairing. EVERY event counts for this split, including Pressure and every
other non-control type: any key change starts a new run, and a return to an
earlier key starts yet another run (never a reusable group). Break events also
split runs and are excluded from all runs.

Recoveries are successful Duel/Interception/Ball Recovery with valid
location; shots are Shot with valid location. Each segment has at most 12 of
each. Candidate pairs must lie in the SAME run and require same team,
`0 < shot_ms-recovery_ms <=12000`, and normalized shot_x-recovery_x >=15,
all before rounding.

Blocker test SECOND (inside one run only). Every event strictly BETWEEN the
pair in CANONICAL ORDER (including records at either endpoint's timestamp)
must avoid opponent control or unsuccessful control. "Transparent" applies
ONLY here: non-control events never block a pair in this test, and earlier
same-team Shots do not break the candidate, so multiple recoveries/shots may
compete. Transparency never exempts an event from the segmentation step above.

Worked example: `rj` Ball Recovery (Open Play) at 90.0 s, `jbreak` Pressure
(From Corner) at 90.5 s, `sj` Shot (Open Play) at 91.0 s, all same
period/possession, form THREE runs, so `rj`/`sj` can never pair even though
`jbreak` is transparent in the blocker test.

Choose a one-to-one matching per segment: maximize pair count, then minimize
total millisecond duration, then choose the lexicographically smallest sorted
list of `(recovery_id,shot_id)` string tuples. Do not greedily take first shots.

Header: `recovery_id,shot_id,team_id,seconds,distance_forward`

seconds = shot-recovery milliseconds/1000. distance_forward is normalized x
difference. Sort by recovery_id string, then shot_id string.
""",
    "lineup-consistency": """## Goal: reconcile active-player intervals

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
""",
}
