import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="team,player,mismatch_type,minutes_played"
def test_mismatches():
    m={(r["team"],r["player"]):r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert m[("Team A","A4")]["mismatch_type"]=="started_no_events"
    assert m[("Team A","A5")]["mismatch_type"]=="started_no_events"
    assert m[("Team B","B9")]["mismatch_type"]=="sub_minute_mismatch"
    assert ("Team A","A6") not in m, "A6 has clean sub, should not be flagged"
def test_minutes():
    m={(r["team"],r["player"]):r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert m[("Team B","B9")]["minutes_played"]=="20"
def test_sorted():
    rows=list(csv.DictReader(open("/workspace/output.csv")))
    keys=[(r["team"],r["player"]) for r in rows]
    assert keys==sorted(keys)
