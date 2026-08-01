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

Every operation this track covers gets one CLI subcommand. The contract:

- **Primary input on stdin.** A document (OML) for document-consuming
  operations, a schema (OSD) for schema-consuming operations.
- **Secondary input, where an operation needs two,** as a file path
  argument — a schema file for `validate`/`materialize`, a second schema
  file for `compatible_with`/`equivalent`.
- **Successful result on stdout**, in the format matching the operation's
  result kind:
  - Document-producing (`write`): OML.
  - Schema-producing (`normalize`, `prune`, `extract`): OSD.
  - Boolean-result (`is_empty`, `compatible_with`, `equivalent`): exactly
    the literal token `true` or `false`, nothing else, followed by a single
    newline. Exit code is `0` regardless of which boolean was printed —
    exit code answers "did the command run," never "what was the answer."
  - `lint`: one finding per line, three tab-separated fields —
    `code<TAB>severity<TAB>location` — matching the fields already
    normative for a `LintFinding` (§6.11). Findings MUST be printed in the
    same deterministic `(code, location)` order §6.11 already requires, so
    line-by-line comparison is sufficient; no JSON parsing is needed for
    this one result kind.
- **Failure: non-zero exit, JSON diagnostics on stderr.** The array uses
  exactly §8.2's envelope — `code`, `path`, `message`, `severity` — the
  same one §8.5's JSON-vector track uses. This track does not define a
  second error vocabulary.

| Operation | Primary input (stdin) | Secondary input (arg) | Stdout on success |
|---|---|---|---|
| `write` | Document (OML) | — | OML |
| `validate` | Document (OML) | Schema (OSD, file arg) | *(no stdout; exit 0)* |
| `materialize` | Document (OML) | Schema (OSD, file arg) | OML |
| `normalize` | Schema (OSD) | — | OSD |
| `prune` | Schema (OSD) | — | OSD |
| `extract` | Schema (OSD) | `keep` label set (file arg, one label per line) | OSD |
| `is_empty` | Schema (OSD) | — | `true` / `false` |
| `compatible_with` | Schema (OSD) | Second schema (OSD, file arg) | `true` / `false` |
| `equivalent` | Schema (OSD) | Second schema (OSD, file arg) | `true` / `false` |
| `infer` | Sample documents (OML, one per line via a wrapping array, or newline-delimited — implementation's CLI already defines its own sample-batch convention; this contract does not re-specify it) | `--allow-any` flag, optional | OSD |
| `lint` | Schema (OSD) | — | `code<TAB>severity<TAB>location` lines |

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
