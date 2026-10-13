import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="id,minute,play_pattern,derived_tag"
def test_tags():
    m={r["id"]:r["derived_tag"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert m["k001"]=="open_play"
    assert m["k002"]=="corner"
    assert m["k003"]=="corner"
    assert m["k004"]=="free_kick"
    assert m["k005"]=="throw_in"
    assert m["k006"]=="kick_off"
def test_conflicts():
    m={r["id"]:r["derived_tag"] for r in csv.DictReader(open("/workspace/output.csv"))}
    assert m["k007"]=="free_kick", "pass.free_kick must beat From Corner"
    assert m["k008"]=="corner", "corner has top priority"
def test_count():
    assert len(list(csv.DictReader(open("/workspace/output.csv"))))==8
