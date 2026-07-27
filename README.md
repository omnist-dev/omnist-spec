# omnist-spec

The language-agnostic specification for **Omnist**: a Document model, a Schema
model, two text formats (OML and OSD), and a Schema Algebra of decidable
operations over schemas.

This repository holds the specification only. It contains no implementation.
Implementations live elsewhere and are expected to conform to what is written
here.

## Why a separate spec

Omnist has three implementations (Python, TypeScript, Rust). Without a written
contract, "what Omnist does" is whatever the oldest implementation happens to
do, and the other two drift. The spec exists so that:

- a new implementation can be written from the documents in `docs/` alone,
- a disagreement between implementations has an authority to appeal to,
- a behavior change is a spec change first, and a code change second.

## Repository structure

| Path | Contents |
|---|---|
| `docs/index.md` | Abstract, principles, RFC 2119 keyword notice |
| `docs/01-glossary.md` | One authoritative definition per term |
| `docs/02-document-model.md` | The Document: edges, scalars, invariants, resource caps |
| `docs/03-schema-model.md` | Records, fields, cardinality, `any`, what is refused |
| `docs/04-oml-grammar.md` | OML (Omnist Markup Language) grammar |
| `docs/05-osd-grammar.md` | OSD (Omnist Schema Definition) grammar |
| `docs/06-schema-algebra.md` | `compatible_with`, `equivalent`, `normalize`, `prune`, `is_empty`, `extract`, `infer`, `lint` |
| `docs/07-codecs-and-deserialization.md` | Two-stage ingestion, per-format mapping |
| `docs/08-conformance-and-errors.md` | Canonical error taxonomy, test-harness protocol |
| `docs/09-divergence-ledger.md` | Permitted vs forbidden implementation variation |
| `docs/10-governance-and-versioning.md` | Spec-first workflow, SemVer, discrepancy protocol |
| `grammars/oml.abnf` | OML grammar, machine-readable |
| `grammars/osd.abnf` | OSD grammar, machine-readable |
| `test-suite/` | Conformance test vectors (JSON) |

Read `docs/index.md` first, then the chapters in order. Chapters 2 and 3 are
prerequisites for everything after them.

## Status

Version 0.1. The document set is complete in outline and normative in the areas
it covers. Chapter 8's error taxonomy is new material: it does not yet describe
any implementation. Chapter 9 records which parts of the spec each
implementation currently satisfies.

## License

Apache-2.0. See `LICENSE`.
