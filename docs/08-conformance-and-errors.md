# 8. Conformance and errors

## 8.1 Status of this chapter

**The error-code taxonomy in §8.3 is new normative content. No implementation
emits it today.** It is written here because conformance testing needs stable,
language-independent identifiers, and comparing human-readable message strings
across three languages is not a test, it is a coincidence.

The prior art, stated accurately so the migration cost is visible:

| Implementation | What exists now |
|---|---|
| Python (reference, beta) | Validation and materialization results carry kebab-case codes: `shape-mismatch`, `unexpected-field`, `cardinality`, `null-not-allowed`, `type-mismatch`. `lint` carries its own: `unsatisfiable-record`, `unreachable-record`, `duplicate-record`, `any-field`. Everything else is a bare exception class (`DocumentError`, `SchemaError`, `ParseError`) with a human message and no code. |
| TypeScript (alpha) | Diagnostic records carry a `code: string` field using the same kebab-case tags as Python's validation codes. |
| Rust (alpha) | Top-level `thiserror` structs (`DocumentError`, `ParseError`, `FormatError`, `WriteError`) carry no code. But `SchemaError`'s validation path has an `ErrorCode` enum rendering the identical kebab-case tags Python and TypeScript use (`unexpected-field`, `cardinality`, `type-mismatch`, `null-not-allowed`, `shape-mismatch`), attached to every `ValidationError` produced by both `validate` and `materialize`. An earlier version of this table said "no code field anywhere," which was wrong — Rust has reached the same partial convergence as the other two. |

There is a second, separate family of prior art this table previously missed
entirely: **format-adjustment codes.** Python's format readers/writers already
emit dotted (not namespaced) codes on their `WriteReport`/`check_*` results —
`temporal.stringified` (a temporal leaf stringified to ISO-8601 for a format
with no native temporal type), `null.omitted` (TOML/XML, a null-valued leaf
dropped since the format can't represent it), `float.special` (JSON, a
`NaN`/`Infinity`/`-Infinity` substituted with `null` in lenient mode),
`key.sanitized` (XML), `string.ambiguous` (XML, a string value that would
read back as a different type), `shape.empty_ambiguous`, `string.illegal_xml_char`,
`string.cr_normalized`, and `string.line-break-char` (all XML). These map
directly onto §8.3.8's `format.*` family below — the migration here is
mostly a rename, not new design, which the original wording of this section
didn't make clear.

So there is partial, undocumented convergence on validation codes across all
three implementations, and a second, separate area of already-shipped
convergence on format-adjustment codes (Python only, so far) — and nothing at
all outside those two areas. There has never been a cross-language
convention. This chapter proposes one.

**Migration.** The kebab-case validation tags all three implementations already
share are the closest prior art and map cleanly onto §8.3's `validate.*` family.
All three SHOULD migrate to the namespaced form. None of this is required for
the current release; it is required before a version of this spec declares
§8.3 mandatory.

Until then, an implementation is conformant on error *behavior* — which inputs
fail, and where — without being conformant on error *codes*. The test-vector
format in §8.5 separates the two so that can be measured.

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

### 8.3.2 `document.*` — building and limits

| Code | Raised when |
|---|---|
| `document.limit.depth` | Nesting exceeds the implementation's configured depth limit |
| `document.limit.nodes` | Node count exceeds the implementation's configured node limit |
| `document.limit.int-digits` | An integer literal exceeds the implementation's configured digit limit |
| `document.unlabeled-element` | An input construct has no label to become an edge |

The three `document.limit.*` codes correspond to the three quantities in
[§2.4](02-document-model.md#24-safety-limits). There are three, they are flat,
and no implementation may add a fourth or split one into tiers. **The codes are
fixed; the threshold that triggers each one is not** — an implementation MAY
configure any of the three limits to a value other than the reference default,
per §2.4, but whatever value it configures, crossing it MUST raise exactly this
code, never a different one and never silently.

### 8.3.3 `schema.*` — schema well-formedness

| Code | Raised when |
|---|---|
| `schema.no-root` | No `root` declaration |
| `schema.unknown-type` | A type name resolves to neither a scalar nor a defined record |
| `schema.duplicate-record` | A record name is defined twice |
| `schema.duplicate-field` | A label is used by two fields in one record |
| `schema.reserved-name` | A record is named after a scalar kind or `any` |
| `schema.invalid-cardinality` | Negative minimum, or maximum below minimum |
| `schema.non-integer-cardinality` | A cardinality bound is not a whole number |
| `schema.empty-cardinality` | `[]` written as a cardinality |
| `schema.unquoted-label` | A bare name in field-label position |
| `schema.nullable-ref` | `?` applied to a reference |
| `schema.nullable-any` | `any?` |

### 8.3.4 `validate.*` — document against schema

| Code | Raised when | Existing tag it replaces |
|---|---|---|
| `validate.shape-mismatch` | A value where a node is expected, or the reverse | `shape-mismatch` |
| `validate.type-mismatch` | A value of the wrong scalar kind | `type-mismatch` |
| `validate.null-not-allowed` | `null` at a non-nullable scalar | `null-not-allowed` |
| `validate.unexpected-field` | A label no field of the closed record names | `unexpected-field` |
| `validate.cardinality` | An edge count outside `[min, max]` | `cardinality` |

### 8.3.5 `materialize.*` — schema-directed deserialization

| Code | Raised when |
|---|---|
| `materialize.inexact-conversion` | A leaf cannot be converted to the declared type without loss or invention |

Shape and cardinality problems found during materialization use the
`validate.*` codes above. Materialization performs the same checks; there is no
reason for a second set of names.

### 8.3.6 `algebra.*` — operations over schemas

| Code | Raised when |
|---|---|
| `algebra.extract-invalidates-root` | `extract`'s `keep` set removes a label the root needs |
| `algebra.infer-no-samples` | `infer` called with zero samples |
| `algebra.infer-scalar-root` | A sample's root is a value rather than a node |
| `algebra.infer-conflicting-scalars` | Samples disagree on a scalar kind, other than integer/number |

### 8.3.7 `lint.*` — schema diagnostics

These are the only codes that already exist in namespaced-adjacent form. The
bare tags MUST become:

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

Three of these describe behavior that is currently silent in the reference
implementation — attribute dropping, namespace dropping, and interleaving loss
are none of them reported today, confirmed live for all three. Adding the
report is a behavior change and needs a test vector before it lands.

`format.null-unrepresentable`'s severity was previously listed as `error`,
which never matched the reference implementation: the write still succeeds,
with the null leaf simply dropped and reported as an adjustment, the same
"succeeded, but something was adjusted" shape as the other warning-severity
rows in this table. Corrected to `warning`; `format.float-special` remains the
one row correctly at `error`, since substituting a value (not just dropping
one) is a stronger change to what's actually represented.

### 8.3.9 `write.*`

| Code | Raised when |
|---|---|
| `write.unsupported-value` | A value has no representation in the target format and strict mode is in force |

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
MUST be absent when it occurs exactly once. This keeps the common case readable.

Unlike the codes above, this path format is **not** new: it is the format the
Python reference already emits, verified directly — a failure at the second of
two `i` edges reports `$.i[1].q`, and a failure at a singly-occurring label
reports `$.name` with no index. The rule is documented here rather than
proposed.

**Schema paths** are `RecordName` for a record-level diagnostic and
`RecordName.label` for a field-level one. This matches what `lint` already
reports.

**The whole-schema fallback is `$`.** Some diagnostics have no specific
record or field to name: `schema.no-root` (there is no root declaration at
all), a dangling root reference (the named root never resolves to a
defined record), and `algebra.infer-no-samples`/`algebra.infer-scalar-root`
(these fail before any schema exists, since they're about the shape of
the input samples, not a schema). All four use `$` — the same sentinel
Document paths use for the whole node — as the schema-side/pre-schema
equivalent of "the whole thing, not a part of it." This is a deliberate
extension of the two path forms above, not a third form: it says what to
do when neither a specific record nor a specific field applies, rather
than introducing new path syntax.

**Text-position paths** are for `parse.*` diagnostics (§8.3.1) — stage 1
fails before any Document exists, so there is no `$`-rooted structure yet
for a Document path to descend into. The format is `line:col`, 1-based,
computed from the byte offset of the failure:

```
1:1                      the very first character
14:8                      line 14, column 8
```

**This is new normative content, unlike the two path forms above.** Python
already computes 1-based `(line, col)` from a byte offset internally
(`oml.py`'s `line_col`) but only ever embeds it in the diagnostic's
human-readable *message* string ("line 14, col 8: ..."), never as a
structured path — which is exactly why no cross-implementation convention
exists yet to document. This section specifies one rather than describing
one already in use, the same way §8.3's code taxonomy does.

A `parse.*` diagnostic's `path` MUST be a text-position path. A `document.*`,
`schema.*`, `validate.*`, `materialize.*`, `algebra.*`, or `lint.*` diagnostic's
`path` MUST be a Document or Schema path, per the two forms above — never a
text-position path, since a Document or Schema already exists by the time any
of those families can fire.

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
  `determinism-regression` (the same four-way vocabulary the OML/OSD
  conformance harness uses, [§2](conformance-harness.md) of that page) —
  what a vector is actually pinning, so a reader doesn't have to
  reverse-engineer it from the input/expect pair. `happy-path` is an
  ordinary conforming case with nothing specific being probed;
  `edge-case` deliberately exercises a specific rule, invariant, or
  boundary (regardless of whether the outcome is success or failure);
  `error-case` is primarily testing that an invalid input is correctly
  rejected; `determinism-regression` pins a specific
  ordering/reproducibility regression tied to a known bug.
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

**This table was corrected against `test-suite/`'s actual 140 vectors and
`omnist`'s `tools/conformance/vector_runner.py`, which passes all of them
(104 pass, 35 legitimate skip, 0 fail) — an earlier revision of this table
predated most of those vectors and, checked directly rather than assumed
correct, disagreed with six of the twelve original rows. The table below
states what is actually implemented and verified working, not an
un-exercised ideal.**

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
plus a `format` field.** This is deliberate, not an oversight: per
[Operations & Models Reference](operations-and-models-reference.md),
`materialize`'s abstract signature is `materialize(node, S) -> node` — it
operates on an already-parsed Document, matching §7.1's two-stage
separation (stage 1 parses, stage 2 materializes; a vector testing stage 2
should not silently re-test stage 1's `parse` by embedding it as a hidden
first step). A vector wanting to exercise the full parse-then-materialize
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
  — not a missing feature, a structural limit (TypeScript's `integer`/
  `number` collapse, [§9.4 D-6](09-divergence-ledger.md#94-known-open-divergences),
  is the worked example). This category MUST have a corresponding entry in
  chapter 9's divergence ledger, and the skip reason a harness reports for
  the affected vectors MUST cite that entry by number (e.g. `"skip: D-6"`)
  — a skip with no citable reason, or a reason invented ad hoc instead of
  pointing at a ledger entry, is not acceptable reporting under this
  section.

**CI gating.** A conformant CI run MUST fail the build when the fail count
is nonzero. A conformant CI run MUST NOT fail the build merely because the
skip count is nonzero — an implementation legitimately at 104 pass / 0 fail
/ 35 skip has *passed* conformance in the sense this section defines,
provided every one of those 35 skips carries one of the two reason
categories above. Passing CI is a statement about `fail`, not about
reaching zero skips; chapter 9 is where the skip count's honesty is
checked, not the CI gate.

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
