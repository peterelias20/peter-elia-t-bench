# Counter Attacks

## Goal: optimal recovery-to-shot matching

Split the FULL stream into contiguous segment-key runs; split and exclude
breaks. Recoveries are successful Duel/Interception/Ball Recovery with valid
location; shots are Shot with valid location. Each segment has at most 12 of
each. Candidate pairs require same team, `0 < shot_ms-recovery_ms <=12000`,
and normalized shot_x-recovery_x >=15, all before rounding.

Every event strictly BETWEEN the pair in CANONICAL ORDER (including records
at either endpoint's timestamp) must avoid opponent control or unsuccessful
control. Non-controls are transparent. Earlier same-team Shots do not break
the candidate, so multiple recoveries/shots may compete.

Choose a one-to-one matching per segment: maximize pair count, then minimize
total millisecond duration, then choose the lexicographically smallest sorted
list of `(recovery_id,shot_id)` string tuples. Do not greedily take first shots.

Header: `recovery_id,shot_id,team_id,seconds,distance_forward`

seconds = shot-recovery milliseconds/1000. distance_forward is normalized x
difference. Sort by recovery_id string, then shot_id string.

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
