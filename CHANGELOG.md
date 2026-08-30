# Changelog

Versioning per [§10.3](docs/10-governance-and-versioning.md#103-versioning).
This file starts at v0.3.0-alpha; earlier history is in `git log`.

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
