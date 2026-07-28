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

**The exact value of a safety limit** (§2.4). An implementation MAY set its
depth, node-count, and integer-digit limits to values other than the reference
defaults (200 / 1,000,000 / 4,300), to fit its deployment target. What is not
permitted to vary is covered in §9.2.

## 9.2 Forbidden variation

An implementation MUST NOT differ on any of the following. Each is a
conformance failure, not a design choice.

**The Document model.** Edge ordering, repeated-label handling, the seven scalar
kinds, the value/node dichotomy. Adding a scalar kind is the single most
damaging possible divergence: it changes the subtyping lattice and therefore
silently changes compatibility answers.

**Whether a safety limit exists, and what it is called.** All three limits in
§2.4 (depth, node count, integer digits) MUST be enforced by every
implementation, at some finite value it documents. An implementation MUST NOT
be unbounded on any of the three, and exceeding whichever value it configures
MUST raise the matching `document.limit.*` code (§8.3.2) — never a different
code, and never silently. The threshold number is permitted variation (§9.1);
having no threshold at all, or reporting the wrong code when one is crossed, is
not.

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
| Resource caps | all three | depth + int-digits; **no node-count limit** (§9.4 D-1) | depth + int-digits; **no general node-count limit** (§9.4 D-1) |
| OML read | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended |
| OML canonical write | complete | partial | complete |
| OSD read/write | complete | complete | complete |
| `any` type | yes, v0.5.0 | yes | yes |
| `validate` | complete | complete | complete |
| `materialize` | complete | complete | complete |
| `compatible_with` / `equivalent` | complete | complete | complete |
| `prune` / `is_empty` | complete | complete | complete |
| `normalize` | complete | complete | complete |
| `extract` | complete | complete | complete |
| `infer` | complete | complete | complete |
| `lint` | complete | complete | complete (one confirmed conformance bug, see [`omnist-rs#77`](https://github.com/omnist-dev/omnist-rs/issues/77) — `duplicate-record` finding shape deviates from §6.11) |
| Codecs JSON/YAML/TOML/XML | all four | all four | all four |
| §8.3 error codes | no — partial kebab-case tags | no — partial kebab-case tags | no — partial kebab-case tags |

**On the TypeScript and Rust columns' upgrade from "partial"/"not yet" to
"complete."** Two consecutive audits found this table substantially
understated both alpha implementations. TypeScript's `OML read`,
`materialize`, `compatible_with`/`equivalent`, `prune`/`is_empty`,
`normalize`, `extract`, `infer`, `lint`, and codec coverage were confirmed
present and under test, not merely claimed. The same was then found true of
Rust, across nearly the entire column — `compatible_with`/`equivalent`,
`prune`/`is_empty`, `normalize`, `extract`, `infer`, `lint`, all four codecs,
`validate`, `materialize`, and OML read/write are all implemented and tested
in `omnist-rs`, not "not yet"/"partial"/"JSON only" as this table previously
claimed. Rust's error-code row was also wrong in the same way as its TS
counterpart: `omnist-rs`'s `ErrorCode` enum renders the identical kebab-case
strings Python and TypeScript already use. Per this chapter's own authority
rule (§9.3, "this table is a summary and MUST NOT be treated as one; the
conformance harness's skip counts are"), all of these cells should be treated
as provisionally corrected pending a full harness run — replace "complete"
with a more specific note if the harness's actual skip counts turn out
nonzero for any of them. Given this table has now been found stale twice in a
row for the two alpha implementations, whoever next revises it should
strongly consider re-verifying every cell directly rather than editing around
the existing claims.

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
| D-1 | Resource caps: Python enforces all three. TypeScript and Rust both enforce depth and integer-digit length correctly (confirmed at the parsing layer, under test in both) but **neither has a general node-count limit** — TypeScript has none at all; Rust has one, but it's scoped narrowly to YAML's own anchor/alias-amplification defense (`formats/yaml.rs`) rather than shared across the Document builder and the other three readers. Confirmed absent by source inspection in both, not merely unverified. | Open. TypeScript needs a general node-count limit (tracked as `omnist-ts` issue #77); Rust needs the same (tracked as `omnist-rs` issue #78, being fixed alongside this correction). |
| D-2 | A duplicate `root` declaration in OSD: Python lets the later one silently win. The spec ([§5.8](05-osd-grammar.md#58-root)) declines to bless this. | Open. Proposed resolution: make it `schema.duplicate-root`, an error. Needs a vector first. |
| D-3 | XML attributes and namespace prefixes are dropped silently, with no adjustment reported. [§8.3.8](08-conformance-and-errors.md#838-format--codec-adjustments) defines codes for reporting them. | Open. Reporting is a behavior change; vector first. |
| D-4 | No implementation emits §8.3 codes. Python, TypeScript, and Rust all share undocumented kebab-case validation tags. | Open by design. See [§8.1](08-conformance-and-errors.md#81-status-of-this-chapter) for the migration path. |
| D-5 | OML-Extended read support (raw and multiline strings): **confirmed complete in both TypeScript and Rust** — implemented and tested in each (TypeScript: `test/oml.test.ts`'s raw-string and multiline-string suites; Rust: `oml/tests.rs`, 988 lines). This entry previously claimed it was Python-only, which was stale for both. | Closed. All three implementations read OML-Extended; only the canonical-writer restriction (write Core only) remains correctly one-sided, and that's already described elsewhere in the spec. |

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
