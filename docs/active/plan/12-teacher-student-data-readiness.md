# 12 — Teacher/student data readiness and probe

Status: probe complete; full fixed-suite decision pending

## Evidence

- The Qwen3-Coder 30B teacher corpus has 2,450 records, with 17 identical
  duplicate rows removed in a derived copy.
- The gated external corpus has 1,908 records, zero exact overlap with the
  teacher corpus, but fails the source-concentration review at 71.17%.
- A deterministic family-capped external probe contains 585 records and passes
  the identity and source-balance gates.
- The merged teacher-plus-balanced probe contains 3,018 unique records and
  completed an isolated 200-step CUDA run.

## Decision

The probe is retained as directional evidence, not as a promoted student. Its
two-task benchmark showed one partial score improvement and one tie, with no
fully verified TypeScript task. The fixed 200-task comparison remains required
before selecting a new recipe.

## Next actions

1. Recover or regenerate task/check metadata for the fixed 200-task suite.
2. Evaluate base, prior student, and probe adapter on exactly the same tasks.
3. Compare per-family executable correctness, output length, and latency.
4. Run a small recipe matrix only if the probe improves executable quality.
5. Keep all candidate adapters held until the promotion thresholds are met.
