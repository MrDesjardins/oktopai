# Oktopai speed-and-quality training plan

## Position

The experiment has demonstrated an important asymmetry: a 397 MB trained GGUF runs roughly four times faster than the 4.7 GB prompt-specialized model, but currently fails most coding validators. The next objective is not simply more synthetic data or more epochs. It is a verified data and optimization loop that improves quality while preserving the small-model latency and memory advantage.

```text
real task → teacher candidates → executable verifier → accepted record
                                      ↓
                              train and evaluate
                                      ↓
                         versioned artifact and gate
```

## What the current result says

The v1 and v2 failures have several plausible causes:

1. A 0.5B student may be too small for broad coding behavior.
2. The training set is tiny and mostly idealized short answers.
3. The trainer currently computes loss over system and user text as well as the completion; it should primarily teach the answer.
4. Benchmark records need strict domain filtering.
5. A TypeScript artifact must first be evaluated on TypeScript tasks, not eight unrelated domains.
6. Synthetic traces amplify teacher mistakes unless independently compiled, tested, or reviewed.
7. Longer training on noisy records can make the student confidently reproduce errors.

More examples alone did not improve v2, so the next iteration changes both data quality and the objective.

## Phase A: a clean TypeScript quality gate

Build at least 50 TypeScript-only held-out tasks, split by family rather than random rows:

- generic indexed access and mapped types;
- union narrowing and null handling;
- inference and overloads;
- async return types and error paths;
- React prop and event typing;
- module and package typing;
- TypeScript migrations and compiler diagnostics.

Every task needs failing source, compiler configuration, expected behavior, and a deterministic validator. A model passes only when it compiles and satisfies behavior checks. Text similarity is not a quality metric.

Candidate gate:

- at least 80% held-out pass rate;
- no more than a 5-point regression on a general coding smoke set;
- no prohibited `any`, fabricated APIs, or unsafe assertions;
- cold/warm load, p95 latency, tokens/second, and artifact size recorded.

Until these gates pass, the trained expert remains opt-in and low priority.

## Phase B: stronger local teacher data

Use the existing 7B Ollama specialist as a candidate generator. For each task, request multiple forms: direct repair, minimal patch, explanation plus patch, alternative implementation, and a hard negative. Run every candidate through the local TypeScript compiler and task-specific tests. Keep only passing candidates.

Each record must preserve task context, candidate output, exact verifier command/result, teacher model and parameters, source/license, language and dependency versions, and content hashes. Target 1,000–3,000 verified TypeScript records before claiming data-scale evidence.

Agentic Codex/OpenCode transcripts can be valuable when they contain a real failure, diagnosis, patch, tool result, and corrected patch. Do not ingest transcripts blindly: redact secrets and private paths, remove irrelevant chatter, check licensing, and accept only traces whose final change passes an independent verifier. Synthetic data should multiply real failures, not replace them.

## Phase C: fix the objective

Use the tokenizer chat template and completion-only loss masking:

```text
system + user context  → ignored by loss
assistant completion    → loss applied here
```

Run a controlled ablation matrix:

| Experiment | Data | Objective |
|---|---|---|
| A | current clean seed | current SFT |
| B | current clean seed | completion-only SFT |
| C | 1,000 verified repairs | completion-only SFT |
| D | repairs plus hard negatives | completion-only SFT |
| E | compiler-filtered teacher candidates | completion-only SFT |

Keep the base, rank, quantization, prompts, and held-out suite fixed between rows.

## Phase D: distillation and preference optimization

After supervised fine-tuning produces a passing baseline:

1. Distill concise, correct teacher outputs.
2. Add preference pairs where one candidate compiles and another fails.
3. Try DPO/ORPO or a verifier-guided objective once chosen/rejected labels are reliable.
4. Use execution-guided rejection sampling before full reinforcement learning.

Full RL is not the first move on this machine; verifier-guided filtering provides cleaner signal with less complexity.

## Phase E: measure the Pareto frontier

Every artifact must report parameter count, GGUF size, cold/warm load, unload time, time to first token, tokens/second, memory, and verified quality by task family. The target is the best quality/speed/memory point, not the smallest model. If 0.5B cannot reach the quality gate, test a 1.5B–3B student before adding increasingly complex training methods.

## Concrete next sequence

1. Fix strict domain filtering in dataset construction.
2. Add chat-template and completion-only loss masking to `train_lora.py`.
3. Add a verifier-backed TypeScript dataset builder with compiler evidence.
4. Expand the TypeScript benchmark to 50 held-out tasks.
5. Generate local teacher candidates and retain only verified repairs.
6. Train A/B adapters with identical hyperparameters.
7. Add hard negatives and preference pairs after the SFT baseline passes.
8. Export the best checkpoint to GGUF and measure the speed/quality frontier.
9. Test a second student size if the 0.5B quality ceiling is too low.
10. Promote an artifact into default routing only after the quality gate passes.

The first implementation of this sequence is now present: dataset construction strictly filters benchmark examples by task domain, and `train_lora.py` supports chat-template formatting, completion-only masking, and dynamic padding. The initial v3 run completed on CPU; its two-task check still failed the generic task, so the next work remains expanding verified TypeScript coverage rather than promoting v3.

The corpus expansion is now operational. `scripts/generate_typescript_synthetic.py` creates 10,000 deterministic records across 10 TypeScript families and compiles the entire generated corpus with the local TypeScript compiler. The unified v5 corpus contains 10,014 records: 7,537 train, 1,497 validation, and 980 test. These are programmatic examples, not evidence of real-world coverage; the next data layer should add license-reviewed open-source repository tasks and compiler-filtered local teacher traces.

The long-term domain sequence is:

```text
TypeScript → CSS/layout → React → Next.js → testing → SQL → general coding
```

Each domain gets its own task families, verifier, dataset manifest, adapter/checkpoint lineage, GGUF export, and lifecycle measurements. Shared base weights may be reused, but domain quality gates remain independent.

## Governance

Every dataset release needs provenance, license status, redaction status, task/version metadata, verifier logs, and a manifest hash. Repository content stays local. Teacher generation remains local-only, with no silent remote fallback.

## Success definition

The experiment succeeds when a versioned small expert is measurably better on its narrow task family than the shared baseline while being materially faster or smaller, and oktopai can route, load, evict, and reconstruct context without relying on model-specific KV state.

Current data-flywheel result: 10,000 compiler-verified programmatic TypeScript records plus 13 independently compiler-verified local teacher traces, for a 10,024-record v6 corpus. The next scale-out should repeat this process with larger teacher batches and license-reviewed repository tasks, then train and test the resulting artifact against the held-out split.

## Repository-data flywheel

The first public source acquisition is a shallow checkout of
`microsoft/TypeScript`, recorded in `experiments/runs.jsonl` with commit and
license-file provenance. `scripts/extract_typescript_repo_tasks.py` selects
compiler-conformance fixtures as reviewable candidates. It does not promote
raw source to training labels: candidates must be answered by a local teacher,
then pass a compiler- or test-based verifier, and only then enter a versioned
training split. This separation is essential for avoiding large volumes of
plausible but incorrect synthetic data.

The intended loop is:

```text
public repository → provenance manifest → candidate extraction
  → local teacher trace → compiler/test filter → deduplicated split
  → adapter training → held-out executable benchmark → ledger
```

The same pipeline can later ingest CSS, React, Next.js, testing, and SQL
repositories. Each domain should have its own verifier and versioned test set;
record count alone is not a quality metric.
