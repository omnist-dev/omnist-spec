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
  schema-wellformedness/     S-1..S-7 vectors not already covered by osd-grammar/ (dangling refs, forward refs, mutual recursion)
  materialize/               schema-directed deserialization vectors (ch.7): upgrades, rejections, any passthrough
  is-empty/                  is_empty / satisfiability vectors
  prune/                     prune vectors
  normalize/                 normalize vectors
  extract/                   extract vectors
  infer/                     infer / infer_with_report vectors, including allow_any
  lint/                      lint vectors
  formats-json/              JSON codec vectors
  formats-yaml/              YAML codec vectors, including the sexagesimal-time and Norway-problem sharp edges, and the D-18 alias-expansion bound
  formats-toml/              TOML codec vectors
  formats-xml/               XML codec vectors
  formats-oml/               OML write-direction vectors (ch.4): date/time/datetime-shaped strings must stay quoted, distinct from a genuinely temporal-kinded scalar writing bare
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
- A `number` holding `NaN`, `Infinity`, or `-Infinity` is `V = "NaN"`,
  `"Infinity"`, or `"-Infinity"` — the literal string, not a bare JSON
  number. JSON itself has no token for any of the three, so a vector can't
  hold one as an ordinary numeric `V` without making the vector file itself
  invalid JSON; the string form is unambiguous here because a real
  `number`'s `V` is always a JSON number, never a JSON string.

**Some vectors cannot be honestly run by every implementation, and that's
expected.** A `document` whose `kind` is `"integer"` or
`"number"` can't be faithfully constructed by an implementation with no
native distinction between the two (e.g. TypeScript). Such an
implementation's runner MUST report `skip` for the affected vectors, not
`fail` and not a forced `pass`, and MUST record the gap as a numbered
`DIV-N` entry in
[§9.4](../docs/09-divergence-ledger.md#94-known-open-divergences) — the same
discipline already applies to
`document-model/limits.json`'s vectors for implementations with no
runtime-configurable safety limit (§2.4).

### Declared-limit keys, and the allowlist every runner needs

A vector that pins a safety-limit boundary carries the limit it was written
against as a `declared_max_*` key inside `input`. These are the four in the
suite today:

```
declared_max_depth              §2.4 maximum nesting depth
declared_max_nodes              §2.4 maximum node count
declared_max_int_digits         §2.4 maximum integer digits
declared_max_alias_expansion    §2.4.1 maximum alias expansion factor (D-18)
```

A key is a **vector-local parameter, not the reference default**. A runner
MUST recognize every key in this list and, when the implementation under test
exposes no configuration surface for that limit, report `skip` for the vector
— not `fail`, and not a `pass` obtained by running it against whatever
default the implementation happens to ship. Running a boundary vector against
the wrong number does not test the boundary; depending on which side of it
the default falls, it either fails for the wrong reason or passes without
exercising anything.

Runners implement this as an allowlist — Python's is a `_LIMIT_KEYS` set in
`tools/conformance/vector_runner.py`, and the other ports' runners are
modelled on it. **A key missing from that set is silently treated as an
ordinary vector**, which is the failure mode above.

`declared_max_alias_expansion` is new in v0.18.0-beta, and no port enforces
D-18 yet either, so adopting it takes two steps: **(a)** implement the rule,
and **(b)** allowlist the key. Skipping (b) does not produce a failure — it
produces a **false pass**, which is the more dangerous outcome because nobody
investigates a green result. `expansion-one-past-declared-limit-fails` and
`nested-anchor-fan-out-exceeds-expansion-limit` fail loudly until step (a) is
done. But `expansion-at-declared-limit-succeeds` reports green whether or not
step (b) is done: without the allowlist entry it runs against the port's own
default maximum rather than the **3** it declares, so it pins no boundary at
all and will happily mask a wrong threshold. See
[`docs/porting-a-conformance-runner.md`](../docs/porting-a-conformance-runner.md)
and [§9.4](../docs/09-divergence-ledger.md#94-known-open-divergences)'s
`DIV-3`.

## Matching

Four rules, all normative, all from chapter 8:

1. Message text is never compared.
2. Diagnostics compare as a **set**. Order is not specified.
3. The match is exact. An extra diagnostic fails the vector just as a missing
   one does.
4. **Code-agnostic mode** compares only `ok` and the set of paths. This is the
   mode for implementations that have not adopted the chapter 8 code taxonomy —
   which today is all of them. A run must state which mode produced it.

**A code-agnostic run passes vectors the implementation does not really
satisfy.** A diagnostic with the right `ok` and the right position but the
wrong code reports green and nothing in the run says otherwise. Rule 4's "a
run must state which mode produced it" exists for that reason and is not a
formality: state the mode wherever the numbers are quoted, not only inside
the runner's own output. Four of the five rows in
[§9.4](../docs/09-divergence-ledger.md#94-known-open-divergences)'s `DIV-4`
were invisible for exactly this reason, one of them a vector the Python
reference had never met since the day it was written.

## Reporting

Report pass, fail, and **skip** counts separately. Skip is a first-class result:
an implementation that has not built `extract` skips those vectors and says so.
A run that reports skips as passes cannot be used to track convergence, which is
the only reason the suite exists.
