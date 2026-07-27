# 1. Glossary

One authoritative definition per term. Every other chapter uses these terms
exactly as defined here. Where a term has a common meaning elsewhere that
differs (notably *array*, *object*, *nullable*), the difference is stated.

---

**any** — The one type in the Schema model that accepts every legal Document
value, including `null`. It opens the value at one declared, counted label. It
does not open the record's label alphabet. Written `any` in OSD, lowercase only.
`any?` is an error, because `any` already includes `null`. See
[chapter 3](03-schema-model.md).

**cardinality** — A field's `[min, max]` bound on how many edges with that
field's label may appear in a node. `min` is a non-negative integer. `max` is a
non-negative integer or unbounded. Cardinality is the only mechanism for
multiplicity: it expresses required, optional, and repeated in one range. It
never constrains order.

**closed record** — A record that permits only the labels its fields name. Any
other label in a matching node is invalid. Every record in Omnist is closed;
there is no open record and no wildcard field.

**Document** — A node, together with the invariants in
[chapter 2](02-document-model.md). Written OML, JSON, YAML, TOML, or XML; the
Document itself is format-independent.

**edge** — A pair `(label, target)`. The unit a node is built from.

**environment (env)** — The map from record name to record definition that a
schema carries. Written `env` throughout. Lookup is by name, so forward
references and mutual recursion both work.

**equivalent** — Two schemas accept exactly the same set of Documents. Computed
as mutual `compatible_with`. See [chapter 6](06-schema-algebra.md).

**field** — A triple `(label, type, cardinality)` inside a record. A field's
type is exactly one scalar kind, exactly one reference, or `any`. It is never a
composition of candidates.

**label** — The string naming an edge. Labels may repeat within a node. In OSD a
label is always written quoted, which is what distinguishes it from a schema
name.

**materialization** — Stage two of ingestion: walking an untyped node together
with a schema, upgrading leaves to the declared types where the conversion is
value-exact, and checking record shape in the same pass. See
[chapter 7](07-codecs-and-deserialization.md).

**node** — Either a scalar value (including `null`), or an ordered list of
edges. This is the only recursive structure in the Document model.

**nullable** — A property of a *scalar* type, written with a trailing `?`. A
nullable scalar additionally accepts `null`. Nullability MUST NOT be applied to
a reference or to `any`. "This record might be absent" is cardinality `[0,1]`,
not nullability. See [chapter 3](03-schema-model.md).

**OML** — Omnist Markup Language. The native text format for Documents.
Brace-delimited, not indentation-sensitive. See
[chapter 4](04-oml-grammar.md).

**OML-Core** — The subset of OML that the canonical writer emits and every
conformant reader MUST accept.

**OML-Extended** — Read-only spellings a conformant reader MUST accept but a
canonical writer MUST NOT emit: raw strings and triple-quoted multiline strings.

**optional** — Cardinality with `min = 0`. Distinct from nullable: optional
means the edge may be absent, nullable means the value present at the edge may
be `null`.

**OSD** — Omnist Schema Definition. The text format for Schemas. See
[chapter 5](05-osd-grammar.md).

**record** — A named, closed set of fields. The only definition kind in the
Schema model. Records are always named and always reached through a reference;
there are no inline or anonymous records.

**reference (Ref)** — A named pointer to a record in the environment. The only
way a field's type can be a record.

**root** — The reference a schema declares as its entry point. Exactly one root
per schema. A schema is single-rooted, which is what makes a lossless XML round
trip possible.

**satisfiable** — A record is satisfiable if at least one finite Document can
match it. A record with a mandatory field whose type is an unsatisfiable record
is itself unsatisfiable. Computed as a least fixpoint. See
[chapter 6](06-schema-algebra.md).

**scalar** — A leaf value. Exactly seven kinds exist: `string`, `integer`,
`number`, `boolean`, `date`, `time`, `datetime`. There is no `float` kind and no
`decimal` kind. `null` is a value, not a kind: it is admitted by a nullable
scalar or by `any`.

**Schema** — The pair `(root, env)`. `root` is a reference; `env` maps names to
records.

**Schema Algebra** — The set of decidable operations over schemas defined in
[chapter 6](06-schema-algebra.md): `compatible_with`, `equivalent`, `normalize`,
`prune`, `is_empty`, `extract`, `infer`, `lint`.

**subschema** — `a` is a subschema of `b` if every Document `a` accepts is also
accepted by `b`. `compatible_with(a, b)` decides this.

**target** — The second component of an edge: either a scalar value or a nested
node.

**type** — Exactly one of: a scalar (with a nullable flag), a reference, or
`any`. Nothing else is a type.

**unsatisfiable** — Not satisfiable. A schema whose root record is unsatisfiable
accepts no Document at all; `is_empty` reports this.

---

## 1.1 Pairs that get confused

Several terms look alike but describe different sides of the model — one data,
one constraint. This table exists because mixing them up is the single most
common way to misread this spec.

| This | Is not | Because |
|---|---|---|
| **edge** | **field** | An edge is a `(label, target)` pair in a Document. A field is a `(label, type, cardinality)` rule in a Record. Edges are data; fields are constraints. |
| **multiplicity** | **cardinality** | Multiplicity is how many edges with a given label a node actually has, right now. Cardinality is the `[min, max]` range a field allows. Multiplicity is measured; cardinality is declared. |
| **scalar value** | **scalar (type)** | `"Ann"` is a scalar value. `string` is a scalar type. A value has a kind; a type constrains which kind a value may have. |
| **nullable** | **cardinality `[0,1]`** | Nullable says the edge must exist but its value may be `null`. `[0,1]` says the edge itself may be absent. They answer different questions and can combine (`string? [0,1]`). |
| **`any`** | **reference (`Ref`)** | `any` stops validation at that point — anything goes. A reference continues validation into a named, closed record. `any` is the one deliberate opening; `Ref` is the ordinary case. |
| **array sugar** | **edge list** | Array sugar (`["a", "b"]`) is concrete syntax some formats use. An edge list (repeated `(label, target)` pairs) is what it always becomes in the Document model. There is no array *type* underneath the sugar. |
| **prune** | **normalize** | `prune` removes what can never appear (unreachable or unsatisfiable records). `normalize` does that and then merges records that are structurally identical. `normalize` always implies `prune`; `prune` alone does not merge. |
| **untyped Document** | **materialized Document** | The untyped Document is stage-one output — a parsed tree with no schema applied. The materialized Document is stage-two output — the same tree with leaves upgraded to schema-declared kinds. See [chapter 7](07-codecs-and-deserialization.md). |
| **record** | **Schema** | A record is one closed field template. A Schema is the whole graph: a root reference plus every record it can reach, `(root, env)`. |
| **OML** | **OSD** | OML writes data. OSD writes constraints. Never the reverse. |
