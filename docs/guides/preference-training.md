# Preference training

The repository now includes a local TRL DPO path in
`scripts/train_preference.py`. Preference candidates are produced from
compiler-verified TypeScript examples, then retained only when the chosen
variant compiles and the deterministic rejected variant does not.

The first run used 1,000 pairs and 300 CUDA steps on the RTX 5080. It took
218.5 seconds, reached training reward accuracy 1.0, and produced DPO loss
0.3661. On the corrected 20-task held-out sample it verified 6/20, so the
adapter was not promoted. This is expected research behavior: a preference
loss improvement is not a code-quality improvement until an independent
compiler/test suite confirms it.

```bash
python3 scripts/build_preference_pairs.py \
  --input .oktopai/datasets/typescript-synthetic-v2.jsonl \
  --output .oktopai/datasets/typescript-preferences-v1.jsonl --limit 3000
python3 scripts/verify_preference_pairs.py \
  --input .oktopai/datasets/typescript-preferences-v1.jsonl \
  --output .oktopai/datasets/typescript-preferences-verified-v1.jsonl --limit 3000
HF_HOME=.oktopai/hf-cache .venv-training/bin/python scripts/train_preference.py \
  --data .oktopai/datasets/typescript-preferences-verified-v1.jsonl \
  --base-model .oktopai/hf-bases/qwen2.5-coder-0.5b \
  --output .oktopai/adapters/typescript-dpo-v1 \
  --max-pairs 1000 --max-steps 300 --device cuda --train
```

The next iteration should make prompt formatting identical between SFT, DPO,
and evaluation, then compare base, SFT, and DPO on the same held-out batch.
