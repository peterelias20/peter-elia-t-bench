import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="id,minute,player,end_x,end_y"
def test_ids():
    ids=sorted(r["id"] for r in csv.DictReader(open("/workspace/output.csv")))
    assert ids==["x001","x005","x007"], f"{ids}"
def test_height_ignored():
    assert "x004" not in {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
def test_box():
    assert "x002" not in {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "x003" not in {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
