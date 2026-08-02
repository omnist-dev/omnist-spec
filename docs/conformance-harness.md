# OML/OSD Conformance Harness

*Normative for any implementation that opts into this track. See
[§8.6](08-conformance-and-errors.md#86-omloscd-conformance-harness) for how
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

| Operation | Real command | Success (stdout) | Exit code |
|---|---|---|---|
| `write` | `omnist format INPUT [--compact] [-o FILE]` | canonical OML | 0 |
| `validate` | `omnist validate INPUT --from oml --schema SCHEMA --json` | `{"ok": true}` | 0 (ok), 1 (validation failure, `errors` populated), 2 (parse/read error, `errors` empty) |
| `materialize` | `omnist convert INPUT --from oml --to oml --schema SCHEMA` | materialized OML | 0, or 2 on inexact conversion/shape failure (verified: message format matches §7.2's error text, e.g. `$.d: 'not-a-date' cannot be read as date (not a value-exact conversion)`) |
| `normalize` | `omnist schema normalize SCHEMA [--compact] [-o FILE]` | OSD | 0 |
| `prune` | `omnist schema prune SCHEMA [--compact] [-o FILE]` | OSD | 0 |
| `extract` | `omnist schema extract SCHEMA --keep label1,label2,... [--compact] [-o FILE]` | OSD | 0, non-zero if `keep` invalidates the root (§6.9) |
| `is_empty` | `omnist schema is-empty SCHEMA --result-format json` | `{"empty": bool}` | **0 if empty (`true`), 1 if not empty (`false`)** — the boolean result is encoded in the exit code too, not just stdout; do not assume 0 always means "command succeeded" for this command |
| `compatible_with` | `omnist schema compatible-with A B --result-format json` | `{"compatible": bool}` | 0 if `true`, 1 if `false` — same exit-code-carries-the-boolean pattern |
| `equivalent` | `omnist schema equivalent A B --result-format json` | `{"equivalent": bool}` | 0 if `true`, 1 if `false` |
| `infer` | `omnist infer FILE [FILE...] --from oml [--allow-any] [--compact] [-o FILE]` — **multiple positional document files, one per sample; not a single stdin stream** | OSD | 0, non-zero on ambiguous type without `--allow-any` |
| `lint` | `omnist schema lint SCHEMA --json [--severity info\|warning]` | `{"ok": bool, "findings": [{"code","severity","location","message"}]}` — `ok` is `false` iff any `warning`-severity finding is present | 0 (always — findings are informational output, not a command failure) |

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

Every row above (except `materialize`) was checked directly against
`omnist/cli.py` source for this revision, including `lint`'s exact `--json`
output shape, which the previous revision had left as an unverified guess.

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
        return omnist.ops.isomorphic.is_isomorphic(actual, expected)
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

This requires `Field.__eq__`, `Record.__eq__`, and `Schema.__eq__` to exist
in the Python library — confirmed, as of this writing, that they do not
(§5, below). `omnist`'s existing `ops/isomorphic.py` already backs
`is_isomorphic`, so the `isomorphic` mode needs no new library code.

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

A Python script/package under `conformance/orchestrator/`. Reads a manifest
naming which fixtures to run and which implementation CLI to invoke (a
command name, e.g. `omnist` — resolved from `PATH`, not hardcoded to a
location), runs each fixture's operation through that CLI, applies §4's
comparison, and reports pass/fail/skip per fixture — reusing §8.5.5's
reporting discipline (skip is a first-class result, never silently folded
into pass).

**Out of scope for this revision:** wiring the orchestrator against
TypeScript or Rust CLIs, CI integration, and fixture volume beyond the
referee self-test set. These are deferred, not declined — tracked
separately once Python-only support is working end to end.
