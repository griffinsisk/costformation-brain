# Capability-based query strategy

Choose information sources by the evidence they can provide, not by vendor name.

| Capability | Use it for |
| --- | --- |
| `cloud_inventory`, `resource_metadata` | Accounts, subscriptions, projects, resources, tags, labels, and naming patterns |
| `metrics`, `usage_volume`, `observability` | Utilization, request volume, telemetry, and allocation-driver evidence |
| `business_context`, `documentation`, `meeting_context` | Customer goals, terminology, ownership statements, decisions, and constraints |
| `crm` | Account-level business context and confirmed stakeholder information |

CloudZero is authoritative for current CloudZero-visible accounts, dimensions, billing metadata, and cost coverage. Cross-reference it with the local CostFormation file and independent read-only capabilities.

Independent read-only queries may run in parallel. Distill useful findings into the evidence schema with source links, timestamps, confidence, and promotion status; do not retain raw responses or transcripts. If sources conflict, preserve the conflict and prefer the most direct authoritative source only after recording why.

Never invoke a write operation, publish CostFormation, or change an external system without explicit customer approval.
