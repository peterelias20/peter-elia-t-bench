"""Author reference algorithms; copied into each task's private solution."""
import argparse
import csv
import json
import math
import re
from functools import lru_cache
from pathlib import Path

CONTROL = {"Pass", "Carry", "Ball Receipt", "Shot", "Ball Recovery", "Interception", "Duel"}
BREAK = {"Half Start", "Half End", "Foul Committed", "Foul Won", "Offside", "Ball Out", "Substitution", "Red Card"}


def name(e, key):
    value = e.get(key)
    return value.get("name", "") if isinstance(value, dict) else ""


def clock(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}:\d{2}:\d{2}\.\d{3}", value):
        raise ValueError("invalid clock")
    h, m, s = value.split(":")
    seconds, fraction = s.split(".")
    if len(fraction) != 3 or not (0 <= int(m) < 60 and 0 <= int(seconds) < 60):
        raise ValueError("invalid clock")
    return (int(h) * 3600 + int(m) * 60 + int(seconds)) * 1000 + int(fraction)


def canonical(raw):
    latest = {}
    for position, e in enumerate(raw):
        if not isinstance(e, dict) or not isinstance(e.get("id"), str):
            continue
        revision = e.get("revision", 0)
        if type(revision) != int or revision < 0:
            continue
        old = latest.get(e["id"])
        if old is None or (revision, position) > old[:2]:
            latest[e["id"]] = (revision, position, e)
    result = []
    for _, _, e in latest.values():
        if e.get("deleted") is True:
            continue
        try:
            if type(e["period"]) != int or type(e["index"]) != int:
                continue
            if type(e["team"]["id"]) != int or not isinstance(name(e, "type"), str) or not name(e, "type"):
                continue
            if type(e["possession"]) != int or not isinstance(name(e, "play_pattern"), str) or not name(e, "play_pattern"):
                continue
            result.append(dict(e, _ms=clock(e["timestamp"])))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return sorted(result, key=order)


def order(e):
    return e["period"], e["_ms"], e["index"], e["id"]


def point(e, key="location"):
    p = e.get(key)
    if not isinstance(p, list) or len(p) != 2:
        return None
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in p):
        return None
    return p if 0 <= p[0] <= 120 and 0 <= p[1] <= 80 else None


def team(e):
    return e["team"]["id"]


def player(e):
    p = e.get("player")
    return p.get("id") if isinstance(p, dict) else None


def team_name(e, match):
    return next(t["name"] for t in match["teams"] if t["id"] == team(e))


def norm(p, e, match):
    sign = next(t for t in match["teams"] if t["id"] == team(e))["attack_sign"][str(e["period"])]
    return tuple(p) if sign == 1 else (120 - p[0], 80 - p[1])


def successful(e):
    t = name(e, "type")
    if t == "Pass":
        return name(e, "pass_outcome") in ("", "Complete")
    if t in {"Duel", "Interception"}:
        return name(e, "outcome") == "Won"
    if t == "Ball Recovery":
        return e.get("recovery_failure") is not True
    return True


def segment_key(e):
    return e["period"], e.get("possession"), name(e, "play_pattern")


def next_control(events, i, limit):
    """First control, with breaks/key changes invalidating the search."""
    start = events[i]
    for e in events[i + 1:]:
        if segment_key(e) != segment_key(start) or name(e, "type") in BREAK:
            return None
        if e["_ms"] - start["_ms"] > limit:
            return None
        if name(e, "type") in CONTROL:
            return e
    return None


def reception(events, i, match, limit):
    e = events[i]
    r = next_control(events, i, limit)
    recipient = e.get("recipient", {})
    end = point(e, "end_location")
    if r is None or team(r) != team(e) or player(r) != recipient.get("id"):
        return None
    if not successful(r) or not point(r) or not end:
        return None
    if not (0 < r["_ms"] - e["_ms"] <= limit):
        return None
    return r if math.dist(end, point(r)) <= 2 else None


def matching(left, right, edges):
    """Exact cardinality, total millisecond cost, then lexicographic pair list."""
    left = sorted(left, key=lambda e: e["id"])
    right = sorted(right, key=lambda e: e["id"])
    choices = {e["id"]: [] for e in left}
    for i, r in enumerate(right):
        for l in left:
            pair = (l["id"], r["id"])
            if pair in edges:
                choices[l["id"]].append((i, edges[pair], pair))

    @lru_cache(None)
    def visit(i, mask):
        if i == len(left):
            return 0, 0, ()
        best = visit(i + 1, mask)
        for j, cost, pair in choices[left[i]["id"]]:
            if mask & (1 << j):
                continue
            count, total, pairs = visit(i + 1, mask | (1 << j))
            candidate = count + 1, total + cost, (pair,) + pairs
            if (-candidate[0], candidate[1], candidate[2]) < (-best[0], best[1], best[2]):
                best = candidate
        return best

    return visit(0, 0)[2]


def lineup_consistency(events, match, lineups):
    roster, starters, names = {}, set(), {}
    for t in lineups:
        for p in t["players"]:
            k = t["team_id"], p["id"]
            roster[k] = p
            names[k] = p["name"]
            if p["starter"]:
                starters.add(k)
    active = {k: 0 for k in starters}
    dismissed, seen, flags, minutes = set(), set(), {}, {}
    periods = {p["id"]: p for p in match["periods"]}
    finish = sum(p["duration_ms"] for p in match["periods"])

    def elapsed(e):
        p = periods[e["period"]]
        return p["offset_ms"] + min(e["_ms"], p["duration_ms"])

    def flag(k, value):
        flags.setdefault(k, set()).add(value)

    def close(k, now):
        minutes[k] = minutes.get(k, 0) + max(0, now - active.pop(k))

    for e in events:
        k = team(e), player(e)
        typ, now = name(e, "type"), elapsed(e)
        if k[1] is not None and k not in names:
            names[k] = name(e, "player")
        if typ == "Substitution":
            on = team(e), e.get("substitution", {}).get("replacement", {}).get("id")
            if on[1] is None:
                flag(k, "invalid_substitution")
                continue
            if on not in names:
                names[on] = e["substitution"]["replacement"].get("name", "")
            valid = k in roster and on in roster and k in active and on not in active and on not in dismissed and k != on
            if not valid:
                flag(k, "invalid_substitution")
                flag(on, "invalid_substitution")
                continue
            close(k, now)
            active[on] = now
        elif typ == "Red Card":
            if k not in active:
                flag(k, "invalid_dismissal")
            else:
                close(k, now)
                dismissed.add(k)
        elif typ in CONTROL and k[1] is not None:
            seen.add(k)
            if k not in roster:
                flag(k, "unregistered_player")
            if k not in active:
                flag(k, "inactive_appearance")
    for k in list(active):
        close(k, finish)
    for k in starters - seen:
        flag(k, "started_no_events")
    tnames = {t["id"]: t["name"] for t in match["teams"]}
    rows = [(k[0], k[1], tnames[k[0]], names.get(k, ""), ";".join(sorted(v)), minutes.get(k, 0) / 60000)
            for k, v in sorted(flags.items())]
    return ["team_id", "player_id", "team", "player", "mismatch_types", "minutes_played"], rows



def run(task):
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--match", required=True)
    parser.add_argument("--lineups")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    events = canonical(json.loads(Path(args.events).read_text()))
    match = json.loads(Path(args.match).read_text())
    teams = {t["id"] for t in match["teams"]}
    periods = {p["id"] for p in match["periods"]}
    events = [e for e in events if team(e) in teams and e["period"] in periods]
    lineups = json.loads(Path(args.lineups).read_text()) if args.lineups else None
    header, rows = globals()[task.replace("-", "_")](events, match, lineups)
    if task in {"forward-passes", "progressive-carries", "switch-of-play", "crosses", "set-piece-splitter"}:
        lookup = {e["id"]: order(e) for e in events}
        rows.sort(key=lambda row: lookup[row[0]])
    with open(args.output, "w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(header)
        writer.writerows(tuple(f"{v:.6f}" if isinstance(v, float) else v for v in row) for row in rows)


if __name__ == '__main__':
    run('lineup-consistency')
