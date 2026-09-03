# TypeScript next-step handoff

Updated: 2026-08-28

## Current state

- Targeted corpus generated and strict-compiler verified:
  `.oktopai/datasets/typescript-targeted-contract-verified-20260828.jsonl`
  (3,600 records; 2,659 train, 581 validation, 360 test).
- Targeted adapter probe completed on CUDA for 2,000 steps:
  `.oktopai/adapters/typescript-targeted-0.5b-probe`
- The directory name is stale: `adapter_config.json` identifies
  `.oktopai/hf-bases/qwen2.5-coder-3b` as the base. Never evaluate it against
  the 0.5B base.
- Training log:
  `.oktopai/logs/typescript-targeted-0.5b-probe.log`
- Final training loss: 0.001187.
- The first fixed-suite evaluation is/was launched with seed `20260826`:
  `.oktopai/evaluations/typescript-targeted-0.5b-probe-heldout-50-seed-20260826.json`

## Resume after reboot

From `/home/miste/code/oktopai`, first check whether the evaluation output
already exists and is valid. Do not start a duplicate evaluation if it does.

```bash
./.venv-training/bin/python -c "import json,os; p='.oktopai/evaluations/typescript-targeted-0.5b-probe-heldout-50-seed-20260826.json'; print('exists',os.path.exists(p)); print('records',len(json.load(open(p))['records']) if os.path.exists(p) else 0)"
```

If missing, rerun the first evaluation with GPU access:

```bash
./.venv-training/bin/python scripts/evaluate_adapter.py --base-model .oktopai/hf-bases/qwen2.5-coder-3b --adapter .oktopai/adapters/typescript-targeted-0.5b-probe --tasks benchmarks/typescript-heldout-980.json --domain typescript --max-tasks 50 --shuffle-seed 20260826 --max-new-tokens 256 --device cuda --output .oktopai/evaluations/typescript-targeted-0.5b-probe-heldout-50-seed-20260826.json
```

Then run the second fixed seed, writing a separate file. The compatible report
uses a corrected filename:

```bash
./.venv-training/bin/python scripts/evaluate_adapter.py --base-model .oktopai/hf-bases/qwen2.5-coder-3b --adapter .oktopai/adapters/typescript-targeted-0.5b-probe --tasks benchmarks/typescript-heldout-980.json --domain typescript --max-tasks 50 --shuffle-seed 20260827 --max-new-tokens 256 --device cuda --output .oktopai/evaluations/typescript-targeted-3b-compatible-heldout-50-seed-20260827.json
```

After both reports exist, compare adapter and base record-level verification,
break results down by family, and only then decide whether a 200-task run or
another data revision is justified. For the unattended continuation, run:

```bash
./.venv-training/bin/python scripts/run_typescript_overnight_20260828.py
```

It resumes the compatible targeted lineage through 3,000, 5,000, 8,000, and
12,000 steps, evaluates each stage, and finishes with a 200-task report. It
skips valid reports and never exports, registers, uploads, or promotes a
model. Run it in the GPU-capable context; the managed shell may not expose
CUDA.

## Gate and safety

Do not merge, quantize, register, promote, or upload this candidate. The prior
3B gated adapter failed the final quality gate, and this probe is diagnostic
until both fixed seeds are complete. Preserve all JSON reports and update the
failure-analysis report before any new training.

## Follow-up experiment — 2026-08-29

The 12,000-step targeted adapter improved the 200-task result to 180/200
verified versus 108/200 for the compatible base, but it was slower and the
synthetic corpus still left async-return weak. A fresh corpus and adapter are
now in progress:

- Corpus: `.oktopai/datasets/typescript-targeted-contract-v2-verified-20260829.jsonl`
  (4,800 records; strict compilation passed; eight balanced families).
- New adapter: `.oktopai/adapters/typescript-targeted-v2-3b-probe`.
- Training: 2,000 CUDA steps, completion-only loss, isolated from the prior
  adapter.
- Queued reports:
  `.oktopai/evaluations/typescript-targeted-v2-3b-heldout-50-seed-20260826.json`
  and
  `.oktopai/evaluations/typescript-targeted-v2-3b-heldout-50-seed-20260827.json`.

Do not extend or promote this probe until both reports are complete and the
new adapter is compared against both the base and the existing 12,000-step
candidate.

## Pause/resume procedure

Long evaluations checkpoint atomically after every completed task. To resume
the paused full validation, run:

```bash
./.venv-training/bin/python scripts/run_typescript_v2_validation_queue.py
```

The queue skips the completed 200-task report and invokes
`evaluate_adapter.py --resume` for the 980-task report at
`.oktopai/evaluations/typescript-targeted-v2-3b-heldout-980-seed-20260827.json`.
If that file contains a partial report, completed task IDs are loaded and only
the remaining tasks are generated. Do not change the base, adapter, task file,
domain, seed, or output path when resuming.

## Extended unattended continuation — 2026-08-30

The current full v2 validation remains the first priority. A separate
12-hour follow-up is waiting for its completion:

```bash
./.venv-training/bin/python scripts/run_typescript_12h_followup.py
```

It writes family analysis to
`.oktopai/evaluations/typescript-targeted-v2-980-family-analysis.json`. Only
if the full v2 adapter beats the base on verified task count does it merge the
verified v2 and external-gated records into
`.oktopai/datasets/typescript-targeted-v3-mixed-20260830.jsonl`, train an
isolated v3 adapter through 3,000/5,000/8,000 steps, and evaluate each stage.
Otherwise it stops after analysis. It never modifies the v2 adapter or
promotes an artifact.

## Pause point after v3 training — 2026-08-30

The v3 mixed-corpus adapter completed training through 8,000 steps. Its queued
200-task evaluation was stopped after 68 records so the checkpoint could be
reviewed alongside the complete 3,000- and 5,000-step reports. The partial
8,000-step report is retained for audit only and must not be treated as a
quality result.

Complete results so far:

| Checkpoint | Adapter verified | Adapter score | Base verified | Base score |
|---|---:|---:|---:|---:|
| v2 | 123/200 | 0.814 | 94/200 | 0.740 |
| v3, 3,000 steps | 140/200 | 0.800 | 94/200 | 0.740 |
| v3, 5,000 steps | 133/200 | 0.840 | 94/200 | 0.740 |

The decision at this pause point is to analyze checkpoint stability, family
tradeoffs, and the cost of adapter inference before authorizing another
evaluation. No promotion, export, registration, upload, or new training is
authorized by this handoff.
