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
