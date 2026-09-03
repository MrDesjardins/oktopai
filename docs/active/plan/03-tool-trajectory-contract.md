# 03 — Define the tool-trajectory contract

## Objective

Turn the existing tool-use design into a versioned, machine-checkable data
contract.

## Required event types

- `inspect`: read/search/list repository facts.
- `diagnose`: run compiler, lint, or tests and capture exact results.
- `edit`: apply a bounded patch with changed paths.
- `observe`: record tool output, exit code, and relevant diagnostics.
- `retry`: explain the correction after a failed observation.
- `final`: summarize the verified change and remaining risks.

## CPU-only work

- Define JSON Schema or equivalent validation rules.
- Define allowed tools and safe argument shapes.
- Define replay requirements for files, patches, commands, and results.
- Define rejection reasons for fabricated observations or unsupported claims.

## Exit criteria

- A trajectory can be validated without a model.
- A rejected trajectory has a specific, reproducible failure reason.
