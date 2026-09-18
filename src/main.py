"""Run the cloud native ITGC-OPS-001 proof of concept."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from .detection import evaluate
from .integrity import validate_sources
from .loaders import load_sources
from .models import ReviewResult
from .reporting import print_summary, write_cases, write_evidence, write_exceptions


ROOT = Path(__file__).resolve().parents[1]


def run(config_path: Path, manifest_path: Path) -> tuple[ReviewResult, dict]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    statuses = validate_sources(config, ROOT, manifest_path)
    run_material = {"config": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    "sources": [(item.path, item.actual_sha256) for item in statuses]}
    run_id = "RUN-" + hashlib.sha256(json.dumps(run_material, sort_keys=True).encode()).hexdigest()[:16]
    if not statuses or not all(item.ok for item in statuses):
        return ReviewResult(run_id, [], [], statuses, {"expected_executions": 0, "expectations_evaluated": 0}), config
    data = load_sources(ROOT)
    findings, evaluations = evaluate(config, data)
    inventory = data["inventory"]
    population = {
        "in_scope_operations": len(inventory),
        "scheduled_jobs": sum(row["operation_type"] == "job" for row in inventory),
        "backup_resources": sum(row["operation_type"] == "backup" for row in inventory),
        "expected_executions": len(data["expected"]),
        "expectations_evaluated": sum("expectation_id" in row for row in evaluations),
        "recorded_execution_rows": len(data["jobs"]) + len(data["backups"]),
        "incidents": len(data["incidents"]),
        "restore_tests": len(data["restore_tests"]),
        "restore_targets_evaluated": sum("restore_test_for" in row for row in evaluations),
    }
    return ReviewResult(run_id, findings, evaluations, statuses, population), config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/source_manifest.json")
    parser.add_argument("--evidence-json", type=Path, default=ROOT / "output/control_evidence.json")
    parser.add_argument("--exceptions-csv", type=Path, default=ROOT / "output/exceptions.csv")
    parser.add_argument("--cases-dir", type=Path, default=ROOT / "output/cases")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)
    result, config = run(args.config, args.manifest)
    write_evidence(result, config, args.evidence_json)
    write_exceptions(result, args.exceptions_csv)
    if result.input_valid:
        write_cases(result, config, args.cases_dir)
    print_summary(result)
    if not result.input_valid:
        for source in result.source_status:
            if not source.ok:
                print(f"INVALID SOURCE {source.path}: {', '.join(source.errors)}")
        return 3
    if args.fail_on_findings and result.findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
