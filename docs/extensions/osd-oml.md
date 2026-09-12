# OSD-OML

**Status: normative.** Version 1.0 of this extension.

## E.1 Summary

Schema has one native textual surface: OSD ([chapter 5](../05-osd-grammar.md)).
This extension adds a second, peer surface: **OSD-OML**, a Document-shaped
representation of a Schema, written using OML's existing, unmodified grammar
and machinery ([chapter 4](../04-oml-grammar.md)). OML serialization, storage,
and any future binary encoding of Schema fall out of machinery that already
exists for Documents generally — none of them need a separate schema-specific
design.

## E.2 Motivation

Three concrete needs converge on the same underlying gap: a future "bundle"
format embedding a schema alongside conforming documents; a future document
store that wants to persist schemas the same way it persists document data,
as OML, rather than inventing a separate schema-storage format; and a future
binary OML encoding, which a Schema should be serializable into without a
parallel, schema-specific binary design.

All three need the same thing: **Schema needs a Document-shaped
representation, not just a text syntax.** OML's reader/writer only ever
operate on Documents; before this extension there is no path from a `Schema`
object into that machinery at all.

## E.3 Terminology

- **OSD** keeps its existing meaning everywhere in the spec — the native,
  human-authored text grammar (chapter 5). This extension changes nothing
  about OSD text.
- **OSD-OML** is the new surface: the Document-shaped representation of a
  Schema, written using OML's existing, unmodified grammar.
- OSD and OSD-OML are **peers**, not a base format and a derived variant — the
  same relationship JSON and YAML have to Document. Neither is "the real one."
  Both are legitimately "an Omnist Schema Definition," in different syntax.
- File extension: **`.oml`**, not a distinct extension. An OSD-OML file *is*
  an ordinary OML file, parsed and written with the exact same generic reader
  and writer as any other OML document (§E.9).
- **Cross-reference disambiguation.** Rules genuinely about OSD *syntax*
  (tokenization, grammar productions) remain exactly as OSD-text-specific as
  they already are — OSD-OML has no grammar of its own; it inherits OML's
  grammar wholesale. Rules about Schema *well-formedness* (duplicate root,
  invalid cardinality, unresolved reference, etc.) are already scoped to
  Schema, not to OSD text specifically — visible in the existing `schema.*`
  error-code prefix, as opposed to `parse.*`. Those rules already apply to
  both surfaces with no restatement needed.

## E.4 Framing and scope

The target is **Schema ↔ Document ↔ OML text**, not "OSD gets an OML format."
The Document-shaped intermediate is unavoidable — OML's reader/writer only
ever operate on Documents, never on `Schema` objects directly.

Scope is deliberately narrow: only OML matters as a text surface for this
extension. JSON/YAML/TOML/XML serialization of Schema is out of scope — the
Document-shaped form would technically support it later via the existing
codecs, but that is not specified here.

Governing principle for every choice below: **explicit and consistent beats
concise.** This representation is for lossless, programmatic round-tripping,
not for humans to hand-author — OSD text remains the recommended surface for
hand authoring.

## E.5 `cardinality`

`{ min, max }`, both independently optional.

| OSD | OSD-OML | Meaning |
|---|---|---|
| *(omitted)* | *(edge omitted)* | exactly 1 |
| *(omitted)* | `{}` | exactly 1 |
| `[3]` | `{ min: 3, max: 3 }` | exactly 3 |
| `[1,5]` | `{ min: 1, max: 5 }` | 1 to 5 |
| `[5,]` | `{ min: 5 }` | 5+, unbounded |
| `[,5]` | `{ max: 5 }` | 0 to 5 |
| `[,]` | `{ min: 0 }` | 0+, unbounded |

`[0,0]` has no row: `[0,0]` is illegal OSD source
([§5.5](../05-osd-grammar.md), `schema.invalid-cardinality`) — a field that
can never appear is indistinguishable from an undeclared one, and OSD does
not permit two spellings of the same thing. OSD-OML inherits this
prohibition directly: `{ min: 0, max: 0 }` MUST be rejected by the
semantic-validation layer ([§E.10](#e10-structural-vs-semantic-validation)) with the same code.

Absent `cardinality` edge and `{}` (present-but-empty) both mean the default
— deliberately, to avoid two similar-looking forms meaning different things.
Per-key defaulting (`min` absent → 0, `max` absent → unbounded) only applies
once at least one key is present.

## E.6 `type`

Always a structured node, never a bare literal — including `any`, even
though `any` has no variability to attach to it. This is decided in favor of
uniformity (every field's `type` is always a node; nothing downstream
branches on "is this a string or an object") over the shorter bare-literal
alternative for `any`.

```oml
type: { kind: "scalar", name: "string" }
type: { kind: "scalar", name: "string", nullable: true }
type: { kind: "ref", name: "Address" }
type: { kind: "any" }
```

`nullable` MUST appear (as `true`) only when the scalar is actually
nullable — it MUST NOT be present as `false`.

Reference resolution is an exact string match of `name` against a declared
`record.name`. There is no path syntax and no case-insensitivity.

## E.7 `record` / `field` / `root`

```oml
record: {
  name: "Address"
  field: { label: "street", type: { kind: "scalar", name: "string" } }
  field: { label: "city", type: { kind: "scalar", name: "string" } }
}
record: {
  name: "Person"
  field: { label: "name", type: { kind: "scalar", name: "string" } }
  field: {
    label: "nickname"
    type: { kind: "scalar", name: "string", nullable: true }
  }
  field: { label: "address", type: { kind: "ref", name: "Address" } }
  field: {
    label: "tags"
    cardinality: { min: 0 }
    type: { kind: "scalar", name: "string" }
  }
  field: {
    label: "scores"
    cardinality: { min: 1, max: 5 }
    type: { kind: "scalar", name: "number" }
  }
  field: { label: "payload", type: { kind: "any" } }
}
root: "Person"
```

Repeated `record` and `field` OML labels use ordinary OML array-sugar
([§4.3.1](../04-oml-grammar.md)) — no special syntax.

**Record/field order is not semantically significant**, the same as OSD
text. Canonical serialization order for every Schema-producing operation —
including `schema_from_document`/`parse_schema_oml` — follows
[§3.3's canonical serialization order](../03-schema-model.md#33-formal-definition)
invariant unchanged; this extension states no order rule of its own.
Consequence: raw Document equality is *stricter* than schema equivalence —
comparing two Schema-Documents for real requires materializing to `Schema`
first ([§E.9](#e9-architecture)), not diffing the Documents directly.

Field labels containing `[` or `]` are illegal at the OSD level
(`schema.bracket-in-label`, [§5.4](../05-osd-grammar.md)) because they can
collide with `validate`'s diagnostic-path convention. OSD-OML inherits this
the same way it inherits the `[0,0]` ban: the semantic-validation layer MUST
reject a `field.label` string containing either character, with the same
code, regardless of surface syntax.

## E.8 Cardinality-on-fields principle (Document-shape design rule)

**A field is `[1,1]` only if it's genuinely mandatory in every valid case.
It's `[0,1]` if it's legitimately absent in some case. The Document shape
never tries to encode *which* case makes which presence/absence correct** —
that is always the semantic-validation layer's job ([§E.10](#e10-structural-vs-semantic-validation)).

Applied throughout:

| Field | Cardinality | Why |
|---|---|---|
| `Type.kind` | `[1,1]` | always present |
| `Type.name` | `[0,1]` | absent for `any` |
| `Type.nullable` | `[0,1]` | absent unless true |
| `Field.label` | `[1,1]` | every field is named — OSD's own grammar has no unlabeled-field form |
| `Field.type` | `[1,1]` | every field has a type |
| `Field.cardinality` | `[0,1]` | absent means the default |
| `Record.name` | `[1,1]` | every record is named |
| `Record.field` | `[0,]` | empty records are legal (`record R { }`) |
| top-level `record` | `[0,]` | — |
| top-level `root` | `[1,1]` | exactly one, required |

## E.9 Architecture

A Schema-Document MUST be parsed and written with the exact same generic
`read_oml`/`write_oml` used for any other Document — implementations MUST
NOT introduce a schema-aware mode into the OML layer.

All schema-specific semantics live in a separate conversion layer above
that, mirroring OSD text's own architecture: a grammar produces a parse
tree, and a separate stage-2 pass does the semantic checks
([§5.1](../05-osd-grammar.md)'s two-stage model). This extension swaps "OSD
grammar" for "generic OML parsing" as stage 1 and reuses the same stage 2.

A free consequence of this architecture: Schema-Documents automatically
inherit every existing Document-level safety limit (max depth, max node
count, integer digit caps, [§2.4](../02-document-model.md)) — implementations
need not build anything new for this.

## E.10 Structural vs. semantic validation

There is no separate meta-schema mechanism for OSD-OML's Document shape —
per [§E.9](#e9-architecture), stage 2 is Core's own shared
schema-construction validator, the same one OSD text uses, applied to
generic OML input instead of an OSD parse tree. That validator MUST catch
everything below:

| Problem | Error code |
|---|---|
| negative / inverted cardinality | `schema.invalid-cardinality` |
| `[0,0]` cardinality (§E.5) | `schema.invalid-cardinality` |
| `min`/`max` not `integer`-kind | `schema.invalid-cardinality` |
| `name`/`label` not `string`-kind | `schema.invalid-type` |
| empty-string `field.label` | `schema.empty-label` |
| `[`/`]` in `field.label` (§E.7) | `schema.bracket-in-label` |
| duplicate `record.name` | `schema.duplicate-record` |
| duplicate `field.label` (within a record) | `schema.duplicate-field` |
| reserved record name (matches scalar keyword or `any`) | `schema.reserved-name` |
| zero `root` edges | `schema.no-root` |
| more than one `root` edge | `schema.duplicate-root` |
| unresolved reference | `schema.unknown-type` |
| unknown/extra keys anywhere | `schema.unknown-key` |

All codes are reused from the existing `schema.*` family
([§8](../08-conformance-and-errors.md)) except `schema.invalid-type` and
`schema.unknown-key`, which are new — these checks have no OSD-text analog
because OSD's own grammar makes them structurally impossible there (e.g.
`min` being non-integer-kind cannot happen in OSD text, since the grammar's
`int` token guarantees it; OSD-OML's `min` is an arbitrary OML value, so the
check becomes reachable for the first time).

## E.11 Validation contract

- **Atomic.** Converting a Schema-Document MUST either succeed with a fully
  valid `Schema`, or fail and produce nothing — never a partial `Schema`.
  This mirrors `parse_schema`'s existing contract for OSD text.
- **Fail-fast**, not collect-all-errors. Most checks are causally dependent
  on each other (a duplicate-name failure makes downstream
  reference-resolution checks meaningless), and Schema-Documents are
  expected to be machine-generated, so one bug class is likely to repeat
  across many fields — fixing the generator fixes all instances at once.
- **No fixed cross-implementation check order is required**, despite
  fail-fast. Conformance is defined by test policy, not by mandating
  implementation order: a vector with exactly one error asserts the exact
  `code`/`path`; a vector with multiple simultaneous errors (if one is ever
  added) asserts only `ok: false`, nothing about which error surfaced
  first.
- "Validated in the same manner" across implementations means the same
  *externally observable* contract (check list, codes/paths for
  single-error cases, atomicity, the multi-error looseness above) — **not**
  identical internal architecture. Internal structure (two-stage vs.
  one-pass, etc.) is legitimate implementation-surface variation, the same
  category as method names and builder patterns already permitted to
  differ across implementations.

## E.12 API / CLI surface

Since OSD and OSD-OML are peers, not one derived from the other, there is
no single read/write function that sensibly handles "either" without being
told which.

**Read side:**

- `parse_schema(text) -> Schema` — existing, OSD text specific, unchanged.
- `schema_from_document(doc) -> Schema` — new pure conversion primitive.
  Takes an already-parsed Document and applies exactly the semantic layer
  described in [§E.10](#e10-structural-vs-semantic-validation).
- `parse_schema_oml(text) -> Schema` — new convenience wrapper, equal to
  `schema_from_document(read_oml(text))`.

**Write side**, symmetric:

- `write_schema(schema) -> osd_text` — existing, unchanged.
- `schema_to_document(schema) -> Document` — new primitive.
- `write_schema_oml(schema) -> oml_text` — new wrapper.

**CLI:** every schema-consuming and schema-producing command (`validate`,
`materialize`, `lint`, `normalize`, `extract`, `compatible-with`,
`equivalent`, `is-empty`, `prune`, `schema format`, ...) MUST accept
`--from`/`--to osd|osd-oml`, reusing the existing flag pattern the
data-conversion commands already have. Extension-based format detection is
explicitly rejected — it is unreliable in general, and outright impossible
for stdin input, which has no filename to infer from. Flag values MUST
match the format name exactly (`osd-oml`, not a shorthand like `oml`).

**Backward compatibility:** omitting `--from`/`--to` entirely MUST mean
`osd`, unconditionally — matching prior, only-ever-OSD behavior exactly.
`osd-oml` is always opt-in.

## E.13 Worked example

Both directions, for one small schema:

**OSD:**

```osd
record Address {
    "street": string,
    "city": string,
}
record Person {
    "name": string,
    "nickname" [0,1]: string?,
    "address": Address,
}
root Person
```

**OSD-OML** (canonical form, one record/field per line for readability —
compact form is also legal and MUST round-trip identically per OML's own
compact-mode guarantee, [§4.9](../04-oml-grammar.md)):

```oml
record: {
  name: "Address"
  field: { label: "street", type: { kind: "scalar", name: "string" } }
  field: { label: "city", type: { kind: "scalar", name: "string" } }
}
record: {
  name: "Person"
  field: { label: "name", type: { kind: "scalar", name: "string" } }
  field: {
    label: "nickname"
    cardinality: { min: 0 }
    type: { kind: "scalar", name: "string", nullable: true }
  }
  field: { label: "address", type: { kind: "ref", name: "Address" } }
}
root: "Person"
```

**Round-trip requirement:**

```
schema_from_document(read_oml(write_oml(schema_to_document(S)))) == S
```

for every valid `Schema` `S`, where `==` means `equivalent(S, S')` per
[§6.7](../06-schema-algebra.md)'s Schema-equivalence, not raw Document
equality (§E.7's note on order not being significant).

## E.14 Non-goals

The following are explicitly out of scope for this extension and are not
implicitly authorized by it:

- **A bundle format** (`schema` + repeated `document` edges) combining a
  schema with conforming documents in one OML file, for RPC- and
  database-shaped use cases. Deferred until a concrete application needs
  it, so the design is pulled by real requirements (streaming? partial
  results? schema-by-reference?) instead of guessed at in the abstract.
- JSON/YAML/TOML/XML serialization of Schema — technically reachable later
  via the existing codecs once Schema is Document-shaped, but not
  specified here.
- A binary OML encoding of Schema — depends on a binary OML format
  existing at all, which is itself unspecified.

## E.15 Conformance

An implementation conforms to this extension when it implements
`schema_from_document`, `parse_schema_oml`, `schema_to_document`, and
`write_schema_oml` per §E.5–§E.12, passes the extension's conformance
vectors (tagged `osd-oml` in the test suite), and satisfies the round-trip
requirement (§E.13) for every vector's schema. Extension conformance is
reported independently of Core conformance, per
[Extensions §Conformance and versioning](overview.md#conformance-and-versioning).
