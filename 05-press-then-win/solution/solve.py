#!/usr/bin/env python3
import json, csv
WIN = {"Duel", "Interception", "Ball Recovery"}
def parse_ts(t):
    h, m, rest = t.split(":")
    s = float(rest)
    return int(h)*3600 + int(m)*60 + s
def main():
    evs = json.load(open("/workspace/events.json"))
    for e in evs:
        e["_ts"] = parse_ts(e["timestamp"])
    pressures = sorted([e for e in evs if e.get("type",{}).get("name")=="Pressure"], key=lambda x: (x["period"], x["_ts"]))
    wins = sorted([e for e in evs if e.get("type",{}).get("name") in WIN], key=lambda x: (x["period"], x["_ts"]))
    used = set()
    rows = []
    for p in pressures:
        best = None
        for w in wins:
            if w["id"] in used: continue
            if w["period"] != p["period"]: continue
            if w["team"]["id"] != p["team"]["id"]: continue
            d = w["_ts"] - p["_ts"]
            if 0 < d <= 5.0 + 1e-9:
                if best is None or d < best[1]:
                    best = (w, d)
        if best:
            used.add(best[0]["id"])
            rows.append((p["id"], best[0]["id"], p["team"]["name"], round(best[1],3)))
    rows.sort(key=lambda r: r[0])
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["pressure_id","win_id","team","seconds_between"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
