# Overnight Queue Plan — 2026-08-26

## Objective

Use the available overnight window to improve oktopai's TypeScript specialist
without confusing more compute with better results. The current CUDA run must
finish first. Every later stage records raw outputs, timings, checksums, and
quality decisions so a failed experiment is still reproducible.

## Non-negotiable rules

- Never replace the base model or current adapter in place.
- Never train on external records before provenance, deduplication, and strict
  TypeScript verification.
- Never promote an adapter based only on training loss or tokens/second.
- Keep the fixed held-out suite untouched and use the same seed for comparisons.
- Stop a parallel workload if it materially slows the active student training.
- Do not download another large model overnight.
- Keep all generated data, manifests, logs, and checksums under versioned or
  persistent `.oktopai` artifact paths.

## Queue order

### 0. Finish and capture the current run

The active run trains a Qwen2.5-Coder 3B student with a LoRA adapter from 2,450
Qwen3-Coder 30B answers. Checkpoints are already saved periodically. When the
run exits:

1. confirm the final checkpoint and training metadata;
2. preserve the 2,450-record teacher trace and verified corpus;
3. collect loss, step time, GPU/device, and checkpoint inventory;
4. use the controller's fixed 200-task held-out evaluation;
5. do not export unless the student improves the base model.

### 1. Throughput optimization without quality regression

Build a repeatable local throughput matrix using the same base model, data,
seed, and a short bounded run. Compare the current configuration with:

- pre-tokenized data versus tokenization during mapping;
- batch size 1, 2, and 4, subject to VRAM safety;
- equivalent effective batch sizes via adjusted accumulation;
- gradient checkpointing enabled versus disabled when memory permits;
- length-grouped batches and dataloader workers;
- BF16, TF32, fused optimizer, and attention implementation when available.

For each variant capture GPU memory, wall time, tokens/second, examples/second,
loss curve, and compiler acceptance on a fixed smoke subset. A variant is
eligible for the next quality run only if it is faster and its short-run loss
and smoke acceptance are not materially worse. A throughput win that damages
held-out quality is rejected.

Expected deliverable: a selected training configuration and a report comparing
throughput, memory, and quality. The active 12,000-step run remains the
scientific baseline even if a faster recipe is found.

### 2. External-data quality pipeline

Process the two persisted TypeScript imports:

- `bleugreen/typescript-instruct`: 10,000 raw records;
- `grenishrai/typescript-dataset`: 3,000 raw records, 7 exact duplicates removed.

The pipeline is:

```text
raw JSONL
  -> checksum and source manifest
  -> schema/provenance audit
  -> exact and normalized deduplication
  -> family classification
  -> isolated strict tsc verification
  -> rejection diagnostics and acceptance metrics
  -> repository/source-level train/validation/test split
  -> candidate corpus, never automatic promotion
```

Verification runs only after the current student is finished, or with a
strictly limited worker count that does not starve training. Report acceptance
by source and family. Imported examples must beat a minimum gate of 40%
compiler acceptance, at least four families, and no single source contributing
more than 70% of the accepted set unless explicitly documented.

### 3. Analyze the teacher–student run

Produce a factual report containing:

- teacher generation acceptance and family coverage;
- student training configuration, duration, steps, and loss trajectory;
- base versus adapter held-out correctness;
- per-family gains and regressions;
- output length, time to first token, total latency, and tokens/second;
- checkpoint-by-checkpoint quality if intermediate evaluation is available;
- failure categories with representative raw outputs;
- whether the student is eligible for export.

Training loss is diagnostic only. The primary decision is held-out executable
quality, followed by latency and regression checks.

## Controlled next training loop

Only if the current evaluation or the external-data gate justifies it:

1. merge verified external records with the existing teacher corpus using a
   versioned manifest;
2. preserve a fixed held-out suite and create a new validation split;
3. run the selected throughput configuration on a new adapter directory;
4. evaluate the new adapter against both the original base and current student;
5. keep the winner only when correctness improves across families without a
   serious regression;
6. export to GGUF/Ollama only after the quality decision;
7. benchmark warm/cold generation and model hot-swapping;
8. record the result and stop rather than filling time with unjustified runs.

If no candidate passes, retain the data and diagnostics and use the remaining
window for analysis, not blind additional training.

## Expected artifact layout

```text
.oktopai/
  external/typescript/       raw imports, normalized data, manifests
  adapters/                   immutable checkpoint directories
  evaluations/               held-out JSON reports and raw outputs
  benchmarks/                throughput and lifecycle measurements
  logs/                      queue logs
experiments/runs.jsonl        append-only event ledger
docs/research/                interpretations and source notes
```

## Morning summary

The final summary must state what actually completed, with exact artifact paths,
commit IDs, test results, quality gates, speed measurements, rejected
experiments, and the three highest-value next experiments. It must distinguish
completed work from queued work and must not claim a specialist is good unless
the fixed held-out evaluation supports that claim.
