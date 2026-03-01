# AGENTS.md — Global Software Factory Policy

## Role
Operate with explicit artifacts, approval gates, and auditability first.

## Mandatory Read Order (each run)
1. SOUL.md
2. USER.md
3. POLICY.md
4. ROUTING.md (router/lead only)
5. Relevant project packet + docs
6. memory/YYYY-MM-DD.md (today + yesterday)
7. MEMORY.md (only in trusted main contexts)

## Global Rules
- No coding agent may deploy to production.
- No coding agent may write directly to protected branches.
- No secrets in MEMORY.md, task packets, or logs.
- Use structured task packets for all non-trivial work.
- Before compaction/handoff: save continuity snapshot (current task, key decisions, next step).

## Handoff Standard
Always include: taskId, stage, ownerAgent, nextAgent, evidence paths, blockers.
