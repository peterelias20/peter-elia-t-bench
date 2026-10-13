#!/usr/bin/env python3
import json, csv, math
def wing(y):
    if y < 30: return "L"
    if y > 50: return "R"
    return "M"
def main():
    evs = json.load(open("/workspace/events.json"))
    rows = []
    for e in evs:
        try:
            if e.get("type", {}).get("name") != "Pass":
                continue
            if "end_location" not in e or e["end_location"] is None:
                continue
            loc, end = e["location"], e["end_location"]
            L = round(math.hypot(end[0]-loc[0], end[1]-loc[1]), 2)
            if L > 35 and ((wing(loc[1]) == "L" and wing(end[1]) == "R") or (wing(loc[1]) == "R" and wing(end[1]) == "L")):
                rows.append((e["id"], e["minute"], e["player"]["name"], L, end[0], end[1]))
        except (KeyError, TypeError, IndexError):
            continue
    rows.sort(key=lambda r: (r[1], r[0]))
    with open("/workspace/output.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "minute", "player", "length", "end_x", "end_y"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
