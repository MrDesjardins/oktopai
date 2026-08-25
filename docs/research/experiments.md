# Experiments and roadmap

The benchmark dataset covers TypeScript generics, React rendering, Next.js server/client boundaries, test generation, and general refactoring. It reports deterministic routing accuracy and latency and writes `.oktopai/benchmark-routing.json`. With Ollama running, `benchmark --live` writes raw generated outputs and timing data to `.oktopai/benchmark-outputs.jsonl`; no subjective quality claim is made by the MVP.

Next experiments:

1. Compare cold and warm timings for one small installed model while varying `max_warm_models`.
2. Measure routing accuracy against a larger labeled prompt/file corpus and tune weights without adding an LLM router.
3. Compare truly specialized checkpoints or LoRA adapters against the shared-base-model prompts using a fixed, human- or test-scored task set.

The installed-model comparison experiment is reproducible with:

```bash
PYTHONPATH=src python3 scripts/compare_installed_models.py
```

It compares only models already present in Ollama and writes raw responses to `.oktopai/installed-model-comparison.json`. It intentionally does not rank model quality automatically; the next step is to add executable assertions and human scoring criteria.

### Initial installed-model run

The first run used the four identical specialist tasks from the comparison script and the models already present in Ollama. Results below are generation times, not quality scores:

| Model | TypeScript | React | Next.js | Testing | Observation |
|---|---:|---:|---:|---:|---|
| `qwen2.5-coder:7b` | 5.2 s | 2.7 s | 2.4 s | 2.3 s | Fastest baseline; produced plausible but sometimes generic answers |
| `qwen30-coder-8k` | 73.3 s | 7.5 s | 12.4 s | 12.6 s | Much higher first-load cost |
| `qwen35-planner-8k` | error | 35.4 s | 79.8 s | error | Could not reliably remain available during the run |
| `qwen3-coder:30b` | 86.2 s | 6.2 s | 7.7 s | 10.0 s | Large cold-load penalty, faster after residency |
| `qwen3.5:35b-a3b` | 80.4 s | 23.3 s | 34.3 s | error | Memory pressure/runtime availability affected the run |

This is not a quality ranking. It is an early lifecycle result: the 7B model was consistently available and responsive, while the larger models imposed substantial residency and switching costs. That supports testing small distilled specialists against the 7B baseline rather than assuming a larger model is always better for interactive local work.

The repository-context review also exposed a concrete quality failure: qwen2.5-coder proposed changing the router's deterministic tie-break sort even though that sort was already present. This validates the need for executable expert benchmarks and verifier steps before claiming specialization success.

### Versioned benchmark run

The first live run of `benchmarks/tasks.json` against `qwen2.5-coder:7b` routed all 8 tasks correctly. Routing took approximately 0.6 ms. Generation times ranged from approximately 1.25 to 3.84 seconds.

Verification produced:

- 4 `fixture_pass` results;
- 2 `verified` results from SQL and Python execution;
- 1 `checklist_pass` result;
- 1 failed TypeScript check.

The failures are valuable: they show that a response can be generated quickly while still failing domain checks. SQL now executes against an in-memory fixture. The remaining JavaScript-family validators require project-local compiler/framework dependencies or hermetic fixtures before they can become fully executable.

### Next.js/TypeScript swap benchmark

The oracle benchmark applies known-correct repairs to the fixture and passes both `tsc --noEmit` and `next build` using Next.js 16.3.2.

The live swapped run used `oktopai-nextjs` followed by `oktopai-typescript`:

- Next.js response: approximately 0.78 seconds at approximately 145 tokens/second;
- TypeScript response: approximately 0.42 seconds at approximately 153 tokens/second;
- TypeScript and Next.js build: failed because the generated files omitted the required `"use client"` directive and did not use the fully safe generic signature.

This is the first end-to-end proof that the benchmark can distinguish fast local generation from verified project correctness. The failure is now a candidate for specialist training and a regression test.

Future roadmap: model/adaptor metadata, predictive loading, retrieval, automated evaluation, multi-expert critique, and GPU-aware capacity estimation.
