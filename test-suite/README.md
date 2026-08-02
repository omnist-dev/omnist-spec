# Conformance test suite

Language-independent test vectors. An implementation is conformant when it runs
every vector here with zero failures.

The protocol — envelope fields, matching rules, operation drivers, the canonical
document encoding, and reporting — is normative and lives in
[`docs/08-conformance-and-errors.md`](../docs/08-conformance-and-errors.md#85-conformance-harness-protocol).
This file is a short orientation, not a second definition. Where the two
disagree, chapter 8 wins.

## Layout

```
test-suite/
  validate/                  document-against-schema vectors
  algebra-compatibility/     compatible_with / equivalent vectors
  document-model/            parse-stage safety limit vectors (depth/nodes/int-digits)
  oml-grammar/               OML text-to-Document parse vectors (ch.4)
  osd-grammar/               OSD text-to-Schema parse vectors (ch.5)
```

More directories are added per operation as vectors are written. One directory
per driver; file names group related cases.

## Vector shape

Every vector is a JSON object with the same six keys.

| Key | Meaning |
|---|---|
| `name` | Unique across the whole suite. Harness results are keyed on it. |
| `spec` | The section this vector pins, as a repo-relative path plus anchor. |
| `operation` | Selects the driver. MUST be one of the names on the [Operations & Models Reference](../docs/operations-and-models-reference.md) page. |
| `purpose` | One of `happy-path`, `edge-case`, `error-case`, `determinism-regression`. |
| `input` | Driver-specific. Schemas are OSD text; documents use the canonical encoding below. |
| `expect` | Either a success value or `{"ok": false, "diagnostics": [...]}`. |

A file holds `{"vectors": [ ... ]}`.

## Canonical document encoding

Documents are not written as plain JSON. Plain JSON would smuggle its own
map-and-array assumptions back into a model built specifically to avoid them,
and would leave the reader's JSON library to decide whether `1` is an integer or
a number.

- A node is `{"edges": [[label, target], ...]}`. Order is the array's order.
  Repeated labels are repeated entries.
- A scalar is `{"scalar": {"kind": K, "value": V}}`, `K` one of the seven kinds.
- `null` is `{"scalar": {"kind": null, "value": null}}`.

## Matching

Four rules, all normative, all from chapter 8:

1. Message text is never compared.
2. Diagnostics compare as a **set**. Order is not specified.
3. The match is exact. An extra diagnostic fails the vector just as a missing
   one does.
4. **Code-agnostic mode** compares only `ok` and the set of paths. This is the
   mode for implementations that have not adopted the chapter 8 code taxonomy —
   which today is all of them. A run must state which mode produced it.

## Reporting

Report pass, fail, and **skip** counts separately. Skip is a first-class result:
an implementation that has not built `extract` skips those vectors and says so.
A run that reports skips as passes cannot be used to track convergence, which is
the only reason the suite exists.
