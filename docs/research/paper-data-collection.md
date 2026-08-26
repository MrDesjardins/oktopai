# Paper data collection and post-run protocol

This document is the measurement contract for the future oktopai paper. It
prevents attractive but incomplete claims such as “the model is faster” or
“the specialist is better” without recording the hardware, artifact, quality,
and cost that produced the result.

## Required identity for every run

Every experiment records:

- UTC start and end time;
- local Git commit and dirty-tree status;
- dataset, source repository commit, split, row count, and SHA-256;
- teacher/student/base/adapter/runtime identifiers and licenses;
- quantization, context length, decoding settings, and concurrency;
- hardware, CUDA/driver/runtime versions, and GPU memory;
- script command, prompt/template version, and environment manifest;
- output/checkpoint paths and checksums;
- cost, GPU price, storage, transfer size, and accepted-record cost for Runpod.

Use `experiments/runs.jsonl` as the append-only source of truth. Markdown
summaries may explain results, but must not replace the ledger.

## Metrics to collect

### Data and training

- candidate, accepted, rejected, duplicate, and preference-pair counts;
- counts by domain, task family, repository, version, and difficulty;
- compiler/test/browser/database verification results and failure reasons;
- train/validation/test split hashes and contamination checks;
- optimizer, learning rate, batch size, sequence length, steps, epochs;
- training wall time, peak memory, loss curves, validation loss, and tokens seen;
- adapter size, merged checkpoint size, quantized artifact size, and checksum.

### Routing and orchestration

- selected logical expert and physical model;
- score, alternatives, routing reasons, and routing latency;
- preload, warm reuse, cold load, unload, eviction, and shared-model reuse;
- GPU/CPU residency and model-load duration;
- session size, context truncation, tool calls, and lifecycle events.

### Coding quality

- task completion rate;
- strict compiler pass rate;
- lint, unit-test, framework-build, browser, accessibility, migration, and
  query-result pass rates;
- files changed, patch size, unnecessary changes, and rollback rate;
- tool-selection accuracy, unnecessary-tool rate, unsafe-command rate;
- recovery rate after a failed command;
- unsupported-claim rate and evidence-grounding score;
- human review only as a separate labeled metric, never mixed with automated
  verification.

### Speed and cost

- time to first response/token when available;
- prompt tokens, completion tokens, generation duration, and tok/s;
- end-to-end verified repair latency;
- sequential versus concurrent throughput;
- cold-start and warm-start latency;
- Runpod wall time, cost, cost per generated record, and cost per accepted
  verified record.

## Required comparisons

Every specialist experiment compares the same held-out tasks across:

1. shared base model;
2. prompt-specialized model;
3. LoRA/QLoRA adapter;
4. merged and quantized standalone model when available;
5. stronger teacher only as a data-generation reference.

For hot-swapping, compare one shared model, adapter swapping, and independent
standalone specialists under the same request sequence. Report both individual
request speed and total verified-workflow speed.

## Current active experiment chain

The active chain is:

1. Runpod Qwen2.5-Coder-14B teacher pilot;
2. transfer and checksum raw records;
3. local strict TypeScript verification and family analysis;
4. sequential versus four-worker teacher throughput test;
5. update prompt/data curriculum from rejected records;
6. train the next student adapter;
7. merge/export/quantize only after held-out evaluation;
8. run the website fixture and hot-swap benchmark;
9. terminate Runpod after artifacts are locally verified.

Do not start Qwen3-Coder-Next, a larger teacher, or a long Runpod generation
run until the current pilot has a measured acceptance rate and cost per useful
record. A stronger model is valuable only if it produces more accepted,
diverse, tool-grounded records per dollar.

## Post-run execution checklist

When the local and Runpod work finish, execute this order:

```bash
# 1. Verify the repository state and record the completion event.
rtk git status
python3 scripts/record_experiment.py --kind teacher-data \
  --name typescript-runpod-pilot --status completed \
  --metadata '{"pod_id":"9793s4612yjtgg","model":"qwen2.5-coder:14b"}'

# 2. Copy the remote manifest, raw JSONL, logs, and checksums locally.
#    Verify every SHA-256 before terminating the Pod.

# 3. Independently verify accepted teacher outputs.
python3 scripts/ingest_verified_teacher_data.py \
  --input .oktopai/runpod/teacher-pilot/answers.jsonl \
  --output .oktopai/datasets/typescript-runpod-verified.jsonl

# 4. Record acceptance, family coverage, latency, and cost metrics.
python3 scripts/record_experiment.py --kind teacher-data \
  --name typescript-runpod-pilot-verification --status completed \
  --metadata '{"input":"...","accepted":0,"rejected":0}'

# 5. Run tests and the fixed held-out benchmark before training.
uv run pytest
PYTHONPATH=src python3 scripts/run_benchmark.py --route-only

# 6. Only if the quality gate passes, train the next student adapter.
.venv-training/bin/python scripts/train_lora.py \
  --data .oktopai/datasets/typescript-runpod-verified.jsonl \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --output .oktopai/adapters/typescript-runpod-v1 --train

# 7. Evaluate first; export only a winning artifact.
.venv-training/bin/python scripts/evaluate_adapter.py ...

# 8. Synchronize and checksum artifacts, then terminate—not stop—the Pod.
```

The commands with `...` are intentionally not run blindly: their exact paths,
task split, and evaluator arguments must be filled from the completed manifest.
This avoids silently evaluating a different dataset or promoting an artifact
from an incomplete remote run.

## Paper claims we may eventually make

Only claim a specialist improvement when the result is reproduced on a fixed
held-out suite and includes confidence intervals or repeated-run variation.
State clearly whether the result is:

- better code quality;
- better tool-use reliability;
- faster generation;
- faster verified workflow completion;
- lower memory or cold-start cost;
- lower remote training cost;
- or merely lower training loss.

The central paper result should be the complete verified website workflow:
TypeScript, Next.js, CSS, and SQLite specialists selected and hot-swapped on a
machine with constrained GPU memory, compared against a shared-model baseline.
