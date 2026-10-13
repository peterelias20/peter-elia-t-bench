# peter-elia-t-bench

Ten synthetic football analytics tasks, each targeting hard difficulty.

| Task name | Folder | Challenge |
|---|---|---|
| codimango/forward-passes | forward-passes | Reconciled goalward passes, verified receivers and line crossings |
| codimango/progressive-carries | progressive-carries | Maximal carry stitching, spatial gaps and path efficiency |
| codimango/switch-of-play | switch-of-play | Normalized wing switches with verified reception and retention |
| codimango/possession-chains | possession-chains | Contiguous segments, terminal events and signed progression |
| codimango/press-then-win | press-then-win | Maximum-cardinality attribution with cost and lexical tie breaking |
| codimango/shot-ending-sequences | shot-ending-sequences | Bounded backward reconstruction with transparent pressure events |
| codimango/crosses | crosses | Cross reception, shot provenance and competing assist attribution |
| codimango/set-piece-splitter | set-piece-splitter | Stateful restart precedence, expiry and provenance |
| codimango/counter-attacks | counter-attacks | Optimal recovery-to-shot matching with intervening-control constraints |
| codimango/lineup-consistency | lineup-consistency | Atomic substitutions, reentries, dismissals and playing intervals |

Each package contains `task.toml`, `instruction.md`, `environment/`, private
`solution/`, and `tests/`. Only input JSON files are copied into the agent image.
Submit `/workspace/analyze.py` and `/workspace/output.csv`. The analyzer must
accept arbitrary input/output paths; see each task's instruction for its schema.

All feeds require revision reconciliation and authoritative team IDs/directions.
The verifier checks every output field and row order, then executes the submitted
analyzer on five frozen cases. It never runs the reference solution while grading
an agent submission. The task harness must inject private tests after the agent
turn and run the Linux verifier as root so candidate code can be isolated as
`nobody`.

```sh
python3 tools/verify_tasks.py
```

Author generators in `tools/` rebuild the packages and independent labels:

```sh
python3 tools/build_tasks.py
```

Difficulty labels describe the intended challenge. Model pass rates for these
revisions are not yet measured. See [HARDENING.md](HARDENING.md).
