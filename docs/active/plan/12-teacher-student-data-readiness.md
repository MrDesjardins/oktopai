# 12 — Teacher/student data readiness and probe

Status: probe complete; rejected by fixed 200-task gate

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

The probe is rejected as a student candidate. On the identical fixed 200-task
suite it verified 31/200 tasks with mean score 0.4408, below both the prior
student (57/200, 0.6217) and the base (94/200, 0.7400). Its faster generation
does not compensate for the quality regression.

## Next actions

1. Preserve the fixed-suite task/check metadata and normalized base report.
2. Analyze failure families and objective mismatch before changing the corpus.
3. Prefer task-contract or preference-objective experiments over naive corpus
   expansion.
4. Keep all candidate adapters held until the promotion thresholds are met.
