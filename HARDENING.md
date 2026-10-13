# Task hardening

## Name changes

Removed numeric prefixes from all ten folder names and `[task].name` entries.
The root README lists the resulting `codimango/<folder>` names.

## Requirements added

| Task | New work required |
|---|---|
| forward-passes | Reconcile revisions; normalize direction; measure goal-distance gain; validate first receiver; count crossed lines |
| progressive-carries | Stitch maximal episodes with time/spatial continuity; include bridge distances; gate on net gain and efficiency |
| switch-of-play | Recompute strict wing geometry; validate reception; require two retained controls with terminal-shot behavior |
| possession-chains | Preserve contiguous chronology; handle repeated keys and terminal events; compute duration and signed progress |
| press-then-win | Solve one-to-one attribution for maximum count, minimum total time, and deterministic lexical tie breaking |
| shot-ending-sequences | Traverse backwards with separate event-count, gap and age limits; handle pressure, rebounds and period boundaries |
| crosses | Validate first touch and later shot; resolve competing cross attribution; handle non-null false/zero traits |
| set-piece-splitter | Maintain restart state with explicit precedence, inheritance, action-count expiry, time expiry and provenance |
| counter-attacks | Optimize recovery/shot matching under geometry, timing and intervening-control constraints |
| lineup-consistency | Track active intervals with atomic substitutions, reentries, dismissals, homonyms and separate stoppage-time clipping |

Every task now requires a reusable single-file `analyze.py` with explicit input
and output arguments, plus sample output. All difficulty labels are `hard` and
task timeouts are 300 seconds.

## Verifier corrections

The former `tests/test.sh` ran `/solution/solve.sh` before checking results.
It could therefore reward an agent that produced no solution. The revised
verifier exclusively evaluates the submitted sample and submitted analyzer.

Frozen cases contain expected rows authored in `tools/fixtures.py`; the fixture
builder never imports or executes the oracle. The reference is tested against
those labels. All fields, row counts, duplicates, order and finite decimal
values are checked. Unrounded values decide eligibility in the specification.

Five cases per task cover base scenarios, revision replay (including equal
revision tombstones and malformed winners), mirrored coordinates and changed
identities, independent segments, and empty input. Test data is only injected
at verification time. Docker images contain input fixtures and metadata only.

The root Linux verifier protects `/tests`, `/solution` when present, and verifier
logs, then executes a code snapshot as `nobody` with read-only case inputs.
Its isolation depends on the harness running verification as root and injecting
the private tests after the agent turn. The local macOS verifier checks
correctness without claiming that Linux privilege isolation is present.

## Verification

Run the local gate with Python 3.11 or later:

```sh
python3 tools/verify_tasks.py
```

It checks names, TOML, Python syntax, all six reference checks per task, and two
negative submissions per task: a no-op with correct existing sample output,
and a program that always writes the sample answer. Results: **60/60 reference
checks pass; all 20 negative submissions are rejected.**

Run the Linux container gate with:

```sh
python3 tools/verify_container.py
```

The container gate uses the task's declared Python 3.11 environment and actual
`solve.sh` / `test.sh` entrypoints. It copies packages into a private `/task`
directory on the container filesystem. Docker Desktop host bind mounts do not
provide the same ownership/permission behavior; the gate uses container-owned
files. During candidate execution it probes denial of private labels, reference
code, the package directory, and verifier reward writes. Results: **all ten
packages pass their six checks in Linux (60/60), including permission probes.**

## Difficulty calibration and publication

Hard difficulty is the design target; no model trials have been run for these
revisions. The earlier READMEs asserted model pass rates without supporting
logs, so those claims were removed. Local reference success and shortcut
rejection do not establish a model pass-rate split.

The renamed task definitions are published through this Git repository. A
Codimango lookup for the original `codimango/01-forward-passes` name returned
`404 Not Found`; repository metadata changes do not demonstrate that existing
server task identities were renamed. No explicit task rerun or model validation
was started; any validation triggered by a repository push is handled by the
platform.
