# Targeted trajectory follow-up corpus

Date: 2026-08-31

The unseen-family evaluation identified two concentrated repair gaps in the v2
adapter: numeric `Record` values and primitive array unions. This follow-up
tranche targets those gaps without modifying the preserved 50-record test set.

## Frozen corpus

- Raw records: 40
- SFT records: 40
- Families: 20 `record-numeric-method`, 20 `primitive-array-narrowing`
- Split: 30 train, 10 validation
- Unique IDs: 40
- Independent replay: 40/40 passed
- Source SHA256: `bceff60e077c364c5ff5618271ac5cd49603e570eb2d5a75c4e83a3b00ac5dac`
- SFT SHA256: `dbf90427674f55bdac784892311436890061254c834ee2513215b1aea97b03a1`

Artifacts:

- `.oktopai/datasets/typescript-trajectories-targeted-v1.jsonl`
- `.oktopai/datasets/typescript-trajectories-targeted-v1-sft.jsonl`
- `.oktopai/datasets/typescript-trajectories-targeted-v1-sft.manifest.json`

## Readiness decision

The corpus is ready for an isolated follow-up training experiment. Its
validation split is intentionally small and synthetic, so training loss or
validation loss will not be treated as a quality claim. The unchanged 50-record
unseen test set must remain the primary transfer comparison, with contract
validity and independent replay reported separately.

## Training result

The isolated targeted adapter completed 200 CUDA steps in 323.9 seconds. Final
training loss was 0.2342 and validation loss was 0.01153. The very low loss on
10 synthetic validation records is evidence of fitting, not proof of transfer;
held-out generation and replay remain the next gate.

## Transfer result

On the unchanged 50-record unseen test set, the targeted adapter produced
49/50 contract-valid outputs. Independent replay passed 41/49. The numeric
record-method family improved from 0/10 replay passes with the original v2
adapter to 10/10. Primitive array-union performance declined from 5/10 to
2/10, showing that the focused tranche fixed one gap while destabilizing the
other. One object-literal output was contract-invalid.

The targeted adapter is therefore a useful diagnostic candidate but is not a
general-purpose replacement for v2 and is not promoted.

## Redesigned v2 corpus

To address the single-family validation flaw and regression risk, a new mixed
corpus is frozen at 60 records: 20 numeric-record, 20 primitive-array, 10
discriminated-union protection, and 10 object-literal protection examples.
There are 48 training and 12 validation records, with validation coverage of
4, 4, 2, and 2 records respectively. Independent replay passed 60/60.

The protection families are included to detect loss of capabilities that were
already working. The unchanged 50-record unseen set remains the external
transfer test and must not be folded into training.

## Redesigned v2 training result

The mixed-family targeted v2 adapter completed 200 CUDA steps in 348.3 seconds.
Final training loss was 0.2408 and final balanced validation loss was 0.003563.
Because the validation split contains only 12 synthetic records, this low loss
is fitting evidence rather than a quality claim. The unchanged 50-record test
set remains the required transfer gate.

## Redesigned v2 transfer result

The balanced 12-record validation set passed 12/12 contract checks and 12/12
independent replays. On the unchanged 50-record unseen set, the adapter
produced 49/50 contract-valid outputs, but only 36/49 passed replay. Numeric
record handling remained fixed, but primitive array-union repair fell to 0/10;
four other outputs also added an extra diagnose/observe sequence that did not
match the verifier’s expected trajectory. The redesigned candidate is rejected
for promotion and retained only for regression analysis.
