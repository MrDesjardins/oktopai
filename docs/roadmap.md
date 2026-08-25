# oktopai Roadmap: Local Power Through Specialization and Hot-Swapping

## Vision

oktopai is an experiment in making a small local machine feel like a much larger coding system.

The goal is not to find one local model that competes with every frontier model at every task. The goal is to compose a collection of very small, very capable specialists and move them through limited GPU memory as needed:

```text
large problem space
        │
        ▼
explainable task router
        │
        ├── TypeScript specialist
        ├── React specialist
        ├── Next.js specialist
        ├── SQL specialist
        ├── testing specialist
        ├── debugging specialist
        └── general coding specialist
        │
        ▼
small active model in GPU memory
```

The central hypothesis is:

> A small model trained or adapted for one narrow coding domain can outperform a much larger general local model on that domain, while hot-swapping allows a machine with limited GPU memory to access many specialists over time.

This is a hypothesis to measure, not an assumption to claim.

## What makes the approach novel

The unit of capability is not one model. It is a composed local system:

```text
capability = router
           + specialist model or adapter
           + repository/version context
           + lifecycle policy
           + evaluation evidence
```

The GPU is treated as a working set rather than a permanent home for every model. Inactive specialists can be unloaded while their immutable weights remain available through CPU memory, disk caching, or the runtime's model store.

This creates a practical alternative to choosing between:

- one weak general-purpose local model; or
- one large model that exceeds the machine's memory budget.

The intended user experience is a local coding system that feels broad because it is a coordinated fleet of narrow experts, while each individual active expert remains small enough to load quickly.

## Design principles

1. **Specialization must be earned by evaluation.** A specialist is promoted only when it beats the shared baseline on a fixed task suite.
2. **Adapters before full checkpoints.** LoRA/QLoRA adapters are the first specialization mechanism; full distilled checkpoints are pursued when smaller latency or memory footprints justify them.
3. **Distillation is a first-class target.** The project will explicitly investigate teacher-to-student distillation rather than treating it as an optional future idea.
4. **Hot-swapping is part of model quality.** A model that is marginally better but too slow to load may be worse in the composed system than a slightly smaller specialist.
5. **Version awareness belongs in the expert contract.** Experts target durable concepts but declare tested language/framework version ranges.
6. **No cloud fallback.** Repository content stays local and missing local capability is reported rather than silently sent elsewhere.
7. **Every claim has a benchmark.** We measure task success, latency, memory, load frequency, and residency—not only subjective output quality.

## Phase 0 — Prove the orchestration loop

Status: **in progress**

The current MVP establishes:

- TOML expert registry;
- deterministic, explainable routing;
- logical experts mapped to physical models;
- Ollama runtime abstraction;
- preload, keep-alive, unload, and LRU lifecycle operations;
- model-independent session context;
- structured lifecycle telemetry;
- offline benchmark cases;
- optional live runtime tests.

Immediate completion work:

- run the first live benchmark with the installed qwen model; **completed for the initial and versioned task sets**;
- build a versioned benchmark corpus with executable verification; **initial corpus and runner completed**;
- measure cold start, warm start, generation, and time-to-first-response;
- expose `max_warm_models` in configuration and CLI;
- verify two distinct physical models can remain warm when memory permits;
- add a long-running oktopai daemon so lifecycle state is not recreated for every CLI invocation.

Exit criteria:

- one local model answers coding prompts;
- routing works without a model;
- switching experts produces observable lifecycle events;
- two logical experts sharing one physical model do not reload weights;
- raw outputs and timings are reproducible from a saved benchmark run.

## Phase 1 — Establish the shared-model baseline

Before training anything, build a strong baseline using one local coding model and expert-specific prompting.

Create a versioned benchmark corpus with:

- TypeScript compiler errors and generic-type tasks;
- React rendering and hook behavior;
- Next.js server/client and routing issues;
- SQL query correction and schema reasoning;
- test generation and test repair;
- debugging from stack traces;
- general refactoring.

Each task should include:

- repository snapshot or minimal fixture;
- language/framework versions;
- expected behavior;
- executable tests where possible;
- difficulty level;
- privacy and license metadata.

Measure:

- compile/test pass rate;
- exact or semantic correctness;
- unnecessary-change rate;
- routing accuracy;
- time to first token;
- total response time;
- model load time;
- resident memory;
- tokens per second;
- context length used.

Exit criteria:

- a reproducible baseline exists;
- each expert has at least 25–100 labeled tasks;
- specialization decisions are based on measured failure patterns.

## Phase 2 — Build specialist datasets, not merely specialist prompts

The most important training asset will be the dataset and evaluator, not the first model checkpoint.

For each domain, build a specialist data pipeline:

```text
source examples
    → normalize
    → remove secrets and duplicates
    → attach version metadata
    → generate hard negatives
    → split by repository/task family
    → train adapter or student
    → run executable evaluation
```

Potential data sources:

- permissively licensed repositories;
- synthetic tasks generated from compiler and test failures;
- documented migration examples;
- local repository tasks with explicit permission;
- hand-authored expert demonstrations;
- automatically minimized failing examples.

Avoid training on raw repository contents without consent. The data pipeline must preserve provenance and license information.

Specialist datasets should emphasize failure modes that general models miss:

- TypeScript: inference traps, variance, generics, narrowing, module resolution, compiler flags;
- React: stale closures, effects, memoization, rendering identity, accessibility;
- Next.js: server/client boundaries, caching, route handlers, streaming, version migrations;
- testing: flaky tests, fixtures, isolation, mocking boundaries, test repair;
- SQL: joins, null semantics, indexes, query plans, dialect differences.

## Phase 3 — Adapter specialists

Train the first specialists as LoRA or QLoRA adapters on a common base model.

```text
base model + TypeScript adapter → TypeScript expert
base model + Next.js adapter     → Next.js expert
base model + testing adapter     → testing expert
```

Why adapters first:

- lower training cost;
- smaller artifacts;
- common tokenizer and base behavior;
- easier A/B testing;
- potential to share immutable base weights;
- clean rollback when an adapter regresses general coding.

Each adapter must record:

- exact base model identifier and digest;
- training framework and configuration;
- dataset manifest;
- supported runtime;
- quantization status;
- compatible language/framework versions;
- benchmark results;
- license and provenance.

The runtime registry should treat an adapter as a physical capability variant, not as an unrelated expert with missing lineage.

## Phase 4 — Distilled micro-experts

Distillation is a core research track for oktopai.

The objective is not simply to make a smaller copy of a general model. It is to create a student optimized for a narrow task distribution:

```text
teacher(s)
  ├── frontier-quality coding traces
  ├── verified reference solutions
  └── specialist demonstrations
          │
          ▼
task-specific student
  ├── smaller parameter count
  ├── lower context and memory requirements
  ├── faster load time
  └── measurable skill on one domain
```

Possible distillation targets:

- a 1–3B TypeScript repair model;
- a 1–3B testing model;
- a 1–3B SQL model;
- a 3–7B Next.js model if the framework reasoning requires more capacity;
- specialized small verifier models for compile/test review.

Distillation experiments should compare:

1. shared base model with a system prompt;
2. shared base model with an adapter;
3. distilled specialist of similar memory size;
4. larger general model where available.

The result must be judged by capability per memory and capability per second, not parameter count alone.

Important distillation variants:

- response distillation from teacher answers;
- preference distillation using verified versus flawed patches;
- execution-guided distillation using compiler/test results;
- tool-use distillation for shell, compiler, and test workflows;
- intermediate-reasoning distillation only where licensing and safety permit;
- verifier-guided rejection sampling.

The strongest early opportunity is likely execution-guided distillation: generate candidate fixes, compile or test them, and retain solutions that actually work.

## Phase 5 — Version-aware expert fleet

Do not create one model for every TypeScript or Next.js release by default.

Instead, maintain:

```text
durable specialist skill
        + detected repository version
        + version-specific documentation
        + compatibility tests
        + migration examples
```

Create a version-specific adapter or distilled model only when:

- behavior changed materially between versions;
- the general specialist fails a version-specific suite;
- the version has enough usage to justify maintenance;
- the artifact provides a measurable improvement.

Experts should declare compatibility ranges and evaluation coverage, for example:

```toml
name = "nextjs"
model = "oktopai-nextjs-student-3b:q4"
compatible_versions = [">=14,<16"]
evaluation_suite = "nextjs-boundaries-v3"
artifact_digest = "sha256:..."
```

## Phase 6 — Hot-swapping as a scheduling problem

Once multiple real specialists exist, lifecycle management becomes a scheduling and caching problem.

Track:

- model or adapter load time;
- GPU memory consumed;
- CPU memory consumed;
- disk footprint;
- generation throughput;
- recent usage;
- predicted next expert;
- switching frequency;
- task urgency;
- model quality for the current task.

The lifecycle policy should support:

- one active specialist for minimum memory;
- two or more warm specialists when capacity allows;
- LRU eviction;
- cost-aware eviction;
- predictive preload from the next file or command;
- hysteresis to prevent rapid swapping;
- a deadline-aware choice between waiting for a better expert and using a warm fallback;
- shared-base and adapter-aware residency accounting.

Example policy:

```text
current: TypeScript expert
next predicted: testing expert
available GPU memory: enough for one specialist

1. keep TypeScript warm while its response is active
2. save model-independent session state
3. unload TypeScript
4. preload testing specialist
5. reconstruct context from the shared session
6. generate and record transition cost
```

The system should eventually optimize not just response quality, but expected user-perceived latency:

```text
utility = task_quality
        - cold_start_penalty
        - swap_penalty
        - memory_pressure_penalty
```

## Phase 7 — Model artifact registry

The fleet will eventually need a registry for models and adapters.

Every artifact should be immutable and addressable by digest. A manifest should include:

- artifact name and version;
- base model and digest;
- adapter or full checkpoint;
- quantization;
- runtime compatibility;
- memory requirements;
- expected load time;
- supported domain and versions;
- benchmark results;
- dataset and license provenance;
- creation date;
- checksum;
- security/signature metadata.

Possible storage backends:

- local filesystem for experiments;
- private object storage;
- private Hugging Face repository;
- OCI-compatible artifact registry;
- eventually a public model catalog for reproducible specialists.

oktopai should never silently download an artifact during a coding request. Model installation should be explicit:

```text
oktopai artifacts list
oktopai artifacts install typescript-student-3b:q4
oktopai artifacts verify typescript-student-3b:q4
```

## Phase 8 — Multi-expert verification

A single specialist should not always be trusted.

For difficult tasks, oktopai can use a staged local workflow:

```text
primary expert → proposed patch
       │
       ▼
compiler/test verifier
       │
       ├── pass → return result
       └── fail → repair or ask a second specialist
```

Examples:

- TypeScript expert proposes a patch; compiler verifier checks it.
- Next.js expert proposes a server/client change; framework fixture tests it.
- SQL expert proposes a query; schema fixtures and query-plan checks verify it.
- Testing expert proposes tests; the test suite checks whether they actually fail before the fix and pass afterward.

This is how a fleet of modest models can become more reliable than any single model.

## Success metrics

The project succeeds if it demonstrates all of the following on constrained hardware:

1. A small specialist beats the shared general model on its target task suite.
2. The specialist loads within a practical interactive latency budget.
3. Several specialists can be installed without requiring all of them to occupy GPU memory simultaneously.
4. Hot-swapping preserves useful conversation and repository context.
5. The total system provides broader useful coding coverage than any one local model.
6. Quality, memory, load time, and switching costs are measured together.
7. Results are reproducible from versioned artifacts and benchmark datasets.

The key headline metric should be:

```text
verified task success per GiB of GPU memory
```

Secondary metrics:

- verified task success per second;
- cold-start and warm-start latency;
- percentage of requests served by a warm model;
- average number of swaps per session;
- quality loss after context reconstruction;
- percentage of generated patches that pass tests;
- storage required for the complete expert fleet.

## Immediate next experiments

1. Finish pulling qwen2.5-coder and run the live baseline benchmark.
2. Add a second small installed model only after measuring the first model's memory and latency.
3. Implement `max_warm_models=2` and a persistent oktopai daemon.
4. Build the first executable TypeScript benchmark from compiler-error fixtures.
5. Create a tiny TypeScript adapter dataset and compare prompt-only versus adapter performance.
6. Prototype execution-guided teacher traces for TypeScript repair.
7. Distill a first micro-expert only after the adapter baseline and dataset evaluator are stable.

The near-term goal is not to claim that a tiny model is universally superior. It is to prove that specialization plus hot-swapping can produce a more capable local coding experience than a single general model under the same GPU-memory constraint.
