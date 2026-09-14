# Changelog

Versioning per [§10.3](docs/10-governance-and-versioning.md#103-versioning).
This file starts at v0.3.0-alpha; earlier history is in `git log`.

## v0.9.2-beta (2026-09-14)

**Editorial (patch)** — first batch of fixes from the whole-spec quality
audit ([#63](https://github.com/omnist-dev/omnist-spec/issues/63)-[#80](https://github.com/omnist-dev/omnist-spec/issues/80)).
Citation rot only; no normative rule changed, no implementation affected.

- **[#64](https://github.com/omnist-dev/omnist-spec/issues/64)**:
  `formats/json.md` documented `NaN`/`Infinity` as substitute-`null`-and-report,
  which [§8.3.8](docs/08-conformance-and-errors.md#838-format-codec-adjustments)
  had already superseded with unconditional `write.unsupported-value`. The
  conformance vector was updated when that rule changed; this prose was not,
  and the vector cited this page as its authority. Rewritten to match, and to
  cite §8.3.8 rather than restate its rationale.
- **[#67](https://github.com/omnist-dev/omnist-spec/issues/67)**:
  `formats/xml.md`'s "Parity gaps" section carried three stale claims — a
  retired `D-3` ledger citation, "per-port rollout is still in progress"
  (it completed), and "As of spec v0.1 ... Python, TypeScript, and Rust"
  (five ports, and the spec is at v0.9). **All five `formats/*.md` pages**
  were then swept for the same pattern, per the issue's own fix note:
  `toml.md` and `yaml.md` carried that identical stale sentence verbatim,
  and `json.md`/`oml.md` carried less brittle but still duplicated status
  claims. Every one now defers wholly to §9.3 and states no per-port status
  of its own, which is the only arrangement that cannot drift.
- **[#65](https://github.com/omnist-dev/omnist-spec/issues/65)**: the
  divergence ledger's entry IDs collided with chapter 2's Document-model
  rules — both were `D-N`, and `08-conformance-and-errors.md` used both
  meanings in one file. Ledger entries are now `DIV-N`; the convention and
  the reason are stated in [§9.4](docs/09-divergence-ledger.md#94-known-open-divergences),
  and `porting-a-conformance-runner.md`'s filing instruction updated. The two
  citations left dangling by deleted entries (`D-3` in §8.3.8, `D-7` in the
  porting guide) are resolved. §9.4 now also warns to check for inbound
  citations before deleting an entry, which is how both arose.

## v0.9.1-beta (2026-09-13)

**Tooling (patch)** — fixes a typo in v0.9.0-beta's own new
`osd-grammar/reserved-names/case-mismatched-name-is-not-reserved` vector:
its field label `x` was unquoted, which OSD text's grammar rejects
outright (labels are always quoted, [§5.4](docs/05-osd-grammar.md#54-records-and-fields)) —
the vector failed to parse at all, before ever reaching the case-sensitivity
check it existed to exercise. Found by the Python port (`omnist`) during
its v0.9.0-beta pin-bump verification. Fixed to `"x"`; spot-checked
against the Python reference parser, confirmed to now exercise the
intended check. No other vector in the file has this typo (checked via a
pattern scan of every vector's input text). Not a spec-content change —
the S-3/S-8 rules from v0.8.0-beta/v0.9.0-beta are unaffected.

## v0.9.0-beta (2026-09-13)

**Normative (minor)** — [OSD-OML](docs/extensions/osd-oml.md) bumped to
**v1.1**: E.5 through E.9 rewritten from documentation-style prose (closed
grammar + numbered, exhaustive rules replacing tables-plus-examples that
were never structurally guaranteed to be exhaustive — found to have real
gaps by simulating an implementor against them). Builds on v0.8.0-beta's
new Sec3.3 S-8.

- **New code `schema.invalid-name`** (R-3a): a `record.name` or ref-branch
  `type.name` MUST satisfy S-8's `Name` domain. Closes a real hole: OSD-OML
  could construct a `Schema` (e.g. a record named `"My Record!"`) with no
  possible OSD-text representation at all, since OSD's `name` token cannot
  tokenize outside that domain and nothing previously stopped OSD-OML from
  producing one.
- **New rule, no prior code assigned**: `nullable: false` explicitly
  present (R-13) now reuses `schema.invalid-type` — previously this input
  had no stated outcome at all, not even an unstated one.
- **New rule**: `type.kind` outside `scalar`/`ref`/`any` (R-11) now reuses
  `schema.invalid-type` — same gap as `nullable: false`, no code existed
  for this input before.
- **`nullable` on a `ref-node`/`any-node`** (R-14/R-15) is now explicit
  `schema.unknown-key`, enforcing Sec3.3 S-7 structurally via the grammar's
  own closed key sets rather than a separate semantic check that E.10
  never actually listed.
- **New path-kind assignment** (R-21/R-22): `schema.missing-key`,
  `schema.invalid-type`, `schema.unknown-key`, and `schema.invalid-name`
  now explicitly use a Document path; every other reachable `schema.*`
  code keeps Schema path, unchanged. [§8.4](docs/08-conformance-and-errors.md#84-paths)
  previously allowed either without saying which applied where.
- **Canonical `schema_to_document` output** (E.8) now states one general
  "omit at default" rule instead of per-field special cases — codifies
  behavior two existing vectors already tested individually without
  either stating the general rule they were both instances of.

5 new conformance vectors added to `test-suite/extensions-osd-oml/`
covering the above. No port implements OSD-OML yet (per
[§9.6](docs/09-divergence-ledger.md#96-extension-support)), so every new
vector reports as a skip everywhere, same as the existing 24 — no port
behavior change, no port version bump required by this release.

## v0.8.0-beta (2026-09-13)

**Normative (minor)** — two Core gaps surfaced while reviewing OSD-OML's
formal rigor (extension chapters had been drifting toward
documentation-style prose instead of the closed-grammar/numbered-rule
style [§3.3](docs/03-schema-model.md#33-formal-definition)/[§5](docs/05-osd-grammar.md)
already use; auditing against that standard found these):

- **New [§3.3](docs/03-schema-model.md#33-formal-definition) S-8**: a
  `Name` (record name, or a `Ref`'s target) MUST match
  `[A-Za-z_][A-Za-z0-9_]*`. Previously enforced only implicitly by OSD
  text's own tokenizer — never stated as a model-level rule, so never
  available for a new syntax surface (OSD-OML) to inherit. No behavior
  change for OSD text (its grammar already enforced this structurally);
  closes a real gap for OSD-OML, addressed separately.
- **[§3.3](docs/03-schema-model.md#33-formal-definition) S-3 clarified**:
  the reserved-name check is exact and case-sensitive. Previously
  unstated. Characterization only — verified against all five ports'
  source before landing; all five already agree independently. New
  vector: `osd-grammar/reserved-names/case-mismatched-name-is-not-reserved`.

No implementation behavior change required by either item.

## v0.7.0-beta (2026-09-13)

**Normative (minor)** — closes [omnist-spec#54](https://github.com/omnist-dev/omnist-spec/issues/54):
the four OSD-OML operations added in v0.6.0-beta (`schema_from_document`,
`parse_schema_oml`, `schema_to_document`, `write_schema_oml`) had no
registered comparison semantics in [§8.5.3](docs/08-conformance-and-errors.md#853-operation-drivers) —
nothing guaranteed a harness would actually verify the declaration-order
behavior their own vectors encoded. Registered all four: the two
Schema-producing operations compare byte-for-byte as canonical OSD text,
matching `normalize`/`prune`'s existing rule; the two Document-producing
operations compare as a Document, order-sensitive per D-1/D-3. Also
extends `parse_schema`'s vector shape with an optional `schema` field
(byte-for-byte) for vectors specifically pinning round-trip fidelity
rather than mere acceptance.

Adds the Core-level conformance vectors this enables and that were
missing since v0.6.0-beta's canonical-serialization-order principles
landed: a `parse_schema` declaration-order round-trip
(`osd-grammar/canonical-output/declaration-order-round-trips-exactly`), a
`prune` survivor-order vector, and a `normalize` alphabetical-order vector
using a genuine forced-merge case where declaration order and alphabetical
order disagree. All three are characterization vectors (§10.2) — verified
green against the Python reference before being written, not new
behavior.

## v0.6.0-beta (2026-09-12)

**Normative (minor)** — introduces an **Extensions** mechanism: optional
capabilities built entirely on Core, versioned and reported independently
of Core conformance ([Extensions overview](docs/extensions/overview.md)).
No implementation is required to support any extension to remain
Core-conformant.

Ships the first extension, **OSD-OML**
([docs/extensions/osd-oml.md](docs/extensions/osd-oml.md)): a
Document-shaped, OML-syntax peer to OSD text for representing a Schema.
Adds `schema_from_document`, `parse_schema_oml`, `schema_to_document`, and
`write_schema_oml` to the API surface, and `--from`/`--to osd|osd-oml` to
every schema-consuming and schema-producing CLI command. `osd` remains the
unconditional default; the extension is opt-in and changes no existing
behavior. Three new error codes (`schema.missing-key`, `schema.invalid-type`,
`schema.unknown-key`), defined in [§8.3.3](docs/08-conformance-and-errors.md#833-schema-schema-well-formedness)
as general Schema-construction rules rather than owned by the extension,
cover checks reachable only through OSD-OML's generic OML input, since
OSD's own grammar makes them structurally impossible in OSD text.
`schema.unknown-type`'s definition is widened to explicitly cover an
invalid scalar name, not only a dangling reference — the same failure,
now stated once for both cases instead of two.

Also formalizes **canonical serialization order**
([§3.3](docs/03-schema-model.md#33-formal-definition)), closing a gap that
predates this release: `env` was always a set (order semantically
irrelevant), but no chapter ever specified what order a *writer* emits —
an omission first exposed by OSD-OML's own round-trip vectors. Five
principles, plus a determinism requirement, now govern every
Schema-producing operation, Core or extension: read-side operations and
`prune` preserve real order (declaration order, or a filtered subset of
it); `normalize` (and `extract`, which is defined in terms of it) fall
back to alphabetical order where merging has destroyed any single
"original" position; `infer` preserves sample-encounter order, per its
own existing pseudocode. Verified against all 5 ports' source before
writing this down: every rule was already true, deliberately, wherever
checked — this costs no implementation changes. [§5.9](docs/05-osd-grammar.md#59-canonical-output)'s
existing byte-identical-output claim is narrowed to what is actually true
and guaranteed: two implementations parsing the *same* source and writing
it back agree byte-for-byte; this does not extend to two different texts
(OSD vs. OSD-OML) describing the same schema, which MAY legitimately
differ.

Extensions also gain a **versioning policy**
([Extensions overview](docs/extensions/overview.md)) — a reusable,
Core-§10.3-shaped bump table, and a rule that an extension MAY declare a
dependency on another extension's minimum version — and a
[§9.6](docs/09-divergence-ledger.md#96-extension-support) divergence-ledger
table tracking per-implementation extension adoption, separate from Core
conformance.

## v0.5.0-beta (2026-08-30)

**Normative (minor)** — a systematic spec-correctness audit (two
techniques: adversarial-collision testing on already-shipped codec
writers, and checking for grammar productions referenced by name but
never formally defined) found and fixed 11 real defects:

- §8.3.8: illegal-character labels, unrepresentable TOML nulls,
  NaN/Infinity, and empty internal XML nodes now fail the write
  outright (`write.unsupported-value`), unconditionally — previously
  silently substituted/dropped with only a warning, which could make
  two genuinely different, independently-valid inputs collide into
  identical output with no diagnostic. Retires `format.key-sanitized`,
  `format.string-illegal-char`, `format.null-unrepresentable`,
  `format.float-special`, `format.shape-empty-ambiguous`.
- §8.3.8 / XML: a `\r` byte is now escaped as `&#13;` on write instead
  of written raw — XML's mandatory line-ending normalization made a
  raw `\r` and a raw `\n` indistinguishable on read-back; the numeric
  character reference survives intact. Retires
  `format.string-cr-normalized` (a genuine fix, not a new failure
  case).
- §4.2.3: `NUMBER`/`INTEGER` literals with a leading zero (`01`, `00.5`)
  are now rejected (`parse.leading-zero`) — this lexical grammar was
  referenced by name but never formally defined anywhere in the spec.
- §4.2.4: `DATE`/`TIME`/`DATETIME`/`tz-offset` calendar and clock
  ranges are now normative (month 01-12, day valid for month/leap
  year, hour/minute/second in range, no leap-second spelling, tz-offset
  sharing `TIME`'s exact minute range) — also undefined before this.
  Closes a real collision: a 60-minute tz-offset (`+00:60`) was
  previously indistinguishable from a valid `+01:00` once silently
  normalized instead of rejected.
- §5.4/§5.5: `[0,0]` cardinality, an empty-string field label, and a
  field label containing `[`/`]` are all now rejected at
  schema-construction time — each was either a redundant second
  spelling for "undeclared" or (for brackets) could collide with
  §3.6.1's repeated-label diagnostic-path convention.
- §8.5.3: a harness comparing a `write` vector's text for XML MUST now
  strip insignificant inter-tag whitespace before comparing — the spec
  places no requirement on XML writer whitespace, so a byte-exact
  vector was accidentally pinning one implementation's formatting
  choice as if it were normative.

**Patch** — two prose corrections (§3.4 no longer contradicts the
`[0,0]` rule; §7.4 no longer cites a `format.adjustment.*` family that
was never real) and two test-suite vector fixes found during port
rollout of the above (a `prune` fixture that depended on now-illegal
`[0,0]` syntax; a temporal vector's expected value missing seconds
canonicalization, invisible to a semantic-equality harness but wrong
for a string-backed one).

All 9 behavioral fixes above were implemented and merged across all 5
ports (Python, TypeScript, Rust, Go, Java) the same day — see
[§9.3](docs/09-divergence-ledger.md#93-current-status) for current
per-port versions and conformance counts.

## v0.4.0-beta (2026-08-23)

**Normative (minor)**

- §5.8: a schema with more than one `root` declaration is now an error
  (`schema.duplicate-root`), closing D-2 — previously implementation-
  defined (Python silently let the later one win).
- §8.3.8: `format.attribute-dropped`, `format.namespace-dropped` (XML
  read), and `format.interleaving-lost` (JSON-family write) MUST now be
  emitted, closing D-3 — previously dropped with no diagnostic at all.

**First beta.** [§9.4](docs/09-divergence-ledger.md#94-known-open-divergences)
has no open entries for the first time: D-2 and D-3 (above) are closed,
and D-10 (the OSD-lexer `parse.*` code migration) finished rolling out
across all five ports this same day. Two independent from-scratch ports
(Go, Java) have already been built against this spec with every gap
treated as a defect and fixed here rather than worked around — the
condition this project has used informally as its alpha exit bar. Beta
means: no known churn, not that churn is impossible — a new gap found by
a future port is still a real spec defect and still gets fixed, the same
process as ever.

## v0.3.0-alpha (2026-08-23)

**Normative (minor)**

- §5.3.1: a literal control character below U+0020 inside an OSD string is
  now an error (`parse.control-character`), matching OML's existing rule —
  previously unspecified.
- §8.3.1: `parse.*` codes now explicitly cover OSD's own lexical stage, not
  just OML's — previously no code family existed for a raw OSD
  tokenizer/syntax error.
- §6.8: `local_signature` formally defined (was referenced but never
  specified, `equivalence_classes`' de-duplication rule).
- §8.3.8: `format.*` table completed — 6 codes that §8.1 had promised but
  never actually added.

**Editorial (patch, bundled into this release rather than tagged
separately)**

- §8, §9: full rewrite for conciseness — cut narrative/audit-trail prose
  throughout, especially §9.3's status table and §9.4's known-divergences
  list (7 of 9 entries were long-resolved but kept as growing historical
  paragraphs; removed entirely, resolution lives in each port's own issue
  history).
- §9.3 and `docs/index.md` no longer duplicate the same Implementations
  table — `docs/index.md` now links out instead of maintaining a second
  copy that goes stale independently.
- Fixed 7 long-broken internal links (anchor-slug mismatches) and 2
  genuinely 404ing external links (`grammars/*.abnf`, now pointed at
  GitHub blob URLs instead of an unreachable relative path).
- `conformance-harness.md` corrected from a stale "Python-only" scope
  note — all five current implementations have this track today.

**Not yet promoted to beta.** Two divergences remain genuinely open
([§9.4](docs/09-divergence-ledger.md#94-known-open-divergences) D-2, D-3),
and the §8.3.1 code migration (D-10) is still an in-progress per-port
rollout. This audit pass itself found two new normative gaps in the space
of one session (D-10, the control-character rule) — real churn is still
low but nonzero, which is the signal beta is meant to represent the
absence of.
