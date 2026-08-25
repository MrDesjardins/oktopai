# Overnight TypeScript specialist plan

This is the execution plan for the RTX 5080 machine. The objective is two-dimensional: a TypeScript expert must produce compiler-valid, useful code, and its production Ollama artifact must sustain at least 150 generated tokens per second, with a target above 300 tok/s.

## Promotion gates

An adapter remains experimental until it passes all of these on a disjoint held-out suite:

1. 80% overall compiler/test verification;
2. 70% minimum in every TypeScript task family;
3. 60% on repository-derived repairs;
4. no regression against the base model on general coding tasks;
5. results reproduced across two fixed evaluation seeds.

Speed is measured only after exact-lineage merge and GGUF export: cold load, warm load, time to first token, decode tok/s, prompt processing tok/s, VRAM, resident model size, and swap/unload latency.

## Sequence for the next 10+ hours

### Phase 0 — finish and record v10

The active 2,000-step CUDA run must finish. Record wall time, optimizer steps/sec, loss, checkpoint, GPU memory, and any interruption. Evaluate 200 held-out tasks stratified by family; never select from the training split.

### Phase 1 — data quality expansion

Grow the corpus from 48 verified repository repairs to at least 1,000. Each repair needs source, compiler diagnostics, a teacher patch, an independent `tsc --strict` or project test result, license/provenance, and a deduplication hash. Keep synthetic data for coverage, but cap its share in the quality train split so it cannot drown real repairs.

### Phase 2 — controlled SFT matrix

Run with identical held-out tasks: current clean corpus at 2,000 steps; synthetic plus 1,000 repairs at 3,000 steps; the same data for 5,000 steps to test undertraining; larger LoRA rank at 3,000 steps; and a 1.5B/3B student if available locally. Use bf16 on the RTX 5080 when stable, gradient accumulation, checkpoint retention, and early stopping on validation compiler pass rate—not training loss alone.

### Phase 3 — preference optimization

Start DPO from the best SFT adapter, not from the untouched base. Use real chosen/rejected repairs first, then compiler-verified hard negatives. Compare beta values 0.05, 0.1, and 0.2 on the same 200-task slice. Reject any run whose held-out pass rate drops.

### Phase 4 — serving and hot-swap proof

For every candidate that passes quality gates: merge into its exact base, export F16 GGUF, quantize Q4_K_M and Q5_K_M, register explicit Ollama models, benchmark warm/cold generation and swap behavior, and retain only the best quality/speed/memory Pareto points.

The 150/300+ tok/s target is a serving target. Transformers + PEFT numbers are diagnostics and must not be compared directly to Ollama GGUF decode speed.

## Decision tree

- If quality rises with steps: continue the best SFT to 3–5k steps.
- If loss falls but quality stalls: stop adding synthetic records; improve repository repairs, prompt contracts, and verifier coverage.
- If 0.5B remains below 70% after clean SFT+DPO: move to 1.5B or 3B.
- If quality passes but speed is below 150 tok/s: use smaller quantization, shorter context, GPU offload, and llama.cpp/Ollama measurements.
- If speed exceeds 300 tok/s but quality fails: do not promote the artifact.

The controller is `scripts/run_overnight_typescript.py`. It is resumable and records stage boundaries in `experiments/runs.jsonl`.
