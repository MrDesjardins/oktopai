# oktopai

An experimental, local-only coding orchestrator. The MVP routes prompts to explainable logical experts, maps them to physical models, manages a small warm-model LRU, preserves model-independent session context, and records telemetry.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

No model or system dependency is downloaded by setup. Ollama is optional. If installed, start it with `ollama serve` and use an already-installed model; the example config uses `qwen2.5-coder:7b`, but edit `config/experts.toml` to match your inventory.

```bash
oktopai inspect
oktopai models
oktopai route "Fix this TypeScript generic" --file src/types.ts
oktopai ask "Fix this TypeScript generic" --file src/types.ts
oktopai benchmark
oktopai events
```

Use `oktopai preload "Why does this React component rerender?" --file src/App.tsx` to exercise predictive loading without generating text. Add `--live` to `benchmark` only when you want to generate against already-installed local models.

`route` works without a runtime. `ask` never falls back to a cloud provider and gives an actionable message when Ollama or the configured model is unavailable. The default session and events are stored under `.oktopai/`.

## Design

See [docs/architecture.md](docs/architecture.md), [docs/environment.md](docs/environment.md), and [docs/experiments.md](docs/experiments.md). Expert configuration is in [config/experts.toml](config/experts.toml).

The long-term specialization, distillation, artifact-registry, and hot-swapping strategy is documented in [docs/roadmap.md](docs/roadmap.md).

The complete documentation index is [docs/index.md](docs/index.md). The benchmark can be run with `PYTHONPATH=src python3 scripts/run_benchmark.py --route-only` or against installed local models with `--model` / `--all-installed`.

Local specialist packaging and training preparation:

```bash
PYTHONPATH=src python3 scripts/register_specialists.py
PYTHONPATH=src python3 scripts/prepare_training_data.py
PYTHONPATH=src python3 scripts/distill_plan.py --domain typescript
```

These commands create manifests and datasets only. They never download models or silently train.

Run offline tests with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
