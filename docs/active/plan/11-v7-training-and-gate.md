# 11 — v7 source-localization training and gate

## Preconditions

- v7 SFT manifest exists and reports 476 records, 422 train / 54 validation.
- `audit_patch_emitter_sft.py` passes with zero failures.
- CPU unit tests and Python compilation pass.
- GPU memory is independently confirmed sufficient for the 3B base model.

## Training

Train one isolated adapter from
`.oktopai/datasets/typescript-patch-emitter-v7-source-localization-sft.jsonl`
using the frozen Qwen2.5-Coder-3B base and the existing 200-step configuration.
Do not overwrite v5 or any previously held adapter.

## Evaluation gate

First inspect that the adapter directory and configuration are complete. Then
run the unchanged 20-record local repository gate with compiler-backed replay.
Record contract validity, replacement replay, compilation, exact-gold matches,
family results, and all failed outputs. Do not start a broader evaluation.

## Acceptance interpretation

- A candidate is not successful merely because JSON parses or replacements
  replay; compiler-backed project success is required.
- Compare numeric-ratio failures specifically against the held v5 baseline of
  15/20 compilation.
- Any improvement must be independently reproducible and documented before a
  promotion decision. No export, upload, registration, or promotion is part
  of this step.

## Current state

The data and CPU preconditions are complete. GPU training is pending because
available memory has repeatedly been below the safe threshold. No v7
checkpoint or evaluation report exists.

## Result — 2026-09-01

- Host checks confirmed CUDA is available on the RTX 5080; the stale
  `.venv-training/bin/python` handoff path was valid on the host, and the
  mandatory PyTorch check returned `True NVIDIA GeForce RTX 5080`.
- The isolated 200-step run completed in 368.6 seconds and saved
  `.oktopai/adapters/typescript-patch-emitter-v7-source-localization`.
- Final training loss was 0.05131 and final validation loss was 0.01107.
  One intermediate validation pass reported a recoverable CUDA OOM; later
  validation passes completed and training exited successfully.
- The unchanged 20-record local gate completed with 15/20 contract-valid,
  15/20 replacement-replay-valid, 15/20 compiler-successful, and 0/20
  exact-gold matches.
- The five failures all emitted an unchanged replacement for the downstream
  canvas condition. This ties the held v5 baseline of 15/20 compilation and
  is not a promotion signal.
- The first attempted evaluation report is retained separately as an invalid
  54-record prompt/source mismatch diagnostic; it is not a model result.
- A host-context heartbeat is running at
  `.oktopai/logs/pc-heartbeat.log` for the authorized work window.

The v7 candidate is held. Do not promote, export, upload, or start a broader
evaluation from this result.
