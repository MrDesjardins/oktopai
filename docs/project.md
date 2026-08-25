# Project overview

## Mission

oktopai aims to make limited local hardware broadly useful for coding by composing narrow experts instead of demanding one enormous general model.

The system treats GPU memory as a working set:

```text
repository + prompt
        ↓
explainable router
        ↓
logical expert
        ↓
physical model or adapter
        ↓
load/reuse/evict policy
        ↓
local response + verification evidence
```

## Current MVP

The MVP uses Python 3 and a dependency-light design. It contains:

- TOML expert registry;
- deterministic router;
- repository signal detector;
- runtime protocol;
- Ollama adapter;
- model lifecycle manager;
- JSON model-independent sessions;
- JSONL telemetry;
- benchmark dataset and runner;
- optional local integration test.

The initial logical experts are general coding, TypeScript, React, Next.js, and testing. They now use five local Ollama aliases built from the same `qwen2.5-coder:7b` base with specialist system prompts. This proves packaging and routing, but does not yet prove learned specialization.

## Important distinction

Routing accuracy is not coding quality. A router can choose the correct domain while the model gives an incorrect answer. The benchmark therefore stores routing results, raw model output, latency, and verification results separately.

The long-term research question is:

> Can a collection of small domain specialists deliver higher verified coding success per GiB of GPU memory than one general local model?

## Repository layout

```text
config/experts.toml              logical expert registry
benchmarks/tasks.json             versioned benchmark corpus
scripts/run_benchmark.py         reproducible benchmark runner
scripts/compare_installed_models.py  installed-model comparison
src/oktopai/                      application package
tests/                            offline and opt-in integration tests
docs/                             project record and research plan
.oktopai/                         local generated artifacts, ignored by git
```

## Non-goals for the current iteration

- cloud APIs or remote fallback;
- automatic model downloads;
- embeddings or vector databases;
- training during coding requests;
- a graphical interface;
- claims that one model is better without executable or human evaluation.
