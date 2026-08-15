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
silently changes compatibility answers. The one narrow, explicitly documented
exception is [§2.3](02-document-model.md#23-structural-invariants) D-5's
scalar-kind-identity invariant: an implementation whose target language
genuinely cannot represent a specific kind distinction independent of a
schema MAY skip **only the specific vectors whose outcome actually depends
on that distinction**, provided it documents the gap as a ledger entry here
([§9.4](#94-known-open-divergences) D-6 and D-7(1) are the current instances
— TypeScript's `integer`/`number` collapse and Rust's missing temporal
`Scalar` variant, respectively) and its harness cites that entry per §8.5.5.
Every other Document-model vector — which is most of them in both cases,
since each collapse is narrow — MUST still pass in full; a limited,
precisely-scoped, thoroughly tested and clearly reported divergence is what
this exception permits, not a blanket exemption for the surrounding area.
**This exception covers a missing distinction being skipped, never an
incorrect output being produced** — D-7(2) (Rust's OML writer silently
mis-quoting a plain string because it shape-guesses a missing kind signal)
is the latter, remains a forbidden-variation bug under "Canonical output"
below, and gets no exception here. This is a structural accommodation for a
specific, named invariant, not a general license to
reinterpret "MUST NOT differ."

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

As of spec v0.2.2-alpha.

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.7.12 | 0.0.4-alpha | 0.0.1-alpha | 0.1.0-alpha | 0.0.1-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha, built spec-first by an external agent guided step-by-step (§9.5) |
| Document model | complete | complete except `integer`/`number` kind distinction independent of a schema (§9.4 D-6) | complete | complete, all seven scalar kinds natively distinguished (`math/big.Int` for `integer`) | complete, all seven scalar kinds natively distinguished (`BigInteger` for `integer`), source-audited |
| Resource caps | all three | depth + int-digits; **no node-count limit** (§9.4 D-1) | depth + int-digits; **no general node-count limit** (§9.4 D-1) | all three, source-audited | all three, source-audited |
| OML read | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended, source-audited |
| OML canonical write | complete | partial | complete | complete | complete, source-audited |
| OSD read/write | complete | complete | complete | complete | complete, source-audited |
| `any` type | yes, v0.5.0 | yes | yes | yes | yes, source-audited |
| `validate` | complete | complete | complete | complete | complete, source-audited |
| `materialize` | complete | complete | complete | complete | complete, source-audited |
| `compatible_with` / `equivalent` | complete | complete | complete | complete | complete, source-audited |
| `prune` / `is_empty` | complete | complete | complete | complete | complete, source-audited |
| `normalize` | complete | complete | complete | complete | complete, source-audited — surfaced a real spec gap (`local_signature`, §9.4 below) |
| `extract` | complete | complete | complete | complete | complete, source-audited |
| `infer` | complete | complete | complete | complete | complete, source-audited |
| `lint` | complete | complete | complete | complete | complete, source-audited |
| Codecs JSON/YAML/TOML/XML | all four | all four | all four | all four | all four, source-audited |
| §8.3 error codes | no — partial kebab-case tags | no — partial kebab-case tags | no — partial kebab-case tags | yes | yes — also found the `format.*` gap in §8.3.8 |
| Conformance | reference | — | — | 151/151 real vectors (0 real fails) | **181/181, zero real fails, zero skips** |
| Fuzz testing | yes | — | yes, found real bugs | yes, found real bugs | yes, found a real infinite-loop bug (`TomlCodec`) |
| Test coverage | — | — | 100%, gated | — | **99.65% line / 97.87% branch, gated** |

**On the Go column.** `omnist-go` is the fourth implementation, built
spec-first under §9.5 with no reference-implementation access except as
a narrow, already-filed-gap tie-breaker. As of PR #61 (main `0a03f30`,
2026-08-10), both conformance tracks report zero real fails — Track 2
150/151 (1 known TOML strict-mode skip, out of scope), Track 1 19/19 —
source-audited against the real `algebra/*.go`, `formats/*/`, `oml/`,
and `osd/` implementations rather than accepted from the repo's own
docs. Getting a clean report took two rounds of independent
verification: both of `omnist-go`'s initial gap diagnoses
(`omnist-spec#41`, `#42`) were reported backwards — #41 was a genuine
`omnist-go` bug misdiagnosed as a vector defect (missing `integer <:
number` exception in `conformScalar`), #42 was a harness comparison-rule
gap misdiagnosed as a fixture defect — both fixed in PR #61 and this
spec's commit `40ef979`.

**On the Java column.** `omnist-j` is the fifth implementation, built
spec-first under §9.5 through an external coding agent guided
step-by-step rather than working autonomously — every "done" report was
independently re-verified (fresh build, fresh conformance run, source
read) before being accepted, catching an unpushed-commit gap and
self-reported numbers that didn't match reality along the way. As of
`v0.0.1-alpha` (main `b3efb33`, 2026-08-15), conformance is 181/181
(both tracks, independently reproduced) and test coverage is a gated
99.65% line / 97.87% branch, up from an ungated 60.0%/53.0% after a
source-audited gap-closing pass — every remaining uncovered line is a
documented, empirically-verified trip-wire, including one JaCoCo report
that looked like a real gap (`SchemaAlgebra`'s bare `continue`
statements) but was confirmed via a standalone reproduction to be a
bytecode-mapping artifact, not an untested branch. Building this port
surfaced one genuine spec gap — `local_signature`, used in §6.8's
`normalize` pseudocode but never formally defined — fixed on this spec
(commits `f6ec180`, `ebe10e2`) before the port proceeded.

**On the TypeScript and Rust columns.** Two consecutive audits found
this table substantially understated both alpha implementations.
TypeScript's `OML read`, `materialize`, `compatible_with`/`equivalent`,
`prune`/`is_empty`, `normalize`, `extract`, `infer`, `lint`, and codec
coverage were confirmed present and under test, not merely claimed —
the same was then found true of nearly all of Rust's column. Both
error-code rows were also wrong the same way: `omnist-ts` and
`omnist-rs` both render the identical kebab-case strings Python already
uses. Per this chapter's own authority rule (§9.3 — this table is a
summary, not the source of truth; the harness's skip counts are), these
cells are provisionally corrected pending a full harness run per port.
Given this table has now been found stale twice in a row for these two
columns, treat every cell here with the same skepticism until it's been
source-audited directly rather than edited around the existing claims.

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
| D-1 | Resource caps: was a real, security-relevant gap — an unbounded node count is a memory-exhaustion DoS (a depth-1 document with one label repeated arbitrarily many times slides under any depth limit with nothing else to stop it). This was never a legitimate language-limitation exemption under §9.2's forbidden-variation rule ("all three [caps] MUST be enforced... MUST NOT be unbounded on any"): a node counter needs no type-system feature either language lacks, unlike D-6/D-7(1)'s genuinely structural scalar-kind gaps. | Closed — both fixed weeks before this entry was corrected: `omnist-ts` issue #77 (PR #81, merged `a6e08aa`, 2026-07-28) added a shared `MAX_NODES` counter threaded through every construction path; `omnist-rs` issue #78 (merged the same day) added `document::MAX_NODES = 1_000_000` enforced in the shared arena builder, unifying with YAML's prior narrower anchor/alias guard. This ledger entry itself sat stale claiming "Open" for two weeks after both were actually fixed — caught only when a user asked directly whether the divergence was a legitimate language limitation; verified live against both implementations' real source before closing (a 1,000,001-edge single-label document is rejected by each with the correct `document.limit.nodes`-family error). Lesson: a ledger status needs periodic re-verification independent of whatever specific issue prompted the last edit, not just updates triggered by unrelated audits. |
| D-2 | A duplicate `root` declaration in OSD: Python lets the later one silently win. The spec ([§5.8](05-osd-grammar.md#58-root)) declines to bless this. | Open. Proposed resolution: make it `schema.duplicate-root`, an error. Needs a vector first. |
| D-3 | XML attributes and namespace prefixes are dropped silently, with no adjustment reported — and confirmed the same is true of cross-label interleaving lost on write (`format.interleaving-lost`), not just the two XML-specific codes this entry previously named. [§8.3.8](08-conformance-and-errors.md#838-format--codec-adjustments) defines codes for reporting all three. Why this matters in practice, concretely rather than abstractly: [`docs/formats/yaml.md`](formats/yaml.md)'s "Norway problem" is the closest real-world case in the ecosystem of a codec doing something a document author never expected — an unquoted `on:` key silently becoming the boolean `true` under YAML 1.1. That case is *caught*, loudly, as a `DocumentError`, because a boolean key can't become a Document label at all. D-3's cases are the same class of surprise with no error at all — the information is simply gone, and a caller has no way to learn it happened short of reading the source text themselves. | Open. Reporting is a behavior change; vector first. |
| D-4 | No implementation emits §8.3 codes. Python, TypeScript, and Rust all share undocumented kebab-case validation tags. | Open by design. See [§8.1](08-conformance-and-errors.md#81-status-of-this-chapter) for the migration path. |
| D-5 | OML-Extended read support (raw and multiline strings): **confirmed complete in both TypeScript and Rust** — implemented and tested in each (TypeScript: `test/oml.test.ts`'s raw-string and multiline-string suites; Rust: `oml/tests.rs`, 988 lines). This entry previously claimed it was Python-only, which was stale for both. | Closed. All three implementations read OML-Extended; only the canonical-writer restriction (write Core only) remains correctly one-sided, and that's already described elsewhere in the spec. |
| D-6 | TypeScript's Document model could not represent [§2.3](02-document-model.md#23-structural-invariants) D-5's `integer`/`number` distinction independent of a schema — JS's single numeric type meant `Node`'s scalar union carried no kind tag, and `valueKind`/`matchesKind` derived `"integer"` vs `"number"` from `Number.isInteger(v)` (shape, not source kind). This turned out not to be a genuine language limitation once `omnist-ts#98`/D-9 forced the real fix: `integer`-kinded values are now backed by native `bigint` (`number`-kinded values stay `number`), which gives `typeof v === "bigint"` vs `"number"` as a real, native kind tag — no shape-guessing needed. | Closed — fixed in `omnist-ts` PR #99 (merged `528bad4`, 2026-08-10) as a direct consequence of fixing D-9, independently verified: `matchesKind`/`valueKind` diff-confirmed to use `typeof` exclusively, and the vector this used to require skipping (`validate/scalar-kinds/number-does-not-satisfy-integer-even-when-whole`) now runs for real and passes rather than being cited `skip`. Conformance tally: 110/0/36 of 146 (pre-fix pin) -> 116/0/36 of 152 (post-fix pin) — the one real pass beyond the six new vectors from the pin bump is exactly this vector converting from skip to pass. |
| D-7 | **Closed in full, 2026-08-10.** Rust's `document::Scalar` used to have no `Date`/`Time`/`DateTime` variant — five variants only (`Null`/`Bool`/`Int`/`Float`/`Str`) — cited as an "architecture decision" that a 2026-08-10 re-scrutiny found didn't actually hold up (the cited issue #16 never discussed `Scalar`'s shape; nothing structurally prevented adding the variants). Asked `omnist-rs` to reconsider; they did, filed a real design plan first (`omnist-rs#105`), checked every real consumer before committing to a representation (no `chrono` dependency needed — `Date(String)`/`Time(String)`/`Datetime(String)`, always shape-validated and canonicalized on construction), and implemented it in PR #107 (merged, `v0.1.3-alpha`). (1) was the accepted-as-structural gap (`format.temporal-stringified` unreachable on write) — no longer applicable, since `Scalar` now carries the distinction. (2) was the real, separately-fixed bug (`oml/writer.rs` shape-guessing), whose `RawNode::TemporalLeaf` write-hint workaround is now *removed entirely*, not just superseded — the real variants make it redundant, confirmed in the diff. TOML's `toml_edit::Value::Datetime` is now read as its own fully-typed value instead of being collapsed to a string (a genuine correctness improvement, not just parity); YAML's resolver constructs real variants for unquoted plain scalars the same way OML's scanner does. `infer` gains real Date/Time/Datetime inference as a disclosed side effect. 100% coverage maintained, verified against live Python source before merge, `schema::matches_kind`'s hybrid (real-variant-or-shape-match) approach specifically checked against Python's actual `schema.py` after an initial strict-only attempt was caught wrong by the parity corpus. | Closed. Confirmed live: `formats-json/basic/temporal-leaf-is-stringified-on-write` now `[PASS]`, not the prior cited `[SKIP]` — Rust's conformance tally moved from 129/0/23 to 130/0/22 of 152. |
| D-8 | TypeScript's OML writer (`src/oml.ts`, `writeScalar`/`isTimeLiteral`) shape-guessed `time` from string content, the same bug class as D-7(2) but narrower in scope — unlike D-7, this was not a consequence of a missing `Scalar` variant: TypeScript's `date`/`datetime` were already correctly provenance-tracked (collapsed onto the native `Date` object plus `src/temporal.ts`'s `WeakMap`-based kind tag, per `docs/python-parity.md` #2), and that mechanism works. `time` had no native JS type to collapse onto, so a `time`-kinded value was always a plain string with no tag — confirmed by source inspection that `materialize`'s own `time`-upgrade path (`src/deserialize.ts` line 231) returned the value completely untagged, identical to an ordinary string. `isTimeLiteral`'s shape-guess was therefore not a shortcut alongside real tracking; it was the *only* mechanism this repo had for `time`, a real gap rather than an accepted structural limit. Confirmed live at the time: a plain string `"12:00:00"` (never time-kinded, no schema involved) wrote to OML unquoted, silently promoting it to a genuine temporal literal on the next read — Python and Rust both got this right. `test-suite/formats-oml/basic/time-shaped-string-stays-quoted-on-write` failed outright (not a cited skip) until fixed. | Closed — fixed in `omnist-ts` issue #96 (PR #97, merged `015ac5b`), independently reviewed by this ledger's maintainer (not just accepted from the report): took the same provenance-tracking fork D-7(2) chose, adding a `TimeValue` wrapper class (`src/temporal.ts`) giving `time` real object identity the way `Date` already gives `date`/`datetime`, constructed only at the two genuine construction points (`readOml`'s `TIME`-token grammar, `materialize`'s schema-directed upgrade); `isTimeLiteral`'s shape-guess removed entirely, not bypassed. Diff-reviewed: `TimeValue` confirmed transparent everywhere else that matters — `isScalar`/Document equality, `matchesKind`/`valueKind`, and the three other format writers (JSON/YAML/TOML/XML) all unwrap it to plain text via a new `unwrapTimeValues` helper deliberately not called by the OML writer, the one place the tag must stay visible. `omnist-ts`'s conformance tally after the fix: 110/0/36 of 146 vectors (all three target vectors, including `time-shaped-string-stays-quoted-on-write`, now pass for real, not as a skip). |
| D-9 | **§2.2 defines `integer` as arbitrary-precision, not fixed-width — TypeScript and Rust both violate this, in two different and differently bad ways, and neither divergence was previously in this ledger or exercised by any vector.** Found 2026-08-10 auditing this chapter directly at a user's prompt ("are these language limitations or laziness"), not from any conformance run — the existing `document-model/limits.json` vectors only ever test small digit counts (999/1000) against a tiny vector-local `declared_max_int_digits`, never a real integer near the 4,300 reference default with *no* override, so this gap was structurally invisible to the harness until `document-model/limits/integer-beyond-fixed-width-still-parses-under-default-limit` was added (25 digits, default limits, no `declared_max_int_digits`). **Rust**: `document.rs`'s `Scalar::Int(i64)` — confirmed live, a 25-digit OML integer literal is rejected outright: `"integer literal ... is out of range for a 64-bit integer"`. This is a Grammar-acceptance forbidden-variation bug (§9.2): Rust accepts a strict subset of valid OML text, and it is not a genuine language limitation — Rust can do arbitrary-precision arithmetic (the `Go` port does exactly this with `math/big.Int`); the module doc comment at the top of `document.rs` explains this was a deliberate choice made when building the integer-digit *guard*, reasoning "the guard would be permanently-dead code... nowhere near the 4300-digit cap" — which is true of the guard, but was never connected back to the actual requirement that `integer` itself be arbitrary-precision, not that only the guard needs to reach 4,300. **TypeScript**: worse in a different way — no rejection at all. `Node`'s `Scalar` union has no distinct integer representation (already the root of D-6), so a large integer literal parses as a JS `number` (IEEE 754 float64) and silently loses precision: confirmed live, `9999999999999999999999999` (25 nines) round-trips as `1e+25` — a different, wrong value, with no error, no adjustment report, nothing. This is worse than D-6 (a kind-tag distinction that's merely unrepresentable) because a *value* is silently corrupted, which is squarely forbidden under "Algebra results" and "Canonical output" in §9.2, not covered by D-6's narrow exception (which covers a missing distinction being skipped, never a wrong value being produced — the same principle D-7(2) was held to). | **Closed for all four implementations**, both fixed on 2026-08-10, each independently reviewed against the actual diff rather than accepted from the report. **TypeScript**: `omnist-ts` PR #99 (merged `528bad4`) — `integer`-kinded `Scalar`s now back onto native `bigint` across every codec (OML's own grammar, JSON via a tag-and-revive scheme since `JSON.parse` has no native bigint support, YAML/TOML via each parser library's own bigint mode), confirmed exact round-trip of the original 25-nines repro. A genuine DoS regression was caught and fixed *during* this same PR's review before merge: `formats/xml.ts`'s schema-directed integer path switched `Number(value)` to `BigInt(value)` to fix the precision loss, but that path never ran through the shared `MAX_INT_DIGITS` guard the other codecs use — fixed with a digit-count check on the raw text before `BigInt()` ever sees it, verified in the diff. **Rust**: `omnist-rs` PR #106 (merged `cf7c264`) — `Scalar::Int`/`Value::Int` moved onto `num_bigint::BigInt`, matching Python/Go's own arbitrary-precision approach. Also caught a regression during the same fix, independently of TypeScript's: YAML's legacy sexagesimal-literal fold used to rely on `i64` overflow as an incidental size bound on its folded result — a naive `BigInt` swap would have silently removed that bound, letting a many-`:`-group literal build an unbounded integer; fixed by enforcing the digit cap explicitly on the fold's result. One residual, narrower, and legitimately disclosed gap remains in Rust: `toml_edit` (the underlying crate, not this port's own choice) enforces a hard `i64` ceiling when *reading* TOML source text, before this port's `Scalar` conversion ever runs — writing an oversized integer *to* TOML still round-trips out fine, since the writer renders plain digit text rather than going through `toml_edit`'s typed API; only the TOML read path is affected, and it's an external-dependency constraint rather than something this port's own representation can lift. Not itself a new ledger entry — genuinely narrow, disclosed, and outside the pattern D-9 was about (an unexamined choice mislabeled as a limitation). |

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
