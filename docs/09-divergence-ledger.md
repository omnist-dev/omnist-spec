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

As of spec v0.2.0-alpha.

| | Python | TypeScript | Rust | Go |
|---|---|---|---|---|
| Version | 0.7.12 | 0.0.4-alpha | 0.0.1-alpha | 0.0.x-alpha |
| Maturity | beta, reference | alpha | alpha | alpha, built spec-first with no reference-implementation access (§9.5) |
| Document model | complete | complete except `integer`/`number` kind distinction independent of a schema (§9.4 D-6) | complete | complete, all seven scalar kinds natively distinguished (`math/big.Int` for `integer`, per spec §2.4's digit-count requirement) |
| Resource caps | all three | depth + int-digits; **no node-count limit** (§9.4 D-1) | depth + int-digits; **no general node-count limit** (§9.4 D-1) | unverified in this table — not yet audited by source inspection the way Python/TS/Rust were |
| OML read | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended | complete, Core + Extended (self-reported; not yet independently audited) |
| OML canonical write | complete | partial | complete | complete (self-reported) |
| OSD read/write | complete | complete | complete | complete (self-reported) |
| `any` type | yes, v0.5.0 | yes | yes | yes (self-reported) |
| `validate` | complete | complete | complete | pending a fix confirmed needed by this audit — `conformScalar` is missing the `integer <: number` value-level subtype exception (§3.6.1's `matches_kind`, formally defined in commit `40ef979`); tracked in `omnist-go`'s own issue tracker following `omnist-spec#41`'s resolution |
| `materialize` | complete | complete | complete | complete (self-reported) |
| `compatible_with` / `equivalent` | complete | complete | complete | complete (self-reported) |
| `prune` / `is_empty` | complete | complete | complete | complete (self-reported) |
| `normalize` | complete | complete | complete | complete (self-reported) |
| `extract` | complete | complete | complete | complete (self-reported) |
| `infer` | complete | complete | complete | complete (self-reported) |
| `lint` | complete | complete | complete | complete (self-reported) |
| Codecs JSON/YAML/TOML/XML | all four | all four | all four | all four (self-reported) |
| §8.3 error codes | no — partial kebab-case tags | no — partial kebab-case tags | no — partial kebab-case tags | **yes** — confirmed via `omnist-spec#42`'s investigation that `omnist-go` already emits §8.3's namespaced codes (e.g. `lint.unreachable-record`), ahead of the other three and ahead of D-4 resolving; the conformance harness's Track 1 comparison rule was updated (commit `40ef979`) specifically because this made it the first column not to match D-4's "no implementation yet" premise |

**On the Go column.** `omnist-go` (`omnist-dev/omnist-go`) is the fourth
implementation referenced throughout this spec and built under §9.5's
process — spec-first, no reference-implementation access except as a
narrow tie-breaker on already-filed gaps. A 2026-08-10 re-run against its
already-current pin (`896e14e`) reported 149 pass / 1 fail / 1 skip of 151
vectors on Track 2, and 18 pass / 1 fail of 19 on Track 1. Both remaining
fails were independently re-investigated rather than accepted at face value:
- The Track 2 fail (`validate/scalar-kinds/integer-satisfies-number-typed-field`)
  was reported as a vector defect (`omnist-spec#41`); verification against
  the reference implementation showed the vector was correct and the gap was
  `matches_kind` never being formally defined in §3.6.1 (fixed, commit
  `40ef979`) — this is now a confirmed real `omnist-go` gap (missing the
  `integer <: number` value-level exception in `conformScalar`), reflected
  in the `validate` row above.
- The Track 1 fail (`lint/edge-case-unreachable-record`) was reported as a
  fixture defect (`omnist-spec#42`); verification against the reference
  implementation showed the fixture was correct (Python genuinely emits the
  bare, pre-namespacing code) and the gap was the harness's Track 1
  comparison rule never extending §8.5.2 rule 4's code-agnostic comparison
  the way Track 2 already does (fixed, commit `40ef979`) — `omnist-go` was
  actually right to emit the namespaced code, reflected in the §8.3 error
  codes row above.

Every other "complete" cell in this column is still self-reported from that
repo's own docs, not yet independently source-audited the way the
Python/TypeScript/Rust columns were (see the note below on those columns'
own history of being found stale on exactly this kind of unaudited claim) —
treat the rest of this column as provisional until a full source audit
confirms it.

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
| D-3 | XML attributes and namespace prefixes are dropped silently, with no adjustment reported — and confirmed the same is true of cross-label interleaving lost on write (`format.interleaving-lost`), not just the two XML-specific codes this entry previously named. [§8.3.8](08-conformance-and-errors.md#838-format--codec-adjustments) defines codes for reporting all three. Why this matters in practice, concretely rather than abstractly: [`docs/formats/yaml.md`](formats/yaml.md)'s "Norway problem" is the closest real-world case in the ecosystem of a codec doing something a document author never expected — an unquoted `on:` key silently becoming the boolean `true` under YAML 1.1. That case is *caught*, loudly, as a `DocumentError`, because a boolean key can't become a Document label at all. D-3's cases are the same class of surprise with no error at all — the information is simply gone, and a caller has no way to learn it happened short of reading the source text themselves. | Open. Reporting is a behavior change; vector first. |
| D-4 | No implementation emits §8.3 codes. Python, TypeScript, and Rust all share undocumented kebab-case validation tags. | Open by design. See [§8.1](08-conformance-and-errors.md#81-status-of-this-chapter) for the migration path. |
| D-5 | OML-Extended read support (raw and multiline strings): **confirmed complete in both TypeScript and Rust** — implemented and tested in each (TypeScript: `test/oml.test.ts`'s raw-string and multiline-string suites; Rust: `oml/tests.rs`, 988 lines). This entry previously claimed it was Python-only, which was stale for both. | Closed. All three implementations read OML-Extended; only the canonical-writer restriction (write Core only) remains correctly one-sided, and that's already described elsewhere in the spec. |
| D-6 | TypeScript's Document model cannot represent [§2.3](02-document-model.md#23-structural-invariants) D-5's `integer`/`number` distinction independent of a schema — JS has one numeric type, so `Node`'s scalar union carries no kind tag for numbers, and `valueKind`/`matchesKind` derive `"integer"` vs `"number"` from `Number.isInteger(v)` (shape, not source kind). Confirmed and already documented in `omnist-ts`'s own `docs/python-parity.md` #1 (issue #3 there): `matchesKind(1.0, "integer")` is `true` in TypeScript, `false` in Python. This is a deliberate, target-language-driven design choice there, not drift — but it means any conformance vector whose `document` input depends on this distinction (e.g. `test-suite/validate/scalar-kinds/number-does-not-satisfy-integer-even-when-whole`) cannot be faithfully constructed in TypeScript's model and MUST be reported `skip`, never `fail` or a forced `pass`, by its conformance runner. Rust is unaffected (native `i64`/`f64` distinction). | Open by design, TypeScript-only. Tracked alongside `omnist-ts` issue #85 (building that repo's conformance runners), which specifies this skip requirement explicitly rather than leaving it to be discovered vector-by-vector. |
| D-7 | Rust's `document::Scalar` (`omnist/src/document.rs`) has no `Date`/`Time`/`DateTime` variant at all — five variants only (`Null`/`Bool`/`Int`/`Float`/`Str`), an already-closed architecture decision (`omnist-rs` issue #16). This has two confirmed consequences, one accepted and one not: (1) **Accepted, cited.** `format.temporal-stringified` is structurally unreachable on write — a temporal-kind input leaf is already indistinguishable from a plain string by the time the writer sees it, so no adjustment can be reported. `test-suite/formats-json/basic/temporal-leaf-is-stringified-on-write` is correctly reported `skip` citing `omnist-rs` issue #16 (`omnist-rs` issue #89 did the reclassification, matching this ledger's own §8.5.5 discipline). (2) **Was a real bug, now fixed.** `oml/writer.rs`'s `write_str_scalar` used to shape-guess date/time/datetime from string *content* (`is_iso_date`/`is_iso_time`/`is_iso_datetime`) to decide whether to quote a `Scalar::Str`, with no provenance signal to consult instead — confirmed live at the time that a plain JSON string `"2024-01-01"` (never temporal, no schema involved) was written to OML unquoted, silently promoting it to a genuine temporal literal on the next OML read, while Python and TypeScript both got this right. `omnist-rs` issue #99 settled the fix between two named options empirically, using `test-suite/formats-oml/oml.json`'s vectors (added in `omnist-spec` v0.1.1-alpha per issue #33): a `kind: "string"` input and a `kind: "date"` input holding the *identical* value string require opposite output, which rules out "always quote" as structurally unable to pass both for real. Fixed by adding a `RawNode::TemporalLeaf(Scalar)` write-hint variant (not touching `Scalar` itself, `#16` stays closed), fed by OML's own bare-literal grammar and by schema-directed `materialize` upgrades, with a manual `PartialEq` confirmed not to leak into document equality anywhere else. All 6 new vectors now pass for real, not as a skip (117/0/22 of 139 -> 124/0/22 of 146). | (1) Closed by design. (2) Closed — fixed in `omnist-rs` issue #99 (PR #100), independently reviewed, verified live (146-vector run, full `cargo test`, CI's `conformance` job green). |
| D-8 | TypeScript's OML writer (`src/oml.ts`, `writeScalar`/`isTimeLiteral`) shape-guesses `time` from string content, the same bug class as D-7(2) but narrower in scope — unlike D-7, this is not a consequence of a missing `Scalar` variant: TypeScript's `date`/`datetime` are already correctly provenance-tracked (collapsed onto the native `Date` object plus `src/temporal.ts`'s `WeakMap`-based kind tag, per `docs/python-parity.md` #2), and that mechanism works. `time` has no native JS type to collapse onto, so a `time`-kinded value is always a plain string with no tag — confirmed by source inspection that `materialize`'s own `time`-upgrade path (`src/deserialize.ts` line 231) returns the value completely untagged, identical to an ordinary string. `isTimeLiteral`'s shape-guess is therefore not a shortcut alongside real tracking; it is the *only* mechanism this repo has for `time` today, a real gap rather than an accepted structural limit. Confirmed live: a plain string `"12:00:00"` (never time-kinded, no schema involved) writes to OML unquoted, silently promoting it to a genuine temporal literal on the next read — Python and Rust both get this right. `test-suite/formats-oml/basic/time-shaped-string-stays-quoted-on-write` fails outright (not a cited skip) until this is fixed. | Open, TypeScript-only. Tracked as `omnist-ts` issue #96, which lays out the same two-option fork D-7(2) faced (provenance tracking, needing new infrastructure since a bare JS string has no identity to tag; or dropping the bare-literal round-trip for `time` specifically) without prescribing which. |

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
