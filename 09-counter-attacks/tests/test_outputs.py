import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="recovery_id,shot_id,team,seconds,distance_forward"
def test_pairs():
    rows=list(csv.DictReader(open("/workspace/output.csv")))
    assert len(rows)==2, f"{rows}"
    m={r["recovery_id"]:r for r in rows}
    assert m["r001"]["shot_id"]=="s101" and m["r002"]["shot_id"]=="s102"
def test_boundaries():
    m={r["recovery_id"]:r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert abs(float(m["r002"]["seconds"])-12.0)<1e-6
    assert "r003" not in m and "r004" not in m
def test_pattern_break():
    assert "r005" not in {r["recovery_id"] for r in csv.DictReader(open("/workspace/output.csv"))}
