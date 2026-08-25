# oktopai documentation

This directory is the project record. It documents both the working MVP and the longer-term research direction: a local fleet of small, specialized coding models that are hot-swapped through limited GPU memory.

## Start here

1. [Project overview](research/project.md) — what oktopai is and how the pieces fit.
2. [Architecture](guides/architecture.md) — runtime, routing, lifecycle, context, and state boundaries.
3. [Roadmap](active/roadmap.md) — adapters, distillation, micro-experts, artifact registry, and multi-expert verification.
4. [Benchmark plan](guides/benchmark.md) — task schema, verification levels, metrics, and reproducibility.
5. [Current status](active/status.md) — what has been implemented and what has been measured.

## Operations and research

- [Environment](operations/environment.md) — machine and runtime findings.
- [Local operations](operations/operations.md) — safe commands for Ollama and oktopai.
- [Build and training status](operations/build.md) — what can run now and what requires additional toolchains.
- [Experiments](research/experiments.md) — completed runs and observations.
- [Experiment ledger](research/experiment-ledger.md) — append-only measurements and provenance for every run.
- [Architecture decisions](research/decisions.md) — explicit tradeoffs and rejected shortcuts.
- [Training and artifacts](guides/training.md) — future dataset, adapter, distillation, and model-registry plan.
- [Preference training](guides/preference-training.md) — verified pairs and DPO experiments.
- [TypeScript specialist plan](active/typescript-specialist-plan.md) — teacher–student data, LoRA versus full-model training, evaluation, and hardware strategy.
- [Speed and quality plan](active/speed-quality-plan.md) — the verified-data, distillation, and optimization program for reliable small experts.

## Archived

- [Overnight TypeScript plan](archived/overnight-typescript-plan.md) — completed overnight execution plan retained for historical context.

## Privacy boundary

The system is local-only. Repository content is sent only to the configured local runtime. No cloud fallback is implemented. Model artifacts may eventually be obtained from a registry, but installation must be explicit and separate from coding requests.
