# Runpod teacher-data experiment

## Objective

Use a temporary Runpod GPU to turn the 100,000 repository-grounded TypeScript
candidate tasks into valuable student-training data. The remote job must produce
reproducible, compiler-verified records and preserve every useful artifact for
future experiments.

This is a data-generation experiment, not an automatic model-promotion step.

## Data-safety and persistence design

The remote Pod is compute, not the source of truth. The source of truth remains
the local repository and its ignored `.oktopai/` artifact store.

Before starting:

1. Record the local Git commit, corpus SHA-256, task count, and source commit.
2. Upload a compressed copy of the candidate corpus and a manifest.
3. Store all remote work under `/workspace/oktopai-run/`.
4. Write outputs incrementally, not only at the end:
   - `teacher-answers.jsonl`;
   - `verified-training.jsonl`;
   - `rejected.jsonl`;
   - `metrics.jsonl`;
   - `run-manifest.json`.
5. Download checkpoints and outputs periodically and at completion.
6. Verify SHA-256 checksums locally before deleting the Pod.
7. Terminate the Pod only after the local manifest confirms every artifact.

For the first run, use Pod volume storage plus local transfer. A network volume
can be added later if repeated experiments justify its recurring storage cost.
The Pod is never the only copy of generated data.

## Remote workload

The Pod will run four resumable stages:

1. **Teacher generation**: answer candidate tasks in bounded batches and record
   raw outputs, prompt, model identifier, decoding settings, and timing.
2. **Verification**: extract TypeScript and run `tsc --noEmit --strict`; keep
   passing answers and retain rejected answers with diagnostics.
3. **Quality sampling**: calculate pass rates by task family, perspective,
   source file, and difficulty. Stop early if the teacher produces low-value
   outputs.
4. **Packaging**: produce student-ready JSONL and chosen/rejected preference
   candidates, with provenance and checksums.

The student will not train on raw teacher output. Only verified records enter
the training corpus.

## Teacher model decision

The first useful comparison should be:

- local Qwen2.5-Coder-7B baseline;
- remote Qwen2.5-Coder-14B-Instruct teacher, quantized for the A40;
- optional stronger teacher only if the 14B pass rate is inadequate.

The 14B teacher is preferred for the first remote run because an A40 has enough
VRAM for quantized inference and it should provide better repairs than the
0.5B student. A larger checkpoint must not be downloaded silently: its exact
size, license, quantization, and storage impact will be recorded before pull.

The value gate is not the teacher's prose quality. A teacher candidate is useful
only if it improves independently verified TypeScript outcomes. Initial gates:

- at least 60% strict-compiler pass rate overall;
- at least 40% in every selected task family;
- no single source file contributes more than 2% of accepted records;
- deduplicated accepted records are at least 10% of attempted tasks;
- at least 1,000 accepted records before a long student-training run.

If these gates fail, stop the remote run, retain diagnostics, and revise prompts
or teacher/model choice. Do not spend the remaining balance generating more of
the same low-quality data.

## Cost and termination guard

Use an A40 Pod with a fixed maximum runtime and explicit termination time. The
Pod is expected to be used for a short pilot first, not an unbounded overnight
job. Record compute hours, GPU price, storage cost, transfer size, accepted
records, and cost per accepted verified record.

The Pod must be terminated—not merely stopped—after verified artifacts are
downloaded. A stopped Pod can continue incurring storage charges.

## Execution order

1. Finish the current local focused-adapter run and record its result.
2. Create a local manifest and checksum for the 100k candidate corpus.
3. Provision the A40 Pod with bounded disk and SSH access.
4. Install the pinned remote environment.
5. Pull the approved teacher checkpoint and record its manifest.
6. Transfer the corpus and run a small 500-task pilot.
7. Inspect pass rate and family coverage.
8. Continue only if the pilot passes the value gates.
9. Generate the larger verified corpus in resumable batches.
10. Transfer, checksum, and validate all outputs locally.
11. Terminate the Pod.
12. Train 0.5B and 1.5B/3B students locally or on a later approved run.

## Failure recovery

If the connection fails, the manifest and JSONL offsets allow resuming from the
last completed batch. If the Pod disappears, the local copies remain the source
of truth. If a teacher answer is invalid, it is retained as a rejected example
for preference training rather than discarded without evidence.

## First provisioning attempt

The first A40 Secure Cloud Pod was created on 2026-08-26 at approximately
$0.44/hour with 50 GB persistent Pod storage. The container booted and reported
CUDA 12.8 and a ready SSH service, but the SSH proxy rejected the supplied local
ed25519 key. No corpus or model was uploaded. The empty Pod was terminated and
the Runpod account was confirmed to have zero Pods afterward.

Before retrying, register and verify the local public SSH key in Runpod account
settings or through `runpodctl` SSH-key setup. Pod creation should remain blocked
until a non-interactive SSH command succeeds.

## Successful pilot provisioning

On 2026-08-26 the registered key was accepted by a Secure Cloud A40 Pod:

- Pod: `9793s4612yjtgg` (`oktopai-typescript-teacher-pilot`)
- GPU: NVIDIA A40, 48 GB class, CUDA 12.8
- Image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- Persistent mount: `/workspace`, 50 GB
- Observed price: `$0.44/hour`
- Remote workspace: `/workspace/oktopai-run/`

The private GitHub repository cannot be cloned anonymously from the Pod. No
GitHub credential is copied to the Pod. Instead, the compressed corpus was
downloaded from the private release using a short-lived signed asset URL, and
the small remote teacher script was transferred from the checked-in commit.
Both compressed and decompressed corpus checksums matched the local manifest.

Ollama was installed inside the Pod and detected the A40 through CUDA. The
teacher checkpoint is `qwen2.5-coder:14b`; Ollama reported a 15 GB model and
loaded it at 100% GPU residency. A one-task smoke test completed successfully
in 10.6 seconds at 128 output tokens. The bounded pilot is running with 500
tasks, 384 maximum output tokens, and incremental JSONL persistence. It must
be inspected and verified before any larger paid generation run.

### GPU utilization and concurrency note

The A40 reports approximately 14.9 GiB used out of 46.1 GiB while the 14B
model is loaded at 100% GPU residency. This is expected: `100% GPU` describes
placement of the model, not filling every byte of VRAM. The quantized weights
are about 15 GB; the remaining VRAM is available for KV cache, larger context,
and concurrent sequences. The first pilot intentionally uses one sequential
request (`OLLAMA_NUM_PARALLEL=1`) so its latency measurements are easy to
interpret.

After the sequential quality gate, the next throughput experiment is bounded
concurrency: restart Ollama with one model, `OLLAMA_NUM_PARALLEL=4`, and a
smaller context limit, then run the teacher script with `--workers 4`. This
should improve aggregate records/second without loading four copies of the
weights. It may reduce per-request token/second, so both metrics must be
reported. Increasing concurrency is a throughput experiment, not a reason to
force VRAM allocation or claim that quality improved.

## Pilot result and closeout (2026-08-26)

The A40 pilot completed with 501 raw records: one smoke-test record plus 500
pilot tasks. The compressed input and raw output were copied locally and their
SHA-256 checksums matched the remote manifest.

Local strict TypeScript verification accepted 69 records and rejected 432,
which is a 13.8% acceptance rate over the 500 pilot tasks. Accepted examples
covered 9 of 10 families; the `test` family had no accepted records. This fails
the predeclared quality gates of 60% overall and 40% per family. The result is
valuable negative evidence, but it is not sufficient to train or promote a
student model. No larger paid teacher run was started.

A 20-record four-worker throughput sample completed in 118.067 seconds, about
0.169 records/second. The sequential pilot's mean generation duration was
15.32 seconds, about 0.065 records/second by generation-time estimate, giving
an approximate 2.6x aggregate throughput improvement. This is a small runtime
sample, not a quality comparison; individual concurrent requests were often
slower because they shared the GPU.

The fixed local route suite remained 100% accurate at 0.705 ms routing latency.
The normal Python suite passed 10 tests with one optional integration test
skipped. A live local Ollama endpoint was unavailable, so no new local
generation quality claim was made. The Pod should be terminated only after the
parallel sample and all checksums are confirmed locally.
