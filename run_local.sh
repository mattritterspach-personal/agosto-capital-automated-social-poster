#!/usr/bin/env bash
# Local runner: loads .env and runs the poster. Usage:
#   ./run_local.sh --test --dry-run     (safe: prints what would be sent)
#   ./run_local.sh --test               (real test post = post1 to all platforms)
#   ./run_local.sh --due                (post whatever is scheduled for today)
set -euo pipefail
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; source .env; set +a; fi
python3 -m pip install -q -r requirements.txt
python3 post.py "$@"
