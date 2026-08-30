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

import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (repo, ledger column index -- 0-based, matching the "| Version | ... |" row
# in docs/09-divergence-ledger.md's Sec9.3 table: Python, TypeScript, Rust,
# Go, Java in that order)
PORT_REPOS = [
    ("omnist", 0),
    ("omnist-ts", 1),
    ("omnist-rs", 2),
    ("omnist-go", 3),
    ("omnist-j", 4),
]


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


def latest_github_tag(repo: str) -> str | None:
    """Latest tag's name for omnist-dev/<repo>, via the public (unauthenticated)
    GitHub API. Returns None (not a failure) on any network/API problem --
    this check is best-effort against live state, not something that
    should block CI on a transient GitHub API hiccup or rate limit."""
    url = f"https://api.github.com/repos/omnist-dev/{repo}/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "omnist-spec-version-check"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tags = json.load(resp)
    except Exception as e:  # noqa: BLE001 -- deliberately broad, see docstring
        print(f"  (skipping {repo}: could not reach GitHub API -- {e})", file=sys.stderr)
        return None
    if not tags:
        return None
    return tags[0]["name"]


def check_ledger_versions() -> list[str]:
    """Sec9.3's Version row cites each port's version -- compare against
    that port's actual latest git tag. Best-effort: a port not being
    reachable is reported, not treated as a mismatch."""
    path = ROOT / "docs" / "09-divergence-ledger.md"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\| Version \|(.+)\|$", text, re.MULTILINE)
    if not m:
        return [f"{path}: could not find the '| Version | ... |' row in Sec9.3's table"]
    cells = [c.strip() for c in m.group(1).split("|") if c.strip()]
    problems = []
    for repo, idx in PORT_REPOS:
        if idx >= len(cells):
            problems.append(f"{path}: Version row has fewer cells than expected (missing {repo}?)")
            continue
        ledger_version = cells[idx]
        tag = latest_github_tag(repo)
        if tag is None:
            continue
        tag_version = tag.lstrip("v")
        if ledger_version != tag_version:
            problems.append(
                f"{path}: ledger says {repo} is {ledger_version!r}, "
                f"but its latest tag is {tag!r} ({tag_version!r})"
            )
    return problems


def main() -> int:
    latest = latest_changelog_version()
    problems = [p for check in CITATIONS if (p := check(latest))]
    problems += check_ledger_versions()
    if problems:
        print(f"CHANGELOG.md's latest entry is {latest!r}. Stale citations found:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"All known version citations match CHANGELOG.md's latest entry ({latest}), "
          f"and the divergence ledger's Version row matches every port's latest tag.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
