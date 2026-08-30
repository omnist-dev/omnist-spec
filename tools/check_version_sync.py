#!/usr/bin/env python3
"""Fails if a known version citation in this repo disagrees with
CHANGELOG.md's own latest entry -- the single source of truth for this
repo's version. Exists because a version bump touched CHANGELOG.md but
missed docs/index.md's H1 on 2026-08-30 and shipped that way; this is
the same "grep the exact old string everywhere, don't trust a
single-file diff" gotcha every omnist port's own docs already warn
about, applied to the spec repo itself.

Add a new (path, checker) pair to CITATIONS below for any other file
found to cite the version -- don't special-case new fixes.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def latest_changelog_version() -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## (v\d+\.\d+\.\d+(?:-[a-zA-Z]+)?)", text, re.MULTILINE)
    if not m:
        raise SystemExit("could not find a '## vX.Y.Z' heading in CHANGELOG.md")
    return m.group(1)


def major_minor(version: str) -> str:
    m = re.match(r"v(\d+)\.(\d+)\.\d+", version)
    if not m:
        raise SystemExit(f"unexpected version shape: {version!r}")
    return f"v{m.group(1)}.{m.group(2)}"


def check_index_h1(latest: str) -> str | None:
    path = ROOT / "docs" / "index.md"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^# Omnist Specification, (v\d+\.\d+)", text, re.MULTILINE)
    if not m:
        return f"{path}: could not find the 'Omnist Specification, vX.Y' H1 at all"
    want = major_minor(latest)
    got = m.group(1)
    if got != want:
        return f"{path}: H1 says {got!r}, CHANGELOG.md's latest entry is {latest!r} (expected {want!r})"
    return None


CITATIONS = [check_index_h1]


def main() -> int:
    latest = latest_changelog_version()
    problems = [p for check in CITATIONS if (p := check(latest))]
    if problems:
        print(f"CHANGELOG.md's latest entry is {latest!r}. Stale citations found:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"All known version citations match CHANGELOG.md's latest entry ({latest}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
