# Current CPU Analysis

Date: 2026-08-30

## Decision

The strongest complete comparable checkpoint currently available is the v3 mixed adapter at 5,000 steps. The v3 8,000-step files are partial recovery artifacts, not evaluation results:

- canonical 8k report: 91/200 records, `complete: false`
- max-64 recovery report: 16/200 records, `complete: false`
- the two-model CPU recovery was partial
- adapter-only CPU recovery: 200/200 unique records, `complete: true`

No promotion, export, registration, or upload is justified from the current evidence.

## Complete 200-task comparison

| Run | Base verified | Adapter verified | Adapter score | Adapter mean output tokens |
|---|---:|---:|---:|---:|
| v2, 3b | 94/200 | 123/200 | 0.8142 | 134.8 |
| v3, 3k | 94/200 | 140/200 | 0.8000 | 30.0 |
| v3, 5k | 94/200 | 133/200 | 0.8400 | 37.6 |

The v3 5k run has the best mean verification score among these complete reports, but fewer fully verified tasks than v3 3k. This is favorable evidence, not a robust monotonic training trend.

## 8k follow-up result

The isolated adapter-only follow-up is complete at [the preserved report](../../.oktopai/evaluations/typescript-targeted-v3-mixed-3b-step-8000-heldout-200-seed-20260826-cpu64-adapter-only.json). It reuses the fixed-seed base outputs from v3 5k and generates fresh v3-8k adapter outputs. The run has 200 unique records and 52 explicit generation timeouts. On the 148 non-timeout records, the cached base verified 71/148 with score 0.7432; the adapter verified 0/148 with score 0.0738 and averaged 1.0 generated token. The 64-token/CPU constraint makes this unsuitable for direct comparison with the complete GPU reports. It is evidence that the CPU-constrained path is operational, not evidence that v3-8k quality regressed.

## Beyond prompt → answer

The repository now contains a typed trajectory contract, an allowlisted tool/command policy, an independent verifier that replays edits and compiles TypeScript, and a 20-record verified trajectory corpus. These artifacts support inspect → diagnose → edit → observe → retry → final distillation rather than only final answers.

## Next authorized step

The GPU runtime stalled before the first record. The CPU-constrained, resumable evaluation is now complete as a diagnostic recovery, with its own output path and a 64-token cap. Do not overwrite partial reports, start another training run, or promote the adapter until a normal uncapped GPU report is available and compared with the complete evidence.

## Trajectory-aware candidate

The isolated trajectory-aware adapter was trained for 200 CUDA steps from the
frozen 20-record SFT conversion. On the two-record validation split, both
adapter outputs were contract-valid and passed independent replay through the
trajectory verifier. The base model produced contract-invalid outputs on both
records. Because the split is tiny and synthetic, this demonstrates that the
pipeline can teach the structured format; it does not establish generalization
or justify promotion.

## Expanded trajectory corpus v2

The next CPU-only step expanded the synthetic trajectory seed into 100
records, balanced across five families: unknown length, nullable property,
unknown property, generic string handling, and implicit-any repair. The split
is 80 training and 20 validation records, with 100 unique IDs.

The independent replay verifier passed all 100 records. It recreated each
temporary repository, applied the recorded edit, ran strict TypeScript for the
diagnosis and retry, and observed the expected failure-then-pass sequence.
The converted SFT file and manifest are stored under `.oktopai/datasets/`.
This establishes corpus integrity and format coverage; it is not evidence of
model quality until a separately trained candidate is evaluated on held-out
tasks.

The immediate next gate is review of this corpus and its manifest. If approved,
the next training run should be isolated, explicitly labeled as v2 trajectory
training, and evaluated against the same held-out validation records plus a
broader executable suite. Until that decision, no GPU training is started.

## v2 trajectory training result

The isolated v2 adapter completed the approved 200-step CUDA run in 353.8
seconds. Final training loss was 0.2219 and validation loss was 0.2069. The
loss curve reached its lowest validation value near the middle of the run and
then leveled off around 0.20 while training loss continued toward zero, which
is consistent with overfitting this small synthetic corpus. No held-out model
generation has been started yet; the adapter remains an unpromoted experiment.

The detailed trainer history places the best recorded validation loss at step 60
(0.1259). It increased to 0.2069 at step 200 while training loss fell to
0.00044. The run saved checkpoints at steps 100 and 200, so the best validation
point was not retained as an adapter artifact. Held-out evaluation of the final
adapter should therefore be read as a final-checkpoint diagnostic, not as a
best-checkpoint selection result.

## v2 held-out trajectory result

The final v2 adapter generated contract-valid trajectories for all 20 validation
records, and the independent replay verifier passed all 20. The base model
produced no contract-valid trajectories on this split. The adapter averaged
9.45 seconds and 257 generated tokens per record; the base averaged 5.19
seconds and 232 tokens. This confirms that the teacher-student path learned the
structured inspect/diagnose/edit/observe/retry/final format on the held-out
synthetic families. It does not yet show robustness on unseen task families or
real repositories, and the adapter remains unpromoted.

## Unseen-family transfer result

The broader evaluation corpus contains 50 test-only records from five families
absent from v2 training: union-return, discriminated-union, array-union,
object-literal-mismatch, and record-method. The corpus itself was independently
verified 50/50 before model generation.

The adapter generated contract-valid JSON for all 50 records, while the base
generated none. Independent replay of the adapter output passed 35/50. The 10
record-method failures and 5 array-union failures show that structured format
transfer is stronger than executable repair transfer: the model learned the
event shape, but still applies incorrect repairs on particular unseen type
patterns. Adapter generation averaged 9.92 seconds per record versus 5.93
seconds for the base.

Decision: hold the adapter as an unpromoted research artifact. The next useful
step is targeted analysis of those 15 failed repairs and a new verifier-backed
training/evaluation design, not export or registration.
