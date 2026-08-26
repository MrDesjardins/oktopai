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
