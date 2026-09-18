"""Validate collected source evidence and fail closed on integrity errors."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .models import SourceStatus


def _records(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def validate_sources(config: dict, root: Path, manifest_path: Path) -> list[SourceStatus]:
    if not manifest_path.exists():
        return [SourceStatus(str(manifest_path), "manifest", "required", "", 0, 0, "", "", ("manifest missing",))]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {item["path"]: item for item in manifest.get("sources", [])}
    statuses: list[SourceStatus] = []
    for relative in config["sources"]:
        entry = entries.get(relative, {})
        path = root / relative
        errors: list[str] = []
        actual_hash = ""
        actual_records = 0
        if not entry:
            errors.append("source absent from manifest")
        if not path.exists():
            errors.append("source file missing")
        else:
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            actual_records = _records(path)
            if entry and actual_hash != entry.get("sha256"):
                errors.append("SHA-256 mismatch")
            if entry and actual_records != entry.get("record_count"):
                errors.append("record count mismatch")
        for field in ("source_system", "query_or_export", "collected_at"):
            if entry and not entry.get(field):
                errors.append(f"missing provenance field: {field}")
        statuses.append(SourceStatus(
            relative, entry.get("source_system", ""), entry.get("query_or_export", ""),
            entry.get("collected_at", ""), entry.get("record_count", 0), actual_records,
            entry.get("sha256", ""), actual_hash, tuple(errors),
        ))
    extra = set(entries) - set(config["sources"])
    if extra:
        statuses.append(SourceStatus("manifest", "manifest", "scope reconciliation", manifest.get("generated_at", ""),
                                     len(config["sources"]), len(entries), "", "", (f"unconfigured manifest sources: {sorted(extra)}",)))
    return statuses
