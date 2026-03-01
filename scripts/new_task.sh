#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <PROJECT_KEY> <TASK_ID> <TITLE> <OWNER_AGENT>"
  exit 1
fi

PROJECT_KEY="$1"
TASK_ID="$2"
TITLE="$3"
OWNER_AGENT="$4"

TASK_DIR="projects/${PROJECT_KEY}/tasks/${TASK_ID}"
mkdir -p "$TASK_DIR/artifacts" "$TASK_DIR"

cat > "$TASK_DIR/plan.md" <<EOF
# Plan for ${TASK_ID}

## Title
${TITLE}

## Owner
${OWNER_AGENT}

## Breakdown
- [ ] Define approach
- [ ] Implement
- [ ] Test
- [ ] Review
- [ ] Release
EOF

echo "Created task workspace: $TASK_DIR"
