"""Write RCM ready evidence, exception registers, and human owned cases."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .models import ReviewResult


EXCEPTION_COLUMNS = [
    "run_id", "finding_id", "control_id", "rule_id", "severity", "operation_id",
    "operation_type", "platform", "criteria", "condition", "cause", "effect",
    "evidence_refs", "remediation", "mitigation", "root_cause_guidance",
    "closure_evidence", "escalation", "status", "human_approver", "closure_date",
]


def build_payload(result: ReviewResult, config: dict) -> dict:
    return {
        "schema_version": "1.0", "run_id": result.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "control": config["control"], "review_window": config["review_window"],
        "input_valid": result.input_valid, "population_reconciled": result.population_reconciled,
        "population": result.population,
        "source_provenance": [item.as_dict() for item in result.source_status],
        "counts_by_severity": dict(sorted(Counter(f.severity for f in result.findings).items())),
        "evaluations": result.evaluations, "findings": [item.as_dict() for item in result.findings],
    }


def write_evidence(result: ReviewResult, config: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_payload(result, config), indent=2) + "\n", encoding="utf-8")


def write_exceptions(result: ReviewResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXCEPTION_COLUMNS)
        writer.writeheader()
        for finding in result.findings:
            row = finding.as_dict()
            row["evidence_refs"] = " | ".join(row["evidence_refs"])
            writer.writerow({"run_id": result.run_id, **row, "status": "Open - human decision required", "human_approver": "", "closure_date": ""})


def write_cases(result: ReviewResult, config: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for finding in result.findings:
        text = f"""# Operations exception {finding.finding_id}

- **Run ID:** `{result.run_id}`
- **Control / rule:** `{finding.control_id}` / `{finding.rule_id}`
- **Severity:** {finding.severity}
- **Operation:** `{finding.operation_id}` ({finding.platform})
- **Status:** Open — human decision required

## RCM finding

- **Criteria:** {finding.criteria}
- **Condition:** {finding.condition}
- **Cause:** {finding.cause}
- **Effect:** {finding.effect}
- **Evidence references:** {", ".join(finding.evidence_refs) or "None available"}

## Human approved response

- [ ] Authorized owner approves the response before production action: {finding.remediation}
- [ ] Mitigation/lookback completed: {finding.mitigation}
- [ ] Root cause documented: {finding.root_cause_guidance}
- [ ] Closure evidence attached: {finding.closure_evidence}
- [ ] Escalation requirement addressed: {finding.escalation}
- [ ] `{config['control']['owner']}` approves closure and records the closure date.

Automation may detect, route, and recommend. It must not mutate production,
approve its own recommendation, accept risk, or close this case.
"""
        (directory / f"{finding.finding_id}.md").write_text(text, encoding="utf-8")


def print_summary(result: ReviewResult) -> None:
    print("BATCH JOB AND BACKUP OPERATIONS CONTROL")
    print(f"Run ID: {result.run_id}")
    print(f"Input provenance valid: {result.input_valid}")
    print(f"Population reconciled: {result.population_reconciled}")
    print(f"Expected executions evaluated: {result.population.get('expectations_evaluated', 0)}")
    print(f"Restore test populations evaluated: {result.population.get('restore_targets_evaluated', 0)}")
    print(f"Findings: {len(result.findings)}")
    for finding in result.findings:
        print(f"[{finding.severity.upper()}] {finding.rule_id} {finding.operation_id}: {finding.condition}")
