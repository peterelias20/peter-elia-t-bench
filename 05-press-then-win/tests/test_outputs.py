import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="pressure_id,win_id,team,seconds_between"
def test_pairs():
    rows=list(csv.DictReader(open("/workspace/output.csv")))
    assert len(rows)==2, f"got {rows}"
    m={r["pressure_id"]:r for r in rows}
    assert m["pr1"]["win_id"]=="w1" and m["pr2"]["win_id"]=="w2"
def test_boundary():
    rows={r["pressure_id"]:r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert abs(float(rows["pr2"]["seconds_between"])-5.0)<1e-6
    assert "pr3" not in rows and "pr4" not in rows
def test_cross_period():
    assert "pr5" not in {r["pressure_id"] for r in csv.DictReader(open("/workspace/output.csv"))}
def test_team():
    assert "pr6" not in {r["pressure_id"] for r in csv.DictReader(open("/workspace/output.csv"))}
