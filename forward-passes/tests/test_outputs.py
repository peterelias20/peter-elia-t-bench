"""Frozen verifier. Injected by the harness after the agent turn.

Never invokes /solution. Expected rows are authored separately from the oracle.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ID_COLUMNS = {"id", "pass_id", "receipt_id", "first_id", "last_id", "chain_id", "start_id", "end_id",
              "retained_until_id", "pressure_id", "win_id", "shot_id", "origin_id", "cross_id", "recovery_id",
              "restart_id", "event_ids"}
INTEGER_COLUMNS = {"team_id", "player_id", "period", "possession_id", "lines_crossed", "carry_count",
                   "event_count", "unique_players", "ends_in_shot", "chain_length"}
TEXT_COLUMNS = ID_COLUMNS | {"team", "player", "play_pattern", "wing_change", "assist_type", "derived_tag", "source", "mismatch_types"}


def compare(path, header, expected):
    with open(path, newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    if not rows or rows[0] != header:
        raise AssertionError(f"header must be {','.join(header)}")
    if len(rows) - 1 != len(expected):
        raise AssertionError(f"expected {len(expected)} rows, got {len(rows)-1}")
    for i, (actual, wanted) in enumerate(zip(rows[1:], expected), 1):
        if len(actual) != len(header):
            raise AssertionError(f"row {i}: incorrect field count")
        for column, value, target in zip(header, actual, wanted):
            if column in TEXT_COLUMNS:
                if value != str(target):
                    raise AssertionError(f"row {i}, {column}: expected {target!r}, got {value!r}")
            elif column in INTEGER_COLUMNS:
                # Do not accept decimal or exponential serialization of integer IDs/counts.
                if value != str(int(target)):
                    raise AssertionError(f"row {i}, {column}: expected integer {target!r}, got {value!r}")
            else:
                number = float(value)
                if not math.isfinite(number) or abs(number - float(target)) > 1e-6:
                    raise AssertionError(f"row {i}, {column}: expected {target!r}, got {value!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/workspace")
    parser.add_argument("--reward", default="/logs/verifier/reward.txt")
    args = parser.parse_args()
    workspace = Path(args.workspace)
    root = Path(__file__).resolve().parent
    cases = [json.loads(p.read_text()) for p in sorted((root / "cases").glob("*.json"))]
    failures = []
    passed = 0
    try:
        base = next(c for c in cases if c["name"] == "base")
        compare(workspace / "output.csv", base["header"], base["expected"])
        passed += 1
        print("PASS sample output")
    except Exception as error:
        failures.append(f"sample output: {error}")
    try:
        # Snapshot code before running it. Inputs, expected labels, and reward paths
        # are never taken from agent-authored code or agent-writable input files.
        script = (workspace / "analyze.py").read_bytes()
    except OSError as error:
        failures.append(f"analyze.py missing: {error}")
        script = None
    for case in cases:
        if script is None:
            continue
        try:
            with tempfile.TemporaryDirectory(prefix="task-verifier-") as directory:
                work = Path(directory)
                work.chmod(0o755)
                (work / "analyze.py").write_bytes(script)
                (work / "analyze.py").chmod(0o444)
                for key in ("events", "match", "lineups"):
                    if case.get(key) is not None:
                        p = work / (key + ".json")
                        p.write_text(json.dumps(case[key], ensure_ascii=False), encoding="utf-8")
                        p.chmod(0o444)
                out = work / "result"
                out.mkdir()
                output = out / "output.csv"
                command = [sys.executable, "-I", "-B", str(work / "analyze.py"),
                           "--events", str(work / "events.json"), "--match", str(work / "match.json"), "--output", str(output)]
                if case.get("lineups") is not None:
                    command += ["--lineups", str(work / "lineups.json")]
                demote = None
                if sys.platform.startswith("linux") and os.geteuid() == 0:
                    import pwd
                    nobody = pwd.getpwnam("nobody")
                    os.chown(out, nobody.pw_uid, nobody.pw_gid)
                    def demote():
                        os.setgroups([])
                        os.setgid(nobody.pw_gid)
                        os.setuid(nobody.pw_uid)
                result = subprocess.run(command, cwd=out, env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(out)},
                                        capture_output=True, text=True, timeout=20, preexec_fn=demote)
                if result.returncode:
                    raise AssertionError(f"program exited {result.returncode}: {result.stderr[-1200:]}")
                if output.is_symlink() or output.stat().st_size > 1000000:
                    raise AssertionError("output must be a regular CSV smaller than 1 MB")
                # Root evaluator snapshots before parsing. Candidate processes have
                # no access to the private grader mount or verifier logs.
                snapshot = work / "snapshot.csv"
                shutil.copyfile(output, snapshot)
                compare(snapshot, case["header"], case["expected"])
                passed += 1
                print(f"PASS {case['name']}")
        except Exception as error:
            failures.append(f"{case['name']}: {error}")
    total = len(cases) + 1
    for failure in failures:
        print("FAIL " + failure)
    print(f"Passed {passed}/{total} checks")
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text("1.0\n" if passed == total and not failures else "0.0\n")
    return 0 if passed == total and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
