#!/usr/bin/env python3
import json, csv
REC = {"Ball Recovery", "Duel", "Interception"}
def pts(t):
    h, m, r = t.split(":")
    return int(h)*3600 + int(m)*60 + float(r)
def sign(team, period):
    return (1 if period == 1 else -1) if team == "Team A" else (-1 if period == 1 else 1)
def nx(x, s): return x if s == 1 else 120 - x
def main():
    evs = json.load(open("/workspace/events.json"))
    for e in evs: e["_ts"] = pts(e["timestamp"])
    recs = [e for e in evs if e.get("type",{}).get("name") in REC]
    shots = [e for e in evs if e.get("type",{}).get("name") == "Shot"]
    used = set(); rows = []
    for r in sorted(recs, key=lambda x: (x["period"], x["_ts"])):
        cands = []
        for s in shots:
            if s["id"] in used: continue
            if s["team"]["id"] != r["team"]["id"]: continue
            if s["period"] != r["period"]: continue
            if s["possession"] != r["possession"]: continue
            if s.get("play_pattern",{}).get("name") != r.get("play_pattern",{}).get("name"): continue
            d = s["_ts"] - r["_ts"]
            if not (0 < d <= 12.0 + 1e-9): continue
            # intervening pattern check
            bad = False
            for m in evs:
                if m["period"] != r["period"]: continue
                if not (r["_ts"] < m["_ts"] < s["_ts"]): continue
                if m.get("play_pattern",{}).get("name") != s.get("play_pattern",{}).get("name"):
                    bad = True; break
            if bad: continue
            sg = sign(r["team"]["name"], r["period"])
            df = round(nx(s["location"][0], sg) - nx(r["location"][0], sg), 2)
            if df < 15: continue
            cands.append((d, s, df))
        if cands:
            cands.sort(key=lambda x: x[0])
            d, s, df = cands[0]
            used.add(s["id"])
            rows.append((r["id"], s["id"], r["team"]["name"], round(d,3), df))
    rows.sort(key=lambda x: (x[3], x[0]))
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["recovery_id","shot_id","team","seconds","distance_forward"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
