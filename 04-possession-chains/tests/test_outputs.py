import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="possession_id,team,event_count,start_minute,end_minute"
def test_split():
    rows={(r["possession_id"],r["team"]):r for r in csv.DictReader(open("/workspace/output.csv"))}
    # possession 1 must appear twice (Open Play x2, From Corner x2)
    poss1=[r for r in csv.DictReader(open("/workspace/output.csv")) if r["possession_id"]=="1"]
    assert len(poss1)==2, f"possession 1 should split into 2 chains, got {poss1}"
    counts=sorted(int(r["event_count"]) for r in poss1)
    assert counts==[2,2], f"{counts}"
def test_counts():
    rows=list(csv.DictReader(open("/workspace/output.csv")))
    assert len(rows)==5, f"expected 5 chains, got {len(rows)}"
def test_extra_time():
    rows={r["possession_id"]:r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert rows["20"]["start_minute"]=="90" and rows["20"]["end_minute"]=="92"
    assert rows["3"]["start_minute"]=="45" and rows["3"]["end_minute"]=="46"
def test_sorted():
    rows=list(csv.DictReader(open("/workspace/output.csv")))
    keys=[(int(r["start_minute"]),int(r["possession_id"])) for r in rows]
    assert keys==sorted(keys)
