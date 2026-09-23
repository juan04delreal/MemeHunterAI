#!/usr/bin/env bash
set -euo pipefail
BRANCH='research/prospective-quote-lab'
[[ "${GITHUB_REF_NAME:-}" == "$BRANCH" ]] || exit 1
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
publish() {
  git add -- prospective_lab/data
  if ! git diff --cached --quiet; then
    git commit -m 'prospective lab: read-only observation checkpoint' >/dev/null
  fi
  for ATTEMPT in 1 2 3; do
    git pull --rebase --quiet origin "$BRANCH" || {
      git rebase --abort 2>/dev/null || true
      echo 'PUBLISH_FAILED: rebase conflict; no force push or data reset' >&2
      return 1
    }
    if git push --quiet origin "HEAD:$BRANCH"; then return 0; fi
    sleep 2
  done
  echo 'PUBLISH_FAILED: push failed after three attempts' >&2
  return 1
}
END=$(( $(date +%s) + 4500 ))
LAST=0
TESTED=''
while (( $(date +%s) < END )); do
  git fetch --quiet origin "$BRANCH"
  git show FETCH_HEAD:prospective_lab/control.json > /tmp/prospective-control.json
  python3 -c 'import json,sys; c=json.load(open("/tmp/prospective-control.json")); sys.exit(0 if c.get("enabled") is True and c.get("mode")=="WATCH_ONLY" else 1)' || break
  CURRENT=$(find prospective_lab -maxdepth 1 -name '*.py' -print0 | sort -z | xargs -0 sha256sum)
  if [[ "$CURRENT" != "$TESTED" ]]; then
    python3 -m unittest discover -s prospective_lab -p 'test_*.py' -v
    TESTED="$CURRENT"
  fi
  PROSPECTIVE_CONTROL_PATH=/tmp/prospective-control.json python3 prospective_lab/collector.py
  PROSPECTIVE_CONTROL_PATH=/tmp/prospective-control.json python3 prospective_lab/confirmation_pilot.py || echo 'CONFIRMATION_PILOT_PROCESS_ERROR: original collector preserved' >&2
  NOW=$(date +%s)
  if (( NOW-LAST >= 60 )); then publish; LAST=$NOW; fi
done
publish
