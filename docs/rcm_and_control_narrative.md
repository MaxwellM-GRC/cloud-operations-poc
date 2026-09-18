# ITGC-OPS-001 control narrative and RCM mapping

| RCM attribute | Definition |
|---|---|
| Control ID | ITGC-OPS-001 |
| Control name | Batch Job and Backup Operations |
| Risk category | `it_operations` |
| Risk | Failure to execute, monitor, resolve, and recover scheduled processing and backups could result in incomplete, inaccurate, unavailable, or untimely financial data. |
| Control description | Management performs daily monitoring of scheduled jobs and backups in scope and periodically validates backup recoverability, investigating failures and retaining resolution and data integrity evidence. |
| Objective | Scheduled jobs and backups in scope complete as required, failures are resolved timely, and backup recoverability is periodically validated. |
| Population | All scheduled jobs and backups in scope, their execution records, failures, and restore tests for the review period. |
| Frequency | Daily for executions; per policy for restore testing. |
| Source checklist | SOX_Computer_Operations_Backup_Job_Scheduling_Checklist.docx |
| Activity | Reconcile expected job and backup schedules to system generated execution logs, incident records, rerun outcomes, and restore test evidence. |
| Nature | Automated detection with human approved response and closure. |

## Rule design

| Rule | Test | Evidence |
|---|---|---|
| OPS-01 | Reconcile every materialized expected occurrence to at least one execution result. | CMDB, schedule snapshot, Kubernetes/Step Functions/AWS Backup event. |
| OPS-02 | For every failed, delayed, or skipped job, require a linked incident, resolution within four hours, and data integrity evidence. | Execution event and incident system. |
| OPS-03 | For every failed backup, require a resolved incident within 24 hours and a successful replacement backup. | AWS Backup job and incident system. |
| OPS-04 | For each protected resource, require a current successful restore test or current failed test with an explicitly approved remediation plan. | Restore job and resilience test registry. |

The detector creates one finding per affected operation and rule. Each finding uses
criteria, condition, cause, and effect fields, evidence references, severity, and
full exception response guidance. Stable finding IDs support case correlation across
runs. Automation never remediates production or approves/ closes its own cases.

## Exception case lifecycle

The monitor retains the evidence package, then opens or updates one GitHub exception
case per finding. An authorized owner reviews the remediation and mitigation or
lookback, records root cause and recurrence, meets the response SLA or documents
escalation, attaches closure evidence, and approves closure. Automation cannot make
the decision to remediate, accept risk, escalate, or close a case.

## Reviewer procedure

1. Confirm `input_valid` and `population_reconciled` are true.
2. Compare the CMDB and expected occurrence counts to independent scope evidence.
3. Inspect source provenance and reperform selected SHA-256 and row count checks.
4. Reperform a sample of passing and exception evaluations.
5. Inspect each case for authorized remediation approval, lookback, root cause,
   closure evidence, escalation, and control owner approval.
