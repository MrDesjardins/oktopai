# Build status and execution boundary

## Fully implemented locally

- Local Ollama discovery and generation.
- Explainable routing.
- Shared-session reconstruction.
- Runtime lifecycle events and loaded-model detection.
- LRU design and configurable per-command warm capacity.
- Versioned benchmark corpus.
- Route-only and live benchmark runners.
- SQL and Python executable validators.
- Fixture-contract validators for JavaScript-family tasks.
- Specialist Modelfiles using the installed qwen2.5-coder base.
- Local artifact manifest registration.
- Verified-data extraction for future training.
- Distillation-plan generation.
- Next.js/TypeScript fixture benchmark with single-model and swapped-specialist modes.
- Token-count and tokens-per-second capture from Ollama responses.
- Local teacher-trace generation with provenance and candidate labeling.

## Safe commands

```bash
PYTHONPATH=src python3 scripts/register_specialists.py
PYTHONPATH=src python3 scripts/prepare_training_data.py
PYTHONPATH=src python3 scripts/distill_plan.py --domain typescript
```

## What cannot honestly be completed without new prerequisites

Training a genuinely distilled or LoRA-specialized model requires:

- a larger, licensed specialist dataset;
- a training framework such as PyTorch/Transformers, Unsloth, or MLX;
- enough disk and memory for the base model and optimizer/checkpoint state;
- a held-out executable evaluation set;
- explicit decisions about model licenses and artifact hosting.

The training stack is now installed in the ignored repository-local `.venv-training`, with PyTorch 2.13.0, Transformers 5.15.1, Datasets 5.0.1, PEFT 0.20.0, Accelerate 1.14.0, and TRL 1.10.0. CUDA is not available to PyTorch in this WSL environment, so training is CPU-bound until GPU access is configured. No base training model was downloaded.

`scripts/download_training_base.py` provides the explicit, opt-in path to a small Transformers-compatible base checkpoint.

The Next.js fixture is now installed locally with Next.js 16.3.2 and reports zero npm vulnerabilities. Use `scripts/run_nextjs_benchmark.py --install --build` for isolated temporary builds; dependency installation may download hundreds of megabytes.

## Model lifecycle boundary

Ollama remains the resident model server. oktopai records logical expert usage and asks Ollama to preload/unload physical models. A future long-running oktopai daemon is still needed to preserve a single in-process LRU across all client requests; Ollama's `/api/ps` state is already queried across CLI processes.
