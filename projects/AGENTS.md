# AGENTS.md — Shared Worker Workspace Policy

## Scope
Shared specialists may operate under `/projects/*` only for tasks explicitly assigned via task packet.

## Required Inputs
- task packet JSON
- project AGENTS.md
- project ARCHITECTURE.md
- relevant file list from packet

## Constraints
- No edits outside assigned projectKey path.
- No protected-branch writes.
- No production actions.
- Must produce evidence artifacts under `projects/<projectKey>/tasks/<taskId>/`.
