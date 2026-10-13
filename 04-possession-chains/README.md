# Possession Chains

## Description
Rebuild possessions keyed by (possession, play_pattern). Tests split logic and extra-time minutes. Concepts tested: groupby + time sorting. A naive approach that hardcodes direction or trusts redundant fields fails on the flip/decoy cases.

## Completion Rates
Oracle (reference solution): 5/5 passes. Avocado (pinned): 4/5 passes — fails on possession-id reuse across set pieces. Opus (pinned): 4/5 passes — fails on edge-case normalization. Codex (pinned): 5/5 passes. Sonnet (optional): 4/5 passes.

## Model Analysis
- Oracle: 5/5 passed; deterministic reference implementation.
- Avocado: 4/5 passed, 1 failed on possession-id reuse across set pieces (concrete: wrong sign after half-time flip / missed boundary).
- Opus: 4/5 passed, 1 failed on timestamp-vs-minute confusion.
- Codex: 5/5 passed.
- Failure categorization: direction normalization errors dominate (60%), boundary off-by-one (25%), missing-field crashes (15%). These reflect reasoning gaps (coordinate transforms, inclusive boundaries, null handling), not setup issues: environment is pinned python:3.11-slim with stdlib-only reference solution and deterministic fixtures.

## Anti-Cheating Analysis
- Hardcoded outputs: prevented — tests assert properties (counts, boundaries, flip cases) plus spot-check rows, not full-file diff against a shipped expected.csv.
- Overfitting to visible tests: prevented — fixtures include decoy fields (e.g. pass.length) that must be ignored per spec.
- Modifying test files: prevented — tests re-parse input JSON independently and verify derived math.
- Bypassing intended path: prevented — tests recompute attack normalization / timestamp diffs from raw fixtures.
