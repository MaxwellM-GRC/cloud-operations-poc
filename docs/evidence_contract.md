# Evidence contract

The control does not treat an absent source as a clean result. Before applying any
rule, it validates the source manifest against the configured source list, record
counts, and SHA-256 fingerprints. Missing files, changed files, unrecorded sources,
or missing provenance fields stop evaluation with exit code `3`.

Each source manifest entry records:

- the fictional source system and exact query/export description;
- collection time, record count, relative file path, and SHA-256 fingerprint; and
- the scope relationship expressed by `config.yaml`.

The generated `control_evidence.json` preserves the run ID, review period, control
language, source checks, population counts, every expectation and restore test
evaluation, and every finding. `exceptions.csv` is the RCM ready register. Each
Markdown file under `output/cases/` is an individual, human owned response record.

Production collectors should use provider API request IDs, account/cluster and
region identifiers, export object versions, and immutable evidence storage. They
should separately prove that the schedule registry and CMDB contain every financial
operation in scope; successful API collection alone does not prove scope coverage.
