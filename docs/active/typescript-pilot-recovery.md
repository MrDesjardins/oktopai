# TypeScript teacher-pilot recovery plan

## Diagnosis

The first Runpod Qwen2.5-Coder-14B pilot generated 500 tasks plus one smoke
record. Local strict verification accepted 69 records and rejected 432. This is
not yet evidence that the teacher is incapable of TypeScript; the experiment
also exposed a contract mismatch:

- the corpus mixed code repairs with explanation, diagnosis, and review tasks;
- the teacher was asked to prefer code even when the task primarily requested
  prose reasoning;
- ingestion accepted only fenced TypeScript blocks;
- 189 responses had unfenced code or prose and were discarded before useful
  verification;
- 57 explanation/review responses were judged by a code compiler even though
  their primary expected output was an explanation;
- the test family produced zero accepted records;
- accepted rates by family were only 12–20% for the non-test families.

The result is a failed data-quality gate and a successful instrumentation
experiment. It does not justify training the student or spending more on
Runpod yet.

## Synthetic contract dataset completed

To replace the missing reliable examples without another paid run, the
programmatic contract generator produced 5,000 deterministic records at
`.oktopai/datasets/typescript-contract-v1-5000.jsonl`:

- 8 balanced families, including a dedicated test family;
- 3,736 train, 756 validation, and 508 test records;
- every completion is fenced TypeScript with an explicit output contract;
- the combined completion file passed strict TypeScript compilation;
- provenance marks every row as synthetic rather than human or teacher truth.

This is a verified supervised seed corpus, not yet a distilled corpus. It can
be used to test the student training pipeline, but the next quality increase
requires teacher trajectories and repository-level fixtures on top of it.

## Handbook curriculum expansion

The official TypeScript Handbook topic map was used to expand the synthetic
curriculum beyond the original repair templates. The generator now covers
primitives, arrays, tuples, literal types, optional properties, unions,
narrowing, `unknown`, predicates, discriminated unions, `never`, callbacks,
overloads, generic constraints, `keyof`, conditional types, mapped types,
template literal types, utility types, classes, async returns, and declaration
files. It also includes JavaScript cases for JSDoc contracts, null narrowing,
and `checkJs` behavior.

The generated artifact is
`.oktopai/datasets/typescript-handbook-v1-10000.jsonl`:

- 10,000 deterministic records;
- 8,752 TypeScript records and 1,248 JavaScript records;
- 24 curriculum families;
- TypeScript and JavaScript compilation both pass (`--strict` and
  `--allowJs --checkJs` respectively);
- each row retains the relevant official documentation URL in provenance.

This is broad language coverage, not complete TypeScript coverage. It should
be combined with repository-grounded repairs, version-specific compiler cases,
tool trajectories, and held-out project fixtures before making a capability
claim.

## Correct data contract

Split TypeScript tasks into distinct output contracts:

1. **Repair/code tasks** — return a single fenced TypeScript/TSX patch or a
   structured patch object. Verify with the relevant project compiler/tests.
2. **Explanation tasks** — return an explanation plus optional code. Verify the
   explanation against source facts and diagnostics; compile only the optional
   code block.
3. **Review tasks** — return findings with file/line evidence, severity, and a
   proposed patch. Verify the findings against the source and compile the patch.
4. **Tool trajectories** — return typed inspect/diagnose/edit/verify events.
   Replay every event; never trust claimed command results.

These records must not be collapsed into one “compile the whole answer” gate.
The student coding corpus should initially use only code and tool-trajectory
records. Explanation and review data should be retained in separate datasets.

## Local recovery work

1. Add a pilot analyzer that reports output shape, family, fenced-code rate,
   compiler status, and rejection reason.
2. Update the teacher prompt with an explicit schema per task contract.
3. Improve extraction conservatively: accept only fenced code or a validated
   structured patch; never compile arbitrary prose as TypeScript.
4. Add a dedicated test-task fixture and test-specific validator.
5. Generate a 50-task local dry run using the existing local runtime if
   available, otherwise use deterministic mock responses to test the pipeline.
6. Require at least 80% schema compliance before another remote pilot.
7. Require at least 60% verified acceptance overall and 40% in every selected
   code family before training.

The local training environment currently reports no usable CUDA device. Do not
start a long CPU training run from this 5,000-row corpus; use it for pipeline
validation and schedule the controlled adapter run on an approved GPU only
after the corrected teacher/data contract is exercised.

## Next remote pilot

Only after the local recovery gates pass, use Runpod for a 100-task stratified
pilot:

- 20 generic/type-system tasks;
- 20 module/API-contract tasks;
- 20 refactor/repair tasks;
- 20 test tasks;
- 20 migration/configuration tasks.

Use a strict code-output teacher prompt and a separate explanation/review run.
Compare Qwen2.5-Coder-14B with Qwen3-Coder-Next only if the current teacher,
under the corrected contract, still fails the verified gate. The comparison
must report accepted records per dollar, not only model fluency.

## Training decision

Do not train from the original 69 accepted records. They are too few, family-
imbalanced, and derived from a mismatched acceptance contract. After the
corrected pilot, train a small adapter only if the new accepted dataset passes
the gate and has held-out family coverage. Evaluate the adapter against the
same base model and prompt-specialized baseline before merging or quantizing.

## Paper value

Preserve the failed pilot as a useful negative result. It demonstrates why
teacher-data quality requires output contracts, task-specific validators, and
acceptance metrics rather than raw completion counts or training loss.
