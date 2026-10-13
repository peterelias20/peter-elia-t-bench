#!/usr/bin/env python3
import json, csv
def sign(team, period):
    return (1 if period == 1 else -1) if team == "Team A" else (-1 if period == 1 else 1)
def main():
    evs = json.load(open("/workspace/events.json"))
    rows = []
    for e in evs:
        try:
            if e.get("type",{}).get("name") != "Pass": continue
            if "end_location" not in e or e["end_location"] is None: continue
            p = e.get("pass", None)
            if not isinstance(p, dict) or p.get("cross") is None: continue
            s = sign(e["team"]["name"], e["period"])
            end = e["end_location"]
            nx = end[0] if s == 1 else 120 - end[0]
            if nx >= 102 and 18 <= end[1] <= 62:
                rows.append((e["id"], e["minute"], e["player"]["name"], end[0], end[1]))
        except (KeyError, TypeError, IndexError):
            continue
    rows.sort(key=lambda r: (r[1], r[0]))
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","minute","player","end_x","end_y"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
