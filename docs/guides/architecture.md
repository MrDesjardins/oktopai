# Architecture

`ExpertRegistry` loads logical experts from TOML. `Router` scores them deterministically from prompt words, file extension/path, imports, package dependencies, and repository config files. `LifecycleManager` maps logical experts to physical model identifiers and applies an LRU warm-model limit. `Session` stores conversation, files, repository facts, and expert history independently of any model. `OllamaRuntime` is the replaceable local-runtime adapter.

The CLI is intentionally thin. The router does not call a model, and the runtime never knows routing rules.

## State layers

- Immutable model weights: the model files managed by Ollama; they are not changed by a conversation.
- GPU/CPU residency: runtime-managed placement of those weights while a model is loaded.
- OS disk caching/memory mapping: the operating system may cache model pages after eviction; this is outside oktopai's control.
- KV-cache conversation state: model-specific attention state that can accelerate continuation, but is tied to architecture, weights, tokenizer, and exact context.
- Model-independent session state: oktopai's JSON messages/files/facts/history, used to reconstruct prompts after switching experts.

A KV cache normally cannot be reused across different models because its tensors encode that model's layers, dimensions, attention scheme, tokenizer interpretation, and prior token sequence. Reconstructing from the shared session is the portable boundary.

Ollama preload is implemented as an empty generation with `keep_alive`; unloading uses `keep_alive: 0`. This is a runtime request, not a promise that arbitrary GPU state can be serialized or restored.

## Extension points

Replace `Router` scoring with a learned classifier, add separate physical checkpoints or adapters to TOML, add predictive `ensure_warm` calls, then add retrieval and multi-expert verification without changing the session/runtime boundary.

The live Ollama integration test is intentionally opt-in with `OKTOPAI_LIVE_TESTS=1`; the default test suite uses fakes and never requires a daemon or model download.
