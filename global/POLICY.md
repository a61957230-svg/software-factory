# POLICY.md

## Mandatory Controls
1. No direct prod deploy by coding agents
2. No direct main-branch write by coding agents
3. Human approval required for destructive/prod actions
4. Security review mandatory for medium/high risk tasks
5. Separate trust boundaries across gateways

## Model Tiering
- Cheap: routine coding/docs/tests/routing
- Mid: lead planning, review, security triage
- Strong: complex architecture/debugging (manual escalation)
