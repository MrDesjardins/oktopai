# Safe mixed trajectory follow-up

Date: 2026-08-31

The targeted v2 adapter fixed numeric record repairs but regressed primitive
array repairs and trajectory sequencing. To reduce that risk, this follow-up
retains the successful original v2 foundation and adds the targeted mixed
families as a supplement.

## Frozen corpus

- Foundation: 100 records from `typescript-trajectories-v2`
- Targeted supplement: 60 records from `typescript-trajectories-targeted-v2`
- Total: 160 unique records
- Training: 128 records
- Validation: 32 records (20 foundation, 12 targeted)
- Independent replay: 160/160 passed
- Families: 5 foundation families plus 2 target and 2 protection families

Artifacts:

- `.oktopai/datasets/typescript-trajectories-safe-mixed-v1.jsonl`
- `.oktopai/datasets/typescript-trajectories-safe-mixed-v1-sft.jsonl`
- `.oktopai/datasets/typescript-trajectories-safe-mixed-v1-sft.manifest.json`

## Training gate

This corpus is ready for one isolated follow-up run. The unchanged 50-record
unseen test set remains outside the merge and is the primary transfer gate.
The decision criteria are: preserve the original v2 trajectory behavior,
improve numeric record repairs, recover primitive array narrowing, and avoid
new contract-sequence failures. No export or promotion is authorized from
training loss alone.

## Evaluation result

The safe-mixed adapter passed balanced internal validation completely: 32/32
contract-valid outputs and 32/32 independent replays. On the unchanged
50-record unseen test, it produced 50/50 contract-valid outputs and passed
50/50 independent replays. This includes full recovery of the two previously
failing target families while preserving the protection families.

The base produced 0/50 contract-valid outputs. Adapter generation averaged
9.41 seconds per record versus 5.50 seconds for the base. The result is the
strongest trajectory-format and executable-replay signal in this sequence, but
the tasks are still synthetic; no promotion or export is justified yet.

## Training result

The safe-mixed adapter completed 200 CUDA steps in 404.9 seconds. Final
training loss was 0.2596 and final validation loss was 0.1303. The validation
loss remained moderate on the larger mixed split, unlike the near-zero loss of
the narrow targeted run. This is a healthier fitting signal, but executable
evaluation on the unchanged 50-record test set remains required.
