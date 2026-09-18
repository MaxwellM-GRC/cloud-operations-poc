import csv
import json
from pathlib import Path

from src.main import run
from src.reporting import write_cases, write_evidence, write_exceptions


ROOT = Path(__file__).resolve().parents[1]


def result_and_config():
    return run(ROOT / "config.yaml", ROOT / "data/source_manifest.json")


def test_population_is_reconciled_and_inputs_are_valid():
    result, _ = result_and_config()
    assert result.input_valid
    assert result.population_reconciled
    assert result.population["expected_executions"] == 8
    assert result.population["restore_targets_evaluated"] == 3


def test_evidence_contains_rcm_and_provenance_fields(tmp_path):
    result, config = result_and_config()
    path = tmp_path / "evidence.json"
    write_evidence(result, config, path)
    payload = json.loads(path.read_text())
    assert payload["control"]["risk"].startswith("Failure to")
    assert payload["control"]["description"].startswith("Management performs")
    assert payload["control"]["control_description"].startswith("Management performs")
    assert payload["control"]["source_checklist"] == "SOX_Computer_Operations_Backup_Job_Scheduling_Checklist.docx"
    assert payload["control"]["activity"]
    assert payload["source_provenance"][0]["actual_sha256"]
    assert {"criteria", "condition", "cause", "effect"} <= payload["findings"][0].keys()


def test_exception_register_and_cases_are_one_per_finding(tmp_path):
    result, config = result_and_config()
    csv_path = tmp_path / "exceptions.csv"
    cases = tmp_path / "cases"
    write_exceptions(result, csv_path)
    write_cases(result, config, cases)
    with csv_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(result.findings) == len(list(cases.glob("*.md")))
    assert all(row["status"] == "Open - human decision required" for row in rows)
    assert "Automation may detect" in next(cases.glob("*.md")).read_text()
