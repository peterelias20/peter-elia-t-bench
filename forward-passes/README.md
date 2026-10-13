# Forward Passes

## Goal: verified, goalward forward passes

Consider only successful Open Play Passes with valid start/end coordinates.
Require normalized `end_x > start_x` AND a strictly positive reduction in
Euclidean distance to the goal center `(120,40)`. Require reception within
2000 ms. Count lines crossed among x=40,80,102 using `start_x < line <= end_x`.

Header:
`pass_id,receipt_id,team_id,player_id,forward_distance,goal_distance_gain,lines_crossed,start_x,end_x,end_y`

`player_id` is the passer; forward_distance is normalized end_x-start_x;
goal_distance_gain is start-goal distance minus end-goal distance.
The final three coordinate columns are RAW. Sort by the pass's canonical order.

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
