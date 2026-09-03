# 05 — Create the trajectory corpus

## Objective

Generate a high-quality teacher corpus that teaches repair behavior, not only
final code.

## Curriculum

1. Inspect-only and diagnosis-only tasks.
2. Inspect → patch tasks.
3. Patch → compile/test tasks.
4. Failed-command recovery and retry tasks.
5. Multi-file repository repairs.

Each accepted record must preserve the task, repository facts, ordered tool
events, observations, patch, verification evidence, provenance, and split.

## Exit criteria

- Initial family-balanced corpus exists.
- Every accepted final repair passes an independent verifier.
- Held-out repositories and task templates are separated from training data.

## v2 completion note

The v2 CPU preflight corpus is complete at
`.oktopai/datasets/typescript-trajectories-v2.jsonl`: 100 records across five
families, split 80/20 train/validation. Its SFT conversion and manifest are
`typescript-trajectories-v2-sft.jsonl` and
`typescript-trajectories-v2-sft.manifest.json`. Independent replay passed
100/100. Training remains a separate decision gate.
