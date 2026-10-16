# Counter Attacks

## Goal: optimal recovery-to-shot matching

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
must avoid opponent control or unsuccessful control. "Transparent" is a
blocker-test-only term: non-control events never block a pair in this test,
and earlier same-team Shots do not break the candidate, so multiple
recoveries/shots may compete. Transparency never exempts an event from the
segmentation step above: a transparent event with a different segment key
still cuts the run at the segmentation step, so the pair never reaches the
blocker test.

Worked example: `rj` Ball Recovery (Open Play) at 90.0 s, `jbreak` Pressure
(From Corner) at 90.5 s, `sj` Shot (Open Play) at 91.0 s, all same
period/possession, form THREE runs, so `rj`/`sj` can never pair even though
`jbreak` is transparent in the blocker test. Common mistake (and the reason
the base fixture excludes `rj,sj`): treating a transparent `Pressure` as
run-invisible. Precedence: if any other sentence in this prompt appears to
say non-controls never split runs, this Segment FIRST paragraph overrides it
for counter-attacks.

Applying the transition-phase concept above is deliberate domain reasoning:
a dead-ball pattern change ends the phase even with no touch, which is why
the `rj`/`jbreak`/`sj` example forms three runs. Fixtures use the real
StatsBomb event taxonomy, 120x80 pitch ranges, and `HH:MM:SS.mmm` timestamps;
adversarial cases (revisions, deletes, name collisions, mirrored directions)
simulate real feed noise while keeping grading deterministic.

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
