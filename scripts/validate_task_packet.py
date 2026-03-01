#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

REQUIRED = [
    'schemaVersion','taskId','projectKey','title','type','priority','riskLevel',
    'lifecycleStage','acceptanceCriteria','constraints','approvalsNeeded',
    'relevantFiles','ownerAgent','nextAgent','audit','rollback'
]

TASK_RE = re.compile(r'^[A-Z]+-[0-9]{8}-[0-9]{3}$')
PROJ_RE = re.compile(r'^[a-z0-9-]{2,32}$')

ALLOWED_TYPE = {'feature','bugfix','refactor','security','infra','docs','release'}
ALLOWED_PRIORITY = {'P0','P1','P2','P3'}
ALLOWED_RISK = {'low','medium','high','critical'}
ALLOWED_STAGE = {'intake','breakdown','assignment','implementation','review','release','done','blocked'}


def die(msg):
    print(f'ERROR: {msg}')
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        die('Usage: validate_task_packet.py <packet.json>')

    p = Path(sys.argv[1])
    if not p.exists():
        die(f'File not found: {p}')

    data = json.loads(p.read_text())

    for k in REQUIRED:
        if k not in data:
            die(f'Missing required field: {k}')

    if data['schemaVersion'] != '1.0.0':
        die('schemaVersion must be 1.0.0')
    if not TASK_RE.match(data['taskId']):
        die('taskId format invalid')
    if not PROJ_RE.match(data['projectKey']):
        die('projectKey format invalid')
    if data['type'] not in ALLOWED_TYPE:
        die('type invalid')
    if data['priority'] not in ALLOWED_PRIORITY:
        die('priority invalid')
    if data['riskLevel'] not in ALLOWED_RISK:
        die('riskLevel invalid')
    if data['lifecycleStage'] not in ALLOWED_STAGE:
        die('lifecycleStage invalid')
    if not isinstance(data['acceptanceCriteria'], list) or not data['acceptanceCriteria']:
        die('acceptanceCriteria must be non-empty array')

    approvals = data['approvalsNeeded']
    for k in ['merge','deploy','securityReview','humanApproval']:
        if k not in approvals or not isinstance(approvals[k], bool):
            die(f'approvalsNeeded.{k} missing or not boolean')

    if data['riskLevel'] in {'high','critical'} and not approvals['securityReview']:
        die('securityReview must be true for high/critical risk')

    if data['riskLevel'] in {'medium','high','critical'} and not approvals['humanApproval']:
        die('humanApproval must be true for medium/high/critical risk')

    print('OK: task packet is valid')


if __name__ == '__main__':
    main()
