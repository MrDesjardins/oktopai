# Real-repository trajectory gate

Date: 2026-08-31

## Scope

This is the first evaluation that uses a repository-shaped snapshot rather
than the synthetic one-file `src/index.ts` harness. Each of the eight held-out
records contains the local Next.js fixture files (`app/page.tsx`,
`lib/getValue.ts`, `tsconfig.json`, and project metadata). Replay runs the
fixture's project-level `tsc --noEmit --pretty false` command in an isolated
temporary checkout with the local dependencies mounted.

The corpus is evaluation-only and was not added to training:

- Dataset: `.oktopai/datasets/typescript-trajectories-real-repository-eval-v1.jsonl`
- Independent verifier: `scripts/verify_real_repository_trajectory.py`
- Fixture replay: 8/8 records passed before model evaluation

## Model result

The lineage-correct safe-mixed adapter was evaluated against the local
Qwen2.5-Coder-3B base. The adapter produced 0/8 contract-valid trajectories;
the base also produced 0/8. No generated adapter trajectory reached replay.

The adapter failure is structural rather than a compiler-repair score:

- emitted event names included unsupported `run` and `content` events;
- emitted tool names included unsupported `content_inspection` and
  `content_substitution`;
- compiler commands did not satisfy the allowlist; and
- several outputs lacked a terminating valid `final` event or an edit.

This means the strong 50/50 synthetic safe-mixed result does not transfer to
the repository-shaped prompt format. It is evidence that the current
trajectory contract is overfit to the synthetic serialization/task context,
not evidence to promote the adapter. No additional evaluation should start
until the prompt/schema mismatch and repository-task coverage are analyzed.

## Correction round 1: explicit contract conditioning

The training prompt was updated to include the exact JSON output shape,
allowlisted event/tool names, compiler-command allowlist, and expected repair
ordering. The same contract is now included by the trajectory evaluator. The
160-record safe-mixed corpus was regenerated as
`.oktopai/datasets/typescript-trajectories-safe-mixed-v2-contract-sft.jsonl`
(128 train / 32 validation), without adding the real-repository evaluation
records.

An isolated adapter was trained as
`.oktopai/adapters/typescript-trajectory-safe-mixed-v2-contract` for 200 CUDA
steps in 361.4 seconds. Final train loss was 0.1901 and final validation loss
was 0.1288; the best observed validation loss was approximately 0.0995 around
step 128. It is a candidate only. The next step is one controlled evaluation
against the unchanged eight real-repository tasks.

## Correction round 1 result

The contract-conditioned candidate was evaluated on the unchanged eight tasks
and remained 0/8 contract-valid. The failure profile improved but did not
clear the gate: four outputs were malformed/truncated JSON, while four had
trajectory-shaped output with observations missing integer `exit_code` values.
Representative outputs also edited `tsconfig.json` or `app/page.tsx` instead
of the known failing `lib/getValue.ts` file.

The next CPU-side correction makes the known TS7053 location explicit in the
task and requires JSON-only output. The evaluation generator remains separate
from training data; the next run also raises the generation cap from 512 to
1024 tokens to distinguish truncation from repair-quality failure.

## Correction round 2: file-content escaping

The 1024-token run of the v2 contract-conditioned adapter produced 4/8
contract-valid outputs, but all four failed independent replay because their
edit contents contained literal `\\n` sequences. The verifier observed the
claimed `[2, 0]` sequence as `[2, 2]`, confirming that the model's claimed
success was not executable.

The contract now explicitly states that `args.content` is complete file text
and that JSON must escape each real newline once. A regression unit test covers
the distinction. The new isolated adapter
`.oktopai/adapters/typescript-trajectory-safe-mixed-v3-escaping` completed 200
CUDA steps in 354.7 seconds with train loss 0.183 and final validation loss
0.1338. Its bounded evaluation is the next gate.

## Correction round 3 result

The single-line adapter produced 8/8 contract-valid outputs at a 1024-token
cap. Independent replay passed 4/8. The four failures were structurally valid
but stopped after an unsuccessful observation or repeated an edit without a
final project-level diagnosis; their claimed completion did not correspond to
a successful final typecheck. The four passing records used the compact
single-line repair representation and reached executable success.

The contract and verifier were strengthened so accepted trajectories must
contain an `observe` with `exit_code: 0` after the last edit. The complete
single-line training corpus still passes independent replay 160/160, and the
unit suite passes 13 tests with one skip. The next training round will use this
stronger completion requirement before another held-out evaluation.

## Correction round 4 result

The v6 adapter, trained with the strengthened verification instruction, was
evaluated at the same 1024-token cap and regressed to 0/8 raw contract-valid.
Its outputs were close to the schema but omitted the canonical `args` wrapper
and sometimes the tool field. A conservative CPU-only normalizer recovered
4/8 structurally valid records, but all four still failed project replay: the
repair used `obj[key] as T[keyof T]`, which does not suppress the invalid index
operation under strict TypeScript. The normalizer is retained as an
interoperability experiment, not as a quality bypass.

The latest reliable executable result remains v5: 8/8 raw contract-valid and
4/8 independently replayed. The v6 training loss was 0.1068 with final
validation loss 0.1106, demonstrating again that loss is not a sufficient
quality signal.

The supplement-trained adapter was also checked through the conservative
normalizer: raw validity was 0/8, normalized validity was 4/8, and all four
normalized records passed full-project replay. The normalizer only moves
unambiguous top-level `path`/`content`/`command` fields into `args`, removes
the known command suffix, and decodes literal newline escapes. The evaluator
now records raw and normalized metrics separately so interoperability cannot
be mistaken for native model contract adherence.

## Correction round 5 result

The field-level schema-conditioned adapter trained on the 172-record mixed
corpus produced 8/8 raw contract-valid outputs at a 1024-token cap. All 8/8
passed independent full-project replay. The generated repairs consistently
targeted `lib/getValue.ts` and used the compiler-valid generic form
`<T, K extends keyof T>(obj: T, key: K): T[K]`.

The report records normalization separately: all records had a harmless
known command suffix normalized before replay, but raw contract validity was
already 8/8. Training took 353.5 seconds; train loss was 0.0993 and final
validation loss 0.1169. This is the strongest real-repository result so far,
but it remains a small eight-task diagnostic and is not promotion evidence.

## Artifact lineage note

## Correction round 6: disjoint family coverage and union narrowing

The v2 disjoint real-repository gate expanded coverage from eight tasks to 40
evaluation-only tasks across five compiler-repair families. The schema-
conditioned candidate generated 40/40 contract-valid trajectories and passed
32/40 independent full-project replays. Family results were:

- generic lookup: 8/8
- async return: 8/8
- union narrowing: 0/8
- array narrowing: 8/8
- object/record mismatch: 8/8

The eight union failures were plausible repairs, but their multi-line file
contents were emitted with literal escaped newline text, so the project stayed
broken. This isolates the next correction to union-narrowing exemplars rather
than broadening the evaluation or changing the verifier.

A verified 12-record union supplement was generated at
`.oktopai/datasets/typescript-trajectories-union-supplement-v1.jsonl` and
passed independent replay 12/12. It was merged with the existing mixed corpus
into `.oktopai/datasets/typescript-trajectories-real-supplement-union-v1.jsonl`
(184 records: 152 train / 32 validation); the complete mixed verifier passed
184/184. The SFT preflight is recorded in the matching `-sft.jsonl` and
manifest artifacts. No new model evaluation has started yet.

## Correction round 6 result

The union-focused adapter
`.oktopai/adapters/typescript-trajectory-real-supplement-v3-union` was trained
for 200 CUDA steps in 354.1 seconds. Train loss was 0.1011 and final
validation loss was 0.0845. On the unchanged 40-task disjoint gate it produced
40/40 natively contract-valid trajectories; no normalization was applied.

Independent full-project replay passed 40/40. Family results were:

- generic lookup: 8/8
- async return: 8/8
- union narrowing: 8/8
- array narrowing: 8/8
- object/record mismatch: 8/8

This resolves the previously isolated union-narrowing failure on this gate,
raising executable replay from 32/40 to 40/40. The result is still a bounded
local evaluation, so the adapter remains a candidate and has not been
promoted, exported, or uploaded.

## Correction round 7: broader transfer gate

To test whether the round-6 result generalized beyond the five original
families, an evaluation-only v3 gate was generated with 80 tasks across ten
families. Its project snapshots passed independent replay 80/80. The round-6
adapter produced 72/80 native contract-valid trajectories; all 72 generated
records passed independent full-project replay. Nine families passed 8/8, while
all eight discriminated-union tasks produced malformed or schema-like output.

A verified 12-record discriminated-union supplement was generated and passed
12/12 project replay. Merging it with the prior corpus produced
`.oktopai/datasets/typescript-trajectories-real-supplement-union-v2.jsonl`
(196 records: 164 train / 32 validation), which passed mixed replay 196/196.
The corresponding SFT preflight artifacts are present. The next justified
step is an isolated training run for this protocol/family correction; no
evaluation of that candidate has started yet.

## Correction round 7 result and round 8 preparation

The discriminated-union correction adapter trained for 200 CUDA steps in
365.6 seconds (train loss 0.1051; final validation loss 0.0708). On the
unchanged 80-task gate it produced 71/80 native contract-valid trajectories;
71/71 generated records passed independent full-project replay. The intended
discriminated-union family remained 0/8 contract-valid, while the other nine
families remained 8/8 except readonly mutation at 7/8. Inspection showed the
failure was envelope corruption: outputs copied contract/schema fields,
omitted the outer `trajectory` array, or truncated into extra JSON data.

To address that specific failure, the shared training/evaluation contract now
explicitly requires `trajectory` as the first JSON key, limits top-level keys
to `trajectory` and `final`, and forbids copying contract fields into output.
The schema regression test still passes 15/15. A new 196-record SFT preflight
artifact was prepared with this envelope instruction; training is the next
isolated step.

## Correction round 8 result

The envelope-conditioned adapter
`.oktopai/adapters/typescript-trajectory-real-supplement-v5-envelope` trained
for 200 CUDA steps in 368 seconds (train loss 0.1052; final validation loss
0.0934). On the unchanged 80-task gate it produced 80/80 native
contract-valid trajectories, with zero normalization applied. Independent
full-project replay passed 80/80. Every family passed 8/8, including the
previously failing discriminated-union family.

A CPU contamination audit found zero ID overlap and zero exact broken/fixed
trajectory-pair overlap between the 196-record training corpus and the
80-record evaluation gate. The gate is still a controlled local fixture, so
this is strong evidence for the protocol/family correction but not a general
promotion claim. The candidate remains held.

The audit is now reproducible with
`scripts/audit_trajectory_overlap.py`; its current run reports `clean: true`.

## Next gate: multi-file repository context

The 80-task gate still used one repair source file plus project metadata. To
test repository-context transfer, an evaluation-only 60-task gate was added at
`.oktopai/datasets/typescript-trajectories-real-repository-eval-v4-multifile.jsonl`.
Each snapshot contains an imported type/helper, the target source file, a decoy
constants file, and the normal Next.js project files. It covers six
cross-file families: property access, discriminated unions, optional values,
callbacks, generic record keys, and nullability.

The independent full-project verifier passed 60/60, and the reusable overlap
audit found zero training/evaluation ID overlap and zero exact repair-pair
overlap. This gate is ready for a controlled evaluation of the held candidate;
no evaluation has started yet.

## Multi-file gate result

The held envelope-conditioned adapter produced 60/60 native contract-valid
trajectories on the multi-file gate, with zero normalization applied. The
independent full-project verifier passed 60/60. All six cross-file families
passed 10/10: property access, union narrowing, optional values, callbacks,
generic record keys, and nullability.

For this same gate, the base model produced 0/60 parseable/contract-valid
outputs, while the adapter produced 60/60. This is a controlled local
comparison, not a general benchmark; the adapter remains held pending broader
real-repository evidence and systems review.

An initial launch attempt paired the 3B adapter with the 0.5B base and failed
with LoRA tensor-shape mismatches. The corrected run used
`.oktopai/hf-bases/qwen2.5-coder-3b`, as recorded in the adapter config. The
failed mismatched launch generated no result and is not part of the score.

The evaluator now records `family_summary` directly in every new report,
covering parseability, raw contract validity, normalized validity, and
normalization use for both base and adapter. The change is covered by the
16-test CPU unit suite and Python compilation checks.

## Source-derived data inventory

The local Microsoft/TypeScript-derived datasets were inspected before using
them as a new gate. The verified 2,450-record files contain response-only
`messages`/`completion` examples with public-source provenance: they contain
zero trajectory records and zero repository snapshots. The current 196-record
local corpus contains 196/196 trajectories and snapshots, but is deliberately
fixture-derived rather than public-source-derived.

This inventory is recorded by `scripts/inventory_trajectory_datasets.py`.
The source-derived response data therefore remains excluded from trajectory
quality claims until it has independently verified repository snapshots and
tool trajectories.

## Local repository gate

Because public-source licensing and trajectory artifacts remain unresolved, a
separate evaluation-only gate was built from the clean local
`desktop-ai-companion` checkout. Twenty snapshots include the real Vite/React
project files and local TypeScript dependency boundary; controlled mutations
cover literal unions, nullable native data, and numeric typing. The local
project verifier passes 20/20, and the overlap audit reports zero IDs and zero
exact repair pairs against the 196-record training corpus. This gate is
eligible for held-candidate evaluation but is not training data.

The pre-training static audit `scripts/audit_trajectory_corpus.py` now checks
IDs, split/family accounting, repository snapshots, and the shared trajectory
contract before replay. The current 196-record corpus passes with 196 unique
IDs and zero static failures; independent compiler replay remains a separate
required check.

The legacy v1 real-repository evaluation generator was also updated to carry
the same outer-envelope contract, and the contract-definition consistency
check now finds no older trajectory prompt copy. The CPU suite remains 19/19.

## Safety hardening

Trajectory validation now rejects absolute paths, parent-directory traversal,
and shell metacharacters/chaining in compiler commands. The stricter validator
passes the complete 196-record mixed corpus (196/196) and the CPU unit suite
passes 17/17, including dedicated rejection tests. This is a validation
boundary improvement only; it does not rewrite or admit invalid model output.

## Large-file transfer failure

The local `desktop-ai-companion` gate revealed a limitation hidden by the
small fixture: the held adapter emitted 43–111-character snippets for a
7.8-KB target file. Structural validation had counted these as 20/20 valid,
but independent replay was 0/20. The new completeness check rejects these
records before replay as `incomplete_edit_content`, aligning protocol metrics
with executable behavior. The 196-record training corpus remains 196/196
verified, and the CPU unit suite passes 20/20.

The completeness requirement is now present in the shared schema and all
training/evaluation prompt copies. No new model evaluation has started after
this correction.

## Compact replacement correction

The large-file failure motivated a deterministic edit alternative: an edit may
now carry exact once-only `replacements` instead of regenerating complete
`content`. Every old anchor must occur exactly once; missing or ambiguous
anchors are rejected, and all replay lanes apply replacements without shell
commands.

Twelve synthetic long-file exemplars were generated and replayed 12/12. They
were merged into a 208-record corpus (176 train / 32 validation), which passed
static preflight and mixed replay 208/208. The corresponding SFT preflight
artifact is ready. This correction contains no local private repository source.

The validator also now requires a diagnosis before the first edit and another
diagnosis after the last edit, so observations cannot be presented as
verification without a causal compiler step. The complete mixed corpus still
passes 196/196 replay, and the CPU unit suite passes 19/19.

The first 12-example replacement run did not change local-gate behavior: its
candidate still emitted complete-content snippets on 0/20 tasks. The targeted
replacement supplement was therefore expanded to 60 long-file exemplars. The
new merged corpus has 256 records (224 train / 32 validation), passes static
preflight and mixed replay 256/256, and has a ready SFT manifest. The next
training run is isolated and aimed specifically at this distribution failure.

## Replacement conditioning diagnosis

The v7 run trained on a mixed format: 60 replacement examples and 196
complete-content examples. It still emitted abbreviated `content` on all 20
local tasks despite lower validation loss, identifying a format-prior problem.

The evaluator also exposed a resource issue: keeping base and adapter models
resident together caused CUDA OOM. It now generates base outputs, releases the
base model/cache, and loads the adapter sequentially; `--limit` supports
bounded smoke tests. The first v8 correction made every edit a replacement but
used whole-file old/new pairs, which exceeded the 1,024-token output cap. The
converter now derives minimal changed-line replacements. All 256 records pass
static audit, with replacement payloads of 154–468 JSON characters, so the next
candidate can learn one compact format consistently.

## Current held result

v10 was trained from the uniformly replacement-conditioned corpus with the
additional minimality instruction. Its final validation loss was 0.0945 after
200 steps. The one-record local smoke test still expanded the replacement
toward the complete 7.8-KB source file. At the normal 1,024-token cap it
truncated; at 4,096 tokens it emitted 2,781 tokens but malformed JSON.

This is not a replay success and the adapter remains held. The combined
evidence indicates prompt-context copying: when the complete large repository
snapshot is present, the model reconstructs unchanged old/new context even
though every training target uses compact changed-line replacements. The next
design decision should therefore address the representation/context boundary
(for example, an explicit inspect-then-patch interface or a two-stage patch
emitter) before another model evaluation. No further evaluation was started in
this round.

The compact corpus itself passes static audit at 256/256 with zero failures,
and the CPU unit suite passes 23 tests with one skip.

## Bounded patch-emitter v5 result — 2026-09-01

The stage-two patch emitter was retrained after adding 60 local-shape records
matching the desktop repository patterns and explicit downstream diagnostic
offsets. The merged corpus contains 436 records (386 train / 50 validation).
Prompts use bounded numbered source windows and omit the full repository
snapshot, preventing the earlier full-file replacement copying behavior.

The v5 adapter produced valid exact-replacement JSON on all 20 local tasks and
all 20 replacements replayed exactly once. Compiler-backed evaluation passed
15/20, tying the earlier wide-context v3 result. The five failures were all
numeric-ratio tasks: each targeted the downstream canvas-size condition with
an unchanged old/new pair rather than the diagnostic source expression
containing `devicePixelRatio || "1"`.

The representation boundary is therefore successful for contract and replay
reliability, but semantic diagnostic localization remains the limiting factor.
Exact-gold matching is 0/20 and is retained as a strict diagnostic metric;
compiler success is the operational metric. The candidate remains held. The
next correction will add focused numeric source-localization examples and a
no-op replacement guard.

## Numeric source-localization correction prepared — 2026-09-01

The replacement contract now rejects unchanged pairs at both replay and
trajectory-validation boundaries. A focused 40-record supplement varies the
numeric fallback literal, source-file length, indentation, and downstream
diagnostic offset while explicitly naming the source expression as the edit
target. Static audit passes 40/40. Merging it with the prior patch-emitter
corpus produces 476 unique records (422 train / 54 validation), and the
prepared SFT artifact is ready for a separate isolated training run.

This is a data and contract correction only. No new candidate has been
trained, and v5 remains held pending review.

The subsequent v6 training launch was attempted twice. Both attempts exited
during model loading because an unrelated Python process occupied
approximately 15.7 GiB of the 16.3 GiB GPU. No checkpoint was produced, so
there is no v6 model result to interpret and no evaluation was started.

Before the next training attempt, bounded CPU replay found that the numeric
supplement's synthetic `window` declaration conflicted with the standard DOM
library. Replacing it with a non-conflicting desktop-style global fixed the
fixture; the first two records now pass compiler replay 2/2. The merged
source audit remains clean at 476/476, and the SFT artifact and manifest were
regenerated from the corrected source.

## Bounded patch-emitter correction

The v10 evidence showed that stronger replacement instructions were not enough
when the full 7.8-KB snapshot remained in the prompt. The model copied source
context into the replacement payload, so the correction must change the stage
boundary rather than only add more examples.

The trajectory stage retains repository inspection and compiler diagnosis. A
new stage-two patch emitter receives task/facts, compiler diagnostic, target
path, and a numbered bounded source window; its request deliberately omits
`repository_files`. `bounded_file_excerpt`, diagnostic location parsing, and
`build_patch_emitter_request` implement this boundary.

`scripts/prepare_patch_emitter_data.py` generated 256 preflight SFT records
(224 train / 32 validation). Prompts contain no full repository snapshots; the
largest is 1,351 characters and completions range from 190–513 characters. The
builder validates every replacement against the source before omitting that
source from the prompt. CPU coverage passes 25 tests with one skip. No
patch-emitter training or evaluation has started yet.
