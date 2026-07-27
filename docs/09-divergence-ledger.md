# 9. Divergence ledger

Three implementations exist. They will not be identical. This chapter draws the
line between variation that is fine and variation that is a bug, and records
where each implementation currently stands.

## 9.1 Permitted variation

An implementation MAY differ freely on all of the following. None of it is
observable in a conformance result.

**Language surface.** Method names, module layout, whether operations are free
functions or methods, naming conventions, builder patterns, iterator protocols.
Python's `schema.compatible_with(other)` and Rust's
`compatible_with(&a, &b)` are the same operation.

**Error representation.** Exception classes, `Result` types, error enums, unions
of tagged objects. What matters is that the same inputs fail, at the same paths,
with the same codes once §8.3 is adopted.

**Message text.** Wording, punctuation, capitalization, suggested fixes, and
localization. Conformance never compares messages.

**Performance and internal representation.** Memoization strategy, whether
records are interned, arena versus reference counting, parallelism, laziness.
The observable results must match; the route to them need not.

**Extra operations.** An implementation MAY offer conveniences the spec does not
define — a diff view, a pretty-printer variant, a streaming reader — provided
they cannot produce a Document or Schema the spec forbids.

**Optional surfaces.** A command-line interface, a language-server integration,
a formatter. Nothing in this spec requires them.

## 9.2 Forbidden variation

An implementation MUST NOT differ on any of the following. Each is a
conformance failure, not a design choice.

**The Document model.** Edge ordering, repeated-label handling, the seven scalar
kinds, the value/node dichotomy. Adding a scalar kind is the single most
damaging possible divergence: it changes the subtyping lattice and therefore
silently changes compatibility answers.

**Resource caps.** 200, 1 000 000, 4300. Not configurable above those values,
not tiered, not per-format.

**Validation results.** Which documents a schema accepts, and where a rejection
is located.

**Algebra results.** Every boolean from `compatible_with`, `equivalent`, and
`is_empty`. Every schema from `prune`, `normalize`, and `extract`, compared as
canonical OSD text byte for byte — including record naming, which
`normalize`'s minimum-of-block rule fixes deterministically.

**Grammar acceptance.** Which texts parse and which do not, for both OML and
OSD. Accepting a superset is as much a failure as accepting a subset: it lets
documents circulate that other implementations reject.

**Canonical output.** The exact bytes a canonical OML or OSD writer emits for a
given Document or Schema.

**Determinism.** Any observable ordering — environment key order, canonical
output, `lint` finding order — MUST be a deterministic function of the input
alone. Never of hash seeding, iteration order of an unordered collection,
filesystem order, or wall-clock time.

## 9.3 Current status

As of spec v0.1.

| | Python | TypeScript | Rust |
|---|---|---|---|
| Version | 0.7.12 | 0.0.4-alpha | 0.0.1-alpha |
| Maturity | beta, reference | alpha | alpha |
| Document model | complete | complete | complete |
| Resource caps | all three | see §9.4 | see §9.4 |
| OML read | complete, Core + Extended | partial | partial |
| OML canonical write | complete | partial | partial |
| OSD read/write | complete | complete | complete |
| `any` type | yes, v0.5.0 | yes | yes |
| `validate` | complete | complete | partial |
| `materialize` | complete | partial | partial |
| `compatible_with` / `equivalent` | complete | partial | not yet |
| `prune` / `is_empty` | complete | partial | not yet |
| `normalize` | complete | not yet | not yet |
| `extract` | complete | not yet | not yet |
| `infer` | complete | not yet | not yet |
| `lint` | complete | not yet | not yet |
| Codecs JSON/YAML/TOML/XML | all four | JSON | JSON |
| §8.3 error codes | no — partial kebab-case tags | no — partial kebab-case tags | no — no code field |

**On `any` in Rust.** Rust supports `any`. It is present as `FieldType::Any` in
the OSD parser, is written back out as `any`, and rejects `any?` the same way
Python does. Earlier drafts of this ledger claimed Rust lacked it; that was
wrong and is corrected here.

**On "partial."** Partial means the operation exists and passes some vectors.
The conformance harness's skip counts (§8.5.5) are the authority on exactly
which; this table is a summary and MUST NOT be treated as one.

## 9.4 Known open divergences

These are live discrepancies. Each needs resolution under
[chapter 10](10-governance-and-versioning.md)'s protocol.

| # | Issue | Status |
|---|---|---|
| D-1 | Resource caps are enforced in Python at all three limits. TypeScript and Rust enforce depth but their node-count and integer-digit enforcement is unverified. | Open. Needs vectors at each boundary, then implementation. |
| D-2 | A duplicate `root` declaration in OSD: Python lets the later one silently win. The spec ([§5.8](05-osd-grammar.md#58-root)) declines to bless this. | Open. Proposed resolution: make it `schema.duplicate-root`, an error. Needs a vector first. |
| D-3 | XML attributes and namespace prefixes are dropped silently, with no adjustment reported. [§8.3.8](08-conformance-and-errors.md#838-format--codec-adjustments) defines codes for reporting them. | Open. Reporting is a behavior change; vector first. |
| D-4 | No implementation emits §8.3 codes. Python and TypeScript share undocumented kebab-case validation tags. | Open by design. See [§8.1](08-conformance-and-errors.md#81-status-of-this-chapter) for the migration path. |
| D-5 | OML-Extended read support (raw and multiline strings) is Python-only. | Open. TypeScript and Rust must accept them; only the writer restriction is one-sided. |

## 9.5 Adding a fourth implementation

A new implementation is conformant when it passes the vectors in `test-suite/`
with zero failures. Skips are permitted and MUST be reported; they are how
partial implementations are tracked honestly rather than by claim.

Recommended build order, since the dependencies are real:

1. Document model and resource caps
2. OML reader, then canonical OML writer
3. OSD reader, then canonical OSD writer
4. `validate`
5. `satisfiable_set`, `is_empty`, `prune`
6. `compatible_with`, then `equivalent`
7. `normalize` — needs `prune`
8. `extract` — needs `prune` and `normalize`
9. `lint` — needs `satisfiable_set` and `equivalence_classes`
10. `infer`
11. Codecs beyond OML
12. `materialize`

Steps 1 through 6 are the useful core. An implementation that stops there is
still worth having.
