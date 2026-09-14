#!/usr/bin/env python3
"""Every normative paragraph must carry a citable rule number.

A requirement nobody can cite is a requirement nobody can point at in a
review, a bug report, or a conformance discussion -- and one nothing
structurally guarantees is complete. That was the single largest finding of
this spec's 2026-09 quality audit: five chapters carried roughly 98
MUST-level requirements between them with no anchors at all.

This script enforces the rule for chapters that have been brought up to
standard, and reports -- without failing -- the two that predate it. Chapters
2 and 3 have D- and S- spines already, but a handful of their normative
paragraphs sit outside those lists; see omnist-spec#63.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Chapters whose coverage is enforced: a gap here fails CI.
ENFORCED = {
    "docs/04-oml-grammar.md": "OML",
    "docs/05-osd-grammar.md": "OSD",
    "docs/06-schema-algebra.md": "A",
    "docs/07-codecs-and-deserialization.md": "C",
    "docs/08-conformance-and-errors.md": "E",
}

# Chapters reported but not enforced, pending #63's remaining work.
REPORTED = {
    "docs/02-document-model.md": "D",
    "docs/03-schema-model.md": "S",
}

NORMATIVE = re.compile(r"\bMUST\b|\bSHALL\b")


def _paragraphs(lines: list[str]):
    """Blank-line-delimited blocks, skipping fenced code."""
    in_fence, block = False, []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if block:
                yield block
                block = []
            continue
        if in_fence:
            continue
        if line.strip() == "":
            if block:
                yield block
                block = []
        else:
            block.append(i)
    if block:
        yield block


def _rules(lines: list[str]):
    """Split paragraphs further, so each bullet in a list is its own rule."""
    for block in _paragraphs(lines):
        items, cur = [], []
        for i in block:
            if re.match(r"\s*[-*] ", lines[i]) and cur:
                items.append(cur)
                cur = [i]
            else:
                cur.append(i)
        if cur:
            items.append(cur)
        yield from items


def gaps_in(path: str, prefix: str) -> list[tuple[int, str]]:
    lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
    tag = re.compile(rf"\b{re.escape(prefix)}-\d+\b")
    out = []
    for item in _rules(lines):
        text = " ".join(lines[i] for i in item)
        if not NORMATIVE.search(text):
            continue
        # A table row states its requirement in the table's own terms.
        if lines[item[0]].lstrip().startswith("|"):
            continue
        if not tag.search(text):
            out.append((item[0] + 1, lines[item[0]].strip()[:88]))
    return out


def main() -> int:
    failed = False

    for path, prefix in ENFORCED.items():
        gaps = gaps_in(path, prefix)
        if gaps:
            failed = True
            print(f"error: {path} has {len(gaps)} normative paragraph(s) "
                  f"with no {prefix}-N rule number:", file=sys.stderr)
            for line_no, preview in gaps:
                print(f"  {path}:{line_no}: {preview}", file=sys.stderr)
        else:
            print(f"{path}: covered ({prefix}-N)")

    for path, prefix in REPORTED.items():
        gaps = gaps_in(path, prefix)
        note = "covered" if not gaps else f"{len(gaps)} outside the {prefix}- spine"
        print(f"{path}: {note} (not enforced, see omnist-spec#63)")

    if failed:
        print("\nEvery normative paragraph needs a citable rule number.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
