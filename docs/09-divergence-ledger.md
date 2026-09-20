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

**Update after the v0.19.0-beta port sweeps.** TypeScript ([omnist-ts#148](https://github.com/omnist-dev/omnist-ts/pull/148)), Go ([omnist-go#118](https://github.com/omnist-dev/omnist-go/pull/118)) and Rust ([omnist-rs#183](https://github.com/omnist-dev/omnist-rs/pull/183)) each bumped to v0.19.0-beta, adopted D-15/D-21, E-23, OML-25 and the YAML merge-key rules, and now compare diagnostics as `(path, code)` sets with every skip an E-20 "not yet implemented" skip that names its tracking issue. The cells above for those three were re-measured from each port's own conformance run, not carried forward. Two things are deliberately not claimed: no port implements D-18 (DIV-3), and Rust's Version cell stays at its latest tagged release, 0.2.2-alpha — the v0.19.0-beta work is merged to `main` as an unreleased 0.3.0-alpha, and the Rust conformance numbers below are for that `main`. Rust's `publish.yml` runs on a `v*` tag, so tagging it publishes to crates.io, which is a separate human decision. Python and Java have not completed the sweep; the Python column is the v0.17.0-beta measurement and Java is unchanged.

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
| Version | 0.9.5 | 0.3.1-alpha | 0.2.2-alpha | 0.4.0-alpha | 0.2.4-alpha |
| Maturity | beta, reference | alpha | alpha | alpha | alpha |
| Document model | complete | complete (`bigint` for `integer`) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) | complete (all 7 kinds natively distinguished) |
| Resource caps (§2.4's three universal limits; D-18 is enforced by no port yet — DIV-3) | all three | all three | all three | all three | all three |
| OML read/write | complete | complete | complete | complete | complete |
| OSD read/write | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) | complete (duplicate root rejected) |
| `any` type | yes | yes | yes | yes | yes |
| `validate` / `materialize` | complete | complete | complete | complete | complete |
| Schema algebra (all 6 ops) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #137) | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback | complete, codepoint-safe alphabetical fallback (PR #103) |
| Codecs (JSON/YAML/TOML/XML) | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported | all four, attribute/namespace/interleaving drops reported |
| §8.3 error codes | yes | yes | yes | yes | yes |
| Conformance (vectors, compared as (path, code) sets except Python — pins differ: TypeScript, Rust (unreleased `main`) and Go are on v0.19.0-beta, of 249; Python is on v0.17.0-beta, of 225, and compares codes loosely, see DIV-4; Java is still on v0.9.1-beta, of 204, pending its sweep) | 145 pass / 0 fail / 80 skip | 189 pass / 0 fail / 60 skip | 209 pass / 0 fail / 40 skip | 215 pass / 0 fail / 34 skip | 176 pass / 0 fail / 28 skip |
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

**`DIV-1` and `DIV-2` are retired numbers and MUST NOT be reused.** Both
entries closed and were deleted; the numbers stay spent so a citation to
either in an older document, issue, or port changelog cannot silently come to
mean something else. This note lives here, in the preamble, rather than inside
any single entry — an entry is deleted when it closes, and a retirement note
that rides along inside one disappears with it.

Because a closed entry is deleted rather than archived, a citation to one
can outlive it. **Before removing an entry, search the docs for inbound
citations** — that is how the previous `D-3` and `D-7` references ended up
pointing at nothing.

**DIV-3. No implementation enforces the alias expansion limit (D-18) yet.**
D-18, D-19 and D-20 ([§2.4.1](02-document-model.md#241-bounding-alias-expansion))
are new normative content as of **v0.18.0-beta**. As of that release no port
enforces them, the Python reference included: all six vectors in
`test-suite/formats-yaml/alias-expansion.json` — both rejection cases among
them — are currently *accepted* by the reference, verified by running them,
not assumed. This is a rollout gap, not a design defect and not a
divergence any implementation intends to keep: it is the expected interval
between a spec rule landing and the ports adopting it. Tracked by
omnist-spec#75 and the PR that introduced the rule. Remove this entry when
every port enforces D-18.

**What a runner actually reports today, vector by vector — and the one that
lies.** An earlier draft of this entry claimed the two declared-limit boundary
vectors "report as failures rather than skips" until a port allowlists
`declared_max_alias_expansion`. That is wrong, and wrong in the dangerous
direction. Run against the reference as it behaves today, all six vectors are
*accepted*, which means:

| vector | `expect.ok` | reported today |
|---|---|---|
| `nested-anchor-fan-out-exceeds-expansion-limit` | false | **fail** — real, and nothing to do with the allowlist; this vector carries no boundary the runner could skip on |
| `merge-key-config-expands-one-to-one-and-succeeds` | true | pass, correctly |
| `merge-key-sequence-flattens-each-alias-and-succeeds` | true | **fail**, as of v0.19.0-beta — it passed while the vector encoded the reference's own reversed merge order; omnist-spec#98 corrected the vector to source order and the reference has yet to follow (`DIV-4`) |
| `anchor-to-anchor-chain-under-limit-succeeds` | true | pass, correctly |
| `expansion-at-declared-limit-succeeds` | true | **a false pass** — it reports green only because nothing enforces the limit, not because the runner recognized and skipped a declared-limit vector |
| `expansion-one-past-declared-limit-fails` | false | **fail** — real, same reason as the first |

So the honest count is **three outright failures and one false pass** — two
from D-18 and, since v0.19.0-beta, one from the merge-order correction — not
two failures where skips belong. The false pass is the part that matters. Adopting
D-18 is two steps, not one: **(a)** implement the rule, and **(b)** add
`declared_max_alias_expansion` to the runner's limit-key allowlist. A port that
does (a) and forgets (b) does not get a loud failure to tell it so —
`expansion-at-declared-limit-succeeds` keeps reporting green while being run
against that port's own default maximum instead of the 3 the vector declares,
so it exercises the wrong boundary and can mask a real threshold bug
indefinitely. A failure gets triaged. A pass gets believed.

Until a port completes both steps, its runner reports these vectors as `fail`
or `skip` citing this entry. It MUST NOT report
`expansion-at-declared-limit-succeeds` as a pass on the strength of step (a)
alone.

**DIV-4. The Python reference and Java do not yet satisfy the rules v0.19.0-beta and v0.20.0-beta settled.**
Four of the seven rows below are rules new in v0.19.0-beta, and the `OML-26`
row is new in v0.20.0-beta. The
`parse.codec-syntax` row is a pre-existing §8.3.1 code that the new
doubled-BOM vectors are simply the first to exercise, and the `E-11` row is a
pre-existing path rule the same vectors are the first to catch on a
non-string diagnostic; both are listed here because adopting D-21 is what
first requires them. Each row was measured,
not assumed: the Python column comes from running the input against the
reference at v0.9.5, and the TypeScript column from the port's own sweep
reported on
[omnist-ts#148](https://github.com/omnist-dev/omnist-ts/pull/148). TypeScript, Go and Rust have since completed their sweeps
([omnist-go#118](https://github.com/omnist-dev/omnist-go/pull/118),
[omnist-rs#183](https://github.com/omnist-dev/omnist-rs/pull/183)); their
column records that. Java has not been measured against these rules and is
left blank rather than guessed at.

| Rule | Python reference today | TypeScript, Go, Rust | Required |
|---|---|---|---|
| **D-21**, second leading BOM ([§2.5](02-document-model.md#25-encoding)) | swallows it on **YAML and XML**: the doubled-BOM input builds the same Document as the single-BOM one. OML already rejects it correctly at `parse.unexpected-token` `1:1`; JSON, TOML and OSD reject it but with the code or path defects in the two rows below | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | reject on all six surfaces, `1:1` |
| **`parse.codec-syntax`** ([§8.3.1](08-conformance-and-errors.md#831-parse-text-to-document-stage-1)) | emits `parse.syntax` with **no `path` at all** for a malformed JSON or TOML read | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | `parse.codec-syntax` with a `line:col` path (E-11) |
| **E-11**, text positions on OSD diagnostics generally ([§8.4](08-conformance-and-errors.md#84-paths)) | reports the OSD doubled-BOM rejection at `path` `0`, a raw character offset, where E-11 requires `line:col` — the same defect as the E-23 row below on a diagnostic that is **not** a string error, so fixing E-23 alone will not close it | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | `1:1` |
| **E-23**, string-error position ([§8.4](08-conformance-and-errors.md#84-paths)) | reports **every** OSD string error as a raw character offset, not only the control-character case — `path` is `18` for the escaped control character and `15` for an unterminated string, where E-11 requires a `line:col` either way. The OML side is already correct (`1:4` on all four of its string-error vectors) | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | the opening quote, as `line:col` |
| **OML-25**, scalar then leftover ([§4.6.1](04-oml-grammar.md#461-top-level-disambiguation)) | emits `parse.unexpected-token` for **every** input the rule covers — `nan: 1`, `inf: 1`, `null: 1`, `true: 1`, `5: 1` and `1`-newline-`2` — at `1:4`, `1:4`, `1:5`, `1:5`, `1:2` and `2:1`. Every position is already right, so this is a code change only — and it means the reference never met the pre-existing `null: 1` vector either | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | `parse.trailing-content` throughout |
| **OML-26**, complete top-level edge then leftover ([§4.6.1](04-oml-grammar.md#461-top-level-disambiguation)) | emits `parse.unexpected-token` where OML-26 requires `parse.trailing-content`, measured live at v0.9.5: `a: 1 b: 2` at `1:6` and `a: 2024-01-01T99` at `1:14`. Positions are right in both, so this is a code change only, the same shape as the OML-25 row — and as with that row it means the reference has never met the pre-existing `date-then-non-time-suffix-is-date-plus-trailing-content` vector. The same is true of the two leftover tokens that could not begin a document, `a: 1 }` and `a: 1 ,`, both `parse.unexpected-token` at `1:6` — and on the first of those the reference's own message already reads "unexpected trailing content after the document body", so it names the condition correctly and reports the other code. OML-27's two cases are already correct: `a: { b: 1 c: 2 }` at `1:11` and `a: [1 2]` at `1:7`, both `parse.unexpected-token` | reported **satisfied** — all three implemented this ahead of the spec text that now states it, carried forward from the v0.19.0-beta sweeps rather than re-measured here (see below) | `parse.trailing-content` at top level, `parse.unexpected-token` inside `{...}` and `[...]` |
| **Merge-key order** ([YAML](formats/yaml.md)) | flattens a merge **sequence** in reverse, following PyYAML 6.0.3: `svc` reads `retries, region, name`, and the three-key collision shape reads `b, c, a` where the rule gives `a, b, c`. Values are right in every shape measured; only sequence order is wrong. The single-alias form, key-collision resolution, nested merges and repeated aliases all already match | **satisfied** — the port's `(path, code)` runner passes the vectors for this row | sequence (source) order |

**Why none of this surfaced until now.** The Python reference's conformance
runner compares **code-agnostically** (§8.5.2 rule 4) — legitimately, since
§8.1 does not yet make §8.3 mandatory. One row is invisible to it outright:
**OML-25**, where `ok` and every path already match and only the code is
wrong, so the vector reports a pass. That is how the reference came to fail
the `null: 1` vector's expectation for as long as that vector has existed
while its own suite stayed green. The rest are masked differently rather than
not at all — that runner also reports `skip` for any expected diagnostic
carrying no structured path, which is every `parse.codec-syntax` case it
produces today — and the D-21 and merge-order rows do fail loudly. The lesson
generalizes past these seven rows: **a code-agnostic runner passes vectors the
implementation does not really satisfy**, and a port should report which
comparison mode produced its numbers.

**These vectors are an E-20 "not yet implemented" skip, not an E-21 one.**
Eighteen vectors are new in v0.19.0-beta, three were corrected, and five more
are new in v0.20.0-beta for OML-26/OML-27; a port that
has not yet adopted the rules above may report the affected ones as `skip`
under E-20's **first** category, which requires no ledger citation of its
own. E-21's documented-divergence category — the one that MUST cite a ledger
entry by number — is for a capability a target language or design genuinely
cannot provide, and none of these rows is that. They are all rollout work on
a rule that landed, the same shape as `DIV-3`. This entry exists to record
what the work is, not to convert it into a permitted divergence, and a port
citing `DIV-4` as an E-21 reason is misreading it.

**The leftover-after-an-edge question is settled and now carries a rule
number.** omnist-spec#103 asked what a complete top-level edge followed by
unseparated content reports, and the answer — `parse.trailing-content` at top
level, `parse.unexpected-token` inside `{...}` or `[...]` — is
**OML-26/OML-27** as of v0.20.0-beta, with five vectors pinning it. It was
implemented by TypeScript, Go and Rust ahead of the spec text that now states
it, which is what the row above records; the Java port is reported to
implement it as well, but that has not been measured here and is not claimed
as one of the three. The Python reference does not implement it.

Remove this entry when every implementation satisfies all seven rows. Tracked
by omnist-spec#98, #99, #100, #101 and #103.

**DIV-5. No OSD writer escapes a label (OSD-15) or refuses an unwritable one
(OSD-14) yet.** Two rules, one surface, and only the first of them can be
pinned by a vector.

**OSD-15, canonical escaping.** [§5.9](05-osd-grammar.md#59-canonical-output)
listed what a canonical OSD writer emits and never said how a label is
escaped, though §5.3.1's weak unescaping makes the inverse exact: `\` is
written `\\`, `"` is written `\"`, nothing else is escaped. Measured live
against the Python reference (v0.9.5), whose `to_osd` escapes nothing:

| Label | What `to_osd` writes | What re-parsing it gives |
|---|---|---|
| `a\b` | `"a\b"` | **`ab`** — silent corruption, a different schema with no diagnostic |
| `a"b` | `"a"b"` | `parse.unterminated-string` |
| `a\"b` | `"a\"b"` | **`a"b`** — silent corruption |
| `a\` (ends in a backslash) | `"a\"` | `parse.unterminated-string` |

The silent-corruption rows are the reason this is a rule and not a style
note, and they are a **latent defect in the reference**, not a rollout gap
the spec created: the labels were always representable and were simply never
being written correctly. The four
`osd-grammar/canonical-output/label-*` vectors added in v0.20.0-beta pin it,
and the reference is red on all four. **The Go, Rust, TypeScript and Java OSD
writers were not measured for this** and nothing is claimed about them.

**OSD-14, the unwritable label.** [OSD-14](05-osd-grammar.md#59-canonical-output) is
new normative content as of **v0.20.0-beta**: a field label carrying a C0
control character has no OSD spelling at all (§5.3.1 bans the byte in a
string body, escape context included, and OSD unescaping is weak), so an OSD
writer handed such a schema MUST fail with `write.unsupported-value` rather
than emit text no conformant reader accepts. Measured behaviour today, and
only what was measured:

| Implementation | Behaviour |
|---|---|
| Python reference (v0.9.5) | `to_osd` emits the raw byte — `record R {`, newline, `    "a<U+0001>b": string,` — and the reference's own `parse_schema` then rejects what it wrote, `parse.control-character`. Run live, not assumed |
| Go | `osd.Write` emits a backslash plus the raw control byte, which its own reader now rejects, so write-then-read no longer round-trips; from the v0.19.0-beta sweep review ([omnist-go#118](https://github.com/omnist-dev/omnist-go/pull/118)) |
| TypeScript, Rust, Java | not measured |

**This half of the entry also records that the suite cannot express the
case.** A vector
gives a schema as OSD text (§8.5.3), so a schema whose label has no OSD text
cannot be written as a vector input at all, and §8.5.3 has no driver taking a
schema in any other form — `write_schema` is a documented operation
([§E.11](extensions/osd-oml.md#e11-api-cli-surface)) that the driver table and
the [Operations & Models Reference](operations-and-models-reference.md) both
omit. So OSD-14 ships as a rule with no vector behind it, which is exactly
the untestable-MUST shape omnist-spec#105 raises for D-14 on the read side;
both need the same thing, a vector input form that is not already-valid text
in the surface under test. Until that exists, adoption is verified by hand
against the two rows above and this entry says so rather than letting a green
suite imply coverage. Remove this entry when every port escapes labels per
OSD-15 and refuses the write per OSD-14, and a vector pins the second half.

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
