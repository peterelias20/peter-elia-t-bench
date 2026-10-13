#!/usr/bin/env python3
import json, csv
def attack_sign(team, period):
    if team == "Team A":
        return 1 if period == 1 else -1
    else:
        return -1 if period == 1 else 1
def main():
    events = json.load(open("/workspace/events.json"))
    rows = []
    for e in events:
        try:
            if e.get("type", {}).get("name") != "Pass":
                continue
            if "end_location" not in e or e["end_location"] is None:
                continue
            loc = e.get("location")
            end = e["end_location"]
            if loc is None:
                continue
            s = attack_sign(e["team"]["name"], e["period"])
            if (end[0] - loc[0]) * s > 0:
                rows.append((e["id"], e["minute"], e["player"]["name"], end[0], end[1]))
        except (KeyError, TypeError, IndexError):
            continue
    rows.sort(key=lambda r: (r[1], r[0]))
    with open("/workspace/output.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "minute", "player", "end_x", "end_y"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
