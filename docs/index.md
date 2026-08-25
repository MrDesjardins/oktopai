# oktopai documentation

This directory is the project record. It documents both the working MVP and the longer-term research direction: a local fleet of small, specialized coding models that are hot-swapped through limited GPU memory.

## Start here

1. [Project overview](project.md) — what oktopai is and how the pieces fit.
2. [Architecture](architecture.md) — runtime, routing, lifecycle, context, and state boundaries.
3. [Roadmap](roadmap.md) — adapters, distillation, micro-experts, artifact registry, and multi-expert verification.
4. [Benchmark plan](benchmark.md) — task schema, verification levels, metrics, and reproducibility.
5. [Current status](status.md) — what has been implemented and what has been measured.

## Operations and research

- [Environment](environment.md) — machine and runtime findings.
- [Experiments](experiments.md) — completed runs and observations.
- [Local operations](operations.md) — safe commands for Ollama and oktopai.
- [Training and artifacts](training.md) — future dataset, adapter, distillation, and model-registry plan.
- [Preference training](preference-training.md) — verified pairs and DPO experiments.
- [Speed and quality plan](speed-quality-plan.md) — the verified-data, distillation, and optimization program for reliable small experts.
- [Experiment ledger](experiment-ledger.md) — append-only measurements and provenance for every run.
- [Build and training status](build.md) — what can run now and what requires additional toolchains.
- [Architecture decisions](decisions.md) — explicit tradeoffs and rejected shortcuts.

## Privacy boundary

The system is local-only. Repository content is sent only to the configured local runtime. No cloud fallback is implemented. Model artifacts may eventually be obtained from a registry, but installation must be explicit and separate from coding requests.
