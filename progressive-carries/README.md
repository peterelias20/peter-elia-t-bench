# Progressive Carries

## Goal: stitch progressive carry episodes

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
