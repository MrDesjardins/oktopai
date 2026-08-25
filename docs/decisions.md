# Architecture decisions

## TOML instead of YAML

TOML is available through Python's standard library on supported versions, so the registry does not need an external parser dependency.

## Ollama first, behind an interface

Ollama is installed on the target machine and exposes preload, keep-alive, generation, and unload behavior. The runtime protocol isolates those details so llama.cpp, MLX, or another backend can be added later.

## Shared session instead of KV-cache transfer

KV caches are model-specific tensors and normally cannot be reused across different models. oktopai stores messages, files, repository facts, and expert history, then reconstructs the prompt after a swap.

## Deterministic routing before learned routing

An explainable baseline is required before adding a learned router. Otherwise routing errors become difficult to separate from model errors.

## Adapters before independent checkpoints, but distillation remains a primary goal

Adapters reduce the first specialization experiment's cost and preserve a shared base. Distilled micro-experts remain a core roadmap item because the ultimate target is lower memory and faster swapping, not merely different prompts.

## No automatic downloads

Model downloads are large and affect privacy, storage, and reproducibility. Installation must be explicit.

## Verification before quality claims

The benchmark reports raw outputs and evidence levels. A textual checklist is not treated as proof of correctness. Executable validators and human review are future additions where a domain cannot yet be checked automatically.
