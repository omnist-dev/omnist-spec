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

Since omnist-spec#149 the gate also covers SHOULD, not
only MUST/SHALL; counts a letter-suffixed label (`R-3a`) as a rule number;
sees definitions that sit in a table cell (`| `infer` | **S-21.** ...`) or
inline (`**A-9:**`, `**(A-10)**`, `**Determinism requirement (A-5).**`); and fails when a document cites a rule
number nothing defines.

The remaining findings that predate the gate live in
`tools/rule_coverage_baseline.txt` (kind|file|identity). A finding not in the
baseline fails CI; a baseline line that no longer applies also fails, so the
file only shrinks. Kinds: cited-not-defined (a normative paragraph that cites
its chapter's rule without defining one), outside-spine (osd-oml.md, read-only
until #53), out-of-order (chapter 6 only), unvectored-should (a SHOULD rule no
vector names). A vector that cites an undefined rule number also fails.
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
#
# Citation-only enforcement (omnist-spec#149, v0.35.0-beta): the per-format
# pages, the porting guide, the conformance harness and the glossary restate
# or apply rules that other chapters own, and have no rule-number spine of
# their own. Each normative paragraph in them MUST cite a rule number of any
# namespace (`(C-10)`, `[E-7](...)`), so that a requirement stated here points
# at the one place that owns it; the paragraphs are not themselves numbered,
# and a citation must resolve (dangling_citations). A paragraph with no owning
# rule yet goes in UNNUMBERED, with a reason, until it is numbered.
CITATION_ONLY = [
    "docs/formats/json.md",
    "docs/formats/oml.md",
    "docs/formats/overview.md",
    "docs/formats/toml.md",
    "docs/formats/xml.md",
    "docs/formats/yaml.md",
    "docs/porting-a-conformance-runner.md",
    "docs/conformance-harness.md",
    "docs/01-glossary.md",
]

# Reported, not enforced: normative text that has no rule-number spine to be
# held to.
#   - extensions/osd-oml.md has an R- spine (R-1..R-23), but E.7, E.8, E.10
#     and E.11 carry MUST paragraphs outside it, and the extension is still
#     being rewritten (omnist-spec#53), so renumbering now would collide.
REPORTED: dict[str, str | None] = {
    "docs/extensions/osd-oml.md": "R",
}

# SHOULD counts as normative too (MAY does not: it grants, it does not bind).
NORMATIVE = re.compile(r"\bMUST\b|\bSHALL\b|\bSHOULD\b")

# A normative paragraph that genuinely has no rule number yet, and that the
# spec owner has not decided how to number. Matched by the start of the
# paragraph's first line; every entry needs a reason, and the check fails if
# an entry stops matching, so this list cannot rot.
UNNUMBERED = {
    ("docs/07-codecs-and-deserialization.md",
     "A reader or writer SHOULD be able to report the adjustments"):
        "7.4 format reports: a SHOULD with no C- rule; numbering it is a "
        "spec-owner decision",
    ("docs/formats/json.md", "**Bare nested arrays are rejected.**"):
        "JSON reader refusal with no owning rule; number it when next edited",
    ("docs/formats/yaml.md", "**A second sharp edge, real enough to have a name"):
        "a YAML boolean key is refused because a label is a string (2.2.2); "
        "no rule numbers the refusal yet",
    ("docs/conformance-harness.md", "- **Format is explicit, not assumed.**"):
        "Track 1 CLI wrapper contract; 8.6 delegates it here and no E- rule "
        "owns it",
    ("docs/conformance-harness.md", "- **Schema-producing commands accept `--compact`**"):
        "Track 1 CLI wrapper contract; no E- rule owns it",
    ("docs/conformance-harness.md", "**`is_empty`/`compatible_with`/`equivalent` encode"):
        "Track 1 CLI wrapper contract; no E- rule owns it",
    ("docs/conformance-harness.md", "- `Record.__eq__`"):
        "Track 1 referee comparison (harness section 4); no E- rule owns it",
    ("docs/conformance-harness.md", "- `Schema.__eq__`"):
        "Track 1 referee comparison (harness section 4); no E- rule owns it",
}

# Where each rule namespace is defined. A label may be *cited* anywhere; it
# may be *defined* only in its owning file, which is what makes the
# duplicate check below precise: the ledger leads paragraphs with
# `**OSD-15, canonical escaping.**`, which is a citation of chapter 5's rule
# used as a heading, not a second definition of it.
DEFINING_FILE = dict(
    (path, prefix) for path, prefix in ENFORCED.items()
)
DEFINING_FILE["docs/09-divergence-ledger.md"] = "DIV"
DEFINING_FILE["docs/extensions/osd-oml.md"] = "R"

# A definition is a bold label opening a paragraph or a list item:
#
#     **E-24. A precondition this spec imposes ...
#     - **E-21. Documented divergence.** ...
#     **E-20.** **A skip MUST cite a reason ...
#     **DIV-5. OSD-14 has no vector, so its adoption ...
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

# Definitions that do not open the line: a table cell
# (`| `infer` | **S-21.** ...`), and the inline forms chapter 6 uses
# (`**A-9:** ...`, `**(A-10)** ...`). `**S-9** applies` is a citation: the
# label closes the bold with nothing after it inside.
INLINE_DEFINITION = re.compile(
    r"\*\*(?:\((?P<paren>(?:D|S|A|C|E|R|OML|OSD|DIV)-\d+[a-z]?)\)"
    r"|(?P<label>(?:D|S|A|C|E|R|OML|OSD|DIV)-\d+[a-z]?)(?=[.:,]))"
)

# A bold run-in title that ends in a label (`**Determinism requirement
# (A-5).**`). It is a definition only when nothing else defines that label:
# chapter 2 has `**On writers (D-15).**`, a sub-heading *citing* a rule
# defined elsewhere, which must not count as a second definition.
TITLE_DEFINITION = re.compile(
    r"\*\*[^*\n]*?\((?P<label>(?:D|S|A|C|E|R|OML|OSD|DIV)-\d+[a-z]?)\)\.?\*\*"
)


def definitions_in(line: str) -> list[str]:
    """Every rule label a line defines, at line start or inline."""
    found = []
    m = DEFINITION.match(line)
    if m:
        found.append(m.group("label"))
    for m in INLINE_DEFINITION.finditer(line):
        label = m.group("paren") or m.group("label")
        if label not in found:
            found.append(label)
    return found


def title_definitions_in(line: str) -> list[str]:
    return [m.group("label") for m in TITLE_DEFINITION.finditer(line)]


def duplicate_definitions() -> list[str]:
    """Fail when one rule label is defined twice.

    omnist-spec#105's first head shipped a second `E-26` -- a new rule given
    a number v0.20.0-beta had already spent on an unrelated one -- and every
    check in this repo stayed green. A spent number silently coming to mean
    two things is the same failure the ledger's retired `DIV-1`/`DIV-2`
    preamble guards against by hand, applied to every namespace.
    """
    seen: dict[str, list[str]] = {}
    titles: dict[str, list[str]] = {}
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
            for label in definitions_in(line):
                # Only a label from this file's own namespace is a
                # definition here; anything else is a citation being used
                # as a heading.
                if label.rsplit("-", 1)[0] != prefix:
                    continue
                seen.setdefault(label, []).append(f"{rel}:{lineno}")
            for label in title_definitions_in(line):
                if label.rsplit("-", 1)[0] == prefix:
                    titles.setdefault(label, []).append(f"{rel}:{lineno}")

    for label, places in titles.items():
        if label not in seen:
            seen[label] = places[:1]

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


ANY_LABEL = r"(?:D|S|A|C|E|R|OML|OSD)"


def gaps_in(path: str, prefix: str | None) -> list[tuple[int, str]]:
    lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
    # `R-3a` is a rule number: the letter suffix must not defeat `\b`.
    tag = re.compile(
        rf"\b{re.escape(prefix) if prefix else ANY_LABEL}-\d+[a-z]?\b")
    out = []
    for item in _rules(lines):
        text = " ".join(lines[i] for i in item)
        if not NORMATIVE.search(text):
            continue
        if not tag.search(text):
            first = lines[item[0]].strip()
            if any(path == p and first.startswith(start)
                   for (p, start) in UNNUMBERED):
                continue
            out.append((item[0] + 1, first[:88]))
    return out


def stale_exemptions() -> list[str]:
    """An UNNUMBERED entry that no longer matches a paragraph is an error."""
    errors = []
    for (path, start), reason in UNNUMBERED.items():
        lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
        hit = any(lines[item[0]].strip().startswith(start)
                  and NORMATIVE.search(" ".join(lines[i] for i in item))
                  for item in _rules(lines))
        if not hit:
            errors.append(f"{path}: the UNNUMBERED exemption {start!r} "
                          f"matches no normative paragraph any more; "
                          f"remove it ({reason})")
    return errors


# --- citations must resolve ---------------------------------------------------

CITE = re.compile(r"(?<![\w-])((?:D|S|A|C|E|R|OML|OSD)-\d+[a-z]?)(?![\w-])")


def all_definitions() -> set[str]:
    """Every defined label, from each namespace's owning file."""
    defined: set[str] = set()
    for rel, prefix in DEFINING_FILE.items():
        in_fence = False
        for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                defined.update(
                    d for d in definitions_in(line) + title_definitions_in(line)
                    if d.rsplit("-", 1)[0] == prefix)
    return defined


def citation_files() -> list[pathlib.Path]:
    """Prose that cites rule numbers. The CHANGELOG is history (it cites
    numbers as they stood in their release), and DIV- numbers are exempt:
    a closed divergence leaves the ledger by design, so a citation of it is
    a pointer into history, not into the current text."""
    files = sorted((ROOT / "docs").rglob("*.md"))
    files += [ROOT / "README.md", ROOT / "test-suite" / "README.md",
              ROOT / "conformance" / "README.md"]
    return [f for f in files if f.is_file()]


def dangling_citations() -> list[str]:
    defined = all_definitions()
    bases = {re.sub(r"[a-z]$", "", d) for d in defined}
    errors = []
    for path in citation_files():
        rel = path.relative_to(ROOT).as_posix()
        in_fence = False
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in CITE.finditer(line):
                label = m.group(1)
                # `E-4a` is satisfied by a defined `E-4a`; a bare `E-4` by
                # `E-4` or by any of its lettered sub-rules.
                if label in defined or label in bases:
                    continue
                errors.append(f"{rel}:{lineno}: cites {label}, which "
                              f"nothing defines")
    return errors


RANGE_CLAIM = re.compile(
    r"numbered \*\*(?P<p>[A-Z]+)-1\*\* through \*\*(?P=p)-(?P<n>\d+)\*\*")


def stale_range_claims() -> list[str]:
    """A chapter that says "numbered A-1 through A-23" must have defined
    exactly that many: a rule added past the stated end, or a stated end
    nothing reaches, is a count gone stale."""
    defined = all_definitions()
    errors = []
    for path in citation_files():
        text = path.read_text(encoding="utf-8")
        for m in RANGE_CLAIM.finditer(text):
            prefix, claimed = m.group("p"), int(m.group("n"))
            nums = [int(d.rsplit("-", 1)[1].rstrip("abcdefghijklmnopqrstuvwxyz"))
                    for d in defined if d.rsplit("-", 1)[0] == prefix]
            top = max(nums, default=0)
            if top != claimed:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: says {prefix}-1 "
                    f"through {prefix}-{claimed}, but the highest {prefix}- "
                    f"rule defined is {prefix}-{top}")
    return errors


BASELINE = ROOT / "tools" / "rule_coverage_baseline.txt"


def _ident(text: str) -> str:
    """A stable, line-number-free identity for a paragraph: its opening words."""
    return re.sub(r"\s+", " ", text.strip())[:70].rstrip().replace("|", "/")


def cited_not_defined(path: str, prefix: str) -> list[str]:
    """Normative paragraphs that cite a rule of this namespace without
    defining one. `gaps_in` is satisfied by any same-namespace number, so a
    paragraph that merely mentions `E-5` passes; most of these are
    continuation paragraphs of the rule above them. Tracked against the
    baseline: no new one may appear (omnist-spec#149)."""
    lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
    out = []
    for item in _rules(lines):
        text = " ".join(lines[i] for i in item)
        if NORMATIVE.search(text) and not any(
                d.rsplit("-", 1)[0] == prefix
                for i in item
                for d in definitions_in(lines[i]) + title_definitions_in(lines[i])):
            out.append(f"cited-not-defined|{path}|{_ident(lines[item[0]])}")
    return out


def outside_spine(path: str, prefix: str) -> list[str]:
    """Normative paragraphs in a file that owns a spine but carry none of its
    numbers. Read-only for osd-oml.md (still being rewritten, #53)."""
    return [f"outside-spine|{path}|{_ident(preview)}"
            for _, preview in gaps_in(path, prefix)]


def out_of_order() -> list[str]:
    """Chapter 6 numbers its rules in document order (almost: A-22 and A-23
    are documented exceptions, baselined). A label that breaks the order is
    reported minimally: the longest in-order subsequence is kept, the rest
    flagged (so A-22 and A-23, not A-14..A-21, when 22 and 23 sit early)."""
    out = []
    for rel, prefix in DEFINING_FILE.items():
        if prefix != "A":
            # Only chapter 6 promises document order; every other chapter
            # numbers by history (a rule added later takes the next free
            # number wherever it sits) and says so.
            continue
        seq: list[tuple[int, str]] = []
        seen: set[str] = set()
        in_fence = False
        for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for d in definitions_in(line) + title_definitions_in(line):
                if d.rsplit("-", 1)[0] == prefix and d not in seen:
                    seen.add(d)
                    seq.append((int(re.sub(r"\D", "", d.rsplit("-", 1)[1])), d))
        n = len(seq)
        best = [1] * n
        prev = [-1] * n
        for i in range(n):
            for j in range(i):
                if seq[j][0] <= seq[i][0] and best[j] + 1 > best[i]:
                    best[i], prev[i] = best[j] + 1, j
        keep: set[int] = set()
        if n:
            k = max(range(n), key=lambda i: best[i])
            while k != -1:
                keep.add(k)
                k = prev[k]
        out += [f"out-of-order|{rel}|{seq[i][1]}" for i in range(n) if i not in keep]
    return out


def vector_texts() -> list[tuple[str, str]]:
    """(file, text) for every prose field of every vector."""
    import json
    out = []
    for path in sorted((ROOT / "test-suite").glob("*/*.json")):
        rel = path.relative_to(ROOT).as_posix()
        for v in json.loads(path.read_text(encoding="utf-8"))["vectors"]:
            out.append((rel, " ".join(str(v.get(k, ""))
                                      for k in ("name", "spec", "comment"))))
    return out


def dangling_vector_citations() -> list[str]:
    """A vector naming a rule number nothing defines (a typo, or a rule
    that was renumbered out from under it)."""
    defined = all_definitions()
    bases = {re.sub(r"[a-z]$", "", d) for d in defined}
    errors = []
    for rel, text in vector_texts():
        for m in CITE.finditer(text):
            if m.group(1) not in defined and m.group(1) not in bases:
                errors.append(f"{rel}: a vector cites {m.group(1)}, which "
                              f"nothing defines")
    return sorted(set(errors))


def unvectored_should() -> list[str]:
    """A rule that carries a SHOULD is exactly the one an implementation can
    skip unnoticed. Each needs a vector that names its exact number in its
    own namespace (a vector citing a neighbouring rule does not count)."""
    named = set()
    for _, text in vector_texts():
        named.update(m.group(1) for m in CITE.finditer(text))
    out = []
    for path, prefix in ENFORCED.items():
        lines = (ROOT / path).read_text(encoding="utf-8").split("\n")
        for item in _rules(lines):
            text = " ".join(lines[i] for i in item)
            if not re.search(r"\bSHOULD\b", text):
                continue
            for i in item:
                for d in definitions_in(lines[i]) + title_definitions_in(lines[i]):
                    if d.rsplit("-", 1)[0] == prefix and d not in named:
                        out.append(f"unvectored-should|{path}|{d}")
    return sorted(set(out))


def load_baseline() -> set[str]:
    if not BASELINE.is_file():
        return set()
    return {ln.strip() for ln in BASELINE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")}


def baseline_findings() -> list[str]:
    found = list(unvectored_should()) + out_of_order()
    for path, prefix in REPORTED.items():
        if prefix:
            found += outside_spine(path, prefix)
    for path, prefix in ENFORCED.items():
        found += cited_not_defined(path, prefix)
    return found


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

    for path in CITATION_ONLY:
        gaps = gaps_in(path, None)
        if gaps:
            failed = True
            print(f"error: {path} has {len(gaps)} normative paragraph(s) "
                  f"citing no rule number (a citation of any rule is "
                  f"enough, or an UNNUMBERED entry with a reason):",
                  file=sys.stderr)
            for line_no, preview in gaps:
                print(f"  {path}:{line_no}: {preview}", file=sys.stderr)
        else:
            print(f"{path}: every normative paragraph cites a rule "
                  f"(citation-only)")

    found = baseline_findings()
    base = load_baseline()
    new = sorted(set(found) - base)
    stale = sorted(base - set(found))
    kinds: dict[str, int] = {}
    for f in found:
        k = f.split("|", 1)[0]
        kinds[k] = kinds.get(k, 0) + 1
    print("baseline (pre-existing, tools/rule_coverage_baseline.txt): "
          + (", ".join(f"{k}={v}" for k, v in sorted(kinds.items())) or "none"))
    if new:
        failed = True
        print(f"error: {len(new)} new finding(s) not in the baseline "
              f"(fix them; do not add to the baseline):", file=sys.stderr)
        for f in new:
            print(f"  {f}", file=sys.stderr)
    if stale:
        failed = True
        print(f"error: {len(stale)} baseline entr(y/ies) no longer apply; "
              f"delete them from the baseline:", file=sys.stderr)
        for f in stale:
            print(f"  {f}", file=sys.stderr)

    vdang = dangling_vector_citations()
    if vdang:
        failed = True
        print(f"error: {len(vdang)} vector citation(s) of an undefined rule:",
              file=sys.stderr)
        for line in vdang:
            print(f"  {line}", file=sys.stderr)
    else:
        print("vectors: every cited rule number is defined")

    for err in stale_exemptions():
        failed = True
        print(f"error: {err}", file=sys.stderr)

    for err in stale_range_claims():
        failed = True
        print(f"error: {err}", file=sys.stderr)

    dangling = dangling_citations()
    if dangling:
        failed = True
        print(f"error: {len(dangling)} citation(s) of a rule number that "
              f"nothing defines:", file=sys.stderr)
        for line in dangling:
            print(f"  {line}", file=sys.stderr)
    else:
        print("citations: every cited rule number is defined")

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
