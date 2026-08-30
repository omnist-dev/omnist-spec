# 9. Divergence ledger

Five implementations exist. They will not be identical. This chapter draws the
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
silently changes compatibility answers. The one narrow, explicitly documented
exception is [§2.3](02-document-model.md#23-structural-invariants)'s
scalar-kind-identity invariant: an implementation whose target language
genuinely cannot represent a specific kind distinction independent of a
schema MAY skip **only the specific vectors whose outcome actually depends
on that distinction**, provided it documents the gap as a ledger entry in
[§9.4](#94-known-open-divergences) and its harness cites that entry per
§8.5.5. Every other Document-model vector MUST still pass in full — a
limited, precisely-scoped, thoroughly tested and clearly reported divergence
is what this exception permits, not a blanket exemption for the surrounding
area. **This exception covers a missing distinction being skipped, never an
incorrect output being produced.**

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

*This table is a summary, current as of the date below. It is not the source
of truth — each implementation's own conformance harness run is. Numbers are
kept terse deliberately: this table records **what**, not **how it got that
way** — the reasoning, history, and audit trail for any cell live in that
port's own issue tracker and commit history, not here.*

**Last source-audited: 2026-08-30**, directly against each port's own code,
merged PR history, and (Rust) a live local conformance run — not carried
forward from a prior edit. All five ports have now closed the full 9-issue
spec-correctness audit batch filed 2026-08-29/30 (`omnist#322-330`,
`omnist-ts#125-133`, `omnist-rs#158-166`, `omnist-go#95-103`,
`omnist-j#87-95`): `[0,0]`-cardinality rejection, empty/bracket-label
rejection, OML leading-zero rejection, DATE/TIME/DATETIME/tz-offset range
validation, write-side unconditional failures for unrepresentable values,
and XML carriage-return escaping. Python (`omnist` PRs #331-334, now 0.9.4),
TypeScript (`omnist-ts` PR #134, one combined PR, now 0.3.0-alpha), Rust
(`omnist-rs` PRs #167-170, now 0.2.2-alpha), Go (`omnist-go` PRs #104-109,
now 0.3.0-alpha), and Java (`omnist-j` PRs #96-100, now 0.2.2-alpha) all
verified independently, each against its own conformance harness.

While implementing this batch, the Rust port found and reported a genuine
omnist-spec test-suite defect (`omnist-spec#51` — an un-canonicalized
temporal-scalar value in one happy-path vector, invisible to a
native-temporal-type harness but a real literal-string mismatch for a
string-backed one); fixed in commit `830590b`. Verified locally that Rust's
conformance count moves from 165/1/6 to **166/0/6** once its submodule pin
picks up that commit — Rust's own PR to bump past `0ac1eac` is still
pending, so the table below records both the currently-merged count and the
verified-pending one.

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.9.4 | 0.3.0-alpha | 0.2.2-alpha | 0.3.0-alpha | 0.2.2-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete | complete | complete | complete | complete |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| Conformance (vectors, of 155; Rust/TS/Go of 172, Java of 201 — ahead on the vendored omnist-spec pin) | reference | 124 pass / 0 fail / 48 skip | 165 pass / 1 fail / 6 skip on the merged `0ac1eac` pin (the 1 fail was `omnist-spec#51`, now fixed in `830590b`; verified locally at **166 pass / 0 fail / 6 skip** once Rust's own submodule-bump PR lands) | 170 pass / 0 fail / 2 skip | 201 pass / 0 fail / 0 skip |
| Conformance (fixtures, of 19) | reference | 19/19 | 19/19 | 19/19 | 19/19 |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100%, gated | 100%, gated | 100%, gated | 100%, gated | 99.6%/99.3%, gated |

## 9.4 Known open divergences

Only genuinely unresolved items belong here. A closed item is removed
entirely once fixed — its resolution lives in the fixing repo's own issue,
not as a growing paragraph in this file.

None currently open.

## 9.5 Adding a sixth implementation

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
