#!/usr/bin/env bash
set -euo pipefail
BRANCH='research/early-wallet-watchlist'
[[ "${GITHUB_REF_NAME:-}" == "$BRANCH" ]] || { echo 'Ref guard failed'; exit 1; }
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
mkdir -p watchlist/data
publish() {
  git add -- watchlist/data
  if ! git diff --cached --quiet; then
    git commit -m 'watchlist: observation checkpoint' >/dev/null
  fi
  for attempt in 1 2 3; do
    if git pull --rebase --quiet origin "$BRANCH" && git push --quiet origin "HEAD:$BRANCH"; then
      return 0
    fi
    git rebase --abort 2>/dev/null || true
    sleep $((attempt * 3))
  done
  echo 'Checkpoint publication failed; data remains in this job checkout.'
  return 1
}
END=$(( $(date +%s) + 4500 ))
LAST_PUBLISH=0
REASON='window_finished'
while (( $(date +%s) < END )); do
  START=$(date +%s)
  git fetch --quiet origin "$BRANCH"
  git show FETCH_HEAD:watchlist/control.json > /tmp/early-watch-control.json
  if ! python3 -c 'import json,sys; c=json.load(open("/tmp/early-watch-control.json")); sys.exit(0 if c.get("enabled") is True and c.get("mode")=="WATCH_ONLY" else 1)'; then
    REASON='stopped_by_control'
    break
  fi
  python3 watchlist/collector.py --once
  NOW=$(date +%s)
  if (( NOW - LAST_PUBLISH >= 300 )); then
    publish
    LAST_PUBLISH=$NOW
  fi
  WAIT=$(( 60 - ($(date +%s) - START) ))
  if (( WAIT > 0 )); then sleep "$WAIT"; fi
done
export END_REASON="$REASON"
python3 - <<'PY'
import json, os
from pathlib import Path
from datetime import datetime, timezone
p=Path('watchlist/data/runtime.json')
p.write_text(json.dumps({'ended_at':datetime.now(timezone.utc).isoformat(),
  'reason':os.environ['END_REASON'], 'run_id':os.environ.get('GITHUB_RUN_ID'),
  'note':'A queued replacement may continue collection; check the latest workflow run.'},indent=2)+'\n')
PY
publish
