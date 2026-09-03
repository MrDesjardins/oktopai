# 06 — Train and evaluate a trajectory specialist

Status: completed as an isolated trajectory-aware candidate and held-out replay check

## Objective

Compare response-only SFT with trajectory-aware training on a fixed suite. The trajectory-aware candidate trained for 200 CUDA steps; both held-out adapter outputs passed contract validation and independent replay. The validation split contains only two synthetic records, so this remains diagnostic. The response-only v3 step-8,000 follow-up completed separately as a CPU-constrained diagnostic and is not directly comparable to the normal GPU quality reports.

## GPU-gated work

- Train an isolated adapter from the accepted trajectory corpus.
- Keep the base, tokenizer, and benchmark fixed.
- Evaluate code quality and tool behavior separately.
- Measure verified success, unnecessary tools, recovery rate, latency, and
  memory.

## Required comparisons

1. Base model with the existing prompt.
2. Current v3 response-only adapter.
3. Trajectory-aware adapter.

## Exit criteria

- The trajectory-aware candidate improves verified task success or recovery
  without unacceptable unsafe-tool behavior.
- Results are reproducible and documented before packaging.
