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

§2.4's fourth limit, the alias expansion factor (D-18), is scoped rather than
universal: it binds an implementation's codec for any format that has an
anchor/reference mechanism, which today means YAML and nothing else. Where it
applies it is as non-negotiable as the other three — a finite documented
maximum, and `document.limit.alias-expansion` when it is crossed. Where no
such mechanism exists there is nothing to enforce, and an implementation
shipping no YAML codec is not diverging by not enforcing it.

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
merged PR, real CI run, and (for this round) each port's actual recorded
submodule gitlink and committed test assertions — not carried forward
from a prior edit, and not taken from self-reported summary numbers alone
(see the Java note below for why that distinction mattered this round).
All five ports have bumped their `omnist-spec` submodule pin to
**v0.9.1-beta** (`47a84d6`) and confirmed the new
[§3.3](03-schema-model.md#33-formal-definition) S-8 (`Name` domain) and
S-3 (case-sensitive reserved-name matching) rules were already
pre-existing behavior everywhere (no code change needed anywhere, per
source-level verification done alongside this bump — every port's
reserved-name check was already a plain, case-sensitive equality, and
every port's `name` tokenizer already matched the S-8 domain): Python
(`omnist` PR #342, merge `18e5cbd`), TypeScript (`omnist-ts` PR #146,
merge `5249267`), Rust (`omnist-rs` PR #178, merge `2ef92b2`), Go
(`omnist-go` PR #115, merge `04df6f8`), and Java (`omnist-j` PR #109,
merge `62ccbb3`).

This bump also brought in 5 new vectors from v0.8.0-beta/v0.9.0-beta/v0.9.1-beta:
1 new Core-level `osd-grammar` vector (the S-3 characterization case) and
4 new `extensions-osd-oml/*` vectors (exercising the new
`schema.invalid-name` code and related rules from OSD-OML's v1.1 rewrite,
[extensions/osd-oml.md](extensions/osd-oml.md)). **No port implements
OSD-OML yet** — the 4 extension vectors correctly report as *skips*
everywhere, same as the existing 24; the 1 new Core vector passes
everywhere. Each port with an "implement OSD-OML" tracking issue added a
note about the new S-8/`schema.invalid-name` requirement: Go
(`omnist-go#111`), Java (`omnist-j#105`), Rust (`omnist-rs#175`), and
Python and TypeScript filed theirs for the first time this round
(`omnist#341`, `omnist-ts#145`). No port cut a version bump — pure
pin/doc-metadata updates, none altered any port's own library behavior.

**A same-day spec-side bug surfaced and was fixed mid-round**: the new
S-3 vector's own JSON content had an unquoted field label (a shell-quoting
artifact from vector generation, not a spec-content error), which made it
fail to parse before ever exercising the check it existed to test. Caught
by Python's port session during its pin-bump verification — exactly the
kind of thing this cross-port verification step exists to catch. Fixed in
[omnist-spec#60](https://github.com/omnist-dev/omnist-spec/pull/60)
(v0.9.1-beta); every port from Python onward verified against the
corrected vector, not the original v0.9.0-beta one.

**A self-reported number needed correcting**: Java's PR #109 description
stated "205 pass / 0 fail / 28 skip," which doesn't sum to the expected
204 total. The actual committed `ConformanceTest.java` assertions are
correct (`176`/`0`/`28`, matching every other port's math) — the PR body's
figure had accidentally summed in Track 1's 29 fixture-passes without
also adding Track 1's skip count. Not a real defect, just confirms why
this table cites committed test assertions over summary prose when they
diverge.

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.9.5 | 0.3.0-alpha | 0.2.2-alpha | 0.3.1-alpha | 0.2.3-alpha |
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
| Conformance (vectors — Python now on v0.17.0-beta pin post-D-15 sweep, of 225; TypeScript/Rust/Go/Java still on v0.9.1-beta pin, of 204, pending the same sweep) | 145 pass / 0 fail / 80 skip | 128 pass / 0 fail / 76 skip | 170 pass / 0 fail / 34 skip | 175 pass / 0 fail / 29 skip | 176 pass / 0 fail / 28 skip |
| Conformance (fixtures) | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 (Java's own harness headline count is 29, but 10 of those are `_referee-self-test/*` fixtures — tests of the harness's own equality logic, not this port's behavior — that Java's `Track1Runner` already special-cases but still folds into the same headline number; the other four ports exclude these from their public count. Root cause confirmed, tracked in `omnist-j#110`, not urgent) |
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

**Entries are numbered `DIV-1`, `DIV-2`, …** — deliberately *not* `D-N`,
which is chapter 2's Document-model rule namespace
([§2.3](02-document-model.md#23-structural-invariants)'s `D-1`..`D-5`). The
two were previously indistinguishable, so a bare `D-3` could mean either an
edge-ordering invariant or a retired XML divergence, and both readings
appeared in the same chapter.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

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
