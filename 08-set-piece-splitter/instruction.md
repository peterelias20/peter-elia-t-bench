# Set-Piece Splitter

## Goal
Tag every event as `open_play | corner | free_kick | throw_in | kick_off`.

## Inputs
- `/workspace/events.json` with `play_pattern.name` and optional `pass.corner`, `pass.free_kick`, `pass.throw` (presence of key = set piece, value may be `{}`).

## Precedence table (exact — conflicts resolved here, not by guessing)
1. If `pass` dict has key `corner` (non-null) -> `corner` (highest).
2. Elif `pass` has key `free_kick` -> `free_kick`.
3. Elif `pass` has key `throw` -> `throw_in`.
4. Else map `play_pattern.name`: `Open Play`->`open_play`, `From Corner`->`corner`, `From Free Kick`->`free_kick`, `From Throw In`->`throw_in`, `From Kick Off`->`kick_off`, anything else ->`open_play`.

## Output
- `/workspace/output.csv` header: `id,minute,play_pattern,derived_tag`
- `play_pattern` is raw `play_pattern.name`.
- One row per input event. Sort by `minute`, then `id`.
