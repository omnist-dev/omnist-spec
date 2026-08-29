# 8. Conformance and errors

## 8.1 Status of this chapter

**The error-code taxonomy in §8.3 is normative content that implementations
are still migrating onto.** It exists because conformance testing needs
stable, language-independent identifiers — comparing human-readable message
strings across languages is not a test, it is a coincidence. See the
`§8.3 error codes` row in [§9.3](09-divergence-ledger.md#93-current-status)
for current per-port adoption status.

**None of this is required for the current release; it is required before a
version of this spec declares §8.3 mandatory.** Until then, an
implementation is conformant on error *behavior* — which inputs fail, and
where — without being conformant on error *codes*. §8.5 separates the two
so that can be measured, and §8.5.2 rule 4 lets a harness run in
code-agnostic mode for exactly this reason.

## 8.2 Code format

A code is a lowercase, dot-separated path. Each segment is
`[a-z][a-z0-9-]*`. The first segment is the family. Codes are stable
identifiers: once published, a code's meaning MUST NOT change. Retiring a code
means adding a new one and leaving the old one documented as retired.

Codes are not messages. An implementation MUST emit a human-readable message
alongside the code, and the message MAY be localized, reworded, or improved at
any time. Conformance tests match on codes and paths, never on message text.

Every diagnostic carries at least:

| Field | Meaning |
|---|---|
| `code` | The identifier from §8.3 |
| `path` | Location in the Document or schema; see §8.4 |
| `message` | Human-readable, actionable, unversioned |
| `severity` | `error`, `warning`, or `info` |

## 8.3 The taxonomy

### 8.3.1 `parse.*` — text to Document, stage 1

| Code | Raised when |
|---|---|
| `parse.unexpected-token` | A token appears where the grammar does not allow it |
| `parse.trailing-content` | Content remains after the document's single node |
| `parse.unterminated-string` | A string is not closed before end of input |
| `parse.invalid-escape` | An unrecognized backslash escape |
| `parse.unpaired-surrogate` | A `\uXXXX` surrogate escape without its partner |
| `parse.control-character` | A literal control character in a context that forbids it |
| `parse.reserved-word-label` | `null`, `true`, or `false` used as a bare label |
| `parse.bare-word` | A bare identifier in value position that is not `null`/`true`/`false` |
| `parse.empty-array` | `[]` in OML value position |
| `parse.nested-array` | An array element that is itself an array |
| `parse.separator-in-array` | A newline or `;` used as an array separator |

**Six of these codes also cover OSD's own lexical stage**:
`parse.unexpected-token`, `parse.trailing-content`,
`parse.unterminated-string`, `parse.invalid-escape`,
`parse.unpaired-surrogate`, `parse.control-character`. OSD produces a
Schema rather than a Document, but tokenizing OSD source text is the same
kind of operation as tokenizing OML source text — a lexical failure before
any semantic well-formedness checking has begun (§8.3.3 covers
well-formedness, not lexing) is the same class of error regardless of what
stage-2 structure a successfully-tokenized input eventually becomes. An
unterminated string or an unexpected character in OSD source MUST be
reported with the matching `parse.*` code above, never a `schema.*` code
and never an implementation-invented code outside this taxonomy. The
remaining five codes (`reserved-word-label`, `bare-word`, `empty-array`,
`nested-array`, `separator-in-array`) describe OML's value grammar
specifically and have no OSD equivalent.

### 8.3.2 `document.*` — building and limits

| Code | Raised when |
|---|---|
| `document.limit.depth` | Nesting exceeds the implementation's configured depth limit |
| `document.limit.nodes` | Node count exceeds the implementation's configured node limit |
| `document.limit.int-digits` | An integer literal exceeds the implementation's configured digit limit |
| `document.unlabeled-element` | An input construct has no label to become an edge |

These three `document.limit.*` codes correspond exactly to the three
quantities in [§2.4](02-document-model.md#24-safety-limits) — no fourth, no
tiers. **The codes are fixed; the threshold that triggers each one is not**
— an implementation MAY configure any of the three limits to a value other
than the reference default, per §2.4, but whatever value it configures,
crossing it MUST raise exactly this code, never a different one and never
silently.

### 8.3.3 `schema.*` — schema well-formedness

| Code | Raised when |
|---|---|
| `schema.no-root` | No `root` declaration |
| `schema.duplicate-root` | More than one `root` declaration |
| `schema.unknown-type` | A type name resolves to neither a scalar nor a defined record |
| `schema.duplicate-record` | A record name is defined twice |
| `schema.duplicate-field` | A label is used by two fields in one record |
| `schema.reserved-name` | A record is named after a scalar kind or `any` |
| `schema.invalid-cardinality` | Negative minimum, or maximum below minimum |
| `schema.non-integer-cardinality` | A cardinality bound is not a whole number |
| `schema.empty-cardinality` | `[]` written as a cardinality |
| `schema.unquoted-label` | A bare name in field-label position |
| `schema.empty-label` | A field label is the empty string |
| `schema.quoted-type` | A quoted string in type position |
| `schema.nullable-ref` | `?` applied to a reference |
| `schema.nullable-any` | `any?` |

`schema.unquoted-label` and `schema.quoted-type` are the two directions of
[§5.2](05-osd-grammar.md#52-the-quoting-rule)'s quoting rule — a bare name
belongs only in type position, a quoted string only in label position, and
each direction gets its own code.

### 8.3.4 `validate.*` — document against schema

| Code | Raised when |
|---|---|
| `validate.shape-mismatch` | A value where a node is expected, or the reverse |
| `validate.type-mismatch` | A value of the wrong scalar kind |
| `validate.null-not-allowed` | `null` at a non-nullable scalar |
| `validate.unexpected-field` | A label no field of the closed record names |
| `validate.cardinality` | An edge count outside `[min, max]` |

### 8.3.5 `materialize.*` — schema-directed deserialization

| Code | Raised when |
|---|---|
| `materialize.inexact-conversion` | A leaf cannot be converted to the declared type without loss or invention |

Shape and cardinality problems found during materialization use the
`validate.*` codes above — materialization performs the same checks, so
there is no separate set of names for them.

### 8.3.6 `algebra.*` — operations over schemas

| Code | Raised when |
|---|---|
| `algebra.extract-invalidates-root` | `extract`'s `keep` set removes a label the root needs |
| `algebra.infer-no-samples` | `infer` called with zero samples |
| `algebra.infer-scalar-root` | A sample's root is a value rather than a node |
| `algebra.infer-conflicting-scalars` | Samples disagree on a scalar kind, other than integer/number |
| `algebra.infer-mixed-shape` | Samples disagree on whether a label's value is a node or a scalar |

### 8.3.7 `lint.*` — schema diagnostics

| Code | Severity |
|---|---|
| `lint.unsatisfiable-record` | warning |
| `lint.unreachable-record` | warning |
| `lint.duplicate-record` | warning |
| `lint.any-field` | info |

### 8.3.8 `format.*` — codec adjustments

| Code | Severity | Meaning |
|---|---|---|
| `format.temporal-stringified` | warning | A temporal leaf was written as an ISO-8601 string |
| `format.float-special` | error | `NaN` or an infinity was substituted with `null` |
| `format.null-unrepresentable` | warning | A null leaf cannot be written in the target format, so it is dropped |
| `format.attribute-dropped` | warning | An XML attribute was discarded on read |
| `format.namespace-dropped` | warning | An XML namespace prefix was discarded on read |
| `format.interleaving-lost` | warning | Cross-label interleaving could not be written |
| `format.multiple-roots` | error | A multi-root Document cannot be written to a single-root format |
| `format.string-line-break-char` | warning | A label or value contains U+0085 (NEL); written quoted so it round-trips |
| `format.shape-empty-ambiguous` | warning | An empty internal node was written as a self-closing tag, which reads back as an empty-string leaf, not an empty node |
| `format.value-stringified` | warning | A non-string scalar was written as text in a format with no native typed literals for it, so it reads back as a string |
| `format.string-cr-normalized` | warning | A string contains a carriage return; the target format's own parse-time line-ending normalization means it will read back as `\n`, not the original byte |

**`format.attribute-dropped`, `format.namespace-dropped`, and
`format.interleaving-lost` MUST be emitted** wherever the codec adjustment
they describe occurs, with a conformance vector for each — see
[§9.4](09-divergence-ledger.md#94-known-open-divergences) D-3 for
per-port rollout status.

Every code above describes a write that still succeeds — the document was
written, with a note about what changed. Two adjustments that used to be in
this table are not like that, and MUST NOT be treated as ones a writer can
choose an arbitrary fallback for and still succeed:

- **A label isn't a legal identifier in the target format** (e.g. a space in
  an XML tag name).
- **A string contains a character the target format cannot represent at all**
  (e.g. a raw C0 control character XML 1.0 forbids).

In both cases, there is no single well-defined substitute the way `null`
is the one legal JSON spelling for `NaN` — sanitizing a label or replacing a
character means inventing content, and there is more than one equally
arbitrary way to do it. A previous version of this spec had these succeed
anyway (`format.key-sanitized`, `format.string-illegal-char`, warning and
error severity respectively) — that was found to be genuinely unsafe, not
just imprecise: two *different* labels can sanitize to the *same* result
(`"my label"` and `"my_label"` both becoming `<my_label>`), silently
producing a Document, on read-back, that looks like one label repeated
twice, with no diagnostic anywhere indicating a collision occurred. The
correct behavior is `write.unsupported-value` (below): the write fails,
unconditionally, not only under `strict`.

### 8.3.9 `write.*`

| Code | Raised when |
|---|---|
| `write.unsupported-value` | A value has no representation in the target format and strict mode is in force, **or** a label/string cannot be represented at all in the target format's own syntax (unconditional, regardless of `strict`) |

## 8.4 Paths

A path locates a diagnostic. Paths are normative and MUST be byte-identical
across implementations, because conformance vectors match on them.

**Document paths** start at `$` and descend by label. A repeated label is
disambiguated by a zero-based occurrence index in brackets.

```
$                        the root node
$.name                   the single edge labeled `name`
$.item[0]                the first edge labeled `item`
$.item[2].sku            `sku` inside the third `item`
```

The index MUST be present when the label occurs more than once in that node, and
MUST be absent when it occurs exactly once.

**Schema paths** are `RecordName` for a record-level diagnostic and
`RecordName.label` for a field-level one.

**The whole-schema fallback is `$`.** Some diagnostics have no specific
record or field to name: `schema.no-root`, `schema.duplicate-root`, a
dangling root reference, and `algebra.infer-no-samples`/
`algebra.infer-scalar-root` (these fail before any schema exists). All five
use `$` — the same sentinel Document paths use for the whole node — as the
schema-side/pre-schema equivalent of "the whole thing, not a part of it."

**Text-position paths** are for `parse.*` diagnostics (§8.3.1) — stage 1
fails before any Document exists, so there is no `$`-rooted structure for a
Document path to descend into. The format is `line:col`, 1-based, computed
from the byte offset of the failure:

```
1:1                      the very first character
14:8                     line 14, column 8
```

A `parse.*` diagnostic's `path` MUST be a text-position path. A `document.*`,
`schema.*`, `validate.*`, `materialize.*`, `algebra.*`, or `lint.*` diagnostic's
`path` MUST be a Document or Schema path — never a text-position path, since a
Document or Schema already exists by the time any of those families can fire.

## 8.5 Conformance harness protocol

A conformant implementation passes the vectors in `test-suite/`. Vectors are
JSON, one case per object, grouped into files by operation.

### 8.5.1 Common envelope

```json
{
  "name": "unique-vector-id",
  "spec": "docs/03-schema-model.md#36-validation",
  "operation": "validate",
  "purpose": "happy-path",
  "input": { },
  "expect": { }
}
```

- `name` MUST be unique across the whole suite. A harness reports results keyed
  on it.
- `spec` points at the section the vector pins. A vector with no section to
  point at is a vector testing something unspecified, which is a spec defect.
- `operation` selects the driver. It MUST be one of the operation names listed
  on the [Operations & Models Reference](operations-and-models-reference.md)
  page — that page is the vocabulary's single source, not a free-text field
  vectors can spell differently across files.
- `purpose` MUST be one of `happy-path`, `edge-case`, `error-case`, or
  `determinism-regression` — what a vector is actually pinning, so a reader
  doesn't have to reverse-engineer it from the input/expect pair.
  `happy-path` is an ordinary conforming case with nothing specific being
  probed; `edge-case` deliberately exercises a specific rule, invariant, or
  boundary (regardless of whether the outcome is success or failure);
  `error-case` is primarily testing that an invalid input is correctly
  rejected; `determinism-regression` pins a specific ordering/reproducibility
  regression tied to a known bug.
- `expect` holds either a success value or a `diagnostics` list.

### 8.5.2 Diagnostics matching

```json
"expect": {
  "ok": false,
  "diagnostics": [
    { "path": "$.port", "code": "validate.type-mismatch" }
  ]
}
```

Matching rules, all normative:

1. Message text MUST NOT be compared.
2. The diagnostic list MUST be compared as a **set**, not a sequence. Ordering
   of diagnostics is not specified and implementations may find problems in any
   order.
3. Every expected diagnostic MUST be present, and no unexpected diagnostic may
   be. Partial matching is not permitted; an implementation reporting three
   problems where the vector expects two has failed.
4. A harness MAY be run in **code-agnostic mode**, comparing only `ok` and the
   set of paths. This is the mode implementations that have not yet adopted
   §8.3 run in. A run MUST state which mode produced its results.

### 8.5.3 Operation drivers

| `operation` | `input` | success `expect` |
|---|---|---|
| `parse` | `{format, text}` | `{ok, document}` |
| `parse_schema` | `{text}` | `{ok}` |
| `validate` | `{schema, document}` | `{ok}` |
| `materialize` | `{schema, document}` | `{ok, document}` |
| `write` | `{document, format}` | `{ok, text}` — `diagnostics` MAY be present alongside a successful `{ok: true, ...}` result (a write can succeed with a reported adjustment, e.g. `format.temporal-stringified`; success and a diagnostics list are not mutually exclusive here the way they are for every other operation) |
| `compatible_with` | `{a, b}` | `{result: bool}` |
| `equivalent` | `{a, b}` | `{result: bool}` |
| `normalize` | `{schema}` | `{schema: <canonical OSD text>}` — compared byte for byte per §5.9's canonical-output requirement |
| `prune` | `{schema}` | `{schema: <canonical OSD text>}` |
| `is_empty` | `{schema}` | `{empty: bool}` |
| `extract` | `{schema, keep}` | `{ok, schema}` |
| `infer` | `{samples, allow_any}` | `{ok, schema}` — `allow_any` defaults to `false` when absent |
| `infer_with_report` | `{samples, allow_any}` | `{ok, schema, fallbacks}` — `fallbacks` is a list of `{location, reason}`, always present on success (empty when nothing was opened) |
| `lint` | `{schema}` | `{ok, findings}` — `findings` is a list of `{code, severity, location}`; message text is never compared (§8.5.2 rule 1) so no `message` field is required |

Every operation's failure `expect` is `{ok: false, diagnostics: [...]}`, per
§8.5.2 — `write` is the only operation where `ok: true` and `diagnostics` can
coexist, noted above.

**`materialize`'s `input` is a canonical-JSON Document, not raw format text
plus a `format` field.** This is deliberate: per
[Operations & Models Reference](operations-and-models-reference.md),
`materialize`'s abstract signature is `materialize(node, S) -> node` — it
operates on an already-parsed Document, matching §7.1's two-stage
separation. A vector wanting to exercise the full parse-then-materialize
pipeline for a specific format uses two vectors — one `parse`, one
`materialize` — not one vector conflating both stages.

Schemas in `input` are OSD text. Documents are given in the canonical JSON
encoding of §8.5.4, not in a format-specific text, except where the vector is
specifically testing a parser.

### 8.5.4 Canonical document encoding

A Document must be written into a JSON vector file without JSON's own
map-and-array shape smuggling assumptions back in. The encoding is explicit:

```json
{"scalar": {"kind": "integer", "value": 42}}
{"edges": [["name", {"scalar": {"kind": "string", "value": "Ann"}}],
           ["tag",  {"scalar": {"kind": "string", "value": "x"}}],
           ["tag",  {"scalar": {"kind": "string", "value": "y"}}]]}
```

- A node is `{"edges": [[label, target], ...]}`. The outer array preserves
  order; repeated labels appear as repeated entries.
- A scalar is `{"scalar": {"kind": K, "value": V}}` where `K` is one of the
  seven kinds. Temporal values are ISO-8601 strings. `integer` values are JSON
  numbers when they fit exactly and decimal strings otherwise.
- `null` is `{"scalar": {"kind": null, "value": null}}`.

This is verbose on purpose. A vector file must not depend on the reader's JSON
library to decide whether `1` is an integer or a number.

### 8.5.5 Reporting

*Building your own runner? [Porting a Conformance Runner](porting-a-conformance-runner.md)
collects what all three existing ports learned, including this section's
skip/CI discipline in practice.*

A harness run reports, per vector: pass, fail, or skip. **Skip is a first-class
result.** An implementation that has not built `extract` yet skips those
vectors and reports the count. A run that hides skips as passes is worthless for
tracking convergence, which is the whole point of
[chapter 9](09-divergence-ledger.md).

**A skip MUST cite a reason, and the reason determines what else is
required:**

- **Not yet implemented.** The operation or feature doesn't exist yet in
  this implementation. Temporary by nature — expected to become a `pass`
  once the work lands. No ledger entry is required for this category on its
  own, though the usual issue tracker SHOULD have something open for it.
- **Documented divergence.** The vector's outcome depends on a capability
  this implementation's target language or design genuinely cannot provide
  — not a missing feature, a structural limit. This category MUST have a
  corresponding entry in [chapter 9](09-divergence-ledger.md)'s divergence
  ledger (see [§9.4](09-divergence-ledger.md#94-known-open-divergences) for
  the current open entries), and the skip reason a harness reports for the
  affected vectors MUST cite that entry by number (e.g. `"skip: D-N"`) — a
  skip with no citable reason, or a reason invented ad hoc instead of
  pointing at a ledger entry, is not acceptable reporting under this
  section. A divergence this narrow is closed, and its entry removed from
  the ledger, once the implementation adds real support — it doesn't stay
  listed once resolved.

**CI gating.** A conformant CI run MUST fail the build when the fail count
is nonzero. A conformant CI run MUST NOT fail the build merely because the
skip count is nonzero — an implementation with real, cited reasons for
every skip has *passed* conformance in the sense this section defines.
Passing CI is a statement about `fail`, not about reaching zero skips;
chapter 9 is where the skip count's honesty is checked, not the CI gate.

## 8.6 OML/OSD conformance harness

§8.5's harness exercises operations through a canonical JSON encoding
(§8.5.4) specifically to avoid the representational ambiguity of format
text — the same Document can be written as OML or OSD in more than one way
(indentation, array sugar versus repeated labels, field declaration order)
and still be the identical model. That is the right design for testing
**operation correctness**, but it never touches the OML/OSD text an
implementation actually reads and writes, which is a second, independent
thing worth testing on its own: **codec fidelity** at the surface a human or
another tool actually uses.

**[conformance-harness.md](conformance-harness.md)** specifies a second,
complementary conformance track for exactly that: a CLI wrapper contract
every implementation exposes one command per operation under, a
directory-per-fixture format for OML/OSD input and expected output, and a
structural-equality comparison algorithm (not text diffing) for judging
whether an implementation's actual output matches. It reuses this chapter's
operation vocabulary (§8.5.3) and diagnostic envelope (§8.2) rather than
defining either a second time.

This track's fixtures and orchestrator live in this repository, under
`conformance/`, not in a separate repository — alongside the spec text they
pin, for the same reason `test-suite/` does: chapter 10's Spec-TDD workflow
(§10.2) requires a vector and the prose it tests to land in the same PR, and
that is only practical when both live in one place.
