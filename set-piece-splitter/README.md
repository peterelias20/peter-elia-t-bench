# Set Piece Splitter

## Goal: restart provenance with bounded inheritance

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

## Author verification

The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.

Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.

Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.
