# Security Controls

## Mandatory
- No coding agent deploy to prod
- No coding agent direct main writes
- Human approval for destructive/prod actions
- Secrets only via env/vault
- Separate project memory and workspace

## Host Hardening
- Dedicated service user
- Firewall restrict egress
- Patch cadence weekly + emergency patch SLA
- Immutable audit logs retention
