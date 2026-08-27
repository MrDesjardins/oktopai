# Online Data and Small Models Research

Research date: 2026-08-26

This document records public sources worth evaluating for future oktopai
specialists. Discovery is not adoption: every downloaded example must be
license-reviewed, deduplicated, provenance-tagged, and passed through the
language-specific verifier before it enters training.

## Recommended data sources

| Area | Candidate | Why it is useful | Gate or warning |
| --- | --- | --- | --- |
| TypeScript | [bleugreen/typescript-instruct](https://huggingface.co/datasets/bleugreen/typescript-instruct) | Roughly 41K TypeScript instruction rows | Inspect generation method, deduplicate, compile every answer; not automatically a verified benchmark |
| TypeScript | [grenishrai/typescript-dataset](https://huggingface.co/datasets/grenishrai/typescript-dataset) | Claims 3K+ advanced type-system examples covering generics, unions, narrowing, and transformations | Treat as candidate data until independently compiled and provenance checked |
| JavaScript/Python | [CodeSearchNet](https://github.com/github/CodeSearchNet) | Public repository-derived data with Python and JavaScript functions paired with documentation | It is mainly docstring/code supervision, not complete repair trajectories; preserve repository-level splits |
| All languages | [The Stack v2](https://huggingface.co/datasets/bigcode/the-stack-v2-train) | Large opt-out-aware source-code corpus with broad language coverage | Too large to download casually; use filtered, license-aware slices only |
| Next.js | [Tesslate/Next.js-Dataset](https://huggingface.co/datasets/Tesslate/Next.js-Dataset) | About 50K Next.js instruction examples and Apache-2.0 metadata | Mostly generated architectural answers; validate code with a Next.js fixture and avoid treating prose as proof |
| Next.js/React/UI | [marianbusoi/nextjs-react-dataset](https://huggingface.co/datasets/marianbusoi/nextjs-react-dataset) and [ui-instruct-4k](https://huggingface.co/datasets/iamdyeus/ui-instruct-4k) | React, TypeScript, Tailwind, and Next.js component tasks | Small or unclear verification signals; run lint, typecheck, and browser tests where applicable |
| CSS/JavaScript | [webdev-coding-dataset](https://huggingface.co/datasets/Hoglet-33/webdev-coding-dataset) | Frontend tasks spanning HTML, CSS, and JavaScript | Require browser rendering and accessibility checks; syntax alone is insufficient |
| Python | [python-code-instructions-85k](https://huggingface.co/datasets/NickIBrody/python-code-instructions-85k) | 85,903 deduplicated function/instruction rows with fixed splits | Dataset card says examples lack per-row provenance and repository isolation; compile and test before use |
| SQL | [SQL model and dataset search](https://huggingface.co/models?language=sql) | Candidate SQL checkpoints and Spider-oriented fine-tunes | Search results are not a quality guarantee; benchmark against SQLite execution and schema-grounded tasks |

## Priority order

1. **TypeScript:** download only the two focused datasets in a controlled
   slice, normalize them to the oktopai schema, deduplicate against our
   repository corpus, and run strict `tsc` verification. This is the highest
   value because it directly complements the current teacher run.
2. **JavaScript:** use CodeSearchNet as broad background data and generate
   repair/test tasks from JavaScript repositories. JavaScript examples should
   be converted into TypeScript only when the conversion is semantically
   checked; TypeScript is not simply JavaScript with annotations.
3. **Next.js and React:** use the focused datasets as task seeds, then verify
   complete mini-projects with `npm`, TypeScript, lint, and browser checks.
4. **Python:** use the 85K dataset for warm-up experiments, but prioritize
   repository-level bug fixes and test-backed examples over isolated
   docstring-to-function rows.
5. **CSS:** build a renderer-backed dataset. A valid stylesheet must be tested
   in a browser for layout assertions, responsive breakpoints, and basic
   accessibility, not just parsed successfully.
6. **SQL:** begin with SQLite because execution is local and deterministic.
   Use schema plus natural-language request plus query plus execution result
   as the core training contract. SQLCoder-sized models are useful teachers,
   but they are not automatically suitable small students.

## Small model candidates

The best first student remains **Qwen2.5-Coder 3B**, which is already in the
project and has an available LoRA training path. The official Qwen family also
offers 0.5B and 1.5B variants for experiments where multiple specialists must
fit concurrently. Smaller models improve residency and swap time, but quality
must be measured on the same held-out suites.

[StarCoder2-3B](https://huggingface.co/bigcode/starcoder2-3b) is a valuable
comparison baseline: it is a 3B code model trained on many programming
languages and supports fill-in-the-middle use. Its model card warns that it is
not an instruction model, so it is better suited to completion or infilling
experiments than as an immediate conversational router backend.

For SQL, a compact SQL-specific checkpoint may be useful, but a 7B SQLCoder
model is a specialist candidate rather than a tiny multi-model resident. We
should first compare it as a teacher or exclusive SQL expert against a
distilled 1.5B/3B student using SQLite execution accuracy.

## Router use versus coding use

The router does not need a large coding model. It should initially remain a
deterministic classifier using prompt, file extension, imports, dependencies,
and repository facts. A future learned router could use a tiny text classifier
or embeddings, but it should be evaluated on routing accuracy and latency
separately from code generation.

A small coding model can also act as a fast draft model for speculative
decoding, while a larger specialist verifies or completes the answer. That is
different from using the model to select an expert and should remain a later,
measured optimization.

## Download policy

No source listed here is downloaded automatically. Before adoption, record the
dataset revision, license, byte size, checksum, provenance fields, and expected
verification cost in an experiment manifest. Prefer filtered slices over
multi-gigabyte corpus downloads. The acceptance rule is:

```text
public candidate
  -> license/provenance review
  -> exact deduplication and decontamination
  -> language-specific compilation/execution
  -> family balance and held-out split
  -> training only after the data gate passes
```

The public sources are accelerators for finding task ideas and coverage gaps.
They do not replace the central oktopai principle: useful training data is
code that survives the same tools a developer will use.
