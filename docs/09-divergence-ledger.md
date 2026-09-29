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

**Whether a safety limit exists, and what it is called.** All three universal
limits in §2.4 (depth, node count, integer digits) MUST be enforced by every
implementation, at some finite value it documents. An implementation MUST NOT
be unbounded on any of them, and exceeding whichever value it configures
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

**Last updated: 2026-09-29**, from each port's own merged and
independently reviewed PR and its own conformance run, not carried forward
from an earlier edit. All five ports have adopted spec **v0.21.0-beta**:
Python ([omnist#349](https://github.com/omnist-dev/omnist/pull/349)),
TypeScript ([omnist-ts#150](https://github.com/omnist-dev/omnist-ts/pull/150)),
Go ([omnist-go#120](https://github.com/omnist-dev/omnist-go/pull/120)),
Rust ([omnist-rs#184](https://github.com/omnist-dev/omnist-rs/pull/184)) and
Java ([omnist-j#114](https://github.com/omnist-dev/omnist-j/pull/114)). Every
port's runner now compares diagnostics as `(path, code)` sets. Python's runner
was code-agnostic until #349; on the same suite it reported 159 pass / 17 fail /
97 skip before that rewrite.

Two Version cells need a caveat. Rust's 0.3.0-alpha was tagged on 2026-09-29 at
the merge commit of the v0.21.0-beta work (`179f3b6`); its `publish.yml` run
was still in progress and crates.io still listed 0.2.2-alpha as the newest
release when this was written, so 0.3.0-alpha is tagged but not yet confirmed
published. Java's 0.2.5-alpha is the latest tag; its Maven Central release run
waits for manual approval, so that version is not necessarily published yet.

Three things are deliberately not claimed as done anywhere: no port enforces
the alias expansion limit D-18 (`DIV-3`), no port implements the OSD-OML
extension (§9.6), and whether `a: 1`, a newline, then `}` is a
`parse.trailing-content` case is an open spec question
([omnist-spec#109](https://github.com/omnist-dev/omnist-spec/issues/109)), not a
divergence.

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.10.0 | 0.4.0-alpha | 0.3.0-alpha | 0.5.0-alpha | 0.2.5-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 is enforced by no port yet — DIV-3) | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| OSD writer: label escaping (OSD-15), unwritable label refused (OSD-14) | both done | both done (OSD-15 fixed in #150) | both done (`to_osd` returns `Result`) | both done (`osd.Write` returns an error) | both done |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| D-14, invalid UTF-8 rejected with `parse.invalid-encoding` at `1:1` (§2.5) | yes, via the CLI | yes, via the CLI | yes, via `omnist-cli` | yes, at the front of all six readers | yes, on stdin |
| Conformance (Track 2 JSON vectors, 273 at v0.21.0-beta, all compared as `(path, code)` sets) | 233 pass / 0 fail / 40 skip | 213 pass / 0 fail / 60 skip | 233 pass / 0 fail / 40 skip | 239 pass / 0 fail / 34 skip | 239 pass / 0 fail / 34 skip |
| Conformance (fixtures) | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 (harness headline 29/0/0: the 10 `_referee-self-test/*` fixtures are folded into it, [omnist-j#110](https://github.com/omnist-dev/omnist-j/issues/110)) |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100%, gated | 100%, gated | 100%, gated | 100%, gated | 100%, gated |

**What each port skips.** Python: 28
OSD-OML ([omnist#341](https://github.com/omnist-dev/omnist/issues/341)), 6
alias-expansion (`DIV-3`), 6 `declared_max_depth` / `declared_max_nodes` /
`declared_max_int_digits` vectors (its limits are module constants). TypeScript:
28 OSD-OML, 6 alias-expansion (`DIV-3`), 6 compile-time limits, and 20
`schema.*` vectors
([omnist-ts#149](https://github.com/omnist-dev/omnist-ts/issues/149):
`SchemaError` has no structured code or path). Rust: 28 OSD-OML
([omnist-rs#175](https://github.com/omnist-dev/omnist-rs/issues/175)), 6
alias-expansion ([omnist-rs#180](https://github.com/omnist-dev/omnist-rs/issues/180),
`DIV-3`), 6 `document-model/limits` (compile-time constants,
[omnist-rs#181](https://github.com/omnist-dev/omnist-rs/issues/181)). Go: 28
OSD-OML ([omnist-go#111](https://github.com/omnist-dev/omnist-go/issues/111)),
6 alias-expansion ([omnist-go#117](https://github.com/omnist-dev/omnist-go/issues/117),
`DIV-3`). Java: 28 OSD-OML ([omnist-j#105](https://github.com/omnist-dev/omnist-j/issues/105)),
6 alias-expansion ([omnist-j#113](https://github.com/omnist-dev/omnist-j/issues/113),
`DIV-3`). Skip counts are therefore not comparable across ports beyond those
shared categories.

**Note on the D-14 row.** D-14 has vectors (E-27's `bytes_hex`) and all five
ports pass them. OSD-14 has none: its "done" cells rest on the unit tests each
port's PR reports (`DIV-5`).

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

**`DIV-1`, `DIV-2`, `DIV-4` and `DIV-6` are retired numbers and MUST NOT be
reused.** All four entries closed and were deleted; the numbers stay spent so a
citation to any of them in an older document, issue, vector comment, or port
changelog cannot silently come to mean something else. `DIV-4` (the rules
v0.19.0-beta and v0.20.0-beta settled) and `DIV-6` (`bytes_hex` and D-14) closed
when the v0.21.0-beta sweep left every port satisfying every row. This note
lives here, in the preamble, rather than inside any single entry — an entry is
deleted when it closes, and a retirement note that rides along inside one
disappears with it.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

**DIV-3. No implementation enforces the alias expansion limit (D-18) yet.**
D-18, D-19 and D-20 ([§2.4.1](02-document-model.md#241-bounding-alias-expansion))
are normative content as of **v0.18.0-beta**, and as of v0.21.0-beta no port
enforces them. This is a rollout gap, not a design defect and not a divergence
any implementation intends to keep: it is the expected interval between a spec
rule landing and the ports adopting it. Tracked by omnist-spec#75, and per port
by [omnist-go#117](https://github.com/omnist-dev/omnist-go/issues/117),
[omnist-rs#180](https://github.com/omnist-dev/omnist-rs/issues/180) and
[omnist-j#113](https://github.com/omnist-dev/omnist-j/issues/113). Remove this
entry when every port enforces D-18.

**What a runner reports today.** All five ports skip the six vectors in
`test-suite/formats-yaml/alias-expansion.json` as E-20 skips citing this entry.
Java has a partial stop-gap, not an implementation: SnakeYAML's default cap of
50 collection aliases rejects legitimate merge-key configs with 51 or more
references (documented in omnist-j#113).

**Adopting D-18 is two steps, not one:** **(a)** implement the rule, and
**(b)** add `declared_max_alias_expansion` to the runner's limit-key allowlist.
A port that does (a) and forgets (b) gets no loud failure to tell it so —
`expansion-at-declared-limit-succeeds` would report green while being run
against that port's own default maximum instead of the 3 the vector declares,
so it exercises the wrong boundary and can mask a real threshold bug
indefinitely. A failure gets triaged. A pass gets believed. Until a port
completes both steps, its runner MUST NOT report that vector as a pass on the
strength of step (a) alone.

**DIV-5. OSD-14 has no vector, so its adoption rests on each port's unit tests.**
[OSD-14](05-osd-grammar.md#59-canonical-output), new in **v0.20.0-beta**: a
field label carrying a C0 control character has no OSD spelling, so an OSD
writer handed such a schema MUST fail with `write.unsupported-value` rather than
emit text no conformant reader accepts. As of v0.21.0-beta all five ports
implement it and report it done, verified by the unit tests in each port's PR
and by nothing else — the suite cannot check it. The companion rule, OSD-15
(canonical label escaping), is adopted by all five ports and is pinned by the
four `osd-grammar/canonical-output/label-*` vectors, which pass everywhere; it
needs no entry.

**Why this is still listed.** A vector gives a schema as OSD text (§8.5.3), so a
schema whose label has no OSD text cannot be written as a vector input at all,
and §8.5.3 has no driver taking a schema in any other form — `write_schema` is a
documented operation ([§E.11](extensions/osd-oml.md#e11-api-cli-surface)) that
the driver table and the
[Operations & Models Reference](operations-and-models-reference.md) both omit.
E-27's `bytes_hex` fixed the same untestable-MUST shape for D-14 on the read
side and does nothing here: OSD-14 is a **write**-side rule whose input is a
Schema, and it still needs a driver that accepts a schema in some form other
than OSD text — a canonical Schema encoding, or a `write_schema` driver fed by
`schema_from_document`. Until that exists, adoption is verified by hand and this
entry says so rather than letting a green suite imply coverage. Remove this
entry when a vector pins OSD-14 and every port passes it.

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
