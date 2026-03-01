# RISKS.md

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| Cross-project memory bleed | High | Separate project MEMORY.md + per-agent store | Lead + Security Reviewer |
| Unauthorized deploy | Critical | Gatekeeper + human approval + env protection | Gatekeeper |
| Secret leakage | Critical | Vault/env only, scanners, no secrets in memory | Security Reviewer |
