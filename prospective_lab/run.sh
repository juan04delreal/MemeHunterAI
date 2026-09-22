#!/usr/bin/env bash
set -euo pipefail
BRANCH='research/prospective-quote-lab'
[[ "${GITHUB_REF_NAME:-}" == "$BRANCH" ]] || exit 1
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
publish() {
  git add prospective_lab/data
  if ! git diff --cached --quiet; then git commit -m 'prospective lab: observation checkpoint' >/dev/null; fi
  git pull --rebase --quiet origin "$BRANCH" || { git rebase --abort 2>/dev/null || true; return 1; }
  git push --quiet origin "HEAD:$BRANCH" || return 1
}
END=$(( $(date +%s) + 4500 ))
LAST=0
while (( $(date +%s) < END )); do
  START=$(date +%s)
  git fetch --quiet origin "$BRANCH"
  git show FETCH_HEAD:prospective_lab/control.json > /tmp/prospective-control.json
  python3 -c 'import json,sys; c=json.load(open("/tmp/prospective-control.json")); sys.exit(0 if c.get("enabled") is True and c.get("mode")=="WATCH_ONLY" else 1)' || break
  python3 prospective_lab/lab.py
  NOW=$(date +%s)
  if (( NOW-LAST >= 300 )); then publish || true; LAST=$NOW; fi
  WAIT=$(( 15 - ($(date +%s)-START) )); if (( WAIT>0 )); then sleep "$WAIT"; fi
done
publish || true
