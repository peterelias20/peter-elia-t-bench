"""Hand-specified scenarios and expected rows, independent of the oracle.

No reference implementation is imported when generating verifier labels.
"""
import copy
import math

MATCH = {
    "teams": [
        {"id": 101, "name": "Amber, FC", "attack_sign": {"1": 1, "2": -1, "3": -1}},
        {"id": 202, "name": "Cobalt Ω", "attack_sign": {"1": -1, "2": 1, "3": 1}},
    ],
    "periods": [
        {"id": 1, "offset_ms": 0, "duration_ms": 2700000},
        {"id": 2, "offset_ms": 2700000, "duration_ms": 2700000},
        {"id": 3, "offset_ms": 5400000, "duration_ms": 900000},
    ],
}


def stamp(ms):
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"


def event(id, ms, typ="Pass", loc=(60, 40), end=None, *, team=101, period=1,
          poss=1, actor=1, pattern="Open Play", index=0, **extra):
    e = {"id": id, "revision": 0, "period": period, "index": index,
         "timestamp": stamp(ms), "minute": 99, "second": 59, "possession": poss,
         "team": {"id": team, "name": "MISLEADING TEAM"},
         "player": {"id": actor, "name": "Same Name"}, "type": {"name": typ},
         "play_pattern": {"name": pattern}, "location": list(loc) if loc is not None else None}
    if end is not None:
        e["end_location"] = list(end)
    e.update(extra)
    return e


def reception_pair(prefix, ms, a, b, *, team=101, period=1, poss=1, delay=2000, **extra):
    return [event(prefix + "p", ms, loc=a, end=b, team=team, period=period, poss=poss,
                  recipient={"id": 2}, **extra),
            event(prefix + "r", ms + delay, "Ball Receipt", b, team=team, period=period, poss=poss, actor=2)]


def forward():
    evs, rows = [], []
    cases = [
        ("a", (30, 40), (85, 40), 101, 1, 2000, True),
        ("b", (85, 40), (100, 40), 101, 1, 2001, False),
        ("c", (90, 40), (15, 40), 101, 2, 1, True),
        ("d", (80, 40), (18, 40), 202, 1, 1000, True),
        ("e", (90, 40), (95, 80), 101, 1, 1000, False),
        ("f", (40, 40), (40, 20), 101, 1, 1000, False),
        ("g", (80, 40), (102, 40), 202, 2, 1000, True),
        ("h", (40, 40), (80, 40), 101, 1, 0, False),
        ("i", (30, 40), (80, 40), 101, 1, 1000, False),
        ("j", (30, 40), (80, 40), 101, 1, 1000, False),
        ("k", (30, 40), (80, 40), 101, 3, 1000, False),
        ("l", (40, 40), (80, 40), 101, 1, 1000, True),
    ]
    for n, (prefix, a, b, team, period, delay, keep) in enumerate(cases):
        ms = 10000 + n * 10000
        pair = reception_pair(prefix, ms, a, b, team=team, period=period, poss=n + 1, delay=delay)
        if prefix == "i":
            pair[0]["pass_outcome"] = {"name": "Incomplete"}
        if prefix == "j":
            evs.append(event("jblock", ms + 500, "Carry", b, team=202, poss=n + 1))
        if prefix == "l":
            pair[1]["location"] = [82, 40]  # Inclusive reception distance 2.
        evs.extend(pair)
        evs.append(event(prefix + "pressure", ms + 100, "Pressure", poss=n + 1, team=team, period=period))
        if keep:
            sign = next(t for t in MATCH["teams"] if t["id"] == team)["attack_sign"][str(period)]
            x0, x1 = (a[0], b[0]) if sign == 1 else (120 - a[0], 120 - b[0])
            gain = math.hypot(120 - x0, a[1] - 40) - math.hypot(120 - x1, b[1] - 40)
            rows.append([prefix + "p", prefix + "r", team, 1, x1 - x0, gain,
                         sum(x0 < x <= x1 for x in (40, 80, 102)), a[0], b[0], b[1]])
    # Latest revision invalidates a previously qualifying pass.
    evs += reception_pair("rev", 150000, (30, 40), (80, 40), poss=50)
    corrected = copy.deepcopy(evs[-2])
    corrected.update(revision=2, end_location=None)
    evs.append(corrected)
    evs += reception_pair("deleted", 170000, (30, 40), (80, 40), poss=51)
    evs.append({"id": "deletedp", "revision": 3, "deleted": True})
    return evs, rows, None


def carries():
    evs, rows = [], []
    def chain(prefix, ms, coords, *, team=101, period=1, poss=1, gap=1000, keep=False):
        for i, (a, b) in enumerate(coords):
            evs.append(event(prefix + str(i), ms + i * gap, "Carry", a, b, team=team, period=period, poss=poss))
            evs.append(event(prefix + "pressure" + str(i), ms + i * gap + 100, "Pressure", team=team, period=period, poss=poss))
        if keep:
            sign = next(t for t in MATCH["teams"] if t["id"] == team)["attack_sign"][str(period)]
            df = (coords[-1][1][0] - coords[0][0][0]) * sign
            path = sum(math.dist(a, b) for a, b in coords) + sum(math.dist(x[1], y[0]) for x, y in zip(coords, coords[1:]))
            rows.append([prefix + "0", prefix + str(len(coords) - 1), team, 1, len(coords), df, path, df / path])
    chain("a", 10000, [((70,40),(76,40)), ((76,40),(82,40))], keep=True)
    chain("b", 20000, [((40,40),(34,40)), ((34,40),(28,40))], team=101, period=2, poss=2, keep=True)
    chain("c", 30000, [((70,40),(79.9999,40))], poss=3)
    chain("d", 40000, [((70,40),(75,60)), ((75,60),(85,40))], poss=4)
    chain("e", 50000, [((70,40),(80,40))], team=202, period=2, poss=5, keep=True)
    chain("f", 60000, [((69,40),(75,40)), ((76,40),(81,40))], poss=6, keep=True)
    chain("g", 70000, [((70,40),(76,40)), ((76,40),(82,40))], poss=7, gap=1001)
    chain("h", 80000, [((70,40),(76,40)), ((77.001,40),(83,40))], poss=8)
    chain("i", 90000, [((70,40),(76,40)), ((76,40),(82,40))], poss=9)
    evs.append(event("ibreak", 90500, "Pass", poss=9))
    chain("j", 100000, [((40,40),(30,40))], team=202, period=3, poss=10)
    chain("k", 110000, [((70,40),(80,40))], poss=11, keep=True)
    evs.append(event("malformed", 105000, "Carry", (70,40), (80,40), poss=99, revision=2))
    evs[-1]["location"] = [True, 40]
    return evs, rows, None


def switches():
    evs, rows = [], []
    for n, prefix in enumerate("abcdefghij"):
        ms, poss = 10000 + n * 20000, n + 1
        team, period = (101, 2) if prefix == "b" else (101, 1)
        a, b = (60, 10), (70, 70)
        if prefix == "c": a, b = (60, 30), (70, 70)
        if prefix == "d": a, b = (60, 29), (81, 57)  # Exactly 35.
        if prefix == "e": a, b = (60, 29), (81.0001, 57)  # Strictly >35, rounds to 35.
        pair = reception_pair(prefix, ms, a, b, team=team, period=period, poss=poss,
                              delay=3001 if prefix == "f" else 3000,
                              **{"pass": {"length": 0}})
        evs.extend(pair)
        first = event(prefix + "u", ms + 4000, "Carry", b, (75,60), team=team, period=period, poss=poss, actor=2)
        last = event(prefix + "v", ms + (9001 if prefix == "g" else 9000), "Shot", (75,60), team=team, period=period, poss=poss, actor=2)
        if prefix == "h": first["team"]["id"] = 202
        if prefix == "i": first["type"]["name"] = "Shot"
        if prefix == "j": first.update(type={"name":"Pass"}, pass_outcome={"name":"Incomplete"})
        evs += [first, last, event(prefix + "pr", ms + 5000, "Pressure", team=202, period=period, poss=poss)]
        if prefix in "abe":
            rows.append([prefix + "p", prefix + "r", prefix + "v", "right_to_left" if period == 2 else "left_to_right", math.dist(a,b), 3])
    return evs, rows, None


def chains():
    evs = [
        event("a", 10000, loc=(30,40), end=(40,40)),
        event("pressure", 18001, "Pressure", poss=99),
        event("b", 18000, "Carry", (40,40),(35,40), actor=2),
        event("c", 19000, "Shot", (35,40), actor=2),
        event("d", 20000, loc=(35,40), end=(50,40)),
        event("e", 21000, "Carry", (50,40),(55,40), pattern="From Corner"),
        event("f", 22000, "Carry", (55,40),(60,40)),
        event("g", 30001, loc=(60,40),end=(70,40), pass_outcome={"name":"Incomplete"}),
        event("h", 31000, "Carry", (70,40),(75,40)),
        event("break", 32000, "Foul Won"),
        event("i", 33000, "Carry", (75,40),(80,40)),
        event("j", 34000, "Carry", (45,40),(35,40), team=202),
        event("k", 35000, "Carry", (35,40),(30,40), team=202),
        event("l", 1000, "Carry", (40,40),(30,40), period=2),
        event("m", 2000, "Pass", None, (20,40), period=2),
        event("n", 2000, "Shot", (20,40), period=2, index=1),
    ]
    rows = [
        ["a",1,1,101,"Open Play",3,2,"a","c",9,5,1],
        ["d",1,1,101,"Open Play",1,1,"d","d",0,15,0],
        ["e",1,1,101,"From Corner",1,1,"e","e",0,5,0],
        ["f",1,1,101,"Open Play",1,1,"f","f",0,5,0],
        ["g",1,1,101,"Open Play",1,1,"g","g",0,10,0],
        ["h",1,1,101,"Open Play",1,1,"h","h",0,5,0],
        ["i",1,1,101,"Open Play",1,1,"i","i",0,5,0],
        ["j",1,1,202,"Open Play",2,1,"j","k",1,15,0],
        ["l",2,1,101,"Open Play",3,1,"l","n",1,10,1],
    ]
    return evs, rows, None


def presses():
    evs = [
        event("pa",10000,"Pressure",(0,40)),
        event("pb",11000,"Pressure",(15,40)),
        event("wa",12000,"Duel",(7,40),outcome={"name":"Won"}),
        event("wb",13000,"Interception",(0,40),outcome={"name":"Won"}),
        # Cardinality beats chronological greedy: pa->wb, pb->wa.
        event("pc",20000,"Pressure",(50,40),poss=2),
        event("pd",21000,"Pressure",(50,40),poss=2),
        event("wc",22000,"Ball Recovery",(50,40),poss=2),
        # Minimum duration picks pd, leaves pc unmatched.
        event("pe",30000,"Pressure",(50,40),poss=3,index=0),
        event("pf",30000,"Pressure",(50,40),poss=3,index=1),
        event("we",35000,"Ball Recovery",(60,40),poss=3,index=0),
        event("wf",35000,"Duel",(50,40),poss=3,index=1,outcome={"name":"Won"}),
        # Equal objectives require lexical pairing pe->we, pf->wf.
        event("pg",40000,"Pressure",poss=4),
        event("wg",45001,"Ball Recovery",poss=4),
        event("ph",50000,"Pressure",poss=5),
        event("wh",51000,"Duel",poss=5,outcome={"name":"Lost"}),
        event("pi",60000,"Pressure",poss=6),
        event("foul",60500,"Foul Won",poss=6),
        event("wi",61000,"Ball Recovery",poss=6),
        event("pj",70000,"Pressure",poss=7),
        event("pattern",70500,"Pressure",poss=7,pattern="From Corner"),
        event("wj",71000,"Ball Recovery",poss=7),
        event("pk",80000,"Pressure",poss=8),
        event("wk",80000,"Ball Recovery",poss=8,index=1),
        event("pl",90000,"Pressure",poss=9,team=202),
        event("wl",91000,"Ball Recovery",poss=9,team=101),
        event("pm",100000,"Pressure",poss=10),
        event("wm",101000,"Ball Recovery",poss=10,recovery_failure=True),
        event("pn",110000,"Pressure",poss=11),
        event("wn",111000,"Ball Recovery",(70.0001,40),poss=11),
    ]
    rows = [["pa","wb",101,3,0],["pb","wa",101,1,8],["pd","wc",101,1,0],
            ["pe","we",101,5,10],["pf","wf",101,5,0]]
    return evs, rows, None


def shots():
    evs, rows = [], []
    # Cap at five previous events, not five including the shot.
    for i in range(8):
        evs.append(event("a" + str(i),10000+i*1000,"Shot" if i==7 else "Carry",(30+i*5,40),(35+i*5,40),poss=1))
    evs.append(event("pressure",16500,"Pressure",team=202))
    rows.append(["a7","a2",6,"a2;a3;a4;a5;a6;a7",40,40,5,25])
    evs += [event("b0",30000,"Carry",(30,40),(50,40),poss=2),
            event("b1",34000,"Carry",(50,40),(60,40),poss=2),
            event("b2",38001,"Shot",(60,40),poss=2)]
    rows.append(["b2","b2",1,"b2",60,40,0,0])
    evs += [event("c0",40000,"Carry",(30,40),(50,40),poss=3),
            event("c1",41000,"Shot",(50,40),poss=3),event("c2",42000,"Shot",(55,40),poss=3)]
    rows += [["c1","c0",2,"c0;c1",30,40,1,20],["c2","c2",1,"c2",55,40,0,0]]
    evs += [event("d0",50000,"Carry",(30,40),(50,40),poss=4),
            event("d1",51000,"Shot",(50,40),poss=4,pattern="From Corner")]
    rows.append(["d1","d1",1,"d1",50,40,0,0])
    evs += [event("e0",60000,"Carry",(30,40),(50,40),poss=5),
            event("e1",61000,"Carry",(50,40),(60,40),poss=5,team=202),
            event("e2",62000,"Shot",(60,40),poss=5)]
    rows.append(["e2","e2",1,"e2",60,40,0,0])
    # Total 15-second boundary with each retained gap <=4 seconds.
    for i, ms in enumerate([70000,74000,78000,82000,85000]):
        evs.append(event("f"+str(i),ms,"Shot" if i==4 else "Carry",(30+i*5,40),(35+i*5,40),poss=6))
    rows.append(["f4","f0",5,"f0;f1;f2;f3;f4",30,40,15,20])
    for i, ms in enumerate([90000,94000,98000,102000,105001]):
        evs.append(event("g"+str(i),ms,"Shot" if i==4 else "Carry",(30+i*5,40),(35+i*5,40),poss=7))
    rows.append(["g4","g1",4,"g1;g2;g3;g4",35,40,11.001,15])
    evs += [event("h0",1000,"Carry",(80,40),(70,40),poss=8,period=2),
            event("h1",1000,"Shot",(70,40),poss=8,period=2,index=1),
            event("invalidshot",2000,"Shot",None,poss=8,period=2)]
    rows.append(["h1","h0",2,"h0;h1",80,40,0,10])
    return evs, rows, None


def cross_scenarios():
    evs, rows = [], []
    for i, prefix in enumerate("abcdefghij"):
        ms, poss = 10000+i*15000, i+1
        period = 2 if prefix == "b" else 1
        end = (18,62) if period==2 else (102,18)
        flags = {"cross": {}} if prefix not in "cd" else {"cross": None if prefix=="c" else False}
        pair = reception_pair(prefix,ms,(80,10),end,period=period,poss=poss,delay=2501 if prefix=="e" else 2500,**{"pass":flags})
        if prefix == "d": pair[1]["type"]["name"] = "Shot"
        evs += pair
        shot = event(prefix+"s",ms+(8001 if prefix=="f" else 8000),"Shot",end,poss=poss,period=period,actor=2)
        evs.append(shot)
        if prefix=="g": evs.append(event("gblock",ms+4000,"Carry",end,poss=poss,period=period,team=202))
        if prefix=="h": pair[0]["pass_outcome"]={"name":"Incomplete"}
        if prefix=="i": pair[0]["end_location"]=[101.9999,18]
        if prefix=="j": evs.append(event("jbreak",ms+4000,"Ball Out",poss=poss))
        if prefix in "abd":
            rows.append([prefix+"p",prefix+"r",prefix+("r" if prefix=="d" else "s"),101,"direct" if prefix=="d" else "assisted",2.5 if prefix=="d" else 8,end[0],end[1]])
    # Two crosses nominate a single shot: latest wins.
    evs += reception_pair("k",200000,(80,10),(105,40),poss=30,delay=1000,**{"pass":{"cross":0}})
    evs += reception_pair("l",202000,(105,40),(108,40),poss=30,delay=1000,**{"pass":{"cross":False}})
    evs.append(event("sharedshot",208000,"Shot",(108,40),poss=30,actor=2))
    rows.append(["lp","lr","sharedshot",101,"assisted",6,108,40])
    return evs, rows, None


def restarts():
    evs = [
        event("a",10000,**{"pass":{"corner":{},"free_kick":{}}}),
        event("b",11000,"Pressure",team=202),
        event("c",12000,"Carry"),
        event("d",20000,"Shot"),  # age 10 inclusive and third control
        event("e",20001,"Carry"),
        event("f",30000,poss=2,pattern="From Corner",**{"pass":{"corner":None,"free_kick":False}}),
        event("g",31000,"Carry",poss=2),
        event("h",32000,"Carry",poss=2),
        event("i",33000,"Carry",poss=2),  # Fourth control default.
        event("j",40000,poss=3,pattern="From Throw In"),
        event("k",50001,"Carry",poss=3),  # expiry
        event("l",60000,poss=4,**{"pass":{"corner":0}}),
        event("m",61000,"Carry",poss=4,team=202),  # opponent clears
        event("n",62000,"Carry",poss=4),
        event("o",70000,poss=5,**{"pass":{"throw":{}}}),
        event("p",71000,"Foul Won",poss=5,pattern="From Corner"),
        event("q",72000,"Carry",poss=5),
        event("r",80000,"Carry",poss=6,**{"pass":{"corner":{}}}), # only Pass flags count
        event("s",81000,poss=6,pattern="From Kick Off"),
        event("t",82000,poss=6,pass_outcome={"name":"Incomplete"}),
        event("u",83000,"Carry",poss=6),
        event("v",84000,poss=7,**{"pass":{"corner":{}}}),
        event("w",1000,"Carry",poss=7,period=2),
    ]
    default = lambda id: [id,"open_play","default","",0]
    rows = [["a","corner","explicit_pass","a",0],default("b"),["c","corner","inherited","a",2],
            ["d","corner","inherited","a",10],default("e"),["f","free_kick","explicit_pass","f",0],
            ["g","free_kick","inherited","f",1],["h","free_kick","inherited","f",2],default("i"),
            ["j","throw_in","pattern","j",0],default("k"),["l","corner","explicit_pass","l",0],
            default("m"),default("n"),["o","throw_in","explicit_pass","o",0],default("p"),default("q"),default("r"),
            ["s","kick_off","pattern","s",0],["t","kick_off","inherited","s",1],default("u"),
            ["v","corner","explicit_pass","v",0],default("w")]
    return evs, rows, None


def counters():
    evs = [
        event("ra",10000,"Ball Recovery",(30,40)),
        event("rb",11000,"Interception",(60,40),outcome={"name":"Won"}),
        event("sa",12000,"Shot",(80,40)),
        event("sb",13000,"Shot",(50,40)),  # ra->sb, rb->sa preserves cardinality
        event("rc",20000,"Ball Recovery",(30,40),poss=2),
        event("rd",21000,"Ball Recovery",(30,40),poss=2),
        event("sc",22000,"Shot",(50,40),poss=2), # pick latest recovery
        event("re",30000,"Ball Recovery",(30,40),poss=3,index=0),
        event("rf",30000,"Ball Recovery",(30,40),poss=3,index=1),
        event("se",42000,"Shot",(45,40),poss=3,index=0),
        event("sf",42000,"Shot",(45,40),poss=3,index=1),
        event("rg",50000,"Ball Recovery",(30,40),poss=4),
        event("sg",62001,"Shot",(50,40),poss=4),
        event("rh",70000,"Duel",(30,40),poss=5,outcome={"name":"Lost"}),
        event("sh",71000,"Shot",(50,40),poss=5),
        event("ri",80000,"Ball Recovery",(30,40),poss=6),
        event("iblock",80000,"Carry",(40,40),poss=6,team=202,index=1),
        event("si",81000,"Shot",(50,40),poss=6),
        event("rj",90000,"Ball Recovery",(30,40),poss=7),
        event("jbreak",90500,"Pressure",poss=7,pattern="From Corner"),
        event("sj",91000,"Shot",(50,40),poss=7),
        event("rk",100000,"Ball Recovery",(30,40),poss=8),
        event("sk",101000,"Shot",(44.9999,40),poss=8),
        event("rl",1000,"Ball Recovery",(80,40),poss=9,period=2),
        event("sl",13000,"Shot",(65,40),poss=9,period=2),
    ]
    rows = [["ra","sb",101,3,20],["rb","sa",101,1,20],["rd","sc",101,1,20],
            ["re","se",101,12,15],["rf","sf",101,12,15],["rl","sl",101,12,15]]
    return evs, rows, None


def lineups():
    # 105 regulation minutes incl extra period: verifies metadata-based capping.
    roster = [{"team_id":101,"players":[{"id":i,"name":"Twin, Ω" if i in (1,2) else f"Player {i}","starter":i<=3} for i in range(1,7)]},
              {"team_id":202,"players":[{"id":1,"name":"Twin, Ω","starter":True}]}]
    evs = [
        event("a",60000,"Carry",actor=1),event("b",60000,"Carry",actor=1,team=202,index=1),
        event("c",120000,"Carry",actor=2),
        event("d",600000,"Substitution",actor=1,substitution={"replacement":{"id":4,"name":"Wrong"}}),
        event("e",600000,"Carry",actor=1,index=1), # inactive after same-time sub
        event("f",600000,"Carry",actor=4,index=2),
        event("g",1200000,"Substitution",actor=4,substitution={"replacement":{"id":1}}),
        event("h",1800000,"Substitution",actor=4,substitution={"replacement":{"id":5}}), # invalid, no state changes
        event("i",1800001,"Carry",actor=5),
        event("j",2400000,"Red Card",actor=2),
        event("k",2400001,"Carry",actor=2),
        event("l",2800000,"Substitution",actor=1,substitution={"replacement":{"id":6}}), # p1 stoppage clips to45
        event("m",1000,"Carry",actor=6,period=2),
        event("n",600000,"Substitution",actor=6,period=2,substitution={"replacement":{"id":2}}), # dismissed cannot reenter
        event("o",1200000,"Red Card",actor=6,period=2),
        event("p",1200001,"Carry",actor=6,period=2),
        event("q",1500000,"Red Card",actor=6,period=2),
        event("r",1800000,"Carry",actor=99,period=2),
        event("s",1000,"Carry",actor=1,team=202,period=3),
    ]
    rows = [
        [101,1,"Amber, FC","Twin, Ω","inactive_appearance",35],
        [101,2,"Amber, FC","Twin, Ω","inactive_appearance;invalid_substitution",40],
        [101,3,"Amber, FC","Player 3","started_no_events",105],
        [101,4,"Amber, FC","Player 4","invalid_substitution",10],
        [101,5,"Amber, FC","Player 5","inactive_appearance;invalid_substitution",0],
        [101,6,"Amber, FC","Player 6","inactive_appearance;invalid_dismissal;invalid_substitution",20],
        [101,99,"Amber, FC","Same Name","inactive_appearance;unregistered_player",0],
    ]
    return evs, rows, roster


BUILDERS = {"forward-passes":forward,"progressive-carries":carries,"switch-of-play":switches,
            "possession-chains":chains,"press-then-win":presses,"shot-ending-sequences":shots,
            "crosses":cross_scenarios,"set-piece-splitter":restarts,"counter-attacks":counters,
            "lineup-consistency":lineups}
