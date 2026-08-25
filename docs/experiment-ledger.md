# Experiment ledger

`experiments/runs.jsonl` is the append-only project record for data, training,
conversion, runtime, and benchmark work. Every long-running operation should
write a `started` event before work and a terminal event afterwards. This makes
progress measurable across sessions and prevents speed numbers from being
separated from quality and provenance.

Each event contains:

- `kind`: dataset, source, teacher-data, training, export, runtime, or benchmark;
- `name`: stable experiment identifier;
- `status`: started, completed, stopped, or failed;
- `metadata`: counts, commit hashes, wall time, hardware, losses, pass rates,
  model IDs, and artifact paths.

Append an event manually or from scripts:

```bash
python3 scripts/record_experiment.py \
  --kind dataset --name typescript-repo-v1 --status completed \
  --metadata '{"records": 0, "source_commit": "..."}'
```

The ledger is intentionally JSONL rather than a database: it is diffable,
portable, and easy to analyze later with Python, DuckDB, or a notebook. A
future dashboard should derive metrics from it rather than hand-editing docs.

## Current baseline

The first serious data cycle produced 10,000 compiler-verified synthetic
TypeScript records and 13 independently compiler-verified local teacher traces.
The 150-step v5 run took 483.9 seconds on CPU and reduced training loss to
0.559, but the executable two-task quality gate still failed. That result is a
useful negative measurement: more records and lower loss do not automatically
produce a useful specialist. Future runs must report quality gates alongside
loss and tokens/second.

## Measurement policy

Record dataset provenance and license before training; keep train/validation/
test repositories and generated variants disjoint; record cold and warm model
latency separately; and never call a model “better” without executable or
human-scored held-out results. Raw GitHub source is evidence and a task source,
not automatically valid instruction/answer training data.
