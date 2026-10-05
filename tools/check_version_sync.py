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
import os
import pathlib
import re
import sys
import time
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


STAGE_RANK = {"alpha": 0, "beta": 1, "rc": 2, "": 3}
VERSION = re.compile(r"v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z]+))?$")


def version_key(version: str) -> tuple[int, int, int, int]:
    """Orders vX.Y.Z-stage the way releases are ordered: by number, then
    alpha < beta < rc < a plain release. Raises on a shape it does not know."""
    m = VERSION.match(version)
    if not m:
        raise ValueError(f"unexpected version shape: {version!r}")
    stage = (m.group(4) or "").lower()
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)),
            STAGE_RANK.get(stage, -1))


def changelog_versions() -> list[str]:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    return re.findall(r"^## (v\d+\.\d+\.\d+(?:-[a-zA-Z]+)?)", text,
                      re.MULTILINE)


def latest_changelog_version() -> str:
    versions = changelog_versions()
    if not versions:
        raise SystemExit("could not find a '## vX.Y.Z' heading in CHANGELOG.md")
    # The newest by version, not the first heading: an entry added at the
    # wrong end of the file must not silently become "latest".
    return max(versions, key=version_key)


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


def check_changelog_order(latest: str) -> str | None:
    first = changelog_versions()[0]
    if first != latest:
        return (f"CHANGELOG.md: the first entry is {first!r} but the newest "
                f"version in it is {latest!r}; entries must run newest first")
    return None


def vector_count() -> int:
    total = 0
    for path in sorted((ROOT / "test-suite").glob("*/*.json")):
        total += len(json.loads(path.read_text(encoding="utf-8"))["vectors"])
    return total


# Counts the ledger quotes next to a spec version. A count is only checked
# against the suite when the version quoted *is* the latest one: an older
# version legitimately had fewer vectors.
COUNT_QUOTES = [
    re.compile(r"suite is (?P<v>v\d+\.\d+\.\d+-[a-z]+), (?P<n>\d+) vectors"),
    re.compile(r"; (?P<n>\d+) at (?P<v>v\d+\.\d+\.\d+-[a-z]+)\)"),
]


def check_ledger_quotes(latest: str) -> list[str]:
    """Version and count quotes in the ledger must match the repo: every
    "Spec version pinned" cell names a released version no newer than the
    latest, and every vector count quoted for the latest version is the
    suite's real size."""
    path = ROOT / "docs" / "09-divergence-ledger.md"
    text = path.read_text(encoding="utf-8")
    problems = []
    released = set(changelog_versions())
    m = re.search(r"^\| Spec version pinned \|(.+)\|$", text, re.MULTILINE)
    if not m:
        problems.append(f"{path}: could not find the '| Spec version pinned | "
                        f"... |' row in Sec9.3's table")
    else:
        for cell in (c.strip() for c in m.group(1).split("|") if c.strip()):
            if cell not in released:
                problems.append(f"{path}: pinned spec version {cell!r} is not "
                                f"a CHANGELOG.md release")
            elif version_key(cell) > version_key(latest):
                problems.append(f"{path}: pinned spec version {cell!r} is "
                                f"newer than the latest, {latest!r}")
    actual = vector_count()
    seen = 0
    for pattern in COUNT_QUOTES:
        found = list(pattern.finditer(text))
        seen += len(found)
        for q in found:
            if q.group("v") == latest and int(q.group("n")) != actual:
                problems.append(
                    f"{path}: says {q.group('n')} vectors at {latest}, but "
                    f"test-suite/ holds {actual}")
    if not seen:
        problems.append(f"{path}: no vector-count quote matched; the quote "
                        f"patterns in tools/check_version_sync.py have rotted")
    return problems


CITATIONS = [check_index_h1, check_changelog_order]


class Unreachable(Exception):
    """The tags of a port could not be fetched."""


def latest_github_tag(repo: str) -> str | None:
    """Newest tag (by version, not by the API's listing order) of
    omnist-dev/<repo>. Retries a few times; raises Unreachable if GitHub
    cannot be reached, which main() turns into a failure unless --offline
    was given. A check that silently skips when offline is a check that
    passes while checking nothing. Uses $GITHUB_TOKEN when present (CI
    passes one, which lifts the unauthenticated rate limit)."""
    headers = {"User-Agent": "omnist-spec-version-check"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    url = f"https://api.github.com/repos/omnist-dev/{repo}/tags?per_page=100"
    last: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                tags = json.load(resp)
            break
        except Exception as e:  # noqa: BLE001 -- retried, then reported
            last = e
            time.sleep(2 * (attempt + 1))
    else:
        raise Unreachable(f"{repo}: {last}")
    names = []
    for t in tags:
        try:
            version_key(t["name"])
        except ValueError:
            continue  # a tag that is not a release version
        names.append(t["name"])
    if not names:
        return None
    return max(names, key=version_key)


def check_ledger_versions(offline: bool = False) -> list[str]:
    """Sec9.3's Version row cites each port's version -- compare against
    that port's actual latest git tag. A port that cannot be reached is a
    problem unless `offline` says the live check was skipped on purpose."""
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
        if offline:
            continue
        try:
            tag = latest_github_tag(repo)
        except Unreachable as e:
            problems.append(f"could not fetch tags ({e}); run with --offline "
                            f"to skip the live check on purpose")
            continue
        if tag is None:
            problems.append(f"{repo}: no release tag found")
            continue
        tag_version = tag.lstrip("v")
        if ledger_version != tag_version:
            problems.append(
                f"{path}: ledger says {repo} is {ledger_version!r}, "
                f"but its latest tag is {tag!r} ({tag_version!r})"
            )
    return problems


def main() -> int:
    offline = "--offline" in sys.argv[1:] or os.environ.get("OMNIST_OFFLINE") == "1"
    latest = latest_changelog_version()
    problems = [p for check in CITATIONS if (p := check(latest))]
    problems += check_ledger_quotes(latest)
    problems += check_ledger_versions(offline)
    if problems:
        print(f"CHANGELOG.md's latest entry is {latest!r}. Stale citations found:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    live = ("is not checked (--offline)" if offline
            else "matches every port's latest tag")
    print(f"All known version citations match CHANGELOG.md's latest entry "
          f"({latest}); the ledger's pinned versions are releases, its vector "
          f"counts match test-suite/, and its Version row {live}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
