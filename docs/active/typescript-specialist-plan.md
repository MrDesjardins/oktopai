# TypeScript specialist training plan

## Clarification: model training versus LoRA training

The current experiments are genuine neural-network training, but they use
LoRA (Low-Rank Adaptation). The 0.5B base model weights remain frozen while a
small set of trainable matrices is optimized with backpropagation. The result
is an adapter, not an independent model until it is merged into the exact base
checkpoint.

The phases are:

1. **LoRA/QLoRA experimentation**: cheap, fast comparisons of data, prompts,
   objectives, and student sizes.
2. **Adapter merge**: combine the best adapter with its exact base model to
   create a standalone Transformers checkpoint.
3. **GGUF quantization**: create an Ollama-loadable specialist and measure
   memory, swap time, and generation speed.
4. **Full-model fine-tuning**: optional later work that updates all model
   weights. It needs much more VRAM, storage, compute, and regularization, and
   should only happen after the LoRA experiments identify a strong recipe.

LoRA is therefore not a substitute for the final model. It is the controlled
research instrument we use before spending substantially more compute on a
full model.

## Objective

Produce a TypeScript coding student that is measurably better than the base
model on compiler- and test-verified tasks, while remaining small enough to
load, unload, and swap locally. Promotion requires 80% overall verification,
70% minimum in every task family, 60% on repository-derived repairs, no
general-coding regression, and reproducibility across two fixed evaluation
seeds.

## Data plan

The repository-grounded corpus builder is `scripts/build_typescript_usecase_corpus.py`.
It creates many deterministic task variants from real public TypeScript source,
with repository commit and source hashes attached. A stronger teacher may answer
the resulting JSONL offline or through an explicitly approved dataset-generation
service. The answers must then pass through
`scripts/ingest_verified_teacher_data.py`, which runs strict TypeScript
compilation and discards unverified answers before student training.

Raw volume is not enough. The target corpus is:

- 50,000–100,000 programmatic examples covering the skill matrix;
- 10,000–30,000 license-reviewed repository repair tasks;
- 5,000–10,000 teacher-generated candidates;
- 2,000–5,000 compiler-verified preference pairs;
- at least 2,000 held-out evaluation tasks never used for training.

The skill matrix includes generics, narrowing, mapped and conditional types,
overloads, async code, Node and DOM APIs, module resolution, tsconfig,
dependency upgrades, React/Next.js TypeScript, tests, monorepos, and compiler
version migrations.

Every repository task must preserve provenance, license, TypeScript version,
package manager, configuration, diagnostics, candidate patch, and independent
verification. A task is training truth only after `tsc --noEmit --strict` and,
where practical, project tests or builds pass.

## Teacher–student pipeline

The first pipeline is sequence-level distillation:

1. Create a broken or incomplete TypeScript task.
2. Ask a stronger local teacher for one or more repairs.
3. Extract code and discard unsupported prose.
4. Compile and test every candidate.
5. Keep verified repairs as chosen examples.
6. Preserve failed candidates and deliberately weakened repairs as rejected
   examples.
7. Train the student with supervised fine-tuning, then preference optimization.

This is not classical logit distillation because Ollama does not provide the
teacher token distributions needed for that objective. Later, run the teacher
with a training-oriented Transformers/vLLM stack and add a KL-divergence logit
loss if sequence-level distillation plateaus.

## Experiment matrix

Run identical data and held-out tasks across:

- Qwen2.5-Coder-0.5B LoRA: smallest swap candidate;
- 1.5B–3B QLoRA: likely quality/speed compromise;
- 7B reference: teacher and upper-quality baseline.

For each, compare clean SFT, longer SFT, higher-rank LoRA, and preference
optimization. Select by verified quality first, then latency and resident
memory. Do not select by training loss alone.

## Hardware plan

The RTX 5080 is sufficient for the current 0.5B experiments and likely for
1.5B–3B QLoRA with bounded context. A 48 GB rental is the next useful upgrade
for larger students, longer contexts, or simultaneous teacher/student work.
An 80 GB GPU is useful for 7B full fine-tuning or logit distillation, but is not
required yet. Cloud runs must use public or sanitized data; private repository
content remains local.

## Execution order

1. Finish the second fixed-seed evaluation of `typescript-v3-5000`.
2. Report per-family quality and verify the improvement is reproducible.
3. Expand verified repository repairs and multi-file tasks.
4. Build chosen/rejected preference pairs.
5. Train 0.5B, 1.5B/3B candidates with the same evaluation contract.
6. Run preference optimization from the best SFT candidate.
7. Merge and quantize only candidates that pass quality gates.
8. Benchmark Ollama cold load, warm load, swap latency, VRAM, and decode
   tok/s.
9. Add SQLCoder as a separate SQL physical model and verify router/lifecycle
   swapping without mixing its weights into TypeScript.
10. Repeat the data-and-verification process for React, Next.js, CSS, and
    Python specialists.

The current 0.5B adapter is an encouraging experiment, not a finished
specialist. Its latest result was 39/100 verified versus 28/100 for the base;
the next fixed-seed result determines whether that gain is real.
