# 00 — Current checkpoint

## State

- v3 training is complete through 8,000 steps.
- Complete evaluation reports exist for v2, v3-3,000, and v3-5,000.
- The v3-8,000 evaluation is partial at 68/200 and must remain paused.
- No GPU work is required for this step.

The CPU-only contract/verifier phase is complete. The mixed 184-record corpus
passed independent replay 184/184. The union-correction candidate then passed
the unchanged 40-task disjoint real-repository gate with native contract
validity 40/40 and independent project replay 40/40. No packaging or
promotion decision has been made.

## Exit criteria

- The complete evidence set and its limitations are documented.
- The candidate remains held while the evidence and next experiment are
  reviewed; the next action is chosen in `02-v3-evaluation-decision.md`.
