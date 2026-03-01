# OpenClaw Enterprise Software Factory (Implemented Starter)

This package is an implementation-ready multi-agent factory scaffold for OpenClaw.

## Goals
- Router-led intake and routing
- One lead per project
- Shared specialist pool
- Strict task packets + auditable lifecycle
- Memory isolation: global / project / task
- PR-only delivery with gated merge + deploy

## Quick Start
1. Review `configs/openclaw.factory.single-gateway.json`
2. Adapt paths to your host
3. Validate packets with `python3 scripts/validate_task_packet.py examples/task-packet.alpha.json`
4. Enforce runtime assignment gate: `python3 scripts/assign_task.py examples/task-packet.alpha.json`
5. Run queue/approval monitor: `python3 scripts/monitor_factory.py`
6. Use guarded command gate for risky ops: `scripts/guarded_exec.sh --approval-id <ID> -- "<command>"`
7. Copy AGENTS templates from `templates/`
8. Wire CI from `.github/workflows/pr-checks.yml`
9. Enable local git gate hooks: `git config core.hooksPath .githooks`
10. Apply GitHub branch protection (when token available):
   - `GH_TOKEN=... GH_OWNER=... GH_REPO=... scripts/github_apply_protection.sh`

## Agent Roster (initial)
- router
- lead-project-alpha
- lead-project-beta
- lead-project-gamma
- backend-worker
- frontend-worker
- qa-worker
- devops-worker
- docs-release-writer
- code-reviewer
- security-reviewer
- release-gatekeeper
