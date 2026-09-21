#!/usr/bin/env python3
"""Every normative paragraph must carry a citable rule number.

A requirement nobody can cite is a requirement nobody can point at in a
review, a bug report, or a conformance discussion -- and one nothing
structurally guarantees is complete. That was the single largest finding of
this spec's 2026-09 quality audit: five chapters carried roughly 98
MUST-level requirements between them with no anchors at all.

Every normative chapter is enforced here; omnist-spec#63 closed the last
gap, chapters 2 and 3, whose D- and S- spines existed but left 22 normative
paragraphs outside them.

Table rows count. A row is a paragraph in disguise: `docs/03-schema-model.md`
carried a MUST-level requirement on `infer` and `any` inside a table cell,
unrestated anywhere in prose and uncitable, which an earlier version of this
script skipped wholesale.

A citable number also has to mean one thing. Since v0.21.0-beta this script
also fails when a rule label is *defined* twice -- omnist-spec#105's first
head gave a new rule the `E-26` that v0.20.0-beta had already spent on an
unrelated one, and nothing here noticed.
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
    "docs/02-document-model.md": "D",
    "docs/03-schema-model.md": "S",
}

# Every normative chapter is enforced. Chapters 2 and 3 joined the set once
# omnist-spec#93 closed the 22 paragraphs that sat outside their existing
# D- and S- spines -- a gap invisible until this script existed.
REPORTED: dict[str, str] = {}

NORMATIVE = re.compile(r"\bMUST\b|\bSHALL\b")

# Where each rule namespace is defined. A label may be *cited* anywhere; it
# may be *defined* only in its owning file, which is what makes the
# duplicate check below precise: the ledger leads paragraphs with
# `**OSD-15, canonical escaping.**`, which is a citation of chapter 5's rule
# used as a heading, not a second definition of it.
DEFINING_FILE = dict(
    (path, prefix) for path, prefix in ENFORCED.items()
)
DEFINING_FILE["docs/09-divergence-ledger.md"] = "DIV"

# A definition is a bold label opening a paragraph or a list item:
#
#     **E-24. A precondition this spec imposes ...
#     - **E-21. Documented divergence.** ...
#     **E-20.** **A skip MUST cite a reason ...
#     **DIV-6. No port's conformance runner reads ...
#
# The label must be followed by `.`, `,`, or the closing `**`, which is what
# separates a definition from a citation mid-sentence (`per E-24, the code
# is ...`) or a bolded cross-reference inside running text. Sub-rules carry
# their own letter (`E-4a`) and are separate labels, not repeats of `E-4`.
DEFINITION = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+|\d+\.[ \t]+)?\*\*"
    r"(?P<label>(?:D|S|A|C|E|R|OML|OSD|DIV)-\d+[a-z]?)"
    r"(?=[.,]|\*\*)"
)


def duplicate_definitions() -> list[str]:
    """Fail when one rule label is defined twice.

    omnist-spec#105's first head shipped a second `E-26` -- a new rule given
    a number v0.20.0-beta had already spent on an unrelated one -- and every
    check in this repo stayed green. A spent number silently coming to mean
    two things is the same failure the ledger's retired `DIV-1`/`DIV-2`
    preamble guards against by hand, applied to every namespace.
    """
    seen: dict[str, list[str]] = {}
    for rel, prefix in DEFINING_FILE.items():
        path = ROOT / rel
        lines = path.read_text(encoding="utf-8").splitlines()
        in_fence = False
        for lineno, line in enumerate(lines, start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = DEFINITION.match(line)
            if not m:
                continue
            label = m.group("label")
            # Only a label from this file's own namespace is a definition
            # here; anything else is a citation being used as a heading.
            if label.rsplit("-", 1)[0] != prefix:
                continue
            seen.setdefault(label, []).append(f"{rel}:{lineno}")

    errors = []
    for label, places in sorted(seen.items()):
        if len(places) > 1:
            errors.append(
                f"rule {label} is defined {len(places)} times: "
                + ", ".join(places)
            )
    return errors


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


TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _rules(lines: list[str]):
    """Split paragraphs further, so each bullet or table row is its own rule.

    A table row states a requirement as much as a paragraph does, and it can
    only be cited if it carries a rule number of its own. The alignment row
    (`|---|---|`) is layout, never a requirement.
    """
    for block in _paragraphs(lines):
        items, cur = [], []
        for i in block:
            row = lines[i].lstrip().startswith("|")
            if (row or re.match(r"\s*[-*] ", lines[i])) and cur:
                items.append(cur)
                cur = [i]
            else:
                cur.append(i)
        if cur:
            items.append(cur)
        for item in items:
            if TABLE_SEP.match(lines[item[0]]):
                continue
            yield item


def gaps_in(path: str, prefix: str) -> list[tuple[int, str]]:
    lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
    tag = re.compile(rf"\b{re.escape(prefix)}-\d+\b")
    out = []
    for item in _rules(lines):
        text = " ".join(lines[i] for i in item)
        if not NORMATIVE.search(text):
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
        print(f"{path}: {note} (reported, not enforced)")

    dupes = duplicate_definitions()
    if dupes:
        failed = True
        print(f"error: {len(dupes)} rule number(s) defined more than once:",
              file=sys.stderr)
        for line in dupes:
            print(f"  {line}", file=sys.stderr)
    else:
        print("rule numbers: every definition is unique within its namespace")

    if failed:
        print("\nEvery normative paragraph needs a citable rule number, and "
              "every rule number needs exactly one definition.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
