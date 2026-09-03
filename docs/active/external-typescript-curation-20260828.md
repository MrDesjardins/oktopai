# External TypeScript curation — 2026-08-28

## Outcome

The two bounded external datasets contain useful topic coverage, but they are
not ready to train on as downloaded. We processed every one of the 12,993
deduplicated records without using Qwen or any other language model to repair
them.

| disposition | records | training use |
| --- | ---: | --- |
| strict-verified code | 2,108 | eligible for a later gated corpus merge |
| explanation | 93 | retained separately for explanation/tool-use teaching |
| quarantine | 10,792 | not eligible; needs context-aware semantic reconstruction |

The verified count includes the previously independently checked external
records and deterministic repairs. The source answer and
prompt are retained in every output, along with verification evidence and the
repair method.

## Files

- `.oktopai/datasets/typescript-external-curated.jsonl` — training-shaped,
  strict-verified code records.
- `.oktopai/datasets/typescript-external-explanations.jsonl` — prose answers,
  intentionally separated from code-generation targets.
- `.oktopai/external/typescript/curation-quarantine.jsonl` — every unresolved
  record, including its original answer and reason for rejection.
- `.oktopai/external/typescript/curation-report.json` — machine-readable counts.
- `scripts/curate_external_typescript.py` — reproducible deterministic curation.

## Why we did not force all rows into training

Compilation proves syntax and type-checking, not that an answer satisfies the
prompt. Many rows are partial Angular/DevExtreme methods that refer to imports,
component fields, decorators, or framework versions not present in the row.
Wrapping those fragments in declarations would make them compile while
teaching the student fabricated APIs. Other rows contain prose, and some ask
for behavior without specifying an input/output contract. Those records must
remain quarantined until a contract and tests are authored.

The direct repairs are deliberately narrow: explicit parameters for an error-ID
lookup, a precise union contract for a length function, and a pure error-text
function where the original answer was only an unbound callback. These are
batch-checked with the pinned TypeScript 5.7.2 compiler.

## Next quality gate

The curated code must not be merged automatically with the existing teacher
corpus. First run family balance, duplicate detection, `any`/unsafe-cast
analysis, and the fixed held-out suite. Then train a short adapter probe and
accept it only if it beats the current base on held-out verification and does
not regress latency beyond the declared budget. The quarantine is the input to
the next contract-authoring pass, not a training source.

## Training gate result

The curated code was passed through the pre-training gate:

- 1,908 records admitted after removing `any` targets and unfinished markers.
- Stable splits: 1,529 train, 173 validation, and 206 test records.
- 200 records rejected by the gate (199 unsafe `any` targets and one unfinished
  source marker).
- Family metadata was assigned deterministically for balancing and evaluation.

This gated external corpus is ready for a controlled adapter probe. It is not
yet merged with the 2,450-record teacher corpus, because that comparison must
keep the existing held-out suite fixed and report whether the added data
improves the student rather than merely increasing dataset size.
