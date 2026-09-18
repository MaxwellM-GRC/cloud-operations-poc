# Batch Job and Backup Operations — Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cloud-operations-poc/actions/workflows/ci.yml/badge.svg)

Automated detection reconciles expected cloud batch schedules, Kubernetes CronJob and AWS Step Functions execution records, AWS Backup jobs, incident records, and restore test evidence.

> All names, people, organizations, systems, accounts, and records in this repository are fictional. No employer, client, or production data is included.

## The problem it catches

A recorded job execution alone does not demonstrate that every required process ran, that a failure was resolved on time, or that affected financial data was reconciled. Similarly, a completed backup does not prove that a failed backup received a replacement recovery point or that a restore remains possible.

The fictional fixture includes a missing settlement export, a late revenue rollup resolution without data integrity evidence, an unresolved ledger backup, a failed ledger restore test without approved remediation, and an overdue application state restore test. Each becomes a separate exception case for human review.

## What this control tests

| Control ID | Control description | Severity |
|---|---|---|
| OPS-01 | Each expected job and backup has a recorded execution result. | High |
| OPS-02 | Failed, delayed, or skipped jobs have timely incident, resolution, and data integrity evidence. | High |
| OPS-03 | Backup failures are resolved and successful backup completion is evidenced. | High |
| OPS-04 | Required restore tests occur within policy frequency and pass or have approved remediation. | High |

## How it works

```text
CMDB + expected schedules ───┐
Kubernetes / Step Functions ├─► source provenance gate ─► full population review
AWS Backup + incidents ──────┤                                  │
Restore test registry ───────┘                                  ▼
                                               rule results + exception cases
```

1. The source provenance gate checks required sources, record counts, SHA-256 fingerprints, and collection metadata. The review fails closed if a source is missing, changed, unrecorded, or incomplete.
2. The control reconciles every materialized expected execution to Kubernetes, AWS orchestration, or AWS Backup evidence.
3. It evaluates job failure response, backup replacement and resolution, and recoverability testing for the complete operation population.
4. It writes RCM ready evidence and one exception case for every detected condition.

Automation may detect, route, and recommend. A human approved decision is required before a production change, risk acceptance, or exception closure.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.main
```

Use `--fail-on-findings` in a monitor to return exit code `2` when exceptions exist. Invalid evidence returns exit code `3`.

## Sample output

```text
BATCH JOB AND BACKUP OPERATIONS CONTROL
Input provenance valid: True
Population reconciled: True
Expected executions evaluated: 8
Restore test populations evaluated: 3
Findings: 5
[HIGH] OPS-01 k8s-settlement-export: Expected execution EXP-JOB-002 has no recorded result.
[HIGH] OPS-02 aws-revenue-rollup: SFN-RUN-2003 was not resolved within the 4-hour SLA; SFN-RUN-2003 lacks data integrity evidence.
[HIGH] OPS-03 aws-s3-ledger: BKP-RUN-3003 lacks a resolved incident; BKP-RUN-3003 has no successful replacement backup.
```

The generated evidence package is:

```text
output/
  control_evidence.json   Source provenance, population results, evaluations, and findings
  exceptions.csv          RCM ready exception register
  cases/OPS-*.md          One human owned exception case per finding
```

## Continuous monitoring

GitHub Actions runs the test suite and a sample review on every push and pull request. The Operations Control Monitor runs every weekday, on demand, and after changes to the control inputs. It retains the evidence package for 90 days, then opens or updates one GitHub exception case for each finding before signaling a failure when findings exist.

The fixture intentionally contains exceptions, so a red monitor result is expected until the fictional conditions are resolved. The monitor never closes a case automatically. A control owner must approve the response, complete mitigation and follow up work, document root cause, attach closure evidence, address escalation, and approve closure. Job response uses a four hour SLA; backup response uses a 24 hour SLA. Immediate escalation applies to financial processing failure, data loss risk, or unavailable recoverability.

## Production design and limitations

This POC uses static fictional extracts. A production collector would read evidence from AWS Backup, CloudWatch, EventBridge, Step Functions, Kubernetes APIs and audit logs, the incident platform, and the resilience test registry. It should use least privilege identities that can collect evidence but cannot modify the workloads being observed.

Production operation also requires independent completeness reconciliation across cloud accounts, clusters, applications, and financial processes; durable evidence retention; schedule expansion for timezones, dependencies, retries, holidays, and late arrivals; and isolated restore testing that validates recovery objectives.

### Human decision boundary

Automation is limited to read only evidence collection, detection, case routing, and recommendations. The control owner or an authorized delegate must make and record the decision to rerun a workload, change a scheduler or backup policy, initiate a restore, accept risk, escalate, or close an exception case. Automation must never make those decisions or execute those production actions.

## Control mapping

| RCM attribute | Definition |
|---|---|
| Control ID | ITGC-OPS-001 |
| Control name | Batch Job and Backup Operations |
| Framework context | SOX ITGC operations; Cloud Native ITGC Automation portfolio |
| Risk category | `it_operations` |
| Risk | Failure to execute, monitor, resolve, and recover scheduled processing and backups could result in incomplete, inaccurate, unavailable, or untimely financial data. |
| Control description | Management performs daily monitoring of scheduled jobs and backups in scope and periodically validates backup recoverability, investigating failures and retaining resolution and data integrity evidence. |
| Objective | Scheduled jobs and backups in scope complete as required, failures are resolved timely, and backup recoverability is periodically validated. |
| Frequency | Daily for executions; per policy for restore testing. |
| Population | All scheduled jobs and backups in scope, their execution records, failures, and restore tests for the review period. |
| Activity | Reconcile expected job and backup schedules to system generated execution logs, incident records, rerun outcomes, and restore test evidence. |
| Evidence contract | [Source provenance and evidence contract](docs/evidence_contract.md) |

The detailed control narrative, reviewer procedure, and RCM rule mapping are in [docs/rcm_and_control_narrative.md](docs/rcm_and_control_narrative.md). The production considerations are in [docs/production_design.md](docs/production_design.md).

## Repository layout

```text
config.yaml                 Control definition, rules, response guidance, and source scope
data/                       Fictional schedule, cloud execution, backup, incident, and restore evidence
data/source_manifest.json   Source provenance, record counts, and SHA-256 fingerprints
src/                        Validation, evaluation, and RCM ready reporting
tests/                      Rule, integrity, population, and output tests
docs/                       Control narrative, evidence contract, and production design
.github/workflows/          CI and scheduled control monitoring
```

MIT — see [LICENSE](LICENSE).
