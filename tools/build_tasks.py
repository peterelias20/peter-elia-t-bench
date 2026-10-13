"""Rebuild the ten task packages without calling an oracle for labels."""
import copy
import json
from pathlib import Path
import random
import re

from fixtures import BUILDERS, MATCH, event, stamp
from specifications import COMMON, DETAILS

ROOT = Path(__file__).resolve().parent.parent
IDS = {"id", "pass_id", "receipt_id", "first_id", "last_id", "chain_id", "start_id", "end_id",
       "retained_until_id", "pressure_id", "win_id", "shot_id", "origin_id", "cross_id", "recovery_id", "restart_id"}
HEADERS = {
    "forward-passes":"pass_id,receipt_id,team_id,player_id,forward_distance,goal_distance_gain,lines_crossed,start_x,end_x,end_y",
    "progressive-carries":"first_id,last_id,team_id,player_id,carry_count,distance_forward,path_length,efficiency",
    "switch-of-play":"pass_id,receipt_id,retained_until_id,wing_change,length,reception_seconds",
    "possession-chains":"chain_id,period,possession_id,team_id,play_pattern,event_count,unique_players,start_id,end_id,duration_seconds,net_progress,ends_in_shot",
    "press-then-win":"pressure_id,win_id,team_id,seconds_between,distance",
    "shot-ending-sequences":"shot_id,origin_id,chain_length,event_ids,origin_x,origin_y,duration_seconds,distance_forward",
    "crosses":"cross_id,receipt_id,shot_id,team_id,assist_type,seconds_to_shot,end_x,end_y",
    "set-piece-splitter":"id,derived_tag,source,restart_id,age_seconds",
    "counter-attacks":"recovery_id,shot_id,team_id,seconds,distance_forward",
    "lineup-consistency":"team_id,player_id,team,player,mismatch_types,minutes_played",
}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sort_rows(task, case):
    rows, header = case["expected"], case["header"]
    if task == "lineup-consistency":
        rows.sort(key=lambda row:(row[0], row[1]))
    elif task in {"press-then-win","counter-attacks","shot-ending-sequences"}:
        rows.sort(key=lambda row:row[0])
    else:
        # This is serialization of authored rows, not result computation.
        keys = {}
        for e in case["events"]:
            if all(k in e for k in ("timestamp","period","index")) and isinstance(e["index"],int):
                keys[e["id"]] = (e["period"], e["timestamp"], e["index"], e["id"])
        rows.sort(key=lambda row:keys[row[0]])


def mirrored(base):
    case = copy.deepcopy(base)
    case["name"] = "mirrored-identities"
    ids = {id:f"opaque-{len(base['events'])-i:04d}" for i,id in enumerate(sorted({e["id"] for e in base["events"] if isinstance(e,dict) and isinstance(e.get("id"),str)}))}
    teams = {101:701,202:303}
    person = lambda id: 1000-id
    renamed = lambda s: "Renamed, " + s
    for e in case["events"]:
        if isinstance(e,dict) and e.get("id") in ids:
            e["id"] = ids[e["id"]]
            if isinstance(e.get("team"),dict): e["team"]["id"] = teams[e["team"]["id"]]
            if isinstance(e.get("player"),dict):
                e["player"]["id"] = person(e["player"]["id"])
                e["player"]["name"] = renamed(e["player"].get("name",""))
            if isinstance(e.get("recipient"),dict): e["recipient"]["id"] = person(e["recipient"]["id"])
            if "substitution" in e:
                p=e["substitution"]["replacement"]
                if "id" in p: p["id"] = person(p["id"])
                if "name" in p: p["name"] = renamed(p["name"])
            for key in ("location","end_location"):
                p=e.get(key)
                if isinstance(p,list) and len(p)==2 and all(type(v) in (int,float) for v in p):
                    e[key]=[120-p[0],80-p[1]]
            if type(e.get("possession"))==int: e["possession"]=e["possession"]*17+3
    for t in case["match"]["teams"]:
        t["id"]=teams[t["id"]]
        t["name"]=renamed(t["name"])
        t["attack_sign"]={k:-v for k,v in t["attack_sign"].items()}
    if case["lineups"]:
        for t in case["lineups"]:
            t["team_id"]=teams[t["team_id"]]
            for p in t["players"]:
                p["id"]=person(p["id"])
                p["name"]=renamed(p["name"])
    for row in case["expected"]:
        for i,col in enumerate(case["header"]):
            if col in IDS and row[i]: row[i]=ids[row[i]]
            elif col=="event_ids": row[i]=";".join(ids[id] for id in row[i].split(";"))
            elif col=="team_id": row[i]=teams[row[i]]
            elif col=="player_id": row[i]=person(row[i])
            elif col=="possession_id": row[i]=row[i]*17+3
            elif col in {"team","player"}: row[i]=renamed(row[i])
            elif col in {"start_x","end_x","origin_x"}: row[i]=120-row[i]
            elif col in {"end_y","origin_y"}: row[i]=80-row[i]
    random.Random(77).shuffle(case["events"])
    return case


def reconciled(base):
    case=copy.deepcopy(base)
    case["name"]="revision-replay"
    for e in case["events"]: e["revision"]=e.get("revision",0)+10
    # Keep original order for equal revision winners. Every existing scenario's
    # stale versions now rank lower than the selected copies.
    for e in list(case["events"]):
        if "type" not in e: continue
        stale=copy.deepcopy(e)
        stale["revision"]=1
        stale["location"]=[0,0]
        stale["end_location"]=[120,80]
        case["events"].insert(0,stale)
    dead=event("tie-deleted",250000,"Carry",(70,40),(90,40),poss=123,revision=5)
    case["events"] += [dead, {"id":"tie-deleted","revision":5,"deleted":True}]
    malformed=event("bad-clock",260000,"Carry",(70,40),(90,40),poss=124,revision=5)
    malformed["timestamp"]="00:01:60.000"
    case["events"].append(malformed)
    # No fallback to a valid stale version of a malformed winner.
    old=event("bad-winner",270000,"Carry",(70,40),(90,40),poss=125,revision=1)
    invalid=copy.deepcopy(old)
    invalid.update(revision=2,index="not-an-integer")
    case["events"] += [old,invalid]
    return case


def replicated(base, task):
    case=copy.deepcopy(base)
    case["name"]="independent-segments"
    if task=="lineup-consistency":
        # Delete the rejected sub and rogue bench appearance: both never happened.
        case["events"] += [{"id":"h","revision":50,"deleted":True},{"id":"i","revision":50,"deleted":True}]
        case["expected"]=[r for r in case["expected"] if r[1] not in (4,5)]
        return case
    second=copy.deepcopy(base)
    for e in second["events"]:
        e["id"]="copy-"+e["id"]
        if "timestamp" in e:
            h,m,s=e["timestamp"].split(":")
            sec,fraction=s.split(".")
            ms=(int(h)*3600+int(m)*60+int(sec))*1000+int(fraction)
            e["timestamp"]=stamp(ms+400000)
        if "possession" in e: e["possession"]+=500
    for row in second["expected"]:
        for i,col in enumerate(second["header"]):
            if col in IDS and row[i]: row[i]="copy-"+row[i]
            elif col=="event_ids": row[i]=";".join("copy-"+id for id in row[i].split(";"))
            elif col=="possession_id": row[i]+=500
    case["events"] += second["events"]
    case["expected"] += second["expected"]
    random.Random(19).shuffle(case["events"])
    return case


def build():
    reference=(ROOT/"tools/reference.py").read_text()
    common=reference[:reference.index("def forward_passes(")]
    runner=reference[reference.index("def run("):]
    grader=(ROOT/"tools/grader.py").read_text()
    for task,builder in BUILDERS.items():
        directory=ROOT/task
        events,expected,lineups=builder()
        base={"name":"base","header":HEADERS[task].split(","),"events":events,"match":copy.deepcopy(MATCH),"lineups":lineups,"expected":expected}
        random.Random(42).shuffle(base["events"])
        # Keep a deletion winner last if a builder ever supplies equal revisions.
        cases=[base,reconciled(base),mirrored(base),replicated(base,task)]
        empty=copy.deepcopy(base)
        empty.update(name="empty-feed",events=[],expected=[])
        if task=="lineup-consistency":
            for t in lineups:
                for p in t["players"]:
                    if p["starter"]:
                        tn=next(x["name"] for x in MATCH["teams"] if x["id"]==t["team_id"])
                        empty["expected"].append([t["team_id"],p["id"],tn,p["name"],"started_no_events",105])
        cases.append(empty)
        for n,case in enumerate(cases):
            sort_rows(task,case)
            dump(directory/"tests/cases"/f"{n:02d}-{case['name']}.json",case)
        dump(directory/"environment/events.json",base["events"])
        dump(directory/"environment/match.json",base["match"])
        if lineups: dump(directory/"environment/lineups.json",lineups)
        title=task.replace("-"," ").title()
        prompt="# "+title+"\n\n"+COMMON+"\n"+DETAILS[task]
        if lineups:
            prompt=prompt.replace("--match MATCH --output OUTPUT","--match MATCH --lineups LINEUPS --output OUTPUT")
        (directory/"instruction.md").write_text(prompt)
        fname=task.replace("-","_")
        start=reference.index("def "+fname+"(")
        end=reference.find("\ndef ",start+1)
        function=reference[start:end]
        (directory/"solution/solve.py").write_text(common+function+"\n\n"+runner+f"\n\nif __name__ == '__main__':\n    run({task!r})\n")
        (directory/"solution/solve.sh").write_text("#!/bin/bash\nset -euo pipefail\ncp /solution/solve.py /workspace/analyze.py\npython3 /workspace/analyze.py --events /workspace/events.json --match /workspace/match.json "+("--lineups /workspace/lineups.json " if lineups else "")+"--output /workspace/output.csv\n")
        (directory/"tests/test_outputs.py").write_text(grader)
        (directory/"tests/test.sh").write_text("#!/bin/bash\nset -euo pipefail\nmkdir -p /logs/verifier\nprintf '0.0\\n' > /logs/verifier/reward.txt\n# Harness injects /tests only after the agent finishes. Protect it from candidate children.\nif [ \"$(id -u)\" = 0 ]; then\n    chmod -R go-rwx /tests /logs/verifier\n    if [ -d /solution ]; then chmod -R go-rwx /solution; fi\nfi\npython3 -I /tests/test_outputs.py\n")
        docker="FROM python:3.11-slim\nWORKDIR /workspace\nCOPY events.json /workspace/events.json\nCOPY match.json /workspace/match.json\n"
        if lineups: docker+="COPY lineups.json /workspace/lineups.json\n"
        (directory/"environment/Dockerfile").write_text(docker)
        metadata=(directory/"task.toml").read_text()
        metadata=re.sub(r'name = "codimango/[^\"]+"',f'name = "codimango/{task}"',metadata,count=1)
        metadata=re.sub(r'difficulty = "[^\"]+"','difficulty = "hard"',metadata,count=1)
        metadata=re.sub(r'description = "[^\"]+"',f'description = "{title}: reconciled feeds and verified stateful analytics"',metadata,count=1)
        metadata=re.sub(r'timeout = \d+','timeout = 300',metadata,count=1)
        (directory/"task.toml").write_text(metadata)
        (directory/"README.md").write_text(f"# {title}\n\n"+DETAILS[task]+"\n## Author verification\n\n"+
            "The five frozen cases have independently authored expected rows: base, revision replay, mirrored identities/directions, independent segments, and empty feed. The grader compares every field and required row order. It checks submitted sample output and executes the submitted `analyze.py` on all five cases. It never executes the reference solution.\n\n"+
            "Only events and match metadata (plus the roster for lineup consistency) are copied into the agent image. Verifier cases and labels must be injected by the harness after the agent turn. The root Linux verifier executes a snapshot of candidate code as `nobody`, with read-only case inputs and private grader/reward directories. A harness running verification as the agent user does not provide the same process isolation.\n\n"+
            "Difficulty is a design target, not a measured result. No model calibration has been run for this revision. Previous pass-rate claims were removed because the repository contained no supporting trial artifacts. See the root HARDENING.md for local verification commands and results.\n")
        for p in [directory/"solution/solve.sh",directory/"tests/test.sh"]: p.chmod(0o755)
        print(task,len(events),"events",len(expected),"sample rows")


if __name__=="__main__":
    build()
