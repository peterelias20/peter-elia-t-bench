# Press Then Win

## Goal: optimal pressure-to-win attribution

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
