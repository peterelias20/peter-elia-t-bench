"""Run the Linux entrypoint/isolation gate with a local Docker engine."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "football-task-check:local"


def main():
    subprocess.run(["docker", "build", "--tag", IMAGE, str(ROOT / "forward-passes/environment")], check=True)
    with tempfile.TemporaryDirectory(prefix="football-container-check-") as directory:
        bundle = Path(directory)
        for task in ROOT.iterdir():
            if (task / "task.toml").exists():
                shutil.copytree(task, bundle / task.name)
        (bundle / "tools").mkdir()
        shutil.copyfile(ROOT / "tools/container_check.py", bundle / "tools/container_check.py")
        shutil.copyfile(ROOT / "README.md", bundle / "README.md")
        created = subprocess.run(["docker", "create", "--network", "none", "--workdir", "/", IMAGE,
                                  "bash", "-c", "chmod -R go-rwx /task; python3 -u /task/tools/container_check.py"],
                                 check=True, capture_output=True, text=True)
        container = created.stdout.strip()
        try:
            # Use container-owned files: Docker Desktop host bind mounts may not
            # enforce host ownership/modes identically to the Linux filesystem.
            subprocess.run(["docker", "cp", str(bundle) + "/.", container + ":/task"], check=True)
            subprocess.run(["docker", "start", "--attach", container], check=True, timeout=180)
            status = subprocess.run(["docker", "inspect", "--format", "{{.State.ExitCode}}", container],
                                    check=True, capture_output=True, text=True)
            if status.stdout.strip() != "0":
                raise SystemExit("Container verification failed with exit " + status.stdout.strip())
        finally:
            subprocess.run(["docker", "rm", "--force", container], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
