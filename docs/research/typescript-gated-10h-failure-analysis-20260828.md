# TypeScript gated 10-hour failure analysis

Date: 2026-08-28

## Evidence

The final fixed-seed report is
`.oktopai/evaluations/typescript-external-gated-10h-final-heldout-200.json`.
It contains 200 tasks from `benchmarks/typescript-heldout-980.json`, with
independent base and adapter verification. The adapter scored 0.5088 with
37/200 verified; the base scored 0.7754 with 108/200 verified.

| Family | Tasks | Adapter verified | Base verified | Adapter score | Base score |
|---|---:|---:|---:|---:|---:|
| record-dictionary | 23 | 0 | 23 | 0.000 | 1.000 |
| readonly-generic | 22 | 0 | 18 | 0.477 | 0.909 |
| generic-indexed-access | 29 | 0 | 0 | 0.750 | 0.526 |
| null-narrowing | 19 | 0 | 19 | 0.404 | 1.000 |
| type-predicate | 8 | 0 | 8 | 0.125 | 1.000 |
| async-return | 18 | 1 | 0 | 0.389 | 0.500 |
| object-constraint | 25 | 4 | 0 | 0.400 | 0.500 |
| overload-signature | 17 | 6 | 17 | 0.676 | 1.000 |
| mapped-type | 25 | 14 | 23 | 0.773 | 0.973 |
| discriminated-union | 14 | 12 | 0 | 0.929 | 0.500 |

## Decision

Do not merge, quantize, register, or upload the adapter. The result fails the
80% overall verification gate and shows regression on several families where
the base is already reliable.

## Next data package

1. Add compiler-verified repairs for record dictionaries, null narrowing,
   type predicates, readonly generics, async return types, and overloads.
2. Prefer minimal, strict-mode, no-`any` examples with explicit negative cases
   and independent compile/test checks.
3. Add multi-file repository repairs covering exports, inferred contracts,
   tsconfig/module boundaries, and public API changes.
4. Preserve chosen/rejected pairs: the base or a known-good repair is chosen;
   adapter outputs that compile incorrectly are rejected examples only after
   their failure is independently reproduced.
5. Retrain a small controlled candidate and evaluate it with both fixed seeds
   before considering preference optimization or packaging.

The current adapter remains an isolated research artifact. This report does
not authorize promotion or external transfer.

## Targeted corpus generated

The first follow-up corpus is
`.oktopai/datasets/typescript-targeted-contract-verified-20260828.jsonl`.
It contains 3,600 deterministic records across `generic`, `narrowing`,
`readonly`, `predicate`, `async`, and `api-contract`. Strict TypeScript
compilation passed for the complete corpus; the deterministic split is 2,659
train, 581 validation, and 360 test records.

The next experiment may train an isolated small candidate on this corpus, then
must run both fixed held-out seeds and the family gates before any packaging
decision. The existing gated 3B adapter remains untouched.
