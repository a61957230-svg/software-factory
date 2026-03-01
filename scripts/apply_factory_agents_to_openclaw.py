#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

CONFIG = Path('/data/openclaw/.openclaw/openclaw.json')
BACKUP_DIR = Path('/data/openclaw/.openclaw/workspace/software-factory/configs/backups')
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

factory_agents = [
    {
        "id": "router",
        "name": "Factory Router",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/global",
        "agentDir": "/data/openclaw/.openclaw/agents/router/agent",
        "model": {"primary": "github-copilot/gpt-4o"},
        "subagents": {
            "allowAgents": [
                "lead-project-alpha",
                "lead-project-beta",
                "lead-project-gamma",
                "backend-worker",
                "frontend-worker",
                "qa-worker",
                "devops-worker",
                "docs-release-writer",
                "code-reviewer",
                "security-reviewer",
                "release-gatekeeper"
            ]
        }
    },
    {
        "id": "lead-project-alpha",
        "name": "Lead Project Alpha",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects/alpha",
        "agentDir": "/data/openclaw/.openclaw/agents/lead-project-alpha/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "lead-project-beta",
        "name": "Lead Project Beta",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects/beta",
        "agentDir": "/data/openclaw/.openclaw/agents/lead-project-beta/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "lead-project-gamma",
        "name": "Lead Project Gamma",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects/gamma",
        "agentDir": "/data/openclaw/.openclaw/agents/lead-project-gamma/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "backend-worker",
        "name": "Backend Worker",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects",
        "agentDir": "/data/openclaw/.openclaw/agents/backend-worker/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "frontend-worker",
        "name": "Frontend Worker",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects",
        "agentDir": "/data/openclaw/.openclaw/agents/frontend-worker/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "qa-worker",
        "name": "QA Worker",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects",
        "agentDir": "/data/openclaw/.openclaw/agents/qa-worker/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "devops-worker",
        "name": "DevOps Worker",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects",
        "agentDir": "/data/openclaw/.openclaw/agents/devops-worker/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "docs-release-writer",
        "name": "Docs & Release Writer",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/projects",
        "agentDir": "/data/openclaw/.openclaw/agents/docs-release-writer/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/global",
        "agentDir": "/data/openclaw/.openclaw/agents/code-reviewer/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "security-reviewer",
        "name": "Security Reviewer",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/global",
        "agentDir": "/data/openclaw/.openclaw/agents/security-reviewer/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    },
    {
        "id": "release-gatekeeper",
        "name": "Release Gatekeeper",
        "workspace": "/data/openclaw/.openclaw/workspace/software-factory/global",
        "agentDir": "/data/openclaw/.openclaw/agents/release-gatekeeper/agent",
        "model": {"primary": "github-copilot/gpt-4o"}
    }
]


def main():
    if not CONFIG.exists():
        raise SystemExit(f'Config not found: {CONFIG}')

    data = json.loads(CONFIG.read_text())

    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    backup = BACKUP_DIR / f'openclaw.json.backup.{ts}'
    backup.write_text(json.dumps(data, indent=2))

    data.setdefault('agents', {}).setdefault('list', [])
    existing = {a.get('id'): a for a in data['agents']['list'] if isinstance(a, dict) and a.get('id')}

    for agent in factory_agents:
        existing[agent['id']] = agent

    # Preserve original order + append new deterministically
    merged = []
    seen = set()
    for a in data['agents']['list']:
        aid = a.get('id') if isinstance(a, dict) else None
        if aid and aid in existing and aid not in seen:
            merged.append(existing[aid])
            seen.add(aid)
    for aid in sorted(existing.keys()):
        if aid not in seen:
            merged.append(existing[aid])
            seen.add(aid)

    data['agents']['list'] = merged

    # extend main allowAgents
    main_agent = None
    for a in data['agents']['list']:
        if a.get('id') == 'main':
            main_agent = a
            break
    if main_agent:
        allow = main_agent.setdefault('subagents', {}).setdefault('allowAgents', [])
        for aid in [x['id'] for x in factory_agents]:
            if aid not in allow:
                allow.append(aid)

    CONFIG.write_text(json.dumps(data, indent=2))

    # create agent dirs
    for agent in factory_agents:
        Path(agent['agentDir']).mkdir(parents=True, exist_ok=True)

    print('Patched openclaw.json with factory agents.')
    print(f'Backup written: {backup}')
    print('Restart required: openclaw gateway restart')


if __name__ == '__main__':
    main()
