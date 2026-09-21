# OSD-OML

**Status: normative.** Version 1.1 of this extension, versioned
independently of Core per
[Extensions: Conformance and versioning](overview.md#conformance-and-versioning).
Depends on Core only.

**v1.1 (2026-09-13):** E.5 through E.9 rewritten from documentation-style
prose into a closed formal grammar plus numbered, exhaustive rules —
matching the style [§3.3](../03-schema-model.md#33-formal-definition)/[§5](../05-osd-grammar.md)
already hold themselves to. No previously-legal input becomes illegal and
no previously-illegal input becomes legal for anything already covered by
an existing conformance vector; this closes gaps that had no vector at
all (a missing error code for `nullable: false`, no rule for `type.kind`
outside its three legal values, no path-kind assignment for the codes
unique to this extension, and a new rule — R-3a, `schema.invalid-name` —
closing a real hole where a `Schema` constructible via OSD-OML had no OSD
text representation at all). See `omnist-spec`'s own `CHANGELOG.md` for
the full list.

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
  and writer as any other OML document (§E.7).
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

## E.5 Formal definition

```
schema-doc    = { record: record-node*, root: String }   ; CLOSED: only these labels
record-node   = { name: String, field: field-node* }      ; CLOSED
field-node    = { label: String, type: type-node,
                   cardinality: cardinality-node? }        ; CLOSED
type-node     = scalar-node | ref-node | any-node
scalar-node   = { kind: "scalar", name: scalar-name,
                   nullable: True? }                       ; CLOSED
ref-node      = { kind: "ref", name: String }               ; CLOSED
any-node      = { kind: "any" }                              ; CLOSED
scalar-name   = "string" | "integer" | "number" | "boolean"
              | "date" | "time" | "datetime"
cardinality-node = { min: Integer?, max: Integer? }          ; CLOSED
```

Each `; CLOSED` node has exactly the keys shown — no other key is legal on
that node, regardless of `kind`. This is what makes `type-node`'s three
branches mutually exclusive by construction rather than by convention: for
example, `nullable` simply is not part of `ref-node`'s or `any-node`'s
grammar, so it can never be a semantic afterthought on those branches (see
R-14, R-15) — it is a structural fact about the shape, the same way `str`
and `int` are different Python types rather than one type with a
"which-one" flag.

`type-node` is always a node, never a bare literal — including
`kind: "any"`, even though `any` has no variability to attach to it. This
favors uniformity (every field's `type` is always a node; nothing
downstream branches on "is this a string or an object") over the shorter
bare-literal alternative `any` alone would otherwise allow.

Repeated `record` and `field` OML labels use ordinary OML array-sugar
([§4.3.1](../04-oml-grammar.md)) — no special syntax.

## E.6 Rules

Numbered for direct citation, matching
[§3.3](../03-schema-model.md#33-formal-definition)'s S-1..S-8 and
[§5.5](../05-osd-grammar.md#55-cardinality)'s conventions. Each rule states
its violation code. **This list is authoritative and closed: a conforming
implementation's validator has exactly these checks, for input that
already matches E.5's grammar shape — no more, no fewer**, except where a
rule explicitly notes it is inherited from a Core rule not restated here
in full (see "Error path assignment" below).

### Top level

- **R-1.** `record` MUST be `[0,]`; `root` MUST be exactly `[1,1]`. Missing
  `root` → `schema.no-root`. More than one `root` → `schema.duplicate-root`.
- **R-2.** `root`'s value MUST be `string`-kind and MUST resolve to a
  declared `record.name` (R-16). Unresolved (a dangling root reference) →
  `schema.unknown-type`, **path `$`** — this is
  [§8.4](../08-conformance-and-errors.md#84-paths)'s existing whole-schema
  fallback for exactly this case, unchanged from OSD text; §8.4.1 preserves
  it as an explicit exception to its own two rules. Not `string`-kind →
  `schema.invalid-type`, which is new to OSD-OML and takes the Document path
  §8.4.1 assigns it.

### `record-node`

- **R-3.** `name` MUST be `[1,1]`, `string`-kind → `schema.missing-key` if
  absent, `schema.invalid-type` if present but not `string`-kind.
- **R-3a.** `name` MUST satisfy
  [§3.3](../03-schema-model.md#33-formal-definition) S-8 (the `Name`
  domain, `[A-Za-z_][A-Za-z0-9_]*`) → `schema.invalid-name` if it does not.
  This exists because OSD text's own tokenizer makes an out-of-domain
  record name unwritable — it can't even be parsed, let alone constructed
  — while OSD-OML's `name` is a plain string with no such constraint. Without
  this rule, `schema_from_document` could construct a `Schema` that
  `write_schema` has no way to represent as OSD text at all.
- **R-4.** `name` MUST NOT equal any `scalar-name` keyword (R-12) or `any`
  → `schema.reserved-name`. **Comparison is exact and case-sensitive**, per
  [§3.3](../03-schema-model.md#33-formal-definition) S-3.
- **R-5.** `name` MUST be unique across all `record-node`s in the document
  → `schema.duplicate-record`.
- **R-6.** `field` MAY be `[0,]` (empty records are legal).

### `field-node`

- **R-7.** `label` MUST be `[1,1]`, `string`-kind, non-empty, and MUST NOT
  contain `[` or `]` → `schema.missing-key` / `schema.invalid-type` (same
  pattern as R-3) / `schema.empty-label` / `schema.bracket-in-label`
  respectively. (Unlike R-3a, `label` has no identifier-domain restriction
  — a field label is a *value*, per [§5.2](../05-osd-grammar.md#52-the-quoting-rule)'s
  identifier-vs-value distinction, and OSD text allows arbitrary quoted-string
  labels; there is no asymmetry here to close.) One consequence runs the other
  way and is handled on the OSD side rather than here: a label carrying a C0
  control character is constructible through this rule and has no OSD text at
  all, so an OSD *writer* refuses it per
  [OSD-14](../05-osd-grammar.md#59-canonical-output) while `write_schema_oml`
  writes it normally — this surface is the one that can carry it.
- **R-8.** `label` MUST be unique within its enclosing `record-node` →
  `schema.duplicate-field`.
- **R-9.** `type` MUST be `[1,1]` → `schema.missing-key` if absent.
- **R-10.** `cardinality` MAY be `[0,1]`; absent and `{}` are both legal
  and both mean the default (E.8 states which one a canonical *writer*
  emits).

### `type-node`

- **R-11.** `kind` MUST be `[1,1]`, `string`-kind, and MUST be exactly one
  of `scalar` / `ref` / `any` → `schema.missing-key` / `schema.invalid-type`
  (wrong Document value-kind, or a `string`-kind value outside the
  three-value set — both cases reuse the same code as R-3's "right key,
  wrong content" pattern).
- **R-12.** (`kind: "scalar"`) `name` MUST be `[1,1]`, `string`-kind, and
  MUST be one of the seven `scalar-name` keywords → `schema.missing-key` /
  `schema.invalid-type` / `schema.unknown-type` respectively.
- **R-13.** (`kind: "scalar"`) `nullable`, if present, MUST be the literal
  `true` → `schema.invalid-type` if present as `false` (reuses R-11's
  "right key, wrong content" code; there was previously no stated
  violation code for this case at all).
- **R-14.** (`kind: "ref"`) `name` MUST be `[1,1]`, `string`-kind, and MUST
  resolve to a declared `record.name` (R-16) → `schema.missing-key` /
  `schema.invalid-type` / `schema.unknown-type`. `nullable` is not a legal
  key in this branch (E.5) → `schema.unknown-key` if present — this is how
  [§3.3](../03-schema-model.md#33-formal-definition) S-7 (`nullable` only
  on a `Scalar`) is enforced for OSD-OML: structurally, via the grammar,
  not as a separate semantic check layered on top.
- **R-15.** (`kind: "any"`) no keys beyond `kind` are legal →
  `schema.unknown-key` if `name` or `nullable` is present.

### Reference resolution

- **R-16.** A `ref-node`'s `name` is resolved by exact, case-sensitive
  string lookup against the set of all declared `record.name`s in the
  document, collected independently of edge order. **Forward references
  and mutual recursion are legal** — this mirrors
  [§5.6](../05-osd-grammar.md#56-types)'s "resolution is by lookup in the
  schema's environment" guarantee for OSD text exactly; OSD-OML does not
  relax or tighten it.

### `cardinality-node`

- **R-17.** `min`, if present, MUST be `integer`-kind and non-negative →
  `schema.non-integer-cardinality` / `schema.invalid-cardinality`.
- **R-18.** `max`, if present, MUST be `integer`-kind, non-negative, and
  `>= min` (using `min`'s effective value, 0 if absent) →
  `schema.non-integer-cardinality` / `schema.invalid-cardinality`.
- **R-19.** `{ min: 0, max: 0 }` is illegal, the same reasoning as OSD
  text's `[0,0]` ban ([§5.5](../05-osd-grammar.md#55-cardinality)): a field
  that can never appear is indistinguishable from an undeclared one →
  `schema.invalid-cardinality`.

### Closure

- **R-20.** Any key present on a node that is not listed in that node's
  E.5 grammar branch → `schema.unknown-key`. This single rule is what
  makes E.5's `; CLOSED` annotations enforceable, and is why R-1 through
  R-19 never separately restate "no other keys are allowed."

### Error path assignment

Path-kind assignment is **not** an OSD-OML rule and is not restated here.
It is Core's, in
[§8.4.1](../08-conformance-and-errors.md#841-which-kind-each-schema-code-uses):
`schema.missing-key`, `schema.invalid-type`, `schema.unknown-key` and
`schema.invalid-name` use a Document path; every other `schema.*` code uses a
Schema path; the whole-schema cases, including R-2's dangling root, keep `$`.

- **R-21.** A diagnostic raised by any rule in this section MUST carry the
  path kind §8.4.1 assigns to its code.
- **R-22.** *Retired.* This number previously carried the Schema-path half of
  the assignment, now stated in §8.4.1. The number is kept rather than reused
  so that existing citations to R-22 resolve to an explanation instead of to
  whatever rule would otherwise have inherited the slot — this list is
  numbered for citation, so a vacated number is a hazard, not a tidy-up.

The reason those four codes needed an explicit assignment at all is a
property of this extension's input shape: OSD text's grammar establishes a
record or field's identity before any check can run, so a Schema path was
always the only buildable option there. OSD-OML's Document-shaped input has
no such guarantee — a `record-node` missing its `name` has no `RecordName` to
build a Schema path from. The rule is Core's because any future surface with
the same property inherits the same problem.

Every code cited above is defined in
[§8.3.3](../08-conformance-and-errors.md#833-schema-schema-well-formedness)
as a general Schema-construction rule, not something owned by this
extension — they apply identically regardless of which surface (OSD text
or OSD-OML) fed the shared validator. `schema.missing-key`,
`schema.invalid-type`, `schema.unknown-key`, and `schema.invalid-name` have
no OSD-text analog: OSD's own grammar makes the first three structurally
impossible to reach (e.g. a field with no type, or a stray key, cannot be
written in OSD text at all), and the fourth is impossible for a different
reason — OSD's `name` token cannot tokenize outside its own domain in the
first place. OSD-OML's generic OML input is what makes all four checks
reachable for the first time, not a rule specific to this extension.

## E.6a Illustrative examples

These exist to make E.6's rules easy to check by eye, not to define
anything — if an example and a rule ever disagree, the rule wins, and
that's a bug in the example.

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
A legal, unremarkable schema exercising every branch in E.5's grammar at
once — worth reading top to bottom once before the boundary cases below.

**R-3a (identifier domain).** `record: { name: "My Record!" }` — illegal
→ `schema.invalid-name` (R-3a) — `"My Record!"` is a perfectly good OML
string but not a legal `Name` (§3.3 S-8): OSD text has no way to tokenize
it as a record name at all. `record: { name: "MyRecord" }` is legal.

**R-4 (reserved name).** `record: { name: "string" }` — illegal →
`schema.reserved-name`, exact match against the keyword. `record: { name: "String" }`
(capital S) is a case-mismatch — whether this collides is not yet settled
even for OSD text (§3.3 S-3's comparison rule is newly stated but this
specific boundary was not part of what was verified); no example is given
for it here until that's confirmed, rather than asserting an answer.

**R-11 (`kind` outside the three-value set).**
```oml
type: { kind: "text", name: "string" }
```
illegal → `schema.invalid-type` — `"text"` is `string`-kind but not one of
`scalar`/`ref`/`any`.

**R-13 (`nullable: false` explicitly present).**
```oml
type: { kind: "scalar", name: "string", nullable: false }
```
illegal → `schema.invalid-type`. Compare to the legal non-nullable form,
which omits the key entirely: `type: { kind: "scalar", name: "string" }`.

**R-14 (`nullable` not legal on `ref-node`).**
```oml
type: { kind: "ref", name: "Address", nullable: true }
```
illegal → `schema.unknown-key` — `nullable` is not in `ref-node`'s closed
key set (E.5), regardless of its value. This is the structural enforcement
of Core's S-7.

**R-16 (forward reference, legal).** A `record: { name: "Person", field: [{ label: "address", type: { kind: "ref", name: "Address" } }] }`
declared *before* `record: { name: "Address", ... }` is legal — R-16
collects all record names before resolving any `ref`, so declaration order
carries no meaning.

**R-19 (`{min: 0, max: 0}` illegal).**
```oml
field: { label: "x", cardinality: { min: 0, max: 0 }, type: { kind: "scalar", name: "string" } }
```
illegal → `schema.invalid-cardinality`.

**R-20 (unknown key, general case).**
```oml
record: { name: "Person", description: "a person", field: [] }
```
illegal → `schema.unknown-key` — `description` is not in `record-node`'s
closed key set (E.5), even though it's a plausible-looking addition.

**E.8 (canonical omission, general case).**
`field: { label: "name", type: { kind: "scalar", name: "string" } }` is
the canonical form for a required, non-nullable `string` field — no
`cardinality` edge, not `cardinality: {}`.

The full end-to-end example (one complete schema, both OSD and OSD-OML
form, plus the round-trip requirement) is in E.12.

## E.7 Architecture and construction

A Schema-Document MUST be parsed and written with the exact same generic
`read_oml`/`write_oml` used for any other Document — implementations MUST
NOT introduce a schema-aware mode into the OML layer. All schema-specific
semantics live in a separate conversion layer above that, mirroring OSD
text's own architecture: a grammar produces a parse tree, and a separate
stage-2 pass does the semantic checks ([§5.1](../05-osd-grammar.md)'s
two-stage model). This extension swaps "OSD grammar" for "generic OML
parsing" as stage 1 and reuses the same stage 2 — E.6's rules *are* that
shared stage 2, applied to generic OML input instead of an OSD parse tree,
with no separate meta-schema mechanism of its own. A free consequence:
Schema-Documents automatically inherit every existing Document-level
safety limit (max depth, max node count, integer digit caps,
[§2.4](../02-document-model.md)) — implementations need not build
anything new for this.

**Construction algorithm (non-normative).** A reference shape for
`schema_from_document`, not a binding procedure — per
[§E.10](#e10-validation-contract)'s "internal structure is permitted
variation" principle, extended explicitly to construction order, not just
error-reporting order. Provided because, unlike OSD text (where the
grammar's own parse order constrains implementations toward a similar
shape for free), a Document's edges carry no inherent evaluation order, so
there is nothing to fall back on without stating something explicitly.

1. Validate the document's shape against E.5's grammar and E.6's rules,
   independent of any particular traversal order (R-20's closure check and
   every per-node rule can each be evaluated locally).
2. Collect every declared `record.name` into an environment (R-16) —
   before resolving any `ref-node`, not interleaved with step 3.
3. For each `record-node`, construct its `Record` (in the sense of
   [§3.3](../03-schema-model.md#33-formal-definition)), resolving each
   `field`'s `type` against the environment built in step 2.
4. Resolve `root` against the same environment.
5. Construct the `Schema` per
   [§3.3](../03-schema-model.md#33-formal-definition).

Per [§E.10](#e10-validation-contract), failure at any step MUST produce no
partial `Schema` (atomicity) and MAY report any one applicable error
(fail-fast, no mandated cross-implementation order for which error
surfaces first when several exist).

**Record/field order is not semantically significant**, the same as OSD
text. Canonical serialization order for every Schema-producing operation —
including `schema_from_document`/`parse_schema_oml` — follows
[§3.3's canonical serialization order](../03-schema-model.md#33-formal-definition)
invariant unchanged; this extension states no order rule of its own.
Consequence: raw Document equality is *stricter* than schema equivalence —
comparing two Schema-Documents for real requires materializing to `Schema`
first, not diffing the Documents directly.

## E.8 Canonical `schema_to_document` output

A canonical writer MUST follow one general rule instead of a per-field
special case: **omit any key whose value equals that key's default; MUST
NOT emit the default explicitly.** This was previously only tested at the
level of individual vectors (e.g.
`extensions-osd-oml/write/exactly-one-cardinality-omits-the-edge`,
`extensions-osd-oml/write/any-type-has-no-name-edge`) without ever being
stated as the general rule those vectors were both instances of. Stating
it once here subsumes every specific case:

- `nullable: true` is the only legal explicit value (E.5); its default is
  effectively "absent" — never emitted, full stop.
- `cardinality` at `{min: 1, max: 1}` (exactly-one, the default) MUST be
  omitted entirely — MUST NOT be emitted as `{}`.
- `type.name` on an `any-node` — not applicable; E.5's `any-node` grammar
  branch has no `name` key to omit or emit in the first place.

Key order within a node is not semantically significant (no rule assigns
meaning to it) — a canonical writer MAY use any fixed, deterministic
order, but [§3.3](../03-schema-model.md#33-formal-definition)'s five order
principles still govern the order of *record* and *field* edges
themselves (E.7, unchanged from before this rewrite).

## E.9 Error code recap

A per-code index into E.6's rules, for "what can go wrong" lookup. **This
table is derived from E.6, not an independent source** — if it and a rule
ever disagree, the rule wins and the table has a bug.

| Code | Fired by | Path kind (Sec8.4.1) |
|---|---|---|
| `schema.no-root` | R-1 | Schema (`$` fallback) |
| `schema.duplicate-root` | R-1 | Schema (`$` fallback) |
| `schema.missing-key` | R-3, R-7, R-9, R-12, R-14 | Document (Sec8.4.1) |
| `schema.invalid-type` | R-2, R-3, R-7, R-11, R-12, R-13, R-14 | Document (Sec8.4.1) |
| `schema.invalid-name` | R-3a | Document (Sec8.4.1) |
| `schema.unknown-type` | R-2 (dangling root, path `$`), R-12, R-14 | R-2: `$` / R-12, R-14: Schema |
| `schema.reserved-name` | R-4 | Schema |
| `schema.duplicate-record` | R-5 | Schema |
| `schema.empty-label` | R-7 | Schema |
| `schema.bracket-in-label` | R-7 | Schema |
| `schema.duplicate-field` | R-8 | Schema |
| `schema.unknown-key` | R-14, R-15, R-20 | Document (Sec8.4.1) |
| `schema.non-integer-cardinality` | R-17, R-18 | Schema |
| `schema.invalid-cardinality` | R-17, R-18, R-19 | Schema |

## E.10 Validation contract

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

## E.11 API / CLI surface

Since OSD and OSD-OML are peers, not one derived from the other, there is
no single read/write function that sensibly handles "either" without being
told which.

**Read side:**

- `parse_schema(text) -> Schema` — existing, OSD text specific, unchanged.
- `schema_from_document(doc) -> Schema` — new pure conversion primitive.
  Takes an already-parsed Document and applies exactly the rules
  described in [§E.6](#e6-rules).
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

## E.12 Worked example

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
compact form is also legal and parses to the same Document, per OML's own
compact-mode guarantee, [§4.9](../04-oml-grammar.md#49-canonical-output)):

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

## E.13 Non-goals

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

## E.14 Conformance

An implementation conforms to this extension when it implements
`schema_from_document`, `parse_schema_oml`, `schema_to_document`, and
`write_schema_oml` per §E.5–§E.11, passes the extension's conformance
vectors (tagged `osd-oml` in the test suite), and satisfies the round-trip
requirement (§E.12) for every vector's schema. Extension conformance is
reported independently of Core conformance, per
[Extensions §Conformance and versioning](overview.md#conformance-and-versioning).
