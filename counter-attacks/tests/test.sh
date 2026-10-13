#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
printf '0.0\n' > /logs/verifier/reward.txt
# Harness injects /tests only after the agent finishes. Protect it from candidate children.
if [ "$(id -u)" = 0 ]; then
    chmod -R go-rwx /tests /logs/verifier
    if [ -d /solution ]; then chmod -R go-rwx /solution; fi
fi
python3 -I /tests/test_outputs.py
