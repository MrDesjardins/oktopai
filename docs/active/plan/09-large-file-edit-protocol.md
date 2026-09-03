# 09 — Large-file edit protocol

## Problem

The current `apply_patch` event describes `args.content` as the complete file.
That is reliable for compact fixture files but caused the held adapter to emit
short snippets for a 7.8-KB real repository file. Structural validation alone
accepted those snippets; independent replay rejected them.

## Proposed contract

Keep complete `args.content` for small files. Add a compact edit form for large
files:

```json
{"event":"edit","tool":"apply_patch","args":{"path":"src/main.tsx","replacements":[{"old":"...exact old text...","new":"...exact new text..."}]}}
```

Replay must require every `old` string to occur exactly once, apply all
replacements deterministically, and run the post-edit compiler check. The
validator must reject ambiguous or empty replacements and preserve the raw
versus normalized distinction.

## Sequence

1. Add schema and prompt wording for `content` versus `replacements`.
2. Implement a pure replacement applier with unit tests for ambiguity,
   missing anchors, and successful multi-file replay.
3. Add compact synthetic long-file exemplars; keep local private repository
   snapshots evaluation-only.
4. Verify the mixed corpus and train an isolated candidate only after CPU
   preflight passes.
5. Evaluate on the local long-file gate and the existing 80/60 gates.

## Guardrails

- Never apply fuzzy or first-match edits.
- Never use shell commands to apply model-provided patches.
- Do not admit local repository source into training without explicit scope and
  provenance approval.
