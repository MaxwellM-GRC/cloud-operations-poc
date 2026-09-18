# Production design

This repository uses static, fictional extracts to make the control inspectable.
A production implementation would collect read only evidence from AWS Backup,
CloudWatch Logs/EventBridge/Step Functions, Kubernetes APIs and audit logs, the
incident platform, and the resilience test registry. Collection identities should
be independently managed, least privileged, monitored, and unable to change the
workloads they observe.

The key design boundary is between detection and response. The detector may create
or update a case and recommend a reversible action. An accountable human must
approve any rerun, scheduler change, backup policy change, restore, risk acceptance,
or closure. High risk production actions should use the organization's change and
privileged access controls.

Important production additions include:

- durable event ingestion and immutable evidence retention aligned to policy;
- schedule expansion with timezone, holiday calendar, retry, dependency, and late
  arrival handling;
- independent scope reconciliation to cloud accounts, clusters, applications, and
  financial process inventories;
- deduplicated incident routing, response SLA measurement, and escalation;
- recovery point and recovery time objective testing, restored data validation,
  destructive test isolation, and approved runbooks; and
- operational metrics for source freshness, collector failure, unmatched events,
  case aging, repeated failures, and restore test coverage.

The sample never calls a cloud API or mutates a resource. All provider identifiers,
people, accounts, incidents, and business systems are fictional.
