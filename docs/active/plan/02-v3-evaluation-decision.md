# 02 — Decide whether to evaluate v3-8,000

## Objective

Make an explicit go/no-go decision before using the GPU again.

## Decision inputs

- Stability across the complete 3,000- and 5,000-step reports.
- Family regressions and unresolved async-return behavior.
- Adapter latency versus the base model.
- Whether a 200-task result would change the next training decision.

## Rules

- **Go:** run only the existing 8,000-step 200-task report with the fixed
  configuration, then stop for analysis.
- **No-go:** preserve the 8,000-step artifact as an unmeasured candidate and
  move directly to CPU-only trajectory-pipeline work.
- Do not start a 980-task evaluation, new training run, export, or promotion as
  part of this step.

## Exit criteria

- The decision and rationale are recorded before any GPU command is run.

## Decision — 2026-08-30: GO, narrowly scoped

The complete v2, v3-3,000, and v3-5,000 reports show that v3 can improve on
the base but changes behavior materially between checkpoints. Measuring the
already-trained v3-8,000 artifact can resolve whether the later checkpoint
continues that pattern or produces a useful improvement. The existing report
already contains 68/200 records, so the evaluation is resumable without
discarding work.

Run only the fixed 200-task report with its original base, adapter, task file,
seed, and output path. After it completes, stop. Do not launch the 980-task
evaluation, new training, export, registration, or promotion.
