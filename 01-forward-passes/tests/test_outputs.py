import json, csv, pathlib
def attack_sign(team, period):
    return (1 if period == 1 else -1) if team == "Team A" else (-1 if period == 1 else 1)
def test_output_exists():
    assert pathlib.Path("/workspace/output.csv").exists(), "output.csv missing"
def test_header_exact():
    h = open("/workspace/output.csv").readline().strip()
    assert h == "id,minute,player,end_x,end_y", f"bad header: {h}"
def test_count():
    rows = list(csv.DictReader(open("/workspace/output.csv")))
    assert len(rows) == 5, f"expected 5 forward passes, got {len(rows)}"
def test_expected_ids():
    rows = list(csv.DictReader(open("/workspace/output.csv")))
    ids = sorted(r["id"] for r in rows)
    assert ids == ["e001", "e003", "e006", "e007", "e012"], f"wrong ids: {ids}"
def test_no_backward():
    events = {e["id"]: e for e in json.load(open("/workspace/events.json"))}
    for r in csv.DictReader(open("/workspace/output.csv")):
        e = events[r["id"]]
        s = attack_sign(e["team"]["name"], e["period"])
        assert (e["end_location"][0] - e["location"][0]) * s > 0, f"{r['id']} not forward"
def test_half_flip():
    # e005 (60->75, A, period 2) is backward and must be absent; e006 (60->45, A, period 2) forward present
    rows = {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "e005" not in rows and "e006" in rows
def test_missing_skipped():
    rows = {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "e009" not in rows
def test_sorted():
    rows = list(csv.DictReader(open("/workspace/output.csv")))
    keys = [(int(r["minute"]), r["id"]) for r in rows]
    assert keys == sorted(keys)
def test_carry_excluded():
    rows = {r["id"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert "e010" not in rows
