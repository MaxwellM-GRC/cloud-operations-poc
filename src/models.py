"""Typed records shared by the control pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceStatus:
    path: str
    source_system: str
    query_or_export: str
    collected_at: str
    expected_records: int
    actual_records: int
    expected_sha256: str
    actual_sha256: str
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {**asdict(self), "ok": self.ok, "errors": list(self.errors)}


@dataclass(frozen=True)
class Finding:
    finding_id: str
    control_id: str
    rule_id: str
    severity: str
    operation_id: str
    operation_type: str
    platform: str
    condition: str
    criteria: str
    cause: str
    effect: str
    evidence_refs: tuple[str, ...]
    remediation: str
    mitigation: str
    root_cause_guidance: str
    closure_evidence: str
    escalation: str
    response_sla: str
    recurrence: str

    def as_dict(self) -> dict:
        return {**asdict(self), "evidence_refs": list(self.evidence_refs)}


@dataclass(frozen=True)
class ReviewResult:
    run_id: str
    findings: list[Finding]
    evaluations: list[dict]
    source_status: list[SourceStatus]
    population: dict[str, int]

    @property
    def input_valid(self) -> bool:
        return bool(self.source_status) and all(item.ok for item in self.source_status)

    @property
    def population_reconciled(self) -> bool:
        return self.input_valid and self.population.get("expected_executions", 0) == self.population.get("expectations_evaluated", -1)
