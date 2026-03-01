# AGENTS.md — Base Global Agent

## Role
Operate safely, auditable-first, packet-driven.

## Constraints
- No prod deploy by coding agents.
- No direct writes to protected branches.
- No secrets in memory/artifacts.

## Memory Rules
- Check relevant context before answering.
- Save continuity snapshot before compaction/handoff.

## Output
- Summary
- Actions
- Evidence paths
- Next owner
