"""Evaluate the complete ITGC-OPS-001 population."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from .models import Finding


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _finding(config: dict, rule_id: str, operation: dict, condition: str,
             cause: str, effect: str, evidence_refs: list[str]) -> Finding:
    guidance = config["response_guidance"][rule_id]
    identity = "|".join((rule_id, operation["operation_id"], condition, *sorted(evidence_refs)))
    finding_id = f"{rule_id}-{hashlib.sha256(identity.encode()).hexdigest()[:10].upper()}"
    return Finding(
        finding_id, config["control"]["id"], rule_id, config["rules"][rule_id]["severity"],
        operation["operation_id"], operation["operation_type"], operation["platform"],
        condition, config["rules"][rule_id]["assertion"], cause, effect,
        tuple(evidence_refs), guidance["remediation"], guidance["mitigation"],
        guidance["root_cause"], guidance["closure_evidence"], guidance["escalation"],
    )


def evaluate(config: dict, data: dict[str, list[dict[str, str]]]) -> tuple[list[Finding], list[dict]]:
    findings: list[Finding] = []
    evaluations: list[dict] = []
    inventory = {row["operation_id"]: row for row in data["inventory"]}
    incidents = {row["incident_id"]: row for row in data["incidents"]}
    executions = data["jobs"] + data["backups"]
    by_expectation: dict[str, list[dict]] = {}
    for row in executions:
        by_expectation.setdefault(row["expectation_id"], []).append(row)

    for expected in data["expected"]:
        operation = inventory[expected["operation_id"]]
        matched = by_expectation.get(expected["expectation_id"], [])
        refs = [expected["source_schedule_ref"]] + [row["source_event_ref"] for row in matched]
        assertions = {"OPS-01": bool(matched)}
        if not matched:
            findings.append(_finding(config, "OPS-01", operation,
                f"Expected execution {expected['expectation_id']} has no recorded result.",
                "The expected schedule did not reconcile to Kubernetes, orchestration, or AWS Backup execution evidence.",
                "Required financial processing or protection may be incomplete, inaccurate, unavailable, or untimely.", refs))

        if operation["operation_type"] == "job" and matched:
            exception_runs = [row for row in matched if row["status"] in {"failed", "delayed", "skipped"}]
            job_ok = True
            detail: list[str] = []
            for run in exception_runs:
                incident = incidents.get(run["incident_id"])
                if not incident:
                    job_ok = False
                    detail.append(f"{run['execution_id']} has no incident")
                    continue
                refs.append(incident["source_event_ref"])
                deadline = _time(run["completed_at"]) + timedelta(hours=config["parameters"]["job_resolution_sla_hours"])
                if not incident["resolved_at"] or _time(incident["resolved_at"]) > deadline:
                    job_ok = False
                    detail.append(f"{run['execution_id']} was not resolved within the {config['parameters']['job_resolution_sla_hours']}-hour SLA")
                if not incident["data_integrity_evidence"]:
                    job_ok = False
                    detail.append(f"{run['execution_id']} lacks data integrity evidence")
            assertions["OPS-02"] = job_ok
            if not job_ok:
                findings.append(_finding(config, "OPS-02", operation, "; ".join(detail) + ".",
                    "Failure response evidence is late or incomplete.",
                    "Downstream financial data may be incomplete or inaccurate without a documented reconciliation.", refs))

        if operation["operation_type"] == "backup" and matched:
            failed = [row for row in matched if row["status"] == "failed"]
            backup_ok = True
            detail: list[str] = []
            for run in failed:
                incident = incidents.get(run["incident_id"])
                replacement = [row for row in matched if row.get("replacement_for") == run["execution_id"] and row["status"] == "completed"]
                if incident:
                    refs.append(incident["source_event_ref"])
                if not incident or incident["status"] != "resolved" or not incident["resolved_at"]:
                    backup_ok = False
                    detail.append(f"{run['execution_id']} lacks a resolved incident")
                elif _time(incident["resolved_at"]) > _time(run["completed_at"]) + timedelta(hours=config["parameters"]["backup_resolution_sla_hours"]):
                    backup_ok = False
                    detail.append(f"{run['execution_id']} exceeded the backup resolution SLA")
                if not replacement:
                    backup_ok = False
                    detail.append(f"{run['execution_id']} has no successful replacement backup")
            assertions["OPS-03"] = backup_ok
            if not backup_ok:
                findings.append(_finding(config, "OPS-03", operation, "; ".join(detail) + ".",
                    "Backup failure response did not demonstrate both resolution and a successful replacement recovery point.",
                    "The protected financial data may not have a usable recovery point.", refs))

        evaluations.append({
            "expectation_id": expected["expectation_id"], "operation_id": operation["operation_id"],
            "operation_type": operation["operation_type"], "scheduled_at": expected["scheduled_at"],
            "execution_ids": [row["execution_id"] for row in matched], "assertions": assertions,
            "result": "pass" if all(assertions.values()) else "exception", "evidence_refs": sorted(set(refs)),
        })

    as_of = _time(config["review_window"]["as_of"])
    tests_by_operation: dict[str, list[dict]] = {}
    for test in data["restore_tests"]:
        tests_by_operation.setdefault(test["operation_id"], []).append(test)
    for operation in inventory.values():
        if operation["operation_type"] != "backup":
            continue
        tests = tests_by_operation.get(operation["operation_id"], [])
        latest = max(tests, key=lambda row: _time(row["tested_at"])) if tests else None
        due_after = timedelta(days=int(operation["restore_test_frequency_days"]))
        current = bool(latest and as_of - _time(latest["tested_at"]) <= due_after)
        passed = bool(latest and latest["status"] == "passed" and latest["recovery_point_verified"].lower() == "true")
        approved_plan = bool(latest and latest["remediation_id"] and latest["remediation_approved"].lower() == "true" and latest["approved_by"])
        restore_ok = current and (passed or approved_plan)
        if not restore_ok:
            condition = "No restore test evidence exists."
            refs: list[str] = []
            if latest:
                reasons = []
                if not current:
                    reasons.append(f"latest test is older than {operation['restore_test_frequency_days']} days")
                if not passed and not approved_plan:
                    reasons.append("test failed without approved remediation")
                condition = f"Restore test {latest['restore_test_id']} is noncompliant: " + "; ".join(reasons) + "."
                refs = [latest["source_event_ref"]]
            findings.append(_finding(config, "OPS-04", operation, condition,
                "Recoverability testing is overdue or failed without an approved remediation plan.",
                "Backup recoverability and recovery objectives cannot be relied upon for financial systems.", refs))
        evaluations.append({
            "restore_test_for": operation["operation_id"], "restore_test_id": latest["restore_test_id"] if latest else "",
            "assertions": {"OPS-04": restore_ok}, "result": "pass" if restore_ok else "exception",
            "evidence_refs": [latest["source_event_ref"]] if latest else [],
        })
    return findings, evaluations
