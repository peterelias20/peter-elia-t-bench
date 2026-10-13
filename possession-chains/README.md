# Possession Chains

## Goal: contiguous possession reconstruction

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
