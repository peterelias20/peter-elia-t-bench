import csv, json, pathlib
def test_exists():
    assert pathlib.Path("/workspace/output.csv").exists()
def test_header():
    assert open("/workspace/output.csv").readline().strip() == "id,minute,player,start_x,start_y,end_x,end_y,distance_forward"
def test_count():
    rows = list(csv.DictReader(open("/workspace/output.csv")))
    assert len(rows) == 5, f"got {len(rows)}"
def test_ids():
    ids = sorted(r["id"] for r in csv.DictReader(open("/workspace/output.csv")))
    assert ids == ["c002", "c003", "c004", "c005", "c011"], f"{ids}"
def test_missing_excluded():
    ids = {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "c007" not in ids and "c008" not in ids
def test_thresholds():
    for r in csv.DictReader(open("/workspace/output.csv")):
        assert float(r["distance_forward"]) >= 10.0
def test_short_excluded():
    ids = {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "c001" not in ids and "c006" not in ids and "c012" not in ids
def test_sorted():
    rows = list(csv.DictReader(open("/workspace/output.csv")))
    keys = [(int(r["minute"]), r["id"]) for r in rows]
    assert keys == sorted(keys)
