#!/usr/bin/env python3
import json, csv
BREAK_SUB = ("Half", "Foul", "Offside")
def is_break(e):
    t = e.get("type", {}).get("name", "")
    if any(s in t for s in BREAK_SUB):
        return True
    if e.get("play_pattern", {}).get("name") != "Open Play":
        return True
    return False
def main():
    evs = json.load(open("/workspace/events.json"))
    order = sorted(evs, key=lambda e: (e["period"], e["minute"]*60+e["second"], e["id"]))
    idx = {e["id"]: i for i, e in enumerate(order)}
    rows = []
    for s in [e for e in order if e.get("type",{}).get("name")=="Shot"]:
        if s.get("play_pattern",{}).get("name") != "Open Play":
            rows.append((s["id"], 1, s["location"][0], s["location"][1]))
            continue
        chain = [s]
        i = idx[s["id"]] - 1
        while len(chain) < 6 and i >= 0:
            p = order[i]
            if p["possession"] != s["possession"]: break
            if p.get("play_pattern",{}).get("name") != s.get("play_pattern",{}).get("name"): break
            if is_break(p): break
            chain.append(p)
            i -= 1
        chain.reverse()
        o = chain[0]["location"]
        rows.append((s["id"], len(chain), o[0], o[1]))
    rows.sort(key=lambda r: r[0])
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["shot_id","chain_length","origin_x","origin_y"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
