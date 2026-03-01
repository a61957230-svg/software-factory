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
4. Copy AGENTS templates from `templates/`
5. Wire CI from `ci/github/workflows/pr-checks.yml`

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
