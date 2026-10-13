#!/usr/bin/env python3
import json, csv
from collections import defaultdict
def main():
    lineups = json.load(open("/workspace/lineups.json"))
    evs = json.load(open("/workspace/events.json"))
    starters = {}  # (team, player) -> True
    for t in lineups:
        for p in t["lineup"]:
            starters[(t["team_name"], p["player_name"])] = True
    sub_on = {}; sub_off = {}
    for e in evs:
        if e.get("type",{}).get("name") == "Substitution":
            team = e["team"]["name"]
            off = e["player"]["name"]
            on = e.get("substitution",{}).get("replacement",{}).get("name")
            if on: sub_on[(team, on)] = e["minute"]
            sub_off[(team, off)] = e["minute"]
    # appearances: team -> player -> first minute
    first = {}; seen = set()
    for e in evs:
        if e.get("type",{}).get("name") == "Substitution": continue
        t = e["team"]["name"]; p = e["player"]["name"]
        seen.add((t,p))
        if (t,p) not in first: first[(t,p)] = e["minute"]
        else: first[(t,p)] = min(first[(t,p)], e["minute"])
    # last appearance too for off check
    last = {}
    for e in evs:
        if e.get("type",{}).get("name") == "Substitution": continue
        t = e["team"]["name"]; p = e["player"]["name"]
        last[(t,p)] = max(last.get((t,p), -1), e["minute"])
    rows = []
    checked = set(starters) | set(seen)
    for (team, player) in sorted(checked):
        is_starter = (team, player) in starters
        appeared = (team, player) in seen
        on = sub_on.get((team, player), 0 if is_starter else None)
        off = sub_off.get((team, player), None)
        mins = None
        if on is None and off is None:
            mins = 90 if appeared else 0
        else:
            o = on if on is not None else 0
            f = off if off is not None else 90
            mins = max(0, min(90, f) - max(0, min(90, o)))
        mm = None
        if is_starter and not appeared:
            mm = "started_no_events"
        elif not is_starter and appeared and (team, player) not in sub_on:
            mm = "played_not_started"
        elif (team, player) in sub_on and appeared and first[(team, player)] < sub_on[(team, player)]:
            mm = "sub_minute_mismatch"
        elif is_starter and (team, player) in sub_off and appeared and last[(team, player)] > sub_off[(team, player)]:
            mm = "sub_minute_mismatch"
        if mm:
            rows.append((team, player, mm, mins))
    rows.sort(key=lambda r: (r[0], r[1]))
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["team","player","mismatch_type","minutes_played"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
