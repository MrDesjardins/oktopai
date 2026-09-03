# 04 — Build the trajectory verifier

## Objective

Implement an offline verifier for repository-grounded TypeScript trajectories.

## Verification layers

1. Schema and event ordering.
2. Repository path and version consistency.
3. Tool-command allowlist and unsafe-command rejection.
4. Patch application and changed-file checks.
5. Independent strict TypeScript compilation.
6. Focused tests where the fixture provides them.
7. Final-answer claims grounded in captured observations.

## Exit criteria

- Good traces pass replay and verification.
- Fabricated tool results, invalid patches, failed builds, and unsupported
  claims are rejected.
- Rejected traces can be retained as labeled negative or preference examples.
