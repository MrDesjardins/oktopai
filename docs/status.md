# Current status

Last updated after the first live local-model experiments.

## Working

- Ollama runtime discovery and model listing.
- Local generation with `qwen2.5-coder:7b`.
- Five local prompt-specialized Ollama aliases created from the qwen2.5-coder base.
- Repository-local training stack installed and import-verified; PyTorch reports CUDA unavailable.
- A real TypeScript LoRA adapter was trained locally from `Qwen/Qwen2.5-Coder-0.5B-Instruct`; its manifest and checksums are in `.oktopai/adapters/typescript-v1/manifest.json`.
- The adapter was merged into a standalone Transformers checkpoint and loaded successfully; Ollama Safetensors quantization was tested but crashed in Ollama's MLX path, so no trained Ollama model was created.
- llama.cpp was built locally, the merged checkpoint was exported to a 380 MB Q4_K_M GGUF, registered in Ollama as `oktopai-typescript-trained-q4`, and exercised with a local inference request.
- The two-model benchmark measured the 397 MB trained model at approximately 608 tokens/second and 0.80 seconds/task versus 148 tokens/second and 2.32 seconds/task for the 4.7 GB prompt-specialized model; quality was 7 failures versus 1 failure across the eight-task set.
- The v2 failure-focused dataset contains 17 records and produced a registered `oktopai-typescript-trained-v2-q4` artifact. The three-way benchmark showed no quality improvement over v1: both trained versions had 7 failures and 1 checklist pass.
- v3 now uses strict TypeScript dataset filtering, chat-template formatting, completion-only loss masking, and dynamic padding. The first 14-record v3 run completed with training loss 0.879 and validation loss 1.066; its two-task check still failed generics and passed narrowing.
- Next.js 16.3.2 benchmark fixture installed with zero npm audit vulnerabilities.
- Deterministic routing without a runtime.
- Shared logical experts mapped to one physical model.
- Cross-process detection of Ollama's loaded model state.
- Preload, keep-alive, unload, and lifecycle telemetry.
- Session reconstruction with bounded context.
- Versioned benchmark task corpus.
- Route-only and live benchmark runners.
- Raw output and timing persistence.
- Checklist and Python compilation verification.

## Measured

- qwen2.5-coder:7b generated the initial five-case benchmark in roughly 0.4–7.4 seconds per response.
- Installed larger models showed substantial cold-load and memory costs.
- Routing accuracy on the initial synthetic set was 100%; this set is too small to claim router quality generally.
- A repository review exposed a concrete hallucinated fix, proving the need for executable verification.
- The first versioned eight-task benchmark routed 8/8 tasks correctly after adding file/import context.
- The updated live qwen2.5-coder:7b run produced 4 fixture-contract passes, 2 executable verification passes (SQL and Python), 1 checklist pass, and 1 failed TypeScript check.
- Live generation times for the eight tasks ranged from approximately 1.25 to 3.84 seconds; routing took approximately 0.6 ms.

## Not yet proven

- A distilled specialist outperforming the shared qwen baseline.
- A LoRA adapter outperforming prompt specialization.
- Reliable two-model simultaneous residency on this WSL environment.
- GPU VRAM capacity; `nvidia-smi` is blocked in the current environment.
- TypeScript, React, Next.js, and Vitest tasks passing real project-toolchain validators.
- The current TypeScript/React/Next.js/Vitest fixture contracts are not full compiler or runtime tests; installing project-local tools or adding hermetic tool containers is the next verification step.
- A persistent oktopai daemon with lifecycle state across requests.
- A learned adapter outperforming prompt specialization. Executable held-out evaluation shows both base and adapter passing narrowing and failing the generic task, with approximately equal throughput (~30 tokens/second).
- An Ollama-loadable export of the adapter. The PEFT artifact is tied to the 0.5B Transformers base, while active Ollama aliases use a separate 7B GGUF lineage.
- A trained specialist outperforming the prompt-specialized baseline. The exported model runs, but its first generic response was still invalid; quality remains unproven.
- A compiler-verified 10,000-record synthetic TypeScript corpus now exists across ten families. The combined v5 corpus contains 10,014 records: 7,537 train, 1,497 validation, and 980 test. This is data expansion only; no quality claim is made until a trained artifact passes the held-out suite.
- A bounded v4 training run used 100 optimizer steps from the 10k corpus in 8m45s on CPU, reaching training loss 0.796 and validation loss 0.400. Its two-task executable check still failed, so v4 is not exported or promoted.
- A local teacher batch generated 25 TypeScript traces from the 7B specialist; 13 passed extracted-code compilation and were added to the 10,000-record foundation, producing a 10,024-record v6 corpus.
- A v5 large-corpus adapter trained 150 steps with completion-only masking in 8m03s on CPU, reaching training loss 0.559; it still failed both initial real TypeScript checks and was not exported. A 400-step continuation was stopped at step 162 after CPU slowdown made the run inefficient.

## Next milestones

1. Expand executable TypeScript fixture coverage beyond the current two-file repair.
2. Create the first specialist dataset from verified failures and fixes.
3. Add hermetic TypeScript/React/Next.js/Vitest toolchain fixtures.
4. Expand the TypeScript dataset beyond the current seed/candidate count.
5. Run executable held-out evaluation for the 0.5B base and adapter.
6. Add license-reviewed repository tasks and compiler-filtered teacher traces to the 10k synthetic foundation.
7. Run a full one-pass training experiment on the large corpus with controlled CPU/GPU resource measurement and evaluate the 980-record test split.
8. Export and benchmark the best TypeScript artifact before starting CSS, React, or Next.js corpora.
9. Distill a narrow TypeScript micro-expert and measure capability per GiB.
## Latest research run (2026-08-24/25)

- Added an append-only JSONL experiment ledger at `experiments/runs.jsonl` and
  documented its measurement policy in `docs/experiment-ledger.md`.
- Downloaded a shallow public `microsoft/TypeScript` checkout locally at commit
  `8ac035a394c79e693a3a7d74cb170448503ee894`; the manifest records 65,905 files
  and license files. Raw source is kept separate from training truth.
- Extracted 1,000 compiler-conformance candidates. A local teacher generated
  100 traces; 25 passed the independent `tsc --strict` filter and 75 were
  rejected. The resulting v7 corpus has 10,036 records.
- Trained `typescript-v7` with completion-only loss for 300 optimizer steps on
  CPU: 967.1 seconds, 0.31 steps/sec, reported training loss 0.372.
- The current two-task executable held-out gate remains failed for both base
  and adapter outputs. v7 is therefore not exported or promoted. This is a
  quality result, not a reason to claim specialization: the next work is a
  larger held-out task suite and better teacher/label filtering.
- The generated benchmark now contains 3,000 TypeScript tasks. A randomized
  20-task v7 evaluation produced 8/20 compiler-verified responses for both the
  base and adapter, with average verification score 0.45. Average generation
  speed was 27.74 tok/s for the base and 27.83 tok/s for the adapter. The
  adapter remains unpromoted because it is not measurably better.
- `train_lora.py` now supports `--device auto|cpu|cuda`, resumable checkpoints
  with `--resume`, and step-based checkpoint retention. CUDA explicitly fails
  with an actionable error when the host does not expose a device.
- GPU passthrough was verified with local runtime access: WSL exposes
  `/dev/dxg`, CUDA 13.2, and an NVIDIA GeForce RTX 5080 with 15.92 GiB VRAM;
  PyTorch reports CUDA available. The v8 1,000-step run completed in 685.4
  seconds at 1.459 steps/sec with loss 0.2339, versus 0.31 steps/sec for the
  earlier CPU run.
- Added 3,000 deterministic preference candidates; 1,785 passed family-level
  compiler verification and are stored locally for preference-training work.
  Added a strictly test-split 980-task benchmark. On a randomized 20-task CUDA
  sample, both base and v8 verified 1/20 with average score 0.208, so v8 is not
  promoted.
