"""Run inside a root Linux container with private packages copied to /task.

Exercises the actual solve.sh and test.sh entrypoints and verifies candidate
children cannot read labels/reference code or write verifier rewards.
"""
from pathlib import Path
import os
import shutil
import subprocess


def main():
    os.chdir("/")
    tasks = sorted(p for p in Path("/task").iterdir() if (p / "task.toml").exists())
    for task in tasks:
        for path in ("/workspace", "/solution", "/tests", "/logs/verifier"):
            directory = Path(path)
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True)
        for p in (task / "environment").glob("*.json"):
            shutil.copyfile(p, Path("/workspace") / p.name)
        shutil.copytree(task / "solution", "/solution", dirs_exist_ok=True)
        shutil.copytree(task / "tests", "/tests", dirs_exist_ok=True)
        result = subprocess.run(["bash", "/solution/solve.sh"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        # The sample is produced during the root oracle turn. Probe protections
        # only in candidate re-executions during verification.
        analyze = Path("/workspace/analyze.py")
        probe = """from pathlib import Path
for protected in ('/tests/cases/00-base.json', '/solution/solve.py', '/task/README.md'):
    try:
        Path(protected).read_text()
    except PermissionError:
        pass
    else:
        raise AssertionError('candidate could read private file: ' + protected)
try:
    Path('/logs/verifier/reward.txt').write_text('1.0')
except PermissionError:
    pass
else:
    raise AssertionError('candidate could write verifier reward')
"""
        analyze.write_text(probe + analyze.read_text())
        result = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True)
        assert result.returncode == 0, task.name + "\n" + result.stdout + result.stderr
        assert Path("/logs/verifier/reward.txt").read_text().strip() == "1.0"
        print(f"PASS {task.name}: entrypoints 6/6; private labels, solution, packages and reward protected", flush=True)
    print(f"Linux container verified {len(tasks)} packages.", flush=True)


if __name__ == "__main__":
    main()
