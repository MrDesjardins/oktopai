# 08 — Source-derived trajectory collection

## Objective

Add public-source-informed teacher trajectories only when the source example is
paired with a repository snapshot, an explicit inspect/diagnose/edit/observe
trace, and independent compiler replay.

## Admission rules

- Keep source provenance, repository identity, and license-review metadata.
- Do not treat response-only `messages`/`completion` records as trajectories.
- Preserve the broken snapshot and the exact target path.
- Require a teacher trace using the shared trajectory contract.
- Replay every claimed compiler observation in an isolated checkout.
- Keep source-derived records separate from fixture-derived training and eval
  until overlap and license checks pass.

## Sequence

1. Locate an available local TypeScript repository checkout or approved source
   snapshot; do not download or upload data implicitly.
2. Select a narrow compiler-error family and record the original source path.
3. Generate a repository-shaped repair task with the smallest possible change.
4. Obtain a teacher trajectory, retaining raw output and model metadata.
5. Validate the contract and replay all observations independently.
6. Run `scripts/audit_trajectory_overlap.py` against every held gate.
7. Add only verified records to a separately manifested corpus.

## Current state

The local public-source datasets are response-only (2,450 records inspected).
Several clean local TypeScript repositories are available for reconnaissance,
but their checked-out roots have no visible license file and no trajectory
artifacts. Step 1 therefore remains gated on explicit provenance/license
metadata plus a repository snapshot suitable for replay. Existing
fixture-derived trajectory evidence remains valid but is not labeled
source-derived.

`scripts/inventory_trajectory_datasets.py` now exposes an admission predicate
that requires a non-empty trajectory, repository snapshot, public-source
repository provenance, and explicit `license_spdx_id` or license metadata.
The current public-source inventory reports 0 admissible records; this is an
intentional safety result, not a conversion failure.

Separately, a 20-record evaluation-only snapshot was generated from the clean
local `desktop-ai-companion` checkout. It is marked local-repository evaluation
provenance, not public-source training data. The original checkout remains
untouched; copied snapshots pass the local project verifier 20/20 and have
zero exact repair-pair overlap with training.
