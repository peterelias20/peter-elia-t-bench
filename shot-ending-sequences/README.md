# Shot Ending Sequences

## Goal: reconstruct bounded shot origins

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
