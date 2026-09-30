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

**Last updated: 2026-09-30**, from each port's own merged and
independently reviewed PR and its own conformance run, not carried forward
from an earlier edit. Last source-audited 2026-09-30. All five ports have
adopted spec **v0.22.0-beta** (287 Track 2 vectors) and compare diagnostics as
`(path, code)` sets with strict runners:
Python ([omnist#351](https://github.com/omnist-dev/omnist/pull/351), `e72ba20`),
TypeScript ([omnist-ts#151](https://github.com/omnist-dev/omnist-ts/pull/151), `aee2311`),
Go ([omnist-go#122](https://github.com/omnist-dev/omnist-go/pull/122), `1de5e84`),
Rust ([omnist-rs#185](https://github.com/omnist-dev/omnist-rs/pull/185), `e07b19b`) and
Java ([omnist-j#117](https://github.com/omnist-dev/omnist-j/pull/117), `ac12dc1`).
All five pass all fourteen vectors v0.22.0-beta added.

**Versions.** The Version row is each port's latest **tag**. Python
`v0.10.1` is on PyPI (`omnist-0.10.1` is served). Rust `v0.3.1-alpha` is on
crates.io (newest version `0.3.1-alpha`). Go `v0.5.1-alpha` is distributed by
tag only (module proxy; no registry). TypeScript `v0.4.1-alpha` is tagged but
**not** published to npm: `@omnist-dev/omnist` (the name in `package.json`)
has only `0.2.0-alpha` and `0.3.0-alpha` (the `latest` and `alpha` tag).
Java `v0.2.6-alpha` is tagged, but its Maven Central releases await manual
Portal publishing by the maintainer; Maven Central's `maven-metadata.xml` for
`dev.omnist:omnist-j` lists `0.2.1-alpha` and `0.2.2-alpha` only, so the
latest public release is `0.2.2-alpha`.

Two things are deliberately not claimed as done anywhere: no port enforces the
alias expansion limit D-18 (`DIV-3`), and no port implements the OSD-OML
extension (§9.6).

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.10.1 | 0.4.1-alpha | 0.3.1-alpha | 0.5.1-alpha | 0.2.6-alpha |
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
| Conformance (Track 2 JSON vectors, 287 at v0.22.0-beta, all compared as `(path, code)` sets) | 247 pass / 0 fail / 40 skip | 227 pass / 0 fail / 60 skip | 247 pass / 0 fail / 40 skip | 253 pass / 0 fail / 34 skip | 253 pass / 0 fail / 34 skip |
| Conformance (fixtures) | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 (Java's Track 1 headline is 29/0/0: the 10 `_referee-self-test/*` fixtures are folded into it, [omnist-j#110](https://github.com/omnist-dev/omnist-j/issues/110); its whole-harness headline including Track 2 is 282/0/34) |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100% lines, gated (`coverage report --fail-under=100`) | 100% lines, branches, functions and statements, gated (vitest thresholds) | 100% lines, gated (`cargo llvm-cov --fail-under-lines 100`); region coverage is not gated | 100% per function, gated; excludes `main`, `cmdMaterialize` and the `tools/` harness and doc-example checker | 99.66% line / 99.19% branch measured, gated at 99.6% / 99.1% (about 1 line and 2 branches of headroom, `docs/limitations.md`) |

The Track 2 row above is the v0.22.0-beta suite, 287 vectors. v0.23.0-beta added
11 vectors (298 in all); `DIV-8` records how each port fares on those.
v0.24.0-beta added 4 more (302 in all); `DIV-9` records how each port fares on
those.

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

**`DIV-1`, `DIV-2`, `DIV-4`, `DIV-6` and `DIV-7` are retired numbers and MUST
NOT be reused.** All five entries closed and were deleted; the numbers stay spent so a
citation to any of them in an older document, issue, vector comment, or port
changelog cannot silently come to mean something else. `DIV-4` (the rules
v0.19.0-beta and v0.20.0-beta settled) and `DIV-6` (`bytes_hex` and D-14) closed
when the v0.21.0-beta sweep left every port satisfying every row. `DIV-7` (the
fourteen vectors new in v0.22.0-beta) closed when all five ports passed all
fourteen. `DIV-3`, `DIV-5`, `DIV-8` and `DIV-9` are live. This note
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

**DIV-8. Eleven vectors new in v0.23.0-beta that some ports fail today: array newline cases (OML-28) and codec syntax errors under the path placeholder (E-31, E-32).**
Seven belong to [omnist-spec#115](https://github.com/omnist-dev/omnist-spec/issues/115)
(OML-28, `oml-grammar/arrays/`) and four to
[#114](https://github.com/omnist-dev/omnist-spec/issues/114) (one malformed
document per codec, `formats-{json,yaml,toml,xml}/syntax/`, whose expected path
is the placeholder `line:col`). This is a rollout gap, not a divergence any
implementation intends to keep. It replaces the note on a codec's failure
position that the retired `DIV-7` carried, which described the state before E-31.

**How it was measured.** At each port's default-branch tip on 2026-09-30, read
only: Python `e72ba20` (the merged v0.22.0-beta adoption,
[omnist#351](https://github.com/omnist-dev/omnist/pull/351); the nine first
vectors were also measured at its predecessor `dbd4ec3`, with identical
results), TypeScript `aee2311`
([omnist-ts#151](https://github.com/omnist-dev/omnist-ts/pull/151)), Rust
`e07b19b` ([omnist-rs#185](https://github.com/omnist-dev/omnist-rs/pull/185)),
Go `1de5e84` ([omnist-go#122](https://github.com/omnist-dev/omnist-go/pull/122))
and Java `ac12dc1` ([omnist-j#117](https://github.com/omnist-dev/omnist-j/pull/117)).
Python and TypeScript through `format FILE --json` (OML) and `convert FILE --from
FORMAT --to oml --json`, Java through `format FILE --from FORMAT --json`, Go
through `omnist parse --from FORMAT FILE`, reading the `path: code` its message
prints. **Rust through its library** (`omnist::oml::read_oml` and
`omnist::formats::{json,yaml,toml,xml}::read_*`, reading `ParseError`'s
`position()` and `code`), because `omnist-cli` prints only message text. No port
was measured through its conformance runner. A cell is `(path, code)` as the
port reports it, or `pass`.

| Vectors | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| `oml-grammar/arrays/unterminated-array-then-newline-is-unexpected-token`, `one-element-array-then-newline-is-unexpected-token`, `unterminated-array-then-newline-then-closing-brace-is-unexpected-token` (all `2:1`) | pass | pass | pass | `2:1` `parse.separator-in-array` | pass |
| `oml-grammar/arrays/semicolon-inside-array-is-an-error` (`1:7`), `unterminated-array-with-no-trailing-newline-is-unexpected-token` (`1:9`) | pass | pass | pass | pass | pass |
| `oml-grammar/arrays/colon-after-newline-in-array-is-unexpected-token` (`2:1`), `semicolon-at-end-of-input-in-array-is-unexpected-token` (`1:7`) | pass | pass | pass | `parse.separator-in-array` at the same position | pass |
| `formats-json/syntax/missing-value-is-a-codec-syntax-error` (`{"a": }`) | `1:7` | no diagnostic | `1:7` | `1:7` | `1:7` |
| `formats-yaml/syntax/nested-mapping-value-is-a-codec-syntax-error` (`a: b: c`, newline) | `1:5` | no diagnostic | `1:5` | `1:1` | `1:5` |
| `formats-toml/syntax/key-without-value-is-a-codec-syntax-error` (`a = `, newline) | `1:5` | no diagnostic | `1:5` | `1:5` | `1:5` |
| `formats-xml/syntax/mismatched-closing-tag-is-a-codec-syntax-error` (`<a><b></a>`) | `1:9` | no diagnostic | `1:11` | `0:0` | `1:9` |

The `colon-after-newline…` and `semicolon-at-end-of-input…` row is a Go divergence OML-28 settles: for `a: [1`, newline, `:` and for `a: [1;` at end of input Go reports `parse.separator-in-array` where OML-28 gives `:` and the end of input `parse.unexpected-token`.

Every codec diagnostic that was reported carried `parse.codec-syntax`. The
placeholder passes a well-formed path, whatever its value, so the disagreement
in the codec rows is not itself a failure: **TypeScript** fails all four because
its read raises an error carrying only message text (`errors` is empty in
`--json`, and the library has no `parse.codec-syntax` code path for a codec
failure), and **Go** fails the XML vector because `0:0` is not a text position
(E-31); the other Go codec cells are well-formed. Counting behaviour only, Python
fails 0 of the eleven, TypeScript 4, Rust 0, Go 6 (five OML-28 cases and XML) and Java 0.

**What a runner reports today.** A runner that does not yet implement E-32
compares the string `line:col` to a real path and fails all four codec vectors
in every port, so until a port implements the placeholder its runner reports
those four as **E-20 "not yet implemented" skips citing this entry**, never as a
pass and never as a `fail` its CI has to carry (E-22). The seven OML-28 vectors
need no runner change: a port that passes one is a pass, and a port that fails
one skips it under E-20 until the same change that fixes it drops the skip.
**Remove this entry when every port passes all eleven**, which needs TypeScript to
report `parse.codec-syntax` with some `line:col` (E-11, E-31), Go to fix
OML-28 and the XML position, and every runner to implement E-32.

**Not pinned by any vector.** A JSON candidate, `[1, 2`, was dropped: Go
reports `document.unlabeled-element` for it, not `parse.codec-syntax`. The
other case recorded here, a newline or `;` before `,` or `]`, is now specified
(OML-28, `grammars/oml.abnf`) and pinned by four vectors; `DIV-9` records the
rollout.

**DIV-9. Four vectors new in v0.24.0-beta that Go fails today: a newline or `;` before `,` or `]` inside an array (OML-28, [omnist-spec#117](https://github.com/omnist-dev/omnist-spec/issues/117)).**
The four are `oml-grammar/arrays/newline-before-closing-bracket-after-first-element-is-insignificant`
(`a: [1`, newline, `]`), `newline-before-comma-after-first-element-is-insignificant`
(`a: [1`, newline, `, 2]`), `newline-before-closing-bracket-after-later-element-is-insignificant`
(`a: [1, 2`, newline, `]`) and `semicolon-before-closing-bracket-is-insignificant`
(`a: [1;]`). This is a rollout gap, not a divergence any implementation intends
to keep.

**How it was measured.** At each port's default-branch tip on 2026-09-30, read
only, from a scratch detached worktree: Python `e72ba20`, TypeScript `aee2311`,
Rust `e07b19b`, Go `1de5e84` and Java `ac12dc1` (the same commits as `DIV-8`).
Python and TypeScript through `format FILE --json`, Java through `format FILE
--json`, Go through `omnist parse --from oml FILE`, Rust through its library
(`omnist::oml::read_oml`). No port was measured through its conformance runner.

| Vector input | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| `a: [1` newline `]` | pass | pass | pass | `2:1` `parse.separator-in-array` | pass |
| `a: [1` newline `, 2]` | pass | pass | pass | `2:1` `parse.separator-in-array` | pass |
| `a: [1, 2` newline `]` | pass | pass | pass | `2:1` `parse.separator-in-array` | pass |
| `a: [1;]` | pass | pass | pass | `1:7` `parse.separator-in-array` | pass |
| `a: [1` newline `2]` (existing negative vector, control) | `2:1` `parse.separator-in-array` | same | same | same | same |

Go fails all four, two more than the two cases #117 recorded: the third,
`a: [1, 2` newline `]`, was valid under the previous ABNF as well, so Go
diverged from the grammar there already, and `a: [1;]` fails at the `;`.
Counting behaviour only, Python, TypeScript, Rust and Java fail 0 of the four
and Go 4.

**What a runner reports today.** A port that passes a vector is a pass; a port
that fails one skips it under E-20 "not yet implemented", citing this entry, and
the same change that fixes it drops the skip (E-22). No runner change is needed.
**Remove this entry when every port passes all four**, which needs Go to treat a
`SEP` before `,` or `]` as insignificant.

**Open, unpinned behaviours.** These are spec-unspecified: no rule fixes them,
no vector pins them, and they are not divergences to fix. They are recorded
as facts about the ports, measured when `DIV-7` was open and unchanged since.
- *A document that is only `}`* (§4.6.1: OML-25 and OML-26 both need a complete
  body, so neither applies). Measured, `}` then a newline: all five ports report
  `parse.unexpected-token` at `1:1` (Go's message says "expected a value"). They
  agree today; the spec does not require it.
- *A lone `CR`* (E-29 does not say which position is reported). Measured, OML
  `a: 1`, a lone `CR`, `}`: Python, TypeScript and Rust report
  `parse.unexpected-token` at `1:5`, the `CR`; Go and Java report it at `1:6`,
  the character after. `CRLF` agrees: line 2 column 1 in all five.

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
