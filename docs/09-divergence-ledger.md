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
with the same codes (§8.3 is mandatory, §8.1).

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
defaults (200 / 1,000,000 / 4,300), to fit its deployment target, and, in a
codec for a format with an anchor/reference mechanism, its alias expansion
factor (D-18) and expanded size (D-22) maxima to values other than the
reference defaults (50 / 1,000,000). What is not permitted to vary is covered
in §9.2.

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

§2.4's two further limits, the alias expansion factor (D-18) and the expanded
size (D-22), are scoped rather than universal: they bind an implementation's
codec for any format that has an anchor/reference mechanism, which today means
YAML and nothing else. Where they apply each is as non-negotiable as the other
three — a finite documented maximum, and `document.limit.alias-expansion` or
`document.limit.expanded-size` respectively when it is crossed. Where no such
mechanism exists there is nothing to enforce, and an implementation shipping no
YAML codec is not diverging by not enforcing them. Together with the three
universal limits these are the five quantities D-9 lists.

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
of truth: each implementation's own conformance run is. It records **what**,
not **how it got that way**: the reasoning, history and audit trail for any
cell live in that port's own issue tracker and commit history, not here.*

**Last updated: 2026-10-13.** This chapter records which spec release each port
pins and what is open. It does not record a port's own version, its registry
state or its conformance counts: those are the port's tags and CI, and copying
them here was the largest source of stale figures. The "Spec version pinned" row
is checked against the CHANGELOG's releases by `tools/check_version_sync.py`.
All five ports compare diagnostics as `(path, code)` sets with strict runners,
except that TypeScript's runner compares a read report's diagnostics on paths
only (`DIV-33`).

All five ports implement **v0.35.0-beta**, the latest spec release. Every
earlier wave is complete in every port: the E-10 index on every occurrence of a
repeated label, the D-23 maximum input size (64 MiB by default in every port),
OML-29, C-9 and C-10 (an XML writer fails on a null leaf); v0.27.0-beta's YAML
alias rule set (D-18, D-18a, D-19, D-20 and D-22, malformed-merge errors winning
over limit codes, `<<: []` accepted as a carrier that merges nothing);
v0.28.0-beta's programmatic schema diagnostics (see `DIV-5`); v0.34.0-beta's
duplicate keys (C-11, C-12), YAML collection tags (C-13), configurable limits and
registered write reports; and v0.35.0-beta's quoted path labels (E-36), unaltered
temporals (E-37), XML characters and references (C-15, C-16), YAML escapes and
number spellings (C-14, C-17), lone `CR` (E-29) and negative zero. Which port
adopted what, in which release, is in each port's own changelog.

No port implements the OSD-OML extension (§9.6).

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Spec version pinned | v0.35.0-beta | v0.35.0-beta | v0.35.0-beta | v0.35.0-beta | v0.35.0-beta |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 and D-22 are enforced by all five) | all three | all three | all three | all three | all three |
| Maximum input size (D-23, a SHOULD; default 64 MiB) | yes (`max_input_bytes`) | yes (`maxInputBytes`) | yes (`Limits::max_input_bytes`) | yes (`Limits.MaxInputBytes`) | yes (`Limits.maxInputBytes`) |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| OSD writer: label escaping (OSD-15), unwritable label refused (OSD-14) | both done | both done (OSD-15 fixed in #150) | both done (`to_osd` returns `Result`) | both done (`osd.Write` returns an error) | both done |
| Writers refuse a string with no UTF-8 encoding (C-9) | yes (measured 2026-10-05: all five writers fail with `write.unsupported-value` at `$.a`; `DIV-5`) | yes (measured 2026-10-05, same five writers and result) | not applicable (`String` is always valid UTF-8) | yes (the C-9 unit tests pass, run 2026-10-05; `DIV-5`) | yes (`Utf8WriterTest` passes, run 2026-10-05; `DIV-5`) |
| An XML writer refuses a null leaf (C-10) | yes (measured 2026-10-06: `write_xml` of a null leaf fails with `write.unsupported-value` at `$.a`; all 5 `formats-xml/nulls` vectors pass) | yes (all 5 `formats-xml/nulls` vectors pass, measured) | yes (measured, vector runner) | yes (measured, conformance runner) | yes (measured, harness) |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported (drop paths indexed, measured 2026-10-06) | all four, attribute/namespace/interleaving drops reported (drop paths indexed) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported (drop paths indexed) |
| §8.3 error codes | yes | yes, except that the runner does not compare the codes of a read report (`DIV-33`) | yes | yes | yes |
| D-14, invalid UTF-8 rejected with `parse.invalid-encoding` at `1:1` (§2.5) | yes, via the CLI (re-measured 2026-10-05) | yes, via the CLI (re-measured) | yes, via `omnist-cli` (re-measured) | yes, at the front of all six readers (CLI re-measured) | yes, in the CLI for a file (re-measured; stdin not re-run) |
| Fuzz testing | yes | yes | yes | yes | yes |
| Test coverage (the gate, read from each port's configuration) | 100% lines, gated (`coverage report --fail-under=100`) | 100% lines, branches, functions and statements, gated (vitest thresholds) | 100% lines, gated (`cargo llvm-cov --fail-under-lines 100`); region coverage is not gated | 100% per function, gated; excludes `main`, `cmdMaterialize` and the `tools/` harness and doc-example checker | gated at 99.6% line / 99.1% branch (the port's own configuration) |

This edit re-ran both conformance tracks of every port at its latest tag
against this tree, and re-measured each entry in 9.4 as noted there. Rows it
did not re-measure (the OML, OSD, `any`, `validate`, `materialize`, algebra and
fuzz rows) are carried from an earlier edit; the vector suites each port passes
cover them.

The Track 2 suite is v0.35.0-beta, 731 vectors in this tree. No port fails a
vector it runs, and no port skips any but the 28 OSD-OML vectors, which every
port skips until it implements that extension
([omnist#341](https://github.com/omnist-dev/omnist/issues/341),
[omnist-ts#145](https://github.com/omnist-dev/omnist-ts/issues/145),
[omnist-rs#175](https://github.com/omnist-dev/omnist-rs/issues/175),
[omnist-go#111](https://github.com/omnist-dev/omnist-go/issues/111),
[omnist-j#105](https://github.com/omnist-dev/omnist-j/issues/105)). No port skips
an alias-expansion, limit or input-size vector. Java's Track 1 headline count
includes its ten referee self-test fixtures, so it is not comparable with the
other four ([omnist-j#110](https://github.com/omnist-dev/omnist-j/issues/110)).

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

**`DIV-1`, `DIV-2`, `DIV-3`, `DIV-4`, `DIV-6`, `DIV-7`, `DIV-8`, `DIV-9`,
`DIV-10`, `DIV-11`, `DIV-14`, `DIV-15`, `DIV-16`, `DIV-17`, `DIV-18`, `DIV-19`,
`DIV-20`, `DIV-21`, `DIV-22`, `DIV-23`, `DIV-24`, `DIV-25`, `DIV-26`, `DIV-27`,
`DIV-28`, `DIV-29`, `DIV-30`, `DIV-31`, `DIV-32`, `DIV-34`, `DIV-35`, `DIV-36`,
`DIV-37`, `DIV-38`, `DIV-39`, `DIV-40` and `DIV-41` are retired numbers and MUST
NOT be reused.** All thirty-seven entries closed and were deleted; the numbers stay spent so
a citation to any of them in an older document, issue, vector comment, or port
changelog cannot silently come to mean something else. `DIV-3` (the YAML alias
rules D-18, D-18a, D-19, D-20 and D-22) closed when the last port, Python,
implemented them in omnist#352, so all five ports enforce them. `DIV-4` (the
rules v0.19.0-beta and v0.20.0-beta settled) and `DIV-6` (`bytes_hex` and D-14)
closed when the v0.21.0-beta sweep left every port satisfying every row.
`DIV-7` (the fourteen vectors new in v0.22.0-beta) closed when all five ports
passed all fourteen. `DIV-8` (eleven vectors new in v0.23.0-beta: the OML-28
array newline cases and the codec syntax errors under the `line:col`
placeholder) and `DIV-9` (four OML-28 vectors new in v0.24.0-beta) closed on
2026-10-04, when every port was found to pass every one of the fifteen.
`DIV-14`, `DIV-15` and `DIV-16` (the E-10 index on the first occurrence of a
repeated label in `validate` and `materialize` paths: the seven
`*/repeated-label-paths/*` vectors) and `DIV-17` (the ten
`document-model/input-size` vectors, D-23) and `DIV-18`, `DIV-19` and `DIV-20`
(the seven OML-29 vectors) closed on 2026-10-05: Python, TypeScript
and Rust adopted all three rules, Go and Java had
the paths and the colon gap already, and every port now enforces a 64 MiB
default maximum input size and allowlists `declared_max_input_bytes`. Each
port's own vector run that day, against a suite containing those vectors, has
none failing. `DIV-22`, `DIV-23` and `DIV-24` (the C-10 XML null leaf in
TypeScript, Rust and Go; Java never had one) closed the same day with those ports' next releases, whose vector runs
pass all five `formats-xml/nulls` vectors. `DIV-11` (Rust's Document arena
counting scalar values against the node cap, omnist-rs#192, closed as not
reproducing) closed on
2026-10-05 by measurement, not by an issue: see "Retired by measurement" at the
end of this section. `DIV-21` (Python's XML writer writing a null leaf as an
empty element) closed on 2026-10-06 with Python's next release, which passes all five `formats-xml/nulls` vectors. `DIV-25` (Go's
TOML and XML readers quadratic in the number of keys or elements,
omnist-go#132) and `DIV-26` (Go's XML writer replacing U+FFFE and U+FFFF with
U+FFFD, omnist-go#133) closed the same day with Go's next release: the
re-measured times and the writer's refusal are in the unpinned notes below.
`DIV-27` (Java's dropped-attribute paths, omnist-j#124), `DIV-28` (Python and
TypeScript skipping the vectors that declare a limit: both now expose
configurable limits and run them), `DIV-29` (the depth, node-count and
integer-digit limits outside OML), `DIV-30` (duplicate keys), `DIV-31` (write-side
format reports), `DIV-32` (YAML collection tags and `!!str <<`), `DIV-34` (TOML
number range) and `DIV-35` to `DIV-41` (quoted path labels, writing temporals,
negative zero, XML characters and references, YAML escapes, number spellings and
merge keys, Java's literals and lone `CR`) closed on 2026-10-13: every port's
run of the v0.35.0-beta suite at its latest tag fails none of the 731 vectors.
`DIV-5`, `DIV-12`, `DIV-13`, `DIV-33`, `DIV-42`, `DIV-43` and `DIV-44` are live.
One caution on `DIV-3`: comments in `test-suite/formats-xml/xml.json` and
`test-suite/formats-json/json.json` cite a `DIV-3` closed 2026-08-23. That is
an earlier entry that held the number before the alias-limit entry opened in
v0.18.0-beta (CHANGELOG); it is not the alias entry, and the number was reused
once already, which is why it is now retired. Comments in
`test-suite/document-model/limits-codecs.json` cite `DIV-28` as the reason a port
with no configuration surface skips; that entry is retired and no port skips. This note
lives here, in the preamble, rather than inside any single entry — an entry is
deleted when it closes, and a retirement note that rides along inside one
disappears with it.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

**DIV-5. OSD-14, OSD-16, C-9 and the S-8, S-22, S-23, S-24, S-25 and S-26 programmatic rules have no vector, so adoption rests on each port's unit tests, where it exists at all.**
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
(`schema.unknown-record`), S-24, S-25 and S-26 (`schema.empty-label` and
`schema.bracket-in-label` from a programmatically built label; their OSD-text
forms are pinned), and the `$` path of a programmatic
`schema.invalid-name` (S-8) share OSD-14's blocker: each takes a Schema built
programmatically, which no vector can supply. All five ports have adopted what
applies to them; status read from each port's merged source on 2026-10-04 (a
search for the codes and the writer's `max = 0` check; the behaviour was not
re-run):
- *Go*: S-8 `schema.invalid-name` at `$`, S-22
  `schema.invalid-label` at the record path, S-23 `schema.unknown-record` at
  `$` for an `EnvOrder` entry naming no record, and the OSD writer refuses
  `[0,0]` with `write.unsupported-value`.
- *TypeScript*: S-8, S-22 (a lone surrogate) and the writer
  refusal. S-23 has no surface. See `DIV-13` for a construction difference.
- *Java*: S-8 and S-22 through the new `SchemaException`, and
  the writer refusal. S-23 has no surface, and there is no OSD-OML writer.
- *Rust*: S-8 and the writer refusal. S-22 cannot occur
  (labels are `String`). S-23 has no surface.
- *Python*: S-8, S-22 (including a re-check in `to_osd`) and the
  writer refusal. S-23 has no surface.

Every cell rests on that port's unit tests; the suite checks none of it.

**Widened again at v0.32.0-beta: C-9.**
[C-9](07-codecs-and-deserialization.md#73-writing) (every writer refuses a
string value or label with no UTF-8 encoding,
[omnist-spec#161](https://github.com/omnist-dev/omnist-spec/issues/161)) takes
a Document holding a lone surrogate or, in Go, invalid UTF-8 bytes, which no
vector can supply: an input is UTF-8 text or `bytes_hex`, and neither yields
one without a D-14 `parse.invalid-encoding`. On 2026-10-04 no port implemented
it. As of 2026-10-05 all four ports to which it applies do, each from the
release that adopted v0.32.0-beta or later, and Rust meets it vacuously
(`String` is always valid UTF-8). Measured 2026-10-05 at each port's latest
tag, with the value `\ud800` as a leaf, written by all five writers:
- *Python* and *TypeScript*: JSON, YAML, TOML, XML
  and OML each fail with `write.unsupported-value` at `$.a`.
- *Go*: not run with a value here, since Go's string holds
  bytes; the port's C-9 unit tests (`writer_utf8_test.go` and the per-format
  tests, `go test` on the root, `formats/...` and `oml` packages) pass.
- *Java*: `Utf8WriterTest` passes, which covers all five
  writers per the port's `docs/limitations.md`.
- *Rust*: vacuous; the port documents the audit and a
  tripwire test (`omnist/tests/c9_vacuous.rs`).

The label case and the exact path for a label were not re-measured; the ports
document the node holding the edge as the path. C-9 shares the blocker above: a
Document carrying such a string has no vector form, so it is closed by the same
kind of driver, one that can supply a Document that no text yields. It is
adopted, but its adoption is still verified only by each port's unit tests.

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
entry when vectors pin OSD-14, OSD-16, C-9, S-22, S-23, S-24 and the
programmatic S-8 path, supplied by such a driver, and every port passes them.

**DIV-12. TypeScript's `smol-toml` parses a long array of tables in superlinear time.**
The YAML half of this entry is fixed. The quadratic block-mapping parse
reported in [omnist-ts#157](https://github.com/omnist-dev/omnist-ts/issues/157)
is resolved, and the entry's other shape, an alias pass that treated the items
of `!!pairs` and `!!omap` as scalars, no longer reproduces (C-13 now refuses
those tagged collections, and the one vector that pins the accounting uses an
untagged sequence). Measured 2026-10-06 (`readYaml` in process, one run each):
20,000 flat keys in 0.93 s and 50,000 in 1.55 s, against 22.4 s and 194.8 s
before. The port documents one deviation: in a document whose total quadratic
cost (the sum over its mappings of keys squared) exceeds that of one 4,096-key
mapping, a duplicate-key error names the duplicate key's own position rather
than the `yaml` library's (`docs/limitations.md`, read, not run).
What remains is TOML. Measured 2026-10-13 at the latest tag (the whole CLI run,
start-up included, one run each; `[[a]]` followed by `x = 1`): 60,000 tables
(720 KB) took 3.0 s and 200,000 (2.4 MB) took 25.2 s, still superlinear; the
port's own
`docs/limitations.md` gives about 47 s at 10 MiB and says the cost is the
`smol-toml` library's, and that its default 64 MiB input cap does not bound it.
This is a TypeScript implementation shape against D-9's intent, not a spec gap;
[D-23](02-document-model.md#242-resource-bounds-beyond-the-document) lets an
implementation refuse such an input by size, and D-24 says it does not make the
parse fast. Tracked in [omnist-ts#170](https://github.com/omnist-dev/omnist-ts/issues/170).
**Remove this entry when TypeScript reads an array of tables in linear time.**

**DIV-13. TypeScript's `field(label, type, 0, 0)` rejects cardinality `[0,0]` with `schema.invalid-cardinality`, although S-15 keeps `[0,0]` representable and S-24 makes the writer, not construction, refuse it.**
In TypeScript the `field()` builder throws for `min = 0` and
`max = 0`, a rule left over from before S-15 and S-24. `record()` and
`new Schema` accept a hand-built `[0,0]` literal, so the model can hold one.
Go, Java, Rust and Python accept `[0,0]` at construction. `normalize` and
`extract` on a hand-built `[0,0]` field also throw in TypeScript, because they
rebuild fields through `field()`. The port documents this as a known divergence
in its `docs/schema.md` and `CHANGELOG.md`. Measured 2026-10-13:
`field("a", t.string, 0, 0)` throws `schema.invalid-cardinality`
("has an invalid cardinality [0,0]"). Tracked in
[omnist-ts#170](https://github.com/omnist-dev/omnist-ts/issues/170).
**Remove this entry when TypeScript's `field()` accepts `[0,0]` (S-15).**

**DIV-33. TypeScript's Track 2 runner compares a read report's diagnostics on paths only.**
For a `parse` vector whose `expect.diagnostics` lists the codec's adjustments
(`format.attribute-dropped`, `format.namespace-dropped`), the runner builds the
set of `path`s and ignores the codes (`tools/conformance/vectorRunner.ts`, read,
not mutation-tested), so a wrong code on a read report would pass. Every other
runner gap this entry used to list has closed: the Track 1 lint-code comparison
(omnist#359, omnist-ts#164, omnist-rs#200, omnist-go#135, omnist-j#125), Java's
order-insensitive parse comparison (omnist-j#126) and its re-parse of a `write`
vector's text, TypeScript's path-only write comparison (omnist-ts#166), `compact`
(E-35) and the outer-whitespace trim of E-18. Tracked in
[omnist-ts#170](https://github.com/omnist-dev/omnist-ts/issues/170).
**Remove this entry when TypeScript compares `(path, code)` for a read report.**

**DIV-42. XML integer pretyping (E-4a, C-1): prose only, no vector; Rust and Go differ.**
No vector can pin it, because `parse` takes no schema. Measured 2026-10-13
against the worked case (`<r><n>` holding 4,301 digits, schema
`Root { "r": Inner }`, `Inner { "n": integer }`) through each CLI: Python,
TypeScript and Java refuse it at `$.r.n` (Java's `--json` shows
`document.limit.int-digits`; Python's and TypeScript's text messages name the
digit limit, their codes were not read). Rust refuses it at `$.r.n` with
`materialize.inexact-conversion`, where E-4a requires
`document.limit.int-digits`. Go's `materialize` leaves the value a string,
reporting `materialize.inexact-conversion` at `$.r.n`, and does not pretype XML
at all: `<n>3</n>` also stays `"3"`. Go's library was not measured. Tracked in
[omnist-rs#204](https://github.com/omnist-dev/omnist-rs/issues/204) (Rust) and
[omnist-go#140](https://github.com/omnist-dev/omnist-go/issues/140) (Go).
**Remove this entry when each port refuses the worked case at `$.r.n`.**

**DIV-43. TypeScript's readers lose data: YAML offset datetimes, TOML and YAML fractions, and an 8 MB XML attribute ([omnist-ts#169](https://github.com/omnist-dev/omnist-ts/issues/169)).**
Found by the review of the v0.35.0-beta adoption and identical on the previous
tag, so not a regression. The issue reports four defects: the YAML reader
converts an offset datetime to UTC (`12:00+01:00` reads as `11:00`); the YAML and
TOML readers truncate a fraction to three digits; an XML attribute value over
about 8 MB throws an uncaught `RangeError`; and the XML parser is super-linear
in depth (a 100,000-deep document took about 350 s before the depth limit was
reported). Of these, 2026-10-13 re-measured only the fraction: TOML
`2024-01-15T12:00:00.123456789Z` reads as `.123` (the other ports' results are in
the unpinned notes). The other three are quoted from the issue and were not run.
**Remove this entry when omnist-ts#169 is closed.**

**DIV-44. Java's OML writer emits a fraction its own grammar cannot read, and `format --schema` ignores the schema for XML ([omnist-j#133](https://github.com/omnist-dev/omnist-j/issues/133)).**
The OML grammar allows one to six fraction digits, but the writer emits a time or
datetime with every digit it holds. Measured 2026-10-13: a TOML datetime with a
nine-digit fraction converts to OML as `2024-01-15T12:00:00.123456789+00:00`,
which no conformant OML reader accepts. E-37 says a writer never alters a value
and stringifies when no native literal is exact, so the OML writer should report
`format.temporal-stringified` and write a string. The issue also reports that
the CLI's `format` command does not apply the schema's integer typing to XML,
while `convert` and `validate` do; that part was not re-run.
**Remove this entry when omnist-j#133 is closed.**

**Retired by measurement: Rust's arena cap.** `DIV-11` recorded that Rust's
Document arena counted scalar leaves against the 1,000,000-node cap, so a large
input under D-22's maximum could be refused with `document.limit.nodes`
([omnist-rs#192](https://github.com/omnist-dev/omnist-rs/issues/192), closed
as not reproducing). In Rust the arena's `push` counts only
container entries (`omnist/src/document.rs`, the `arena.containers` counter
tested against `max_nodes`), and the CLI measured 2026-10-05 reads a
1,100,000-scalar JSON array and a 1,100,000-item YAML sequence (each read
wrapped under a key, since the CLI refuses a bare top-level array or sequence
for its shape, not for a limit), a 1,100,000-key JSON object and a
1,100,000-key TOML file without a limit error. The counter arrived in commit `5aad212` (runtime-configurable limits, omnist-rs#181 and #182), which shipped in Rust's next release; at `7e297ba`, the source the entry was read from, the arena had no such counter. The issue was closed as not planned because it does not reproduce.

All five ports pass the five `formats-xml/nulls` vectors: an XML
writer fails on a null leaf with `write.unsupported-value` at the right path,
unconditionally.

**Open, unpinned behaviours.** These are spec-unspecified: no rule fixes them,
no vector pins them, and they are not divergences to fix. They are recorded
as facts about the ports, measured at each port's latest tag on the date given
in the item (2026-10-05 unless stated).
- *A document that is only `}`* (§4.6.1: OML-25 and OML-26 both need a complete
  body, so neither applies). Measured, `}` then a newline: all five ports
  report the error at `1:1`. Python, TypeScript, Go and Java report
  `parse.unexpected-token`; Rust's CLI printed only the message ("expected a
  value") with no code, which was not read from the library. They agree today;
  the spec does not require it.
- *TOML nesting depth.* Rust refuses a TOML document nested about 80 levels
  deep, below the configured depth limit of 200, because the `toml_edit` crate
  has its own recursion cap; the port documents it as `document.limit.depth` at
  `$` (`docs/limitations.md`, `CHANGELOG.md`; the CLI's `--json` errors list
  was empty, so the code was not read from the library). Measured: a 100-level
  inline-table chain and a 100-level table header were both refused by Rust,
  and a 100-level inline-table chain was accepted by Python and Go. The
  threshold is permitted variation (§9.1); the code is the part the spec fixes.

- *U+FFFE and U+FFFF in an XML string value* (omnist-go#133). Measured
  2026-10-13 with a JSON string holding U+FFFE converted to XML: all five ports
  refuse it at `$.a` (Rust and Go with `write.unsupported-value`; the other three
  codes were not read). Go used to write U+FFFD in its place. C-16 now names
  XML 1.0's `Char` for reading.
- *How UTC is spelled when written* (2026-10-13). TOML `2024-01-15T12:00:00Z`
  converted to JSON and YAML: Python, TypeScript, Rust and Go write `+00:00`;
  Java writes `Z`. All five write `+00:00` in OML. The value is the same; E-37
  pins the offset as held, not which spelling stands for UTC. Post-1.0.
- *Fractions longer than six digits, read from TOML* (2026-10-13, a nine-digit
  fraction on a datetime and on a time). Python and Rust read six digits,
  TypeScript three (`DIV-43`), Java all nine (`DIV-44` when written to OML), and
  Go refuses the literal as `parse.codec-syntax` ("malformed datetime literal").
  The spec pins no digit count beyond what OML's grammar allows. Post-1.0.
- *Raw TAB, CR and U+2028 in a YAML plain scalar* (2026-10-13, a JSON string
  `x<char>y` converted to YAML). Python writes TAB and CR double-quoted
  and U+2028 single-quoted with the character raw; TypeScript writes TAB and
  U+2028 raw and CR double-quoted; Rust writes all three raw; Java writes TAB and
  CR double-quoted and U+2028 raw; Go double-quotes all three with escapes. C-14
  pins the escapes for the other controls and not for these. Post-1.0.
- *Go's TOML and XML reader speed.* Measured 2026-10-06 on Go
  (`omnist parse`, whole run, one run each): 20,000 flat TOML keys took 0.09 s
  and 20,000 XML elements 0.10 s, against 11.6 s and 9.2 s before the fix.
  The 50,000-key figures were not re-run.

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
