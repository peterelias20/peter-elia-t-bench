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


def forward_passes(events, match, lineups):
    rows = []
    for i, e in enumerate(events):
        if name(e, "type") != "Pass" or not successful(e) or name(e, "play_pattern") != "Open Play":
            continue
        a, b = point(e), point(e, "end_location")
        if not a or not b:
            continue
        start, end = norm(a, e, match), norm(b, e, match)
        gain = math.dist(start, (120, 40)) - math.dist(end, (120, 40))
        r = reception(events, i, match, 2000)
        if end[0] <= start[0] or gain <= 0 or r is None:
            continue
        lines = sum(start[0] < x <= end[0] for x in (40, 80, 102))
        rows.append((e["id"], r["id"], team(e), player(e), end[0] - start[0], gain, lines, a[0], b[0], b[1]))
    return ["pass_id", "receipt_id", "team_id", "player_id", "forward_distance", "goal_distance_gain", "lines_crossed", "start_x", "end_x", "end_y"], rows


def progressive_carries(events, match, lineups):
    chains = []
    current = []
    for e in events:
        if name(e, "type") == "Pressure":
            if current and segment_key(e) != segment_key(current[-1]):
                chains.append(current)
                current = []
            continue
        if name(e, "type") != "Carry" or not point(e) or not point(e, "end_location"):
            if current:
                chains.append(current)
                current = []
            continue
        if current:
            p = current[-1]
            connected = (segment_key(e) == segment_key(p) and team(e) == team(p) and player(e) == player(p)
                         and 0 <= e["_ms"] - p["_ms"] <= 1000
                         and math.dist(point(p, "end_location"), point(e)) <= 1)
            if not connected:
                chains.append(current)
                current = []
        current.append(e)
    if current:
        chains.append(current)
    rows = []
    for chain in chains:
        a, b = chain[0], chain[-1]
        start, end = norm(point(a), a, match), norm(point(b, "end_location"), b, match)
        distance = end[0] - start[0]
        # Bridging spatial gaps are part of the travelled path.
        path = sum(math.dist(point(e), point(e, "end_location")) for e in chain)
        path += sum(math.dist(point(p, "end_location"), point(q)) for p, q in zip(chain, chain[1:]))
        efficiency = distance / path if path else 0
        if distance >= 10 and end[0] >= 80 and efficiency >= 0.75:
            rows.append((a["id"], b["id"], team(a), player(a), len(chain), distance, path, efficiency))
    return ["first_id", "last_id", "team_id", "player_id", "carry_count", "distance_forward", "path_length", "efficiency"], rows


def switch_of_play(events, match, lineups):
    rows = []
    for i, e in enumerate(events):
        if name(e, "type") != "Pass" or not successful(e) or name(e, "play_pattern") != "Open Play":
            continue
        a, b = point(e), point(e, "end_location")
        if not a or not b:
            continue
        a, b = norm(a, e, match), norm(b, e, match)
        length = math.dist(a, b)
        if not (length > 35 and ((a[1] < 30 and b[1] > 50) or (a[1] > 50 and b[1] < 30))):
            continue
        r = reception(events, i, match, 3000)
        if r is None:
            continue
        retained = []
        for later in events[events.index(r) + 1:]:
            if segment_key(later) != segment_key(e) or name(later, "type") in BREAK or later["_ms"] - r["_ms"] > 6000:
                break
            if name(later, "type") not in CONTROL:
                continue
            if team(later) != team(e) or not successful(later):
                break
            retained.append(later)
            if len(retained) == 2 or name(later, "type") == "Shot":
                break
        if len(retained) == 2:
            rows.append((e["id"], r["id"], retained[-1]["id"], "left_to_right" if a[1] < 30 else "right_to_left", length, (r["_ms"] - e["_ms"]) / 1000))
    return ["pass_id", "receipt_id", "retained_until_id", "wing_change", "length", "reception_seconds"], rows


def possession_chains(events, match, lineups):
    chains, current = [], []
    for e in events:
        if name(e, "type") == "Pressure":
            continue
        if name(e, "type") in BREAK:
            if current:
                chains.append(current)
                current = []
            continue
        if current:
            p = current[-1]
            if segment_key(e) != segment_key(p) or team(e) != team(p) or e["_ms"] - p["_ms"] > 8000:
                chains.append(current)
                current = []
        current.append(e)
        if name(e, "type") == "Shot" or (name(e, "type") == "Pass" and not successful(e)):
            chains.append(current)
            current = []
    if current:
        chains.append(current)
    rows = []
    for chain in chains:
        a, b = chain[0], chain[-1]
        progress = 0
        for e in chain:
            if name(e, "type") in {"Pass", "Carry"} and point(e) and point(e, "end_location"):
                progress += norm(point(e, "end_location"), e, match)[0] - norm(point(e), e, match)[0]
        rows.append((a["id"], a["period"], a["possession"], team(a), name(a, "play_pattern"), len(chain),
                     len({player(e) for e in chain if player(e) is not None}), a["id"], b["id"],
                     (b["_ms"] - a["_ms"]) / 1000, progress, int(name(b, "type") == "Shot")))
    return ["chain_id", "period", "possession_id", "team_id", "play_pattern", "event_count", "unique_players", "start_id", "end_id", "duration_seconds", "net_progress", "ends_in_shot"], rows


def press_then_win(events, match, lineups):
    rows, groups = [], {}
    segment = 0
    previous = None
    for e in events:
        if previous is not None and segment_key(e) != segment_key(previous):
            segment += 1
        if name(e, "type") in BREAK:
            segment += 1
            previous = e
            continue
        groups.setdefault(segment, []).append(e)
        previous = e
    for group in groups.values():
        pressures = [e for e in group if name(e, "type") == "Pressure" and point(e)]
        wins = [e for e in group if name(e, "type") in {"Duel", "Interception", "Ball Recovery"} and successful(e) and point(e)]
        edges = {(p["id"], w["id"]): w["_ms"] - p["_ms"] for p in pressures for w in wins
                 if team(p) == team(w) and 0 < w["_ms"] - p["_ms"] <= 5000 and math.dist(point(p), point(w)) <= 10}
        lookup = {e["id"]: e for e in group}
        for a, b in matching(pressures, wins, edges):
            p, w = lookup[a], lookup[b]
            rows.append((a, b, team(p), edges[(a, b)] / 1000, math.dist(point(p), point(w))))
    return ["pressure_id", "win_id", "team_id", "seconds_between", "distance"], sorted(rows)


def shot_ending_sequences(events, match, lineups):
    rows = []
    for i, s in enumerate(events):
        if name(s, "type") != "Shot" or not point(s):
            continue
        chain = [s]
        if name(s, "play_pattern") == "Open Play":
            for e in reversed(events[:i]):
                if segment_key(e) != segment_key(s) or name(e, "type") in BREAK or name(e, "type") == "Shot":
                    break
                if name(e, "type") == "Pressure":
                    continue
                if team(e) != team(s) or not successful(e) or not point(e):
                    break
                if chain[-1]["_ms"] - e["_ms"] > 4000 or s["_ms"] - e["_ms"] > 15000:
                    break
                chain.append(e)
                if len(chain) == 6:
                    break
        chain.reverse()
        origin = chain[0]
        gain = norm(point(s), s, match)[0] - norm(point(origin), origin, match)[0]
        rows.append((s["id"], origin["id"], len(chain), ";".join(e["id"] for e in chain), point(origin)[0], point(origin)[1], (s["_ms"] - origin["_ms"]) / 1000, gain))
    return ["shot_id", "origin_id", "chain_length", "event_ids", "origin_x", "origin_y", "duration_seconds", "distance_forward"], sorted(rows)


def crosses(events, match, lineups):
    rows = []
    for i, e in enumerate(events):
        flags = e.get("pass")
        if name(e, "type") != "Pass" or not successful(e) or not isinstance(flags, dict) or flags.get("cross") is None:
            continue
        end = point(e, "end_location")
        if not end:
            continue
        x, y = norm(end, e, match)
        if not (x >= 102 and 18 <= y <= 62):
            continue
        r = reception(events, i, match, 2500)
        if r is None:
            continue
        shot = None
        for q in events[events.index(r):]:
            if segment_key(q) != segment_key(e) or name(q, "type") in BREAK or q["_ms"] - e["_ms"] > 8000:
                break
            if name(q, "type") in CONTROL and (team(q) != team(e) or not successful(q)):
                break
            if name(q, "type") == "Shot":
                shot = q
                break
        if shot:
            rows.append((e["id"], r["id"], shot["id"], team(e), "direct" if r["id"] == shot["id"] else "assisted", (shot["_ms"] - e["_ms"]) / 1000, end[0], end[1]))
    # Multiple crosses can lead to the same shot; attribution belongs to the latest cross.
    selected = {}
    lookup = {e["id"]: e for e in events}
    for row in rows:
        old = selected.get(row[2])
        if old is None or order(lookup[row[0]]) > order(lookup[old[0]]):
            selected[row[2]] = row
    return ["cross_id", "receipt_id", "shot_id", "team_id", "assist_type", "seconds_to_shot", "end_x", "end_y"], sorted(selected.values())


def set_piece_splitter(events, match, lineups):
    mapping = {"From Corner": "corner", "From Free Kick": "free_kick", "From Throw In": "throw_in", "From Kick Off": "kick_off"}
    rows, state = [], None
    for e in events:
        typ = name(e, "type")
        if state and (e["period"] != state["event"]["period"] or e.get("possession") != state["event"].get("possession")
                      or e["_ms"] - state["event"]["_ms"] > 10000 or state["count"] >= 3
                      or typ in BREAK or (typ in CONTROL and team(e) != team(state["event"]))):
            state = None
        explicit = None
        flags = e.get("pass")
        if typ == "Pass" and isinstance(flags, dict):
            for key, tag in [("corner", "corner"), ("free_kick", "free_kick"), ("throw", "throw_in")]:
                if flags.get(key) is not None:
                    explicit = tag, "explicit_pass"
                    break
        if explicit is None and name(e, "play_pattern") in mapping:
            explicit = mapping[name(e, "play_pattern")], "pattern"
        if typ in BREAK:
            tag, source, restart, age = "open_play", "default", "", 0
            state = None
        elif explicit:
            tag, source = explicit
            restart, age = e["id"], 0
            state = {"tag": tag, "event": e, "count": 0}
        elif state and team(e) == team(state["event"]):
            tag, source, restart, age = state["tag"], "inherited", state["event"]["id"], (e["_ms"] - state["event"]["_ms"]) / 1000
        else:
            tag, source, restart, age = "open_play", "default", "", 0
        rows.append((e["id"], tag, source, restart, age))
        if state and typ in CONTROL:
            state["count"] += 1
        if typ == "Shot" or (typ == "Pass" and not successful(e)):
            state = None
    return ["id", "derived_tag", "source", "restart_id", "age_seconds"], rows


def counter_attacks(events, match, lineups):
    rows, groups, current = [], [], []
    for e in events:
        if (current and segment_key(e) != segment_key(current[-1])) or name(e, "type") in BREAK:
            if current:
                groups.append(current)
                current = []
        if name(e, "type") not in BREAK:
            current.append(e)
    if current:
        groups.append(current)
    for group in groups:
        recs = [e for e in group if name(e, "type") in {"Duel", "Interception", "Ball Recovery"} and successful(e) and point(e)]
        shots = [e for e in group if name(e, "type") == "Shot" and point(e)]
        edges, gain = {}, {}
        for r in recs:
            for s in shots:
                delta = s["_ms"] - r["_ms"]
                df = norm(point(s), s, match)[0] - norm(point(r), r, match)[0]
                if team(r) != team(s) or not (0 < delta <= 12000) or df < 15:
                    continue
                between = group[group.index(r) + 1:group.index(s)]
                if any(name(e, "type") in CONTROL and (team(e) != team(r) or not successful(e)) for e in between):
                    continue
                edges[(r["id"], s["id"])] = delta
                gain[(r["id"], s["id"])] = df
        lookup = {e["id"]: e for e in group}
        for a, b in matching(recs, shots, edges):
            rows.append((a, b, team(lookup[a]), edges[(a, b)] / 1000, gain[(a, b)]))
    return ["recovery_id", "shot_id", "team_id", "seconds", "distance_forward"], sorted(rows)


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
