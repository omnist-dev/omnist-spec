# OML/OSD Conformance Harness

Implements [`docs/conformance-harness.md`](../docs/conformance-harness.md) —
see that file for the full spec (CLI wrapper contract, fixture format,
comparison algorithm). This README is orientation, not a second definition.

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
  orchestrator/
    referee.py             structural comparison (Sec4) -- Document via
                            Doc.__eq__, Schema via exact/isomorphic modes
    cli_runner.py           invokes the real omnist CLI per Sec2's
                            verified contract
    self_test.py            runs _referee-self-test/
    runner.py                runs the real per-operation fixtures
```

## Running it

Requires `omnist` on `PATH` (or set `OMNIST_CLI` to a different command
name/path).

```bash
python3 -m conformance.orchestrator.self_test      # referee self-check
python3 -m conformance.orchestrator.runner          # all wired operations
python3 -m conformance.orchestrator.runner validate normalize   # a subset
```

## Status

`extract`, `infer`, and `lint` have reserved fixture directories but no
runner wiring yet (`runner.py`'s `RUNNERS` dict) — running them reports
`skip`, not `pass` or `fail`, per §8.5.5's discipline. Fixture volume beyond
what's here is a deliberate follow-up, not an oversight — see
[omnist-spec#25](https://github.com/omnist-dev/omnist-spec/issues/25).

Two `omnist` gaps were found and fixed while building this:
[omnist#277](https://github.com/omnist-dev/omnist/issues/277) (no CLI path
to `materialize` — fixed, 0.7.16) and
[omnist#279](https://github.com/omnist-dev/omnist/issues/279) (isomorphic
schema comparison has no public API — not blocking, `referee.py` uses the
private function with a tracked comment pending a public one).
