# Changelog

Versioning per [§10.3](docs/10-governance-and-versioning.md#103-versioning).
This file starts at v0.3.0-alpha; earlier history is in `git log`.

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
