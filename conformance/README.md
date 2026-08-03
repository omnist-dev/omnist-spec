# OML/OSD Conformance Harness

This repo owns the **fixtures and the spec** — the genuinely portable,
implementation-agnostic parts of the harness. It does not own a runner.
See [`docs/conformance-harness.md`](../docs/conformance-harness.md) for
the full spec (CLI wrapper contract, fixture format, comparison
algorithm); this README is orientation, not a second definition.

## Layout

```
conformance/
  fixtures/
    _referee-self-test/   hand-verified cases proving the comparison logic
                           itself is trustworthy (Sec6) -- no CLI invoked
    write/ validate/ materialize/ normalize/ prune/ extract/
    is_empty/ compatible_with/ equivalent/ infer/ lint/
                           one directory per operation, per Sec3's fixture
                           format
```

## Who runs these fixtures

Each implementation owns its own runner — a referee doing structural
comparison per Sec4, a thin wrapper invoking that implementation's own
CLI per Sec2's contract, and pass/fail/skip reporting per Sec8.5.5's
discipline (skip is first-class, never folded into pass).

`omnist` (Python)'s runner lives in that repo at `tools/conformance/`
(`referee.py`, `cli_runner.py`, `runner.py`, `self_test.py`), consuming
this repo's fixtures via a pinned git submodule
(`vendor/omnist-spec`, tagged, not tracking `master`) and wired into
that repo's own CI — see its `tools/conformance/README.md` for the
bump procedure. This mirrors the same split used for the JSON-vector
suite (`test-suite/`), whose runner (`tools/conformance/vector_runner.py`)
lives in the same place for the same reason.

A TypeScript or Rust port will eventually need its own equivalent
runner in its own repo — not a dependency on `omnist`'s Python one,
and not something this repo provides.

## Status

All 11 operations have fixtures here (19 real fixtures plus the
10-case referee self-test), verified passing against `omnist`'s own
runner. Fixture volume beyond what's here is a deliberate follow-up,
not an oversight — see
[omnist-spec#25](https://github.com/omnist-dev/omnist-spec/issues/25).

Two `omnist` gaps were found and fixed while this track was originally
built here (before the orchestrator moved to `omnist#283`):
[omnist#277](https://github.com/omnist-dev/omnist/issues/277) (no CLI path
to `materialize` — fixed, 0.7.16) and
[omnist#279](https://github.com/omnist-dev/omnist/issues/279) (isomorphic
schema comparison had no public API — fixed, 0.7.17: `Schema.isomorphic_to()`).
