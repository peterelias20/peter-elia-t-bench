#!/usr/bin/env python3
import json, csv
MAP = {"Open Play":"open_play","From Corner":"corner","From Free Kick":"free_kick","From Throw In":"throw_in","From Kick Off":"kick_off"}
def tag(e):
    p = e.get("pass", None)
    if isinstance(p, dict):
        if p.get("corner") is not None: return "corner"
        if p.get("free_kick") is not None: return "free_kick"
        if p.get("throw") is not None: return "throw_in"
    return MAP.get(e.get("play_pattern",{}).get("name"), "open_play")
def main():
    evs = json.load(open("/workspace/events.json"))
    rows = sorted(((e["id"], e["minute"], e["play_pattern"]["name"], tag(e)) for e in evs), key=lambda r: (r[1], r[0]))
    with open("/workspace/output.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["id","minute","play_pattern","derived_tag"])
        w.writerows(rows)
if __name__ == "__main__":
    main()
