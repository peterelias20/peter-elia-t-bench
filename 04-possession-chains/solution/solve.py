#!/usr/bin/env python3
import json, csv
from collections import OrderedDict
def main():
    evs = json.load(open("/workspace/events.json"))
    evs_sorted = sorted(evs, key=lambda e: (e["period"], e["minute"]*60 + e["second"], e["id"]))
    groups = OrderedDict()
    for e in evs_sorted:
        key = (e["possession"], e["play_pattern"]["name"])
        groups.setdefault(key, []).append(e)
    rows = []
    for (poss, pp), lst in groups.items():
        team = lst[0]["team"]["name"]
        mins = [x["minute"] for x in lst]
        rows.append((poss, team, len(lst), min(mins), max(mins), min(x["period"]*100000 + x["minute"]*60+x["second"] for x in lst)))
    rows.sort(key=lambda r: (r[5], r[0]))
    with open("/workspace/output.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["possession_id", "team", "event_count", "start_minute", "end_minute"])
        for poss, team, c, s, e, _ in rows:
            w.writerow([poss, team, c, s, e])
if __name__ == "__main__":
    main()
