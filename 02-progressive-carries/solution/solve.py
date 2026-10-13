#!/usr/bin/env python3
import json, csv
def sign(team, period):
    return (1 if period == 1 else -1) if team == "Team A" else (-1 if period == 1 else 1)
def nx(x, s):
    return x if s == 1 else 120 - x
def main():
    evs = json.load(open("/workspace/events.json"))
    rows = []
    for e in evs:
        try:
            if e.get("type", {}).get("name") != "Carry":
                continue
            if "end_location" not in e or e["end_location"] is None:
                continue
            loc, end = e.get("location"), e["end_location"]
            if loc is None:
                continue
            s = sign(e["team"]["name"], e["period"])
            df = round(nx(end[0], s) - nx(loc[0], s), 2)
            if df >= 10 and nx(end[0], s) >= 80:
                rows.append((e["id"], e["minute"], e["player"]["name"], loc[0], loc[1], end[0], end[1], df))
        except (KeyError, TypeError, IndexError):
            continue
    rows.sort(key=lambda r: (r[1], r[0]))
    with open("/workspace/output.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "minute", "player", "start_x", "start_y", "end_x", "end_y", "distance_forward"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
