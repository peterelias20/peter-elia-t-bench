#!/bin/bash
set -e
cd /workspace
bash /solution/solve.sh
python3 -m pytest /tests/test_outputs.py -v
