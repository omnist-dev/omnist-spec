#!/usr/bin/env python3
"""Structural checks over the conformance vector suite.

Nothing in this repository parsed `test-suite/` before this script existed.
During the 2026-09 quality audit a vector was very nearly committed with a
literal U+0001 byte inside a JSON string -- forbidden by RFC 8259 -- which
would have broken every port's vector reader while the spec's own CI stayed
green. These are the cheap, mechanical invariants that would have caught it.

Deliberately not a conformance runner: it never executes a vector, only
checks that the files are well-formed and internally consistent. Semantic
correctness is the ports' job.
"""

from __future__ import annotations

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


def main() -> int:
    files = sorted(SUITE.glob("*/*.json"))
    if not files:
        print(f"error: no vector files found under {SUITE}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen: dict[str, str] = {}
    total = 0

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

            errors.extend(check_input_form(str(rel), name, vec))

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
        f"'bytes_hex' inputs well-formed (E-27)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
