# Crosses

## Goal: verified cross-to-shot attribution

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
