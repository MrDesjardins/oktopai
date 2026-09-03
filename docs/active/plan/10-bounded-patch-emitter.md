# 10 — Bounded patch-emitter stage

## Finding

The full trajectory model can learn the replacement event, but on a real
7.8-KB file it copies the complete source into `old`/`new` and truncates or
malforms the JSON. Repeating replacement examples and stronger wording did not
remove this behavior.

## Correction

Keep repository-grounded inspection and compiler diagnosis in the trajectory
stage. Add a stage-two patch emitter whose input contains only:

- the task and repository facts;
- the compiler diagnostic and target path;
- a numbered source window around the diagnostic; and
- the exact replacement-only output contract.

The complete repository snapshot is intentionally absent from the emitter
prompt. `bounded_file_excerpt`, `diagnostic_file_location`,
`patch_emitter_context`, and `build_patch_emitter_request` implement this
boundary in `src/oktopai/trajectory.py`.

## Preflight evidence

`scripts/prepare_patch_emitter_data.py` generated 256 SFT records (224 train,
32 validation). Prompts contain no `repository_files`, have a maximum length
of 1,351 characters under the current 2,400-character context bound, and
completion lengths range from 190–513 characters. The source snapshots are
used only while deriving and validating the bounded context; they are not
copied into the emitted prompt.

CPU unit coverage now passes 26 tests with one skip. A targeted local-shape
supplement expanded the corpus to 436 records (386 train / 50 validation),
and the isolated v5 candidate completed 200 steps. Its compiler-backed local
gate tied the prior result at 15/20; all five failures chose an unchanged
downstream condition for the numeric-ratio mismatch. v5 remains held. The
next step is a focused numeric diagnostic-source correction with an explicit
no-op replacement guard.

## Next correction prepared

The no-op guard is implemented and covered by the CPU suite (25/25 passing).
A 40-record numeric source-localization supplement was generated and statically
verified, then merged into a 476-record corpus (422 train / 54 validation).
The next SFT artifact and manifest are prepared. Training remains a separate
isolated decision; no promotion or export is implied.

The v6 launch was attempted twice but exited during model loading while an
unrelated Python process occupied 15,741 MiB of the 16,303 MiB GPU. No v6
checkpoint exists and no evaluation has started; the unrelated process was
not terminated. CPU validation remains the active work until GPU capacity is
available.

The bounded target now exposes every same-file diagnostic line/column and an
explicit source-localization rule for downstream diagnostics. The regenerated
v7 SFT is preflight-clean at 476/476 and the CPU suite is 26/26. It is the
next justified isolated training candidate, pending safe GPU capacity.

The final CPU integrity pass completed successfully (`git diff --check`, Python
compilation, and v7 SFT preflight). CUDA inspection did not complete, so v7
remains untrained and unevaluated pending a safe GPU window.

The latest CUDA query reports only 330 MiB free, confirming that training
should remain deferred. The v7 artifact is preflight-clean and ready, but no
checkpoint or evaluation exists.

The full 40-record compiler replay was retried with four workers and a
300-second bound but timed out without a report. Only the corrected 2/2 sample
is compiler-verified; the complete gate remains pending and v6 remains
untrained/un-evaluated. This historical note predates the current v7
source-localization candidate.

A bounded CPU replay found and fixed a synthetic DOM-name collision in the
numeric supplement. The corrected sample passes compiler replay 2/2; the
476-record source audit and 26-test CPU suite are clean, and the SFT artifact
was regenerated. The next step remains isolated v6 training when GPU memory
is available; the current prepared candidate is v7.

The dedicated SFT preflight now passes 476/476 records: prompts contain no
full snapshots, completions are valid compact replacement JSON, no replacement
is unchanged, and split accounting is 422 train / 54 validation. GPU training
remains deferred while the external process occupies nearly all VRAM.

The verifier now supports bounded parallel replay. The first two corrected
numeric records pass compiler replay 2/2, but a four-worker full 40-record run
exceeded 180 seconds on CPU. Static and SFT preflight remain clean; complete
compiler replay is still an explicit pending check.

The latest confirmed GPU check reported only 618 MiB free, so v7 training
remains deferred. No checkpoint or evaluation exists; the prepared corpus
remains ready for the next safe GPU window.

A large-snapshot prompt-boundary regression test was added and passes in
isolation. It confirms unchanged distant source is not present in the emitter
prompt while the diagnostic window remains available. The full suite should
be rerun when system load permits.
