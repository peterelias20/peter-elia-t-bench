"""Local package gate: reference solvability and rejection of output shortcuts.

Uses only local Python; no Codimango compute, model calls, or remote writes.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def run(command):
    return subprocess.run(command, capture_output=True, text=True, timeout=120)


def verify(task):
    config = tomllib.loads((task / "task.toml").read_text())
    assert config["task"]["name"] == "codimango/" + task.name
    assert not any(c.isdigit() for c in task.name)
    assert config["task"]["difficulty"] == "hard"
    for script in (task / "solution/solve.py", task / "tests/test_outputs.py"):
        compile(script.read_text(), str(script), "exec")
    base = json.loads((task / "tests/cases/00-base.json").read_text())
    with tempfile.TemporaryDirectory(prefix="task-local-check-") as directory:
        work = Path(directory)
        for path in (task / "environment").glob("*.json"):
            shutil.copyfile(path, work / path.name)
        shutil.copyfile(task / "solution/solve.py", work / "analyze.py")
        command = [sys.executable, str(work / "analyze.py"), "--events", str(work / "events.json"),
                   "--match", str(work / "match.json"), "--output", str(work / "output.csv")]
        if (work / "lineups.json").exists():
            command += ["--lineups", str(work / "lineups.json")]
        reference = run(command)
        assert reference.returncode == 0, reference.stderr
        verifier = [sys.executable, str(task / "tests/test_outputs.py"), "--workspace", str(work),
                    "--reward", str(work / "reward.txt")]
        result = run(verifier)
        assert result.returncode == 0 and (work / "reward.txt").read_text().strip() == "1.0", result.stdout + result.stderr
        # Correct preexisting output cannot rescue a submitted program that does
        # no work. This detects the former verifier-runs-reference defect.
        (work / "analyze.py").write_text("# Does not produce any output.\n")
        result = run(verifier)
        assert result.returncode != 0 and (work / "reward.txt").read_text().strip() == "0.0", "no-op accepted"
        # Replaying the visible answer must fail despite a perfect sample CSV.
        script = ("import argparse,csv\np=argparse.ArgumentParser()\n"
                  "p.add_argument('--events');p.add_argument('--match');p.add_argument('--lineups');p.add_argument('--output')\n"
                  "a=p.parse_args()\n"
                  f"rows={([base['header']]+base['expected'])!r}\n"
                  "with open(a.output,'w',newline='') as f:csv.writer(f).writerows(rows)\n")
        (work / "analyze.py").write_text(script)
        result = run(verifier)
        assert result.returncode != 0 and (work / "reward.txt").read_text().strip() == "0.0", "hardcoded answer accepted"
    print(f"PASS {task.name}: reference 6/6; no-op rejected; hardcoded sample rejected")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks", nargs="*")
    args = parser.parse_args()
    tasks = [ROOT / name for name in args.tasks] if args.tasks else sorted(p for p in ROOT.iterdir() if (p / "task.toml").exists())
    for task in tasks:
        verify(task)
    print(f"Verified {len(tasks)} tasks, {len(tasks)*6} reference checks and {len(tasks)*2} shortcut rejections.")


if __name__ == "__main__":
    main()
