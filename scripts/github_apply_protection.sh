#!/usr/bin/env bash
set -euo pipefail

# Apply branch protection/ruleset via GitHub REST API.
# Requires: GH_TOKEN, GH_OWNER, GH_REPO

: "${GH_TOKEN:?Set GH_TOKEN}"
: "${GH_OWNER:?Set GH_OWNER}"
: "${GH_REPO:?Set GH_REPO}"

RULESET_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.github/branch-protection.ruleset.json"

if [[ ! -f "$RULESET_FILE" ]]; then
  echo "Ruleset file not found: $RULESET_FILE"
  exit 1
fi

# Detect default branch
DEFAULT_BRANCH=$(curl -sS -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GH_OWNER/$GH_REPO" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("default_branch","main"))')

echo "Default branch: $DEFAULT_BRANCH"

PAYLOAD=$(python3 - "$RULESET_FILE" "$DEFAULT_BRANCH" <<'PY'
import json,sys
f=sys.argv[1]
def_branch=sys.argv[2]
d=json.load(open(f))
d["conditions"]["ref_name"]["include"]= [def_branch]
print(json.dumps(d))
PY
)

# Try create ruleset
RESP=$(curl -sS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "$PAYLOAD" \
  "https://api.github.com/repos/$GH_OWNER/$GH_REPO/rulesets")

if echo "$RESP" | grep -q '"id"'; then
  echo "Ruleset created successfully"
  echo "$RESP" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("rulesetId=",d.get("id"))'
  exit 0
fi

echo "Ruleset create response:"
echo "$RESP"

# Fallback: classic branch protection API
curl -sS -X PUT \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GH_OWNER/$GH_REPO/branches/$DEFAULT_BRANCH/protection" \
  -d '{
    "required_status_checks": {"strict": true, "checks": [{"context":"validate"}]},
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": true,
      "required_approving_review_count": 2,
      "require_last_push_approval": true
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_linear_history": true
  }' | python3 -m json.tool

echo "Fallback branch protection applied (classic API)."
