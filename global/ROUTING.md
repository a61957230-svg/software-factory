# ROUTING.md

## Router Dispatch Rules
- Intake -> task packet validation -> assign lead by projectKey
- Lead can assign specialists based on task type
- Review stage requires reviewer agents only
- Release stage requires release-gatekeeper + human approval

## Default Specialist Mapping
- feature/backend -> backend-worker
- feature/frontend -> frontend-worker
- testing -> qa-worker
- infra -> devops-worker
- docs/release -> docs-release-writer
- security -> security-reviewer
