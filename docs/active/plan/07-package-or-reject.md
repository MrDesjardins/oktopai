# 07 — Package or reject the candidate

Status: hold for review; no packaging or promotion

## Objective

Hold both experimental candidates. The complete comparable response-only
evidence ends at 5,000 steps; the 8,000-step follow-up is CPU-constrained and
diagnostic only, while the trajectory candidate has only two synthetic held-out
records. Neither meets a promotion gate.

Make the final artifact decision only after quality and systems measurements.

## Promotion gate

- Fixed held-out quality gate passes.
- No material family regression without an explicit tradeoff decision.
- Tool behavior is safe and evidence-grounded.
- Load time, memory, throughput, and artifact lineage are recorded.
- Base model, dataset, code, and checksums are documented.

## Outcomes

- **Promote:** package and register the artifact as opt-in, then benchmark
  hot-swapping.
- **Reject:** retain the artifact and failure analysis, revise data or objective,
  and return to the appropriate earlier step.

The union-correction candidate currently meets the bounded 40-task local
trajectory gate, but this is not sufficient for promotion by itself. Retain
the adapter and all replay evidence while reviewing broader quality,
systems, and lineage measurements. Neither outcome authorizes external upload
by itself.
