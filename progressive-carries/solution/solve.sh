#!/bin/bash
set -euo pipefail
cp /solution/solve.py /workspace/analyze.py
python3 /workspace/analyze.py --events /workspace/events.json --match /workspace/match.json --output /workspace/output.csv
