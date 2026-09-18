# Changelog

Versioning per [§10.3](docs/10-governance-and-versioning.md#103-versioning).
This file starts at v0.3.0-alpha; earlier history is in `git log`.

## v0.18.0-beta (2026-09-18)

**Normative (minor)** — closes
[#75](https://github.com/omnist-dev/omnist-spec/issues/75). **Every
implementation shipping a YAML codec needs a change.** Nothing else does.

- **New D-18: a codec for a format with an anchor/reference mechanism MUST
  bound each anchored definition's expansion factor.** For an anchored
  definition `a`, `W(a)` is the value slots materialized when `a` is expanded
  (a container counts, a scalar leaf counts, a reference inside `a`
  contributes its target's full `W`, recursively), `S(a)` is the slots
  written in `a`'s own definition (a reference counting as exactly one,
  whatever it points at), and `E(a) = W(a)/S(a)`. Input where any `E(a)`
  exceeds the configured maximum MUST be rejected with the new
  `document.limit.alias-expansion` code. Reference default **50**.
  **D-19** requires the check *before* the expansion is materialized — `W`
  and `S` come from the raw reference graph in time linear in input size, so
  an over-limit input costs nothing to refuse. **D-20** rejects a
  self-referential anchor, whose `W` is unbounded.
- **Why this was needed.** §2.4 bounded the *result* — depth, node count,
  integer digits — and nothing bounded the *ratio* between what an input
  writes and what reading it materializes. A sub-1 KB YAML document of
  nested anchors lands under the million-node cap, is accepted with no
  diagnostic at roughly 600× amplification, and can be replayed
  indefinitely. No limit is crossed, so no implementation was
  non-conformant while it happened.
- **The threshold is calibrated against `E` itself, measured.** This is the
  third attempt at #75 and the first that measures the quantity it
  specifies; both earlier drafts were withdrawn for calibrating against
  input bytes or against edge counts rather than the thing being limited.
  Measured against the reference: a `<<: *defaults` merge-key config of the
  docker-compose/GitLab-CI kind reads **`E = 1.00` at every size tested, up
  to 36 KB** (a merge key flattens into the referring mapping instead of
  nesting a copy under it), the worst legitimate document measured — anchor
  chains, scalar-constant reuse — reads **5.75**, and the amplifying shape
  turns dangerous around **`E = 170`**. 50 is ~9× above the worst legitimate
  reading and ~3.4× below the weakest dangerous one.
- **The scope is conditional, and stated as such in three places.** D-18 is
  **not** a fourth universal limit: §2.4's first three rows bind every
  Document however it was built, D-18 binds a *codec that has* an
  anchor/reference mechanism. Among the five formats this spec covers, only
  YAML has one today; a Document built programmatically has no anchors and
  no byte count, so neither of the failure modes that sank the previous
  drafts (division by zero, route ambiguity) exists here. §9.2 says the same
  in its own words, and E-4a pins the reach of the new code.
- **XML's entity expansion is deliberately not re-handled.** It is the same
  hazard — "billion laughs" is an XML attack first — but the data-XML
  profile already rejects a DTD outright, which is stricter than this bound.
  §2.4.1 cross-references it rather than adding a second mechanism.
- **`docs/formats/yaml.md` now states the read-side obligation.** It
  previously treated aliases purely as a value-fidelity question — two
  independent edges both carrying the value — which is exactly the property
  that makes an anchor an amplifier, and it never said so.
- **Five vectors** in `test-suite/formats-yaml/alias-expansion.json`: a
  nested fan-out rejected at `E = 68.20` against a declared 50, a merge-key
  config accepted at `E = 1.00`, an anchor-to-anchor chain accepted at
  `E = 1.67`, and an at-limit/one-past pair on byte-identical input pinning
  that D-18 rejects when `E` *exceeds* the maximum, not when it reaches it.
  The three accepted documents were captured live from the reference. The
  rejected one is accepted by every implementation today, by design — that
  is the defect. 230 vectors total.
- **Port impact is unverified and no port issues are filed yet.** YAML
  libraries differ substantially in native alias handling, so which ports
  need what follows from a per-port check against D-18 now that the spec
  position is settled.

## v0.17.0-beta (2026-09-14)

**Normative (minor)** — closes
[#78](https://github.com/omnist-dev/omnist-spec/issues/78) and
[#93](https://github.com/omnist-dev/omnist-spec/issues/93). This is the
intended freeze point for the quality audit: every normative chapter now has
full rule coverage, enforced in CI. **JSON, TOML and OSD readers need a
change, and every writer does.**

- **New D-15: a leading byte-order mark MUST be stripped, on every surface.**
  Previously left unsettled because a first draft would have made the
  reference non-conformant. Settling it uniformly rather than per-surface,
  for two reasons. A BOM carries no data — it is meaningless for UTF-8, which
  has no byte-order ambiguity to mark — so treating it as content anywhere is
  wrong, and treating it as content on *some* surfaces is how two
  implementations build different Documents from one file. And it overrides
  nothing: RFC 8259 §8.1 explicitly permits a JSON parser to "ignore the
  presence of a byte order mark rather than treating it as an error". TOML is
  the one surface where the rule goes past the format's own specification:
  TOML v1.0.0 has no BOM provision at all, and its ABNF gives `U+FEFF` no
  position, so stripping there is a deliberate Omnist choice for uniformity.
  Measured before this rule, the reference stripped a BOM for OML and XML and
  rejected it for JSON, TOML **and OSD** (`parse_schema` raised
  `parse.unexpected-token`). Both ABNF grammars now admit `%xFEFF` at offset
  zero and nowhere else. D-15 also binds writers: a conformant writer MUST
  NOT emit a leading BOM on any surface, so the rule cannot produce
  byte-level divergence between ports. Three new vectors (JSON, TOML, OSD),
  currently red against the reference by design.
- **Chapters 2 and 3 have complete rule spines.** They already had `D-1..D-5`
  and `S-1..S-8`, but normative paragraphs sat outside them — invisible until
  `check_rule_coverage.py` existed. Now `D-6..D-17` and `S-9..S-21`.
  Existing numbers were left untouched, since `D-1..D-5` are cited from four
  other files; new rules were appended rather than renumbering. `D-17` is the
  §2.3 wrapper sentence itself ("a conformant implementation MUST maintain
  all of the following"), restored with its MUST rather than left as
  non-normative framing — `D-5` carried no MUST of its own and depended on
  it. `S-21` is `infer`'s `any`-emission requirement, previously a table row
  the checker's original table-skipping heuristic couldn't see; the checker
  was fixed to scan table cells generally, not just to carve out this one
  row.
- **§3.3's five canonical-order principles are individually citable as
  `S-9..S-13`.** They were numbered `1.`–`5.` locally while chapter 6's `A-3`,
  `A-9` and `A-18` explicitly inherit from them — load-bearing for another
  chapter's rules while unreachable by number.
- **Three paragraphs were *not* numbered, deliberately.** Mechanical numbering
  would have manufactured rules out of framing text. The depth-limit
  elaboration now reads "On depth (D-12, elaborated)"; the `any`-name
  restriction now cites `S-3` rather than restating it; and §3.3's
  principle-application paragraph cites the `A-` rules it explains. (The
  sentence introducing `D-1..D-5` was initially left unnumbered with its
  MUST removed, on the theory that it was a redundant wrapper — that turned
  out to be wrong, since `D-5` has no MUST of its own; it is `D-17` above,
  not on this list.)
- **All seven normative chapters are now enforced** by
  `tools/check_rule_coverage.py` in CI, with no reported-but-unenforced set
  remaining.

## v0.16.0-beta (2026-09-14)

**Editorial (minor)** — closes
[#63](https://github.com/omnist-dev/omnist-spec/issues/63), the largest
finding of the quality audit. No requirement changed meaning; every one
became citable, and CI now keeps it that way.

- **The remaining four chapters have rule spines**: `OML-1`..`OML-24`
  (chapter 4), `OSD-1`..`OSD-13` (chapter 5), `C-1`..`C-8` (chapter 7),
  `E-1`..`E-22` (chapter 8). With chapter 6's `A-1`..`A-23` from
  v0.15.2-beta, all ~98 previously-unanchored MUST-level requirements now
  have numbers, matching §2.3's `D-` and §3.3's `S-` conventions.
- **Numbered in place**, as in chapter 6, rather than gathered into per-chapter
  tables — a consolidated list would be a second copy free to drift from the
  prose it summarises.
- **New `tools/check_rule_coverage.py`, wired into CI.** It fails the build if
  any normative paragraph in chapters 4–8 lacks a rule number, so the spine
  cannot silently rot the way the citations did. Verified in both directions:
  removing one rule number fails with the file and line, restoring it passes.
- **It immediately found more.** Chapters 2 and 3 already had `D-` and `S-`
  spines, but the checker shows **12 and 10 normative paragraphs respectively
  sitting outside them** — §2.4's limit prose and §3.3's canonical-order
  principles among them. Those two chapters are reported but not enforced for
  now; extending the spine to cover them is follow-up work, and #63 is
  reopened for it rather than the gap going unrecorded.

## v0.15.2-beta (2026-09-14)

**Editorial (patch)** — first instalment of
[#63](https://github.com/omnist-dev/omnist-spec/issues/63). No requirement
changed meaning; every one of them became citable.

- **Chapter 6's normative requirements are now numbered `A-1` through
  `A-23`**, in document order, matching §2.3's `D-` rules and §3.3's `S-`
  rules. Chapter 6 was the worst case the audit found: the largest chapter,
  the most MUSTs, the operations where silent cross-implementation
  divergence is most likely, and not one anchor anyone could cite. Rules an
  implementor can now point at in review include `A-2` (deterministic `env`
  iteration), `A-7` (no structural shortcut for `equivalent`), `A-8`
  (sort-then-minimum representative choice), `A-12` (never relax a deleted
  field to optional), `A-19` (`lint` must not mutate) and `A-20`
  (`any-field` must not by itself cause a non-zero exit).
- **Numbered in place, not gathered into a table.** A consolidated list would
  skim better but would be a second copy of every requirement, free to drift
  from the prose it summarises — the exact failure mode behind several
  findings in this audit, including the glossary duplication fixed in
  v0.15.1-beta. Rule and rationale stay together.
- Verified by construction: after numbering, every `MUST`/`SHALL` line in the
  chapter either carries a rule number or is a continuation line of one.

Chapters 4, 5, 7 and 8 still have no rule spine; #63 stays open for them.

## v0.15.1-beta (2026-09-14)

**Editorial (patch)** — closes
[#70](https://github.com/omnist-dev/omnist-spec/issues/70) and
[#79](https://github.com/omnist-dev/omnist-spec/issues/79). No normative
rule changes except the first item, which pins behavior all implementations
already had.

- **§5.5: a leading `+` in a cardinality bound is a syntax error**, unlike
  `-`. The `-` case was addressed with care and `+` was never mentioned,
  leaving three defensible readings — reject at the token boundary, accept
  then reject at construction, or accept and silently normalize — of which
  the third differs *observably*. Verified against the reference: `[+1]` and
  `[--1]` both raise `parse.unexpected-token` while `[-1]` correctly raises
  `schema.invalid-cardinality`.
- **The glossary no longer restates §6.4's satisfiability rule.** It carried
  a near-verbatim second copy of the propagation rule and the fixpoint note;
  it now gives the one-line intuition and cites §6.4 as normative, so the two
  cannot drift apart.
- **The reading order is split by audience.** All ten chapters were listed
  uniformly, with no signal that 8 through 10 are implementor and maintainer
  material — "Passing the test suite" reads like homework to someone who
  just wants to model data. Now split into *using Omnist* and *implementing
  a port*, with the two questions newcomers ask first — optional versus
  nullable, and string-or-number — linked directly to the sections that
  answer them.
- **The `validate.*` codes are now actionable.** They are the codes a user
  meets most often, and each was a one-line table entry with no guidance on
  what to do. Added a non-normative "usually means" table and a note on the
  two most often confused, `null-not-allowed` and `cardinality`, pointing at
  §3.5.

## v0.15.0-beta (2026-09-14)

**Normative (minor)** — closes
[#77](https://github.com/omnist-dev/omnist-spec/issues/77) and
[#87](https://github.com/omnist-dev/omnist-spec/issues/87); partially
addresses [#78](https://github.com/omnist-dev/omnist-spec/issues/78).

- **`grammars/osd.abnf` and §5.3.1 no longer disagree** (#77). The escape
  alternative admitted an escaped control character the prose forbids, so a
  parser generated from the grammar and one written from the prose disagreed
  on the same bytes. The grammar now excludes `%x00-1F` there, and the prose
  says "raw" rather than "literal" and states that the ban covers escape
  context.
- **`parse.codec-syntax` registered** (#87). Malformed JSON, YAML, TOML or
  XML had no code at all, so the reference invented an unregistered
  `parse.syntax` used at nine sites. One code covers all four formats
  deliberately — splitting it per format adds three codes conveying nothing
  the message does not, and nothing branches on which codec failed. §8.3.1
  now also states the distinction from §8.3.8's refusal codes: malformed
  input versus well-formed input outside the supported profile.
- **New §2.5, Encoding** (#78, partial). Input MUST be valid UTF-8, with
  silent `U+FFFD` repair forbidden — new code `parse.invalid-encoding`, where
  the reference previously raised a bare `UnicodeDecodeError` outside the
  taxonomy entirely. And **labels compare byte-wise, never by Unicode
  normalization**: `café` written as `U+00E9` and as `e` plus `U+0301` are
  two distinct labels.

**Two things were pulled from this release after review.** Both are recorded
here rather than quietly dropped, because the reasoning matters more than the
outcome.

**The expansion-ratio limit (#75) was withdrawn.** It would have added a
fourth §2.4 limit, capping nodes materialized per input byte at 10. Review
found the rule undefined in its central term: §2.2 and the reference count
**containers only** — a scalar leaf is a *value*, not a *node*, pinned by the
existing `node-count-at-declared-limit-succeeds` vector — while the threshold
had been calibrated by counting every edge target. On identical bytes the two
readings differ by roughly 1000×. Under the spec's own definition the alias
bomb measures 0.048 nodes per byte, so the proposed limit **would never have
fired on the attack it was designed to stop**, while realistic anchored
configs — the docker-compose and GitLab-CI merge-key idiom — exceed 10 under
the other reading and would have been wrongly rejected. #75 stays open: the
defect is real, but this was not the fix.

**BOM handling (#78) is explicitly left unsettled.** A first draft required a
leading `U+FEFF` to be stripped on every text surface. Measured against the
reference, OML and XML accept one while JSON and TOML reject it, so the rule
would have made the reference non-conformant in two places — and neither ABNF
grammar admits `%xFEFF`, which would have recreated the exact
grammar-versus-prose split #77 exists to close. §2.5 now says so openly
instead of guessing.

## v0.14.0-beta (2026-09-14)

**Normative (minor)** — closes
[#76](https://github.com/omnist-dev/omnist-spec/issues/76), partially
addresses [#87](https://github.com/omnist-dev/omnist-spec/issues/87).
**All five ports need changes.**

- **New: the data-XML profile** ([XML](docs/formats/xml.md#the-data-xml-profile)).
  The spec described how XML maps to Documents but never said *what XML it
  accepts*, so each port drew its own line and they disagreed — two refused
  `DOCTYPE`-bearing documents, two silently skipped the declaration, one
  accepted it. That is the "grammar acceptance" variation §9.2 forbids,
  live across five implementations. The profile now states what is supported
  positively, and requires everything outside it to be **refused, not
  ignored**: any `DOCTYPE` declaration, entity references beyond XML's five
  predefined, and mixed content.
- **Refuse on sight, not on use.** A `DOCTYPE` must fail when encountered,
  not later if an entity it defines is referenced — so a document that
  declares entities and never uses them is still refused. This keeps the
  failure early and testable rather than conditional on content.
- **Three new `format.*` codes**: `format.dtd-forbidden`,
  `format.entity-forbidden`, `format.mixed-content`. All `error` severity.
  §8.3.8 now notes these are read-side *refusals*, unlike the rest of that
  table, and that they MUST NOT be reported as syntax errors — the documents
  are well-formed XML, and saying otherwise sends users hunting for a defect
  in a valid file.
- **The concept already existed, unnamed.** The Python reference has been
  rejecting mixed content with the message "outside the data-XML profile"
  while the spec defined no such profile, no vector tested it, and the code
  it reported was unregistered.
- **Three new vectors**, currently reported as skips by ports that raise
  unstructured syntax errors for these cases — red-before-green per §10.2.

Security note, recorded accurately: the original issue claimed a faithful
implementor "ships XXE". That is **not true of any current port** — the two
libraries capable of external entity resolution (Python's stdlib, Java's
`javax`) are both already hardened, and the other three never perform I/O
while parsing. The real defect was the conformance divergence, not a live
vulnerability.

## v0.13.0-beta (2026-09-14)

**Normative (minor)** — closes
[#83](https://github.com/omnist-dev/omnist-spec/issues/83). Corrects a false
justification, states a requirement that was only ever implied, and closes
the CI hole that let citation rot accumulate in the first place.

- **§3.4's justification for `max = 0` was wrong.** It claimed the value
  "can arise as a derived value — an intermediate result of algebra
  operations that narrow a cardinality range". No such operation exists:
  chapter 6 has no intersection, meet, or range-narrowing operation, and
  `max = 0` is consumed in three places and produced in none. The real and
  only route is direct programmatic construction, which is now stated. Also
  recorded: no conformance vector can reach `prune`'s `max = 0` rule, since
  every vector supplies schemas as OSD text and OSD text cannot express
  `[0,0]` — the rule is normative but unverifiable through the suite.
- **New in §3.3: the `S-*` constraints govern a Schema however it was
  built** — parsed from OSD, parsed from OSD-OML, produced by an algebra
  operation, or constructed programmatically. This mirrors how
  [§2.4](docs/02-document-model.md#24-safety-limits) already treats a
  Document builder as a peer of the OML parser. Implementations MUST enforce
  S-1 through S-8 at construction rather than relying on their parsers to
  have made violations unreachable.
- **⚠️ That requirement has already found a real bug.** The Python
  reference enforces S-1, S-3, S-5 and S-6 at construction but **not S-8**,
  so a Schema can be built whose canonical OSD output cannot be parsed back
  — violating §5.9's definition of a canonical writer. Filed as
  [omnist#344](https://github.com/omnist-dev/omnist/issues/344). The other
  four ports are unverified and should be checked during the next pin sweep.
- **CI now builds the docs at all, and validates anchors.** Two separate
  holes, both found by review after a first draft of this entry wrongly
  claimed the gate was already active:
    - **Nothing in CI built the documentation.** `check.yml` ran only the
      version check; `docs.yml` runs `mkdocs gh-deploy` — no `--strict` —
      and only on push to `master`, i.e. after merge. A broken build reached
      the published site before anything complained. A `docs-build` job now
      runs `mkdocs build --strict` on every pull request.
    - **`mkdocs` does not validate anchors by default**, so every `#anchor`
      went unchecked; a broken one was reported as INFO and passed. This is
      the root cause of the citation rot fixed in v0.9.2-beta.
      `validation.links.anchors` is now on, verified to abort the build on a
      deliberately broken anchor. Its limit is worth knowing: it catches
      markdown links carrying an anchor, not bare prose citations like
      "see §6.3" — which is exactly how a wrong-section reference in this
      change's own first draft slipped past.
- **New `tools/check_vectors.py`, wired into CI.** Nothing parsed
  `test-suite/` before this. A vector was nearly committed during the audit
  with a literal `U+0001` byte inside a JSON string, which RFC 8259 forbids
  and which would have broken every port's vector reader while this repo's
  CI stayed green. The script checks strict-JSON validity, raw control
  characters (reporting the line), duplicate vector names, and required
  fields — and is verified to fail on that exact byte.

## v0.12.0-beta (2026-09-14)

**Normative (minor)** — eight conformance vectors closing coverage gaps found
by the audit, where a wrong implementation passed the whole suite. No spec
prose changed; no implementation behavior changes. Closes
[#72](https://github.com/omnist-dev/omnist-spec/issues/72),
[#73](https://github.com/omnist-dev/omnist-spec/issues/73),
[#74](https://github.com/omnist-dev/omnist-spec/issues/74),
[#80](https://github.com/omnist-dev/omnist-spec/issues/80).

- **`normalize`'s refinement fixpoint had no test at all** (#72). All three
  existing vectors merge on the first pass, so an implementation that groups
  by local signature once and skips refinement entirely passed. The new
  `ref-targets-in-different-blocks-block-the-merge` requires a second round.
  Two more pin the discrimination §6.8's own prose warns about — records
  differing only by scalar kind, and only by nullability, must not merge.
- **`extract` step 5's "mandatory or not" ref-drop** (#73) had no vector; all
  four existing ones exercise step 3's mandatory-only propagation. A
  plausible misreading emits a schema with a dangling `Ref` that S-6 says
  cannot exist, and passed conformance.
- **`equivalent` coverage** (#80): same-language schemas differing in record
  *count*, and differing in *declared field set* (an optional field whose
  target is unsatisfiable, so it can never be emitted). The second is the one
  most likely to be got wrong — comparing declared field sets is
  reasonable-looking and returns the wrong answer. A negative-boundary vector
  makes the same target satisfiable so the answer flips.
- **§8.3.8 MUST-fail conditions** (#74): one genuine gap, not the three
  originally reported. The `key-sanitized` and `shape-empty-ambiguous`
  conditions were already covered — the original grep searched for the
  `format.*` code names, which correctly appear nowhere, since §8.3.8 says
  all five emit `write.unsupported-value`. Added the one real gap, a C0
  control character in a string written to XML. See the issue for the
  correction.

## v0.11.0-beta (2026-09-14)

**Normative (minor)** — three rules the spec relied on but never stated,
from the quality audit. Closes
[#66](https://github.com/omnist-dev/omnist-spec/issues/66),
[#68](https://github.com/omnist-dev/omnist-spec/issues/68),
[#69](https://github.com/omnist-dev/omnist-spec/issues/69).

**⚠️ One existing vector's encoding changes — ports must re-verify.** See
§8.5.4 below. Every other change here is prose or additive.

- **New [§4.9](docs/04-oml-grammar.md#49-canonical-output), OML canonical
  output.** `osd-oml.md` cited "§4.9" for OML's compact-mode round-trip
  guarantee; chapter 4 ended at §4.8 and made no such guarantee anywhere, so
  the citation pointed at a rule that was never written. Chapter 4 had no
  canonical-output section at all, while OSD has §5.9 — its writer rules were
  scattered across §4.4 and §4.5 with no round-trip guarantee. §4.9
  consolidates them and pins two previously unstated things: **canonical
  output uses repeated labels, never array sugar** (§4.3.1 makes both parse
  to the same Document, so a canonical form must choose, and two conformant
  writers could otherwise disagree on bytes — which §9.2 forbids); and the
  byte-identical guarantee is **stronger for OML than for OSD**, because
  OML's syntax is the Document model and edge order is data, so there is no
  separate declaration order to preserve. Compact mode is now defined as
  *single-line* rather than merely unindented — a writer keeping newlines but
  dropping indentation produces a third layout, which is not canonical — and
  its round-trip guarantee is split into the two distinct claims it was
  conflating: parsing compact output yields an equal Document, and re-writing
  that Document compactly reproduces the same bytes. New vector
  `formats-oml/canonical-output/repeated-labels-never-array-sugar` pins the
  array-sugar rule, which #66 asked be tested rather than left honor-system.
- **New [§8.4.1](docs/08-conformance-and-errors.md#841-which-kind-each-schema-code-uses),
  path-kind per `schema.*` code.** §8.4 allowed "a Document or Schema path"
  without saying which applied where, leaving a byte-compared value
  unspecified. The rule existed but lived in the OSD-OML extension as
  R-21/R-22, flagged provisional when written. It is a property of the codes,
  not of the extension that first reached them, so it now lives in Core and
  the extension cites it.
- **[§8.5.4](docs/08-conformance-and-errors.md#854-canonical-document-encoding)
  integer threshold pinned at ±(2^53 − 1).** "Fit exactly" was never defined,
  in the encoding whose stated purpose is not depending on the reader's JSON
  library. **This corrected an existing vector**:
  `document-model/limits/integer-beyond-fixed-width-still-parses-under-default-limit`
  encoded a 25-digit integer as a bare JSON number, which requires every
  reader's JSON library to parse it losslessly — JavaScript's `JSON.parse`,
  Go's `encoding/json` into `interface{}`, and `serde_json`'s default all
  fail to. Its expected value is now the decimal-string form. Two new vectors
  pin both sides of the boundary.

## v0.10.0-beta (2026-09-14)

**Normative (minor)** — closes
[#71](https://github.com/omnist-dev/omnist-spec/issues/71). No behavior
change is expected in any implementation: `normalize` already does what §6.8
now says, verified against the Python reference. The other four ports have
not yet run the new vector, so that expectation is unconfirmed for them until
the next submodule-pin round.

§6.8 claimed unconditionally that `normalize` "returns the canonical minimal
schema equivalent to `S`", while its own step 1 returns unsatisfiable schemas
unchanged. Those contradict: two equivalent unsatisfiable schemas normalize
to different text, so the canonical-form guarantee did not hold over the
domain the sentence claimed.

- **The guarantee is now scoped to satisfiable schemas**, with the worked
  counterexample stated inline, and callers are told not to use `normalize`
  output equality as an equivalence test unless both inputs are known
  satisfiable — `equivalent` is correct in every case and remains the
  sanctioned check.
- **The reason is now recorded**, because it is a property of the model
  rather than a fixable defect in the algorithm: Omnist has no direct
  spelling for the empty language. The paper's automaton has one; an Omnist
  schema expresses unsatisfiability only indirectly through a mandatory
  reference cycle, and there are unboundedly many such spellings, all
  equivalent and none distinguished by the model. A canonical form needs a
  canonical representative, and every candidate here is an arbitrary pick.
- **The paper's Theorem 4 is now stated in the spec** — equivalence holds
  exactly when normalized forms are isomorphic, for satisfiable inputs. The
  spec previously cited the paper's *Algorithms* but none of its *Theorems*,
  which is the deeper reason this gap went unnoticed: the theorem that makes
  "minimize then compare" sound was never written down, so neither was its
  precondition.
- **§6.9's `extract` carried the identical overclaim** and is corrected too:
  its step 5 delegates to `normalize`, so it inherits the scope limitation
  along with the canonical form. Step 4 does not prevent this, despite
  appearances — it fires when the root is *invalidated by the keep set*,
  which is a different condition from the result being unsatisfiable. An
  already-unsatisfiable input whose labels are all kept passes step 4 and
  emerges unchanged, confirmed against the reference.
- **New vector** `equivalent/unsatisfiable-schemas-are-equivalent-vacuously`.
  Both existing `equivalent` vectors use satisfiable schemas, so an
  implementation that errored or returned false on unsatisfiable input passed
  the whole suite. That behavior is load-bearing for the scope limitation
  above, so it is now pinned.

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
