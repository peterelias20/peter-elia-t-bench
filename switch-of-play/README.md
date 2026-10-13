# Switch Of Play

## Goal: switches with verified retention

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
