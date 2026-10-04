# omnist-spec

The language-agnostic specification for **Omnist**: a Document model, a Schema
model, two text formats (OML and OSD), and a Schema Algebra of decidable
operations over schemas.

This repository holds the specification only. It contains no implementation.
Implementations live elsewhere and are expected to conform to what is written
here.

## Why a separate spec

Omnist has five implementations (Python, TypeScript, Rust, Go, Java). Without
a written contract, "what Omnist does" is whatever the oldest implementation
happens to do, and the others drift. The spec exists so that:

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
| `docs/formats/` | Per-format codec chapters (JSON, YAML, TOML, XML, OML) |
| `docs/extensions/` | Extensions to the Core: OSD-OML |
| `docs/conformance-harness.md`, `docs/porting-a-conformance-runner.md` | The Track 1 harness protocol and a guide to building a runner |
| `docs/operations-and-models-reference.md` | Reference tables of operations and models |
| `grammars/oml.abnf` | OML grammar, machine-readable and executable |
| `grammars/osd.abnf` | OSD grammar, machine-readable and executable |
| `test-suite/` | Conformance test vectors (JSON, Track 2) |
| `conformance/` | Track 1 fixtures and the referee self-test |
| `tools/` | CI checks: version sync, rule coverage, vector validity, grammars |
| `mkdocs.yml` | Configuration of the published site (spec.omnist.dev) |
| `CHANGELOG.md` | Per-version change log |

Read `docs/index.md` first, then the chapters in order. Chapters 2 and 3 are
prerequisites for everything after them.

## Status

Beta. The current version is the top entry of `CHANGELOG.md`. The document set
is normative in the areas it covers, and five implementations (Python,
TypeScript, Rust, Go, Java) are built against it. Chapter 9 records which parts
of the spec each implementation currently satisfies, and the per-port
conformance numbers.

## License

Apache-2.0. See `LICENSE`.
