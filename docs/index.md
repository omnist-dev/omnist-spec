# Omnist Specification, v0.1

## Abstract

Omnist is a data-modeling system built on one small formalism. A **Document** is
an ordered list of labeled edges. A **Schema** is a graph of named, closed
records constraining those edges. Because both models are small and closed, a
set of operations over schemas — inclusion, equivalence, minimization,
extraction, inference — are decidable and total, not best-effort.

This specification defines:

1. the Document model, and the invariants every implementation must preserve;
2. the Schema model, and what it deliberately cannot express;
3. **OML**, the text format for Documents;
4. **OSD**, the text format for Schemas;
5. the **Schema Algebra**: the operations over schemas and their exact semantics;
6. the ingestion pipeline that turns JSON, YAML, TOML, and XML into Documents;
7. a conformance protocol and error taxonomy.

The target is byte-identical conformance results across independent
implementations. Where a rule is underspecified, that is a defect in this
document, not license to choose.

## Key principles

**One model, many formats.** JSON, YAML, TOML, XML, and OML all read into the
same Document. Conversion is read-one, write-another. No format-specific model
exists.

**Repeated labels are the array.** There is no array type in the Document model
and no array type in the Schema model. `{"tag": ["x","y"]}` is the label `tag`
occurring twice. This is what lets XML's interleaving survive the round trip
that a map-of-arrays would destroy.

**Order is data, never a constraint.** A Document preserves edge order because
it is a faithful record of its input. Schema validation ignores order entirely;
only counts matter.

**Closed by default, open only where written.** Records name every label they
allow. Scalar types are never composed. There are no maps, no wildcard keys, no
unions, no enums. The single opening is the `any` type, which is visible in the
schema text at a fixed label.

**Decidability is the constraint that shapes the rest.** Every refusal in this
spec exists to keep the Schema Algebra total and exact. A feature that would
force an operation to answer "maybe" is not added.

## Relationship to prior work

The Schema Algebra descends from Lee and Cheung, *XML Schema Computations*
(CIKM 2010). Omnist generalizes the paper in one direction and simplifies it in
three. Chapter 6 states the deltas precisely; that is the right place to read
them, since they only matter once the operations are on the table.

## Keywords

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this
specification are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), and only when they appear in
all capitals.

Text in blockquotes, and any section marked *Non-normative*, is commentary. It
explains reasoning and does not impose requirements.

## Reading order

| Chapter | Read it for |
|---|---|
| [01 Glossary](01-glossary.md) | Terms used everywhere else |
| [02 Document model](02-document-model.md) | The data structure |
| [03 Schema model](03-schema-model.md) | The constraint structure |
| [04 OML grammar](04-oml-grammar.md) | Writing Documents as text |
| [05 OSD grammar](05-osd-grammar.md) | Writing Schemas as text |
| [06 Schema Algebra](06-schema-algebra.md) | The operations |
| [07 Codecs](07-codecs-and-deserialization.md) | Reading other formats |
| [08 Conformance and errors](08-conformance-and-errors.md) | Passing the test suite |
| [09 Divergence ledger](09-divergence-ledger.md) | What implementations may differ on |
| [10 Governance](10-governance-and-versioning.md) | How this document changes |
