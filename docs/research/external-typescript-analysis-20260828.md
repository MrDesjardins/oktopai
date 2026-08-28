# External TypeScript Candidate Analysis

Analysis date: 2026-08-28

## Results

The two bounded public imports contained 12,993 normalized records. Strict
TypeScript verification accepted 2,080 records (16.01%):

| Source | Raw | Accepted | Acceptance |
| --- | ---: | ---: | ---: |
| `bleugreen/typescript-instruct` | 10,000 | 1,467 | 14.67% |
| `grenishrai/typescript-dataset` | 2,993 | 613 | 20.48% |
| Combined | 12,993 | 2,080 | 16.01% |

The raw and verified artifacts remain under
`.oktopai/external/typescript/`. The machine-readable report is
`.oktopai/external/typescript/analysis.json`.

## Coverage findings

The accepted set is not balanced enough to train directly:

| Detected family | Accepted records |
| --- | ---: |
| other | 1,505 |
| generics | 191 |
| classes | 184 |
| errors | 78 |
| modules | 38 |
| JSX | 38 |
| async | 32 |
| narrowing | 14 |

There was no exact normalized overlap with the 2,450-record Qwen3-Coder
teacher corpus. That is useful for diversity, but it does not prove that the
external examples are instructionally good or free of benchmark contamination.

## Interpretation

The external data is useful as a source of additional compiling code, but not
as a ready-made TypeScript specialist curriculum. The low acceptance rates
show that the original datasets contain many incomplete, context-dependent, or
syntactically invalid answers. The dominance of `other` means a naive merge
would add volume without reliably adding the concepts where the student needs
help.

The accepted rows contain `any` in 389 answers. This is not automatically an
error—some legitimate interoperability tasks require it—but it should be
reviewed because the specialist contract prefers precise types. The report
found no code fences in accepted completions, so the compiler gate is seeing
the actual extracted code rather than merely prose wrappers.

## Decision

Do not train on the combined external set yet. Before adoption:

1. retain source and license metadata per row;
2. classify families with stronger AST- or task-based signals;
3. review or regenerate rejected prompts rather than silently discarding them;
4. cap the dominant `other` family and oversample underrepresented families;
5. create repository/source-level validation and test splits;
6. run a short training recipe matrix before a long student run.

The analysis tool is `scripts/analyze_external_typescript.py`. It is designed
to be rerun when new bounded sources are added.
