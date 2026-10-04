#!/usr/bin/env python3
"""Run grammars/oml.abnf and grammars/osd.abnf against the conformance vectors.

The grammars are normative artifacts, and until this script existed nothing
ever executed them: the 2026-10-04 audit found that oml.abnf accepted
`a: 1 b: 2` (SEP matched a space-only run), rejected `a : 1`, and that
osd.abnf omitted whitespace altogether and so could not be run at all. This
check parses every text-valued vector with the `abnf` package (version pinned
in tools/requirements-grammars.txt) and compares *acceptance* with what the
vector expects:

  * OML: every `parse` vector whose input format is `oml`, every OSD-OML
    `parse_schema_oml` input, and every OML text a `write` / `write_schema_oml`
    vector expects, against `document` in oml.abnf.
  * OSD: every `parse_schema` vector against `schema` in osd.abnf.

A vector's text is expected to be ACCEPTED unless it expects failure with a
`parse.*` diagnostic, or (OSD only) with one of the `schema.*` codes the
parser raises for shapes osd.abnf itself excludes (OSD_SYNTACTIC_SCHEMA_CODES).
Any other `schema.*` failure is a context condition checked after parsing, and
the grammar accepts the text. Vectors given as
`bytes_hex` that are not valid UTF-8 are skipped: a grammar over characters
has nothing to say about them; decoding is stage 0.

ABNF cannot express the context conditions the grammar files list (T1-T4 for
OML, S1-S5 plus maximal munch for OSD) or the resource limits (OML sec 4.7).
Every vector whose acceptance the grammar CANNOT reproduce is listed in
CONTEXT_EXCEPTIONS below with the condition responsible. The list is exact in
both directions: an unlisted mismatch fails the run, and so does a listed
vector the grammar now gets right (a stale entry hides the next regression).

Run with the pinned package installed:  pip install -r
tools/requirements-grammars.txt && python3 tools/check_grammars.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from abnf import ParseError, Rule
except ImportError:
    print("error: the 'abnf' package is required "
          "(pip install -r tools/requirements-grammars.txt)", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "test-suite"

# vector name -> the context condition that makes the ABNF disagree with it.
T1 = "T1 (tokenizer priority: nan/inf are NUMBER, never a bare label)"
T2 = "T2 (a bare label is never null/true/false)"
T4 = "T4 (calendar/clock value ranges)"
ESC = "escape range condition (unpaired surrogate; stated in oml.abnf)"
CONTEXT_EXCEPTIONS: dict[str, str] = {
    "oml-grammar/reserved/nan-bare-is-a-number-token-not-a-label": T1,
    "oml-grammar/reserved/inf-bare-is-a-number-token-not-a-label": T1,
    "oml-grammar/reserved/null-bare-label-at-top-level-fails-on-trailing-colon": T2,
    "oml-grammar/reserved/true-bare-label-at-top-level-fails-on-trailing-colon": T2,
    "oml-grammar/reserved/null-bare-label-inside-a-node-is-the-reserved-word-error": T2,
    "oml-grammar/errors/unpaired-high-surrogate-is-an-error": ESC,
    "oml-grammar/temporals/date-with-out-of-range-month-is-an-error": T4,
    "oml-grammar/temporals/date-with-day-invalid-for-month-is-an-error": T4,
    "oml-grammar/temporals/february-29-in-a-non-leap-year-is-an-error": T4,
    "oml-grammar/temporals/leap-second-is-an-error": T4,
    "oml-grammar/temporals/tz-offset-minute-out-of-range-is-an-error": T4,
    "osd-grammar/cardinality/negative-minimum-is-invalid-not-a-syntax-error":
        "S4 (a '-' in a bound is a token-level choice: osd.abnf's `int` "
        "excludes it, the reference tokenizer accepts it and rejects it "
        "one step later)",
}

# OSD shapes the grammar itself excludes, though the vector's diagnostic is a
# `schema.*` code rather than `parse.*`: the reference reports them from the
# parser's own checks (S5, 5.5-5.7), so the ABNF rejecting them is correct.
OSD_SYNTACTIC_SCHEMA_CODES = {
    "schema.empty-cardinality",
    "schema.non-integer-cardinality",
    "schema.nullable-ref",
    "schema.nullable-any",
    "schema.unquoted-label",
    "schema.quoted-type",
}


def load(grammar: str, start: str):
    class GrammarRule(Rule):  # one registry per grammar: names collide
        pass

    GrammarRule.load_grammar((ROOT / "grammars" / grammar).read_text("utf-8"))
    return GrammarRule(start)


def vector_text(vec: dict, key: str) -> str | None:
    inp = vec["input"]
    if "text" in inp:
        return inp["text"]
    if "bytes_hex" in inp:
        try:
            return bytes.fromhex(inp["bytes_hex"]).decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None


def expects_accept(vec: dict) -> bool:
    exp = vec["expect"]
    if exp.get("ok") is not False:
        return True
    codes = [d.get("code", "") for d in exp.get("diagnostics", [])]
    if vec["operation"] == "parse_schema" and \
            any(c in OSD_SYNTACTIC_SCHEMA_CODES for c in codes):
        return False
    return not any(c.startswith("parse.") for c in codes)


def accepts(rule, text: str) -> bool:
    try:
        rule.parse_all(text)
        return True
    except ParseError:
        return False


def collect():
    """Yield (grammar, name, text, expected_accept) for every checked text."""
    for path in sorted(SUITE.glob("*/*.json")):
        for vec in json.loads(path.read_text("utf-8"))["vectors"]:
            op, inp = vec["operation"], vec["input"]
            name = vec["name"]
            if op == "parse" and inp.get("format") == "oml":
                text = vector_text(vec, "text")
                yield "oml", name, text, expects_accept(vec)
            elif op == "parse_schema_oml":
                yield "oml", name, vector_text(vec, "text"), expects_accept(vec)
            elif op == "write_schema_oml" and "text" in vec["expect"]:
                yield "oml", name, vec["expect"]["text"], True
            elif op == "write" and inp.get("format") == "oml" \
                    and "text" in vec["expect"]:
                yield "oml", name, vec["expect"]["text"], True
            elif op == "parse_schema":
                yield "osd", name, vector_text(vec, "text"), expects_accept(vec)


# Texts the grammars must REJECT, independent of any vector: ABNF literals are
# case-insensitive unless written %s, and a letter-valued terminal that is
# case-sensitive in the prose must not match the other case (OML-14 escape
# letters, the T of DATETIME, null/true/false/nan/inf, OSD keywords).
MUST_REJECT = {
    "oml": ['a: "\\N"', 'a: "\\B"', 'a: "\\U0041"', 'a: "\\T"',
            "a: 2024-01-01t10:30", "a: NULL", "a: True", "a: FALSE",
            "a: NAN", "a: INF"],
    "osd": ["Record R {}\nroot R", "record R {}\nRoot R"],
}


def main() -> int:
    rules = {"oml": load("oml.abnf", "document"),
             "osd": load("osd.abnf", "schema")}
    errors: list[str] = []
    for grammar, texts in MUST_REJECT.items():
        for text in texts:
            if accepts(rules[grammar], text):
                errors.append(f"{grammar}.abnf accepts {text!r}, which must "
                              f"be rejected (a case-insensitive literal?)")
    checked = {"oml": 0, "osd": 0}
    skipped = 0
    mismatches: list[tuple[str, str, bool]] = []
    for grammar, name, text, want in collect():
        if text is None:
            skipped += 1
            continue
        checked[grammar] += 1
        if accepts(rules[grammar], text) != want:
            mismatches.append((grammar, name, want))

    seen = {name for _, name, _ in mismatches}
    for grammar, name, want in mismatches:
        if name not in CONTEXT_EXCEPTIONS:
            errors.append(
                f"{grammar}.abnf {'rejects' if want else 'accepts'} the text "
                f"of {name!r}, which the vector says it "
                f"{'accepts' if want else 'rejects'} -- fix the grammar or, "
                f"if a context condition is responsible, list the vector in "
                f"CONTEXT_EXCEPTIONS")
    for name in sorted(set(CONTEXT_EXCEPTIONS) - seen):
        errors.append(f"CONTEXT_EXCEPTIONS lists {name!r}, but the grammar "
                      f"now agrees with the vector -- remove the entry")
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"oml.abnf: {checked['oml']} texts, osd.abnf: {checked['osd']} "
          f"texts checked against the vectors; {len(CONTEXT_EXCEPTIONS)} "
          f"context-condition exceptions; {skipped} non-UTF-8 inputs skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
