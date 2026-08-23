# Porting a Conformance Runner

*Non-normative guide.* The rules themselves live in
[`docs/conformance-harness.md`](conformance-harness.md) (track 1: OML/OSD
CLI-wrapper fixtures) and [§8.5](08-conformance-and-errors.md#85-conformance-harness-protocol)
(track 2: JSON vectors). If this page and either of those ever disagree, they
win — this page only collects what three separate ports (`omnist` in Python,
`omnist-ts`, `omnist-rs`) already learned building their own runners, so a
fourth doesn't have to rediscover it from scratch.

## Two tracks, both worth building

**Track 1** (`conformance/fixtures/` in this repo) exercises a real CLI or
direct library calls against small, hand-written fixtures — 19 currently,
plus a 10-case referee self-test. **Track 2** (`test-suite/`) is a larger
JSON-vector suite — 146 vectors as of this writing — dispatched by operation
name rather than fixture directory shape. They're complementary, not
redundant: track 1 proves your CLI wrapper (if you have one) actually works
end to end; track 2 has far denser coverage of individual rules. Build both;
all three existing ports did.

## What to build, in order

**1. A referee.** Structural comparison, using *your own* implementation's
parser and equality — never another port's. Document comparison needs
nothing beyond your `Doc`/`Node` type's own equality, provided it's
order-sensitive (order is data, per [§2.3](02-document-model.md#23-structural-invariants)
D-1/D-3). Schema comparison needs two modes: `exact` (every record name and
field must match — used for `normalize`/`prune`/`extract`, whose output
naming is spec-determined) and `isomorphic` (same structure up to record
renaming — used only for `infer`, since [§6.10](06-schema-algebra.md#610-infersamples)
never normalizes its output). If your library doesn't yet expose an
isomorphism check, you'll need to add one — it's a real, narrow addition (see
`omnist`'s `Schema.isomorphic_to()`, added for exactly this), not a
substitute for whatever your library already uses as its canonical
"same schema" comparison.

Prove the referee trustworthy **before** it judges anything: port the
10-case self-test under `conformance/fixtures/_referee-self-test/` and get
it passing first. All three existing ports did this as their literal step
one.

**2. Track 1's fixture runner.** Walk `conformance/fixtures/`'s
per-operation directories, invoke each operation (CLI or direct library
call — see below), compare with the referee, report pass/fail/skip.

**3. Track 2's vector runner.** Walk `test-suite/`'s JSON files, dispatch on
each vector's `operation` field per [§8.5.3](08-conformance-and-errors.md#853-operation-drivers)'s
table, compare `expect` against your result per
[§8.5.2](08-conformance-and-errors.md#852-diagnostics-matching)'s rules
(message text never compared; diagnostics compare as a set of `(path,
code)`, never severity; no partial matching).

## CLI wrapper, or direct library calls?

`omnist` (Python) uses a CLI wrapper for track 1, because a real, already-existing
CLI was the natural thing to reuse. `omnist-ts` and `omnist-rs` both chose
direct library/function calls for both tracks instead, since a port that's
primarily a library — not primarily a CLI tool — gains nothing from spawning
a subprocess per fixture. Either is conformant; pick whichever fits your
port's actual shape. If you do wrap a CLI, [§2](conformance-harness.md#2-the-wrapper-cli-contract)'s
table documents Python's *real, verified* command shapes — treat it as one
worked example of a CLI binding, not a mandate to replicate Python's exact
flag names in your own CLI.

## Fixture sourcing: a pinned git submodule

All three existing ports vendor this repo the same way: a git submodule
pinned to a tag, never tracking `master`, so fixture updates are explicit,
reviewable commits rather than silent drift. See any of the three repos'
`tools/conformance/README.md` for the exact bump procedure — they're
functionally identical.

## Reporting: skip is not failure, and every skip needs a reason

[§8.5.5](08-conformance-and-errors.md#855-reporting) is normative here, not
just a suggestion: your CI **MUST** fail the build on any nonzero `fail`
count, and **MUST NOT** fail merely because `skip` is nonzero — provided
every skip cites a real reason. Two categories:

- **Not yet implemented.** Temporary; expected to become a `pass` once the
  work lands. No ledger entry required on its own.
- **Documented divergence.** Your target language or design genuinely
  cannot provide something a vector depends on — not a missing feature, a
  structural limit. This requires a numbered entry in
  [chapter 9](09-divergence-ledger.md)'s divergence ledger (see
  [§9.4](09-divergence-ledger.md#94-known-open-divergences) for the current
  open entries), and your runner's skip reason **MUST cite that entry by
  number**. Don't invent an ungrounded skip reason, and don't silently
  rewrite a vector to route around a real divergence instead of documenting
  it. A divergence this narrow — one language, one scalar-kind distinction —
  is closed once the implementation adds real type support and its entry is
  removed from the ledger; it doesn't stay listed as historical record.

If you find a genuinely new divergence category building your own runner,
follow the same pattern: file it as a new `D-`-numbered entry in this repo
first (with real, source-verified evidence — every existing entry cites a
specific file, function, or confirmed behavior, never "presumably"), then
cite it. `§9.2`'s forbidden-variation rules have a narrow, explicit carve-out
for exactly this case (a missing distinction being skipped) — it does **not**
cover producing incorrect output, which stays a plain conformance bug
regardless of the reason behind it. D-7's two halves are the worked example
of that distinction: one accepted accommodation, one real bug that needed
fixing, in the same underlying architecture decision.

## When you find a real failure

Triage before touching anything:

- **A genuine bug in your own implementation.** Fix it, following your
  repo's own conventions (coverage gate, changelog, version bump).
- **A vector or spec-doc defect.** This has happened in both directions
  during this suite's own construction — a vector that looked like a real
  bug turned out to be a construction mistake (a mismatched input string
  that never exercised what its name claimed), and a spec table that looked
  authoritative turned out to disagree with what every implementation
  actually did in six of twelve rows. File the issue on this repo, propose
  the fix, and let it be reviewed rather than assuming your first read is
  correct — don't silently patch a vector or a spec doc from your own repo.
- **A genuinely new divergence.** Follow the process above.

Report real, verified pass/fail/skip counts once you have them — don't imply
parity with another port's numbers if your true ceiling differs for
principled, documented reasons. It usually will: Rust's port currently has
*fewer* skips than Python's or TypeScript's, because its `parse.*`-family
errors already carry structured paths the other two don't yet — a favorable
divergence, still worth reporting accurately rather than rounding to "the
same as everyone else."
