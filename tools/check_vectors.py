#!/usr/bin/env python3
"""Structural checks over the conformance vector suite.

Nothing in this repository parsed `test-suite/` before this script existed.
During the 2026-09 quality audit a vector was very nearly committed with a
literal U+0001 byte inside a JSON string -- forbidden by RFC 8259 -- which
would have broken every port's vector reader while the spec's own CI stayed
green. These are the cheap, mechanical invariants that would have caught it.

One check reaches into OML text: ``check_oml_brace_commas`` scans the OSD-OML
vectors' OML-valued texts (``parse_schema_oml`` input, ``write_schema_oml``
expected output) and rejects a comma directly inside ``{...}``. OML separates
edges with a newline or ``;`` (OML-26/27); a comma is legal only between the
elements of a ``[...]`` array, so ``{ a: 1, b: 2 }`` is a
``parse.unexpected-token`` in every reader. The scanner honours double- and
single-quoted strings, triple-quoted strings and ``#`` comments, and tracks
the innermost open delimiter. Its scope is deliberately narrow: it is a
heuristic for this one mistake (audit F1, which found comma-separated braces
in 27 of 28 vectors), not an OML parser, and checks nothing else about the
text. It has no dependency on any port.

Deliberately not a conformance runner: it never executes a vector, only
checks that the files are well-formed and internally consistent. Semantic
correctness is the ports' job.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUITE = ROOT / "test-suite"

# Tab, LF and CR are the three control characters JSON permits unescaped.
ALLOWED_CONTROLS = {0x09, 0x0A, 0x0D}

# Sec8.5.3's E-27: the read-side drivers, the only ones whose `input` carries
# source text and so the only ones that may give that input as bytes.
BYTES_HEX_OPERATIONS = {"parse", "parse_schema", "parse_schema_oml"}

HEX_DIGITS = set("0123456789abcdef")

# Sec8.5.2's E-32: the one placeholder path a vector may use, and the one
# place it may stand. Everything else in the suite is compared byte for byte.
PATH_PLACEHOLDER = "line:col"
PLACEHOLDER_CODE = "parse.codec-syntax"
PLACEHOLDER_FORMATS = {"json", "yaml", "toml", "xml"}
DOUBLED_BOM_TEXT = "﻿﻿"
DOUBLED_BOM_HEX = "efbbbfefbbbf"

# The vector-local safety-limit parameters (test-suite/README.md, "Declared-limit
# keys"). Each is a positive integer; an unknown `declared_*` key is an error
# because a runner's allowlist would silently run it against its own default.
DECLARED_LIMIT_KEYS = {
    "declared_max_depth",
    "declared_max_nodes",
    "declared_max_int_digits",
    "declared_max_alias_expansion",
    "declared_max_expanded_slots",
}


def check_path_placeholder(rel: str, name: str, vec: dict) -> list[str]:
    """E-32: `"line:col"` as a diagnostic's `path` means "compare the code,
    not the path". Allowed only on a `parse.codec-syntax` entry of a `parse`
    vector over json/yaml/toml/xml, as the vector's only diagnostic, and never
    on D-21's doubled-mark input, whose `1:1` is fixed and stays compared.
    """
    errors: list[str] = []
    expect = vec.get("expect")
    diags = expect.get("diagnostics") if isinstance(expect, dict) else None
    if not isinstance(diags, list):
        return errors
    # Typo guard: a path that is the placeholder in all but case or padding
    # would otherwise pass silently as an ordinary, byte-compared path.
    for d in diags:
        path = d.get("path") if isinstance(d, dict) else None
        if (isinstance(path, str) and path != PATH_PLACEHOLDER
                and path.strip().lower() == PATH_PLACEHOLDER):
            errors.append(
                f"{rel}: {name!r} has path {path!r}, a near-miss of the "
                f"placeholder {PATH_PLACEHOLDER!r} -- E-32 spells it exactly, "
                f"lowercase, no surrounding whitespace"
            )
    marked = [d for d in diags
              if isinstance(d, dict) and d.get("path") == PATH_PLACEHOLDER]
    if not marked:
        return errors
    where = f"{rel}: {name!r} uses the path placeholder {PATH_PLACEHOLDER!r}"
    inp = vec.get("input") if isinstance(vec.get("input"), dict) else {}
    if vec.get("operation") != "parse":
        errors.append(f"{where} on operation {vec.get('operation')!r} -- "
                      f"E-32 allows it only on 'parse'")
    if inp.get("format") not in PLACEHOLDER_FORMATS:
        errors.append(f"{where} on format {inp.get('format')!r} -- E-32 "
                      f"allows it only on {', '.join(sorted(PLACEHOLDER_FORMATS))}; "
                      f"OML and OSD positions are pinned")
    for d in marked:
        if d.get("code") != PLACEHOLDER_CODE:
            errors.append(f"{where} on code {d.get('code')!r} -- E-32 "
                          f"allows it only on {PLACEHOLDER_CODE!r}")
    if len(diags) != 1:
        errors.append(f"{where} in a vector with {len(diags)} diagnostics -- "
                      f"E-32 requires it to be the only one")
    if (str(inp.get("text", "")).startswith(DOUBLED_BOM_TEXT)
            or str(inp.get("bytes_hex", "")).startswith(DOUBLED_BOM_HEX)):
        errors.append(f"{where} on a doubled leading mark -- D-21's 1:1 is "
                      f"fixed and stays compared byte for byte")
    return errors


def check_declared_limits(rel: str, name: str, vec: dict) -> list[str]:
    """Every `declared_*` key is one of the five known limit keys, and its
    value is a positive integer (a bool is not one, though it is an int)."""
    errors: list[str] = []
    for key in vec:
        if key.startswith("declared_"):
            errors.append(
                f"{rel}: {name!r} has {key!r} outside 'input' -- declared-limit "
                f"keys live inside 'input'"
            )
    inp = vec.get("input")
    if not isinstance(inp, dict):
        return errors
    for key, value in inp.items():
        if not key.startswith("declared_"):
            continue
        if key not in DECLARED_LIMIT_KEYS:
            errors.append(
                f"{rel}: {name!r} has unknown key {key!r} -- the known "
                f"declared-limit keys are {', '.join(sorted(DECLARED_LIMIT_KEYS))}"
            )
        elif isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(
                f"{rel}: {name!r} {key!r} is {value!r} -- it must be a "
                f"positive integer"
            )
    return errors


def check_input_form(rel: str, name: str, vec: dict) -> list[str]:
    """E-27: `text` and `bytes_hex` are mutually exclusive, and `bytes_hex`
    is lowercase hex of even length on a read-side operation only.

    Deliberately not a UTF-8 check. A `bytes_hex` vector exists to express
    input that is *not* valid UTF-8 (D-14) -- requiring it to decode would
    reject exactly the vectors the field was added for.
    """
    errors: list[str] = []
    inp = vec.get("input")
    if not isinstance(inp, dict):
        return errors
    has_text = "text" in inp
    operation = vec.get("operation")
    if "bytes_hex" not in inp:
        if operation in BYTES_HEX_OPERATIONS and not has_text:
            errors.append(
                f"{rel}: {name!r} has neither 'text' nor 'bytes_hex' -- "
                f"E-27 requires exactly one on a read-side operation"
            )
        return errors
    raw = inp["bytes_hex"]
    # An explicit null is a wrong type, not an absent field: reporting it as
    # "has neither" would send an author looking for a missing key that is
    # right there.
    if raw is None:
        errors.append(
            f"{rel}: {name!r} 'bytes_hex' is null -- it must be a string of "
            f"lowercase hexadecimal digits"
        )
        return errors
    if has_text:
        errors.append(
            f"{rel}: {name!r} has both 'text' and 'bytes_hex' -- E-27 "
            f"requires exactly one"
        )
    if operation not in BYTES_HEX_OPERATIONS:
        errors.append(
            f"{rel}: {name!r} uses 'bytes_hex' on operation {operation!r} -- "
            f"E-27 allows it only on "
            f"{', '.join(sorted(BYTES_HEX_OPERATIONS))}"
        )
    if not isinstance(raw, str):
        errors.append(f"{rel}: {name!r} 'bytes_hex' is not a string")
        return errors
    if len(raw) % 2:
        errors.append(
            f"{rel}: {name!r} 'bytes_hex' has odd length {len(raw)} -- "
            f"two hex digits per byte"
        )
    bad = sorted(set(raw) - HEX_DIGITS)
    if bad:
        errors.append(
            f"{rel}: {name!r} 'bytes_hex' contains {bad!r} -- lowercase "
            f"hexadecimal digits only, no separators and no prefix"
        )
    return errors


OSD_OML_TEXT_OPERATIONS = {"parse_schema_oml", "write_schema_oml"}


def brace_commas(text: str) -> list[int]:
    """Offsets of every comma whose innermost open delimiter is `{`."""
    found: list[int] = []
    stack: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith('"""', i):
            end = text.find('"""', i + 3)
            i = n if end < 0 else end + 3
            continue
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
            continue
        if c == "'":
            end = text.find("'", i + 1)
            i = n if end < 0 else end + 1
            continue
        if c in "{[":
            stack.append(c)
        elif c in "}]":
            if stack:
                stack.pop()
        elif c == "," and stack and stack[-1] == "{":
            found.append(i)
        i += 1
    return found


def check_oml_brace_commas(rel: str, name: str, vec: dict) -> list[str]:
    """OSD-OML vectors: no comma directly inside braces (see module docs)."""
    if vec.get("operation") not in OSD_OML_TEXT_OPERATIONS:
        return []
    texts = []
    inp = vec.get("input")
    if isinstance(inp, dict) and isinstance(inp.get("text"), str):
        texts.append(("input.text", inp["text"]))
    exp = vec.get("expect")
    if isinstance(exp, dict) and isinstance(exp.get("text"), str):
        texts.append(("expect.text", exp["text"]))
    errors = []
    for where, text in texts:
        for off in brace_commas(text):
            line = text.count("\n", 0, off) + 1
            errors.append(
                f"{rel}: {name!r} {where} line {line} has a comma between "
                f"edges inside braces -- OML separates edges with a newline "
                f"or ';' (OML-26/27)"
            )
    return errors


def main() -> int:
    files = sorted(SUITE.glob("*/*.json"))
    if not files:
        print(f"error: no vector files found under {SUITE}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen: dict[str, str] = {}
    total = 0
    # Counts the prose in docs/ and test-suite/README.md used to hardcode
    # (and let go stale): they are printed here, so the docs can point at
    # this output instead of repeating a number that drifts.
    declared_keys: collections.Counter[str] = collections.Counter()
    placeholder_vectors = 0

    for path in files:
        rel = path.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8")

        # RFC 8259: a raw control character inside a string literal is invalid.
        # Python's json module rejects this too, but reporting it here names
        # the line, which a bare JSONDecodeError does not make obvious.
        for lineno, line in enumerate(raw.splitlines(), start=1):
            for ch in line:
                if ord(ch) < 0x20 and ord(ch) not in ALLOWED_CONTROLS:
                    errors.append(
                        f"{rel}:{lineno}: raw control character U+{ord(ch):04X} "
                        f"-- must be written as an escape"
                    )

        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON -- {exc}")
            continue

        vectors = doc.get("vectors")
        if not isinstance(vectors, list):
            errors.append(f"{rel}: no top-level 'vectors' array")
            continue

        for vec in vectors:
            total += 1
            name = vec.get("name")
            if not name:
                errors.append(f"{rel}: a vector has no 'name'")
                continue
            if name in seen:
                errors.append(
                    f"{rel}: duplicate vector name {name!r} "
                    f"(also in {seen[name]})"
                )
            else:
                seen[name] = str(rel)

            for field in ("operation", "expect"):
                if field not in vec:
                    errors.append(f"{rel}: {name!r} has no {field!r}")

            inp = vec.get("input")
            if isinstance(inp, dict):
                declared_keys.update(
                    k for k in inp if k.startswith("declared_"))
            exp = vec.get("expect")
            if isinstance(exp, dict) and any(
                    isinstance(d, dict) and d.get("path") == PATH_PLACEHOLDER
                    for d in exp.get("diagnostics") or []):
                placeholder_vectors += 1

            errors.extend(check_declared_limits(str(rel), name, vec))
            errors.extend(check_input_form(str(rel), name, vec))
            errors.extend(check_path_placeholder(str(rel), name, vec))
            errors.extend(check_oml_brace_commas(str(rel), name, vec))

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        print(
            f"\n{len(errors)} problem(s) across {len(files)} vector files.",
            file=sys.stderr,
        )
        return 1

    print(
        f"{total} vectors across {len(files)} files: valid JSON, no raw control "
        f"characters, unique names, required fields present, "
        f"'bytes_hex' inputs well-formed (E-27), path placeholder only where "
        f"E-32 allows it, no comma between braced edges in OSD-OML texts."
    )
    keys = ", ".join(f"{k}: {n}" for k, n in sorted(declared_keys.items()))
    print(f"vectors per declared-limit key: {keys}; vectors using the "
          f"{PATH_PLACEHOLDER!r} placeholder: {placeholder_vectors}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
