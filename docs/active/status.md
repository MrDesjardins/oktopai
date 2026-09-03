# Current status

## Real-repository trajectory gate — 2026-08-31

The first repository-shaped trajectory evaluation is complete. Eight held-out
snapshots of the local Next.js fixture passed independent project-level replay
(8/8). The lineage-correct safe-mixed adapter then produced 0/8
contract-valid trajectories; the base also produced 0/8. Outputs used schema
names outside the contract and often omitted a valid final event, so no model
trajectory reached replay. This is a transfer/schema failure, not a promotion
result. See [real-repository-trajectory-analysis.md](real-repository-trajectory-analysis.md).

Per the evaluation hold, no further model evaluation starts until this failure
and the prompt/schema mismatch are analyzed.

The first correction round is complete: trajectory prompts now explicitly
include the event/tool/ordering contract, and the 160-record safe-mixed corpus
was regenerated without the real-repository test records. A separate
contract-conditioned adapter trained for 200 CUDA steps (361.4 seconds), with
final train loss 0.1901 and validation loss 0.1288. One controlled evaluation
of this candidate is now justified; no promotion or export is authorized.

That evaluation completed at 0/8 contract-valid. Four outputs were malformed
or truncated JSON and four had missing integer observation exit codes; several
edited unrelated project files. The next CPU correction makes the known TS7053
location explicit and increases the output cap to separate truncation from
repair quality.

The single-line adapter evaluation reached 8/8 contract-valid and 4/8
independent full-project replays. The four failures omitted a successful
post-edit diagnosis or stopped after a failed observation. The validator now
rejects that false-success pattern; the normalized 160-record corpus passes
160/160 and the unit suite passes 13 tests. The next step is retraining with
the stricter post-edit verification requirement.

That retraining produced v6 with train loss 0.1068 and validation loss 0.1106,
but its raw real-repository contract score regressed to 0/8. A conservative
normalizer recovered four schema-shaped outputs, yet all four still failed
project replay because their generic indexing repair was not compiler-valid.
The best reliable result remains v5 at 4/8 executable replays; no candidate is
promoted.

The supplement-trained report was additionally checked through the conservative
normalizer: raw validity was 0/8, normalized validity 4/8, and normalized
replay 4/4. The evaluator now records raw versus normalized contract metrics
separately. This improves execution interoperability but does not yet improve
native model quality or justify promotion.

The next schema-conditioned adapter achieved 8/8 raw contract-valid and 8/8
independent full-project replays on the unchanged repository suite. It used
the correct `keyof` repair in `lib/getValue.ts` across the records. Training
took 353.5 seconds with train loss 0.0993 and validation loss 0.1169. This is
the strongest real-repository result so far, but the eight-task gate remains
diagnostic and the adapter is not promoted.

The follow-up at a 1024-token cap reached 4/8 contract-valid, but 0/4
independent replays passed because the edits contained literal escaped newline
text and the claimed exit code did not match the real project. A third
isolated adapter added explicit file-content escaping semantics and completed
200 CUDA steps with train loss 0.183 and validation loss 0.1338. Its bounded
real-repository check is next.

## CPU checkpoint — 2026-08-30

The CPU review is complete. The complete evidence currently ends at v3 step 5,000. The step-8,000 reports remain partial (91/200 canonical records and 16/200 max-64 records); a chunked recovery attempt produced no completed chunk and was stopped. They are preserved as diagnostics only.

The trajectory contract, independent verifier, and trajectory corpora are implemented and tested. The original 20-record seed remains preserved; a new v2 corpus contains 100 independently replayed records across five balanced TypeScript repair families. See [analysis-current.md](analysis-current.md).

A separate CPU-constrained 8,000-step follow-up completed under
`...-cpu64-adapter-only.json` with 200 unique records. It contains 52 explicit
generation timeouts and a 64-token cap, so it is diagnostic only; the adapter
is held and not promoted.

## Current research checkpoint — 2026-08-30

The TypeScript v3 mixed-corpus experiment completed training through 8,000
steps on the GPU, but its automatic 200-task evaluation was intentionally
stopped after 68 records. That partial report is not evidence and must not be
resumed or compared as a complete result until explicitly approved.

Complete fixed-seed results currently available:

| Artifact | Verified | Average score | Average speed |
|---|---:|---:|---:|
| Qwen2.5-Coder-3B base | 94/200 | 0.740 | 46–47 tok/s |
| v2 adapter | 123/200 | 0.814 | 28.2 tok/s |
| v3 at 3,000 steps | 140/200 | 0.800 | 27.5 tok/s |
| v3 at 5,000 steps | 133/200 | 0.840 | 27.9 tok/s |

The results show improvement over the base but instability across checkpoints,
not a monotonic training curve. The v3 3,000-step checkpoint was stronger on
discriminated unions and generic indexed access; the 5,000-step checkpoint
recovered record dictionaries and object constraints but regressed some of
those earlier gains. Async-return remains weak at 0/28. The adapters are also
substantially slower than the base in the current independent Transformers
evaluation.

The v3 artifact is a valid PEFT LoRA adapter for the local
Qwen2.5-Coder-3B base. It remains experimental: do not promote, export,
register, upload, or evaluate the incomplete 8,000-step report without a new
decision.

The isolated trajectory-aware adapter was trained for 200 CUDA steps from the
frozen 20-record seed corpus. On its two held-out synthetic records, both
adapter outputs were contract-valid and passed independent replay; the base
model failed the trajectory contract on both. This is a pipeline signal only,
not a quality or generalization claim.

The expanded v2 trajectory corpus is now frozen as a CPU preflight artifact:
100 raw records and 100 SFT records, five families at 20 records each, with
80 train and 20 validation records. Independent replay passed 100/100 records;
the SFT manifest records the source and output hashes. The isolated v2 adapter
then completed 200 CUDA steps in 353.8 seconds with training loss 0.2219 and
validation loss 0.2069. Held-out generation/evaluation is intentionally still
pending; these losses do not establish trajectory quality or generalization.

The subsequent held-out v2 trajectory check generated 20/20 adapter outputs
that satisfied the trajectory contract, and independent replay passed 20/20.
The base produced 0/20 contract-valid outputs. The adapter averaged 9.45
seconds and 257 tokens per record versus 5.19 seconds and 232 tokens for the
base. Because the split is synthetic and family-aligned with training, this is
strong format-learning evidence but not a generalization or promotion result.

An unseen-family transfer check was independently fixture-verified at 50/50
across five families not used in v2 training. The v2 adapter produced
contract-valid output for 50/50 records, but executable replay passed 35/50:
all failures were concentrated in array-union (5) and record-method (10).
The base produced 0/50 contract-valid outputs. Adapter generation averaged
9.92 seconds versus 5.93 seconds for the base. This is useful transfer
evidence, but the synthetic task design and failure concentration mean the
adapter is still not ready for promotion.

The failure analysis is recorded in
[`trajectory-transfer-failure-analysis.md`](trajectory-transfer-failure-analysis.md).
The two concrete gaps are incorrect narrowing of numeric record values and
incorrect use of boxed `Number` checks for primitive array unions. The current
50-record test set remains untouched for future comparison.

The targeted follow-up tranche is now ready at
[`targeted-trajectory-followup.md`](targeted-trajectory-followup.md): 40
records focused on those two gaps, independently replayed 40/40, with 30
training and 10 validation records. It is frozen for a separate training
decision.

The targeted adapter then completed its isolated 200-step CUDA run in 323.9
seconds, with training loss 0.2342 and validation loss 0.01153. The tiny
validation loss is treated as fitting evidence only; targeted held-out replay
is still pending.

The targeted adapter’s balanced transfer check is now complete: on the same
50-record unseen set, record-method replay improved from 0/10 to 10/10, while
array-union replay fell from 5/10 to 2/10. Overall 41/49 contract-valid
outputs passed replay, with one contract-invalid output. This is a partial
capability improvement with regression risk, not a promotion result.

The redesigned targeted v2 corpus is now frozen with 60 records and balanced
validation coverage across four families: 48 train, 12 validation, and 60/60
independent replay. It includes the two target families plus discriminated-
union and object-literal regression-protection families. No training has
started from this redesigned corpus.

The redesigned targeted v2 adapter has now completed its isolated 200-step CUDA
run in 348.3 seconds, with training loss 0.2408 and balanced validation loss
0.003563. The validation set is small and synthetic; transfer evaluation on
the unchanged 50-record test set remains pending.

The redesigned targeted v2 adapter passed its balanced internal validation
12/12, but the unchanged unseen transfer check passed only 36/49 valid outputs.
Primitive array-union replay fell to 0/10, and four outputs added an invalid
extra diagnose/observe sequence. The candidate is rejected for promotion; the
low internal validation loss did not predict transfer quality.

The safer foundation-plus-targeted mix is now frozen at 160 unique records:
the original 100-record v2 foundation plus the 60-record targeted v2 tranche.
It contains 128 train and 32 validation records, and independent replay passed
160/160. This corpus is ready for one isolated follow-up run; the unchanged
50-record unseen test remains outside training.

The safe-mixed adapter has completed its isolated 200-step CUDA run in 404.9
seconds, with training loss 0.2596 and validation loss 0.1303. Its larger
mixed validation set avoided the near-zero loss seen in the narrow targeted
run; balanced executable evaluation remains pending.

The safe-mixed adapter passed balanced validation 32/32 by independent replay,
then passed the unchanged 50-record unseen transfer test 50/50. It produced
50/50 contract-valid outputs versus 0/50 for the base. Adapter generation
averaged 9.41 seconds per record versus 5.50 seconds for the base. This is the
strongest trajectory result so far, but it remains synthetic evidence and is
not a promotion decision.

The next CPU-only work is documentation and implementation of the tool-use
distillation path described in `tool-using-specialists.md`. Current training
still distills verified prompt-to-answer completions; it does not yet teach
inspect/diagnose/edit/compile/retry trajectories.

The historical notes below preserve earlier milestones and are intentionally
retained for experiment provenance.

## Working

- Ollama runtime discovery and model listing.
- Local generation with `qwen2.5-coder:7b`.
- Five local prompt-specialized Ollama aliases created from the qwen2.5-coder base.
- Repository-local training stack installed and import-verified; PyTorch reports CUDA unavailable.
- A real TypeScript LoRA adapter was trained locally from `Qwen/Qwen2.5-Coder-0.5B-Instruct`; its manifest and checksums are in `.oktopai/adapters/typescript-v1/manifest.json`.
- The adapter was merged into a standalone Transformers checkpoint and loaded successfully; Ollama Safetensors quantization was tested but crashed in Ollama's MLX path, so no trained Ollama model was created.
- llama.cpp was built locally, the merged checkpoint was exported to a 380 MB Q4_K_M GGUF, registered in Ollama as `oktopai-typescript-trained-q4`, and exercised with a local inference request.
- The two-model benchmark measured the 397 MB trained model at approximately 608 tokens/second and 0.80 seconds/task versus 148 tokens/second and 2.32 seconds/task for the 4.7 GB prompt-specialized model; quality was 7 failures versus 1 failure across the eight-task set.
- The v2 failure-focused dataset contains 17 records and produced a registered `oktopai-typescript-trained-v2-q4` artifact. The three-way benchmark showed no quality improvement over v1: both trained versions had 7 failures and 1 checklist pass.
- v3 now uses strict TypeScript dataset filtering, chat-template formatting, completion-only loss masking, and dynamic padding. The first 14-record v3 run completed with training loss 0.879 and validation loss 1.066; its two-task check still failed generics and passed narrowing.
- Next.js 16.3.2 benchmark fixture installed with zero npm audit vulnerabilities.
- Deterministic routing without a runtime.
- Shared logical experts mapped to one physical model.
- Cross-process detection of Ollama's loaded model state.
- Preload, keep-alive, unload, and lifecycle telemetry.
- Session reconstruction with bounded context.
- Versioned benchmark task corpus.
- Route-only and live benchmark runners.
- Raw output and timing persistence.
- Checklist and Python compilation verification.

## Measured

- qwen2.5-coder:7b generated the initial five-case benchmark in roughly 0.4–7.4 seconds per response.
- Installed larger models showed substantial cold-load and memory costs.
- Routing accuracy on the initial synthetic set was 100%; this set is too small to claim router quality generally.
- A repository review exposed a concrete hallucinated fix, proving the need for executable verification.
- The first versioned eight-task benchmark routed 8/8 tasks correctly after adding file/import context.
- The updated live qwen2.5-coder:7b run produced 4 fixture-contract passes, 2 executable verification passes (SQL and Python), 1 checklist pass, and 1 failed TypeScript check.
- Live generation times for the eight tasks ranged from approximately 1.25 to 3.84 seconds; routing took approximately 0.6 ms.

## Not yet proven

- A distilled specialist outperforming the shared qwen baseline.
- A LoRA adapter outperforming prompt specialization.
- Reliable two-model simultaneous residency on this WSL environment.
- GPU VRAM capacity; `nvidia-smi` is blocked in the current environment.
- TypeScript, React, Next.js, and Vitest tasks passing real project-toolchain validators.
- The current TypeScript/React/Next.js/Vitest fixture contracts are not full compiler or runtime tests; installing project-local tools or adding hermetic tool containers is the next verification step.
- A persistent oktopai daemon with lifecycle state across requests.
- A learned adapter outperforming prompt specialization. Executable held-out evaluation shows both base and adapter passing narrowing and failing the generic task, with approximately equal throughput (~30 tokens/second).
- An Ollama-loadable export of the adapter. The PEFT artifact is tied to the 0.5B Transformers base, while active Ollama aliases use a separate 7B GGUF lineage.
- A trained specialist outperforming the prompt-specialized baseline. The exported model runs, but its first generic response was still invalid; quality remains unproven.
- A compiler-verified 10,000-record synthetic TypeScript corpus now exists across ten families. The combined v5 corpus contains 10,014 records: 7,537 train, 1,497 validation, and 980 test. This is data expansion only; no quality claim is made until a trained artifact passes the held-out suite.
- A bounded v4 training run used 100 optimizer steps from the 10k corpus in 8m45s on CPU, reaching training loss 0.796 and validation loss 0.400. Its two-task executable check still failed, so v4 is not exported or promoted.
- A local teacher batch generated 25 TypeScript traces from the 7B specialist; 13 passed extracted-code compilation and were added to the 10,000-record foundation, producing a 10,024-record v6 corpus.
- A v5 large-corpus adapter trained 150 steps with completion-only masking in 8m03s on CPU, reaching training loss 0.559; it still failed both initial real TypeScript checks and was not exported. A 400-step continuation was stopped at step 162 after CPU slowdown made the run inefficient.

## Next milestones

1. Expand executable TypeScript fixture coverage beyond the current two-file repair.
2. Create the first specialist dataset from verified failures and fixes.
3. Add hermetic TypeScript/React/Next.js/Vitest toolchain fixtures.
4. Expand the TypeScript dataset beyond the current seed/candidate count.
5. Run executable held-out evaluation for the 0.5B base and adapter.
6. Add license-reviewed repository tasks and compiler-filtered teacher traces to the 10k synthetic foundation.
7. Run a full one-pass training experiment on the large corpus with controlled CPU/GPU resource measurement and evaluate the 980-record test split.
8. Export and benchmark the best TypeScript artifact before starting CSS, React, or Next.js corpora.
9. Distill a narrow TypeScript micro-expert and measure capability per GiB.
## Latest research run (2026-08-24/25)

- Added an append-only JSONL experiment ledger at `experiments/runs.jsonl` and
  documented its measurement policy in `docs/research/experiment-ledger.md`.
- Downloaded a shallow public `microsoft/TypeScript` checkout locally at commit
  `8ac035a394c79e693a3a7d74cb170448503ee894`; the manifest records 65,905 files
  and license files. Raw source is kept separate from training truth.
- Extracted 1,000 compiler-conformance candidates. A local teacher generated
  100 traces; 25 passed the independent `tsc --strict` filter and 75 were
  rejected. The resulting v7 corpus has 10,036 records.
- Trained `typescript-v7` with completion-only loss for 300 optimizer steps on
  CPU: 967.1 seconds, 0.31 steps/sec, reported training loss 0.372.
- The current two-task executable held-out gate remains failed for both base
  and adapter outputs. v7 is therefore not exported or promoted. This is a
  quality result, not a reason to claim specialization: the next work is a
  larger held-out task suite and better teacher/label filtering.
- The generated benchmark now contains 3,000 TypeScript tasks. A randomized
  20-task v7 evaluation produced 8/20 compiler-verified responses for both the
  base and adapter, with average verification score 0.45. Average generation
  speed was 27.74 tok/s for the base and 27.83 tok/s for the adapter. The
  adapter remains unpromoted because it is not measurably better.
- `train_lora.py` now supports `--device auto|cpu|cuda`, resumable checkpoints
  with `--resume`, and step-based checkpoint retention. CUDA explicitly fails
  with an actionable error when the host does not expose a device.
- GPU passthrough was verified with local runtime access: WSL exposes
  `/dev/dxg`, CUDA 13.2, and an NVIDIA GeForce RTX 5080 with 15.92 GiB VRAM;
  PyTorch reports CUDA available. The v8 1,000-step run completed in 685.4
  seconds at 1.459 steps/sec with loss 0.2339, versus 0.31 steps/sec for the
  earlier CPU run.
- Added 3,000 deterministic preference candidates; 1,785 passed family-level
  compiler verification and are stored locally for preference-training work.
  Added a strictly test-split 980-task benchmark. On a randomized 20-task CUDA
  sample, both base and v8 verified 1/20 with average score 0.208, so v8 is not
  promoted.
- The 1/20 result was traced to a benchmark defect: generated prompts omitted
  their source code. The benchmark generator now embeds each source fixture in
  the prompt. On the corrected suite, v8 and the base each verified 8/20 with
  average score 0.617; v8 generated faster (40.64 versus 38.11 tok/s) but did
  not improve quality.
- Added an actual TRL DPO path. DPO v1 trained on 1,000 verified pairs for 300
  CUDA steps in 218.5 seconds with reward accuracy 1.0 during training. Its
  held-out sample verified 6/20 at average score 0.567, so it is not promoted;
  the next comparison must rerun base, SFT, and DPO under one identical batch
  and improve prompt/tokenization consistency.
- Added 200 more public TypeScript repository teacher traces; 48 passed the
  local compiler filter. The resulting v8-data corpus contains 10,058 records.
  A 500-step CUDA SFT run on it completed in 334.5 seconds with loss 0.2975,
  but its 20-task held-out sample still tied the baseline at 3/20 under the
  unified chat-template evaluator. A 2,000-step multi-epoch run is currently
  in progress to test whether the issue is undertraining rather than data
  coverage.

## Latest overnight follow-up (2026-08-25)

- The overnight 2,500-step CUDA SFT completed and produced
  `.oktopai/adapters/typescript-overnight-sft`. Its first 200-task report was
  not a valid base-versus-adapter comparison because both labels shared one
  mutable base model instance.
- `scripts/evaluate_adapter.py` now loads independent base and adapter-base
  instances. A corrected 20-task CUDA check produced different outputs on all
  20 tasks; the adapter is therefore not silently identical to the base. The
  20-task result is diagnostic only and is not a promotion gate.
- Added `scripts/run_autonomous_typescript.py`, an unattended queue that can
  generate 50,000 compiler-verified synthetic coverage records, train a
  5,000-step CUDA candidate, evaluate it independently, and append every stage
  to the experiment ledger. It is designed to run locally without cloud APIs.
- The 200-task independent evaluation should be rerun before interpreting the
  overnight quality result. No model is promoted until the disjoint suite,
  family gates, and Ollama GGUF speed measurements pass.
- The second fixed-seed 100-task evaluation reproduced the direction of the
  gain: the base verified 21/100 with score 0.402, while `typescript-v3-5000`
  verified 30/100 with score 0.633. Family analysis shows strong gains on
  generic-indexed-access and object-constraint, but failures remain on async,
  unions, mapped types, overloads, and record dictionaries. This is evidence
  for targeted data expansion, not promotion.

## Latest real-repository correction

- Expanded the disjoint project-level gate to 40 tasks across five families.
- The schema-conditioned candidate previously replayed 32/40; all eight
  failures were union-narrowing tasks with unusable escaped file content.
- Added and independently verified 12 union-narrowing training exemplars.
- The merged 184-record corpus passed the mixed CPU verifier 184/184.
- The isolated union candidate trained for 200 CUDA steps and achieved
  40/40 native contract validity and 40/40 independent full-project replay.
- Family replay: generic lookup 8/8, async return 8/8, union narrowing 8/8,
  array narrowing 8/8, object/record mismatch 8/8.
- This remains a bounded candidate result; no promotion, export, or upload has
  occurred.

## Broader transfer gate

- The 80-task evaluation-only v3 repository gate passed CPU replay 80/80.
- The union candidate achieved 72/80 native contract validity and 72/72
  replay among generated records.
- Nine families passed 8/8; discriminated unions failed 0/8 because outputs
  were malformed/schema-like.
- Added a 12-record discriminated-union supplement; merged 196-record corpus
  passes mixed replay 196/196.
- Prepared the v2 SFT artifact against the local Qwen2.5-Coder-3B base.
- Next step is isolated correction training; no new evaluation has started.

## Envelope correction

- The discriminated-union candidate reached 71/80 native validity and 71/71
  replay; discriminated unions remained 0/8 due to malformed outer envelopes.
- Updated the shared contract and training prompt to require `trajectory` as
  the first key, only `trajectory`/`final` at top level, and no copied schema
  fields.
- Unit regression remains 15/15 passing.
- Prepared the 196-record envelope-conditioned SFT artifact; training is the
  next isolated step.

## Envelope correction result

- Envelope-conditioned adapter trained for 200 CUDA steps: train loss 0.1052,
  final validation loss 0.0934.
- On the 80-task gate: 80/80 native contract-valid, 80/80 independent
  full-project replay, and zero normalization.
- All ten families passed 8/8, including discriminated unions.
- CPU contamination audit: zero training/evaluation ID overlap and zero exact
  broken/fixed pair overlap.
- Evidence is still limited to the controlled local fixture; candidate remains
  held with no promotion, export, or upload.

## Multi-file evaluation gate

- Generated a 60-task evaluation-only gate with imported helper/type files and
  decoy files across six cross-file families.
- Independent full-project replay: 60/60.
- Training/evaluation overlap audit: zero IDs and zero exact repair pairs.
- The gate is ready for a controlled held-candidate evaluation; no evaluation
  has started yet.

## Multi-file gate result

- Envelope-conditioned adapter: 60/60 native contract-valid and 60/60
  independent full-project replay, with zero normalization.
- Six cross-file families all passed 10/10.
- Base model: 0/60 parseable/contract-valid on the same gate.
- This remains controlled local evidence; the adapter is held pending broader
  repository coverage and systems review.

## Evaluation infrastructure

- `evaluate_trajectory_adapter.py` now emits per-family summaries for base and
  adapter parseability, raw validity, normalized validity, and normalization.
- CPU regression suite: 16/16 passing; modified evaluator and new audit/gate
  scripts compile successfully.

## Source-derived trajectory gap

- Local TypeScript-derived datasets were inventoried: 2,450 records each,
  zero trajectory records, and zero repository snapshots.
- They remain excluded from trajectory claims rather than being treated as
  tool-use supervision.
- Added `scripts/inventory_trajectory_datasets.py` to enforce this distinction.
- Local clean TypeScript repositories were found, but no visible license
  metadata or trajectory artifacts make them admissible yet; no source-derived
  data was copied or used.
- Admission is now machine-checked: trajectory, repository snapshot,
  repository provenance, and explicit license metadata are all required.
- Current public-source inventory: 0 admissible records.

## Corpus preflight

- Added `scripts/audit_trajectory_corpus.py` for duplicate-ID, split/family,
  snapshot, and contract checks before training.
- Current 196-record corpus: 196 unique IDs and zero static failures.
- CPU unit suite remains 19/19; compiler replay remains independently
  required.

## Large-file transfer failure

- Local desktop gate exposed 43–111-character snippets emitted for a 7.8-KB
  target file; structural validity was 20/20, but executable replay was 0/20.
- Added `incomplete_edit_content` validation for large repository targets.
- Propagated complete-file requirements to schema, training prompts, and
  evaluator prompts.
- Mixed corpus remains 196/196; CPU tests now pass 20/20.
- No evaluation started after this correction.

## Compact replacement correction

- Added deterministic exact once-only `args.replacements` edit support across
  schema, validator, and replay lanes.
- Added integration coverage; CPU tests now pass 22/22.
- Added 12 synthetic long-file exemplars; merged training corpus is 208
  records (176 train / 32 validation), static checks pass, and mixed replay is
  208/208.
- Prepared the replacement-conditioned SFT artifact; no new evaluation has
  started.

## Trajectory safety hardening

- Validator now rejects absolute/parent-traversal paths and shell
  metacharacters or command chaining.
- Full mixed corpus remains valid: 196/196.
- CPU unit suite: 17/17 passing, including safety regression coverage.

## Trajectory ordering hardening

- Validator now requires diagnosis before editing and after the final edit.
- Mixed corpus remains 196/196 independently replayed.
- CPU unit suite: 19/19 passing.

## Contract consistency

- Updated the legacy real-repository generator with the shared outer-envelope
  contract.
- Contract copies across evaluator, preparer, generator, and schema are now
aligned; CPU tests remain 19/19.

## Local repository evaluation gate

- Generated 20 evaluation-only snapshots from clean local
  `desktop-ai-companion`.
- Local project verifier: 20/20.
- Training overlap audit: zero IDs and zero exact repair pairs.
- Original checkout was not modified; this data is not admitted to training.

## Replacement distribution correction

- First replacement candidate: 0/20 valid on the local long-file gate; all
  failures were incomplete content rather than replacement edits.
- Expanded the replacement supplement from 12 to 60 verified long-file
  exemplars.
- New corpus: 256 records (224 train / 32 validation), 256 unique IDs, zero
  static failures, and 256/256 mixed replay.
- Prepared the larger replacement-conditioned SFT artifact; training is next.

## Replacement conditioning diagnosis

- v7 trained on the mixed 256-record corpus and still emitted abbreviated
  `content` on 20/20 local tasks; lower validation loss did not change that
  behavior.
- The evaluator now runs base and adapter models sequentially after a CUDA OOM
  exposed simultaneous residency; it also has a bounded `--limit` smoke test.
- v8 selected replacements but initially used whole-file pairs, producing a
  massive output that truncated at 1,024 tokens.
- The converter now derives minimal changed-line replacements. All 256 records
  pass static audit, with replacement payloads of 154–468 JSON characters.

## Current held result

- v10 trained with the minimal-replacement contract; final validation loss was
  0.0945 after 200 steps.
- A one-record local smoke test still expanded the replacement toward the full
  7.8-KB file. At a 1,024-token cap it truncated; at 4,096 tokens it produced
  2,781 tokens but malformed JSON. It is therefore not promoted or replayed.
- The evidence now points to prompt-context copying: providing the complete
  large repository snapshot causes verbose old/new reconstruction despite
  compact replacement targets. No further model evaluation is started in this
  round.
- Final checks: compact corpus static audit 256/256 with zero failures; unit
  suite 23 tests, 1 skipped, all executed tests passing.

## Bounded patch-emitter correction

- Added diagnostic-to-source-window helpers and a stage-two patch-emitter
  request that omits complete `repository_files` from the model context.
- Added `scripts/prepare_patch_emitter_data.py`: 256 records (224 train / 32
  validation), maximum prompt size 1,351 characters, completion size 190–513
  characters, and no full snapshots in emitted prompts.
- Added two unit tests for diagnostic location parsing, numbered bounded
  excerpts, and snapshot exclusion. CPU suite now passes 25 tests with 1 skip.
- No patch-emitter training or evaluation has started; the v10 adapter remains
  held pending review of this representation correction.

## Bounded patch-emitter v5 — 2026-09-01

- Added 60 local-shape examples with downstream diagnostic offsets; merged
  corpus: 436 records (386 train / 50 validation), statically audited and
  replay-clean.
- v5 training completed 200 CUDA steps in 353.4 seconds; final validation
  loss was 0.00751.
- Compiler-backed local gate: 20/20 contract-valid, 20/20 replacement replay,
  15/20 project-compiling, and 0/20 exact-gold matches.
- The five failures are all numeric-ratio cases. The model emits an unchanged
  replacement for the downstream canvas condition instead of changing the
  diagnostic source expression `devicePixelRatio || "1"` to `|| 1`.
- This ties the prior v3 compile result and is not a promotion signal. v5 is
  held; the next correction targets numeric diagnostic-source localization
  and rejects downstream no-op replacements.

## Next correction prepared — 2026-09-01

- Replacement application and trajectory validation now reject unchanged
  `old == new` pairs; the CPU suite passes 25/25 tests.
- Generated and statically audited 40 focused numeric source-localization
  examples: 40 unique records, 36 train / 4 validation, zero failures.
- Merged them with the existing patch-emitter source corpus: 476 unique
  records, 422 train / 54 validation, zero static failures.
- Prepared the next bounded-emitter SFT artifact and manifest. Training is
  intentionally not started in this round; v5 remains the held benchmark.
- A v6 training launch was attempted twice, but both processes exited during
  model loading because the GPU was already using 15,741/16,303 MiB through
  an unrelated `/python3.14` process. That process was not interrupted. No
  v6 checkpoint exists and no v6 evaluation has started.
- CPU replay initially exposed a synthetic `window` declaration conflict with
  the DOM library in the numeric supplement. The fixture now uses a
  non-conflicting desktop-style global; the corrected sample passes compiler
  replay 2/2, the source audit remains 476/476, and the SFT artifact/manifest
  were regenerated.
- Added `scripts/audit_patch_emitter_sft.py`. The prepared v6 SFT passes its
  dedicated preflight: 476/476 unique records, 422 train / 54 validation,
  prompt isolation, valid compact completions, no no-op replacements, and
  zero failures.
- Added bounded `--limit` and concurrent `--jobs` support to
  `verify_trajectory.py`. The two-record numeric compiler sample passes 2/2;
  the full 40-record compiler replay exceeded a 180-second CPU bound even
  with four workers, so full compiler verification remains pending and is not
  being represented as complete.
- Latest GPU inspection still shows 15,360/15,978 MiB used (618 MiB free), so
  v6 training remains safely deferred; no checkpoint or evaluation exists.
- A later full supplement replay with four workers and a 300-second bound
  also timed out without a completed report. The verified compiler evidence
  is therefore limited to the corrected 2/2 sample; the 40-record compiler
  gate remains pending rather than being marked successful.
- Added explicit `diagnostic_locations` and a source-localization rule to the
  bounded emitter target. The regenerated v7 SFT contains 476 records (422
  train / 54 validation) and passes the dedicated preflight 476/476 plus the
  26/26 CPU unit suite. It is prepared but not trained or evaluated.
- Final CPU integrity pass is clean: `git diff --check`, Python compilation,
  and the v7 SFT preflight all completed successfully. CUDA inspection timed
  out before execution, so v7 remains untrained and unevaluated.
- A subsequent CUDA query completed and reports 15,648/15,978 MiB used with
  only 330 MiB free. v7 training remains deferred; no checkpoint or
  evaluation has been created.
- Added a regression test that checks large snapshot content is bounded in
  the emitter prompt, not merely omitted as a top-level key. The targeted
  test passes; the previously confirmed 26-test suite remains intact after
  the import fix.

## v7 training and gate result — 2026-09-01

- Direct host checks confirmed the RTX 5080 and PyTorch CUDA availability;
  the earlier sandbox NVML error was an environment visibility issue, not a
  GPU failure.
- The isolated v7 bounded patch-emitter adapter trained for 200 CUDA steps in
  368.6 seconds and saved under
  `.oktopai/adapters/typescript-patch-emitter-v7-source-localization`.
- Final train loss was 0.05131 and validation loss was 0.01107. One
  intermediate validation pass hit a recoverable CUDA OOM; subsequent passes
  completed and the process exited successfully.
- The correctly prepared unchanged 20-record local gate reached 15/20 raw
  contract-valid, 15/20 replacement replay, 15/20 compiler-successful, and
  0/20 exact-gold matches.
- All five failures were unchanged downstream canvas-condition replacements,
  so v7 ties the held v5 compiler baseline rather than improving it. The
  candidate remains held and is not promoted.
- The first 54-record evaluation attempt used a prompt/source mismatch and is
  retained only as a diagnostic; it must not be cited as model evidence.
- A host-context heartbeat records GPU, memory, disk, and process state at
  `.oktopai/logs/pc-heartbeat.log` during unattended work windows.

## v9 corrected corpus training and gate — 2026-09-02

- Repaired the generic verifier to derive the target path from each edit and
  use standalone `es2020` compilation for synthetic fixtures.
- Corrected malformed legacy local-shape fixtures; the full merged source
  corpus now independently replays 516/516.
- Trained isolated v9 for 200 CUDA steps in 340.2 seconds. Final train loss
  was 0.04946 and validation loss was 0.008005.
- The unchanged 20-record local gate produced 15/20 contract-valid, 15/20
  replacement-replay-valid, 15/20 compiler-successful, and 0/20 exact-gold
  matches.
- The five failures again chose unchanged downstream canvas-condition
  replacements. v9 ties v5 and v7 and is held without promotion.
- No broader evaluation, export, upload, or registration is authorized from
  this result.

## Verifier hardening follow-up — 2026-09-02

- `verify_trajectory.py` now derives the compiler target from the recorded edit
  path and automatically prefers the desktop project’s TypeScript compiler
  when available.
- Standalone synthetic replay explicitly uses `--lib es2020` to avoid DOM
  global collisions in isolated fixtures; the real-project verifier is
  unchanged.
- The corrected 516-record source corpus passes full independent replay
  516/516, and the default compiler-path smoke test passes 1/1 without a
  manual `--tsc` argument.
- The next candidate remains a representation-level correction for the five
  numeric downstream no-op failures. No additional training is authorized
  until that hypothesis is encoded and audited.

## Numeric localization correction v8 — 2026-09-02

- Added `scripts/generate_patch_emitter_numeric_variants.py` with 40 varied
  numeric fallback examples covering `||`, `??`, ternary, and conditional
  fallback forms.
- The supplement independently replays 40/40 with the desktop TypeScript
  compiler and has zero duplicate IDs against the existing source corpus.
- Merged source corpus: 516 unique records, 458 train / 58 validation.
- Prepared v8 bounded-emitter SFT: 516/516 static audit pass, no full snapshots
  in prompts, compact replacement completions, and zero no-op replacements.
- A full replay through the legacy generic verifier reported 400/516 because
  that verifier hardcodes `src/index.ts` and is incompatible with 116 existing
  multi-shape records. This is a verifier-lane limitation, not evidence
  against the new 40-record supplement; the new supplement’s explicit 40/40
  compiler replay remains the valid result.
- v8 training has not started. The v7 adapter remains the held benchmark.

## Window-specific numeric correction v10 — 2026-09-02

- Added 24 `window.devicePixelRatio`-specific examples; the supplement
  independently replays 24/24 with the desktop TypeScript compiler.
- Merged source corpus: 540 unique records, 480 train / 60 validation. The
  prepared SFT passed the 540/540 static audit and full compiler-backed replay.
- Trained isolated v10 for 200 CUDA steps on the RTX 5080. The adapter was
  saved successfully; final train loss was 0.05236 and validation loss was
  0.01449.
- The unchanged 20-record local gate produced 15/20 contract-valid, 15/20
  replacement-replay-valid, 15/20 compiler-successful, and 0/20 exact-gold
  matches.
- The same five downstream canvas-condition no-op failures remain. v10 ties
  v5, v7, and v9, so it is held without promotion, export, upload, or
  registration.
- Final regression checks passed: 28 unit tests (1 skipped), Python compile,
  heartbeat shell syntax, and `git diff --check`.
