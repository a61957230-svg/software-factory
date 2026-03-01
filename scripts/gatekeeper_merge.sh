#!/usr/bin/env bash
set -euo pipefail

# Merge helper: enforces local gates before merging into protected branch.
# Usage: scripts/gatekeeper_merge.sh <source-branch> [target-branch]

SRC="${1:-}"
DST="${2:-main}"
if [[ -z "$SRC" ]]; then
  echo "Usage: $0 <source-branch> [target-branch]"
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CURRENT=$(git branch --show-current)
if [[ "$CURRENT" != "$DST" ]]; then
  echo "Switching to $DST"
  git checkout "$DST"
fi

echo "Running pre-merge gate checks..."
./scripts/pr_gate_local.sh

# Require explicit gatekeeper identity marker
if [[ "${GATEKEEPER_APPROVED:-}" != "1" ]]; then
  echo "DENY: set GATEKEEPER_APPROVED=1 to confirm human gatekeeper approval"
  exit 2
fi

git merge --no-ff "$SRC" -m "merge($SRC->$DST): gatekeeper-approved"
echo "Merge complete"
