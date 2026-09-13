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

**Last source-audited: 2026-09-13**, directly against each port's own
merged PR and real CI run — not carried forward from a prior edit. All
five ports have bumped their `omnist-spec` submodule pin to **v0.7.0-beta**
(`c4141d0`) and confirmed the 3 new [§3.3](03-schema-model.md#33-formal-definition)
canonical-serialization-order vectors pass green-on-arrival (no behavior
change needed anywhere — every port's `prune`/`normalize` already complied,
per the source-level verification done alongside this bump): Python
(`omnist` PR #337, merge `7d26a48`), TypeScript (`omnist-ts` PR #142, merge
`8f4bc99`), Rust (`omnist-rs` PR #174, merge `a850fb3`), Go (`omnist-go` PR
#112, merge `1f09394`), and Java (`omnist-j` PR #104, merge `85b7be4`).

This bump also brought in the 24 `extensions-osd-oml/*` vectors from
v0.6.0-beta for the first time. **No port implements OSD-OML yet** (see
[§9.6](#96-extension-support)) — all 24 are correctly reported as *skips*,
not failures, per every port's own existing unknown-operation dispatch
(no harness code needed changing to get this right, except Go, which added
an explicit skip path citing the tracking issue). Each port filed its own
"implement OSD-OML" tracking issue as unscheduled future work: Go
(`omnist-go#111`), Java (`omnist-j#105`), Rust (`omnist-rs#175`); Python
and TypeScript MAY still file theirs. No port cut a version bump for this round — every
change was either a pure pin/doc-metadata update (Python, TypeScript,
Rust) or a test/tooling-only fix (Go's skip-dispatch code, Java's
conformance-count assertion), and none altered any port's own
library behavior, so none crossed this project's own
minor=features/patch=fixes-tooling threshold.

Two ports found and fixed a real, independent bug during this same round,
unrelated to the pin bump itself but caught in the course of it: Java's
`SchemaAlgebra.java` and TypeScript's `ops/minimize.ts` both relied on
their host language's default string comparison (UTF-16 code unit) for
`normalize`'s alphabetical fallback, disagreeing with codepoint order for
names containing supplementary-plane characters — closing
[omnist-spec#54](https://github.com/omnist-dev/omnist-spec/issues/54)'s
sibling finding. Fixed in `omnist-j` PR #103 and `omnist-ts` PR #137,
both merged, both with a live test case at the exact U+FFFF/U+10000
boundary. Python, Rust, and Go were unaffected (codepoint-based or
UTF-8-byte-order string comparison, both already codepoint-safe).

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
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| Conformance (vectors, of 199 — all five ports now on the same v0.7.0-beta pin) | 127 pass / 0 fail / 72 skip | 127 pass / 0 fail / 72 skip | 169 pass / 0 fail / 30 skip | 174 pass / 0 fail / 25 skip | 175 pass / 0 fail / 24 skip |
| Conformance (fixtures, of 19) | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100%, gated | 100%, gated | 100%, gated | 100%, gated | 100%, gated |

**Skip counts above are not directly comparable across ports** — 24 of
each port's skips are the shared `extensions-osd-oml/*` vectors (no port
implements OSD-OML), but the remainder differs for pre-existing,
independently-tracked reasons: Rust's 6 extra skips and Go's 1 extra skip
predate this round (see each port's own conformance docs for the specific
gaps) and are unrelated to this bump.

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

## 9.6 Extension support

Extension support is tracked separately from Core status (§9.3), since an
implementation is fully conformant with zero extensions — this table
records adoption, not conformance gaps.

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| OSD-OML | not yet implemented | not yet implemented | not yet implemented | not yet implemented | not yet implemented |

A new extension gets a new row here once its spec chapter merges; a port's
cell updates once it actually implements and passes that extension's
conformance vectors — same "verified against real state, not carried
forward" discipline as §9.3.
