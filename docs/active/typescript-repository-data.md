# TypeScript repository-grounded data

## Current collection

On 2026-08-26, oktopai shallow-cloned the Microsoft TypeScript repository at
commit `8ac035a394c79e693a3a7d74cb170448503ee894` and extracted 2,450
conformance fixtures whose paths contain type-system signals such as generic,
narrowing, union, JSX, module, or mapped-type terminology.

The working JSONL is intentionally candidate-only:

`.oktopai/datasets/typescript-repository-candidates.jsonl`

It contains source context and a task prompt, but no trusted answer. The
tracked manifest records the source commit and SHA-256. The source checkout
and JSONL are ignored working artifacts; regenerate them with
`scripts/collect_github_source.py` and `scripts/extract_typescript_repo_tasks.py`.

## Quality rule

Raw repository code is not supervised data. TypeScript conformance fixtures
often contain intentional errors and compiler baselines. Every eventual
teacher answer must be normalized into the task contract, compiled with the
specified TypeScript version, and tested where the fixture has executable
behavior. Failed candidates remain in an audit log and never enter the
student corpus.

The next data builder must produce separate families for:

- minimal repairs with a compiler diagnostic;
- API and generic refactors with before/after behavior;
- module and declaration fixes;
- TSX/JSX repairs;
- compiler configuration and version migrations;
- tool trajectories: inspect, edit, compile, test, and summarize.

Train, validation, and test records must be split by repository fixture or
task family, not by near-duplicate lines. The fixed held-out project suite is
the release gate.

## Current decision

Do not retrain the 3B adapter from these 2,450 records yet. They are valuable
source material, but they need teacher answers and executable verification.
This prevents the next run from repeating the synthetic-data overfitting that
produced very low validation loss but poor Ollama quality.
