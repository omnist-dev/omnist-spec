# OML/OSD Conformance Harness

*Normative for any implementation that opts into this track. See
[§8.6](08-conformance-and-errors.md#86-omlosd-conformance-harness) for how
this relates to the §8.5 JSON-vector harness — the two are complementary,
not alternatives.*

## Status

**Scope for this revision: `omnist` (Python) only.** The CLI wrapper
contract below is written implementation-agnostically, since TypeScript and
Rust are expected to adopt it later, but nothing in this document requires
them to yet. Everywhere a design choice was made against a specific
implementation's real behavior, it names Python explicitly rather than
implying a claim about the other two.

## 1. Purpose

Judge whether an implementation's OML/OSD **input and output** — the text a
human or another tool actually reads and writes — matches what the spec
requires, using structural comparison rather than text diffing. Text
diffing is wrong here: the same Document or Schema can be written with
different indentation, array sugar versus repeated labels, or field
declaration order, and still be the identical model (§2, §3.1). A harness
that diffs text would fail correct implementations over formatting choices
the spec never constrains.

## 2. The wrapper CLI contract

**This section describes `omnist`'s (Python's) real, already-existing CLI
(`omnist/cli.py`), verified directly against source — it does not invent a
new convention.** The harness targets what already exists rather than
requiring CLI changes beyond what §5 already calls for. A prior draft of
this section specified an idealized stdin-only contract that did not match
Python's actual CLI; that draft is replaced below.

The real conventions, applying to every subcommand:

- **Primary input is a positional argument, and `-` means stdin** — not
  "always stdin." Every command below accepts a file path or `-`.
- **Format is explicit, not assumed.** Document-consuming commands take
  `--from FORMAT` (`oml`, `json`, `yaml`, `toml`, `xml`). This track only
  ever uses `--from oml`, but the flag MUST still be passed — there is no
  OML-is-the-default behavior to rely on.
- **A schema argument, where needed, is `--schema FILE`** (`validate`) or a
  second positional (`schema compatible-with A B`, `schema equivalent A B`).
- **Schema-producing commands accept `--compact`** (single-line OSD) or
  omit it for pretty-printed, multi-line OSD. **This distinction is
  deliberately irrelevant to this track**: the referee re-parses stdout
  before comparing (§4), so `--compact` vs. pretty-printed output must
  compare equal. Fixtures SHOULD still pick one consistently per fixture
  file for readability; the harness itself must not care which.
- **Structured output already exists via `--json` (most commands) or
  `--result-format json`** (boolean-result commands: `is-empty`,
  `compatible-with`, `equivalent`). Reuse it rather than inventing a
  second mechanism — see the exact JSON shape below, which is **not**
  identical to §8.2's envelope (no per-error `severity` field; errors are
  wrapped under `{"ok", "message", "errors"}` rather than a bare array).
  This is consistent with §8.1's own disclosure that no implementation
  emits the full §8.3 taxonomy yet — Python's `--json` output is real,
  existing, partial convergence, not yet full §8.2 compliance, and this
  track does not require Python to close that gap before being usable.
- **`--json` failure payloads print to stdout, not stderr.** Verified
  functionally across `validate`, `extract`, `infer`, and `convert`
  (materialize) — `_fail()`'s own docstring in `cli.py` confirms this is
  deliberate, not an accident of one command. An earlier revision of this
  section said stderr; that was wrong for every command in this table.
- **One diagnostic in this whole contract is not JSON:** `infer
  --allow-any`'s report of which fields it opened prints to **stderr as
  plain text**, not stdout JSON — see the `infer` row below.

| Operation | Real command | Success (stdout) | Exit code |
|---|---|---|---|
| `write` | `omnist format INPUT [--compact] [-o FILE]` | canonical OML | 0 |
| `validate` | `omnist validate INPUT --from oml --schema SCHEMA --json` | `{"ok": true}` | 0 (ok), 1 (validation failure, `errors` populated), 2 (parse/read error, `errors` empty) — `--json` failure payload on **stdout** |
| `materialize` | `omnist convert INPUT --from oml --to oml --schema SCHEMA --json` | materialized OML (plain, `--json` only affects the failure path) | 0, or 2 on inexact conversion/shape failure — `--json` gives `{"ok": false, "message", "errors": [{"path","code","message"}]}` on stdout, verified matching §7.2's error text exactly |
| `normalize` | `omnist schema normalize SCHEMA [--compact] [-o FILE]` | OSD | 0 |
| `prune` | `omnist schema prune SCHEMA [--compact] [-o FILE]` | OSD | 0 |
| `extract` | `omnist schema extract SCHEMA --keep label1,label2,... [--compact] [-o FILE] [--json]` | OSD | **0, or 1 if `keep` invalidates the root** (§6.9) — `--json` gives `{"ok": false, "message", "errors": []}` on stdout |
| `is_empty` | `omnist schema is-empty SCHEMA --result-format json` | `{"empty": bool}` | **0 if empty (`true`), 1 if not empty (`false`)** — the boolean result is encoded in the exit code too, not just stdout; do not assume 0 always means "command succeeded" for this command |
| `compatible_with` | `omnist schema compatible-with A B --result-format json` | `{"compatible": bool}` | 0 if `true`, 1 if `false` — same exit-code-carries-the-boolean pattern |
| `equivalent` | `omnist schema equivalent A B --result-format json` | `{"equivalent": bool}` | 0 if `true`, 1 if `false` |
| `infer` | `omnist infer FILE [FILE...] --from oml [--allow-any] [--compact] [-o FILE] [--json]` — **multiple positional document files, one per sample; not a single stdin stream** | OSD. With `--allow-any` and an opened field, a plain-text report prints to **stderr** (not stdout, not JSON): `opened N field(s) as \`any\`:\n  RecordName.label — reason` | **0 (including the `--allow-any` success case), or 2 on ambiguous type without `--allow-any`** — `--json` gives `{"ok": false, "message", "errors": []}` on stdout for the exit-2 case |
| `lint` | `omnist schema lint SCHEMA --json [--severity info\|warning]` | `{"ok": bool, "findings": [{"code","severity","location","message"}]}` — `ok` is `false` iff any `warning`-severity finding is present | **1 if any `warning`-severity finding is present, 0 otherwise** — this was previously documented as "0, always," which was flat wrong, not just incomplete |

**`lint` findings' `code` field is compared code-agnostically, like Track
2's diagnostics.** [§8.5.2](08-conformance-and-errors.md#852-diagnostics-matching)
rule 4 already establishes this for the JSON-vector suite specifically
because §8.3-namespaced code adoption is still rolling out across
implementations — see the `§8.3 error codes` row in
[§9.3](09-divergence-ledger.md#93-current-status) for current per-port
status. The reference implementation itself still emits the bare
pre-namespacing form in places (`unreachable-record`, not
`lint.unreachable-record`), so a fixture's `expected.json` recorded
against it necessarily carries that same bare form — an implementation
that has already adopted §8.3's namespaced codes MUST NOT be marked
failing for that; compare `severity` and `location` exactly, and treat
`code` as informational only until every implementation's row in §9.3
reads "yes." This applies to every operation whose fixture carries a
`code` field, not lint alone — the same reasoning that produced §8.5.2
rule 4 for Track 2 applies identically here.

**`is_empty`/`compatible_with`/`equivalent`'s exit-code convention is a real
finding that changes §5.1's general contract**, not a minor detail: this
track's original draft assumed boolean-result commands always exit 0 and
carry the answer only in stdout. Python's real CLI instead encodes the
boolean in the exit code as well (0 = true, 1 = false) — the orchestrator
MUST read the boolean from stdout's `--result-format json` payload, not
infer it from the exit code, since a future implementation (or a future
Python version) could legitimately choose either convention and this track
should not be sensitive to which.

**`materialize` was unreachable via the CLI until `omnist#277` (now closed,
`omnist` 0.7.16).** `convert` only refuses `--from oml --to oml` now when
`args.schema` is falsy — verified directly, functionally, not just by
reading the diff: a `date`-typed field carrying a schema-valid string
materializes and writes back unquoted (exit 0); the same input with no
`--schema` still refuses, pointing at `format` (exit 2); an inexact value
fails with the exact §7.2 error text (exit 2). No longer blocked — every
operation in
the table above is fully CLI-reachable today and unblocked.

Every row above was checked directly against real command output, not just
source reading — `extract`, `infer`, and `lint`'s exact exit codes and
`--json`/stderr shapes (including `lint`'s incorrect "always 0" claim in an
earlier revision, and the stdout-not-stderr correction that applies to every
`--json` failure in this table) were only found by actually running each
command, the same way `materialize`'s CLI gap was.

`parse` and `materialize`'s stage-1-only variant are intentionally **not**
listed — this track tests round-trip and schema-directed behavior, not raw
parsing in isolation; §8.5's JSON-vector track already covers `parse`
directly via its canonical Document encoding, and duplicating that here
would test the same thing twice through two different mechanisms with two
different chances to disagree with each other.

## 3. Fixture format

One fixture is one directory. Two shapes, depending on how many inputs the
operation needs:

**Single-input operations** (`normalize`, `prune`, `write`, `is_empty`,
`lint`):

```
conformance/fixtures/normalize/merge-isomorphic-records/
    input.osd
    expected.osd
    purpose.txt
```

**Two-input operations** (`validate`, `materialize`, `compatible_with`,
`equivalent`, `extract`):

```
conformance/fixtures/validate/order-with-optional-coupon/
    schema.osd
    input.oml
    expected/
        ok.txt              # "true" or "false"
        diagnostics.json    # present only when ok.txt is "false"; array of the Sec8.2 envelope
    purpose.txt
```

**`purpose.txt`**, first line one of `happy-path` / `edge-case` /
`error-case` / `determinism-regression`, followed by a free-text sentence.
This is the same controlled vocabulary [omnist-spec#23](https://github.com/omnist-dev/omnist-spec/issues/23)
already commits to for the JSON-vector track's `"purpose"` field — same
idea, this track's file-per-fixture shape instead of one JSON object.

## 4. The comparison algorithm

The referee is the Python `omnist` library itself, run by the orchestrator
(not the implementation under test — even when the implementation under
test *is* Python, the referee's parse-and-compare step is logically
separate from the CLI invocation being judged).

```
function compare_document(actual_oml_text, expected_oml_text):
    actual = omnist.read_oml(actual_oml_text)
    expected = omnist.read_oml(expected_oml_text)
    return actual == expected

function compare_schema(actual_osd_text, expected_osd_text, mode):
    actual = omnist.parse_schema(actual_osd_text)
    expected = omnist.parse_schema(expected_osd_text)
    if mode == "exact":
        return actual == expected
    if mode == "isomorphic":
        return actual.isomorphic_to(expected)  # omnist#279 -- not yet public; see Sec5
```

**Document comparison** needs no new capability: `Doc.__eq__` in the Python
library already performs exactly this structural, order-sensitive
comparison (order is data per §2.3's D-1/D-3, and equality respects that —
two documents differing only in edge order are genuinely different
documents, not a false mismatch to paper over).

**Schema comparison has two legitimate meanings, and this track uses both,
chosen per operation — never one default for everything:**

- **`exact`** — every record name, and every field's label/type/cardinality,
  must match. Used for `normalize`, `prune`, `extract`: their output naming
  is spec-determined (`normalize`'s sorted-minimum-representative rule,
  §6.8, is exactly what makes two implementations' output
  cross-comparable), so exact equality is the correct, meaningful check.
- **`isomorphic`** — same structure up to a renaming of records. Used for
  `infer`: §6.10 explicitly documents its generated record names as
  implementation-derived and hand-editable, never canonical, so requiring
  exact name matches would fail correct implementations purely on naming
  choices this spec never mandated matching.

**Why `isomorphic` and not `equivalent` (§6.7) for `infer` — this is not an
arbitrary choice between two available oracles.** `equivalent` is defined
purely on accepted-document-language and is too permissive for this specific
check: §6.10 requires `infer` to *never* merge structurally-identical
generated records (that's `normalize`'s job, explicitly not `infer`'s). An
`infer` implementation that incorrectly merges two identical generated
records still accepts exactly the same documents — `equivalent` would
report it as correct, a false negative that lets a real class of `infer`
bug through. Isomorphism catches it: the two record sets have different
cardinality, so no renaming bijection exists between them, regardless of
naming choices. Isomorphism is the narrowest tool that tolerates the one
degree of freedom §6.10 actually grants (naming) while still catching
everything else — not a substitute for `equivalent`, which remains the
model's canonical definition of schema equality everywhere else.

This requires `Field.__eq__`, `Record.__eq__`, and `Schema.__eq__` to exist
in the Python library — confirmed, as of this writing, that they do not
(§5, below). Isomorphic comparison is tracked separately as
[`omnist#279`](https://github.com/omnist-dev/omnist/issues/279), scoped as
an additional `Schema.isomorphic_to(other)` method — deliberately not a
change to `equivalent`'s status or definition. Until that lands, this
track's referee uses the private `_isomorphic` in `omnist/ops/isomorphic.py`
as a flagged, tracked stopgap.

## 5. Required Python library change

Add `__eq__` to `Field`, `Record`, and `Schema` in `omnist/schema.py`:

- `Field.__eq__` — compare `label`, `type`, `min`, `max`.
- `Record.__eq__` — compare `fields` as an **order-independent** set. Fields
  form an unordered set at the model layer (§3.1); two records with the same
  fields declared in different order are the same record and MUST compare
  equal.
- `Schema.__eq__` — compare `root` and `env`. Comparing `env` as a plain
  dict comparison is correct: `env` iteration order is preserved for OSD
  text readability (§3.1) but is not itself semantically significant, so
  equality MUST NOT be sensitive to it.

This is the only implementation change this document requires. It is
small, isolated, and independently testable (a schema built two different
ways but structurally identical compares equal; one differing by a single
field's cardinality does not) before anything else in this track depends
on it.

## 6. Referee self-test

Before this track judges any real implementation output, its own
comparison logic must be shown trustworthy against cases a human already
solved by reading the spec — not cases generated by running any
implementation. A small fixture set (10-15 cases) under
`conformance/fixtures/_referee-self-test/`, covering:

- Two structurally identical schemas, written with different field order
  and different indentation, compare equal under `exact` mode.
- Two schemas differing by one field's cardinality do not compare equal.
- Two schemas with the same structure but different record names compare
  equal under `isomorphic` mode and unequal under `exact` mode.
- Two documents with the same edges in a different order do not compare
  equal (order is data, not noise).
- A document with `[..., "a", "b", ...]` array-sugar input and the
  equivalent repeated-label OML compare equal.

## 7. Orchestrator

**Each implementation owns its own orchestrator, in its own repo — this
repo does not ship one.** An orchestrator invokes that implementation's
CLI per §2's contract, judges the result with §4's comparison (using
that implementation's own parser/library as the referee, not a
cross-language dependency on another implementation's), and reports
pass/fail/skip per fixture, reusing §8.5.5's reporting discipline (skip
is a first-class result, never silently folded into pass).

This section originally described a `conformance/orchestrator/` living
in this repo. That was a design mistake, corrected once actually built:
the orchestrator is inherently implementation-specific code (it imports
and shells out to one implementation), so keeping it in the
implementation-agnostic spec repo meant a TypeScript or Rust port could
never use it without depending on Python cross-language, or rewriting it
from scratch — precisely the outcome this framework exists to avoid. See
[omnist#283](https://github.com/omnist-dev/omnist/issues/283) and
[omnist-spec#27](https://github.com/omnist-dev/omnist-spec/issues/27) for
the move.

`omnist` (Python)'s orchestrator now lives at `tools/conformance/` in
that repo, consuming this repo's fixtures via a pinned git submodule and
wired into `omnist`'s own CI — see that repo's
`tools/conformance/README.md`. `omnist-ts` and `omnist-rs` have each since
built their own equivalents the same way. A fourth port should too —
see [Porting a Conformance Runner](porting-a-conformance-runner.md) for
what all three existing ones learned building theirs.
