# Multi-Gateway Split Policy

## Keep Single Gateway if all true
- Same trust boundary
- Same compliance zone
- Same ownership and approval flow

## Split Gateway when any true
- Client data isolation needed
- Regulatory boundary differs
- Separate prod control ownership
- High volume (>20 active projects)

## Suggested Layout
- gateway-core-internal
- gateway-client-a
- gateway-client-b
- optional gateway-release-control
