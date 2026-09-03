# Active work

Updated: 2026-09-02

This folder contains the current research and implementation work. Start with
the numbered plan in [`plan/`](plan/), then use [`status.md`](status.md) for
the latest evidence and [`typescript-next-step-20260828.md`](typescript-next-step-20260828.md)
for the experiment handoff.

## Current checkpoint

The current held candidates are the v5-envelope trajectory adapter and the
v10 bounded patch-emitter adapter. The strongest trajectory result remains
80/80 native validity and replay on the disjoint gate plus 60/60 on the
multi-file gate. The patch-emitter candidates, including v10, remain held at
15/20 compiler-successful on the unchanged local gate. No promotion, export,
or upload has occurred.

The teacher/student line is also held: Qwen3-Coder 30B produced 2,450/2,450
strictly compiling teacher records, but the Qwen2.5-Coder 3B student reached
57/200 versus 94/200 for the base. A new balanced external-data probe is
prepared and isolated; its short benchmark improves one synthetic task score
but is not enough to claim generalization.

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
