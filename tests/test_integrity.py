import json
from pathlib import Path

import yaml

from src.integrity import validate_sources


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_validates_every_required_source():
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    statuses = validate_sources(config, ROOT, ROOT / "data/source_manifest.json")
    assert len(statuses) == len(config["sources"])
    assert all(item.ok for item in statuses)


def test_missing_manifest_fails_closed(tmp_path):
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    statuses = validate_sources(config, ROOT, tmp_path / "missing.json")
    assert not statuses[0].ok
    assert "manifest missing" in statuses[0].errors


def test_unconfigured_manifest_source_fails_scope_reconciliation(tmp_path):
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
    manifest["sources"].append({
        "path": "data/unapproved.csv", "source_system": "x", "query_or_export": "x",
        "collected_at": "2026-09-08T00:00:00Z", "record_count": 0, "sha256": "x",
    })
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    statuses = validate_sources(config, ROOT, path)
    assert statuses[-1].path == "manifest"
    assert not statuses[-1].ok
