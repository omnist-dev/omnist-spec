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
JSON-vector suite — 273 vectors as of v0.21.0-beta — dispatched by operation
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

**A trap specific to temporal scalars, found the hard way (omnist-spec#51).**
A vector's `expect.document` `value` field for a `date`/`time`/`datetime`
scalar MUST already be written in your own format's canonical spelling — not
just any string that happens to be semantically equivalent to the source
text. This matters because two equally valid comparison strategies exist and
disagree on what "equivalent" means: an implementation with a native temporal
type (Python's reference `omnist`, comparing parsed `datetime` objects) treats
`"2024-01-01T10:30+05:30"` and `"2024-01-01T10:30:00+05:30"` as the identical
value, since a missing `:SS` and an explicit `:00` describe the same instant.
An implementation whose `Scalar::Datetime` (or equivalent) holds the
canonical *string* the reader produced, with no native temporal type behind
it, compares those two spellings as literally different strings — and if your
reader canonicalizes a missing `:SS` to `:00` on read (a legitimate, common
design choice), only one of the two spellings will ever match. A vector
authored and tested only against a native-temporal-type implementation can
pass there while being subtly wrong for a string-backed one, with nothing
in the vector's own JSON signaling which convention it assumed. If you hit a
single, otherwise-inexplicable failure on an isolated happy-path temporal
vector while everything else in the same batch passes, check the vector's
`value` field against its own file's other temporal vectors for exactly this
kind of un-canonicalized omission before assuming your reader is wrong — and
file it against this repo if it's a genuine vector defect rather than
reworking your reader to match one outlier vector.

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
follow the same pattern: file it as a new `DIV-`-numbered entry in this repo
first (with real, source-verified evidence — every existing entry cites a
specific file, function, or confirmed behavior, never "presumably"), then
cite it. `§9.2`'s forbidden-variation rules have a narrow, explicit carve-out
for exactly this case (a missing distinction being skipped) — it does **not**
cover producing incorrect output, which stays a plain conformance bug
regardless of the reason behind it. That distinction is the whole point: one
accepted accommodation and one real bug can come out of the same underlying
architecture decision, and only the first belongs in the ledger.

## Declared-limit keys: keep your allowlist current

A vector that pins a safety-limit boundary carries a `declared_max_*` key in
its `input`, naming the limit value it was written against. Your runner needs
an allowlist of those keys, checked before the vector runs: if the key is
present and your implementation exposes no way to configure that limit to the
stated value, the vector is a `skip`. Python's runner spells this as a
`_LIMIT_KEYS` set in `tools/conformance/vector_runner.py`; every port's
runner has an equivalent.

**A key your allowlist doesn't know about is not skipped — it is run against
your own default**, which is the one outcome the mechanism exists to prevent.
`test-suite/README.md` lists the current keys. Check that list against your
allowlist on every submodule bump, and treat a new key as part of adopting
the rule that introduced it, not as separate work.

As of **v0.18.0-beta** the newest key is `declared_max_alias_expansion`
(§2.4.1's D-18). No port recognizes it yet, and no port enforces D-18 yet
either, so adopting the rule is two steps: **(a)** implement D-18, and
**(b)** add `declared_max_alias_expansion` to your allowlist.

**Doing (a) without (b) buys you a false pass, which is worse than a
failure.** Of the five vectors in `formats-yaml/alias-expansion`, two
(`nested-anchor-fan-out-exceeds-expansion-limit`,
`expansion-one-past-declared-limit-fails`) fail outright until you implement
the rule — loud, triaged, fixed. The third,
`expansion-at-declared-limit-succeeds`, reports **green either way**. It is
green today because nothing enforces the limit at all, and it stays green
after step (a) because it is run against your implementation's own default
maximum instead of the **3** the vector declares — an `E` at your default's
boundary is not the boundary the vector was written to pin, so the vector
exercises nothing and a real off-by-one in your threshold sails through it. A
failure gets looked at. A pass does not. Treat step (b) as part of step (a),
never as follow-up work.

See [§9.4](09-divergence-ledger.md#94-known-open-divergences)'s `DIV-3` for
the per-vector breakdown of what a runner reports today.

## Byte inputs: `bytes_hex` and the one wrong way to run it

New in **v0.21.0-beta**. A read-side vector (`parse`, `parse_schema`,
`parse_schema_oml`) may give its input as `bytes_hex` — lowercase hex, two
digits per byte — instead of `text`, per
[§8.5.3](08-conformance-and-errors.md#853-operation-drivers)'s **E-26**.
Exactly one of the two is present. Fourteen vectors use it today, all of them
[§2.5](02-document-model.md#25-encoding)'s: eight pinning
[D-14](02-document-model.md#25-encoding)'s rejection of invalid UTF-8 across
the six surfaces, six valid-UTF-8 controls proving the reader still accepts
multi-byte characters.

Your runner does three things with it:

1. **Decode the hex to bytes.** Nothing else — no normalization, no trimming.
2. **Hand those bytes to your implementation as bytes**, through whatever
   byte-oriented entry point you have: a bytes-taking reader, a byte stream,
   or a temporary file you point your file reader at. That is the entry point
   D-14 binds.
3. **Compare as usual.** The expected diagnostic for every D-14 vector is
   `parse.invalid-encoding` at `1:1` — always `1:1`, on every surface, wherever
   in the input the bad byte sits, because nothing decoded and the whole input
   is what failed.

**The wrong way, and it is the tempting one:** decode the bytes into your
language's string type with replacement (`U+FFFD`), with a surrogate-escape
scheme, or with any other lossy recovery, and then run the vector through
your ordinary string-taking reader. That is not the vector's input. For a
D-14 vector it asks your reader a question about a string of replacement
characters — which is *valid* UTF-8 — and whatever it answers says nothing
about the rule. It can report a pass for the one behaviour D-14 explicitly
forbids. If your reader only ever takes a string and nothing in your library
decodes bytes on the caller's behalf, that is a real structural limit: report
these vectors as `skip` under **E-21**, citing
[§9.4](09-divergence-ledger.md#94-known-open-divergences)'s `DIV-6`. A skip is
honest and tracked; a decoded-with-replacement pass is neither.

If your language's string type can itself hold ill-formed UTF-8 — Go's
`string` is a byte slice, and Go is the measured case in `DIV-6` — you do not
get the skip. Your string-taking reader is a byte-oriented entry point
wearing a string's clothes, and D-14 binds it.

## Say which comparison mode produced your numbers

§8.5.2 rule 4 permits a runner to compare **code-agnostically** — `ok` plus
the set of `path`s, never `code` — because §8.1 does not yet make §8.3
mandatory. That is a legitimate mode and several ports are in it. It is also
a quiet one: **a code-agnostic run passes vectors the implementation does not
actually satisfy.** A diagnostic with the right `ok` and the right position
but the wrong code reports green, and nothing in the run says so.

This is not hypothetical.
[§9.4](09-divergence-ledger.md#94-known-open-divergences)'s `DIV-4` has a row
of exactly that shape — `OML-25`, where the reference's `ok` and paths match
every affected vector and only the code is wrong — and the reference had
therefore been failing a vector's stated expectation for as long as the
vector existed while its own suite reported clean. §8.5.5 already requires a run to state which mode
produced it; treat that as load-bearing rather than as a header field, and
when you report conformance numbers anywhere else — a README badge, a release
note, an issue — say the mode alongside the count. "249 pass" and "249 pass,
code-agnostic" are different claims.

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
