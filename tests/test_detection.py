from copy import deepcopy
from pathlib import Path

import yaml

from src.detection import evaluate
from src.loaders import load_sources


ROOT = Path(__file__).resolve().parents[1]


def subject():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    data = load_sources(ROOT)
    return config, data, evaluate(config, data)


def test_fixture_produces_expected_rule_population():
    _, _, (findings, _) = subject()
    assert [(f.rule_id, f.operation_id) for f in findings] == [
        ("OPS-01", "k8s-settlement-export"),
        ("OPS-02", "aws-revenue-rollup"),
        ("OPS-03", "aws-s3-ledger"),
        ("OPS-04", "aws-s3-ledger"),
        ("OPS-04", "k8s-app-state"),
    ]


def test_successful_and_supported_executions_pass():
    _, _, (_, evaluations) = subject()
    by_id = {row.get("expectation_id"): row for row in evaluations}
    assert by_id["EXP-JOB-001"]["result"] == "pass"
    assert by_id["EXP-JOB-004"]["result"] == "pass"
    assert by_id["EXP-BKP-002"]["result"] == "pass"


def test_missing_execution_is_a_separate_ops_01_case():
    _, _, (findings, _) = subject()
    item = next(f for f in findings if f.rule_id == "OPS-01")
    assert item.operation_id == "k8s-settlement-export"
    assert "no recorded result" in item.condition


def test_late_resolution_and_missing_reconciliation_trigger_ops_02():
    _, _, (findings, _) = subject()
    item = next(f for f in findings if f.rule_id == "OPS-02")
    assert "4-hour SLA" in item.condition
    assert "data integrity evidence" in item.condition


def test_successful_replacement_clears_backup_failure():
    _, _, (findings, _) = subject()
    assert not any(f.rule_id == "OPS-03" and f.operation_id == "aws-rds-finance" for f in findings)


def test_approved_restore_remediation_can_satisfy_failed_test():
    config, data, _ = subject()
    changed = deepcopy(data)
    test = next(row for row in changed["restore_tests"] if row["operation_id"] == "aws-s3-ledger")
    test["remediation_approved"] = "true"
    test["approved_by"] = "Resilience Risk Owner"
    findings, _ = evaluate(config, changed)
    assert not any(f.rule_id == "OPS-04" and f.operation_id == "aws-s3-ledger" for f in findings)


def test_finding_ids_are_stable():
    _, _, (first, _) = subject()
    _, _, (second, _) = subject()
    assert [f.finding_id for f in first] == [f.finding_id for f in second]
