# Cloud Operations — ITGC Proof of Concept

![CI](https://github.com/MaxwellM-GRC/cloud-operations-poc/actions/workflows/ci.yml/badge.svg)

**Full population monitoring for scheduled cloud processing, backups, failure
resolution, and tested recoverability.**

This standalone POC implements `ITGC-OPS-001` from the Cloud Native ITGC Automation
portfolio. It reconciles expected executions to fictional Kubernetes CronJob, AWS
Step Functions/CloudWatch, and AWS Backup records; evaluates incident response; and
checks whether protected resources have current, successful restore tests.

> **Sanitized:** every organization, person, account, resource, job, incident, and
> source location is fictional. No employer, client, or production data is present.

## What it detects

| Rule | Automated assertion | Severity |
|---|---|---|
| OPS-01 | Each expected job and backup has a recorded execution result. | High |
| OPS-02 | Failed, delayed, or skipped jobs have timely incident, resolution, and data integrity evidence. | High |
| OPS-03 | Backup failures are resolved and successful backup completion is evidenced. | High |
| OPS-04 | Required restore tests are current and pass or have approved remediation. | High |

The fixture intentionally produces five individual findings across four scenarios:
a missing settlement export, a late and unsupported revenue rollup resolution, an
unresolved ledger backup, a failed ledger restore test, and an overdue Kubernetes
application state restore test.

## How it works

```text
CMDB + expected schedules ───┐
Kubernetes / Step Functions ├─► provenance checks ─► population reconciliation
AWS Backup + incidents ──────┤                              │
Restore test registry ───────┘                              ▼
                                            rule results + individual cases
```

The review fails closed if a required source is missing, changed, incomplete, or
lacks provenance. It records the source query, collection time, record count, and
fingerprint, then emits RCM ready findings with criteria, condition, cause, effect,
source references, and human approved response guidance.

## Quick start

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m src.main
```

Generated evidence is written to:

```text
output/
  control_evidence.json   Run, source, population, evaluation, and finding detail
  exceptions.csv          RCM ready exception register
  cases/OPS-*.md          One human owned response case per finding
```

Exit code `0` means the review executed successfully. `--fail-on-findings` returns
`2` when exceptions exist. Invalid evidence returns `3`, so a source failure cannot
look like a clean control result.

## Continuous monitoring and response boundary

GitHub Actions runs tests and a sample review on each change. A weekday monitor also
runs on demand and after changes to control inputs. It always uploads the complete
evidence package, then turns red when exceptions exist. This is expected for the
seeded sample.

Automation may detect, route, and recommend; it cannot mutate production, approve a
risk decision, or close a case. Every generated case requires an authorized human to
approve remediation, complete mitigation and root cause work, attach closure
evidence, address escalation, and approve closure.

## Repository map

```text
config.yaml                 Control, rules, and response guidance aligned to the portfolio
data/                       Fictional cloud, schedule, incident, and restore evidence
data/source_manifest.json   Query provenance, row counts, and file fingerprints
src/                        Validation that fails closed, evaluation, and reporting
tests/                      Rule, integrity, population, and output tests
docs/                       Evidence contract, RCM narrative, production design
.github/workflows/          CI and scheduled control monitoring
```

See [the control narrative](docs/rcm_and_control_narrative.md),
[evidence contract](docs/evidence_contract.md), and
[production design](docs/production_design.md) for implementation detail.

MIT — see [LICENSE](LICENSE).
