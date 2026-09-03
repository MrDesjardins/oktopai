# Trajectory transfer failure analysis

Date: 2026-08-31

## Result

The v2 trajectory adapter was tested on 50 independently verified records from
five families absent from v2 training. It produced contract-valid JSON for
50/50 records, but independent replay passed 35/50.

| Unseen family | Records | Replay passed | Replay failed |
|---|---:|---:|---:|
| union-return | 10 | 10 | 0 |
| discriminated-union | 10 | 10 | 0 |
| array-union | 10 | 5 | 5 |
| object-literal-mismatch | 10 | 10 | 0 |
| record-method | 10 | 0 | 10 |

## Concrete failure modes

### Record values

All ten failures used a repair shaped like:

```ts
typeof record[key] === 'string' ? record[key].toUpperCase() : ''
```

The declared value type is `number`, so this introduces an impossible string
branch and still does not provide a valid numeric repair. The model recognized
that a method was unsafe but ignored the repository type fact already present
in the prompt.

### Primitive array unions

All five failures used a repair shaped like:

```ts
value[0] instanceof Number ? value[0].toFixed(2) : value[0]
```

`number` primitives are not instances of the boxed `Number` object, and this
does not narrow the union in the way required by the compiler. The model chose
a familiar-looking runtime check rather than the valid `typeof item ===
'number'` narrowing pattern.

## Interpretation

The adapter has learned the ordered trajectory format and can transfer it to
new task families. Executable repair transfer is weaker: 15/50 unseen repairs
failed, concentrated in two type-narrowing patterns. This is a targeted
capability gap, not a parser or trajectory-contract failure.

## Follow-up design

Keep the 50-record unseen set test-only and untouched. Add a separate verified
training tranche containing:

1. Record APIs with explicit numeric methods, string methods, nullable values,
   and unknown keys.
2. Primitive arrays and unions requiring `typeof`, `Array.isArray`, and local
   variable narrowing, explicitly excluding boxed-object checks.
3. Negative examples whose edits compile only when the declared repository
   types are respected.

Every new record must pass the independent replay verifier before it enters
training. The next candidate should be evaluated on this unchanged 50-record
test set plus a second held-out set, with replay pass rate reported separately
from contract-valid rate. No export or promotion is justified by the current
result.

## Targeted follow-up outcome

The targeted adapter fixed the numeric-record gap on the unchanged unseen set:
record-method replay improved to 10/10. It did not fix primitive array
narrowing: replay fell to 2/10, and one unrelated object-literal output was
contract-invalid. Overall, 41/49 contract-valid outputs passed replay.

This confirms that targeted training can move a specific executable capability,
but the current tranche is too narrow to support promotion and may cause
regressions in adjacent repair patterns.
