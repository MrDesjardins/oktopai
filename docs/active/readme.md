# Active work

Updated: 2026-09-01

This folder contains the current research and implementation work. Start with
the numbered plan in [`plan/`](plan/), then use [`status.md`](status.md) for
the latest evidence and [`typescript-next-step-20260828.md`](typescript-next-step-20260828.md)
for the experiment handoff.

## Current checkpoint

The current held trajectory candidate is
`.oktopai/adapters/typescript-trajectory-real-supplement-v5-envelope`. It
achieved 80/80 native contract validity and 80/80 independent full-project
replay on the disjoint 80-task gate, then achieved 60/60 native validity and
60/60 replay on the multi-file gate. No promotion, export, or upload has
occurred.

Public-source datasets remain excluded from trajectory training: the local
inventory found response-only records and zero admissible source trajectories.
See `real-repository-trajectory-analysis.md` and `plan/08-source-derived-trajectory-collection.md`
for the evidence and admission rules.

## How to work here

1. Follow the numbered plan in order.
2. Update `status.md` when evidence or experiment state changes.
3. Add dated sections to the existing handoff instead of creating duplicate
   plans for the same model lineage.
4. Keep GPU work behind an explicit step and decision gate.
5. Treat compiler/test verification as evidence, not as a substitute for
   recording the interaction trajectory.

## Supporting documents

- [`tool-using-specialists.md`](tool-using-specialists.md) — target tool-use
  contract and trajectory format.
- [`speed-quality-plan.md`](speed-quality-plan.md) — quality, speed, memory,
  and distillation strategy.
- [`roadmap.md`](roadmap.md) — broader oktopai architecture and milestones.
- [`typescript-pilot-recovery.md`](typescript-pilot-recovery.md) — teacher-data
  quality and recovery rules.
