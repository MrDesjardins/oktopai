# Training, specialization, and artifact plan

## Why training is separate

Normal oktopai operation routes and invokes models. Training is a separate reproducible pipeline that produces an adapter or checkpoint plus evidence. Training must never happen implicitly during a coding request.

```text
dataset → train adapter/student → evaluate → package artifact → install explicitly → route locally
```

## Recommended sequence

1. Shared base plus expert prompts.
2. Curated specialist examples and executable evaluators.
3. LoRA/QLoRA adapters on a common base.
4. Execution-guided teacher traces.
5. Distilled 1–3B micro-experts for narrow domains.
6. Full independent checkpoints only when their memory/load benefits justify the maintenance cost.

## Specialist data

Training data should include compiler failures, minimal reproductions, migration examples, test failures, corrected patches, explanations, and hard negatives. Every item needs provenance, license, framework/language version, and a held-out evaluation family.

The strongest early data source is likely execution-guided repair:

```text
teacher candidate patch
        ↓
compiler/test execution
        ↓
retain passing fixes and useful failure explanations
        ↓
train adapter or student
```

## Distillation target

The objective is not a tiny general model. It is a small student optimized for a narrow task distribution, with a smaller memory footprint and faster load time.

Candidate first students:

- TypeScript repair and type diagnostics;
- testing and test repair;
- SQL correctness;
- Next.js server/client boundaries.

Students must be compared against both the shared qwen baseline and an adapter variant.

## Versioning

Do not create a model for every TypeScript or Next.js release by default. Experts should target durable concepts and declare tested compatibility ranges. Version-specific adapters are justified only after a version-specific evaluation suite demonstrates a real gap.

## Artifact manifest

Every artifact should record:

- immutable artifact name and version;
- base-model digest;
- adapter or checkpoint digest;
- quantization;
- runtime compatibility;
- memory requirement;
- expected load time;
- supported versions;
- evaluation results;
- training data provenance and license;
- checksum and signature.

Future commands:

```text
oktopai artifacts list
oktopai artifacts install typescript-student-3b:q4
oktopai artifacts verify typescript-student-3b:q4
```

Installation must be explicit. Coding requests must never silently download artifacts.

## Current local pipeline

Prepare verified benchmark outputs:

```bash
PYTHONPATH=src python3 scripts/prepare_training_data.py
```

Include fixture-contract outputs only when deliberately accepted as weaker evidence:

```bash
PYTHONPATH=src python3 scripts/prepare_training_data.py --include-fixture
```

Create a domain-specific plan without training:

```bash
PYTHONPATH=src python3 scripts/distill_plan.py --domain typescript
```

The plan records candidate count, detected training executables, base model, student target, and required evaluation steps. It is intentionally a preparation artifact rather than a fake training result.

## Training stack provisioning

Inspect the installation without changing the machine:

```bash
python3 scripts/install_training_stack.py
```

Install into the repository-local `.venv-training` only after reviewing the package and storage impact:

```bash
python3 scripts/install_training_stack.py --install
```

Training data is built from the seed corpus and verified benchmark artifacts:

```bash
PYTHONPATH=src python3 scripts/build_specialist_dataset.py --domain typescript
PYTHONPATH=src python3 scripts/build_specialist_dataset.py --domain nextjs --include-benchmark
```

The first training entrypoint is:

```bash
python3 scripts/train_lora.py --data .oktopai/datasets/typescript.jsonl --base-model /path/to/local/base --output .oktopai/adapters/typescript-v1
python3 scripts/train_lora.py --data .oktopai/datasets/typescript.jsonl --base-model /path/to/local/base --output .oktopai/adapters/typescript-v1 --train
```

The first command is a dry run. The second requires the optional stack and a local Transformers-compatible base model; an Ollama model name is not automatically converted into training weights.

The training entrypoint uses the dataset's explicit `split` field: only `train` records update weights, while `validation` records are evaluated after each epoch. The first adapter run used 5 train records and 3 validation records for 2 epochs, with final training loss 1.53 and validation loss 1.455. These are optimization diagnostics, not a coding-quality claim.

The v3 trainer now uses the tokenizer's chat template and completion-only labels by default. Prompt tokens are masked with `-100`, and dynamic padding avoids wasting CPU time on 2,048-token rows. Use `--loss-mode full` only for an explicit ablation.

The first v3 run used the strictly TypeScript-filtered 14-record dataset (10 train, 4 validation) for 2 epochs. It completed with training loss 0.879 and validation loss 1.066. A two-task executable comparison still had the adapter failing the generic task and passing the narrowing task; this is an objective-pipeline validation, not yet a quality win.

Generate a large compiler-verified synthetic corpus:

```bash
python3 scripts/generate_typescript_synthetic.py \
  --count 10000 --version typescript-synthetic-v2 \
  --output .oktopai/datasets/typescript-synthetic-v2.jsonl --verify
PYTHONPATH=src python3 scripts/build_specialist_dataset.py \
  --domain typescript --name typescript-v5 \
  --include-synthetic --synthetic .oktopai/datasets/typescript-synthetic-v2.jsonl \
  --include-teacher --include-benchmark
```

The generated corpus contains 10,000 records across ten families and passed local `tsc --noEmit --strict --target ES2020` verification. The combined v5 dataset contains 10,014 records: 7,537 train, 1,497 validation, and 980 test. Programmatic records are deliberately labeled as synthetic; they must be complemented by license-reviewed repository tasks and independently verified teacher traces before a quality claim.

The bounded v4 run consumed 100 optimizer steps from the large corpus in 8 minutes 45 seconds on CPU, including validation. It reached training loss 0.796 and validation loss 0.400. A two-task executable check still failed the generic and narrowing tasks, so v4 is not exported or promoted. A full pass over 7,537 training records is estimated at roughly 50 minutes before evaluation on this machine; use `--max-steps -1` only as an intentional long-running experiment.

Teacher data can now be generated from synthetic prompts and independently filtered. The first local batch generated 25 traces from the 7B TypeScript specialist; 13 passed extracted-code TypeScript compilation and were added to the 10,000-record foundation. Rejected traces remain outside training data.

```bash
.venv-training/bin/python scripts/train_lora.py \
  --data .oktopai/datasets/typescript-v3.jsonl \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --output .oktopai/adapters/typescript-v3 --train \
  --loss-mode completion-only
```

Compare the local base and adapter. When the fixture's local TypeScript compiler is present, the command performs an actual `tsc --noEmit --strict` check on extracted code blocks:

```bash
HF_HOME=.oktopai/hf-cache .venv-training/bin/python scripts/evaluate_adapter.py \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --adapter .oktopai/adapters/typescript-v1 \
  --max-tasks 2
```

Package provenance and checksums:

```bash
.venv-training/bin/python scripts/package_adapter.py \
  --adapter .oktopai/adapters/typescript-v1 \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --domain typescript --dataset .oktopai/datasets/typescript.jsonl \
  --evaluation .oktopai/adapter-evaluation-typescript.json
```

Generate raw teacher traces locally from the installed specialist aliases:

```bash
PYTHONPATH=src python3 scripts/generate_teacher_data.py --domain typescript
PYTHONPATH=src python3 scripts/build_specialist_dataset.py --domain typescript --include-teacher --include-benchmark
```

Teacher traces remain `candidate` data until they pass the benchmark or human review. This prevents the model from teaching its own unverified mistakes back to the student.

## Base-model requirement

The Ollama qwen model is stored as a GGUF runtime artifact. Transformers/PEFT training expects a local Hugging Face-style checkpoint directory containing configuration, tokenizer, and model weight files.

```text
Ollama GGUF → inference and hot-swapping
HF checkpoint → LoRA/QLoRA training
trained adapter → package/export → Ollama Modelfile
```

The next training command must use a local HF-compatible coding base, such as a deliberately downloaded small Qwen coder checkpoint or another licensed small coding model. The repository does not silently download that checkpoint.

The resulting PEFT adapter is not currently Ollama-compatible. It targets the 0.5B Transformers checkpoint and must not be attached to the separate 7B Ollama GGUF model. An exact-lineage merge/export experiment is required before registering it as a hot-swappable runtime artifact.

### Merge and runtime export experiment

The adapter can be merged into a standalone Transformers checkpoint without downloading anything:

```bash
.venv-training/bin/python scripts/merge_lora.py \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --adapter .oktopai/adapters/typescript-v1 \
  --output .oktopai/merged/typescript-v1 --merge
```

The merged checkpoint loaded and generated successfully through Transformers. Ollama 0.17.2's experimental Safetensors quantizer crashed in its MLX path on this WSL machine. llama.cpp was then built locally, converted the checkpoint to a 380 MB Q4_K_M GGUF, and Ollama registered it successfully as `oktopai-typescript-trained-q4`. A local inference request completed. Portability is proven; specialist quality is not: the first response still produced an invalid generic fix.

The artifact is exposed as `typescript-trained` with low default priority so the prompt-specialized baseline remains comparable. Select it explicitly with `oktopai ask --expert typescript-trained "..."`.

The controlled downloader defaults to a small Qwen coder checkpoint:

```bash
python3 scripts/download_training_base.py
.venv-training/bin/python scripts/download_training_base.py --download
```

Review the model license and expected 1–3 GB disk/network impact before using `--download`. Then train:

```bash
.venv-training/bin/python scripts/train_lora.py \
  --data .oktopai/datasets/typescript.jsonl \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --output .oktopai/adapters/typescript-v1 \
  --train
```

The v5 large-corpus experiment trained 150 steps with completion-only masking and no mid-run evaluation in 8 minutes 3 seconds on CPU, reaching training loss 0.559. The two-task executable check still failed both real TypeScript tasks, so the artifact remains unexported. A later 400-step continuation was stopped at step 162 after CPU step time increased sharply from about 3 seconds to 6–7 seconds; this exposes the need for resource-aware training schedules rather than blindly increasing epochs.
