import csv, pathlib
def test_exists(): assert pathlib.Path("/workspace/output.csv").exists()
def test_header(): assert open("/workspace/output.csv").readline().strip()=="shot_id,chain_length,origin_x,origin_y"
def test_chains():
    m={r["shot_id"]:r for r in csv.DictReader(open("/workspace/output.csv"))}
    assert len(m)==3
    assert m["q004"]["chain_length"]=="4" and m["q004"]["origin_x"]=="30" and m["q004"]["origin_y"]=="30"
    assert m["q008"]["chain_length"]=="2" and m["q008"]["origin_x"]=="40"
    assert m["q010"]["chain_length"]=="1" and m["q010"]["origin_x"]=="105"
def test_break():
    m={r["shot_id"]:r for r in csv.DictReader(open("/workspace/output.csv"))}
    # foul break: q008 chain must NOT include q005
    assert int(m["q008"]["chain_length"])<4
