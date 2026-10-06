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
  document-model/            parse-stage safety limit vectors (depth/nodes/int-digits, in OML and in the four other formats; input size), the digits of an integer by value across hex, octal, binary and underscored literals (D-28), number literals past binary64's range (D-29), and label identity (D-16)
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
  formats-json/              JSON codec vectors, including the duplicate-key rule and the position it leaves the edge in (C-11), and the lowercase `\uXXXX` escape (C-14)
  formats-yaml/              YAML codec vectors, including the sexagesimal-time and Norway-problem sharp edges, the D-18 alias-expansion bound, anchor/alias resolution (D-20, D-27), duplicate keys rejected (C-12), the tagged merge key (D-27) and the rejected `!!pairs`/`!!omap`/`!!set` collections (C-13), and the NEL escape a YAML writer uses (E-34)
  formats-toml/              TOML codec vectors, including duplicate keys rejected (C-12) and the lowercase `\uXXXX` escape (C-14)
  formats-xml/               XML codec vectors, including the codes a writer reports for a typed leaf (`format.value-stringified`, and `format.temporal-stringified` for a date, time or datetime, E-5)
  formats-oml/               OML write-direction vectors (ch.4): date/time/datetime-shaped strings must stay quoted, distinct from a genuinely temporal-kinded scalar writing bare; the string escapes the canonical writer may emit (OML-15), and compact mode (OML-22..24, asked for with `compact: true`, E-35)
  extensions-osd-oml/        OSD-OML extension vectors: parse_schema_oml, write_schema_oml
```

Every surface's `encoding/` group (in `oml-grammar/`, `osd-grammar/` and the
four `formats-*/` files) holds the §2.5 vectors for that surface: the BOM
rules D-15 and D-21, and, since v0.21.0-beta, D-14's byte-level vectors and
their valid-UTF-8 controls.

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

A `write` vector's `input` is `{document, format}` and may also carry two booleans,
both defaulting to `false` when absent: `strict`, and, on an OML vector only,
`compact` ([E-35](../docs/08-conformance-and-errors.md#853-operation-drivers)),
which asks for OML's one-line layout (OML-22). A runner passes `compact` to the
implementation's OML writer, or `--compact` to its CLI; one that drops it
compares the expanded layout with the compact text and fails every compact
vector for its own reason. `tools/check_vectors.py` rejects `compact` on any
other format and a non-boolean `strict` or `compact`.

On a `write` vector the `diagnostics` list is compared like any other
([E-17](../docs/08-conformance-and-errors.md#852-diagnostics-matching)): each
entry's path **and code**, exactly, as a set. A runner that compares only the
paths of a write vector's diagnostics is in code-agnostic mode for that
operation and has to say so; it is not reporting a conformance pass.

### `bytes_hex`: giving a read-side input as bytes

The three read-side drivers — `parse`, `parse_schema` and `parse_schema_oml`
— take their source text either as `text` or as `bytes_hex`, **exactly one of
the two**. `bytes_hex` is the input's bytes as lowercase hexadecimal, two
digits per byte, no separators and no prefix. §8.5.3's **E-27** is the
normative statement; this is the orientation.

```json
{
  "operation": "parse",
  "input": { "format": "json", "bytes_hex": "7b2261223a2278e282227d" }
}
```

It exists for [D-14](../docs/02-document-model.md#25-encoding), the rule that
input MUST be valid UTF-8. A vector file is JSON and a JSON string holds
text, so a `text` field can carry any valid input and none of the invalid
ones — bytes that are not valid UTF-8 are exactly the bytes a JSON string
cannot hold. D-14 was therefore an untestable MUST until this form existed
(omnist-spec#105), and a reader that silently accepted malformed bytes
reported a clean suite.

Two consequences worth stating plainly:

- **`tools/check_vectors.py` does not require a `bytes_hex` value to
  decode.** Most of these vectors do not decode; that is what they are for.
  It checks the spelling — hex digits, even length, lowercase, read-side
  operation, not alongside `text` — and nothing about the content.
- **A runner hands the decoded bytes to the implementation as bytes**, through
  a byte-oriented entry point — a bytes-taking reader, a byte stream, or any
  entry point that reads a file or standard input, **the CLI included**. It
  MUST NOT decode them to a string with `U+FFFD` replacement or any other
  lossy scheme and run the result: that substitutes a different input and
  reports on a question the vector did not ask. Only an implementation with
  no byte-oriented entry point anywhere reports these as `skip` under E-21,
  and documenting the gap as its own
  [§9.4](../docs/09-divergence-ledger.md#94-known-open-divergences) ledger
  entry. All five ports' runners read `bytes_hex` as of v0.21.0-beta; a
  runner that has not learned the field yet is reporting a `fail`, not a
  skip, until it either runs the vectors or reports an E-20 "not yet
  implemented" skip.

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
  `number`'s `V` is always a JSON number, never a JSON string. This is
  normative: [E-33](../docs/08-conformance-and-errors.md#854-canonical-document-encoding).

**Some vectors cannot be honestly run by every implementation, and that's
expected.** A `document` whose `kind` is `"integer"` or
`"number"` can't be faithfully constructed by an implementation whose language
has no distinction between the two it can use (none of the five ports is in
that position today: TypeScript builds `integer` as a `bigint`). Such an
implementation's runner MUST report `skip` for the affected vectors, not
`fail` and not a forced `pass`, and MUST record the gap as a numbered
`DIV-N` entry in
[§9.4](../docs/09-divergence-ledger.md#94-known-open-divergences) — the same
discipline already applies to
`document-model/limits.json`'s vectors for implementations with no
runtime-configurable safety limit (§2.4).

### Declared-limit keys, and the allowlist every runner needs

A vector that pins a safety-limit boundary carries the limit it was written
against as a `declared_max_*` key inside `input`. These are the six in the
suite today:

```
declared_max_depth              §2.4 maximum nesting depth
declared_max_nodes              §2.4 maximum node count
declared_max_int_digits         §2.4 maximum integer digits
declared_max_alias_expansion    §2.4.1 maximum alias expansion factor (D-18)
declared_max_expanded_slots     §2.4.1 maximum expanded size in value slots
(D-22)
declared_max_input_bytes        §2.4.2 maximum input size in bytes (D-23)
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

`declared_max_input_bytes` is new in v0.30.0-beta. It carries the maximum
input size in **bytes** (D-23). Ten vectors in
`document-model/input-size.json` carry it: an input of exactly the maximum is
accepted and one byte over is refused with `document.limit.input-size` at `$`,
for JSON, YAML and OML, a multi-byte pair that pins that the unit is bytes,
not characters, and a pair that pins that a leading BOM is counted. All five ports
enforce D-23 now (the retired `DIV-17`), so no runner reports these vectors as
a skip; a port that does not yet enforce it reports every vector carrying the key as an E-20 skip. The same two steps apply, and so does
the false-pass hazard: a runner that does not allowlist the key runs the accepted
boundary vectors against its own default and passes without testing
the boundary.

`declared_max_expanded_slots` is new in v0.26.0-beta. It carries `W(root)`'s
maximum, in value slots. It applies only to an input that contains an alias or
merge key: an alias-free input is accepted however far over it, and one vector
pins that. A vector may declare it together with `declared_max_alias_expansion`
to pin which code wins when both are crossed
(D-22: `document.limit.alias-expansion`). All five ports enforce D-22; a runner
for a new port that does not yet reports every vector carrying the key as an
E-20 skip. The same
two steps apply, and so does the same false-pass hazard: a runner that does
not allowlist the key runs `expanded-size-at-declared-cap-succeeds` against its
own default and passes without testing the boundary.

`declared_max_alias_expansion` is new in v0.18.0-beta. All five ports enforce
D-18 now, so a new port adopts it in two steps:
**(a)** implement the rule,
and **(b)** allowlist the key. Skipping (b) does not produce a failure — it
produces a **false pass**, which is the more dangerous outcome because nobody
investigates a green result. `expansion-one-past-declared-limit-fails` and
`nested-anchor-fan-out-exceeds-expansion-limit` fail loudly until step (a) is
done. But `expansion-at-declared-limit-succeeds` reports green whether or not
step (b) is done: without the allowlist entry it runs against the port's own
default maximum rather than the **3** it declares, so it pins no boundary at
all and will happily mask a wrong threshold. See
[`docs/porting-a-conformance-runner.md`](../docs/porting-a-conformance-runner.md).

## Matching

Four rules, all normative, all from chapter 8:

1. Message text is never compared.
2. Diagnostics compare as a **set**. Order is not specified.
3. The match is exact. An extra diagnostic fails the vector just as a missing
   one does.
4. **Code-agnostic mode** compares only `ok` and the set of paths. It is a
   bring-up aid for a port that has not yet adopted the chapter 8 code
   taxonomy, which §8.1 makes mandatory; a result from it is not a conformance
   claim. A run must state which mode produced it.

**One narrow exception to comparing paths byte for byte (E-32).** A
`parse.codec-syntax` diagnostic on JSON, YAML, TOML or XML input may carry the
expected path `line:col`, which is a literal placeholder, not a position. It
means: compare the `code`, and check only that the reported path is a
well-formed text position (`^[1-9][0-9]*:[1-9][0-9]*$`) — which character a
codec's own parser blames is implementation-defined (E-31). It is allowed only
there, as the vector's only diagnostic; `tools/check_vectors.py` rejects it on
any other code, on OML or OSD, and on D-21's doubled-mark vectors, whose `1:1`
stays compared. Every other path is compared byte for byte.

These four rules cover `diagnostics`. How the other `expect` fields compare is
per operation: a Document structurally and order-sensitively, schema text either
**`canonical`** (byte for byte — `parse_schema`'s `schema`, `normalize`,
`prune`, `extract`, `schema_from_document`, `parse_schema_oml`) or, for `infer`
and `infer_with_report`, **`isomorphic`**. Track 1's structural `exact` mode is a
third comparison and is not used here. The list of what each operation must
compare is in
[Porting a Conformance Runner](../docs/porting-a-conformance-runner.md#which-comparison-each-operation-needs).

**A code-agnostic run passes vectors the implementation does not really
satisfy.** A diagnostic with the right `ok` and the right position but the
wrong code reports green and nothing in the run says otherwise. Rule 4's "a
run must state which mode produced it" exists for that reason and is not a
formality: state the mode wherever the numbers are quoted, not only inside
the runner's own output. The `OML-25` row of the retired `DIV-4`
(§9.4)
is invisible for exactly this reason — right `ok`, right paths, wrong code —
and it covers a vector the Python reference had never met since the day it
was written.

## Reporting

Report pass, fail, and **skip** counts separately. Skip is a first-class result:
an implementation that has not built `extract` skips those vectors and says so.
A run that reports skips as passes cannot be used to track convergence, which is
the only reason the suite exists.
