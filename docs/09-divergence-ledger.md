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
of truth — each implementation's own conformance harness run is. Numbers are
kept terse deliberately: this table records **what**, not **how it got that
way** — the reasoning, history, and audit trail for any cell live in that
port's own issue tracker and commit history, not here.*

**Last updated: 2026-10-04**, from each port's own merged and
independently reviewed PR and its own conformance run, not carried forward
from an earlier edit. The Go (`v0.9.0-alpha`) and TypeScript (`v0.7.0-alpha`)
conformance runners were re-run read-only on this date at those tags against
spec v0.28.0-beta (Go 310 pass, 0 fail, 28 skip; TypeScript 304 pass, 0 fail,
34 skip); the other ports' numbers below are each port's own PR figures and
were not re-run for this edit. All
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
2026-10-05 with `git ls-remote --tags`. Python `v0.14.0` is tagged and the
PyPI Simple index serves `omnist-0.14.0` (checked 2026-10-05, after its
Publish run succeeded; `0.13.0` is also served). Rust `v0.6.1-alpha` is tagged and
crates.io's newest version is `0.6.1-alpha` (`0.6.0-alpha` is also published). Go `v0.9.0-alpha` is distributed by tag only (module proxy; no
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
`v0.7.0-alpha`, Rust `v0.6.0-alpha` and later, Go `v0.9.0-alpha` and Java
`v0.4.0-alpha`. Python `v0.13.0` pins v0.28.0-beta and adopts no later rule;
Python `v0.14.0` pins v0.32.0-beta (`634ff12`). Of the v0.28.0-beta releases
only Python `0.12.0`, `0.13.0` and `0.14.0` and Rust `0.6.0-alpha` and
`0.6.1-alpha` are served by their registries today. No port implements the OSD-OML extension (§9.6).

| | Python | TypeScript | Rust | Go | Java |
|---|---|---|---|---|---|
| Version | 0.14.0 | 0.7.0-alpha | 0.6.1-alpha | 0.9.0-alpha | 0.4.0-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 and D-22 are enforced by all five) | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| OSD writer: label escaping (OSD-15), unwritable label refused (OSD-14) | both done | both done (OSD-15 fixed in #150) | both done (`to_osd` returns `Result`) | both done (`osd.Write` returns an error) | both done |
| Writers refuse a string with no UTF-8 encoding (C-9) | no (measured 2026-10-04, `DIV-5`) | no (measured, `DIV-5`) | not applicable (`String`) | no (measured, `DIV-5`) | no (measured, `DIV-5`) |
| An XML writer refuses a null leaf (C-10) | no (measured 2026-10-05, `DIV-21`) | no (measured, `DIV-22`) | no (measured, `DIV-23`) | partly (measured, `DIV-24`: refuses, but the path of a repeated label lacks its index) | yes (measured) |
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
v0.23.0-beta added 11 vectors (298 in all) and v0.24.0-beta 4 more (302 in
all); every port passes all 15 with none skipped. v0.25.0-beta added 10 more
(312 in all), v0.26.0-beta 19 more (331 in all) and v0.27.0-beta 7 more (338
in all); all 36 are in `formats-yaml/alias-expansion.json`, which every port
now passes with none skipped. v0.30.0-beta added 17 more (355 in all): 7
repeated-label path vectors (`DIV-14`, `DIV-15`, `DIV-16`) and 10 input-size
vectors (`DIV-17`), none of them in the cells above, which stay at the
v0.27.0-beta figures. v0.31.0-beta added 7 more (362 in all), the OML-29
vectors in `oml-grammar/grammar.json` (`DIV-18`, `DIV-19`, `DIV-20`), likewise
not in the cells above. v0.33.0-beta added 5 more (367 in all), the XML null
vectors in `formats-xml/xml.json` (`DIV-21`, `DIV-22`, `DIV-23`, `DIV-24`),
also not in the cells above.

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

**`DIV-1`, `DIV-2`, `DIV-3`, `DIV-4`, `DIV-6`, `DIV-7`, `DIV-8`, `DIV-9` and
`DIV-10` are retired numbers and MUST NOT be reused.** All nine entries closed
and were deleted; the numbers stay spent so a
citation to any of them in an older
document, issue, vector comment, or port changelog cannot silently come to mean
something else. `DIV-3` (the YAML alias rules D-18, D-18a, D-19, D-20 and D-22)
closed when the last port, Python, implemented them in omnist#352, so all five
ports enforce them. `DIV-4` (the rules
v0.19.0-beta and v0.20.0-beta settled) and `DIV-6` (`bytes_hex` and D-14) closed
when the v0.21.0-beta sweep left every port satisfying every row. `DIV-7` (the
fourteen vectors new in v0.22.0-beta) closed when all five ports passed all
fourteen. `DIV-8` (eleven vectors new in v0.23.0-beta: the OML-28 array
newline cases and the codec syntax errors under the `line:col` placeholder)
and `DIV-9` (four OML-28 vectors new in v0.24.0-beta) closed on 2026-10-04,
when their own removal condition, every port passing every one of the fifteen,
was found met: the Go and TypeScript runners were re-run that day and pass them,
and the other three ports' own PR figures (§9.3) report 0 failures on the full
suite. `DIV-5`, `DIV-11`, `DIV-12`, `DIV-13`, `DIV-14`, `DIV-15`, `DIV-16`,
`DIV-17`, `DIV-18`, `DIV-19`, `DIV-20`, `DIV-21`, `DIV-22`, `DIV-23` and
`DIV-24` are live.
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

**Widened again at v0.32.0-beta: C-9.**
[C-9](07-codecs-and-deserialization.md#73-writing) (every writer refuses a
string value or label with no UTF-8 encoding,
[omnist-spec#161](https://github.com/omnist-dev/omnist-spec/issues/161)) takes
a Document holding a lone surrogate or, in Go, invalid UTF-8 bytes, which no
vector can supply: an input is UTF-8 text or `bytes_hex`, and neither yields
one without a D-14 `parse.invalid-encoding`. No port implements it. Measured
2026-10-04 at each port's latest tag, with the value `\ud800` (or the byte
`0xff`) as a leaf and as a label, written by all five writers:
- *Python (`0.13.0`)*: JSON, TOML and OML emit the raw surrogate, and the text
  raises `UnicodeEncodeError` on `.encode("utf-8")`
  ([omnist#350](https://github.com/omnist-dev/omnist/issues/350)); YAML emits
  the escape `\uD800`. XML refuses, with `write.unsupported-value`, but at a
  path that contains the label for a label case, where C-9 says the holder.
- *TypeScript (`0.7.0-alpha`)*: JSON, YAML and TOML emit the escape `\ud800`;
  OML emits the raw surrogate, which does not survive UTF-8 encoding. XML
  refuses, with the label inside the path for a label case.
- *Java (`0.4.0-alpha`)*: JSON, TOML and OML emit the raw surrogate (not
  encodable as UTF-8); YAML emits the escape. XML refuses, with a `?` standing
  for the label in the path.
- *Go (`v0.9.0-alpha`)*: JSON, TOML, XML (value) and OML emit `U+FFFD` for the
  invalid byte, a silent repair. YAML fails with the library's own error, not
  a coded one. XML refuses a label with `write.unsupported-value`, with the
  label inside the path.
- *Rust (`0.6.1-alpha`)*: vacuous (`String` is always valid UTF-8), not
  measured.

All of this was run read-only on throwaway checkouts of those tags, which have
since been deleted. C-9 shares the blocker above: a Document carrying such a
string has no vector form, so it is closed by the same kind of driver, one
that can supply a Document that no text yields.

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

**DIV-11. Rust's Document arena cap of 1,000,000 still counts scalar values as well as containers, so a large input under D-22's maximum can be refused with `document.limit.nodes` ([omnist-rs#192](https://github.com/omnist-dev/omnist-rs/issues/192)).**
Rust `0.6.1-alpha` (omnist-rs#191, the fix for omnist-rs#189) made the YAML
materialization cap count containers only, at the spec's 1,000,000 default, so
the 100,000 keys-and-values count this entry first recorded is gone and D-22's
own 1,000-service example (`W(root)` = 62,063) is accepted. What remains was
read on omnist-rs `main` (`omnist/src/document.rs`, not run here): the Document
arena's `push` counts every entry it stores, scalar leaves included, against
`MAX_NODES = 1_000_000` and reports `document.limit.nodes`. D-9 and the §2.4
table define a node as an edge list, a container, so a document of more than
1,000,000 scalars in few containers is refused by Rust and not by an
implementation that counts as D-9 does. The number is permitted variation
(§9.1); the unit is the gap.
**Remove this entry when the arena cap counts containers only
(omnist-rs#192).**

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
repo's own vector runner against the v0.30.0-beta suite: 5 of the 7
`*/repeated-label-paths/*` vectors fail, for example `$.item.sku` where
`$.item[0].sku` is expected and `$.extra` for `$.extra[0]`; the two
single-occurrence vectors pass. Until v0.30.0-beta the spec's own pseudocode
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
runner knew at v0.30.0-beta. Measured 2026-10-04 at each port's latest tag
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

**DIV-18. Python rejects a newline, `;` or comment after the colon of an OML edge ([OML-29](04-oml-grammar.md#421-separators); [omnist-spec#160](https://github.com/omnist-dev/omnist-spec/issues/160)).**
Python `0.12.0` reports `parse.unexpected-token` at the position after the
colon ("expected a value, got SEP") for `a:` newline `1`, where OML-29 and the
ABNF's `edge = label skip COLON gap value` accept it. Measured 2026-10-04 on
tag `v0.12.0` (`597864b`) with its vector runner, the `oml-grammar` suite
replaced by v0.31.0-beta's: all 7 of the OML-29 vectors fail, the six
accepted ones with the error above and the still-rejected `a:` newline
`1 b: 2` with `parse.unexpected-token` at `1:3` where `parse.trailing-content`
at `2:3` is expected.
**Remove this entry when Python passes all 7 OML-29 vectors.**

**DIV-19. TypeScript rejects a newline, `;` or comment after the colon of an OML edge (OML-29).**
The same shape as `DIV-18`. Measured 2026-10-04 on TypeScript `0.7.0-alpha`
(`89bc1bd`), `npm run conformance:vectors`: all 7 vectors fail, 304 pass and 34
skip otherwise, with "expected a value, got SEP".
**Remove this entry when TypeScript passes all 7 OML-29 vectors.**

**DIV-20. Rust rejects a newline, `;` or comment after the colon of an OML edge (OML-29).**
The same shape as `DIV-18`. Measured 2026-10-04 on Rust at `7e297ba`
(`vector_runner`): all 7 vectors fail, 304 pass and 34 skip otherwise, with
"expected a value" at the separator.
**Remove this entry when Rust passes all 7 OML-29 vectors.**

Go (`0.9.0-alpha`, `d43b83f`) and Java (`0.4.0-alpha`, `362b88b`) were measured
the same way and pass all 7 (Go 317 pass, 0 fail, 28 skip; Java's Track 2 run
passes 317): they already skip a gap after the colon.

**DIV-21. Python writes a null leaf as an empty XML element instead of failing ([C-10](07-codecs-and-deserialization.md#73-writing); [omnist-spec#164](https://github.com/omnist-dev/omnist-spec/issues/164)).**
`write_xml(read_json('{"a":null}'))` on Python `0.14.0` (`96ba4a4`, the tag)
returns `<a />`, which reads back as the empty string. With `strict=True` it
raises `WriteError` carrying a warning, "null written as an empty element",
not `write.unsupported-value`. Measured 2026-10-05 with its vector runner on
the tag, the `formats-xml` file replaced by v0.33.0-beta's: 4 of the 5 new
`formats-xml/nulls` vectors fail (the top-level, nested and repeated-label
ones with "expected failure, command succeeded"; the `strict` one with no
diagnostics), and the read-side `empty-element-reads-as-the-empty-string`
passes.
**Remove this entry when Python passes all 5 `formats-xml/nulls` vectors.**

**DIV-22. TypeScript writes a null leaf as an empty XML element instead of failing (C-10).**
The same shape as `DIV-21`. Measured 2026-10-05 on TypeScript `0.7.0-alpha`
(`89bc1bd`), `npm run conformance:vectors`: the top-level, nested and
repeated-label vectors fail ("expected failure, write succeeded"); the
`strict` vector is skipped by the runner because the `WriteError` carries no
structured code or path (the writer itself throws, "null written as an empty
element"); the read-side vector passes. The writer's report code for the
non-strict case is the port-local `null.omitted`.
**Remove this entry when TypeScript passes all 5 `formats-xml/nulls` vectors.**

**DIV-23. Rust writes a null leaf as an empty XML element instead of failing (C-10).**
The same shape as `DIV-21`. Measured 2026-10-05 on Rust `0.6.1-alpha`
(`7e297ba`, `vector_runner`): the top-level, nested and repeated-label vectors
fail ("expected failure, write succeeded"); the `strict` vector fails because
the write fails with a warning-level error that carries no structured path and
code; the read-side vector passes. The report code is the port-local
`null.omitted`, which no part of the spec defines.
**Remove this entry when Rust passes all 5 `formats-xml/nulls` vectors.**

**DIV-24. Go refuses an XML null leaf but reports a repeated label's path without its index (C-10, [E-10](08-conformance-and-errors.md#84-paths)).**
Measured 2026-10-05 on Go `0.9.0-alpha` (`d43b83f`), conformance runner: the
top-level, nested and `strict` vectors pass, and
`null-leaf-in-repeated-label-is-indexed` fails with
`$.root.item:write.unsupported-value` where `$.root.item[1]` is expected. It is
the same missing-index defect `DIV-14` records for `validate`, here in the XML
writer. Only the null case was measured; whether the XML writer's other
diagnostics on a repeated label share it was not.
**Remove this entry when Go passes all 5 `formats-xml/nulls` vectors.**

Java (`0.4.0-alpha`, `362b88b`) was measured the same way and passes all 5: its
XML writer already fails on a null leaf with `write.unsupported-value` at the
right path, unconditionally.

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
