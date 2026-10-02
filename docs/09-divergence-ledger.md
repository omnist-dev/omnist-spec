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

**Last updated: 2026-10-02**, from each port's own merged and
independently reviewed PR and its own conformance run, not carried forward
from an earlier edit. Last source-audited 2026-09-30; the v0.26.0-beta numbers
below are each port's own PR figures and were not re-run for this edit. All
five ports had adopted spec **v0.22.0-beta** (287 Track 2 vectors) and compare diagnostics as
`(path, code)` sets with strict runners:
Python ([omnist#351](https://github.com/omnist-dev/omnist/pull/351), `e72ba20`),
TypeScript ([omnist-ts#151](https://github.com/omnist-dev/omnist-ts/pull/151), `aee2311`),
Go ([omnist-go#122](https://github.com/omnist-dev/omnist-go/pull/122), `1de5e84`),
Rust ([omnist-rs#185](https://github.com/omnist-dev/omnist-rs/pull/185), `e07b19b`) and
Java ([omnist-j#117](https://github.com/omnist-dev/omnist-j/pull/117), `ac12dc1`).
All five pass all fourteen vectors v0.22.0-beta added.

Four ports have since adopted **v0.26.0-beta** (331 Track 2 vectors), with the
whole YAML alias rule set (D-18, D-18a, D-19, D-20 and D-22, malformed-merge
errors winning over limit codes):
TypeScript ([omnist-ts#156](https://github.com/omnist-dev/omnist-ts/pull/156), `5238410`),
Rust ([omnist-rs#187](https://github.com/omnist-dev/omnist-rs/pull/187), `3b0f080`),
Go ([omnist-go#125](https://github.com/omnist-dev/omnist-go/pull/125), `3e970e8`) and
Java ([omnist-j#118](https://github.com/omnist-dev/omnist-j/pull/118), `43b205a`).
Python is still at v0.22.0-beta and implements none of the alias rules
(`DIV-3`).

**Versions.** The Version row is each port's latest **tag**. Python
`v0.10.1` is on PyPI (`omnist-0.10.1` is served). Rust `v0.5.0-alpha` is
tagged and its Publish run is in progress; crates.io's newest version is
still `0.3.1-alpha`. Go `v0.7.0-alpha` is distributed by tag only (module
proxy; no registry). TypeScript `v0.6.0-alpha` is tagged but **not**
published to npm: `@omnist-dev/omnist` (the name in `package.json`) has only
`0.2.0-alpha` and `0.3.0-alpha` (the `latest` and `alpha` tag). Java
`v0.3.0-alpha` is tagged, but its Release workflow run is waiting for
manual approval and nothing newer than `0.2.5-alpha` is on Maven Central:
`maven-metadata.xml` for `dev.omnist:omnist-j` lists `0.2.1-alpha`,
`0.2.2-alpha` and `0.2.5-alpha`, with `0.2.5-alpha` as latest and release.

The v0.26.0-beta adoptions of Go, Rust and TypeScript are merged on each
default branch and tagged (`v0.7.0-alpha`, `v0.5.0-alpha`, `v0.6.0-alpha`).
Java's adoption is in its `v0.3.0-alpha` tag. None of the v0.26.0-beta rule
set is published to a registry yet; Python has not adopted it.
No port implements the OSD-OML extension (§9.6).

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.10.1 | 0.6.0-alpha | 0.5.0-alpha | 0.7.0-alpha | 0.3.0-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 and D-22 are enforced by TypeScript, Rust, Go and Java, not Python — DIV-3) | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| OSD writer: label escaping (OSD-15), unwritable label refused (OSD-14) | both done | both done (OSD-15 fixed in #150) | both done (`to_osd` returns `Result`) | both done (`osd.Write` returns an error) | both done |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| D-14, invalid UTF-8 rejected with `parse.invalid-encoding` at `1:1` (§2.5) | yes, via the CLI | yes, via the CLI | yes, via `omnist-cli` | yes, at the front of all six readers | yes, on stdin |
| Conformance (Track 2 JSON vectors, all compared as `(path, code)` sets; 331 at v0.26.0-beta) | 247 pass / 0 fail / 40 skip (measured at v0.22.0-beta, 287 vectors; not re-run) | 297 pass / 0 fail / 34 skip (measured at v0.26.0-beta (omnist-ts#156); the 34 are 28 OSD-OML and 6 `limits`) | 297 pass / 0 fail / 34 skip (measured at v0.26.0-beta (omnist-rs#187); the 34 are 28 OSD-OML and 6 `limits`) | 303 pass / 0 fail / 28 skip (measured at v0.26.0-beta (omnist-go#125); the 28 are all OSD-OML) | 303 pass / 0 fail / 28 skip (measured at v0.26.0-beta (omnist-j#118); the 28 are all OSD-OML) |
| Conformance (fixtures) | 19/19 (not re-run) | 19/19 (at v0.26.0-beta) | 19/19 (at v0.26.0-beta) | 19/19 (at v0.26.0-beta) | 29/0/0 at v0.26.0-beta (Java's Track 1 headline: the 10 `_referee-self-test/*` fixtures are folded into it, [omnist-j#110](https://github.com/omnist-dev/omnist-j/issues/110)) |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage | 100% lines, gated (`coverage report --fail-under=100`) | 100% lines, branches, functions and statements, gated (vitest thresholds) | 100% lines, gated (`cargo llvm-cov --fail-under-lines 100`); region coverage is not gated | 100% per function, gated; excludes `main`, `cmdMaterialize` and the `tools/` harness and doc-example checker | 99.66% line / 99.19% branch measured, gated at 99.6% / 99.1% (about 1 line and 2 branches of headroom, `docs/limitations.md`) |

The Track 2 row mixes two suites: Python's cell is the v0.22.0-beta suite, 287
vectors, and the other four are at v0.26.0-beta, 331 vectors. v0.23.0-beta added
11 vectors (298 in all); `DIV-8` records how each port fares on those.
v0.24.0-beta added 4 more (302 in all); `DIV-9` records how each port fares on
those. v0.25.0-beta added 10 more (312 in all), and v0.26.0-beta 19 more (331
in all); all 29 are in `formats-yaml/alias-expansion.json`, which `DIV-3`
covers for Python.

**What each port skips.** Python: 28
OSD-OML ([omnist#341](https://github.com/omnist-dev/omnist/issues/341)), 6
alias-expansion (`DIV-3`), 6 `declared_max_depth` / `declared_max_nodes` /
`declared_max_int_digits` vectors (its limits are module constants), all at
v0.22.0-beta; at v0.26.0-beta it will also skip every vector carrying a
declared alias key (`DIV-3`). TypeScript: 28
OSD-OML and 6 compile-time limits. Rust: 28 OSD-OML
([omnist-rs#175](https://github.com/omnist-dev/omnist-rs/issues/175)) and 6
`document-model/limits` (compile-time constants,
[omnist-rs#181](https://github.com/omnist-dev/omnist-rs/issues/181)). Go: 28
OSD-OML ([omnist-go#111](https://github.com/omnist-dev/omnist-go/issues/111)).
Java: 28 OSD-OML
([omnist-j#105](https://github.com/omnist-dev/omnist-j/issues/105)). No port
other than Python skips an alias-expansion vector. Skip counts are therefore not
comparable across ports beyond those shared categories.

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
fourteen. `DIV-3`, `DIV-5`, `DIV-8`, `DIV-9`, `DIV-10`, `DIV-11` and `DIV-12`
are live. This note
lives here, in the preamble, rather than inside any single entry — an entry is
deleted when it closes, and a retirement note that rides along inside one
disappears with it.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

**DIV-3. Python does not enforce the alias expansion limit (D-18, D-18a, D-19, D-20) or the expanded-size cap (D-22); TypeScript, Rust, Go and Java do.**
D-18, D-19 and D-20 ([§2.4.1](02-document-model.md#241-bounding-alias-expansion))
are normative content as of **v0.18.0-beta**, D-18a (the merge carrier rule)
and D-22 as of **v0.26.0-beta**. Four ports now implement the whole set and
pass every vector in `test-suite/formats-yaml/alias-expansion.json` with none
skipped: Go ([omnist-go#125](https://github.com/omnist-dev/omnist-go/pull/125)),
Rust ([omnist-rs#187](https://github.com/omnist-dev/omnist-rs/pull/187)),
TypeScript ([omnist-ts#156](https://github.com/omnist-dev/omnist-ts/pull/156))
and Java ([omnist-j#118](https://github.com/omnist-dev/omnist-j/pull/118)).
Python's reference port does not: its source at the default-branch tip
(`e72ba20`, v0.22.0-beta) has no alias-expansion limit, no
`document.limit.alias-expansion` or `document.limit.expanded-size` code, and
its runner skips the alias vectors citing this entry. Its materialization walk
has a node budget that bounds an amplified alias chain only indirectly, and the
reference still silently accepts the self-merging form `a: &a {<<: *a, k: 1}`
(see [§2.4.1](02-document-model.md#241-bounding-alias-expansion); not re-tested
here). This is a rollout gap, not a design defect and not a divergence Python
intends to keep.
Tracked by omnist-spec#75. Remove this entry when Python enforces D-18, D-18a
and D-22.

**What Python's runner reports today.** At v0.22.0-beta it skips the six
`declared_max_alias_expansion` vectors as E-20 skips citing this entry. When
its submodule reaches v0.26.0-beta it skips every vector in
`formats-yaml/alias-expansion.json` that carries `declared_max_alias_expansion`
or `declared_max_expanded_slots` the same way. The four malformed-merge vectors
carry no declared key, so a runner reports them as a pass or as an E-20 skip
citing this entry. None of this was re-run for this entry.

**Adopting D-18 is two steps, not one:** **(a)** implement the rule, and
**(b)** add `declared_max_alias_expansion` to the runner's limit-key allowlist.
Adopting D-22 is the same two steps with `declared_max_expanded_slots`.
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

**DIV-10. Go rejects an empty merge sequence (`<<: []`) as `parse.codec-syntax`; the other four ports accept it ([omnist-spec#127](https://github.com/omnist-dev/omnist-spec/issues/127)).**
D-18a lists the malformed merge shapes but is silent on a sequence with no
members, and no vector covers it, so the spec has not decided it. As measured in
omnist-spec#127 (not re-run here): Python, TypeScript, Rust and Java accept both
`<<: []` and `s: &s []` followed by `<<: *s` and merge nothing; Go reports
`parse.codec-syntax` for both, as its reader did before D-18a and as
omnist-go#125 keeps. The issue recommends accepting it as a well-formed carrier
with no members, which would change Go only. Until the issue is decided this is
a spec-undecided, port-specific behaviour, not a conformance failure.
**Remove this entry when #127 is decided and every port agrees.**

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

**DIV-12. TypeScript's `yaml` library parses a block mapping in quadratic time, and aliases inside `!!pairs` and `!!omap` are not counted ([omnist-ts#157](https://github.com/omnist-dev/omnist-ts/issues/157)).**
Two denial-of-service shapes that predate v0.26.0-beta and are specific to this
port, measured in omnist-ts#157 (not re-run here). The `yaml` library's parse
cost is quadratic in the keys of one block mapping: 20,000 keys took 22.4 s and
a 1.19 MB, 50,000-key mapping took 194.8 s, before any omnist check runs, so
D-18 and D-22 cannot help. And the alias pass treats the items of `!!pairs` and
`!!omap` as scalars, so an alias tower inside them is invisible to the ratio and
size checks (an 801-byte, 7-level tower was accepted by both and stopped later
by the node limit after about 10 s and 360 MB). This is a TypeScript
implementation defect against D-9, D-18 and D-22, not a spec gap. **Remove this
entry when #157 is fixed.**

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
