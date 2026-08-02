"""Runs real (non-self-test) fixtures under conformance/fixtures/<operation>/
against the omnist CLI, per docs/conformance-harness.md Sec3's fixture
format and Sec2's verified CLI contract. Sec8.5.5's reporting discipline:
pass, fail, or skip -- skip is first-class, never folded into pass.

Usage: python3 -m conformance.orchestrator.runner [operation ...]
  (with no arguments, runs every operation directory that has fixtures)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import cli_runner
from .referee import compare_document, compare_schema

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# Operations with real fixtures wired up so far. Others (extract, infer,
# lint) have directories reserved (per issue #25's scope) but no runner
# wiring yet -- listed here so `skip` is explicit and visible, not a
# silent absence.
WIRED_OPERATIONS = {"write", "validate", "materialize", "normalize", "prune",
                     "is_empty", "compatible_with", "equivalent"}
ALL_OPERATIONS = {"write", "validate", "materialize", "normalize", "prune",
                  "extract", "is_empty", "compatible_with", "equivalent",
                  "infer", "lint"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _purpose(case_dir: Path) -> str:
    p = case_dir / "purpose.txt"
    return _read(p).splitlines()[0] if p.exists() else ""


def run_write(case_dir: Path) -> tuple[str, str]:
    stdout, stderr, code = cli_runner.write(case_dir / "input.oml")
    if code != 0:
        return "fail", f"exit {code}: {stderr.strip()}"
    expected = _read(case_dir / "expected.oml")
    if compare_document(stdout, expected):
        return "pass", "ok"
    return "fail", "output does not match expected (structural comparison)"


def run_validate(case_dir: Path) -> tuple[str, str]:
    stdout, stderr, code = cli_runner.validate(case_dir / "input.oml", case_dir / "schema.osd")
    expect_ok = _read(case_dir / "expected" / "ok.txt").strip() == "true"
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return "fail", f"non-JSON stdout: {stdout!r}"
    if payload.get("ok") != expect_ok:
        return "fail", f"expected ok={expect_ok}, got {payload.get('ok')}"
    return "pass", "ok"


def run_materialize(case_dir: Path) -> tuple[str, str]:
    stdout, stderr, code = cli_runner.materialize(case_dir / "input.oml", case_dir / "schema.osd")
    expect_ok = _read(case_dir / "expected" / "ok.txt").strip() == "true"
    if expect_ok:
        if code != 0:
            return "fail", f"expected success, got exit {code}: {stderr.strip()}"
        expected = _read(case_dir / "expected" / "output.oml")
        if compare_document(stdout, expected):
            return "pass", "ok"
        return "fail", "materialized output does not match expected"
    else:
        if code == 0:
            return "fail", "expected failure, command succeeded"
        return "pass", "ok"


def _run_schema_producing(case_dir: Path, cli_fn) -> tuple[str, str]:
    stdout, stderr, code = cli_fn(case_dir / "input.osd")
    if code != 0:
        return "fail", f"exit {code}: {stderr.strip()}"
    expected = _read(case_dir / "expected.osd")
    if compare_schema(stdout, expected, mode="exact"):
        return "pass", "ok"
    return "fail", "output schema does not match expected (exact structural comparison)"


def run_normalize(case_dir: Path) -> tuple[str, str]:
    return _run_schema_producing(case_dir, cli_runner.normalize)


def run_prune(case_dir: Path) -> tuple[str, str]:
    return _run_schema_producing(case_dir, cli_runner.prune)


def _run_boolean(case_dir: Path, cli_fn, key: str, *, two_input: bool) -> tuple[str, str]:
    if two_input:
        stdout, stderr, code = cli_fn(case_dir / "a.osd", case_dir / "b.osd")
    else:
        stdout, stderr, code = cli_fn(case_dir / "input.osd")
    expect = _read(case_dir / "expected.txt").strip() == "true"
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return "fail", f"non-JSON stdout: {stdout!r}"
    if payload.get(key) != expect:
        return "fail", f"expected {key}={expect}, got {payload.get(key)}"
    return "pass", "ok"


def run_is_empty(case_dir: Path) -> tuple[str, str]:
    return _run_boolean(case_dir, cli_runner.is_empty, "empty", two_input=False)


def run_compatible_with(case_dir: Path) -> tuple[str, str]:
    return _run_boolean(case_dir, cli_runner.compatible_with, "compatible", two_input=True)


def run_equivalent(case_dir: Path) -> tuple[str, str]:
    return _run_boolean(case_dir, cli_runner.equivalent, "equivalent", two_input=True)


RUNNERS = {
    "write": run_write,
    "validate": run_validate,
    "materialize": run_materialize,
    "normalize": run_normalize,
    "prune": run_prune,
    "is_empty": run_is_empty,
    "compatible_with": run_compatible_with,
    "equivalent": run_equivalent,
}


def run_operation(operation: str) -> tuple[int, int, int]:
    """Returns (passed, failed, skipped) counts for one operation directory."""
    op_dir = FIXTURES_DIR / operation
    if not op_dir.is_dir():
        return 0, 0, 0
    cases = sorted(p for p in op_dir.iterdir() if p.is_dir())
    if not cases:
        return 0, 0, 0

    runner_fn = RUNNERS.get(operation)
    passed = failed = skipped = 0
    for case_dir in cases:
        purpose = _purpose(case_dir)
        if runner_fn is None:
            print(f"[SKIP] {operation}/{case_dir.name} ({purpose}): "
                  f"no runner wired up yet for this operation")
            skipped += 1
            continue
        status, message = runner_fn(case_dir)
        print(f"[{status.upper()}] {operation}/{case_dir.name} ({purpose}): {message}")
        if status == "pass":
            passed += 1
        else:
            failed += 1
    return passed, failed, skipped


def main(argv: list[str]) -> int:
    operations = argv or sorted(ALL_OPERATIONS)
    total_pass = total_fail = total_skip = 0
    for op in operations:
        p, f, s = run_operation(op)
        total_pass += p
        total_fail += f
        total_skip += s

    print(f"\n{total_pass} passed, {total_fail} failed, {total_skip} skipped "
          f"(across {len(operations)} operation(s))")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
