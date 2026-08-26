# Usable local specialist orchestrator roadmap

## End state

Oktopai should let a developer build and maintain a real website entirely
locally. The system selects the smallest capable specialist, loads it into the
GPU working set, gives it repository tools, verifies its work with the actual
project toolchain, and unloads or retains models according to demand.

The first usable product target is one website stack:

- TypeScript for types, modules, APIs, and application logic;
- Next.js for routing, server/client boundaries, and framework conventions;
- CSS for layout, responsive behavior, and accessibility-oriented styling;
- SQLite for schema, migrations, queries, and safe data access.

“Usable” means verified repository changes, not merely fluent answers. A task
is successful when the correct files are changed and the relevant compiler,
framework, style, or database checks pass.

## Operating model

```text
user task + repository state
              │
              ▼
       deterministic router
              │
              ├── specialist policy/model
              │       └── typed repository tools
              │
              ▼
       lifecycle manager
       load / warm / evict
              │
              ▼
    compiler, tests, lint, DB checks
              │
              ▼
       evidence-backed response
```

The model is only one part of the system. The router, tool contract, context
state, lifecycle manager, validators, and telemetry must remain model-
independent so that adapters, full checkpoints, and runtimes can change.

## Ordered execution plan

### Phase 1 — Finish the orchestration foundation

Status: in progress.

Complete the runtime-independent product loop:

1. Keep logical experts separate from physical models and adapters.
2. Add persistent lifecycle state and event IDs across CLI invocations.
3. Make model loading, keep-alive, eviction, and shared-model reuse measurable.
4. Add the typed tool boundary described in `tool-using-specialists.md`.
5. Reconstruct every tool call from model-independent session state.
6. Add approval, timeout, output-size, and secret-redaction policies.

Gate: route-only mode works without a runtime; local mode gives structured
events; missing runtimes and models produce actionable errors; no cloud fallback
is possible.

### Phase 2 — Build a real website fixture

Create a small but realistic Next.js application under a benchmark fixture. It
must include TypeScript strict mode, server and client components, CSS modules
or a deliberately chosen styling system, SQLite migrations, seed data, and a
focused test suite.

The fixture should contain intentionally repairable failures:

- generic constraints and narrowing errors;
- incorrect server/client boundaries;
- stale or unsafe database queries and migrations;
- responsive layout and accessibility regressions;
- tests that fail for observable reasons.

Every task gets a clean repository snapshot, a hidden expected invariant, and
commands that can verify the invariant. Do not use subjective screenshots as
the only quality signal.

Gate: a base local model can inspect, patch, and verify at least a small set of
tasks through the typed tool loop.

### Phase 3 — Establish domain baselines

Before training more specialists, measure prompt-specialized baselines using
the same fixture and held-out tasks:

- TypeScript baseline;
- Next.js baseline;
- CSS baseline;
- SQLite baseline;
- general coding baseline.

Record task success, files changed, tool calls, verification passes, cold and
warm latency, prompt/completion tokens, and GPU residency. These baselines are
the control group for every adapter or distilled model.

Gate: each domain has at least 50 executable held-out tasks, split by task
family and repository state. No specialist is promoted based only on prose
review or training loss.

### Phase 4 — Train the TypeScript tool-using specialist

TypeScript remains first because its compiler, language service, public source,
and ecosystem provide unusually strong verification signals.

The training sequence is:

1. curate repository-grounded repair tasks;
2. generate teacher trajectories with inspect → diagnose → patch → verify;
3. independently execute every command and compile every accepted patch;
4. retain failed trajectories as labeled negative/preference examples;
5. train a small LoRA/QLoRA adapter first;
6. compare it to prompt specialization on a hidden repository split;
7. distill into a standalone small checkpoint only if the adapter wins and the
   standalone artifact improves load time, memory, or portability;
8. export to a fast local runtime and benchmark the real tool loop.

The current Runpod teacher pilot is part of this phase. It must pass the quality
gate before scaling to more remote generation.

Gate: TypeScript specialist beats the shared baseline on verified held-out
repairs without unacceptable unsafe-tool behavior, and its artifact metadata
records base model, adapter, data provenance, compiler versions, and checksums.

### Phase 5 — Add Next.js as a framework specialist

Next.js should not simply duplicate the TypeScript adapter. It needs examples
that teach framework-specific decisions: server/client boundaries, route
handlers, data fetching, caching, metadata, configuration, and build output.

Share the TypeScript tool policy and compiler verifier, but add framework
validators and version metadata. Route TypeScript-only tasks to TypeScript and
framework-boundary tasks to Next.js; use a joint verification task when both
domains are involved.

Gate: the fixture builds successfully after representative Next.js repairs, and
the specialist does not regress ordinary TypeScript tasks.

### Phase 6 — Add CSS/layout specialization

CSS quality requires rendered behavior, not only text similarity. Build browser
fixtures with deterministic viewport sizes, accessibility checks, computed-style
assertions, and visual snapshots used as supporting evidence.

Train on layout diagnosis, responsive design, specificity, containment, CSS
modules, and accessibility. Keep browser execution in the host tool layer; the
model proposes bounded edits and interprets results.

Gate: layout assertions and accessibility checks pass on hidden viewports while
the patch remains minimal.

### Phase 7 — Add SQLite specialization

SQLite should use a schema-aware context provider and safe read-only tools.
Training tasks cover schema inspection, migrations, joins, indexes, query
correction, transactions, and parameterization.

Use `EXPLAIN QUERY PLAN`, migration application against a disposable database,
and query-result invariants as evidence. Never allow training or evaluation
tasks to mutate the user's production database.

Gate: migrations apply cleanly, queries return expected fixtures, unsafe string
interpolation is rejected, and the specialist explains query-plan tradeoffs.

### Phase 8 — Prove hot-swapped website development

Run a multi-step benchmark that asks oktopai to create or repair the complete
fixture. Tasks deliberately cross boundaries:

1. router selects TypeScript for a type failure;
2. Next.js specialist repairs a server/client issue;
3. CSS specialist fixes a responsive/accessibility failure;
4. SQLite specialist updates schema and query code;
5. TypeScript specialist reconciles the final types;
6. host runs build, tests, lint, browser checks, and database checks.

Compare three systems: one shared model, prompt-specialized aliases, and the
hot-swapped specialist fleet. Report total task success, verification rate,
wall-clock latency, cold-start cost, warm-start cost, aggregate tok/s, and
model residency. This is the central proof of the oktopai hypothesis.

## Speed and memory strategy

Do not force every model to consume all VRAM. The objective is useful throughput
and quality per GiB:

- keep one physical model loaded when multiple logical experts share it;
- use bounded concurrent requests where independent tasks exist;
- keep sequential tool calls ordered within one repair trajectory;
- use quantized weights and small contexts when quality permits;
- preload predictively from file path and repository signals;
- measure cold load, warm load, first-token latency, generation tok/s, and
  end-to-end verified repair time separately;
- prefer a smaller model that passes the task over a larger model that merely
  produces faster unverified text.

Initial engineering targets are 150+ tok/s for small local generation where
the runtime/model combination supports it, and a stretch target above 300
tok/s. These are performance targets, not quality guarantees; every result
must include model size, quantization, context, concurrency, and hardware.

## Runpod delegation policy

Runpod is an accelerator for expensive, reproducible experiments—not a
required runtime dependency. The local machine remains the source of truth for
code, manifests, benchmark definitions, checksums, and promotion decisions.

### Keep work local

Run locally when work is interactive, small, privacy-sensitive, or needed for
final acceptance:

- routing, lifecycle, tool-policy, and unit tests;
- final evaluation against the local website fixture;
- smoke tests, adapter comparisons, and hot-swap demonstrations;
- repository-specific code not explicitly packaged for remote use;
- artifact checksum and manifest validation after download.

### Delegate to Runpod

Delegate only after a local dry run and only for bounded, resumable workloads:

1. stronger-teacher generation for repository-grounded trajectories;
2. thousands of independent compiler, test, browser, or database checks;
3. QLoRA/adapter training when local CUDA is unavailable or insufficient;
4. quantization and runtime comparisons;
5. bounded parallel-throughput experiments.

Do not delegate an unverified idea, an open-ended generation loop, or a task
without a measurable acceptance criterion.

### Remote experiment gates

Every Runpod job follows this order:

1. local script dry-run and dependency probe;
2. input manifest containing Git commit, dataset hash, model identifier,
   prompt version, and expected schema;
3. 100–500 record pilot;
4. remote quality and cost check;
5. explicit continuation threshold;
6. resumable larger batches;
7. periodic synchronization to local storage;
8. local verification and held-out evaluation;
9. promotion only after the specialist beats its baseline.

The current TypeScript teacher pilot follows this process. Raw teacher records
are not student truth until local strict TypeScript verification accepts them.

### Pod, storage, and privacy rules

- Prefer a secure A40 for a quantized 14B teacher or medium adapter run.
- Use an A100 80 GB only when model size, context, batch size, or training
  demonstrably exceeds the A40.
- Avoid 32B+ teachers until a smaller teacher fails a documented quality gate.
- Mount persistent `/workspace` storage and write JSONL incrementally.
- Keep raw answers, accepted records, rejected records, metrics, logs, and
  checkpoints as separate artifacts.
- Never place GitHub credentials or private repository secrets on the Pod.
- Use signed dataset assets or a minimal explicit transfer package instead of
  requiring a private repository clone.
- Copy outputs back and verify SHA-256 before terminating the Pod.
- Terminate rather than merely stop the Pod after synchronization.

### Cost controls

Each run records GPU price, start/end time, storage, transfer size, model
download size, generated records, accepted records, and cost per accepted
verified record. Stop when the pilot fails its quality threshold, output is
duplicative, cost per accepted record exceeds the budget, or the required
artifact has been synchronized and verified. Remaining account credit alone is
not a reason to extend a low-value run.

### Remote return package

Every completed run must return:

```text
run-manifest.json
teacher-answers.jsonl
accepted-training.jsonl
rejected.jsonl
metrics.jsonl
model-or-adapter/
checksums.sha256
```

The local pipeline verifies schemas, provenance, compiler/tool results, model
metadata, and held-out performance. Loss curves or remote throughput alone
cannot promote a specialist.

### Delegation by phase

| Phase | Local responsibility | Runpod responsibility |
| --- | --- | --- |
| Foundation | router, tools, lifecycle, fixture | none unless runtime comparison is needed |
| TypeScript data | task schema, verifier, held-out split | stronger teacher trajectories and large verification |
| TypeScript training | baseline and final evaluation | QLoRA/adapter sweeps when local CUDA is insufficient |
| Next.js/CSS/SQLite data | fixtures and validators | teacher generation after TypeScript process is proven |
| Multi-domain benchmark | final website and acceptance | optional parallel speed/memory experiments |
| Artifact registry | manifests, checksums, promotion | temporary compute only; never the only artifact copy |

## Artifact and version strategy

Experts target durable concepts plus declared version ranges. Do not train one
model for every patch release by default. Store adapters, merged checkpoints,
runtime exports, manifests, licenses, training data hashes, and held-out
results in a versioned artifact registry. A future public registry can host
these artifacts, but local reproducibility and checksums remain mandatory.

## Immediate order after the current Runpod pilot

1. Retrieve and checksum the raw teacher records.
2. Verify TypeScript outputs locally and calculate acceptance by family.
3. Run sequential versus four-worker generation throughput comparison.
4. Update the teacher prompt/data curriculum based on rejected records.
5. Finish the executable website fixture and held-out suite.
6. Train and evaluate the next TypeScript adapter against the fixed baseline.
7. Only after TypeScript has a verified win, implement Next.js, CSS, and SQLite
   specialist datasets and adapters.
8. Run the complete hot-swap website benchmark and publish the measurements.
