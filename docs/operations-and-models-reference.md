# Operations & Models Reference

*Non-normative index.* Every row here is a pointer, not a new definition. If
this page and the chapter it links to ever disagree, the chapter wins — the
same disclaimer the [glossary](01-glossary.md) and other cross-referencing
pages in this spec already carry. This is not the language-agnostic API
reference already discussed and declined; it picks no calling convention and
introduces no per-language binding. It only collects signatures that are
already normative elsewhere, in the same spirit as the glossary indexing
*terms* rather than *signatures*.

## Models

| Model | Structure | Purpose | Defined in |
|---|---|---|---|
| `Document` | `node \| value` | A parsed instance of any supported format — a node, or (rarely) a bare scalar. | [§2.2](02-document-model.md#22-formal-definition) |
| `Node` | `[edge, edge, ...]` (ordered; labels MAY repeat) | An ordered, possibly-repeating list of labeled edges — Omnist's replacement for the object/array distinction. | [§2.2](02-document-model.md#22-formal-definition) |
| `Edge` | `(label: String, target: value \| node)` | One labeled child of a node. | [§2.2](02-document-model.md#22-formal-definition) |
| `Scalar` (value) | `string \| integer \| number \| boolean \| date \| time \| datetime` | The seven scalar kinds a Document leaf may hold. | [§2.2.1](02-document-model.md#221-scalar-kinds) |
| `Schema` | `(root: Ref, env: Name -> Record)` | A named, closed graph of records — the type a Document is validated or materialized against. | [§3.3](03-schema-model.md#33-formal-definition) |
| `Record` | `{ Field, ... }` (closed: only these labels) | One node shape: an exhaustive, closed list of the fields it permits. | [§3.3](03-schema-model.md#33-formal-definition) |
| `Field` | `(label: String, type: Type, cardinality: [min, max])` | One declared edge on a record: its label, the type at the other end, and how many times it may occur. | [§3.3](03-schema-model.md#33-formal-definition) |
| `Ref` | `Name` (resolved in `env`) | A reference to another record by name; how records compose without inline nesting. | [§3.3](03-schema-model.md#33-formal-definition) |
| `Any` | the singleton `any` type | The model's one sanctioned opening — accepts every legal value or node, closes nothing else. | [§3.7](03-schema-model.md#37-the-any-type) |
| `Cardinality` | `[min, max]` (`max` MAY be unbounded) | The count range an edge's label may occur in a node; the model's only multiplicity mechanism. | [§3.4](03-schema-model.md#34-cardinality) |
| `ValidationResult` | list of `(path, code, message)` | Every conformance failure found for one `validate` or `materialize` call; empty means valid. | [§3.6](03-schema-model.md#36-validation) |
| `AnyFallback` | `(location: String, reason: String)` | One reported opening from an `allow_any = true` `infer` call: where, and why that field couldn't be reduced to one type. | [§6.10](06-schema-algebra.md#610-infersamples) |
| `LintFinding` | `(code, severity, location)` (+ a non-normative message) | One diagnosed structural issue in a schema itself — never a mutation, just a report. | [§6.11](06-schema-algebra.md#611-lints) |

## Operations

| Operation | Signature | Purpose | Defined in |
|---|---|---|---|
| `parse` | `parse(text, format) -> Document` | Stage 1 of reading: turns format text into an untyped Document. Never consults a schema, never fails because of one. | [§7.1](07-codecs-and-deserialization.md#71-two-stages) |
| `validate` | `validate(document, S) -> ValidationResult` | Checks whether a Document conforms to a schema; reports every failure, never converts. | [§3.6.1](03-schema-model.md#361-validatedocument-schema-pseudocode) |
| `materialize` | `materialize(node, S) -> node` (raises with every `ValidationResult` entry on failure) | Validates and upgrades leaves in one pass — the only value-exact, lossless-and-invents-nothing conversions. | [§7.2.1](07-codecs-and-deserialization.md#721-materializenode-schema-pseudocode) |
| `write` | `write(node, format) -> formatted text` | Renders a Document back out to a concrete format, grouping repeated labels into that format's array convention. | [§7.3.1](07-codecs-and-deserialization.md#731-writenode-format-pseudocode) |
| `compatible_with` | `compatible_with(A, B) -> Boolean` | True when every Document `A` accepts is also accepted by `B` — the backward-compatibility check for a schema change. | [§6.6](06-schema-algebra.md#66-compatible_witha-b) |
| `equivalent` | `equivalent(A, B) -> Boolean` | True when `A` and `B` accept exactly the same set of Documents — `compatible_with` in both directions. | [§6.7](06-schema-algebra.md#67-equivalenta-b) |
| `normalize` | `normalize(S) -> Schema` | Returns the canonical minimal schema equivalent to `S`: fewest records, unique up to naming. | [§6.8](06-schema-algebra.md#68-normalizes) |
| `prune` | `prune(S) -> Schema` | Returns a schema equivalent to `S` with every unreachable or unsatisfiable part removed. | [§6.5](06-schema-algebra.md#65-prunes) |
| `is_empty` | `is_empty(S) -> Boolean` | True when no finite Document can match `S`'s root — the satisfiability check. | [§6.4](06-schema-algebra.md#64-is_emptys-and-satisfiability) |
| `extract` | `extract(S, keep) -> Schema` | Returns the minimal subschema recognizing only Documents built from a given label set; fails if the root is invalidated. | [§6.9](06-schema-algebra.md#69-extracts-keep) |
| `infer` | `infer(samples, root_name = "Root", allow_any = false) -> Schema` | Drafts a schema that accepts a set of sample Documents — a starting point meant to be hand-edited, never normalized automatically. | [§6.10](06-schema-algebra.md#610-infersamples) |
| `infer_with_report` | `infer_with_report(samples, root_name = "Root", allow_any = false) -> (Schema, [AnyFallback])` | Same as `infer`, but also returns every `any`-opening it introduced, with location and reason. | [§6.10](06-schema-algebra.md#610-infersamples) |
| `lint` | `lint(S) -> [LintFinding]` | Diagnoses structural issues in a schema itself (unsatisfiable/unreachable/duplicate records, `any` openings) — reports only, never mutates. | [§6.11](06-schema-algebra.md#611-lints) |

## How this affects vector and fixture authoring

Per [omnist-spec#23](https://github.com/omnist-dev/omnist-spec/issues/23): a
JSON-vector's `"operation"` field MUST be one of the operation names listed
above — this page is the canonical vocabulary, not a free-text field authors
can spell differently across files. Where a vector's `input`/`expect`
describes a model instance, it SHOULD use the same field/type names this page
uses, so a vector reads as an instance of a documented model rather than an
ad hoc shape a reader has to reverse-engineer.
