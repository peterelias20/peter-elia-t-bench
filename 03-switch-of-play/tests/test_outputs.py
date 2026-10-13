import csv, math, json, pathlib
def L(a,b): return round(math.hypot(b[0]-a[0],b[1]-a[1]),2)
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="id,minute,player,length,end_x,end_y"
def test_ids():
    ids=sorted(r["id"] for r in csv.DictReader(open("/workspace/output.csv")))
    assert ids==["s001","s002","s003","s005"], f"{ids}"
def test_recompute_not_trust():
    # s006 has pass.length=40 but true len ~14 -> must be absent; s005 pass.length=5 but true ~68 -> present
    ids={r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "s006" not in ids and "s005" in ids and "s007" not in ids
def test_length_values():
    evs={e["id"]:e for e in json.load(open("/workspace/events.json"))}
    for r in csv.DictReader(open("/workspace/output.csv")):
        e=evs[r["id"]]
        assert abs(float(r["length"])-L(e["location"],e["end_location"]))<0.01
        assert float(r["length"])>35
def test_wing_flip():
    evs={e["id"]:e for e in json.load(open("/workspace/events.json"))}
    def wing(y): return "L" if y<30 else ("R" if y>50 else "M")
    for r in csv.DictReader(open("/workspace/output.csv")):
        e=evs[r["id"]]
        assert {wing(e["location"][1]),wing(e["end_location"][1])}=={"L","R"}
