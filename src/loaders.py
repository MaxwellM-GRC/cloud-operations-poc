"""Load normalized fictional cloud evidence."""

from __future__ import annotations

import csv
from pathlib import Path


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_sources(root: Path) -> dict[str, list[dict[str, str]]]:
    jobs = _read(root / "data/kubernetes/cronjob_executions.csv") + _read(root / "data/aws/orchestrator_executions.csv")
    return {
        "inventory": _read(root / "data/governance/in_scope_operations.csv"),
        "expected": _read(root / "data/governance/expected_executions.csv"),
        "jobs": jobs,
        "backups": _read(root / "data/aws/backup_jobs.csv"),
        "incidents": _read(root / "data/governance/incidents.csv"),
        "restore_tests": _read(root / "data/governance/restore_tests.csv"),
    }
