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
JSON-vector suite — 331 vectors as of v0.26.0-beta — dispatched by operation
name rather than fixture directory shape. They're complementary, not
redundant: track 1 proves your CLI wrapper (if you have one) actually works
end to end; track 2 has far denser coverage of individual rules. Build both;
all three existing ports did.

## What to build, in order

**1. A referee.** Comparison, using *your own* implementation's parser and
equality — never another port's. Document comparison needs nothing beyond
your `Doc`/`Node` type's own equality, provided it's order-sensitive (order is
data, per [§2.3](02-document-model.md#23-structural-invariants) D-1/D-3).

Schema comparison needs **three modes**, and *which one an operation uses
depends on the track*. Two ports built one structural referee and reused it
for everything; this table exists so a fourth does not.

| Mode | What it does | Used by |
|---|---|---|
| `exact` | **Structural.** Re-parse both texts with your own OSD parser, then require every record name and every field's label, type and cardinality to match. Declaration order and formatting are *not* compared. | **Track 1** — `normalize`, `prune`, `extract` — and the referee self-test. [`conformance-harness.md`](conformance-harness.md) §4, §6. |
| `canonical` | **Byte-exact string comparison.** Your implementation's canonical output text against the vector's expected text. No re-parse, no normalization of your own. | **Track 2** — every schema-valued `expect` field except `infer`'s and `infer_with_report`'s (table below). [§8.5.3](08-conformance-and-errors.md#853-operation-drivers): "compared byte for byte per §3.3/§5.9". |
| `isomorphic` | **Structural up to a renaming of records.** | `infer` and `infer_with_report`'s `schema` (stated for Track 1 in `conformance-harness.md` §4; §8.5.3 states no comparison for Track 2's, and the same reasoning applies) — the one case where a structural comparison is the *correct* one, because [§6.10](06-schema-algebra.md#610-infersamples) never normalizes `infer`'s output and its record names are implementation-derived. |

**`exact` and `canonical` are not interchangeable, in either direction.**
Making `exact` byte-exact fails the referee self-test on purpose-built cases
(`01-schema-exact-equal-different-field-order` and
`07-schema-exact-equal-different-env-declaration-order` are *meant* to compare
equal). Using `exact` for Track 2 passes vectors a formatting bug should fail:
a structural comparison re-parses both sides, so two texts that differ
byte for byte — wrong indentation, wrong join character, wrong escaping, two
fields swapped — can still parse to the same Schema and report green.
TypeScript and Rust both shipped exactly that
([omnist-ts#150](https://github.com/omnist-dev/omnist-ts/pull/150),
[omnist-rs#184](https://github.com/omnist-dev/omnist-rs/pull/184)); changing
canonical OSD output's indentation, or `to_osd`'s join character, left every
canonical-output vector green, which is also how
[OSD-15](05-osd-grammar.md#59-canonical-output)'s escaping bug went unseen. Build `canonical` as its
own comparison next to `exact`, used only by the Track 2 runner. And do not
overcorrect the other way: `infer` output is *not* canonical, so comparing it
byte for byte fails correct implementations over record names §6.10 never
fixed.

If your library doesn't yet expose an isomorphism check, you'll need to add
one — it's a real, narrow addition (see `omnist`'s `Schema.isomorphic_to()`,
added for exactly this), not a substitute for whatever your library already
uses as its canonical "same schema" comparison.

Prove the referee trustworthy **before** it judges anything: port the
10-case self-test under `conformance/fixtures/_referee-self-test/` and get
it passing first. All three existing ports did this as their literal step
one. The self-test covers `exact` and `isomorphic` only: `canonical` is a string
comparison and has no fixtures there, so prove it with a mutation of your own
instead — change one detail of your canonical output (an indentation width, the
join character, one escape, the order of two fields) and confirm at least one
Track 2 vector goes red. A `canonical` comparison that survives that mutation is
a structural one under another name.

**2. Track 1's fixture runner.** Walk `conformance/fixtures/`'s
per-operation directories, invoke each operation (CLI or direct library
call — see below), compare with the referee, report pass/fail/skip.

**3. Track 2's vector runner.** Walk `test-suite/`'s JSON files, dispatch on
each vector's `operation` field per [§8.5.3](08-conformance-and-errors.md#853-operation-drivers)'s
table, compare `expect` against your result per
[§8.5.2](08-conformance-and-errors.md#852-diagnostics-matching)'s rules
(message text never compared; diagnostics compare as a set of `(path,
code)`, never severity; no partial matching), with the mode each operation's
schema-valued or document-valued field needs, from the table under "Which
comparison each operation needs" below.

## Which comparison each operation needs

Every row cites the text that requires it; nothing here is a requirement of
this page's own. Message text is never compared in either track
([§8.5.2](08-conformance-and-errors.md#852-diagnostics-matching) rule 1).

### Track 1 — fixtures

Source: [`conformance-harness.md`](conformance-harness.md) §2 (contract), §3
(fixture shapes), §4 (comparison), §6 (self-test).

| Operation | What is compared | Mode |
|---|---|---|
| `write` | output OML against `expected.oml` | Document equality: read both with your own reader, order-sensitive (§4 `compare_document`) |
| `normalize`, `prune` | output OSD against `expected.osd` | `exact` (§4) |
| `extract` | on success `expected/output.osd`; `expected/ok.txt` either way | `exact` (§4) |
| `infer` | on success `expected/output.osd`; `expected/ok.txt` either way | `isomorphic` (§4) |
| `validate` | `expected/ok.txt`; on failure `expected/diagnostics.json` | paths; `code` is informational until §9.3 reads "yes" for every implementation (§2, the `lint` findings note) |
| `materialize` | `expected/ok.txt`; on success `expected/output.oml`, on failure `expected/diagnostics.json` | Document equality; failure as `validate` |
| `is_empty`, `compatible_with`, `equivalent` | `expected.txt`, a boolean | equality |
| `lint` | `expected.json` findings | `severity` and `location` exactly; `code` informational (§2) |

### Track 2 — JSON vectors

Source: [§8.5.3](08-conformance-and-errors.md#853-operation-drivers) (drivers),
§8.5.2 (diagnostics matching), §8.5.4 (document encoding). For a **failing**
vector, every operation alike: `ok` is `false` and `diagnostics` is compared as
a **set** of `(path, code)` pairs — every expected pair present, none extra
(§8.5.2 rules 2 and 3, E-17), severity never compared. Paths are compared byte
for byte (E-9, E-11), **with one exception: an expected `path` of the string
`line:col` (E-32) is a placeholder** that a `parse.codec-syntax` vector uses
because a codec's blamed character is implementation-defined (E-31). For that
entry compare the `code`, and check only that the reported path is a
well-formed text position, `^[1-9][0-9]*:[1-9][0-9]*$`; do not compare its
value. Every other path in the suite stays byte for byte. A runner that skips
this step fails the four `formats-*/syntax/` vectors. Rule 4's code-agnostic
mode is the one permitted relaxation of the code, and the run MUST say it was
used.

| `operation` | `expect` fields on success | What a runner MUST compare, and how |
|---|---|---|
| `parse` | `ok`, `document`; `diagnostics` on the XML vectors that read a dropped attribute or namespace | `document`: Document equality, order-sensitive (§8.5.4, D-1/D-3). If the vector lists `diagnostics`, they are compared as a `(path, code)` set and an unlisted one is unexpected (§8.3.8, E-5, E-17 rule 3). |
| `parse_schema` | `ok`; `schema` only when the vector pins round-trip fidelity | `schema` present: **`canonical`**, byte for byte (§8.5.3, §3.3/§5.9). Absent: acceptance only. |
| `validate` | `ok` | `ok`; on failure the `(path, code)` set. |
| `materialize` | `ok`, `document` | `document`: Document equality; on failure the `(path, code)` set. |
| `write` | `ok`, `text`; `diagnostics` MAY accompany a success (`format.temporal-stringified`, `format.interleaving-lost`) | `text`: byte for byte, with §8.5.3 E-18's whitespace rule for XML; `diagnostics` as a `(path, code)` set. On failure the `(path, code)` set. The `strict` key some `write` vectors carry in `input` selects strict mode ([§8.3.9](08-conformance-and-errors.md#839-write)). |
| `compatible_with`, `equivalent` | `result` | the boolean. |
| `is_empty` | `empty` | the boolean. |
| `normalize`, `prune` | `schema` | **`canonical`** (§8.5.3; §9.2: "compared as canonical OSD text byte for byte"). |
| `extract` | `ok`, `schema` | **`canonical`**: `extract` ends by delegating to `normalize` ([§6.9](06-schema-algebra.md#69-extracts-keep) step 5), and §9.2 lists `extract` beside `normalize`/`prune`. On failure the `(path, code)` set (`algebra.extract-invalidates-root`). |
| `infer` | `ok`, `schema` | **`isomorphic`** ([§6.10](06-schema-algebra.md#610-infersamples): output never normalized). On failure the `(path, code)` set. |
| `infer_with_report` | `ok`, `schema`, `fallbacks` | `schema`: **`isomorphic`**. `fallbacks`: a list of `{location, reason}`, always present on success and empty when nothing was opened (§8.5.3); compare it, empty included — a runner that ignores it passes an implementation that never reports. `reason` is one of the two spellings §6.10 fixes, so it is not message text under rule 1. `location` is `RecordName.label` (§6.10) and `infer`'s record names are implementation-derived, so whether `location` is compared exactly or modulo the record renaming is not settled by the text; the vectors' entries look like `Root.id`. Nor does §8.5.3 say whether the list is compared as a sequence or a set, and no vector holds more than one entry. |
| `lint` | `ok`, `findings` | `ok`, and each finding's `code`, `severity` and `location` (§8.5.3); no `message`. Failure vectors carry `ok: false` and `findings` too, not `diagnostics`. |
| `schema_from_document`, `parse_schema_oml` | `ok`, `schema` | **`canonical`** (§8.5.3, same comparison as `parse_schema`). On failure the `(path, code)` set. |
| `schema_to_document` | `ok`, `document` | Document equality, order-sensitive (§8.5.3, §8.5.4). |
| `write_schema_oml` | `ok`, `text` | byte for byte as OML text (§8.5.3, same rule as `write`). |

**Read-side vectors** (`parse`, `parse_schema`, `parse_schema_oml`) take their
source as `text` or as `bytes_hex`, exactly one (E-27; see the section below).

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

As of **v0.26.0-beta** the newest key is `declared_max_expanded_slots`
(§2.4.1's D-22, the absolute cap on expanded size); eight vectors in
`formats-yaml/alias-expansion.json` carry it. It follows the same rule as
every other key: allowlist it, and report `skip` until the cap is implemented.
Before it, as of **v0.18.0-beta**, the newest was `declared_max_alias_expansion`
(§2.4.1's D-18). Every vector in `formats-yaml/alias-expansion.json` carries
one of the two. Go and TypeScript enforce D-18 and a Rust pull request is open,
but no port implements D-22, so until you implement a rule, a runner MUST report
each vector carrying its key as an E-20 skip citing `DIV-3` (never a pass).
Adopting is two steps: **(a)** implement D-18 and D-22, and **(b)** add both
`declared_max_alias_expansion` and `declared_max_expanded_slots` to your
allowlist.

**Doing (a) without (b) buys you a false pass, which is worse than a
failure.** Of the vectors in `formats-yaml/alias-expansion`, every one that
expects rejection (for example `nested-anchor-fan-out-exceeds-expansion-limit`
and `expansion-one-past-declared-limit-fails`) fails outright until you
implement the rule — loud, triaged, fixed. The accepted boundary vectors, such
as
`expansion-at-declared-limit-succeeds`, report **green either way**. It is
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
[§8.5.3](08-conformance-and-errors.md#853-operation-drivers)'s **E-27**.
Exactly one of the two is present. Fourteen vectors use it today, all of them
[§2.5](02-document-model.md#25-encoding)'s: eight pinning
[D-14](02-document-model.md#25-encoding)'s rejection of invalid UTF-8 across
the six surfaces, six valid-UTF-8 controls proving the reader still accepts
multi-byte characters.

Your runner does three things with it:

1. **Decode the hex to bytes.** Nothing else — no normalization, no trimming.
2. **Hand those bytes to your implementation as bytes**, through a
   byte-oriented entry point. Any entry point you provide that reads a file,
   standard input or a byte stream is one — **your CLI counts**, and so does
   a bytes-taking reader. If the only one you have is the CLI, run these
   vectors through the CLI; the signature of the reader behind it does not
   matter, because D-14 binds the place the bytes enter. The "write the bytes
   to a temporary file" route only works if you have a file-reading entry
   point to point at it, which for some ports is exactly and only the CLI.
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
forbids.

**Which non-result you report matters, and E-21 is narrower than it looks.**
If you have simply not taught your runner the `bytes_hex` field yet, that is
an **E-20** "not yet implemented" skip — no ledger citation needed. (Until
you report it as one, a runner that chokes on the unknown field is reporting
a `fail`, which is fine and loud, but say which it is.) **E-21** — the
documented-divergence skip, which needs its own
[§9.4](09-divergence-ledger.md#94-known-open-divergences) ledger entry — is only
for an implementation with **no** byte-oriented entry point anywhere: no
bytes-taking reader, no file/stdin/stream entry point, and no CLI. Check your
CLI before you reach for it; none of the five ports qualifies, and all five
report `parse.invalid-encoding` as of v0.21.0-beta. If
you have a byte-oriented entry point and these vectors fail through it, that
is a plain `fail` and a real bug, not a skip.

If your language's string type can itself hold ill-formed UTF-8 — Go's
`string` is a byte sequence, and Go is the worked example — your
string-taking reader is itself a byte-oriented entry point, and §2.5 spells
out what that means concretely: reject any reader input `s` for which
`utf8.ValidString(s)` is false. The reverse case is Rust, where `&str`
carries validity as its own invariant and the reader has nothing left to
check; there the CLI is the entry point that matters. And note what D-14 does
**not** reach: a lone UTF-16 surrogate in a JavaScript or Java string, or a
surrogate-escape artefact in a Python `str`, is a property of an
already-decoded string, not of bytes you read, and §2.5 puts both out of
scope.

## Say which comparison mode produced your numbers

§8.5.2 rule 4 permits a runner to compare **code-agnostically** — `ok` plus
the set of `path`s, never `code` — because §8.1 does not yet make §8.3
mandatory. That is a legitimate mode; the Python reference's runner used it until
v0.21.0-beta. It is also a quiet one: **a code-agnostic run passes vectors the implementation does not
actually satisfy.** A diagnostic with the right `ok` and the right position
but the wrong code reports green, and nothing in the run says so.

This is not hypothetical.
The retired `DIV-4` (§9.4) had a row of exactly
that shape — `OML-25`, where the reference's `ok` and paths match
every affected vector and only the code is wrong — and the reference had
therefore been failing a vector's stated expectation for as long as the
vector existed while its own suite reported clean. §8.5.5 already requires a run to state which mode
produced it; treat that as load-bearing rather than as a header field, and
when you report conformance numbers anywhere else — a README badge, a release
note, an issue — say the mode alongside the count. "331 pass" and "331 pass,
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
