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

§2.4.2's maximum input size (D-23) is a SHOULD, so an implementation that
enforces none is not diverging by that. One that enforces a maximum MUST
raise `document.limit.input-size` when it is crossed, never another code and
never silently.

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

**Last updated: 2026-10-02**, from each port's own merged and
independently reviewed PR and its own conformance run, not carried forward
from an earlier edit. Last source-audited 2026-09-30; the v0.27.0-beta numbers
below are each port's own PR figures and were not re-run for this edit. All
five ports had adopted spec **v0.22.0-beta** (287 Track 2 vectors) and compare
diagnostics as `(path, code)` sets with strict runners:
Python ([omnist#351](https://github.com/omnist-dev/omnist/pull/351), `e72ba20`),
TypeScript ([omnist-ts#151](https://github.com/omnist-dev/omnist-ts/pull/151), `aee2311`),
Go ([omnist-go#122](https://github.com/omnist-dev/omnist-go/pull/122), `1de5e84`),
Rust ([omnist-rs#185](https://github.com/omnist-dev/omnist-rs/pull/185), `e07b19b`) and
Java ([omnist-j#117](https://github.com/omnist-dev/omnist-j/pull/117), `ac12dc1`).
All five pass all fourteen vectors v0.22.0-beta added.

All five ports now implement **v0.27.0-beta** (338 Track 2 vectors), with the
whole YAML alias rule set (D-18, D-18a, D-19, D-20 and D-22, malformed-merge
errors winning over limit codes, and `<<: []` accepted as a carrier that merges
nothing):
TypeScript ([omnist-ts#156](https://github.com/omnist-dev/omnist-ts/pull/156) and #158),
Rust ([omnist-rs#187](https://github.com/omnist-dev/omnist-rs/pull/187) and #188),
Go ([omnist-go#125](https://github.com/omnist-dev/omnist-go/pull/125), #126 and #127),
Java ([omnist-j#118](https://github.com/omnist-dev/omnist-j/pull/118) and #120) and
Python ([omnist#352](https://github.com/omnist-dev/omnist/pull/352), merged as
`0133f89`, pinned to v0.27.0-beta).

**Versions.** The Version row is each port's latest **tag**, checked
2026-10-04 with `git ls-remote --tags`. Python `v0.12.0` is tagged and the
PyPI Simple index serves `omnist-0.12.0`. Rust `v0.6.0-alpha` is tagged and
crates.io's newest version is still `0.5.1-alpha`, so `0.6.0-alpha` is tagged,
not published. Go `v0.9.0-alpha` is distributed by tag only (module proxy; no
registry). TypeScript `v0.7.0-alpha` is tagged; npm (`@omnist-dev/omnist`)
serves `0.6.0-alpha` as both the `latest` and `alpha` dist-tag, so
`0.7.0-alpha` is tagged, not published. Java `v0.4.0-alpha` is tagged and its
Release run is waiting for manual approval; the latest version on Maven Central
is `0.3.1-alpha`.

The v0.26.0-beta alias rules are in Go `v0.7.0-alpha`, Rust `v0.5.0-alpha`,
TypeScript `v0.6.0-alpha` and Java `v0.3.0-alpha`; the v0.27.0-beta adoption is
in Go `v0.7.1-alpha` and later, Rust `v0.5.1-alpha`, TypeScript `v0.6.1-alpha`,
Java `v0.3.1-alpha` and Python `v0.11.0`. The v0.28.0-beta schema diagnostics
(S-8, S-22, S-23 and S-24; see `DIV-5`) are in Python `v0.12.0`, TypeScript
`v0.7.0-alpha`, Rust `v0.6.0-alpha`, Go `v0.9.0-alpha` and Java `v0.4.0-alpha`.
Of the v0.28.0-beta releases only Python `0.12.0` is served by its registry
today. No port implements the OSD-OML extension (§9.6).

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.12.0 | 0.7.0-alpha | 0.6.0-alpha | 0.9.0-alpha | 0.4.0-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 and D-22 are enforced by all five) | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| OSD writer: label escaping (OSD-15), unwritable label refused (OSD-14) | both done | both done (OSD-15 fixed in #150) | both done (`to_osd` returns `Result`) | both done (`osd.Write` returns an error) | both done |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| D-14, invalid UTF-8 rejected with `parse.invalid-encoding` at `1:1` (§2.5) | yes, via the CLI | yes, via the CLI | yes, via `omnist-cli` | yes, at the front of all six readers | yes, on stdin |
| Conformance (Track 2 JSON vectors, all compared as `(path, code)` sets; 338 at v0.27.0-beta) | 304 pass / 0 fail / 34 skip (measured at v0.27.0-beta, per-port PR omnist#352; the 34 are 28 OSD-OML and 6 `limits`) | 304 pass / 0 fail / 34 skip (measured at v0.27.0-beta, per-port PR omnist-ts#158; the 34 are 28 OSD-OML and 6 `limits`) | 304 pass / 0 fail / 34 skip (measured at v0.27.0-beta, per-port PR omnist-rs#188; the 34 are 28 OSD-OML and 6 `limits`) | 310 pass / 0 fail / 28 skip (measured at v0.27.0-beta, per-port PR omnist-go#126; the 28 are all OSD-OML) | 310 pass / 0 fail / 28 skip (measured at v0.27.0-beta, per-port PR omnist-j#120; the 28 are all OSD-OML) |
| Conformance (fixtures) | 19/19 (at v0.27.0-beta, per-port PR) | 19/19 (at v0.27.0-beta, per-port PR) | 19/19 (at v0.27.0-beta, per-port PR) | 19/19 (at v0.27.0-beta, per-port PR) | 29/0/0 at v0.27.0-beta (Java's Track 1 headline: the 10 `_referee-self-test/*` fixtures are folded into it, [omnist-j#110](https://github.com/omnist-dev/omnist-j/issues/110)) |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100% lines, gated (`coverage report --fail-under=100`) | 100% lines, branches, functions and statements, gated (vitest thresholds) | 100% lines, gated (`cargo llvm-cov --fail-under-lines 100`); region coverage is not gated | 100% per function, gated; excludes `main`, `cmdMaterialize` and the `tools/` harness and doc-example checker | 99.66% line / 99.19% branch measured, gated at 99.6% / 99.1% (about 1 line and 2 branches of headroom, `docs/limitations.md`) |

The Track 2 row is one suite, v0.27.0-beta, 338 vectors, for all five ports.
v0.23.0-beta added 11 vectors (298 in all); `DIV-8` records how each port fares
on those. v0.24.0-beta added 4 more (302 in all); `DIV-9` records how each port
fares on those. v0.25.0-beta added 10 more (312 in all), v0.26.0-beta 19 more
(331 in all) and v0.27.0-beta 7 more (338 in all); all 36 are in
`formats-yaml/alias-expansion.json`, which every port now passes with none
skipped. v0.29.0-beta added 17 more (355 in all): 7 repeated-label path
vectors (`DIV-14`, `DIV-15`, `DIV-16`) and 10 input-size vectors (`DIV-17`),
none of them in the cells above, which stay at the v0.27.0-beta figures.

**What each port skips.** Python: 28
OSD-OML ([omnist#341](https://github.com/omnist-dev/omnist/issues/341)) and 6
`declared_max_depth` / `declared_max_nodes` / `declared_max_int_digits`
vectors (its limits are module constants). TypeScript: 28
OSD-OML and 6 compile-time limits. Rust: 28 OSD-OML
([omnist-rs#175](https://github.com/omnist-dev/omnist-rs/issues/175)) and 6
`document-model/limits` (compile-time constants,
[omnist-rs#181](https://github.com/omnist-dev/omnist-rs/issues/181)). Go: 28
OSD-OML ([omnist-go#111](https://github.com/omnist-dev/omnist-go/issues/111)).
Java: 28 OSD-OML
([omnist-j#105](https://github.com/omnist-dev/omnist-j/issues/105)). No port
skips an alias-expansion vector. Skip counts are therefore not comparable
across ports beyond those shared categories.

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

**`DIV-1`, `DIV-2`, `DIV-3`, `DIV-4`, `DIV-6`, `DIV-7` and `DIV-10` are
retired numbers and MUST NOT be reused.** All seven entries closed and were
deleted; the numbers stay spent so a citation to any of them in an older
document, issue, vector comment, or port changelog cannot silently come to mean
something else. `DIV-3` (the YAML alias rules D-18, D-18a, D-19, D-20 and D-22)
closed when the last port, Python, implemented them in omnist#352, so all five
ports enforce them. `DIV-4` (the rules
v0.19.0-beta and v0.20.0-beta settled) and `DIV-6` (`bytes_hex` and D-14) closed
when the v0.21.0-beta sweep left every port satisfying every row. `DIV-7` (the
fourteen vectors new in v0.22.0-beta) closed when all five ports passed all
fourteen. `DIV-5`, `DIV-8`, `DIV-9`, `DIV-11`, `DIV-12`, `DIV-13`, `DIV-14`,
`DIV-15`, `DIV-16` and `DIV-17` are live.
One caution on `DIV-3`: comments in `test-suite/formats-xml/xml.json` and
`test-suite/formats-json/json.json` cite a `DIV-3` closed 2026-08-23. That is
an earlier entry that held the number before the alias-limit entry opened in
v0.18.0-beta (CHANGELOG); it is not the alias entry, and the number was reused
once already, which is why it is now retired. This note
lives here, in the preamble, rather than inside any single entry — an entry is
deleted when it closes, and a retirement note that rides along inside one
disappears with it.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

**DIV-5. OSD-14, OSD-16 and the S-8, S-22, S-23 and S-24 programmatic rules have no vector, so adoption rests on each port's unit tests, where it exists at all.**
[OSD-14](05-osd-grammar.md#59-canonical-output), new in **v0.20.0-beta**: a
field label carrying a C0 control character has no OSD spelling, so an OSD
writer handed such a schema MUST fail with `write.unsupported-value` rather than
emit text no conformant reader accepts. As of v0.21.0-beta all five ports
implement it and report it done, verified by the unit tests in each port's PR
and by nothing else — the suite cannot check it. The companion rule, OSD-15
(canonical label escaping), is adopted by all five ports and is pinned by the
four `osd-grammar/canonical-output/label-*` vectors, which pass everywhere; it
needs no entry.

**Widened at v0.28.0-beta.** [OSD-16](05-osd-grammar.md#59-canonical-output)
(a writer fails on `max = 0`), S-22 (`schema.invalid-label`), S-23
(`schema.unknown-record`), S-24, and the `$` path of a programmatic
`schema.invalid-name` (S-8) share OSD-14's blocker: each takes a Schema built
programmatically, which no vector can supply. All five ports have adopted what
applies to them; status read from each port's merged source on 2026-10-04 (a
search for the codes and the writer's `max = 0` check; the behaviour was not
re-run):
- *Go (`v0.9.0-alpha`)*: S-8 `schema.invalid-name` at `$`, S-22
  `schema.invalid-label` at the record path, S-23 `schema.unknown-record` at
  `$` for an `EnvOrder` entry naming no record, and the OSD writer refuses
  `[0,0]` with `write.unsupported-value`.
- *TypeScript (`0.7.0-alpha`)*: S-8, S-22 (a lone surrogate) and the writer
  refusal. S-23 has no surface. See `DIV-13` for a construction difference.
- *Java (`0.4.0-alpha`)*: S-8 and S-22 through the new `SchemaException`, and
  the writer refusal. S-23 has no surface, and there is no OSD-OML writer.
- *Rust (`0.6.0-alpha`)*: S-8 and the writer refusal. S-22 cannot occur
  (labels are `String`). S-23 has no surface.
- *Python (`0.12.0`)*: S-8, S-22 (including a re-check in `to_osd`) and the
  writer refusal. S-23 has no surface.

Every cell rests on that port's unit tests; the suite checks none of it.

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
entry when vectors pin OSD-14, OSD-16, S-22, S-23, S-24 and the programmatic
S-8 path, supplied by such a driver, and every port passes them.

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

**DIV-11. Rust's materialization node cap is 100,000 and counts keys as well as values, so a document the spec's own D-22 example accepts is refused with `document.limit.nodes`.**
Rust's YAML materialization cap is 100,000 nodes, reported as
`document.limit.nodes`, and it counts keys and values
(omnist-rs `docs/limitations.md` and `docs/formats/yaml.md`; read, not run
here). D-9 and the §2.4 table define the limit as the nodes materialized while
building one Document, and in the Document model a node is an edge list, a
container, so neither a key nor a scalar value is a node; the reference default
is 1,000,000. The number alone is permitted variation (§9.1), but the unit is
what makes this a gap: D-22's own measured example of 1,000 services merging a
60-key block has `W(root)` = 62,063 value slots, far under D-22's default, and
Rust refuses it because its count of keys plus values exceeds 100,000. Rust
documents this and says it is pre-existing and unchanged by omnist-rs#187.
No tracking issue was found. **Remove this entry when Rust counts nodes as D-9
defines them, or raises the cap, so that no input under D-22's maximum is
refused by the node cap.**

Tracked as [omnist-rs#189](https://github.com/omnist-dev/omnist-rs/issues/189),
which recommends counting containers only and raising the cap to the
spec default.

**DIV-12. TypeScript's `yaml` library parses a block mapping in quadratic time, and aliases inside `!!pairs` and `!!omap` are not counted ([omnist-ts#157](https://github.com/omnist-dev/omnist-ts/issues/157)).**
Two denial-of-service shapes that predate v0.26.0-beta and are specific to this
port, measured in omnist-ts#157 (not re-run here). The `yaml` library's parse
cost is quadratic in the keys of one block mapping: 20,000 keys took 22.4 s and
a 1.19 MB, 50,000-key mapping took 194.8 s, before any omnist check runs, so
D-18 and D-22 cannot help. And the alias pass treats the items of `!!pairs` and
`!!omap` as scalars, so an alias tower inside them is invisible to the ratio and
size checks (an 801-byte, 7-level tower was accepted by both and stopped later
by the node limit after about 10 s and 360 MB). This is a TypeScript
implementation defect against D-9, D-18 and D-22, not a spec gap. Slow parsing
is not unique to TypeScript, but the quadratic shape is only measured there:
the omnist#352 description reports PyYAML parsing a 1.1 MB, 50,000-key
mapping in about 4 s (one point, no scaling series; not re-run here).
**Remove this entry when #157 is fixed.** [D-23](02-document-model.md#242-resource-bounds-beyond-the-document) lets an
implementation refuse such an input by size; it does not make the parse fast
(D-24).

**DIV-13. TypeScript's `field(label, type, 0, 0)` rejects cardinality `[0,0]` with `schema.invalid-cardinality`, although S-15 keeps `[0,0]` representable and S-24 makes the writer, not construction, refuse it.**
In TypeScript `0.7.0-alpha` the `field()` builder throws for `min = 0` and
`max = 0`, a rule left over from before S-15 and S-24. `record()` and
`new Schema` accept a hand-built `[0,0]` literal, so the model can hold one.
Go, Java, Rust and Python accept `[0,0]` at construction. `normalize` and
`extract` on a hand-built `[0,0]` field also throw in TypeScript, because they
rebuild fields through `field()`. The port documents this as a known divergence
in its `docs/schema.md` and `CHANGELOG.md`. Read from the merged source
(`src/schema.ts`); not run here.
**Remove this entry when TypeScript's `field()` accepts `[0,0]` (S-15).**

**DIV-14. Python omits the index on the first occurrence of a repeated label in `validate` and `materialize` paths.**
E-10 and the §3.6.1 and §7.2.1 pseudocode now agree: every occurrence of a label
that occurs more than once in a node is indexed, the first included. Python
`0.12.0` indexes only from the second occurrence. Measured 2026-10-04 with the
repo's own vector runner against the v0.29.0-beta suite: 5 of the 7
`*/repeated-label-paths/*` vectors fail, for example `$.item.sku` where
`$.item[0].sku` is expected and `$.extra` for `$.extra[0]`; the two
single-occurrence vectors pass. Until v0.29.0-beta the spec's own pseudocode
had `i > 0`, so this is a divergence from the corrected rule and from E-10, not
an old defect that went unseen.
**Remove this entry when Python passes all 7 `repeated-label-paths` vectors.**

**DIV-15. TypeScript omits the index on the first occurrence of a repeated label in `validate` and `materialize` paths.**
The same shape as `DIV-14`. Measured 2026-10-04 on TypeScript `0.7.0-alpha`
(`89bc1bd`) with its vector runner: 5 of the 7 `*/repeated-label-paths/*`
vectors fail, the first occurrence paths without `[0]`, and the two
single-occurrence vectors pass.
**Remove this entry when TypeScript passes all 7 `repeated-label-paths` vectors.**

**DIV-16. Rust omits the index on the first occurrence of a repeated label in `validate` and `materialize` paths.**
The same shape as `DIV-14`. Measured 2026-10-04 on Rust at `7e297ba`, two
commits after `0.6.0-alpha`, with its vector runner: 5 of the 7
`*/repeated-label-paths/*` vectors fail in the same way, and the two
single-occurrence vectors pass.
**Remove this entry when Rust passes all 7 `repeated-label-paths` vectors.**

Go (`0.9.0-alpha`, `d43b83f`) and Java (`0.4.0-alpha`, `362b88b`) were measured
the same way and pass all 7: they already index the first occurrence.

**DIV-17. No port enforces a maximum input size, so the ten `document-model/input-size` vectors are not yet satisfied ([D-23](02-document-model.md#242-resource-bounds-beyond-the-document); related [omnist-ts#157](https://github.com/omnist-dev/omnist-ts/issues/157)).**
D-23 is a SHOULD and the ten vectors carry `declared_max_input_bytes`, a key no
runner knew at v0.29.0-beta. Measured 2026-10-04 at each port's latest tag
(Rust two commits past it), on the first six vectors written: Python's runner
fails all six as an unknown
declared-limit key; the TypeScript, Rust and Go runners do not allowlist the
key, so the three one-byte-over vectors fail ("expected failure, parse
succeeded") and the three at-the-maximum vectors pass against the port's own
default, which is a false pass; Java's runner skips all six as an unrecognised
limit key. All five reach E-20 "not yet implemented" skips once the key is
allowlisted. Python's reader was also called directly on each input: it accepts
all six, as it enforces no maximum, so the three one-byte-over cases would fail
even with the key taught.
These runner results are a harness defect as well as a gap: E-20a requires a
runner to fail or skip a vector with a `declared_*` key it does not know, and
the TypeScript, Rust and Go runners do neither.
**Remove this entry when every port either enforces a configurable maximum
input size and passes all ten vectors, or allowlists
`declared_max_input_bytes` and records an E-20 skip for them.**

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
