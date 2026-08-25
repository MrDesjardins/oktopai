# Benchmark plan

## Purpose

The benchmark is the evidence layer for oktopai. It measures whether specialization and hot-swapping improve the complete local system, not merely whether a model produces persuasive prose.

## Dataset

The first dataset is [benchmarks/tasks.json](../benchmarks/tasks.json). It is versioned and includes:

- stable task ID;
- expected expert;
- domain and difficulty;
- prompt and code context;
- tags;
- verification rules.

Current domains include TypeScript, React, Next.js, testing, SQL, Python, and general refactoring.

## Verification levels

Every result declares its evidence level:

- `failed`: a required or forbidden checklist condition was violated;
- `checklist_pass`: textual conditions passed, but no executable test was run;
- `fixture_pass`: a domain fixture contract passed, but its external project toolchain was unavailable;
- `verified`: an executable validator passed, such as Python compilation;
- `human_review`: reserved for later reviewer judgments.

SQL and Python currently have executable validators. TypeScript, React, Next.js, and Vitest currently have fixture-contract validators because this machine does not have `tsc`, React, Next.js, or Vitest project dependencies installed. The benchmark reports that limitation explicitly.

## Commands

Route-only, no Ollama call:

```bash
PYTHONPATH=src python3 scripts/run_benchmark.py --route-only
```

One installed model:

```bash
PYTHONPATH=src python3 scripts/run_benchmark.py --model qwen2.5-coder:7b
```

All models already installed locally:

```bash
PYTHONPATH=src python3 scripts/run_benchmark.py --all-installed
```

Use `--limit 2` for a quick smoke run. The runner never pulls models.

## Artifacts

Runs write:

- `.oktopai/benchmark-report.json` — manifest, routing metrics, per-task records;
- `.oktopai/benchmark-raw.jsonl` — raw local outputs and timing;
- `.oktopai/events.jsonl` — lifecycle and generation telemetry.

## Metrics

Routing:

- selected expert;
- expected expert;
- routing accuracy;
- confidence;
- routing latency.

Runtime:

- cold/warm state;
- load time;
- time to first token when available;
- generation time;
- total response time;
- model residency and swap events.

Quality:

- executable verification pass rate;
- checklist pass rate;
- human score, later;
- regression rate against the shared baseline.

System-level headline metric:

```text
verified task success / GiB of GPU memory
```

## Experimental discipline

Compare models on the same task IDs, prompts, repository versions, generation settings, and validator versions. Save raw outputs. Never rank models from latency alone or from a handful of subjective examples.

## Next.js hot-swap benchmark

The fixture at [benchmarks/nextjs_fixture](../benchmarks/nextjs_fixture) contains two deliberate defects:

- `app/page.tsx` uses `useState` without a Client Component directive;
- `lib/getValue.ts` indexes a generic object with an unconstrained string.

Run the benchmark with one specialist:

```bash
PYTHONPATH=src python3 scripts/run_nextjs_benchmark.py --mode single --model oktopai-nextjs
```

Run the hot-swapped version:

```bash
PYTHONPATH=src python3 scripts/run_nextjs_benchmark.py --mode swapped
```

The swapped run asks the Next.js expert to repair the page, then the TypeScript expert to repair the generic utility. It applies only allowlisted files, measures generation/token throughput, and checks the final source. Add `--build` after installing fixture dependencies to run `npm run typecheck` and `npm run build`. Use `--install` only after explicitly accepting the dependency download.

The latest comparison artifacts are `.oktopai/nextjs-benchmark-oracle.json` and `.oktopai/nextjs-benchmark-swapped.json`. The oracle passed typecheck and production build in approximately 10.6 seconds. The swapped specialists generated at roughly 143 tokens/second each, but the final build failed because the Next.js specialist omitted `"use client"`; the TypeScript specialist produced a valid generic fix.

The benchmark's central comparison is:

```text
single general model → one response → build correctness and latency
swapped specialists  → two targeted responses → build correctness, swap cost, and throughput
```

The hypothesis is not that swapping is always faster than one response. It is that small targeted experts can achieve higher verified correctness and acceptable end-to-end latency under a constrained memory budget.

## Trained GGUF comparison

The latest `.oktopai/benchmark-report.json` compares the existing 4.7 GB prompt-specialized `oktopai-typescript` model with the 397 MB `oktopai-typescript-trained-q4` GGUF over all eight benchmark tasks. The prompt-specialized model produced 4 executable `verified` results, 2 fixture passes, 1 failure, and 1 checklist pass, averaging 148 tokens/second and 2.32 seconds per task. The trained model averaged 608 tokens/second and 0.80 seconds per task, but produced 7 failures and 1 checklist pass. This is strong evidence for the speed and memory thesis, and equally strong evidence that the first tiny dataset is not yet sufficient for quality.

The trained model is therefore registered as an experimental expert with low default routing priority. It must not replace the baseline until its verified correctness improves.

## TypeScript v2 failure-focused retraining

The v2 dataset added seven targeted examples covering generic indexed access, null narrowing, discriminated unions, and typed dictionaries. It contains 17 records: 10 train and 7 validation. The v2 artifact was trained, merged, quantized, and registered as `oktopai-typescript-trained-v2-q4`.

The three-way benchmark did not improve quality: baseline produced 3 verified results, 2 fixture passes, 2 failures, and 1 checklist pass; v1 produced 7 failures and 1 checklist pass; v2 also produced 7 failures and 1 checklist pass. v2 generated at approximately 634 tokens/second, but one SQL response incurred a 99-second outlier while all three models were resident. This is a failed quality iteration and a useful signal that more examples alone are insufficient; the next iteration needs better instruction formatting, loss masking, and domain-specific held-out evaluation.

## Training artifact comparison

`.oktopai/adapter-evaluation-typescript-verified.json` records the same two TypeScript prompts run through the local 0.5B base and its PEFT adapter. The local TypeScript compiler now validates extracted code blocks. Both systems passed the narrowing task and both failed the generic task, so the first adapter does not demonstrate an improvement. Throughput was approximately 30 tokens/second for both. This is useful negative evidence: the dataset is too small and the adapter needs a stronger held-out evaluation before any specialization claim.
## Large generated suite

`benchmarks/typescript-generated-3000.json` contains 3,000 deterministic
TypeScript tasks generated from compiler-verified records. The generator is
`scripts/generate_benchmark_tasks.py`; it preserves family tags and provenance
and adds compiler-backed response checks. A route-only run completed with
100% routing accuracy and 139.24 ms total routing time. Full response runs
against thousands of tasks are intentionally separate because they consume
substantial local inference time; use `--limit` first, then run the full suite
when a long benchmark window is available.
