# Approval Artifacts

This folder stores explicit human/security approvals used by hard runtime gates.

## 1) Task assignment approval (`<TASK_ID>.json`)
Used by `scripts/assign_task.py` for high/critical tasks.

```json
{
  "taskId": "ALPHA-20260301-001",
  "securityReviewApproved": true,
  "humanApproved": true,
  "approvedBy": "adarsh",
  "approvedAt": "2026-03-01T09:15:00Z"
}
```

## 2) Guarded exec approval (`<APPROVAL_ID>.json`)
Used by `scripts/guarded_exec.sh`.

```json
{
  "approvalId": "APPROVAL-20260301-001",
  "riskLevel": "high",
  "humanApproved": true,
  "approvedBy": "adarsh",
  "expiresAt": "2026-03-01T12:00:00Z",
  "commandSha256": "<optional command sha256>"
}
```

If `commandSha256` is provided, command text must match exactly.
